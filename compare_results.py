#!/usr/bin/env python3
"""
Compare pipeline results against gold standard

Usage:
  python compare_results.py [run_folder] [gold_standard_file]
  python compare_results.py --help

Examples:
  python compare_results.py multi_coder_analysis/output/test/framing/20250624_203239 multi_coder_analysis/data/gold_standard_preliminary.csv
  python compare_results.py multi_coder_analysis/output/test/framing/20250624_203239
"""

import pandas as pd
import sys
import argparse
from pathlib import Path

def compare_results(pipeline_file, gold_standard_file, output_file):
    """Compare pipeline results against gold standard and generate comparison report"""
    
    print(f"Loading pipeline results from: {pipeline_file}")
    # Load pipeline results 
    pipeline_df = pd.read_csv(pipeline_file)
    print(f"Pipeline results: {len(pipeline_df)} rows")
    
    print(f"Loading gold standard from: {gold_standard_file}")
    # Load gold standard
    gold_df = pd.read_csv(gold_standard_file)
    print(f"Gold standard: {len(gold_df)} rows")
    
    # Merge on StatementID
    print("Merging datasets...")
    merged_df = pd.merge(
        pipeline_df[['StatementID', 'Pipeline_Result']], 
        gold_df[['StatementID', 'Statement Text', 'Gold Standard']], 
        on='StatementID', 
        how='inner'
    )
    print(f"Merged dataset: {len(merged_df)} rows")
    
    # Add comparison columns
    merged_df['Mismatch'] = merged_df['Pipeline_Result'] != merged_df['Gold Standard']
    
    # Calculate statistics
    total_statements = len(merged_df)
    mismatches = merged_df['Mismatch'].sum()
    matches = total_statements - mismatches
    accuracy = matches / total_statements if total_statements > 0 else 0
    
    print("\n=== COMPARISON RESULTS ===")
    print(f"Total statements compared: {total_statements}")
    print(f"Matches: {matches}")
    print(f"Mismatches: {mismatches}")
    print(f"Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
    
    # Breakdown by category
    print("\n=== GOLD STANDARD BREAKDOWN ===")
    gold_counts = merged_df['Gold Standard'].value_counts()
    for category, count in gold_counts.items():
        print(f"{category}: {count}")
    
    print("\n=== PIPELINE RESULTS BREAKDOWN ===")
    pipeline_counts = merged_df['Pipeline_Result'].value_counts()
    for category, count in pipeline_counts.items():
        print(f"{category}: {count}")
    
    # Confusion matrix
    print("\n=== CONFUSION MATRIX ===")
    confusion = pd.crosstab(
        merged_df['Gold Standard'], 
        merged_df['Pipeline_Result'], 
        margins=True
    )
    print(confusion)
    
    # Category-wise accuracy
    print("\n=== CATEGORY-WISE ACCURACY ===")
    for category in merged_df['Gold Standard'].unique():
        category_df = merged_df[merged_df['Gold Standard'] == category]
        category_matches = (category_df['Pipeline_Result'] == category_df['Gold Standard']).sum()
        category_total = len(category_df)
        category_accuracy = category_matches / category_total if category_total > 0 else 0
        print(f"{category}: {category_matches}/{category_total} = {category_accuracy:.4f} ({category_accuracy*100:.2f}%)")
    
    # Show sample mismatches
    print("\n=== SAMPLE MISMATCHES (first 10) ===")
    mismatches_df = merged_df[merged_df['Mismatch']]
    if len(mismatches_df) > 0:
        for idx, row in mismatches_df.head(10).iterrows():
            print(f"\nStatementID: {row['StatementID']}")
            print(f"Statement: {row['Statement Text'][:100]}...")
            print(f"Gold Standard: {row['Gold Standard']}")
            print(f"Pipeline Result: {row['Pipeline_Result']}")
    else:
        print("No mismatches found!")
    
    # Save detailed comparison
    print(f"\nSaving detailed comparison to: {output_file}")
    
    # Reorder columns for output
    output_df = merged_df[['StatementID', 'Statement Text', 'Gold Standard', 'Pipeline_Result', 'Mismatch']]
    output_df.to_csv(output_file, index=False)
    
    print(f"Comparison complete! Results saved to: {output_file}")
    
    return {
        'total': total_statements,
        'matches': matches,
        'mismatches': mismatches,
        'accuracy': accuracy
    }

def main():
    parser = argparse.ArgumentParser(
        description='Compare pipeline results against gold standard',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python compare_results.py multi_coder_analysis/output/test/framing/20250624_203239 multi_coder_analysis/data/gold_standard_preliminary.csv
  python compare_results.py multi_coder_analysis/output/test/framing/20250624_203239
  python compare_results.py --run-folder multi_coder_analysis/output/test/framing/20250624_203239 --gold-standard multi_coder_analysis/data/gold_standard_preliminary.csv
        """
    )
    
    parser.add_argument(
        'run_folder', 
        nargs='?',
        help='Path to the run folder containing model_labels_tot.csv (e.g., multi_coder_analysis/output/test/framing/20250624_203239)'
    )
    
    parser.add_argument(
        'gold_standard_file', 
        nargs='?',
        help='Path to the gold standard CSV file (e.g., multi_coder_analysis/data/gold_standard_preliminary.csv)'
    )
    
    parser.add_argument(
        '--run-folder', 
        dest='run_folder_named',
        help='Path to the run folder containing model_labels_tot.csv'
    )
    
    parser.add_argument(
        '--gold-standard', 
        dest='gold_standard_named',
        help='Path to the gold standard CSV file'
    )
    
    parser.add_argument(
        '--output',
        help='Output file path for the detailed comparison (optional)'
    )
    
    args = parser.parse_args()
    
    # Determine run folder (positional or named argument)
    run_folder = args.run_folder or args.run_folder_named
    if not run_folder:
        # Default to the most recent run
        run_folder = "multi_coder_analysis/output/test/framing/20250624_203239"
        print(f"No run folder specified, using default: {run_folder}")
    
    # Determine gold standard file (positional or named argument)
    gold_standard_file = args.gold_standard_file or args.gold_standard_named
    if not gold_standard_file:
        # Default gold standard
        gold_standard_file = "multi_coder_analysis/data/gold_standard_preliminary.csv"
        print(f"No gold standard file specified, using default: {gold_standard_file}")
    
    # Construct pipeline file path
    run_path = Path(run_folder)
    pipeline_file = run_path / "model_labels_tot.csv"
    
    # Validate files exist
    if not pipeline_file.exists():
        print(f"Error: Pipeline results file not found: {pipeline_file}")
        print(f"Expected to find model_labels_tot.csv in: {run_path}")
        sys.exit(1)
    
    if not Path(gold_standard_file).exists():
        print(f"Error: Gold standard file not found: {gold_standard_file}")
        sys.exit(1)
    
    # Determine output file
    if args.output:
        output_file = args.output
    else:
        output_file = run_path / "new_comparison_with_gold_standard.csv"
    
    print(f"Run folder: {run_folder}")
    print(f"Pipeline file: {pipeline_file}")
    print(f"Gold standard file: {gold_standard_file}")
    print(f"Output file: {output_file}")
    print("-" * 50)
    
    try:
        results = compare_results(str(pipeline_file), gold_standard_file, str(output_file))
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 