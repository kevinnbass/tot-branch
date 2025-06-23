from __future__ import annotations

"""Per-hop consensus reduction utilities."""

from collections import defaultdict
from typing import Dict, List, Tuple, Iterable

from multi_coder_analysis.models import HopContext
from multi_coder_analysis.core.pipeline import Step
from multi_coder_analysis.core.tiebreaker import conservative_tiebreak
from multi_coder_analysis.utils.tie import is_perfect_tie
from multi_coder_analysis import run_multi_coder_tot as _legacy

__all__ = ["ConsensusStep", "HopVariability"]

# hop -> list[(statement_id, distribution)]
HopVariability = Dict[int, List[Tuple[str, Dict[str, int]]]]


class ConsensusStep(Step[List[HopContext]]):  # type: ignore[misc]
    """Collapse *k* permutations into (optionally) a single survivor.

    The step expects **all** permutations for the same segment at a given hop
    to be present in the incoming list.
    """

    def __init__(
        self,
        hop_idx: int,
        variability_log: HopVariability,
        *,
        tie_collector: list | None = None,
    ):
        self.hop_idx = hop_idx
        self._var = variability_log
        self._tie_collector = tie_collector

    def run(self, ctxs: List[HopContext]) -> List[HopContext]:  # type: ignore[override]
        # Group by segment / statement_id
        buckets: Dict[str, List[HopContext]] = defaultdict(list)
        for c in ctxs:
            buckets[c.statement_id].append(c)

        survivors: List[HopContext] = []
        for sid, perms in buckets.items():
            # Collect votes from permutations ("yes" / "no" / "uncertain")
            votes: List[str] = [
                (p.raw_llm_responses[-1].get("answer", "") if p.raw_llm_responses else "uncertain")
                for p in perms
            ]

            decided, winner = conservative_tiebreak(votes)

            # Record distribution regardless of outcome
            dist = {v: votes.count(v) for v in set(votes)}
            self._var.setdefault(self.hop_idx, []).append((sid, dist))

            if decided and winner == "yes":
                # Select representative permutation (first) to continue
                rep = perms[0]
                rep.is_concluded = True
                if not rep.final_frame:
                    from multi_coder_analysis import run_multi_coder_tot as _legacy
                    rep.final_frame = _legacy.Q_TO_FRAME.get(self.hop_idx)
                survivors.append(rep)
            elif decided and winner == "no":
                # No conclusion – all permutations progress
                survivors.extend(perms)
            else:
                # Tie / no majority – mark concluded as tie (filtered out)
                for p in perms:
                    p.is_concluded = True
                    p.final_frame = "tie"

                if self._tie_collector is not None:
                    entry = {
                        "hop": self.hop_idx,
                        "statement_id": sid,
                        "permutations": []
                    }
                    for p in perms:
                        entry["permutations"].append({
                            "permutation_id": getattr(p, "permutation_idx", None),
                            "answer": (p.raw_llm_responses[-1].get("answer") if p.raw_llm_responses else "uncertain"),
                            "raw_llm_responses": p.raw_llm_responses,
                            "analysis_history": p.analysis_history,
                            "reasoning_trace": p.reasoning_trace,
                        })
                    self._tie_collector.append(entry)
                # Not forwarded further
        return survivors 