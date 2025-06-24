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
from typing import List, Tuple, Sequence
from concurrent.futures import ProcessPoolExecutor, as_completed
import os as _os

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
# Batch-level helpers (new)
# ---------------------------------------------------------------------------

def _make_batches(df: pd.DataFrame, batch_size: int) -> List[pd.DataFrame]:
    """Split *df* into consecutive batches of *batch_size* rows (last batch may be smaller)."""
    if batch_size <= 0:
        raise ValueError("batch_size must be > 0")
    return [df.iloc[i : i + batch_size].copy() for i in range(0, len(df), batch_size)]


def _permute_batches(A: Sequence[pd.DataFrame], B: Sequence[pd.DataFrame]) -> List[Tuple[str, List[pd.DataFrame]]]:
    """Return eight permutations applied to *lists of batches* (not individual rows).

    Each element in *A* or *B* is an intact batch (DataFrame).  Permutations only
    rearrange the *order* of those batches, leaving row order **within** each
    batch unchanged so that the exact segment co-occurrence inside a batch is
    identical across all eight runs.
    """

    A, B = list(A), list(B)  # ensure we can slice/reverse safely
    Ar, Br = list(reversed(A)), list(reversed(B))

    return [
        ("P1_AB", A + B),
        ("P2_BA", B + A),
        ("P3_ArBr", Ar + Br),
        ("P4_BrAr", Br + Ar),
        ("P5_ArB", Ar + B),
        ("P6_BrA", Br + A),
        ("P7_ABr", A + Br),
        ("P8_BAr", B + Ar),
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

    # Mark the first (or only) permutation as primary for hop banners
    if tag in ("P1_AB", "main"):
        _os.environ["PRIMARY_PERMUTATION"] = "1"

    # Minimal console logging inside worker (prefix with tag)
    _logging.basicConfig(level=_logging.INFO, format=f"[{tag}] %(asctime)s %(levelname)s %(message)s")

    # ------------------------------------------------------------------
    # Silence noisy Google SDK / AFC / HTTP libraries inside the *worker*
    # process as we did in the parent.  Each worker has its own logging
    # hierarchy, so we need to repeat the setup locally.
    # ------------------------------------------------------------------

    class _AFCNoiseFilter(_logging.Filter):
        _PHRASES = ("AFC is enabled", "AFC remote call", "max remote calls")

        def filter(self, record):  # type: ignore[override]
            msg = record.getMessage()
            return not any(p in msg for p in self._PHRASES)

    for noisy in ("google", "google.genai", "google.genai.client", "httpx", "urllib3"):
        _logging.getLogger(noisy).setLevel(_logging.ERROR)
        _logging.getLogger(noisy).addFilter(_AFCNoiseFilter())

    # Also attach filter to root so third-party libs inherit it
    _logging.getLogger().addFilter(_AFCNoiseFilter())

    # ---------------- Stdout/Stderr monkey-patch ------------------
    import sys as _sys, io as _io

    class _FilteredStream(_io.TextIOBase):
        def __init__(self, original):
            self._orig = original

        def write(self, s):  # type: ignore[override]
            if any(p in s for p in _AFCNoiseFilter._PHRASES):
                return len(s)
            return self._orig.write(s)

        def flush(self):  # type: ignore[override]
            return self._orig.flush()

    _sys.stdout = _FilteredStream(_sys.stdout)
    _sys.stderr = _FilteredStream(_sys.stderr)

    df_perm = _pkl.loads(df_pickle)
    root_out = _Path(root_out_str)
    perm_out = root_out / tag
    perm_out.mkdir(exist_ok=True)

    tmp_csv = perm_out / f"input_{tag}.csv"
    df_perm.to_csv(tmp_csv, index=False)

    # Decide which execution engine to use
    _needs_pipeline = (
        worker_args["consensus_mode"] != "final" or worker_args["decode_mode"] != "normal"
    )

    if _needs_pipeline:
        # --------------------------------------------------------------
        # New modular pipeline with per-hop consensus / self-consistency
        # --------------------------------------------------------------
        from multi_coder_analysis.config.run_config import RunConfig as _RC  # local import
        from multi_coder_analysis.runtime.tot_runner import execute as _exec

        _cfg = _RC(
            phase="pipeline",
            input_csv=tmp_csv,
            output_dir=perm_out,
            provider=worker_args["provider"],
            model=worker_args["model"],
            batch_size=worker_args["batch_size"],
            concurrency=worker_args["concurrency"],
            regex_mode=worker_args["regex_mode"],
            shuffle_batches=worker_args["shuffle_batches"],
            consensus_mode=worker_args["consensus_mode"],
            decode_mode=worker_args["decode_mode"],
            sc_votes=worker_args["sc_votes"],
            sc_rule=worker_args["sc_rule"],
            sc_temperature=worker_args["sc_temperature"],
            sc_top_k=worker_args["sc_top_k"],
            sc_top_p=worker_args["sc_top_p"],

            # -------------- Archive tagging --------------
            archive_tag=tag,           # ensures per-worker archive file
            copy_prompts=False,
        )

        _result_path = _exec(_cfg)

        # Harmonise output name so downstream majority vote stays unchanged
        import pandas as _pd
        df_out = _pd.read_csv(_result_path)
        # Legacy loader expects ['StatementID', 'Pipeline_Result']
        map_cols = {
            "Frame": "Pipeline_Result",
            "Final": "Pipeline_Result",
            "Majority_Label": "Pipeline_Result",
        }
        for src, tgt in map_cols.items():
            if src in df_out.columns:
                df_out = df_out[["StatementID", src]].rename(columns={src: tgt})
                break
        else:
            # fallback: assume second column is the result
            _other_cols = [c for c in df_out.columns if c != "StatementID"]
            df_out = df_out[["StatementID", _other_cols[0]]].rename(columns={_other_cols[0]: "Pipeline_Result"})

        df_out.to_csv(perm_out / "model_labels_tot.csv", index=False)

    else:
        # --------------------------------------------------------------
        # Legacy deterministic ToT path
        # --------------------------------------------------------------
        from multi_coder_analysis.run_multi_coder_tot import run_coding_step_tot  # lazy import

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
            skip_eval=worker_args["skip_eval"],
            only_hop=worker_args["only_hop"],
            print_summary=False,
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

def run_permutation_suite(
    config,
    args,
    shutdown_event,
    *,
    override_df=None,
    out_dir_suffix: str | None = None,
):  # noqa: D401
    """Run the eight-permutation stress test.

    Parameters
    ----------
    config : dict
        Loaded YAML configuration.
    args : argparse.Namespace
        Parsed CLI arguments (model, provider, batch-size …).
    shutdown_event : threading.Event
        Used for graceful SIGINT handling.
    override_df : pandas.DataFrame | None, optional (keyword-only)
        If supplied, *this* dataframe is used as input instead of reading
        ``args.input``.  Allows the caller to inject an arbitrary slice such
        as *low_ratio_segments.csv* for a fallback pass.
    out_dir_suffix : str | None, optional (keyword-only)
        Appended to the autogenerated output folder name.  The fallback pass
        uses the value ``"fallback"`` so its artefacts live alongside – yet
        separate from – the main permutation run.
    """

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = f"_{out_dir_suffix}" if out_dir_suffix else ""
    root_out = (
        Path("multi_coder_analysis")
        / "output"
        / args.phase
        / args.dimension
        / f"permutations_{timestamp}{suffix}"
    )
    root_out.mkdir(parents=True, exist_ok=True)
    logging.info("⚙️  Permutation suite output → %s", root_out)

    # ------------------------------------------------------------------
    # Copy prompt folder ONCE & write concatenated catalogue at start
    # ------------------------------------------------------------------
    try:
        src_prompt_dir = Path("multi_coder_analysis/prompts")
        dst_prompt_dir = root_out / "prompts"
        import shutil
        shutil.copytree(src_prompt_dir, dst_prompt_dir, dirs_exist_ok=True)

        from multi_coder_analysis.concat_prompts import concatenate_prompts

        _prompts_txt = concatenate_prompts(
            prompts_dir=src_prompt_dir,
            output_file="concatenated_prompts.txt",
            target_dir=root_out,
        )
        logging.info("Copied prompt folder & concatenated ➜ %s", _prompts_txt)
    except Exception as e:
        logging.warning("Could not copy/concatenate prompts: %s", e)

    # ----------------------------------------------------------------------
    # Load dataframe
    # ----------------------------------------------------------------------
    if override_df is not None:
        df_in = override_df.copy()
        logging.info("Override dataframe supplied (%s rows) – skipping file load.", len(df_in))
    else:
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

    # ------------------------------------------------------------------
    # If hop-level consensus is requested, we must run *one* worker only.
    # That worker will generate the eight internal permutations itself so
    # creating separate permutation jobs here would multiply the work 8×8.
    # ------------------------------------------------------------------

    if getattr(args, "consensus", "final") == "hop":
        logging.info("Hop-level consensus → running a single combined job (no external permutations)")
        perm_jobs = [("main", df_in.copy())]
    else:
        # --------------------------------------------------------------
        # Build *batch-level* permutations – preserves batch composition
        # --------------------------------------------------------------

        effective_batch_size = max(1, getattr(args, "batch_size", 1))
        batch_list = _make_batches(df_in, effective_batch_size)

        mid_batches = len(batch_list) // 2
        batchesA, batchesB = batch_list[:mid_batches], batch_list[mid_batches:]

        perm_jobs = [
            (tag, pd.concat(batches, ignore_index=True))
            for tag, batches in _permute_batches(batchesA, batchesB)
        ]

    permutation_metrics: List[dict] = []
    mismatch_union_rows: List[pd.DataFrame] = []

    worker_args = {
        "concurrency": args.concurrency,
        "model": args.model,
        "provider": args.provider,
        "batch_size": args.batch_size,
        "regex_mode": args.regex_mode,
        "shuffle_batches": args.shuffle_batches,
        "skip_eval": getattr(args, "no_eval", False),
        "only_hop": args.only_hop,
        "consensus_mode": getattr(args, "consensus", "final"),
        "decode_mode": getattr(args, "decode_mode", "normal"),
        "sc_votes": getattr(args, "sc_votes", 1),
        "sc_rule": getattr(args, "sc_rule", "majority"),
        "sc_temperature": getattr(args, "sc_temperature", 0.7),
        "sc_top_k": getattr(args, "sc_top_k", 40),
        "sc_top_p": getattr(args, "sc_top_p", 0.95),
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
    # Copy regex catalogue for auditability (prompt folder already copied)
    # ------------------------------------------------------------------
    try:
        patterns_src = Path("multi_coder_analysis/regex/hop_patterns.yml")
        import shutil
        shutil.copy(patterns_src, root_out / "hop_patterns.yml")
        logging.info("Copied hop_patterns.yml to permutation root folder.")
    except Exception as e:
        logging.warning("Could not copy hop_patterns.yml: %s", e)

    # ------------------------------------------------------------------
    # Majority vote across permutations
    # ------------------------------------------------------------------
    vote_frames = []
    for perm_dir in root_out.iterdir():
        if perm_dir.is_dir():
            lab_path = perm_dir / "model_labels_tot.csv"
            if not lab_path.exists():
                continue

            df_lab = pd.read_csv(lab_path)[["StatementID", "Pipeline_Result"]]
            df_lab.rename(columns={"Pipeline_Result": perm_dir.name}, inplace=True)

            # --------------------------------------------------------------
            # NEW: incorporate dissonant duplicate answers found during the
            #      run so that majority voting can weigh them as extra votes.
            #      Each conflicting duplicate becomes its own *synthetic*
            #      column (permTag_dupN) with the alternate label.
            # --------------------------------------------------------------
            dup_dir = perm_dir / "traces_tot" / "batch_traces"
            if dup_dir.exists():
                extra_cols = {}
                dup_idx = 1
                import json as _json
                for dup_file in dup_dir.glob("*_duplicates.json"):
                    try:
                        with dup_file.open("r", encoding="utf-8") as fh:
                            data = _json.load(fh)
                    except Exception:
                        continue

                    for rec in data.get("duplicates", []):
                        sid = str(rec.get("segment_id"))
                        new_ans = str(rec.get("new_answer") or rec.get("new", "")).strip()
                        # 'prev_answers' may be list[str] or str
                        prev_ans_raw = rec.get("prev_answers") or rec.get("prev_answer")
                        if isinstance(prev_ans_raw, list):
                            prev_set = set(map(str, prev_ans_raw))
                        else:
                            prev_set = {str(prev_ans_raw)} if prev_ans_raw is not None else set()

                        # Only count as extra vote if the *new* answer is truly dissonant
                        if new_ans and new_ans not in prev_set:
                            col_name = f"{perm_dir.name}_dup{dup_idx}"
                            extra_cols.setdefault(col_name, {})[sid] = new_ans
                            dup_idx += 1

                # Convert collected maps into DataFrames for merging
                for col_name, sid_map in extra_cols.items():
                    df_extra = pd.DataFrame({
                        "StatementID": list(sid_map.keys()),
                        col_name: list(sid_map.values()),
                    })
                    df_lab = df_lab.merge(df_extra, on="StatementID", how="left")

            vote_frames.append(df_lab)

    if not vote_frames:
        logging.warning("No per-permutation label files found – majority vote skipped.")
        return

    df_votes = vote_frames[0]
    for extra in vote_frames[1:]:
        df_votes = df_votes.merge(extra, on="StatementID")

    def _majority(row):
        """Return winning label or LABEL_TIE.

        Threshold is >50% of the *available* (non-NA) votes so the function
        works whether we have 1, 8 or any other number of permutation
        columns.  The previous hard-coded ≥5 rule only made sense for eight
        columns.
        """
        counts = row.value_counts(dropna=True)
        if counts.empty:
            return "LABEL_TIE"

        total_votes = int(row.count())
        required = (total_votes // 2) + 1  # simple majority (>50%)

        if counts.iloc[0] >= required:
            return counts.idxmax()
        return "LABEL_TIE"

    df_votes["Majority_Label"] = df_votes.drop(columns=["StatementID"]).apply(_majority, axis=1)

    # ------------------------------------------------------------------
    # If a Gold Standard column is available in the *input* dataframe we
    # compute a boolean mismatch flag and the number of individual
    # permutations that disagree with the gold label for each statement.
    # ------------------------------------------------------------------

    if "Gold Standard" in df_in.columns:
        df_votes = df_votes.merge(df_in[["StatementID", "Gold Standard"]], on="StatementID", how="left")
        df_votes["Mismatch"] = df_votes["Majority_Label"] != df_votes["Gold Standard"]

        perm_cols = [tag for tag, _ in perm_jobs]

        def _mismatch_count(row):
            return sum(row[col] != row["Gold Standard"] for col in perm_cols)

        df_votes["Permutation_Mismatch_Count"] = df_votes.apply(_mismatch_count, axis=1)

    # ------------------------------------------------------------------
    # Majority label *strength* ratio: occurrences of Majority_Label across
    # the permutation columns divided by occurrences of the *other* labels.
    # Applies regardless of whether a Gold Standard column is present.
    # ------------------------------------------------------------------

    perm_cols = [tag for tag, _ in perm_jobs]

    def _majority_strength(row):
        maj_label = row["Majority_Label"]
        maj_count = sum(row[col] == maj_label for col in perm_cols)
        other = len(perm_cols) - maj_count
        return maj_count / other if other else float("inf")

    df_votes["Majority_Label_Ratio"] = df_votes.apply(_majority_strength, axis=1)

    df_votes.to_csv(root_out / "majority_vote_comparison.csv", index=False)

    logging.info("✅ Permutation suite finished. Summary files written to %s", root_out)

    # ------------------------------------------------------------------
    # Low ratio traces (automatic export)
    # ------------------------------------------------------------------
    try:
        # Re-use the standalone extractor so behaviour stays in sync
        from scripts import extract_low_ratio_traces as _lr  # package-relative import
    except ImportError:  # pragma: no cover – fallback when running as module
        try:
            import extract_low_ratio_traces as _lr  # type: ignore
        except Exception:
            _lr = None  # extractor not available

    if _lr is not None:
        try:
            lr_records = _lr.collect_traces(root_out, threshold=getattr(args, 'low_ratio_threshold', _lr.THRESHOLD))
            if lr_records:
                _lr.write_output(root_out, lr_records)
                logging.info("Low-ratio trace files written to %s", root_out)
        except Exception as e:
            logging.warning("Could not generate low-ratio trace files: %s", e)

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

    # ------------------------------------------------------------------
    # Special renames for fallback run so downstream scripts can pick them
    # up easily without parsing nested folders.
    # ------------------------------------------------------------------
    if out_dir_suffix == "fallback":
        import shutil as _shutil
        try:
            src = root_out / "model_labels_tot.csv"
            if src.exists():
                _shutil.copy(src, root_out / "low_ratio_segments_fallback.csv")
        except Exception:
            pass
        try:
            src = root_out / "all_mismatch_consolidated_traces.jsonl"
            if src.exists():
                _shutil.copy(src, root_out / "low_ratio_traces_fallback.jsonl")
        except Exception:
            pass
        try:
            src = root_out / "majority_vote_comparison.csv"
            if src.exists():
                _shutil.copy(src, root_out / "majority_vote_comparison_fallback.csv")
        except Exception:
            pass

    return root_out 