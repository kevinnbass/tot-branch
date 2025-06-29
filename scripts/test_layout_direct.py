#!/usr/bin/env python3
"""
Direct test of layout functionality by importing the ToT function.
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the ToT function
from multi_coder_analysis.run_multi_coder_tot import run_coding_step_tot

def test_layout(layout='standard'):
    """Test a specific layout directly."""
    
    print(f"Testing layout: {layout}")
    
    # Create output directory
    output_dir = Path('output/layout_test_direct') / datetime.now().strftime('%Y%m%d_%H%M%S') / layout
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Minimal config
    config = {
        'runtime_provider': 'gemini',
        'individual_fallback': False,
    }
    
    # Input file
    input_file = Path('multi_coder_analysis/data/gold_standard_preliminary.csv')
    
    # Check if file exists and has Gold Standard column
    import pandas as pd
    print(f"Checking input file: {input_file}")
    if input_file.exists():
        df_check = pd.read_csv(input_file, nrows=5)
        print(f"Columns: {df_check.columns.tolist()}")
        print(f"First row:")
        print(df_check.iloc[0])
    
    try:
        # Run the ToT with specific layout
        _, results_path = run_coding_step_tot(
            config=config,
            input_csv_path=input_file,
            output_dir=output_dir,
            limit=2,  # Just test 2 items
            start=None,
            end=None,
            concurrency=1,
            model='models/gemini-2.5-flash-preview-04-17',
            provider='gemini',
            batch_size=1,
            regex_mode='live',
            router=False,
            template='legacy',
            layout=layout,  # Test this specific layout
            shuffle_batches=False,
            shuffle_segments=False,
            skip_eval=False,
            only_hop=None,
            gold_standard_file=None,  # Let it use the Gold Standard column from input
            print_summary=True,
        )
        
        print(f"Success! Results at: {results_path}")
        
        # Check if comparison file exists
        comparison_file = output_dir / 'comparison.csv'
        if comparison_file.exists():
            df = pd.read_csv(comparison_file)
            if 'Mismatch' in df.columns:
                accuracy = 1 - (df['Mismatch'].sum() / len(df))
                print(f"   Accuracy: {accuracy:.3f}")
        
    except Exception as e:
        print(f"Failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    layout = sys.argv[1] if len(sys.argv) > 1 else 'standard'
    test_layout(layout) 