from __future__ import annotations

"""Runtime orchestrator for the Tree-of-Thought pipeline.

This thin wrapper bridges the *runtime* layer (CLI / env / I/O) with the
*core* pipeline logic implemented in :pyfunc:`multi_coder_analysis.run_multi_coder_tot`.
"""

import logging
from pathlib import Path
import threading
import sys
import json
import uuid

from multi_coder_analysis.config.run_config import RunConfig
from multi_coder_analysis import run_multi_coder_tot as tot
from multi_coder_analysis.config import load_settings
from multi_coder_analysis.core.pipeline.tot import build_tot_pipeline
from multi_coder_analysis.core.pipeline.consensus_tot import build_consensus_pipeline
from multi_coder_analysis.core.regex import Engine
from multi_coder_analysis.providers import get_provider
from multi_coder_analysis.providers.base import get_usage_accumulator
from multi_coder_analysis.models import HopContext
from multi_coder_analysis.utils.tie import is_perfect_tie
from datetime import datetime

__all__ = ["execute"]


def execute(cfg: RunConfig) -> Path:
    """Execute the ToT pipeline according to *cfg* and return the output CSV path.

    The function merges any values present in legacy `config.yaml` (loaded via
    `load_settings()`) but **explicit CLI/RunConfig values win**.
    """

    # Merge deprecated YAML settings for backwards compatibility
    legacy = load_settings().dict()
    merged_data = {**legacy, **cfg.dict(exclude_unset=True)}  # CLI overrides YAML
    cfg = RunConfig(**merged_data)

    from uuid import uuid4
    run_id_base = datetime.now().strftime("%Y%m%d_%H%M%S") + "-" + uuid4().hex[:6]
    run_id = f"{run_id_base}_{cfg.archive_tag or 'main'}"

    logging.info(
        "Starting ToT run: provider=%s, model=%s, batch=%s, concurrency=%s",
        cfg.provider,
        cfg.model,
        cfg.batch_size,
        cfg.concurrency,
    )

    cfg.output_dir.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------
    # 📂  Copy prompt folder and dump concatenated prompts (guarded by copy_prompts)
    # --------------------------------------------------
    if cfg.copy_prompts and cfg.archive_tag in (None, "main"):
        try:
            from multi_coder_analysis.concat_prompts import concatenate_prompts
            import shutil as _shutil

            # Source prompt directory – use legacy PROMPTS_DIR so behaviour matches
            _src_prompts = Path(tot.PROMPTS_DIR).resolve()
            _dst_prompts = cfg.output_dir / "prompts"

            # Copy the full folder (idempotent: dirs_exist_ok)
            _shutil.copytree(_src_prompts, _dst_prompts, dirs_exist_ok=True)
            logging.info("Copied prompt folder ➜ %s", _dst_prompts)

            # Concatenate prompts into single file in run folder
            _concat_name = "concatenated_prompts.txt"
            concatenate_prompts(_src_prompts, _concat_name, cfg.output_dir)
        except Exception as _e:
            logging.warning("Could not export prompts catalogue: %s", _e)

    # regex counters collected via Regex Engine; usage stats via providers.base.track_usage
    token_accumulator = get_usage_accumulator()
    token_lock = threading.Lock()

    if cfg.phase == "pipeline":
        provider = cfg.provider
        provider_inst = get_provider(provider)

        # --------------------------------------------------
        # Configure regex engine:** live / shadow / off **
        # --------------------------------------------------
        engine = Engine.default()
        mode = cfg.regex_mode.lower()
        if mode == "off":
            engine.set_global_enabled(False)
        elif mode == "shadow":
            engine.set_global_enabled(True)
            engine.set_force_shadow(True)
        else:  # "live" (default)
            engine.set_global_enabled(True)
            engine.set_force_shadow(False)

        # ---------- Self-consistency mode -----------
        if cfg.decode_mode == "self-consistency":
            from multi_coder_analysis.core.self_consistency import decode_paths, aggregate

            import pandas as pd

            df = pd.read_csv(cfg.input_csv, dtype={"StatementID": str})

            from concurrent.futures import ThreadPoolExecutor, as_completed

            results = []

            def _process_row(row_data):
                local_provider = get_provider(cfg.provider)
                base_ctx = HopContext(
                    statement_id=row_data["StatementID"],
                    segment_text=row_data["Statement Text"],
                    article_id=row_data.get("ArticleID", ""),
                )

                pairs = decode_paths(
                    base_ctx,
                    local_provider,
                    cfg.model,
                    votes=cfg.sc_votes,
                    temperature=cfg.sc_temperature,
                    top_k=cfg.sc_top_k,
                    top_p=cfg.sc_top_p,
                    ranked_list=cfg.ranked_list,
                    max_candidates=cfg.max_candidates,
                )

                frame, conf = aggregate(pairs, rule=cfg.sc_rule)

                # Usage already counted via @track_usage decorator

                return {
                    "StatementID": base_ctx.statement_id,
                    "Frame": frame,
                    "Consistency": f"{conf:.2f}",
                }

            with ThreadPoolExecutor(max_workers=cfg.concurrency) as exe:
                future_to_row = {
                    exe.submit(_process_row, row): row for _, row in df.iterrows()
                }

                for fut in as_completed(future_to_row):
                    results.append(fut.result())

            out_df = pd.DataFrame(results)
            out_path = cfg.output_dir / f"sc_results_{datetime.now():%Y%m%d_%H%M%S}.csv"
            out_df.to_csv(out_path, index=False)

            logging.info("Self-consistency run completed ➜ %s", out_path)

            # --- parameter summary ---
            _write_param_summary(cfg, cfg.output_dir)
            from multi_coder_analysis.runtime.tracing import TraceWriter
            TraceWriter(cfg.output_dir / "traces").write_run_summary(token_accumulator)
            return out_path

        # 'permute' mode deprecated until implemented; behaves like 'normal'

        # ---------- Normal / permute path (default) -----------

        tie_records: list = []
        decision_records: list = []

        # --------------------------------------------------------------
        # Build pipeline (consensus-aware or vanilla) only ONCE
        # --------------------------------------------------------------
        if cfg.consensus_mode == "hop":
            pipeline, hop_var = build_consensus_pipeline(
                provider_inst,
                cfg.model,
                batch_size=cfg.batch_size,
                top_k=(None if cfg.sc_top_k == 0 else cfg.sc_top_k),
                top_p=cfg.sc_top_p,
                tie_collector=tie_records,
                concurrency=cfg.concurrency,
                run_id=run_id,
                archive_dir=legacy.get("archive_dir", Path("output/archive")) if legacy.get("archive_enable", True) else Path(),
                tag=cfg.archive_tag or "main",
                ranked_list=cfg.ranked_list,
                max_candidates=cfg.max_candidates,
                decision_collector=decision_records,
            )
        else:
            pipeline = build_tot_pipeline(
                provider_inst,
                cfg.model,
                top_k=(None if cfg.sc_top_k == 0 else cfg.sc_top_k),
                top_p=cfg.sc_top_p,
                ranked_list=cfg.ranked_list,
                max_candidates=cfg.max_candidates,
            )
            hop_var = {}

        # --------------------------------------------------------------
        # Build ONE big list of contexts holding the entire dataset
        # --------------------------------------------------------------
        import pandas as pd

        df = pd.read_csv(cfg.input_csv, dtype={"StatementID": str})

        all_ctxs: list[HopContext] = []
        if cfg.consensus_mode == "hop":
            # ----------------------------------------------------------
            # Canonical eight permutations  (AB, BA, ArBr, …) identical
            # to the outer permutation suite so that hop-consensus and
            # final-consensus runs are directly comparable.
            # ----------------------------------------------------------

            mid = len(df) // 2
            A = df.iloc[:mid].copy().reset_index(drop=True)
            B = df.iloc[mid:].copy().reset_index(drop=True)

            Ar = A.iloc[::-1].copy().reset_index(drop=True)
            Br = B.iloc[::-1].copy().reset_index(drop=True)

            permuted_dfs = [
                pd.concat([A, B], ignore_index=True),      # P1_AB
                pd.concat([B, A], ignore_index=True),      # P2_BA
                pd.concat([Ar, Br], ignore_index=True),    # P3_ArBr
                pd.concat([Br, Ar], ignore_index=True),    # P4_BrAr
                pd.concat([Ar, B], ignore_index=True),     # P5_ArB
                pd.concat([Br, A], ignore_index=True),     # P6_BrA
                pd.concat([A, Br], ignore_index=True),     # P7_ABr
                pd.concat([B, Ar], ignore_index=True),     # P8_BAr
            ]

            for i, _df_perm in enumerate(permuted_dfs):
                for _, row in _df_perm.iterrows():
                    all_ctxs.append(
                        HopContext(
                            statement_id=row["StatementID"],
                            segment_text=row["Statement Text"],
                            article_id=row.get("ArticleID", ""),
                            permutation_idx=i,
                        )
                    )
        else:
            for _, row in df.iterrows():
                all_ctxs.append(
                    HopContext(
                        statement_id=row["StatementID"],
                        segment_text=row["Statement Text"],
                        article_id=row.get("ArticleID", ""),
                    )
                )

        # ---------------- Run the pipeline ONCE -----------------------
        pipeline.run(all_ctxs)

        # --------------------------------------------------------------
        # Collapse back to one representative context per StatementID
        # --------------------------------------------------------------
        from collections import defaultdict

        grouped: defaultdict[str, list[HopContext]] = defaultdict(list)
        for c in all_ctxs:
            grouped[c.statement_id].append(c)

        contexts: list[HopContext] = []
        for sid, ctx_list in grouped.items():
            # Prefer a concluded context; if multiple concluded, pick first
            rep = next((c for c in ctx_list if c.is_concluded), ctx_list[0])
            # If consensus mode, also ensure we capture tie placeholders
            if rep.final_frame is None and ctx_list and cfg.consensus_mode == "hop":
                # no concluded permutation survived (perfect tie) → mark tie
                rep.final_frame = "tie"
                rep.is_concluded = True
            contexts.append(rep)

        # Usage already counted by decorator

        # --- Persist tie traces if any ---
        if tie_records:
            traces_dir = cfg.output_dir / "traces"
            traces_dir.mkdir(parents=True, exist_ok=True)
            tie_out = traces_dir / f"tie_traces_{datetime.now():%Y%m%d_%H%M%S}.jsonl"
            with tie_out.open("w", encoding="utf-8") as f:
                for rec in tie_records:
                    json.dump(rec, f, ensure_ascii=False)
                    f.write("\n")

            logging.info("Wrote %s tie trace(s) ➜ %s", len(tie_records), tie_out)

        # Convert to DataFrame
        out_rows = [
            {
                "StatementID": c.statement_id,
                "Frame": c.final_frame,
                "Justification": c.final_justification,
            }
            for c in contexts
        ]
        out_df = pd.DataFrame(out_rows)
        out_path = cfg.output_dir / f"tot_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        out_df.to_csv(out_path, index=False)

        # Save variability logs if present
        if hop_var:
            variab_path = cfg.output_dir / f"hop_variability_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            variab_path.write_text(json.dumps(hop_var, indent=2, ensure_ascii=False))

            # also save tie segments
            ties_csv = cfg.output_dir / f"tie_segments_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            import csv
            with ties_csv.open("w", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh)
                w.writerow(["StatementID", "Hop", "Distribution"])
                for hop, rows_ in hop_var.items():
                    for sid, dist in rows_:
                        if is_perfect_tie(dist):
                            w.writerow([sid, hop, json.dumps(dist)])

        # ---------------- Determinative votes summary ------------------
        if decision_records:
            import pandas as _pd
            _dec_df = _pd.DataFrame(decision_records)
            _dec_df.to_csv(cfg.output_dir / f"determinative_votes_{datetime.now():%Y%m%d_%H%M%S}.csv", index=False)

        logging.info(
            "LLM stats – calls=%s prompt=%s response=%s total=%s",
            token_accumulator.get("llm_calls", 0),
            token_accumulator.get("prompt_tokens", 0),
            token_accumulator.get("response_tokens", 0),
            token_accumulator.get("total_tokens", 0),
        )

        # --- parameter summary ---
        _write_param_summary(cfg, cfg.output_dir)

        # ---------------- Segment trace export ------------------------
        try:
            import json as _json
            _trace_path = cfg.output_dir / f"segment_traces_{datetime.now():%Y%m%d_%H%M%S}.jsonl"
            with _trace_path.open("w", encoding="utf-8") as _fh:
                for _ctx in all_ctxs:
                    if not _ctx.is_concluded:
                        continue  # skip ongoing

                    _entry = {
                        "statement_id": _ctx.statement_id,
                        "statement_text": _ctx.segment_text,
                        "permutation_idx": getattr(_ctx, "permutation_idx", None),
                        "final_frame": _ctx.final_frame,
                        "hop_decision": _ctx.q_idx if hasattr(_ctx, "q_idx") else None,
                        "raw_llm_responses": _ctx.raw_llm_responses,
                        "analysis_history": _ctx.analysis_history,
                        "reasoning_trace": _ctx.reasoning_trace,
                    }
                    _fh.write(_json.dumps(_entry, ensure_ascii=False) + "\n")
            logging.info("Per-segment traces written ➜ %s", _trace_path)
        except Exception as _e:
            logging.warning("Could not write segment traces: %s", _e)

        # ---------------- Determinative-hop trace export -------------
        try:
            _det_trace_path = cfg.output_dir / f"determinative_traces_{datetime.now():%Y%m%d_%H%M%S}.jsonl"
            with _det_trace_path.open("w", encoding="utf-8") as _fh:
                for _rec in decision_records:
                    _fh.write(_json.dumps(_rec, ensure_ascii=False) + "\n")
            logging.info("Determinative hop traces written ➜ %s", _det_trace_path)
        except Exception as _e:
            logging.warning("Could not write determinative traces: %s", _e)

        return out_path

    # --- Legacy path (default) ---
    _, output_csv = tot.run_coding_step_tot(
        config={},  # legacy param kept for compatibility
        input_csv_path=cfg.input_csv,
        output_dir=cfg.output_dir,
        concurrency=cfg.concurrency,
        model=cfg.model,
        provider=cfg.provider,
        batch_size=cfg.batch_size,
        regex_mode=cfg.regex_mode,
        shuffle_batches=cfg.shuffle_batches,
        token_accumulator=token_accumulator,  # type: ignore[arg-type]
        token_lock=token_lock,  # type: ignore[arg-type]
    )

    logging.info("ToT run completed ➜ %s", output_csv)
    return Path(output_csv)


# ------------------------------------------------------------
# Helper: write comprehensive parameters summary for the run
# ------------------------------------------------------------


def _write_param_summary(cfg: RunConfig, output_dir: Path) -> None:
    """Dump command-line and full RunConfig to JSON in *output_dir*."""

    summary = {
        "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "command_line": " ".join(sys.argv),
        "parameters": cfg.dict(),
    }

    out_file = output_dir / "parameters_summary.json"
    out_file.write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=str), encoding="utf-8")