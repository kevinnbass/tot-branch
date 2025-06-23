from __future__ import annotations

"""Pure-function Tree-of-Thought pipeline built on :class:`Step`. (Phase 5)"""

from typing import List

from multi_coder_analysis.models import HopContext
from multi_coder_analysis.core.pipeline import Step, Pipeline
from multi_coder_analysis.core.regex import Engine
from multi_coder_analysis.providers import ProviderProtocol

# Re-use existing helper from legacy implementation to avoid code duplication
from multi_coder_analysis import run_multi_coder_tot as _legacy

__all__ = ["build_tot_pipeline"]


class _HopStep(Step[HopContext]):
    """Single-hop processing step.

    The step first tries the regex engine; if inconclusive it delegates to the
    provider using the _legacy._call_llm_single_hop helper to preserve existing
    behaviour.  The class is internal – use :func:`build_tot_pipeline` instead.
    """

    _rx = Engine.default()

    def __init__(
        self,
        hop_idx: int,
        provider: ProviderProtocol,
        model: str,
        *,
        temperature: float,
        top_k: int | None = None,
        top_p: float | None = None,
    ):
        self.hop_idx = hop_idx
        self._provider = provider
        self._model = model
        self._temperature = temperature
        self._top_k = top_k
        self._top_p = top_p

    # ------------------------------------------------------------------
    # The heavy lifting is delegated to code already battle-tested in the
    # legacy module.  This guarantees behavioural parity while moving the
    # orchestration into the new pipeline layer.
    # ------------------------------------------------------------------
    def run(self, ctx: HopContext) -> HopContext:  # noqa: D401
        ctx.q_idx = self.hop_idx

        regex_ans = self._rx.match(ctx)
        if regex_ans:
            ctx.raw_llm_responses.append(regex_ans)
            if regex_ans.get("answer") == "yes":
                ctx.final_frame = regex_ans.get("frame") or _legacy.Q_TO_FRAME[self.hop_idx]
                ctx.final_justification = regex_ans.get("rationale")
                ctx.is_concluded = True
            return ctx

        # Fall-through to LLM
        llm_resp = _legacy._call_llm_single_hop(
            ctx,
            self._provider,
            self._model,
            temperature=self._temperature,
            top_k=self._top_k,
            top_p=self._top_p,
        )  # type: ignore[arg-type]
        ctx.raw_llm_responses.append(llm_resp)
        if llm_resp.get("answer") == "yes":
            ctx.final_frame = _legacy.Q_TO_FRAME[self.hop_idx]
            ctx.final_justification = llm_resp.get("rationale", "").strip()
            ctx.is_concluded = True
        return ctx


def build_tot_pipeline(
    provider: ProviderProtocol,
    model: str,
    *,
    temperature: float = 0.0,
    top_k: int | None = None,
    top_p: float | None = None,
) -> Pipeline[HopContext]:
    """Return a :class:`Pipeline` implementing the 12-hop deterministic chain."""

    steps: List[Step[HopContext]] = [
        _HopStep(
            h,
            provider,
            model,
            temperature=temperature,
            top_k=top_k,
            top_p=top_p,
        )
        for h in range(1, 13)
    ]
    return Pipeline(steps) 