import argparse
import logging
import sys
import yaml
from pathlib import Path
from datetime import datetime
import os
from typing import Dict, Optional
import threading
import signal
import shutil
import multiprocessing as _mp, os as _os, signal as _signal

# --- Import step functions from other modules --- #
# from run_multi_coder import run_coding_step  # TODO: Create this for standard pipeline
# Support both "python multi_coder_analysis/main.py" (script) and
# "python -m multi_coder_analysis.main" (module) invocation styles.
try:
    from .run_multi_coder_tot import run_coding_step_tot  # package-relative when executed as module
    from . import run_multi_coder_tot as _tot_mod
except ImportError:
    from run_multi_coder_tot import run_coding_step_tot  # direct import when executed as script
    import run_multi_coder_tot as _tot_mod
# from merge_human_and_models import run_merge_step  # TODO: Create this
# from reliability_stats import run_stats_step  # TODO: Create this
# from sampling import run_sampling_for_phase  # TODO: Create this

# --- Import prompt concatenation utility ---
# Support both module and script execution styles
try:
    from .concat_prompts import concatenate_prompts  # package-relative
except ImportError:
    from concat_prompts import concatenate_prompts  # script-level fallback

# --- Import reproducibility utils ---
# from utils.reproducibility import generate_run_manifest, get_file_sha256  # TODO: Create this

# --- Global Shutdown Event ---
shutdown_event = threading.Event()

# ---------------------------------------------------------------------------
# Immediate SIGINT handler
# ---------------------------------------------------------------------------
# Many runs spawn background threads *and* ProcessPool workers.  In practice
# the default graceful KeyboardInterrupt takes several seconds (or never
# finishes) while those workers clean up.  Users have asked for an
# *instant* abort when they hit Ctrl-C.  The new handler terminates all
# active child processes, sets the global shutdown flag (so long-running
# loops that catch KeyboardInterrupt can still see it), flushes the
# logging streams, and then exits the interpreter via os._exit which does
# not invoke cleanup handlers – but guarantees prompt return to the shell.
# ---------------------------------------------------------------------------

def _terminate_children() -> None:  # pragma: no cover – best effort clean-up
    try:
        for p in _mp.active_children():
            try:
                p.terminate()
            except Exception:
                pass
    except Exception:
        # Multiprocessing may not be initialised yet; ignore
        pass


def handle_sigint(sig, frame):  # type: ignore[override]
    print()  # newline after ^C so next prompt starts fresh
    logging.error("⌧  Ctrl-C received – aborting run immediately …")

    # Notify any cooperative loops
    shutdown_event.set()

    # Kill child processes (ProcessPoolExecutor workers, etc.)
    _terminate_children()

    # Flush logging to be sure the message appears
    for h in logging.getLogger().handlers:
        try:
            h.flush()
        except Exception:
            pass

    # Exit *now* – bypass atexit/finally blocks to avoid hangs
    _os._exit(130)  # 130 conventionally signals SIGINT termination

# --- Configuration Loading ---
def load_config(config_path):
    """Loads configuration from a YAML file."""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        logging.error(f"Configuration file not found: {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        logging.error(f"Error parsing configuration file: {e}")
        sys.exit(1)

# --- Logging Setup ---
def setup_logging(config):
    """Configures logging based on the config file."""
    log_config = config.get('logging', {})
    level = log_config.get('level', 'INFO').upper()
    log_format = log_config.get('format', '%(asctime)s - %(levelname)s - %(message)s')
    log_file = log_config.get('file')  # optional path for on-disk logging
    
    # Set Google SDK to ERROR level immediately to prevent AFC noise
    logging.getLogger("google").setLevel(logging.ERROR)
    logging.getLogger("google.genai").setLevel(logging.ERROR)
    logging.getLogger("google.genai.client").setLevel(logging.ERROR)
    
    logging.basicConfig(level=level, format=log_format, handlers=[logging.StreamHandler(sys.stdout)])

    # ------------------------------------------------------------------
    # Optional FileHandler – writes the same log stream to disk when the
    # user specifies ``logging.file`` in config.yaml (or passes it via env
    # injection).  Keeps stdout behaviour unchanged.
    # ------------------------------------------------------------------
    if log_file:
        try:
            fh = logging.FileHandler(log_file, encoding="utf-8")
            fh.setLevel(level)
            fh.setFormatter(logging.Formatter(log_format))
            logging.getLogger().addHandler(fh)
            logging.debug("File logging enabled → %s", log_file)
        except Exception as e:
            logging.warning("⚠ Could not set up file logging (%s): %s", log_file, e)

    # Silence noisy AFC-related logs emitted by external libraries
    class _AFCNoiseFilter(logging.Filter):
        _PHRASES = ("AFC is enabled", "AFC remote call", "max remote calls")

        def filter(self, record: logging.LogRecord) -> bool:  # type: ignore[override]
            msg = record.getMessage()
            return not any(p in msg for p in self._PHRASES)

    # Apply filter to root logger and specifically to google logger
    logging.getLogger().addFilter(_AFCNoiseFilter())
    logging.getLogger("google").addFilter(_AFCNoiseFilter())
    logging.getLogger("google.genai").addFilter(_AFCNoiseFilter())

    # Patch sys.stdout/stderr to filter out noisy AFC print statements outside logging
    import sys as _sys, io as _io

    class _FilteredStream(_io.TextIOBase):
        def __init__(self, original):
            self._orig = original

        def write(self, s):  # type: ignore[override]
            # Skip lines containing AFC noise phrases
            if any(p in s for p in _AFCNoiseFilter._PHRASES):
                return len(s)  # Pretend we wrote it to keep caller happy
            return self._orig.write(s)

        def flush(self):  # type: ignore[override]
            return self._orig.flush()

    _sys.stdout = _FilteredStream(_sys.stdout)
    _sys.stderr = _FilteredStream(_sys.stderr)

    # Reduce noise from HTTP libraries / Google SDK unless user sets DEBUG
    if level != "DEBUG":
        for noisy in ("google", "httpx", "urllib3"):
            logging.getLogger(noisy).setLevel(logging.ERROR)  # Changed to ERROR

# --- Main Orchestration ---
def run_pipeline(config: Dict, phase: str, coder_prefix: str, dimension: str, args: argparse.Namespace, shutdown_event: threading.Event):
    """Runs the full multi-coder analysis pipeline."""
    start_time = datetime.now()
    pipeline_timestamp = start_time.strftime("%Y%m%d_%H%M%S")
    logging.info(f"Starting pipeline run ({pipeline_timestamp}) for Phase: {phase}, Coder: {coder_prefix}, Dimension: {dimension}")

    # --- Path Setup & Initial Config Population ---
    try:
        # Create simple input/output structure for testing
        base_output_dir = Path("multi_coder_analysis") / "output" / phase / dimension / pipeline_timestamp
        base_output_dir.mkdir(parents=True, exist_ok=True)
        logging.info(f"Created output directory: {base_output_dir}")

        # --- Copy prompt directory verbatim for auditability (replaces old concatenation) ---
        try:
            src_prompt_dir = Path(args.prompts_dir)
            dst_prompt_dir = base_output_dir / "prompts"
            shutil.copytree(src_prompt_dir, dst_prompt_dir, dirs_exist_ok=True)
            logging.info("Copied prompt folder → %s", dst_prompt_dir)
            # NEW: also write a snapshot of all prompt files concatenated into one for auditability
            try:
                concat_filename = f"concatenated_prompts_{pipeline_timestamp}.txt"
                concatenate_prompts(src_prompt_dir, concat_filename, base_output_dir)
                logging.info("Generated concatenated prompts file → %s", base_output_dir / concat_filename)
            except Exception as _e:
                logging.warning("Could not generate concatenated prompts file: %s", _e)
            # Override prompts dir globally for ToT module
            try:
                _tot_mod.PROMPTS_DIR = src_prompt_dir.resolve()
                logging.info("Using custom prompts directory: %s", _tot_mod.PROMPTS_DIR)
            except Exception as _e:
                logging.warning("Could not override PROMPTS_DIR in run_multi_coder_tot: %s", _e)
        except Exception as e:
            logging.warning("Could not copy prompts folder: %s", e)

        # ------------------------------------------------------------------
        # Copy the exact regex catalogue used for this run into the output
        # directory for audit / reproducibility.
        # ------------------------------------------------------------------
        patterns_src = Path("multi_coder_analysis/regex/hop_patterns.yml")
        try:
            shutil.copy(patterns_src, base_output_dir / "hop_patterns.yml")
            logging.info("Copied hop_patterns.yml to output folder for auditability.")
        except Exception as e:
            logging.warning("Could not copy hop_patterns.yml (%s): %s", patterns_src, e)

        # Compiled_rules.txt no longer generated (redundant with hop_patterns.yml)

        # Determine input file source
        if args.input:
            # Use user-specified input file
            input_file = Path(args.input)
            if not input_file.exists():
                logging.error(f"Specified input file does not exist: {input_file}")
                raise FileNotFoundError(f"Input file not found: {input_file}")
            logging.info(f"Using specified input file: {input_file}")
        else:
            # Create a simple test input file if it doesn't exist (original behavior)
            input_file = Path("data") / f"{phase}_for_human.csv"
            if not input_file.exists():
                input_file.parent.mkdir(parents=True, exist_ok=True)
                # Create a minimal test CSV
                import pandas as pd
                test_data = pd.DataFrame({
                    'StatementID': ['TEST_001', 'TEST_002'],
                    'Statement Text': [
                        'The flu is so deadly that entire flocks are culled.',
                        'Health officials say the outbreak is fully under control.'
                    ]
                })
                test_data.to_csv(input_file, index=False)
                logging.info(f"Created test input file: {input_file}")
            else:
                logging.info(f"Using existing input file: {input_file}")

        # Update config with runtime paths
        config['runtime_input_dir'] = str(input_file.parent)
        config['runtime_output_dir'] = str(base_output_dir)
        config['runtime_phase'] = phase
        config['runtime_coder_prefix'] = coder_prefix
        config['runtime_dimension'] = dimension
        config['runtime_provider'] = args.provider
        config['individual_fallback'] = args.individual_fallback

    except Exception as e:
        logging.error(f"Error during path setup: {e}")
        raise

    # --- Pipeline Step 1: LLM Coding ---
    logging.info("--- Starting Step 1: LLM Coding ---")
    
    if args.use_tot:
        logging.info("Using Tree-of-Thought (ToT) method.")
        if hasattr(args, 'gemini_only') and args.gemini_only:
            logging.warning("--gemini-only flag is ignored when --use-tot is active.")
        
        try:
            raw_votes_path, majority_labels_path = run_coding_step_tot(
                config, 
                input_file,
                base_output_dir,
                limit=args.limit,
                start=args.start,
                end=args.end,
                concurrency=args.concurrency,
                model=args.model,
                provider=args.provider,
                batch_size=args.batch_size,
                regex_mode=args.regex_mode,
                shuffle_batches=args.shuffle_batches,
                skip_eval=args.no_eval,
                only_hop=args.only_hop,
                gold_standard_file=args.gold_standard,
            )
        except Exception as e:
            logging.error(f"Tree-of-Thought pipeline failed with error: {e}", exc_info=True)
            sys.exit(1)
            
    else:
        logging.info("Standard multi-model consensus method not yet implemented in this version.")
        logging.error("Please use --use-tot flag to run the Tree-of-Thought pipeline.")
        sys.exit(1)

    logging.info(f"LLM coding finished. Majority labels at: {majority_labels_path}")

    # TODO: Add merge and stats steps when those modules are implemented
    logging.info("Pipeline completed successfully!")

def re_evaluate_run(run_dir: Path, gold_standard_file: str) -> None:
    """Re-evaluate an existing pipeline run against a new gold standard."""
    import pandas as pd
    from datetime import datetime
    
    logging.info(f"Re-evaluating run: {run_dir}")
    logging.info(f"Using gold standard: {gold_standard_file}")
    
    # Load pipeline results
    model_labels_file = run_dir / "model_labels_tot.csv"
    df_results = pd.read_csv(model_labels_file, dtype={'StatementID': str})
    logging.info(f"Loaded {len(df_results)} pipeline results from {model_labels_file}")
    
    # Load new gold standard
    df_gold = pd.read_csv(gold_standard_file, dtype={'StatementID': str})
    
    # Verify gold standard file has required columns
    if 'StatementID' not in df_gold.columns:
        raise ValueError("Gold standard file must contain 'StatementID' column")
    if 'Gold Standard' not in df_gold.columns:
        raise ValueError("Gold standard file must contain 'Gold Standard' column")
    
    logging.info(f"Loaded {len(df_gold)} gold standard entries from {gold_standard_file}")
    
    # Merge results with new gold standard
    df_comparison = df_results.merge(
        df_gold[['StatementID', 'Gold Standard']], 
        on='StatementID', 
        how='left'
    )
    
    # Log merge statistics  
    total_results = len(df_comparison)
    has_gold = df_comparison['Gold Standard'].notna().sum()
    missing_gold = total_results - has_gold
    logging.info(f"Gold standard merge: {has_gold}/{total_results} results have gold labels, {missing_gold} missing")
    
    if missing_gold > 0:
        missing_ids = df_comparison[df_comparison['Gold Standard'].isna()]['StatementID'].tolist()
        logging.warning(f"Results missing gold standard labels: {missing_ids[:10]}{'...' if len(missing_ids) > 10 else ''}")
    
    # Filter to only results that have gold standard labels
    df_comparison = df_comparison[df_comparison['Gold Standard'].notna()].copy()
    
    if len(df_comparison) == 0:
        logging.error("No pipeline results match the new gold standard")
        return
    
    # Rename columns for consistency with existing evaluation code
    df_comparison = df_comparison.rename(columns={'Gold Standard': 'Gold_Standard'})
    
    # Add mismatch column
    df_comparison['Mismatch'] = df_comparison['Gold_Standard'] != df_comparison['Pipeline_Result']
    
    # Create timestamped comparison file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    comparison_path = run_dir / f"re_evaluation_{timestamp}_comparison.csv"
    df_comparison.to_csv(comparison_path, index=False)
    logging.info(f"Saved re-evaluation comparison to: {comparison_path}")
    
    # Import evaluation functions from run_multi_coder_tot
    try:
        from .run_multi_coder_tot import calculate_metrics, print_evaluation_report, print_mismatches, reorganize_traces_by_match_status
    except ImportError:
        from run_multi_coder_tot import calculate_metrics, print_evaluation_report, print_mismatches, reorganize_traces_by_match_status
    
    # Calculate metrics
    predictions = df_comparison['Pipeline_Result'].tolist()
    actuals = df_comparison['Gold_Standard'].tolist()
    metrics = calculate_metrics(predictions, actuals)
    
    # Print evaluation report
    print(f"\n🔄 RE-EVALUATION RESULTS")
    print(f"📁 Run directory: {run_dir}")
    print(f"📊 Gold standard: {gold_standard_file}")
    print(f"📈 Evaluated {len(df_comparison)} results")
    
    # Calculate mismatch counts
    mismatch_count = int(df_comparison["Mismatch"].sum())
    print(f"❌ Mismatches: {mismatch_count}/{len(df_comparison)} ({mismatch_count/len(df_comparison):.1%})")
    
    print(f"\n🎯 OVERALL ACCURACY: {metrics['accuracy']:.2%}")
    print(f"\n=== Per-Frame Precision / Recall ===")
    
    for frame, stats in metrics['frame_metrics'].items():
        if stats['tp'] + stats['fp'] + stats['fn'] == 0:
            continue  # Skip frames not present in the data
            
        p_str = f"{stats['precision']:.2%}" if stats['precision'] > 0 else "nan%"
        r_str = f"{stats['recall']:.2%}" if stats['recall'] > 0 else "0.00%"
        f1_str = f"{stats['f1']:.2%}" if stats['f1'] > 0 else "nan%"
        
        print(f"{frame:<12} P={p_str:<8} R={r_str:<8} F1={f1_str:<8} "
              f"(tp={stats['tp']}, fp={stats['fp']}, fn={stats['fn']})")
    
    # Print detailed mismatches
    if mismatch_count > 0:
        print_mismatches(df_comparison)
    else:
        print(f"🎉 Perfect match! All {len(df_comparison)} results consistent with gold standard.")
    
    # Reorganize trace files by new match/mismatch status
    trace_dir = run_dir / "traces_tot"
    if trace_dir.exists():
        logging.info("Reorganizing trace files by new match/mismatch status...")
        
        # Create timestamped trace directories for re-evaluation
        re_eval_trace_dir = run_dir / f"traces_tot_re_eval_{timestamp}"
        re_eval_trace_dir.mkdir(exist_ok=True)
        
        # Copy comparison dataframe with proper column names for reorganize function
        df_for_traces = df_comparison.copy()
        if 'Statement Text' not in df_for_traces.columns:
            # Add a placeholder if Statement Text is missing
            df_for_traces['Statement Text'] = df_for_traces['StatementID']
        
        # Copy original traces to re-evaluation directory, then reorganize
        import shutil
        if trace_dir.exists():
            for trace_file in trace_dir.glob("*.jsonl"):
                if not trace_file.name.startswith("consolidated_"):
                    shutil.copy2(trace_file, re_eval_trace_dir)
        
        reorganize_traces_by_match_status(re_eval_trace_dir, df_for_traces)
        logging.info(f"Trace files reorganized in: {re_eval_trace_dir}")
    
    print(f"\n✅ Re-evaluation complete!")
    print(f"📋 Comparison saved to: {comparison_path}")
    if trace_dir.exists():
        print(f"📂 Reorganized traces in: {re_eval_trace_dir}")

def main():
    """Main entry point for the analysis pipeline."""
    # Setup signal handling for graceful shutdown
    signal.signal(signal.SIGINT, handle_sigint)

    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(description="Run the multi-coder analysis pipeline.")
    parser.add_argument("--config", default="config.yaml", help="Path to configuration file")
    parser.add_argument("--phase", default="test", help="Analysis phase (e.g., pilot, validation, test)")
    parser.add_argument("--coder-prefix", default="model", help="Coder prefix for output files")
    parser.add_argument("--dimension", default="framing", help="Analysis dimension")
    parser.add_argument("--input", help="Path to input CSV file (overrides default input file generation)")
    parser.add_argument("--limit", type=int, help="Limit number of statements to process (for testing)")
    parser.add_argument("--start", type=int, help="Start index for processing (1-based, inclusive)")
    parser.add_argument("--end", type=int, help="End index for processing (1-based, inclusive)")
    parser.add_argument("--concurrency", type=int, default=1, help="Number of statements to process concurrently (default: 1)")
    parser.add_argument("--test", action="store_true", help="Run in test mode")
    parser.add_argument("--gemini-only", action="store_true", help="Use only Gemini models (ignored with --use-tot)")
    parser.add_argument(
        "--use-tot", 
        action="store_true",
        help="Activates the 12-hop Tree-of-Thought reasoning chain instead of the standard multi-model consensus method."
    )
    parser.add_argument("--model", default="models/gemini-2.5-flash-preview-04-17", help="Model to use for LLM calls (e.g., models/gemini-2.0-flash)")
    parser.add_argument("--provider", choices=["gemini", "openrouter"], default="gemini", help="LLM provider to use")
    parser.add_argument("--batch-size", "-b", type=int, default=1, help="Number of segments to process in a single LLM call per hop (default: 1)")
    parser.add_argument('--individual-fallback', action='store_true', help='Re-run mismatches individually for batch-sensitivity check')
    parser.add_argument('--regex-mode', choices=['live', 'shadow', 'off'], default='live', help='Regex layer mode: live (default), shadow (evaluate but do not short-circuit), off (disable regex)')
    parser.add_argument('--shuffle-batches', action='store_true', help='Randomly shuffle active segments before batching at each hop')

    # NEW: eight-order permutation sweep mode
    parser.add_argument('--permutations', action='store_true',
                        help='Run the eight-order permutation sweep instead of a single straight pass')

    # Parallel processes for permutation suite
    parser.add_argument('--perm-workers', type=int, default=1,
                        help='Number of permutations to execute in parallel (process-based). Default 1 (serial).')

    # Threshold for identifying low majority-ratio segments (used in permutation suite)
    parser.add_argument('--low-ratio-threshold', type=float, default=7,
                        help='Majority-label ratio below which a segment is considered low-confidence (default: 7)')

    # Skip evaluation even if Gold Standard column is present
    parser.add_argument('--no-eval', action='store_true',
                        help='Disable any comparison against the Gold Standard column. The pipeline will still run and output majority labels, but no accuracy metrics or mismatch files are created.')

    # Fallback pass: re-run permutations on low_ratio_segments.csv only
    parser.add_argument('--fallback-low-ratio', action='store_true',
                        help='After the normal permutation suite finishes, run an extra pass on low_ratio_segments.csv and write *_fallback files. Off by default.')

    # Custom prompts directory
    parser.add_argument('--prompts-dir', default=str(Path('multi_coder_analysis') / 'prompts'),
                        help='Path to prompts directory to use instead of the package default')

    # Diagnostic: run a single hop only (1-12)
    parser.add_argument('--only-hop', type=int, help='If set, run only the specified hop index (1-12) for diagnostic testing')

    # ------------------------------------------------------------------
    # NEW – Gold standard reference file
    # ------------------------------------------------------------------
    parser.add_argument('--gold-standard', help='Path to gold standard reference CSV file (optional - if not provided, will look for Gold Standard column in input file)')

    # ------------------------------------------------------------------
    # NEW – Re-evaluation of existing runs
    # ------------------------------------------------------------------
    parser.add_argument('--re-evaluate', help='Path to existing run output directory to re-evaluate against a new gold standard (use with --gold-standard)')

    # ------------------------------------------------------------------
    # NEW – Consensus strategy & self-consistency decoding (pipeline mode)
    # ------------------------------------------------------------------
    parser.add_argument('--consensus', default='final', choices=['hop', 'final'],
                        help="Consensus strategy: 'hop' = per-hop majority, 'final' = legacy end-of-tree vote (default)")

    parser.add_argument('--decode-mode', default='normal', choices=['normal', 'self-consistency'],
                        help='Decoding mode: normal (single deterministic path) or self-consistency')

    parser.add_argument('--votes', type=int, default=1, dest='sc_votes',
                        help='# paths/votes for self-consistency')

    parser.add_argument('--sc-rule', default='majority', choices=['majority', 'ranked', 'ranked-raw'],
                        help='Aggregation rule for self-consistency votes')

    parser.add_argument('--sc-temperature', type=float, default=0.7,
                        help='Sampling temperature for self-consistency')

    parser.add_argument('--sc-top-k', type=int, default=40,
                        help='top-k sampling cutoff (0 disables)')

    parser.add_argument('--sc-top-p', type=float, default=0.95,
                        help='nucleus sampling p-value')

    args = parser.parse_args()

    # --- Validate Arguments ---
    if args.start is not None and args.start < 1:
        logging.error("Start index must be >= 1")
        sys.exit(1)
    
    if args.end is not None and args.end < 1:
        logging.error("End index must be >= 1")
        sys.exit(1)
    
    if args.start is not None and args.end is not None and args.start > args.end:
        logging.error("Start index must be <= end index")
        sys.exit(1)
    
    if (args.start is not None or args.end is not None) and args.limit is not None:
        logging.error("Cannot use both --limit and --start/--end arguments together")
        sys.exit(1)

    if args.batch_size < 1:
        logging.error("--batch-size must be >= 1")
        sys.exit(1)

    if args.only_hop is not None and not (1 <= args.only_hop <= 12):
        logging.error("--only-hop must be between 1 and 12")
        sys.exit(1)

    # Validate re-evaluation arguments
    if args.re_evaluate:
        if not args.gold_standard:
            logging.error("--re-evaluate requires --gold-standard to specify the new gold standard file")
            sys.exit(1)
        
        re_eval_dir = Path(args.re_evaluate)
        if not re_eval_dir.exists() or not re_eval_dir.is_dir():
            logging.error(f"Re-evaluation directory does not exist: {args.re_evaluate}")
            sys.exit(1)
            
        # Check for required files
        model_labels_file = re_eval_dir / "model_labels_tot.csv"
        if not model_labels_file.exists():
            logging.error(f"Pipeline results file not found: {model_labels_file}")
            sys.exit(1)

    # --- Load Configuration ---
    if not os.path.exists(args.config):
        # Create a minimal config file if it doesn't exist
        default_config = {
            'logging': {'level': 'INFO'},
            'file_paths': {
                'file_patterns': {
                    'model_majority_output': '{phase}_model_labels.csv'
                }
            }
        }
        with open(args.config, 'w') as f:
            yaml.dump(default_config, f)
        logging.info(f"Created default config file: {args.config}")

    config = load_config(args.config)
    setup_logging(config)

    # ------------------------------------------------------------------
    # Re-evaluation mode: evaluate existing run against new gold standard
    # ------------------------------------------------------------------
    if args.re_evaluate:
        try:
            re_evaluate_run(Path(args.re_evaluate), args.gold_standard)
            return  # Exit after re-evaluation
        except Exception as e:
            logging.error(f"Re-evaluation failed: {e}", exc_info=True)
            sys.exit(1)

    # ------------------------------------------------------------------
    # Permutation mode short-circuits the normal pipeline and delegates
    # to the dedicated suite runner.
    # ------------------------------------------------------------------
    if args.permutations:
        # Package-relative first, then local fallback
        try:
            from .permutation_suite import run_permutation_suite  # type: ignore
        except ImportError:
            try:
                from multi_coder_analysis.permutation_suite import run_permutation_suite  # type: ignore
            except ImportError:
                try:
                    from permutation_suite import run_permutation_suite  # type: ignore
                except ImportError as err:
                    logging.error("Permutation suite could not be imported: %s", err)
                    sys.exit(1)

        try:
            perm_root = run_permutation_suite(config, args, shutdown_event)
        except Exception as e:
            logging.error("Permutation suite failed: %s", e, exc_info=True)
            sys.exit(1)

        # ------------------------------------------------------------------
        # Optional fallback permutation on low_ratio_segments.csv
        # ------------------------------------------------------------------
        if args.fallback_low_ratio:
            import pandas as _pd
            low_csv = Path(perm_root) / "low_ratio_segments.csv"
            if low_csv.exists():
                logging.info("🔁  Fallback permutation pass on %s", low_csv)
                try:
                    df_low = _pd.read_csv(low_csv)
                    run_permutation_suite(
                        config,
                        args,
                        shutdown_event,
                        override_df=df_low,
                        out_dir_suffix="fallback",
                    )
                except Exception as _e:
                    logging.error("Fallback permutation failed: %s", _e, exc_info=True)
            else:
                logging.warning("--fallback-low-ratio requested but %s not found", low_csv)
        return  # Skip the rest of main once permutations complete

    try:
        run_pipeline(config, args.phase, args.coder_prefix, args.dimension, args, shutdown_event)
    except Exception as e:
        logging.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main() 