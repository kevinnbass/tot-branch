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
from multi_coder_analysis.providers import ProviderProtocol

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

    # Build a *fresh* pipeline so state does not leak across samples.
    pipeline = build_tot_pipeline(
        provider,
        model,
        temperature=temperature,
        top_k=(None if top_k == 0 else top_k),
        top_p=top_p,
        ranked_list=ranked_list,
        max_candidates=max_candidates,
    )

    samples: List[Tuple[list[str] | str, float]] = []
    for _ in range(votes):
        # Create a shallow copy of the base context
        ctx = HopContext(
            statement_id=base_ctx.statement_id,
            segment_text=base_ctx.segment_text,
            article_id=base_ctx.article_id,
        )
        # Run ToT
        pipeline.run(ctx)
        if ctx.ranking:
            ans_payload = ctx.ranking[: max_candidates]
        else:
            ans_payload = ctx.final_frame or "∅"

        # Use token count as crude negative log-prob if real logprobs missing
        usage = provider.get_last_usage() or {}
        score = -float(usage.get("total_tokens", 0))
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


def _ranked(pairs: List[Tuple[str, float]], normalise: bool) -> Tuple[str, float]:
    buckets: Dict[str, float] = defaultdict(float)
    counts: Dict[str, int] = defaultdict(int)
    for ans, score in pairs:
        buckets[ans] += score
        counts[ans] += 1

    if normalise:
        # Divide by occurrence count → mean score
        for ans in buckets:
            buckets[ans] /= max(counts[ans], 1)

    # Select maximum score (note score is negative token count, so higher is better)
    ans = max(buckets, key=buckets.get)
    return ans, buckets[ans]


def _irv(pairs: list[tuple[list[str] | str, float]]) -> tuple[str, float]:
    from collections import Counter
    rankings = [(r if isinstance(r, list) else [r]) for r, _ in pairs]
    if not rankings:
        return _majority([(str(a), s) for a, s in pairs])
    while True:
        first = Counter(r[0] for r in rankings if r)
        winner, votes = first.most_common(1)[0]
        if votes > len(rankings) / 2:
            return winner, votes / len(rankings)
        loser = first.most_common()[-1][0]
        rankings = [[c for c in r if c != loser] for r in rankings]


def _borda(pairs: list[tuple[list[str] | str, float]]) -> tuple[str, float]:
    from collections import defaultdict
    scores = defaultdict(int)
    for ranking, _ in pairs:
        if not isinstance(ranking, list):
            continue
        for idx, cand in enumerate(ranking):
            scores[cand] += len(ranking) - idx
    if not scores:
        return _majority([(str(a), s) for a, s in pairs])
    winner = max(scores, key=scores.get)
    return winner, scores[winner]


def _mrr(pairs: list[tuple[list[str] | str, float]]) -> tuple[str, float]:
    from collections import defaultdict
    mrr_scores = defaultdict(float)
    for ranking, _ in pairs:
        if not isinstance(ranking, list):
            continue
        for idx, cand in enumerate(ranking, 1):
            mrr_scores[cand] += 1 / idx
    if not mrr_scores:
        return _majority([(str(a), s) for a, s in pairs])
    winner = max(mrr_scores, key=mrr_scores.get)
    return winner, mrr_scores[winner] / len(pairs)


def aggregate(pairs, rule: str = "majority") -> tuple[str, float]:
    """Collapse *pairs* into (answer, confidence) according to *rule*."""
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