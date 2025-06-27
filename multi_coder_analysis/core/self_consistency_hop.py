from __future__ import annotations

"""Hop-by-hop self-consistency decoding.

This variant samples *votes* stochastic answers **per hop**, immediately
aggregates them with the chosen voting rule, then proceeds to the next hop
only if the consensus vote is not a decisive ``yes``.  It therefore stops
spending tokens as soon as the frame is determined, while still injecting
stochastic diversity at every undecided hop.
"""

from typing import List, Tuple, Dict
from collections import Counter

from multi_coder_analysis.models import HopContext
from multi_coder_analysis.core.pipeline.tot import _HopStep  # noqa:  # internal reuse
from multi_coder_analysis.providers import ProviderProtocol, get_provider
from multi_coder_analysis.run_multi_coder_tot import (
    _extract_frame_and_ranking,
    Q_TO_FRAME,
)
from multi_coder_analysis.core.self_consistency import aggregate  # reuse voters
from multi_coder_analysis.providers.base import get_usage_accumulator

__all__ = [
    "decode_iterative",
]


def _build_single_hop_step(
    hop_idx: int,
    provider: ProviderProtocol,
    model: str,
    *,
    temperature: float,
    top_k: int | None,
    top_p: float | None,
    ranked_list: bool,
    max_candidates: int,
) -> _HopStep:
    """Return a HopStep configured for *hop_idx* only."""
    return _HopStep(
        hop_idx,
        provider,
        model,
        temperature=temperature,
        top_k=top_k,
        top_p=top_p,
        ranked_list=ranked_list,
        max_candidates=max_candidates,
    )


def _sample_answers(
    base_ctx: HopContext,
    *,
    hop_idx: int,
    votes: int,
    provider_name: str,
    model: str,
    temperature: float,
    top_k: int | None,
    top_p: float | None,
    ranked_list: bool,
    max_candidates: int,
) -> List[Tuple[str | List[str], float]]:
    """Run *votes* independent samples for a **single hop** and return (ans, score)."""

    samples: List[Tuple[str | List[str], float]] = []

    for _ in range(votes):
        local_provider = get_provider(provider_name)

        if hasattr(local_provider, "reset_usage"):
            try:
                local_provider.reset_usage()  # type: ignore[attr-defined]
            except Exception:
                pass

        step = _build_single_hop_step(
            hop_idx,
            provider=local_provider,
            model=model,
            temperature=temperature,
            top_k=top_k,
            top_p=top_p,
            ranked_list=ranked_list,
            max_candidates=max_candidates,
        )

        # per-instance usage accumulator provides accurate delta; no global snapshot needed

        ctx = HopContext(
            statement_id=base_ctx.statement_id,
            segment_text=base_ctx.segment_text,
            article_id=base_ctx.article_id,
        )

        step.run(ctx)

        # --- cost estimate per vote ---
        try:
            usage_delta = local_provider.get_acc_usage()  # type: ignore[attr-defined]
            score_tokens = int(usage_delta.get("total_tokens", 0))
        except Exception:
            score_tokens = 1

        score = float(max(score_tokens, 1))

        ans_payload: str | List[str] | None = None
        if ctx.final_frame:
            ans_payload = ctx.final_frame
        if ctx.ranking:
            ans_payload = ctx.ranking[: max_candidates]
        if ans_payload is None:
            # Map raw answer field if neither frame nor ranking was set
            raw = ctx.raw_llm_responses[-1].get("answer", "uncertain") if ctx.raw_llm_responses else "uncertain"
            top, ranking = _extract_frame_and_ranking(raw)
            ans_payload = ranking if ranking else top or "uncertain"

        samples.append((ans_payload, score))

    return samples


# ---------------------------------------------------------------------------
# Public helper
# ---------------------------------------------------------------------------

def decode_iterative(
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
    sc_rule: str = "majority",
) -> Tuple[str, float]:
    """Iteratively sample and vote hop-by-hop until frame decided.

    Returns (final_frame, confidence).
    """

    prov_name = provider.__class__.__name__.replace("Provider", "").lower()

    for hop_idx in range(1, 13):
        pairs = _sample_answers(
            base_ctx,
            hop_idx=hop_idx,
            votes=votes,
            provider_name=prov_name,
            model=model,
            temperature=temperature,
            top_k=(None if top_k == 0 else top_k),
            top_p=top_p,
            ranked_list=ranked_list,
            max_candidates=max_candidates,
        )

        winner, conf = aggregate(pairs, rule=sc_rule)

        # Decide if this hop concludes the chain
        if isinstance(winner, list):
            top_choice = winner[0]
        else:
            top_choice = winner

        if str(top_choice).strip().lower() == "yes":
            # Hop 11 special token handled by upstream HopStep; we respect mapping
            frame = Q_TO_FRAME.get(hop_idx, "Neutral")
            return frame, conf

        # continue to next hop otherwise

    # No hop yielded yes → default Neutral
    return "Neutral", 0.0 