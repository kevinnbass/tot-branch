from __future__ import annotations

"""Consensus-aware Tree-of-Thought pipeline builder."""

from typing import List, Tuple
from pathlib import Path
import os as _os

from multi_coder_analysis.models import HopContext, BatchHopContext
from multi_coder_analysis.core.pipeline import Pipeline, Step
from multi_coder_analysis.core.pipeline.tot import _HopStep  # type: ignore
from multi_coder_analysis.core.consensus import ConsensusStep, HopVariability
from multi_coder_analysis.providers import ProviderProtocol
from multi_coder_analysis import run_multi_coder_tot as _legacy
from multi_coder_analysis.core.regex import Engine

__all__ = ["build_consensus_pipeline"]

# ------------------------------------------------------------
#  New pruning step – must run *after* ConsensusStep so that the
#  decision to conclude a statement is global across permutations
# ------------------------------------------------------------

class _ArchivePruneStep(Step[List[HopContext]]):  # type: ignore[misc]
    def __init__(self, *, run_id: str, archive_dir: Path, tag: str):
        self._run_id = run_id
        self._archive_dir = archive_dir
        self._tag = tag

    def run(self, ctxs: List[HopContext]) -> List[HopContext]:  # type: ignore[override]
        from multi_coder_analysis.utils import archive_resolved

        # Persist concluded contexts
        archive_resolved(
            ctxs,
            run_id=self._run_id,
            tag=self._tag,
            archive_dir=self._archive_dir,
        )

        # Return only unresolved segments to keep RAM low
        return [c for c in ctxs if not c.is_concluded]


class _ParallelHopStep(Step[List[HopContext]]):  # type: ignore[misc]
    """Map a single-hop step across all permutations in the list."""

    def __init__(
        self,
        hop_idx: int,
        provider: ProviderProtocol,
        model: str,
        *,
        batch_size: int,
        temperature: float,
        concurrency: int,
        top_k: int | None = None,
        top_p: float | None = None,
        run_id: str,
        archive_dir: Path,
        tag: str,
        ranked_list: bool = False,
        max_candidates: int = 5,
    ):
        self.hop_idx = hop_idx  # store for progress logging
        self._inner = _HopStep(
            hop_idx,
            provider,
            model,
            temperature=temperature,
            top_k=top_k,
            top_p=top_p,
            ranked_list=ranked_list,
            max_candidates=max_candidates,
        )
        self._provider = provider
        self._model = model
        self._temperature = temperature
        self._batch_size = max(1, batch_size)
        self._concurrency = max(1, concurrency)
        # Preserve for child steps (needed only for _log_hop; kept anyway)
        self._run_id = run_id
        self._archive_dir = archive_dir
        self._tag = tag
        self._rx = Engine.default()

    def run(self, ctxs: List[HopContext]) -> List[HopContext]:  # type: ignore[override]
        # --- Progress log (aggregated) ----------------------------------
        try:
            # Unique unresolved statement IDs – matches legacy banner expectation
            _active_ids = {c.statement_id for c in ctxs if not c.is_concluded}
            _active = len(_active_ids)

            # This is filled later during batch processing – initialise empty set
            regex_yes_ids: set[str] = set()
        except Exception:  # noqa: BLE001 – logging must never break flow
            pass

        # Emit *start* banner before any processing
        _primary = _os.getenv("PRIMARY_PERMUTATION", "1") == "1"

        try:
            if _primary:
                print(
                    f"*** START Hop {self.hop_idx:02} → start:{_active} regex:0 llm:0 remain:{_active} ***",
                    flush=True,
                )
        except Exception:
            pass

        # ------------------ Batch processing ---------------------------
        results: List[HopContext] = []

        # Align output ordering with input
        pending: List[HopContext] = []
        for c in ctxs:
            if c.is_concluded:
                results.append(c)
            else:
                pending.append(c)

        # Early exit if nothing to do
        if not pending:
            return results

        # ------------------------------------------------------
        # Split pending into *per-permutation* mini-pools so that
        # batches are formed independently within each permutation.
        # ------------------------------------------------------
        from collections import defaultdict
        from math import ceil

        groups: defaultdict[int | None, list[HopContext]] = defaultdict(list)
        for seg in pending:
            perm_id = getattr(seg, "permutation_idx", None)
            groups[perm_id].append(seg)

        llm_yes_ids: set[str] = set()
        banner_printed = False

        # Collect all LLM tasks across *all* permutations
        all_tasks: list[tuple[BatchHopContext, dict[str, HopContext]]] = []

        for perm_id, segs in groups.items():
            num_batches = ceil(len(segs) / self._batch_size)
            for b_idx in range(num_batches):
                batch_segments = segs[b_idx * self._batch_size : (b_idx + 1) * self._batch_size]

                # -------------- Regex pre-check -----------------
                unresolved: List[HopContext] = []
                for seg in batch_segments:
                    seg.q_idx = self.hop_idx
                    rx_ans = None
                    try:
                        rx_ans = self._rx.match(seg)
                    except Exception as _e:
                        import logging as _lg
                        _lg.warning("Regex engine error on %s Q%s: %s", seg.statement_id, self.hop_idx, _e)

                    if rx_ans and rx_ans.get("answer") == "yes":
                        seg.raw_llm_responses.append(rx_ans)  # type: ignore[arg-type]
                        seg.final_frame = rx_ans.get("frame") or _legacy.Q_TO_FRAME.get(self.hop_idx)
                        seg.final_justification = rx_ans.get("rationale")
                        seg.is_concluded = True
                        results.append(seg)
                        regex_yes_ids.add(seg.statement_id)
                    else:
                        unresolved.append(seg)

                if _primary and not banner_printed:
                    # Emit regex banner before the first LLM call (or immediately
                    # if the entire hop resolves via regex and no LLM call is needed).
                    if len(regex_yes_ids) > 0:
                        print(
                            f"*** REGEX HIT Hop {self.hop_idx:02} → regex:{len(regex_yes_ids)} ***",
                            flush=True,
                        )
                    else:
                        print(
                            f"*** REGEX MISS Hop {self.hop_idx:02} ***",
                            flush=True,
                        )
                    banner_printed = True

                if not unresolved:
                    continue  # this batch fully resolved by regex

                # -------------- Defer LLM batch ------------------
                import uuid
                batch_id = f"batch_{self.hop_idx}_{perm_id}_{uuid.uuid4().hex[:6]}"
                batch_ctx = BatchHopContext(batch_id=batch_id, hop_idx=self.hop_idx, segments=unresolved)

                sid_to_ctx = {c.statement_id: c for c in unresolved}
                all_tasks.append((batch_ctx, sid_to_ctx))

        # Re-attach results in original ordering
        sid_to_processed = {c.statement_id: c for c in results}
        ordered: List[HopContext] = [sid_to_processed[c.statement_id] if c.statement_id in sid_to_processed else c for c in ctxs]

        # --- Execute all queued LLM batches in parallel ------------------
        if all_tasks:
            from concurrent.futures import ThreadPoolExecutor, as_completed

            def _worker(bctx: BatchHopContext):
                return _legacy._call_llm_batch(bctx, self._provider, self._model, self._temperature)

            with ThreadPoolExecutor(max_workers=self._concurrency) as exe:
                future_map = {exe.submit(_worker, ctx): (ctx, sid_map) for ctx, sid_map in all_tasks}

                for fut in as_completed(future_map):
                    batch_ctx, sid_to_ctx = future_map[fut]
                    try:
                        resp_objs = fut.result()
                    except Exception as exc:
                        import logging as _lg
                        _lg.error("LLM batch %s failed: %s", batch_ctx.batch_id, exc)
                        resp_objs = []

                    for obj in resp_objs:
                        sid = str(obj.get("segment_id", "")).strip()
                        ctx = sid_to_ctx.get(sid)
                        if ctx is None:
                            continue
                        ans = str(obj.get("answer", "uncertain")).lower().strip()
                        rationale = str(obj.get("rationale", ""))

                        ctx.raw_llm_responses.append(obj)  # type: ignore[arg-type]

                        if ans == "yes":
                            ctx.final_frame = _legacy.Q_TO_FRAME.get(self.hop_idx)
                            ctx.final_justification = rationale
                            ctx.is_concluded = True
                            llm_yes_ids.add(ctx.statement_id)

                    # any still unresolved after responses
                    for ctx in sid_to_ctx.values():
                        if ctx not in results and ctx.is_concluded is False:
                            results.append(ctx)

        # ---------------- FINISH banner -------------------
        if _primary:
            end_active = _active - len(regex_yes_ids) - len(llm_yes_ids)
            # Ensure regex banner emitted at least once
            if not banner_printed:
                if len(regex_yes_ids) > 0:
                    print(
                        f"*** REGEX HIT Hop {self.hop_idx:02} → regex:{len(regex_yes_ids)} ***",
                        flush=True,
                    )
                else:
                    print(
                        f"*** REGEX MISS Hop {self.hop_idx:02} ***",
                        flush=True,
                    )
            try:
                print(
                    f"*** FINISH Hop {self.hop_idx:02} → start:{_active} "
                    f"regex:{len(regex_yes_ids)} llm:{len(llm_yes_ids)} "
                    f"remain:{end_active} ***",
                    flush=True,
                )
            except Exception:
                pass

        return ordered


def build_consensus_pipeline(
    provider: ProviderProtocol,
    model: str,
    temperature: float = 0.0,
    batch_size: int = 10,
    concurrency: int = 1,
    top_k: int | None = None,
    top_p: float | None = None,
    tie_collector: list | None = None,
    variability_log: HopVariability | None = None,
    *,
    run_id: str,
    archive_dir: Path,
    tag: str,
    ranked_list: bool = False,
    max_candidates: int = 5,
) -> Tuple[Pipeline[List[HopContext]], HopVariability]:
    """Return a pipeline operating on *lists* of HopContext objects."""

    var: HopVariability = variability_log or {}

    steps: List[Step[List[HopContext]]] = []
    for h in range(1, 13):
        steps.append(
            _ParallelHopStep(
                h,
                provider,
                model,
                batch_size=batch_size,
                temperature=temperature,
                concurrency=concurrency,
                top_k=top_k,
                top_p=top_p,
                run_id=run_id,
                archive_dir=archive_dir,
                tag=tag,
                ranked_list=ranked_list,
                max_candidates=max_candidates,
            )
        )
        steps.append(ConsensusStep(h, var, tie_collector=tie_collector))
        steps.append(_ArchivePruneStep(run_id=run_id, archive_dir=archive_dir, tag=tag))

    return Pipeline(steps), var 