#!/usr/bin/env python3
"""
Fix Ctrl+C handling to ensure proper shutdown of all running experiments.
"""

import sys
from pathlib import Path
import re

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))


def fix_layout_experiment_shutdown():
    """Improve shutdown handling in layout_experiment.py"""
    
    file_path = Path("multi_coder_analysis/layout_experiment.py")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace the run_layout_experiment function to add shutdown checking
    old_function = '''def run_layout_experiment(
    config: Dict,
    args,
    layout: str,
    output_base: Path,
) -> Dict:
    """Run a single layout experiment."""
    
    # Create layout-specific output directory
    layout_dir = output_base / layout
    layout_dir.mkdir(parents=True, exist_ok=True)
    
    logging.info(f"🧪 Starting layout experiment: {layout}")
    
    start_time = datetime.now()
    
    try:
        # Run the ToT pipeline with this specific layout
        _, results_path = run_coding_step_tot('''
    
    new_function = '''def run_layout_experiment(
    config: Dict,
    args,
    layout: str,
    output_base: Path,
    shutdown_event: threading.Event = None,
) -> Dict:
    """Run a single layout experiment."""
    
    # Create layout-specific output directory
    layout_dir = output_base / layout
    layout_dir.mkdir(parents=True, exist_ok=True)
    
    logging.info(f"🧪 Starting layout experiment: {layout}")
    
    start_time = datetime.now()
    
    # Check for early shutdown
    if shutdown_event and shutdown_event.is_set():
        return {
            'layout': layout,
            'status': 'skipped',
            'error': 'Shutdown requested before start',
            'duration_seconds': 0,
        }
    
    try:
        # Run the ToT pipeline with this specific layout
        _, results_path = run_coding_step_tot('''
    
    content = content.replace(old_function, new_function)
    
    # Update the run_with_shutdown_check function
    old_check = '''    # Create a thread-local storage for shutdown checking
    def run_with_shutdown_check(layout):
        if shutdown_event.is_set():
            return {
                'layout': layout,
                'status': 'skipped',
                'error': 'Shutdown requested',
            }
        return run_layout_experiment(config, args, layout, experiment_dir)'''
    
    new_check = '''    # Create a thread-local storage for shutdown checking
    def run_with_shutdown_check(layout):
        if shutdown_event.is_set():
            return {
                'layout': layout,
                'status': 'skipped',
                'error': 'Shutdown requested',
            }
        return run_layout_experiment(config, args, layout, experiment_dir, shutdown_event)'''
    
    content = content.replace(old_check, new_check)
    
    # Add better exception handling in the main loop
    old_loop = '''            # Check for shutdown
            if shutdown_event.is_set():
                logging.info("Shutdown requested, cancelling remaining experiments...")
                for f in future_to_layout:
                    f.cancel()
                break'''
    
    new_loop = '''            # Check for shutdown
            if shutdown_event.is_set():
                logging.info("Shutdown requested, cancelling remaining experiments...")
                # Cancel all pending futures
                for f in future_to_layout:
                    if not f.done():
                        f.cancel()
                # Force shutdown the executor
                executor.shutdown(wait=False)
                break'''
    
    content = content.replace(old_loop, new_loop)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Updated layout_experiment.py with better shutdown handling")


def fix_tot_runner_shutdown():
    """Add shutdown event checking in the ToT runner"""
    
    file_path = Path("multi_coder_analysis/run_multi_coder_tot.py")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add shutdown_event parameter to run_coding_step_tot
    old_signature = '''def run_coding_step_tot(
    config: Dict,
    input_csv_path: Path,
    output_dir: Path,
    limit: Optional[int] = None,
    start: Optional[int] = None,
    end: Optional[int] = None,
    concurrency: int = 1,
    model: str = "DEFAULT_MODEL",
    provider: str = "gemini",
    batch_size: int = 1,
    regex_mode: str = "live",
    *,
    router: bool = False,
    template: str = "legacy",
    layout: str = "standard",  # NEW: Layout parameter
    shuffle_batches: bool = False,
    shuffle_segments: bool = False,  # NEW: Fine-grained segment shuffling
    skip_eval: bool = False,
    only_hop: Optional[int] = None,
    gold_standard_file: Optional[str] = None,
    print_summary: bool = True,
) -> Tuple[None, Path]:'''
    
    new_signature = '''def run_coding_step_tot(
    config: Dict,
    input_csv_path: Path,
    output_dir: Path,
    limit: Optional[int] = None,
    start: Optional[int] = None,
    end: Optional[int] = None,
    concurrency: int = 1,
    model: str = "DEFAULT_MODEL",
    provider: str = "gemini",
    batch_size: int = 1,
    regex_mode: str = "live",
    *,
    router: bool = False,
    template: str = "legacy",
    layout: str = "standard",  # NEW: Layout parameter
    shuffle_batches: bool = False,
    shuffle_segments: bool = False,  # NEW: Fine-grained segment shuffling
    skip_eval: bool = False,
    only_hop: Optional[int] = None,
    gold_standard_file: Optional[str] = None,
    print_summary: bool = True,
    shutdown_event: threading.Event = None,  # NEW: Shutdown event
) -> Tuple[None, Path]:'''
    
    content = content.replace(old_signature, new_signature)
    
    # Add shutdown checking in the batch processing loop
    # Find the hop processing loop
    hop_loop_pattern = r'(for hop_idx in (?:hop_range|range\(1, 13\)):\s*\n)'
    
    def add_shutdown_check(match):
        return match.group(1) + '''        # Check for shutdown
        if shutdown_event and shutdown_event.is_set():
            logging.info(f"Shutdown requested at hop {hop_idx}, stopping processing...")
            break
        
'''
    
    content = re.sub(hop_loop_pattern, add_shutdown_check, content)
    
    # Also add shutdown check in the single-segment processing loop
    single_loop_pattern = r'(for _, row in tqdm\(\s*df\.iterrows\(\),.*?\):\s*\n)'
    
    def add_single_shutdown(match):
        return match.group(1) + '''                # Check for shutdown
                if shutdown_event and shutdown_event.is_set():
                    logging.info("Shutdown requested, stopping processing...")
                    break
                
'''
    
    content = re.sub(single_loop_pattern, add_single_shutdown, content, flags=re.DOTALL)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Updated run_multi_coder_tot.py with shutdown event handling")


def fix_main_signal_handler():
    """Improve the signal handler in main.py"""
    
    file_path = Path("multi_coder_analysis/main.py")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace the handle_sigint function with a more robust version
    old_handler = '''def handle_sigint(sig, frame):  # type: ignore[override]
    """
    Forcefully terminate all child processes and exit immediately.
    Does not wait for graceful shutdown.
    """
    shutdown_event.set()
    
    # Kill all child processes
    _terminate_children()
    
    # Flush outputs
    sys.stdout.flush()
    sys.stderr.flush()
    
    # Force exit with SIGINT code
    _os._exit(130)  # 130 conventionally signals SIGINT termination'''
    
    new_handler = '''def handle_sigint(sig, frame):  # type: ignore[override]
    """
    Forcefully terminate all child processes and exit immediately.
    Does not wait for graceful shutdown.
    """
    print("\\n\\n🛑 Interrupt received! Shutting down all experiments...\\n", flush=True)
    
    # Set the shutdown event
    shutdown_event.set()
    
    # Give a brief moment for threads to see the shutdown event
    import time
    time.sleep(0.5)
    
    # Kill all child processes
    _terminate_children()
    
    # Flush outputs
    sys.stdout.flush()
    sys.stderr.flush()
    
    # Force exit with SIGINT code
    print("\\n💀 Force exiting...\\n", flush=True)
    _os._exit(130)  # 130 conventionally signals SIGINT termination'''
    
    content = content.replace(old_handler, new_handler)
    
    # Update the run_layout_experiments call to pass shutdown_event
    old_call = '''        _, results_path = run_coding_step_tot(
            config=config,
            input_csv_path=Path(args.input),
            output_dir=layout_dir,
            limit=args.limit,
            start=args.start,
            end=args.end,
            concurrency=args.concurrency,
            model=args.model,
            provider=args.provider,
            batch_size=args.batch_size,
            regex_mode=args.regex_mode,
            router=args.router if hasattr(args, 'router') else False,
            template=args.template if hasattr(args, 'template') else 'legacy',
            layout=layout,  # Specific layout for this experiment
            shuffle_batches=args.shuffle_batches if hasattr(args, 'shuffle_batches') else False,
            shuffle_segments=args.shuffle_segments if hasattr(args, 'shuffle_segments') else False,
            skip_eval=True,  # Skip individual evaluation, we'll do it at the end
            only_hop=args.only_hop if hasattr(args, 'only_hop') else None,
            gold_standard_file=args.gold_standard,
            print_summary=False,  # Reduce output noise
        )'''
    
    new_call = '''        _, results_path = run_coding_step_tot(
            config=config,
            input_csv_path=Path(args.input),
            output_dir=layout_dir,
            limit=args.limit,
            start=args.start,
            end=args.end,
            concurrency=args.concurrency,
            model=args.model,
            provider=args.provider,
            batch_size=args.batch_size,
            regex_mode=args.regex_mode,
            router=args.router if hasattr(args, 'router') else False,
            template=args.template if hasattr(args, 'template') else 'legacy',
            layout=layout,  # Specific layout for this experiment
            shuffle_batches=args.shuffle_batches if hasattr(args, 'shuffle_batches') else False,
            shuffle_segments=args.shuffle_segments if hasattr(args, 'shuffle_segments') else False,
            skip_eval=True,  # Skip individual evaluation, we'll do it at the end
            only_hop=args.only_hop if hasattr(args, 'only_hop') else None,
            gold_standard_file=args.gold_standard,
            print_summary=False,  # Reduce output noise
            shutdown_event=shutdown_event if 'shutdown_event' in locals() else None,
        )'''
    
    # Find and replace in layout_experiment.py
    layout_file = Path("multi_coder_analysis/layout_experiment.py")
    with open(layout_file, 'r', encoding='utf-8') as f:
        layout_content = f.read()
    
    layout_content = layout_content.replace(old_call, new_call)
    
    with open(layout_file, 'w', encoding='utf-8') as f:
        f.write(layout_content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Updated main.py with improved signal handling")


def main():
    """Apply all shutdown handling fixes"""
    print("Fixing Ctrl+C handling for layout experiments...")
    print("=" * 60)
    
    print("\n1. Updating layout_experiment.py...")
    fix_layout_experiment_shutdown()
    
    print("\n2. Updating run_multi_coder_tot.py...")
    fix_tot_runner_shutdown()
    
    print("\n3. Updating main.py signal handler...")
    fix_main_signal_handler()
    
    print("\n✅ All shutdown handling fixes applied!")
    print("\nNow when you press Ctrl+C:")
    print("- A clear shutdown message will be displayed")
    print("- All running experiments will be cancelled")
    print("- The process will exit immediately")
    print("\nThe shutdown will work at any point during execution.")


if __name__ == "__main__":
    main() 