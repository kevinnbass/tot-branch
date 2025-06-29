#!/usr/bin/env python3
"""Test a single layout to verify functionality."""

import sys
import subprocess
from pathlib import Path
from datetime import datetime

def test_single_layout(layout='standard'):
    """Test a single layout with minimal parameters."""
    
    print(f"Testing layout: {layout}")
    
    # Create output directory
    output_dir = Path('output/layout_test') / datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Build command
    cmd = [
        sys.executable, '-m', 'multi_coder_analysis.main',
        '--use-tot',
        '--input', 'multi_coder_analysis/data/gold_standard_preliminary.csv',
        '--gold-standard', 'multi_coder_analysis/data/gold_standard_preliminary.csv',
        '--provider', 'gemini',
        '--model', 'models/gemini-2.5-flash-preview-04-17',
        '--concurrency', '5',
        '--batch-size', '5',
        '--regex-mode', 'live',
        '--start', '1',
        '--end', '2',  # Just test 2 items
        '--layout', layout,
        '--output', str(output_dir / f'{layout}_results.jsonl')
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Save output
        with open(output_dir / 'stdout.txt', 'w') as f:
            f.write(result.stdout)
        with open(output_dir / 'stderr.txt', 'w') as f:
            f.write(result.stderr)
        
        if result.returncode == 0:
            print(f"✅ Success! Output in: {output_dir}")
            # Check if output file was created
            output_file = output_dir / f'{layout}_results.jsonl'
            if output_file.exists():
                print(f"   Output file size: {output_file.stat().st_size} bytes")
            else:
                print("   ⚠️  No output file created")
        else:
            print(f"❌ Failed with exit code: {result.returncode}")
            print(f"   Error output: {result.stderr[:500]}...")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == '__main__':
    layout = sys.argv[1] if len(sys.argv) > 1 else 'standard'
    test_single_layout(layout) 