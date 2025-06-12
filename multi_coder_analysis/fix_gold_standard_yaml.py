#!/usr/bin/env python3
"""
Gold Standard CSV Relabeling Script (YAML-based)

This script fixes gold standard entries by reading fix configurations
from fixes_config.yaml, making it easy to maintain and extend corrections.
"""

import pandas as pd
import yaml
import os
from datetime import datetime

def load_fixes_config(config_file="fixes_config.yaml"):
    """
    Load the fixes configuration from YAML file.
    
    Args:
        config_file (str): Path to the YAML configuration file
        
    Returns:
        dict: StatementID -> new_label mappings
    """
    if not os.path.exists(config_file):
        print(f"Error: Configuration file {config_file} not found!")
        return {}
    
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        return config.get('fixes', {})
    except Exception as e:
        print(f"Error reading configuration file: {e}")
        return {}

def fix_gold_standard_from_yaml(config_file="fixes_config.yaml", 
                                input_file="data/gold_standard.csv",
                                output_file=None):
    """
    Load gold_standard.csv, apply fixes from YAML config, and save the result.
    
    Args:
        config_file (str): Path to YAML configuration file
        input_file (str): Path to input CSV file
        output_file (str): Path to output CSV file (None for in-place)
    """
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found!")
        return False
    
    # Set default output file if not specified
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"data/gold_standard_fixed_{timestamp}.csv"
    
    # 1. Load the fixes configuration
    print(f"Loading fixes from {config_file}...")
    fixes = load_fixes_config(config_file)
    
    if not fixes:
        print("No fixes found in configuration file!")
        return False
    
    print(f"Found {len(fixes)} fixes to apply")
    
    # 2. Load the CSV
    print(f"Loading {input_file}...")
    df = pd.read_csv(input_file)
    print(f"Loaded {len(df)} rows")
    
    # 3. Apply the fixes
    print(f"\nApplying label fixes...")
    
    changes_made = 0
    for statement_id, new_label in fixes.items():
        # Find rows matching this StatementID
        mask = df['StatementID'] == statement_id
        matching_rows = df[mask]
        
        if len(matching_rows) == 0:
            print(f"Warning: StatementID '{statement_id}' not found in CSV")
            continue
        elif len(matching_rows) > 1:
            print(f"Warning: Multiple rows found for StatementID '{statement_id}'")
            
        # Get the current label for reporting
        current_label = df.loc[mask, 'Gold Standard'].iloc[0] if len(matching_rows) > 0 else "NOT_FOUND"
        
        # Apply the change only if different
        if current_label != new_label:
            df.loc[mask, 'Gold Standard'] = new_label
            changes_made += 1
            print(f"  {statement_id}: {current_label} → {new_label}")
        else:
            print(f"  {statement_id}: already {current_label} (no change)")
    
    # 4. Save the result
    print(f"\nSaving {output_file}...")
    df.to_csv(output_file, index=False)
    
    # 5. Summary
    print(f"\nSummary:")
    print(f"  - Processed {len(df)} total rows")
    print(f"  - Applied {changes_made} label changes")
    print(f"  - Output saved to: {output_file}")
    
    # Show final label distribution
    label_counts = df['Gold Standard'].value_counts()
    print(f"\nFinal label distribution:")
    for label, count in label_counts.items():
        print(f"  {label}: {count}")
    
    return True

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix gold standard labels using YAML configuration')
    parser.add_argument('--config', default='fixes_config.yaml', 
                       help='Path to YAML configuration file')
    parser.add_argument('--input', default='data/gold_standard.csv',
                       help='Input CSV file path')
    parser.add_argument('--output', default=None,
                       help='Output CSV file path (default: timestamped file)')
    parser.add_argument('--in-place', action='store_true',
                       help='Modify the input file in place')
    
    args = parser.parse_args()
    
    output_file = args.input if args.in_place else args.output
    
    success = fix_gold_standard_from_yaml(
        config_file=args.config,
        input_file=args.input, 
        output_file=output_file
    )
    
    exit(0 if success else 1) 