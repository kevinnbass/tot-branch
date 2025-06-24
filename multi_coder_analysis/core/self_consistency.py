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

        before_usage = get_usage_accumulator().copy()

        ctx = HopContext(
            statement_id=base_ctx.statement_id,
            segment_text=base_ctx.segment_text,
            article_id=base_ctx.article_id,
        )

        pipeline.run(ctx)

        after_usage = get_usage_accumulator().copy()

        score = float(after_usage.get("total_tokens", 0) - before_usage.get("total_tokens", 0))

        ans_payload = ctx.final_frame or (ctx.ranking or None)
        if ans_payload is not None:
            if isinstance(ans_payload, list):
                ans_payload = ans_payload[: max_candidates]
            samples.append((ans_payload, score))

    return samples


# ---------------------------------------------------------------------------
# Voting aggregation
# ---------------------------------------------------------------------------

def _majority(pairs):  # type: ignore[override]
    """Hard vote.

    If an element is a ranked list, use its first candidate. Otherwise treat it
    as a plain string label.
    """

    def _top(label):
        return label[0] if isinstance(label, list) else label

    counts = Counter(_top(a) for a, _ in pairs)
    ans, freq = counts.most_common(1)[0]
    return ans, freq / len(pairs)


def _ranked(pairs: List[Tuple[list[str] | str, float]], normalise: bool) -> Tuple[str, float]:
    buckets: Dict[str, float] = defaultdict(float)
    counts: Dict[str, int] = defaultdict(int)

    for ans, score in pairs:
        key = ans[0] if isinstance(ans, list) else ans
        buckets[key] += score
        counts[key] += 1

    if normalise:
        # Average score per candidate
        for ans in buckets:
            buckets[ans] /= max(counts[ans], 1)

    # Edge cases
    ans = min(buckets, key=buckets.get)
    best = buckets[ans]
    worst = max(buckets.values()) or 1

    # unanimous vote → certainty 1.0
    if len(buckets) == 1:
        return ans, 1.0
    # zero-cost paths (all regex) → unknown confidence
    if worst == 0:
        return ans, 0.0

    conf = 1 - (best / worst)
    return ans, conf


def _irv(pairs: list[tuple[list[str] | str, float]]) -> tuple[str, float]:
    from collections import Counter
    rankings = [(r if isinstance(r, list) else [r]) for r, _ in pairs]
    if not rankings:
        return _majority([(a[0] if isinstance(a, list) else a, s) for a, s in pairs])
    while True:
        first = Counter(r[0] for r in rankings if r)
        if not first:
            return _majority([(a[0] if isinstance(a, list) else a, s) for a, s in pairs])
        winner, votes = first.most_common(1)[0]
        if votes > len(rankings) / 2:
            return winner, votes / len(rankings)
        # Determine loser deterministically (alphabetical among least votes)
        min_votes = min(first.values())
        losers = sorted([c for c, v in first.items() if v == min_votes])
        loser = losers[0]
        rankings = [[c for c in r if c != loser] for r in rankings]


def _borda(pairs: list[tuple[list[str] | str, float]]) -> tuple[str, float]:
    from collections import defaultdict
    scores = defaultdict(int)
    for ranking, _ in pairs:
        ranking = ranking if isinstance(ranking, list) else [ranking]
        for idx, cand in enumerate(ranking):
            scores[cand] += len(ranking) - idx
    if not scores:
        return _majority([(a[0] if isinstance(a, list) else a, s) for a, s in pairs])
    winner = max(scores, key=scores.get)
    total = sum(scores.values()) or 1
    return winner, scores[winner] / total


def _mrr(pairs: list[tuple[list[str] | str, float]]) -> tuple[str, float]:
    from collections import defaultdict
    mrr_scores = defaultdict(float)
    for ranking, _ in pairs:
        ranking = ranking if isinstance(ranking, list) else [ranking]
        for idx, cand in enumerate(ranking, 1):
            mrr_scores[cand] += 1 / idx
    if not mrr_scores:
        return _majority([(a[0] if isinstance(a, list) else a, s) for a, s in pairs])
    winner = max(mrr_scores, key=mrr_scores.get)
    total = sum(mrr_scores.values()) or 1
    return winner, mrr_scores[winner] / total


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