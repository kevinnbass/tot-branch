from __future__ import annotations

"""Self-consistency decoding helpers.

This module implements the multi-path sampling + voting strategy popularised
by the *Self-Consistency* paper.  The public surface consists of two helpers:

1. decode_paths() → runs *N* independent passes through the deterministic
   Tree-of-Thought pipeline using stochastic decoding.
2. aggregate()    → collapses the list of answers into a single prediction
   according to one of three voting rules.

The implementation is intentionally dependency-free – we rely on the existing
`build_tot_pipeline` to perform a single ToT pass and use provider-supplied
usage metadata as a crude log-prob proxy when length-normalisation is needed.
"""

from collections import Counter, defaultdict
from typing import Dict, List, Tuple

from multi_coder_analysis.core.pipeline.tot import build_tot_pipeline
from multi_coder_analysis.models import HopContext
from multi_coder_analysis.providers import ProviderProtocol, get_provider
from multi_coder_analysis.providers.base import get_usage_accumulator

__all__ = [
    "decode_paths",
    "aggregate",
]


# ---------------------------------------------------------------------------
# Multi-path decoding
# ---------------------------------------------------------------------------

def decode_paths(
    base_ctx: HopContext,
    provider: ProviderProtocol,
    model: str,
    *,
    votes: int,
    temperature: float,
    top_k: int,
    top_p: float,
    ranked_list: bool = False,
    max_candidates: int = 5,
) -> List[Tuple[list[str] | str, float]]:
    """Run the ToT pipeline *votes* times with stochastic sampling.

    Parameters
    ----------
    base_ctx
        Template context holding the statement text + IDs.
    provider
        Provider implementing the generate() interface.
    model
        Model identifier.
    votes
        Number of independent samples.
    temperature, top_k, top_p
        Sampling hyper-parameters forwarded to the provider.  Note that the
        internal ToT pipeline currently passes only *temperature*.  Providers
        expose *top_k*/*top_p* anyway, so we call them directly when ToT falls
        through to the LLM.
    ranked_list
        Whether to return a ranked list of candidates.
    max_candidates
        Maximum number of candidates to return in ranked list.

    Returns
    -------
    list of tuples
        Each tuple is (answer, score) where *answer* is the final frame label
        or a list of labels if multiple answers are possible, and *score* is a
        rough heuristic of likelihood (negative length-normalised token count
        when probability not available).
    """

    # Determine provider short name once for quick cloning per vote
    prov_name = provider.__class__.__name__.replace("Provider", "").lower()

    samples: List[Tuple[list[str] | str, float]] = []

    for _ in range(votes):
        local_provider = get_provider(prov_name)

        # Reset per-instance usage so we can measure cost per vote precisely
        if hasattr(local_provider, "reset_usage"):
            try:
                local_provider.reset_usage()  # type: ignore[attr-defined]
            except Exception:
                pass

        # Build fresh pipeline each vote to avoid state leakage
        pipeline = build_tot_pipeline(
            local_provider,
            model,
            temperature=temperature,
            top_k=(None if top_k == 0 else top_k),
            top_p=top_p,
            ranked_list=ranked_list,
            max_candidates=max_candidates,
        )

        # ---------------- run single path ----------------

        ctx = HopContext(
            statement_id=base_ctx.statement_id,
            segment_text=base_ctx.segment_text,
            article_id=base_ctx.article_id,
        )

        # Capture global usage **before** the path – used for fallback cost estimation
        before_usage = get_usage_accumulator().copy()

        pipeline.run(ctx)

        # ---------------- cost estimate ----------------
        try:
            usage_delta = local_provider.get_acc_usage()  # type: ignore[attr-defined]
            score_tokens = int(usage_delta.get("total_tokens", 0))
        except Exception:
            # Fallback to global accumulator diff (may include noise)
            after_usage = get_usage_accumulator().copy()
            score_tokens = max(after_usage.get("total_tokens", 0) - before_usage.get("total_tokens", 0), 1)

        score = float(max(score_tokens, 1))

        # Preserve the richer ranked list when available even if a final_frame exists.
        ans_payload = (ctx.ranking or None) or ctx.final_frame
        if ans_payload is not None:
            if isinstance(ans_payload, list):
                ans_payload = ans_payload[: max_candidates]
            samples.append((ans_payload, score))

    return samples


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _canon(label: str | None) -> str:
    """Return a canonical key for *label* (case-folded, trimmed)."""
    return (label or "").strip().lower()


def _remember_original(label: str, mapping: Dict[str, str]) -> str:
    """Store *label* under its canonical form in *mapping* if first seen.

    Returns the canonical key so callers can reuse it inline.  This keeps the
    public API returning a nicely cased label (first spelling encountered)
    while all vote bookkeeping happens on canonical keys.
    """
    key = _canon(label)
    mapping.setdefault(key, label.strip())
    return key


# ---------------------------------------------------------------------------
# Voting rules
# ---------------------------------------------------------------------------

def _majority(pairs):  # type: ignore[override]
    """Hard vote.

    If an element is a ranked list, use its first candidate. Otherwise treat it
    as a plain string label.
    """

    original: Dict[str, str] = {}

    def _top(label):
        tok = label[0] if isinstance(label, list) else label
        return _remember_original(str(tok), original)

    counts = Counter(_top(a) for a, _ in pairs)
    winner_key, freq = counts.most_common(1)[0]
    return original[winner_key], freq / len(pairs)


def _ranked(pairs: List[Tuple[list[str] | str, float]], normalise: bool) -> Tuple[str, float]:
    """Vote using per-answer *counts* with optional cost tie-break.

    The winner is the candidate with the most first-place votes.  If several
    candidates tie on votes we pick the one with the **lowest average cost**
    (fewer tokens ≙ higher likelihood).  Confidence is the product of:

    1. vote share – ``winner_votes / total_votes``
    2. relative cost gap – ``1 – (best_cost / worst_cost)`` (0 if no gap)

    This keeps the return value in \[0, 1].
    """

    if not pairs:
        return "unknown", 0.0

    cost_sum: Dict[str, float] = defaultdict(float)
    counts: Dict[str, float] = defaultdict(float)  # fractional weights per candidate
    original: Dict[str, str] = {}

    # Gather stats ---------------------------------------------------------
    for ans, score in pairs:
        norm_score = max(score, 1e-6)

        # Optional length normalisation (legacy "ranked" behaviour)
        if normalise:
            denom = len(ans) if isinstance(ans, list) else max(len(str(ans).split()), 1)
            norm_score /= denom

        # ↓↓↓ vote accumulation ↓↓↓
        if isinstance(ans, list):
            n = len(ans)
            denom = n * (n + 1) / 2  # sum of 1..n  (Borda total)
            if denom == 0:
                denom = 1.0
            for idx, cand in enumerate(ans):
                key = _remember_original(str(cand), original)
                weight = (n - idx) / denom  # scale so ballot sums to 1
                counts[key] += weight
                cost_sum[key] += norm_score * weight
        else:
            key = _remember_original(str(ans), original)
            counts[key] += 1.0
            cost_sum[key] += norm_score

    # Average cost per candidate (only used for tie-break / confidence)
    avg_cost = {k: (cost_sum[k] / counts[k]) for k in counts}

    # ------------------------------------------------------------------
    # Winner selection
    # ------------------------------------------------------------------
    max_votes = max(counts.values())
    pool = [k for k, v in counts.items() if v == max_votes]
    if len(pool) == 1:
        winner = pool[0]
    else:
        # Tie on votes → choose lowest average cost
        winner = min(pool, key=lambda k: (avg_cost[k], k))

    # ------------------------------------------------------------------
    # Confidence estimation
    # ------------------------------------------------------------------
    # Unweighted first-place ballot count for confidence
    raw_first_counts = Counter(_canon((a[0] if isinstance(a, list) else a)) for a, _ in pairs)
    vote_conf = raw_first_counts.get(winner, 0) / len(pairs)

    if len(avg_cost) == 1:  # unanimous vote
        cost_conf = 1.0
    else:
        best_c = avg_cost[winner]
        worst_c = max(avg_cost.values())
        if best_c == worst_c:
            cost_conf = 1.0  # identical cost → fall back to vote share only
        else:
            cost_conf = max(0.0, 1.0 - (best_c / worst_c))

    conf = vote_conf * cost_conf
    return original[winner], conf


def _irv(pairs: list[tuple[list[str] | str, float]]) -> tuple[str, float]:
    original: Dict[str, str] = {}
    rankings = [[_remember_original(c, original) for c in (r if isinstance(r, list) else [r])] for r, _ in pairs]
    if not rankings:
        return _majority([(a[0] if isinstance(a, list) else a, s) for a, s in pairs])

    # Pre-compute average cost per candidate for deterministic tie-breaks
    cost_sum, count_sum = defaultdict(float), defaultdict(int)
    for ans, score in pairs:
        key = _remember_original((ans[0] if isinstance(ans, list) else ans), original)
        cost_sum[key] += max(score, 1e-6)
        count_sum[key] += 1
    avg_cost = {k: cost_sum[k] / count_sum[k] for k in cost_sum}

    while True:
        first = Counter(r[0] for r in rankings if r)
        if not first:
            return _majority([(a[0] if isinstance(a, list) else a, s) for a, s in pairs])

        winner, votes = first.most_common(1)[0]
        if votes > len(rankings) / 2:
            return original[winner], votes / len(rankings)

        # Identify least-voted candidates
        min_votes = min(first.values())
        tied_losers = [c for c, v in first.items() if v == min_votes]

        # Break tie by highest average cost; if still tied use deterministic lexical order
        loser = max(tied_losers, key=lambda c: (avg_cost.get(c, float("inf")), c))

        rankings = [[c for c in r if c != loser] for r in rankings]


def _borda(pairs: list[tuple[list[str] | str, float]]) -> tuple[str, float]:
    scores = defaultdict(float)
    cost_sum = defaultdict(float)
    count_sum = defaultdict(int)
    original: Dict[str, str] = {}

    for ranking, cost in pairs:
        ranking = ranking if isinstance(ranking, list) else [ranking]
        for idx, cand in enumerate(ranking):
            key = _remember_original(str(cand), original)
            scores[key] += len(ranking) - idx
        # Track cost for average-cost tie-breaks (use cost per ballot once)
        top_key = _remember_original(str(ranking[0]), original)
        cost_sum[top_key] += max(cost, 1e-6)
        count_sum[top_key] += 1

    if not scores:
        return _majority([(a[0] if isinstance(a, list) else a, s) for a, s in pairs])

    max_score = max(scores.values())
    pool = [c for c, s in scores.items() if s == max_score]

    if len(pool) == 1:
        winner = pool[0]
    else:
        avg_cost = {c: (cost_sum.get(c, 0.0) / max(count_sum.get(c, 1), 1)) for c in pool}
        winner = min(pool, key=lambda c: (avg_cost.get(c, float("inf")), c))

    total = sum(scores.values()) or 1.0
    return original[winner], scores[winner] / total


def _mrr(pairs: list[tuple[list[str] | str, float]]) -> tuple[str, float]:
    mrr_scores = defaultdict(float)
    cost_sum = defaultdict(float)
    count_sum = defaultdict(int)
    original: Dict[str, str] = {}

    for ranking, cost in pairs:
        ranking = ranking if isinstance(ranking, list) else [ranking]
        for idx, cand in enumerate(ranking, 1):
            key = _remember_original(str(cand), original)
            mrr_scores[key] += 1 / idx
        # Cost bookkeeping for tie-breaks (use cost once per ballot)
        top_key = _remember_original(str(ranking[0]), original)
        cost_sum[top_key] += max(cost, 1e-6)
        count_sum[top_key] += 1

    if not mrr_scores:
        return _majority([(a[0] if isinstance(a, list) else a, s) for a, s in pairs])

    max_score = max(mrr_scores.values())
    pool = [c for c, s in mrr_scores.items() if s == max_score]

    if len(pool) == 1:
        winner = pool[0]
    else:
        avg_cost = {c: (cost_sum.get(c, 0.0) / max(count_sum.get(c, 1), 1)) for c in pool}
        winner = min(pool, key=lambda c: (avg_cost.get(c, float("inf")), c))

    total = sum(mrr_scores.values()) or 1.0
    return original[winner], mrr_scores[winner] / total


def aggregate(pairs, rule: str = "majority") -> tuple[str, float]:
    """Collapse *pairs* into (answer, confidence) according to *rule*."""
    if not pairs:
        return "unknown", 0.0

    rule = rule.lower()
    if rule == "irv":
        return _irv(pairs)
    if rule == "borda":
        return _borda(pairs)
    if rule == "mrr":
        return _mrr(pairs)
    if rule == "majority":
        return _majority(pairs)
    if rule == "ranked":
        return _ranked(pairs, normalise=True)
    if rule == "ranked-raw":
        return _ranked(pairs, normalise=False)
    raise ValueError(f"Unknown rule: {rule}") 