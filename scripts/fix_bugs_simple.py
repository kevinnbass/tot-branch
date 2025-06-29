#!/usr/bin/env python3
"""
Simple script to fix the core bugs in the prompt layout experiment code.
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
        lines = f.readlines()
    
    # Find the run_tot_chain_batch function signature
    for i, line in enumerate(lines):
        if line.strip().startswith("def run_tot_chain_batch("):
            # Look for the end of the function signature
            j = i
            while j < len(lines) and not lines[j].strip().endswith("):"):
                j += 1
            
            # Check if ranked and max_candidates are already there
            signature_text = ''.join(lines[i:j+1])
            if "ranked:" not in signature_text and "max_candidates:" not in signature_text:
                # Insert before the closing parenthesis
                lines[j] = lines[j].rstrip()[:-2] + "\n    ranked: bool = False,  # NEW: Ranking parameter\n    max_candidates: int = 5,  # NEW: Max candidates for ranking\n):\n"
                print("✅ Added ranked and max_candidates parameters to run_tot_chain_batch")
                
                # Write back
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                return
            else:
                print("ℹ️  ranked and max_candidates already present in run_tot_chain_batch")
                return
    
    print("⚠️  Could not find run_tot_chain_batch function")


def create_thread_safe_cache():
    """Create a simple thread-safe cache implementation."""
    
    cache_code = '''#!/usr/bin/env python3
"""
Thread-safe caching implementation for prompt layout experiments.
"""

import hashlib
import pickle
import threading
from pathlib import Path
from typing import Dict, Optional, Any
import os
import time


class ThreadSafeCache:
    """Thread-safe cache implementation."""
    
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
            
        try:
            with open(cache_path, 'rb') as f:
                value = pickle.load(f)
                # Update memory cache
                with self._lock:
                    self._memory_cache[key] = value
                return value
        except Exception:
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
                pickle.dump(value, f)
            
            # Atomic rename
            temp_path.replace(cache_path)
            return True
            
        except Exception:
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


def add_layout_metrics_to_improved_script():
    """Add layout-specific metrics to the improved experiment script."""
    
    metrics_code = '''

def calculate_layout_metrics(
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
    
    improved_script = Path("scripts/experiment_prompt_layouts_improved.py")
    
    if improved_script.exists():
        # Read current content
        with open(improved_script, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if metrics functions already exist
        if "calculate_layout_metrics" not in content:
            # Find where to insert (before main function)
            insert_pos = content.find("def main():")
            if insert_pos > 0:
                # Insert the new functions
                new_content = content[:insert_pos] + metrics_code + "\n" + content[insert_pos:]
                
                with open(improved_script, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                print("✅ Added layout-specific metrics functions")
            else:
                print("⚠️  Could not find insertion point for metrics functions")
        else:
            print("ℹ️  Layout metrics functions already exist")
    else:
        print("⚠️  Improved script not found")


def main():
    """Run all fixes."""
    print("Applying core bug fixes...")
    print("=" * 60)
    
    print("\n1. Fixing missing ranked and max_candidates parameters...")
    fix_ranked_and_max_candidates()
    
    print("\n2. Creating thread-safe cache implementation...")
    create_thread_safe_cache()
    
    print("\n3. Adding layout-specific metrics...")
    add_layout_metrics_to_improved_script()
    
    print("\n✅ Core fixes applied successfully!")
    print("\nNew files created:")
    print("  - scripts/thread_safe_cache.py")
    print("\nModified files:")
    print("  - multi_coder_analysis/run_multi_coder_tot.py (if needed)")
    print("  - scripts/experiment_prompt_layouts_improved.py (if needed)")


if __name__ == "__main__":
    main() 