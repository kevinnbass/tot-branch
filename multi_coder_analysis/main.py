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

# --- Import step functions from other modules --- #
# from run_multi_coder import run_coding_step  # TODO: Create this for standard pipeline
# Support both "python multi_coder_analysis/main.py" (script) and
# "python -m multi_coder_analysis.main" (module) invocation styles.
try:
    from .run_multi_coder_tot import run_coding_step_tot  # package-relative when executed as module
except ImportError:
    from run_multi_coder_tot import run_coding_step_tot  # direct import when executed as script
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

# --- Signal Handler ---
def handle_sigint(sig, frame):
    print()  # Print newline after ^C
    logging.warning("SIGINT received. Attempting graceful shutdown...")
    shutdown_event.set()
    # Force immediate termination so the user regains control promptly.
    # Using SystemExit keeps cleanup handlers (atexit) intact but stops
    # further execution even if worker threads are busy.
    raise SystemExit(130)  # 130 is the conventional exit code for SIGINT

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

        # --- Concatenate Prompts into run-specific output directory ---
        logging.info("--- Concatenating prompt files ---")
        prompt_concat_path = concatenate_prompts(
            prompts_dir="multi_coder_analysis/prompts",
            output_file=f"concatenated_prompts_{pipeline_timestamp}.txt",
            target_dir=base_output_dir,
        )
        if prompt_concat_path:
            logging.info(f"Concatenated prompts saved to: {prompt_concat_path}")
        else:
            logging.warning("Prompt concatenation failed, but continuing with pipeline...")

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

        # ------------------------------------------------------------------
        # ALSO dump the *compiled* regex table (one line per rule) so that
        # reviewers can see *exactly* what the engine ran, after any
        # compile-time rewrites/downgrades.  Creates an easy-to-read TSV
        # called "compiled_rules.txt" in the same output folder.
        # ------------------------------------------------------------------
        try:
            from multi_coder_analysis import regex_rules as _rr

            dump_path = base_output_dir / "compiled_rules.txt"
            with dump_path.open("w", encoding="utf-8") as fh:
                fh.write("Hop\tMode\tFrame\tRuleName\tRegex\n")

                # Use RAW_RULES because it contains the compiled PatternInfo
                # objects (post-processing) in the original ordering.
                for r in _rr.RAW_RULES:
                    pattern_str = getattr(r.yes_regex, "pattern", str(r.yes_regex))
                    fh.write(f"{r.hop}\t{r.mode}\t{r.yes_frame or ''}\t{r.name}\t{pattern_str}\n")

            logging.info("Compiled regex table dumped → %s", dump_path)
        except Exception as e:
            logging.warning("Could not write compiled_rules.txt: %s", e)

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

    # Skip evaluation even if Gold Standard column is present
    parser.add_argument('--no-eval', action='store_true',
                        help='Disable any comparison against the Gold Standard column. The pipeline will still run and output majority labels, but no accuracy metrics or mismatch files are created.')

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
            run_permutation_suite(config, args, shutdown_event)
        except Exception as e:
            logging.error("Permutation suite failed: %s", e, exc_info=True)
            sys.exit(1)
        return  # Skip the rest of main once permutations complete

    try:
        run_pipeline(config, args.phase, args.coder_prefix, args.dimension, args, shutdown_event)
    except Exception as e:
        logging.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main() 