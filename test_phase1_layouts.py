#!/usr/bin/env python
"""
Test script to verify Phase 1 minimal system layout variations work correctly.
"""

import sys
import subprocess
from pathlib import Path
import os

def test_layout(layout_name):
    """Test a single layout with a small sample."""
    print(f"\n{'='*60}")
    print(f"Testing layout: {layout_name}")
    print('='*60)
    
    cmd = [
        sys.executable, "-m", "multi_coder_analysis.main",
        "--use-tot",
        "--input", "multi_coder_analysis/data/gold_standard_preliminary.csv",
        "--gold-standard", "multi_coder_analysis/data/gold_standard_preliminary.csv",
        "--provider", "gemini",
        "--model", "models/gemini-2.0-flash",
        "--concurrency", "1",
        "--batch-size", "10",
        "--regex-mode", "live",
        "--start", "1",
        "--end", "10",  # Small sample for testing
        "--layout-experiment",
        "--layout-workers", "1"
    ]
    
    # Set environment variable to test specific layout
    env = dict(os.environ)
    env['TOT_LAYOUTS'] = layout_name
    
    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {layout_name} completed successfully")
            # Extract accuracy from output
            for line in result.stdout.split('\n'):
                if 'Accuracy' in line and layout_name in line:
                    print(f"   {line.strip()}")
        else:
            print(f"❌ {layout_name} failed with return code {result.returncode}")
            print("STDERR:", result.stderr[-500:])  # Last 500 chars of error
    except Exception as e:
        print(f"❌ {layout_name} failed with exception: {e}")

def main():
    """Test all Phase 1 layouts."""
    phase1_layouts = [
        'minimal_system',  # Baseline
        'minimal_segment_first',
        'minimal_question_twice',
        'minimal_json_segment',
        'minimal_parallel_criteria',
        'minimal_hop_sandwich'
    ]
    
    print("Testing Phase 1 minimal system layout variations...")
    print(f"Testing {len(phase1_layouts)} layouts")
    
    for layout in phase1_layouts:
        test_layout(layout)
    
    print("\n" + "="*60)
    print("Phase 1 layout testing complete!")
    print("="*60)

if __name__ == "__main__":
    main() 