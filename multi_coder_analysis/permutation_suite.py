"""
Eight-order permutation runner for stress-testing the pipeline.

If ``--permutations`` is passed to ``multi_coder_analysis/main.py`` the normal
single-pass pipeline is skipped and this module orchestrates eight runs that
present the input data in different orders.

Output layout:
    multi_coder_analysis/output/<phase>/<dimension>/permutations_<timestamp>/
        P1_AB/ … P8_BAr/     # per-permutation run folders (same files as normal)
        permutation_summary.json          # per-run accuracy/mismatch count
        all_mismatch_records.csv          # union of per-run mismatches (+freq)
        majority_vote_comparison.csv      # majority label vs gold-standard
"""
from __future__ import annotations

import json
import logging
import shutil
import pickle
from datetime import datetime
from pathlib import Path
from typing import List, Tuple
from concurrent.futures import ProcessPoolExecutor, as_completed

import pandas as pd

# The existing ToT coding step
try:
    from .run_multi_coder_tot import run_coding_step_tot  # package-relative
except ImportError:
    from multi_coder_analysis.run_multi_coder_tot import run_coding_step_tot  # fallback when executed as script
except ImportError:
    from run_multi_coder_tot import run_coding_step_tot  # final fallback

# Prompt concatenation utility
try:
    from multi_coder_analysis.concat_prompts import concatenate_prompts
except ImportError:
    from .concat_prompts import concatenate_prompts  # type: ignore

# Regex rules for compiled dump
try:
    from multi_coder_analysis import regex_rules as _rr
except ImportError:
    from . import regex_rules as _rr  # type: ignore

__all__ = ["run_permutation_suite"]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _split_halves(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Split a dataframe into two (approximately equal) halves, preserving order."""
    mid = len(df) // 2
    return df.iloc[:mid].copy(), df.iloc[mid:].copy()


def _permute(dfA: pd.DataFrame, dfB: pd.DataFrame) -> List[Tuple[str, pd.DataFrame]]:
    """Return the eight orderings described in the design doc."""
    A, Ar = dfA.copy(), dfA.iloc[::-1].copy()
    B, Br = dfB.copy(), dfB.iloc[::-1].copy()
    return [
        ("P1_AB", pd.concat([A, B], ignore_index=True)),
        ("P2_BA", pd.concat([B, A], ignore_index=True)),
        ("P3_ArBr", pd.concat([Ar, Br], ignore_index=True)),
        ("P4_BrAr", pd.concat([Br, Ar], ignore_index=True)),
        ("P5_ArB", pd.concat([Ar, B], ignore_index=True)),
        ("P6_BrA", pd.concat([Br, A], ignore_index=True)),
        ("P7_ABr", pd.concat([A, Br], ignore_index=True)),
        ("P8_BAr", pd.concat([B, Ar], ignore_index=True)),
    ]

# ---------------------------------------------------------------------------
# Worker helper (must be top-level for multiprocessing pickling)
# ---------------------------------------------------------------------------

def _worker(tag: str, df_pickle: bytes, root_out_str: str, cfg_dict: dict, worker_args: dict):  # noqa: D401
    """Run one permutation inside its own process.

    Parameters are kept pickle-friendly (bytes / dict / str) so that the
    default 'spawn' start method on Windows works.
    """

    import pandas as _pd  # local import to avoid cross-process state
    import logging as _logging
    from pathlib import Path as _Path
    import pickle as _pkl

    # Minimal console logging inside worker (prefix with tag)
    _logging.basicConfig(level=_logging.INFO, format=f"[{tag}] %(asctime)s %(levelname)s %(message)s")

    df_perm = _pkl.loads(df_pickle)
    root_out = _Path(root_out_str)
    perm_out = root_out / tag
    perm_out.mkdir(exist_ok=True)

    tmp_csv = perm_out / f"input_{tag}.csv"
    df_perm.to_csv(tmp_csv, index=False)

    from multi_coder_analysis.run_multi_coder_tot import run_coding_step_tot  # imported inside worker

    # Execute pipeline for this permutation
    run_coding_step_tot(
        cfg_dict,
        tmp_csv,
        perm_out,
        limit=None,
        start=None,
        end=None,
        concurrency=worker_args["concurrency"],
        model=worker_args["model"],
        provider=worker_args["provider"],
        batch_size=worker_args["batch_size"],
        regex_mode=worker_args["regex_mode"],
        shuffle_batches=worker_args["shuffle_batches"],
        skip_eval=worker_args.get("skip_eval", False),
    )

    # Compute summary & mismatches
    comp_csv = perm_out / "comparison_with_gold_standard.csv"
    if comp_csv.exists():
        df_comp = _pd.read_csv(comp_csv)
        summary = {
            "tag": tag,
            "accuracy": 1.0 - df_comp["Mismatch"].mean(),
            "mismatch_count": int(df_comp["Mismatch"].sum()),
        }
        miss_rows = df_comp[df_comp.Mismatch].copy()
        miss_rows["perm_tag"] = tag
    else:
        summary = {"tag": tag, "accuracy": None, "mismatch_count": None}
        miss_rows = None

    return summary, miss_rows

# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_permutation_suite(config, args, shutdown_event):  # noqa: D401
    """Run the eight-permutation stress test using the existing ToT pipeline.

    A dedicated sub-folder is created and each permutation runs through
    ``run_coding_step_tot`` which already handles batching, regex layer, token
    accounting, etc.
    """

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    root_out = Path("multi_coder_analysis") / "output" / args.phase / args.dimension / f"permutations_{timestamp}"
    root_out.mkdir(parents=True, exist_ok=True)
    logging.info("⚙️  Permutation suite output → %s", root_out)

    # ----------------------------------------------------------------------
    # Load input dataframe (respecting --input if provided)
    # ----------------------------------------------------------------------
    if args.input:
        source_csv = Path(args.input)
    else:
        source_csv = Path("multi_coder_analysis/data") / f"{args.phase}_for_human.csv"
    if not source_csv.exists():
        logging.error("Input CSV not found: %s", source_csv)
        raise FileNotFoundError(source_csv)

    df_in = pd.read_csv(source_csv, dtype={"StatementID": str})

    # ------------------------------------------------------------------
    # Optional subset selection for quick tests (start/end/limit behave the
    # same way as in the main pipeline).  All filtering happens *before*
    # we split the data into A/B halves so that both halves come from the
    # user-requested subset only.
    # ------------------------------------------------------------------
    total_rows = len(df_in)

    if args.start is not None or args.end is not None:
        start_idx = (args.start - 1) if args.start is not None else 0
        end_idx = args.end if args.end is not None else total_rows

        # clamp indices to safe range
        start_idx = max(start_idx, 0)
        end_idx = min(end_idx, total_rows)

        if start_idx >= end_idx:
            raise ValueError(f"Invalid range: start={args.start} end={args.end} (after bounds check)")

        df_in = df_in.iloc[start_idx:end_idx].copy()
        logging.info("Subset applied via --start/--end → rows %s-%s (%s statements)",
                     start_idx + 1, end_idx, len(df_in))

    elif args.limit is not None:
        df_in = df_in.head(args.limit)
        logging.info("Subset applied via --limit → first %s rows", len(df_in))

    # ------------------------------------------------------------------
    # Optional: drop Gold Standard column entirely if --no-eval flag was
    # provided so that downstream components behave as a non-evaluation
    # run (identical to data without gold labels).
    # ------------------------------------------------------------------
    if getattr(args, "no_eval", False) and "Gold Standard" in df_in.columns:
        df_in = df_in.drop(columns=["Gold Standard"])

    dfA, dfB = _split_halves(df_in)

    permutation_metrics: List[dict] = []
    mismatch_union_rows: List[pd.DataFrame] = []

    # ------------------------------------------------------------------
    # Dispatch permutations (serial or parallel)
    # ------------------------------------------------------------------

    perm_jobs = _permute(dfA, dfB)

    worker_args = {
        "concurrency": args.concurrency,
        "model": args.model,
        "provider": args.provider,
        "batch_size": args.batch_size,
        "regex_mode": args.regex_mode,
        "shuffle_batches": args.shuffle_batches,
        "skip_eval": getattr(args, "no_eval", False),
    }

    if getattr(args, "perm_workers", 1) <= 1:
        # Serial execution (original behaviour)
        for tag, df_perm in perm_jobs:
            logging.info("🔄 Running permutation %s (rows=%s)", tag, len(df_perm))
            summary, miss = _worker(tag, pickle.dumps(df_perm), str(root_out), config, worker_args)
            permutation_metrics.append(summary)
            if miss is not None:
                mismatch_union_rows.append(miss)
    else:
        max_workers = min(len(perm_jobs), args.perm_workers)
        logging.info("Executing permutations in parallel with %s workers", max_workers)

        with ProcessPoolExecutor(max_workers=max_workers) as pool:
            futs = {
                pool.submit(_worker, tag, pickle.dumps(df_perm), str(root_out), config, worker_args): tag
                for tag, df_perm in perm_jobs
            }

            for fut in as_completed(futs):
                tag = futs[fut]
                try:
                    summary, miss = fut.result()
                    permutation_metrics.append(summary)
                    if miss is not None:
                        mismatch_union_rows.append(miss)
                except Exception as exc:
                    logging.error("Permutation %s failed: %s", tag, exc, exc_info=True)

    # ------------------------------------------------------------------
    # Summary files
    # ------------------------------------------------------------------
    if permutation_metrics:
        (root_out / "permutation_summary.json").write_text(json.dumps(permutation_metrics, indent=2))

    if mismatch_union_rows:
        df_all_miss = pd.concat(mismatch_union_rows, ignore_index=True)
        freq = df_all_miss.groupby("StatementID").size().rename("miss_freq").reset_index()
        df_all_miss = df_all_miss.merge(freq, on="StatementID", how="left")
        df_all_miss.to_csv(root_out / "all_mismatch_records.csv", index=False)

    # ------------------------------------------------------------------
    # Concatenate consolidated mismatch trace JSONL files from each perm.
    # ------------------------------------------------------------------
    concat_path = root_out / "all_mismatch_consolidated_traces.jsonl"
    with concat_path.open("w", encoding="utf-8") as out_fh:
        for perm_dir in root_out.iterdir():
            if not perm_dir.is_dir():
                continue
            trace_file = perm_dir / "traces_tot" / "traces_tot_mismatch" / "consolidated_mismatch_traces.jsonl"
            if trace_file.exists():
                try:
                    with trace_file.open("r", encoding="utf-8") as fh:
                        for line in fh:
                            out_fh.write(line)
                except Exception as e:
                    logging.warning("Could not read %s: %s", trace_file, e)
    logging.info("Merged mismatch traces → %s", concat_path)

    # ------------------------------------------------------------------
    # Majority vote across permutations
    # ------------------------------------------------------------------
    vote_frames = []
    for perm_dir in root_out.iterdir():
        if perm_dir.is_dir():
            lab_path = perm_dir / "model_labels_tot.csv"
            if lab_path.exists():
                df_lab = pd.read_csv(lab_path)[["StatementID", "Pipeline_Result"]]
                df_lab.rename(columns={"Pipeline_Result": perm_dir.name}, inplace=True)
                vote_frames.append(df_lab)

    if not vote_frames:
        logging.warning("No per-permutation label files found – majority vote skipped.")
        return

    df_votes = vote_frames[0]
    for extra in vote_frames[1:]:
        df_votes = df_votes.merge(extra, on="StatementID")

    def _majority(row):
        counts = row.value_counts()
        if counts.empty:
            return "LABEL_TIE"
        if counts.iloc[0] >= 5:
            return counts.idxmax()
        return "LABEL_TIE"

    df_votes["Majority_Label"] = df_votes.drop(columns=["StatementID"]).apply(_majority, axis=1)

    # Attach gold if present
    if "Gold Standard" in df_in.columns:
        df_votes = df_votes.merge(df_in[["StatementID", "Gold Standard"]], on="StatementID", how="left")
        df_votes["Mismatch"] = df_votes["Majority_Label"] != df_votes["Gold Standard"]

        # --- NEW: count per-row mismatches across individual permutations ---
        perm_cols = [tag for tag, _ in perm_jobs]
        def _mismatch_count(row):
            return sum(row[col] != row["Gold Standard"] for col in perm_cols)

        df_votes["Permutation_Mismatch_Count"] = df_votes.apply(_mismatch_count, axis=1)

    df_votes.to_csv(root_out / "majority_vote_comparison.csv", index=False)

    logging.info("✅ Permutation suite finished. Summary files written to %s", root_out)

    # ------------------------------------------------------------------
    # Copy prompt bundle + regex catalogue for auditability
    # ------------------------------------------------------------------
    try:
        prompt_concat_path = concatenate_prompts(
            prompts_dir="multi_coder_analysis/prompts",
            output_file=f"concatenated_prompts_{timestamp}.txt",
            target_dir=root_out,
        )
        logging.info("Prompts concatenated → %s", prompt_concat_path)
    except Exception as e:
        logging.warning("Could not concatenate prompts: %s", e)

    try:
        patterns_src = Path("multi_coder_analysis/regex/hop_patterns.yml")
        shutil.copy(patterns_src, root_out / "hop_patterns.yml")
        logging.info("Copied hop_patterns.yml to permutation root folder.")
    except Exception as e:
        logging.warning("Could not copy hop_patterns.yml: %s", e)

    # Dump compiled regex rules for full transparency (same as main pipeline)
    try:
        dump_path = root_out / "compiled_rules.txt"
        with dump_path.open("w", encoding="utf-8") as fh:
            fh.write("Hop\tMode\tFrame\tRuleName\tRegex\n")
            for r in _rr.RAW_RULES:
                pattern_str = getattr(r.yes_regex, "pattern", str(r.yes_regex))
                fh.write(f"{r.hop}\t{r.mode}\t{r.yes_frame or ''}\t{r.name}\t{pattern_str}\n")
        logging.info("Compiled regex table dumped → %s", dump_path)
    except Exception as e:
        logging.warning("Could not write compiled_rules.txt: %s", e)

    # ------------------------------------------------------------------
    # Majority-mismatch consolidated traces (only segments where majority
    # label differs from gold standard)
    # ------------------------------------------------------------------
    try:
        maj_mismatch_ids = set(df_votes[df_votes["Mismatch"]]["StatementID"]) if "Mismatch" in df_votes.columns else set()
        if maj_mismatch_ids and concat_path.exists():
            import json as _json
            dest_path = root_out / "majority_mismatch_consolidated_traces.jsonl"
            with dest_path.open("w", encoding="utf-8") as out_fh, concat_path.open("r", encoding="utf-8") as in_fh:
                for line in in_fh:
                    try:
                        obj = _json.loads(line)
                    except Exception:
                        continue
                    if obj.get("statement_id") in maj_mismatch_ids:
                        out_fh.write(line)
            logging.info("Majority mismatch traces → %s", dest_path)
    except Exception as e:
        logging.warning("Could not create majority mismatch trace file: %s", e) 