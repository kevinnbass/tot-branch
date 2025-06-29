#!/usr/bin/env python3
"""
Script to fix additional bugs in the prompt layout experiment code.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))


def fix_ranked_and_max_candidates():
    """Fix the missing ranked and max_candidates parameters in run_tot_chain_batch."""
    
    file_path = Path("multi_coder_analysis/run_multi_coder_tot.py")
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add ranked and max_candidates to run_tot_chain_batch signature
    old_signature = """def run_tot_chain_batch(
    df: pd.DataFrame,
    provider_name: str,
    trace_dir: Path,
    model: str,
    batch_size: int = 10,
    concurrency: int = 1,
    token_accumulator: dict = None,
    token_lock: threading.Lock = None,
    temperature: float = TEMPERATURE,
    *,
    template: str = "legacy",
    shuffle_batches: bool = False,
    shuffle_segments: bool = False,  # NEW: Fine-grained segment shuffling
    hop_range: Optional[list[int]] = None,
    layout: str = "standard",  # NEW: Layout parameter
) -> List[HopContext]:"""
    
    new_signature = """def run_tot_chain_batch(
    df: pd.DataFrame,
    provider_name: str,
    trace_dir: Path,
    model: str,
    batch_size: int = 10,
    concurrency: int = 1,
    token_accumulator: dict = None,
    token_lock: threading.Lock = None,
    temperature: float = TEMPERATURE,
    *,
    template: str = "legacy",
    shuffle_batches: bool = False,
    shuffle_segments: bool = False,  # NEW: Fine-grained segment shuffling
    hop_range: Optional[list[int]] = None,
    layout: str = "standard",  # NEW: Layout parameter
    ranked: bool = False,  # NEW: Ranking parameter
    max_candidates: int = 5,  # NEW: Max candidates for ranking
) -> List[HopContext]:"""
    
    if old_signature in content:
        content = content.replace(old_signature, new_signature)
        print("✅ Fixed run_tot_chain_batch signature")
    else:
        print("⚠️  Could not find exact signature match, may need manual fix")
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Updated {file_path}")


def add_thread_safe_cache():
    """Add thread-safe caching implementation."""
    
    cache_code = '''#!/usr/bin/env python3
"""
Thread-safe caching implementation for prompt layout experiments.
"""

import hashlib
import pickle
import threading
from pathlib import Path
from typing import Dict, Optional, Any
import fcntl
import os
import time


class ThreadSafeCache:
    """Thread-safe cache implementation using file locking."""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._memory_cache: Dict[str, Any] = {}
        
    def _get_cache_path(self, key: str) -> Path:
        """Get the file path for a cache key."""
        return self.cache_dir / f"{key}.pkl"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache (memory first, then disk)."""
        # Check memory cache first
        with self._lock:
            if key in self._memory_cache:
                return self._memory_cache[key]
        
        # Check disk cache
        cache_path = self._get_cache_path(key)
        if not cache_path.exists():
            return None
            
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with open(cache_path, 'rb') as f:
                    if os.name != 'nt':  # File locking not supported on Windows
                        fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                    try:
                        value = pickle.load(f)
                        # Update memory cache
                        with self._lock:
                            self._memory_cache[key] = value
                        return value
                    finally:
                        if os.name != 'nt':
                            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            except (IOError, EOFError) as e:
                if attempt < max_retries - 1:
                    time.sleep(0.1 * (attempt + 1))  # Exponential backoff
                else:
                    return None
        
        return None
    
    def set(self, key: str, value: Any) -> bool:
        """Set value in cache (both memory and disk)."""
        # Update memory cache
        with self._lock:
            self._memory_cache[key] = value
        
        # Write to disk
        cache_path = self._get_cache_path(key)
        temp_path = cache_path.with_suffix('.tmp')
        
        try:
            with open(temp_path, 'wb') as f:
                if os.name != 'nt':
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    pickle.dump(value, f)
                finally:
                    if os.name != 'nt':
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            
            # Atomic rename
            temp_path.replace(cache_path)
            return True
            
        except Exception as e:
            # Clean up temp file if it exists
            if temp_path.exists():
                temp_path.unlink()
            return False
    
    def clear(self):
        """Clear all cache entries."""
        with self._lock:
            self._memory_cache.clear()
        
        # Remove all cache files
        for cache_file in self.cache_dir.glob("*.pkl"):
            try:
                cache_file.unlink()
            except Exception:
                pass


def generate_cache_key(segment_text: str, hop_idx: int, layout: str, model: str) -> str:
    """Generate a cache key for a specific segment/hop/layout/model combination."""
    content = f"{segment_text}:{hop_idx}:{layout}:{model}"
    return hashlib.md5(content.encode()).hexdigest()
'''
    
    # Write the thread-safe cache implementation
    cache_file = Path("scripts/thread_safe_cache.py")
    with open(cache_file, 'w', encoding='utf-8') as f:
        f.write(cache_code)
    
    print(f"✅ Created thread-safe cache implementation at {cache_file}")


def add_layout_specific_metrics():
    """Add code to track layout-specific metrics."""
    
    metrics_code = '''def calculate_layout_metrics(
    layout: str,
    sys_prompt: str,
    user_prompt: str,
    segment_text: str,
    response_time: float,
) -> Dict[str, Any]:
    """Calculate metrics specific to each layout type."""
    
    metrics = {
        "layout": layout,
        "sys_prompt_length": len(sys_prompt),
        "user_prompt_length": len(user_prompt),
        "total_prompt_length": len(sys_prompt) + len(user_prompt),
        "response_time": response_time,
    }
    
    # Layout-specific metrics
    if layout == "recency":
        # Check segment position in user prompt
        segment_pos = user_prompt.find(segment_text)
        if segment_pos >= 0:
            metrics["segment_position_ratio"] = segment_pos / len(user_prompt)
        else:
            metrics["segment_position_ratio"] = -1
    
    elif layout == "sandwich":
        # Check for quick check section
        import re
        quick_check = re.search(r"QUICK DECISION CHECK", user_prompt, re.IGNORECASE)
        metrics["has_quick_check"] = quick_check is not None
        if quick_check:
            metrics["quick_check_position"] = quick_check.start() / len(user_prompt)
    
    elif layout == "minimal_system":
        # Ratio of system to user prompt
        metrics["system_to_user_ratio"] = len(sys_prompt) / (len(user_prompt) + 1)
    
    elif layout == "question_first":
        # Check question position
        import re
        question = re.search(r"### Question Q\\d+", user_prompt)
        if question:
            metrics["question_position_ratio"] = question.start() / len(user_prompt)
        else:
            metrics["question_position_ratio"] = -1
    
    return metrics


def aggregate_layout_metrics(all_metrics: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    """Aggregate layout-specific metrics across all experiments."""
    
    from collections import defaultdict
    import numpy as np
    
    layout_aggregates = defaultdict(lambda: defaultdict(list))
    
    for metric in all_metrics:
        layout = metric["layout"]
        for key, value in metric.items():
            if key != "layout" and isinstance(value, (int, float)):
                layout_aggregates[layout][key].append(value)
    
    # Calculate statistics
    layout_stats = {}
    for layout, metrics in layout_aggregates.items():
        layout_stats[layout] = {}
        for metric_name, values in metrics.items():
            if values:
                layout_stats[layout][metric_name] = {
                    "mean": np.mean(values),
                    "std": np.std(values),
                    "min": np.min(values),
                    "max": np.max(values),
                    "median": np.median(values),
                }
    
    return layout_stats
'''
    
    # Append to the improved experiment script
    improved_script = Path("scripts/experiment_prompt_layouts_improved.py")
    
    # Read current content
    with open(improved_script, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find where to insert (before main function)
    insert_pos = content.find("def main():")
    if insert_pos > 0:
        # Insert the new functions
        new_content = content[:insert_pos] + metrics_code + "\n\n" + content[insert_pos:]
        
        with open(improved_script, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ Added layout-specific metrics functions")
    else:
        print("⚠️  Could not find insertion point for metrics functions")


def add_error_recovery():
    """Add better error recovery and retry logic."""
    
    recovery_code = '''
import time
from typing import Callable, Any, Optional
import logging


def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
) -> Any:
    """
    Retry a function with exponential backoff.
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        backoff_factor: Factor to multiply delay by after each retry
        exceptions: Tuple of exceptions to catch and retry
    
    Returns:
        Result of the function call
    
    Raises:
        The last exception if all retries fail
    """
    delay = initial_delay
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return func()
        except exceptions as e:
            last_exception = e
            if attempt < max_retries:
                logging.warning(
                    f"Attempt {attempt + 1}/{max_retries + 1} failed: {e}. "
                    f"Retrying in {delay:.1f} seconds..."
                )
                time.sleep(delay)
                delay *= backoff_factor
            else:
                logging.error(f"All {max_retries + 1} attempts failed.")
    
    raise last_exception


def safe_file_operation(
    operation: str,
    file_path: Path,
    content: Optional[str] = None,
    mode: str = 'r',
    encoding: str = 'utf-8',
) -> Optional[str]:
    """
    Safely perform file operations with retry and error handling.
    
    Args:
        operation: 'read' or 'write'
        file_path: Path to the file
        content: Content to write (for write operations)
        mode: File open mode
        encoding: File encoding
    
    Returns:
        File content for read operations, None for write operations
    """
    def _operation():
        if operation == 'read':
            with open(file_path, mode, encoding=encoding) as f:
                return f.read()
        elif operation == 'write':
            # Write to temp file first
            temp_path = file_path.with_suffix('.tmp')
            with open(temp_path, mode, encoding=encoding) as f:
                f.write(content)
            # Atomic rename
            temp_path.replace(file_path)
            return None
        else:
            raise ValueError(f"Unknown operation: {operation}")
    
    try:
        return retry_with_backoff(
            _operation,
            max_retries=3,
            exceptions=(IOError, OSError),
        )
    except Exception as e:
        logging.error(f"Failed to {operation} file {file_path}: {e}")
        raise


class ExperimentCheckpoint:
    """Save and restore experiment progress."""
    
    def __init__(self, checkpoint_dir: Path):
        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_file = self.checkpoint_dir / "checkpoint.json"
    
    def save(self, state: Dict[str, Any]):
        """Save checkpoint state."""
        import json
        content = json.dumps(state, indent=2)
        safe_file_operation('write', self.checkpoint_file, content)
    
    def load(self) -> Optional[Dict[str, Any]]:
        """Load checkpoint state."""
        import json
        if not self.checkpoint_file.exists():
            return None
        try:
            content = safe_file_operation('read', self.checkpoint_file)
            return json.loads(content)
        except Exception:
            return None
    
    def clear(self):
        """Clear checkpoint."""
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()
'''
    
    # Create error recovery utilities
    recovery_file = Path("scripts/error_recovery.py")
    with open(recovery_file, 'w', encoding='utf-8') as f:
        f.write(recovery_code)
    
    print(f"✅ Created error recovery utilities at {recovery_file}")


def add_experiment_monitoring():
    """Add real-time monitoring capabilities."""
    
    monitoring_code = '''#!/usr/bin/env python3
"""
Real-time monitoring for prompt layout experiments.
"""

import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import threading
from collections import defaultdict


class ExperimentMonitor:
    """Monitor experiment progress in real-time."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.monitor_file = output_dir / "monitor.json"
        self.start_time = time.time()
        self.experiments: Dict[str, Dict] = {}
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._monitor_thread = None
    
    def start(self):
        """Start monitoring thread."""
        self._monitor_thread = threading.Thread(target=self._monitor_loop)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
    
    def stop(self):
        """Stop monitoring thread."""
        self._stop_event.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
    
    def update_experiment(self, layout: str, model: str, status: str, **kwargs):
        """Update experiment status."""
        key = f"{layout}_{model}"
        with self._lock:
            if key not in self.experiments:
                self.experiments[key] = {
                    "layout": layout,
                    "model": model,
                    "start_time": time.time(),
                }
            
            self.experiments[key].update({
                "status": status,
                "last_update": time.time(),
                **kwargs
            })
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while not self._stop_event.is_set():
            try:
                self._write_status()
                time.sleep(5)  # Update every 5 seconds
            except Exception as e:
                print(f"Monitor error: {e}")
    
    def _write_status(self):
        """Write current status to file."""
        with self._lock:
            status = {
                "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
                "elapsed_seconds": time.time() - self.start_time,
                "total_experiments": len(self.experiments),
                "completed": sum(1 for e in self.experiments.values() if e.get("status") == "completed"),
                "failed": sum(1 for e in self.experiments.values() if e.get("status") == "failed"),
                "running": sum(1 for e in self.experiments.values() if e.get("status") == "running"),
                "experiments": self.experiments,
            }
        
        # Calculate statistics
        completed_exps = [e for e in self.experiments.values() if e.get("status") == "completed"]
        if completed_exps:
            accuracies = [e.get("accuracy", 0) for e in completed_exps]
            durations = [e.get("duration_seconds", 0) for e in completed_exps]
            
            status["statistics"] = {
                "mean_accuracy": sum(accuracies) / len(accuracies),
                "best_accuracy": max(accuracies),
                "worst_accuracy": min(accuracies),
                "mean_duration": sum(durations) / len(durations),
            }
            
            # Best configuration so far
            best_exp = max(completed_exps, key=lambda e: e.get("accuracy", 0))
            status["best_so_far"] = {
                "layout": best_exp["layout"],
                "model": best_exp["model"],
                "accuracy": best_exp.get("accuracy", 0),
            }
        
        # Write to file
        with open(self.monitor_file, 'w', encoding='utf-8') as f:
            json.dump(status, f, indent=2)
    
    def get_summary(self) -> Dict:
        """Get current summary statistics."""
        with self._lock:
            return {
                "total": len(self.experiments),
                "completed": sum(1 for e in self.experiments.values() if e.get("status") == "completed"),
                "failed": sum(1 for e in self.experiments.values() if e.get("status") == "failed"),
                "running": sum(1 for e in self.experiments.values() if e.get("status") == "running"),
            }


def create_dashboard_html(monitor_file: Path, output_file: Path):
    """Create a simple HTML dashboard for monitoring."""
    
    html_template = """<!DOCTYPE html>
<html>
<head>
    <title>Experiment Monitor</title>
    <meta http-equiv="refresh" content="10">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .status { background: #f0f0f0; padding: 10px; border-radius: 5px; margin: 10px 0; }
        .completed { color: green; }
        .failed { color: red; }
        .running { color: blue; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #4CAF50; color: white; }
        tr:nth-child(even) { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <h1>Prompt Layout Experiment Monitor</h1>
    <div id="content">Loading...</div>
    <script>
        function loadStatus() {
            fetch('monitor.json')
                .then(response => response.json())
                .then(data => {
                    let html = '<div class="status">';
                    html += `<p>Started: ${data.start_time}</p>`;
                    html += `<p>Elapsed: ${Math.floor(data.elapsed_seconds / 60)} minutes</p>`;
                    html += `<p>Total: ${data.total_experiments} | `;
                    html += `<span class="completed">Completed: ${data.completed}</span> | `;
                    html += `<span class="running">Running: ${data.running}</span> | `;
                    html += `<span class="failed">Failed: ${data.failed}</span></p>`;
                    
                    if (data.best_so_far) {
                        html += `<p><strong>Best so far:</strong> ${data.best_so_far.layout} with ${data.best_so_far.model} - Accuracy: ${data.best_so_far.accuracy.toFixed(3)}</p>`;
                    }
                    html += '</div>';
                    
                    html += '<h2>Experiments</h2>';
                    html += '<table>';
                    html += '<tr><th>Layout</th><th>Model</th><th>Status</th><th>Accuracy</th><th>Duration</th></tr>';
                    
                    for (let key in data.experiments) {
                        let exp = data.experiments[key];
                        let statusClass = exp.status;
                        let accuracy = exp.accuracy ? exp.accuracy.toFixed(3) : '-';
                        let duration = exp.duration_seconds ? exp.duration_seconds.toFixed(1) + 's' : '-';
                        
                        html += `<tr>`;
                        html += `<td>${exp.layout}</td>`