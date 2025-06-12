#!/usr/bin/env python3
"""
Gold Standard CSV Relabeling Script

This script fixes specific gold standard entries by changing them to "Neutral"
to address bare-negation and capability cases that were incorrectly labeled.
"""

import pandas as pd
import os

def fix_gold_standard():
    """
    Load gold_standard.csv, apply label fixes, and save the result.
    """
    
    # Input and output file paths
    input_file = "data/gold_standard.csv"
    output_file = "data/gold_standard_fixed.csv"
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found!")
        return False
    
    # 1. Load the CSV
    print(f"Loading {input_file}...")
    df = pd.read_csv(input_file)
    print(f"Loaded {len(df)} rows")
    
    # 2. Define the fixes - StatementID -> new_label mappings
    fixes = {
        "seg_v5_012_1003_chunk0": "Neutral",  # "The cases do not present an immediate public health concern"
        "seg_v5_14_1002_chunk0": "Neutral",   # "Human infections do occur after close contact..."  
        "seg_v5_3_1002_chunk0": "Neutral",    # "These avian influenza detections do not present..."
        "seg_v5_7_1009_chunk0": "Neutral",    # "Recent detections do not present..."
        "seg_v5_14_1008_chunk0": "Neutral",   # "These avian influenza detections do not present..."
        "seg_v5_10_1006_chunk0": "Neutral",   # "The USDA says avian influenza does not present..."
        "seg_v5_6_1000_chunk0": "Neutral",    # "Birds from the flocks will not enter the food system"
        "seg_v5_7_1000_chunk0": "Neutral",    # [Another similar statement]
        "seg_v5_8_1000_chunk0": "Neutral",    # [Another similar statement]
        "seg_v5_6_1004_chunk0": "Neutral",    # [Another similar statement] 
        "seg_v5_13_1006_chunk0": "Neutral",   # [Another similar statement]
        "seg_v5_8_1007_chunk0": "Neutral",    # [Another similar statement]
        "seg_v5_54_101_chunk0": "Neutral",    # "It's arguably more humane than letting them die..."
        "seg_v5_20_101_chunk0": "Neutral"     # [Another similar capability statement]
    }
    
    # 3. Apply the fixes
    print(f"\nApplying {len(fixes)} label fixes...")
    
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
        
        # Apply the change
        df.loc[mask, 'Gold Standard'] = new_label
        changes_made += 1
        
        print(f"  {statement_id}: {current_label} → {new_label}")
    
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
    success = fix_gold_standard()
    exit(0 if success else 1) 