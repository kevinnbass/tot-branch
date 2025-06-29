#!/usr/bin/env python3
"""
Script to run layout experiments with all 13 layouts.
Provides easy command-line interface for testing.
"""

import sys
import argparse
from pathlib import Path
import subprocess
import json
import pandas as pd
from datetime import datetime

# All available layouts
ALL_LAYOUTS = [
    # Original 5
    'standard', 'recency', 'sandwich', 'minimal_system', 'question_first',
    # New 8
    'hop_last', 'structured_json', 'segment_focus', 'instruction_first',
    'parallel_analysis', 'evidence_based', 'xml_structured', 'primacy_recency'
]

# Layouts optimized for different scenarios
LAYOUT_GROUPS = {
    'position_based': ['standard', 'recency', 'hop_last', 'question_first', 'primacy_recency'],
    'structure_based': ['structured_json', 'xml_structured', 'segment_focus', 'sandwich'],
    'process_based': ['evidence_based', 'parallel_analysis', 'instruction_first'],
    'minimal': ['minimal_system', 'hop_last', 'instruction_first'],
    'high_yield': ['hop_last', 'evidence_based', 'primacy_recency', 'structured_json', 'parallel_analysis']
}


def run_single_layout(layout, base_cmd, output_dir):
    """Run experiment with a single layout."""
    print(f"\n{'='*60}")
    print(f"Running layout: {layout}")
    print(f"{'='*60}")
    
    # Create layout-specific output directory
    layout_dir = output_dir / layout
    layout_dir.mkdir(parents=True, exist_ok=True)
    
    # Build command with layout
    cmd = base_cmd + ['--layout', layout]
    
    # Run the command
    start_time = datetime.now()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Save output
        with open(layout_dir / 'stdout.txt', 'w') as f:
            f.write(result.stdout)
        with open(layout_dir / 'stderr.txt', 'w') as f:
            f.write(result.stderr)
        
        # Extract metrics if available
        metrics = extract_metrics(result.stdout)
        metrics['layout'] = layout
        metrics['duration_seconds'] = duration
        metrics['exit_code'] = result.returncode
        
        # Save metrics
        with open(layout_dir / 'metrics.json', 'w') as f:
            json.dump(metrics, f, indent=2)
        
        if result.returncode == 0:
            print(f"✅ {layout} completed in {duration:.1f}s")
            if 'accuracy' in metrics:
                print(f"   Accuracy: {metrics['accuracy']:.3f}")
        else:
            print(f"❌ {layout} failed with exit code {result.returncode}")
            
        return metrics
        
    except Exception as e:
        print(f"❌ {layout} failed with error: {e}")
        return {'layout': layout, 'error': str(e)}


def extract_metrics(stdout):
    """Extract metrics from command output."""
    metrics = {}
    
    # Look for accuracy
    import re
    accuracy_match = re.search(r'OVERALL ACCURACY:\s*(\d+\.?\d*)%', stdout)
    if accuracy_match:
        metrics['accuracy'] = float(accuracy_match.group(1)) / 100
    
    # Look for F1 scores
    f1_matches = re.findall(r'(\w+)\s+P=\s*(\d+\.?\d*)%\s+R=\s*(\d+\.?\d*)%\s+F1=\s*(\d+\.?\d*)%', stdout)
    if f1_matches:
        metrics['frame_metrics'] = {}
        for frame, p, r, f1 in f1_matches:
            metrics['frame_metrics'][frame] = {
                'precision': float(p) / 100,
                'recall': float(r) / 100,
                'f1': float(f1) / 100
            }
    
    # Look for token usage
    token_match = re.search(r'Total tokens\s*:\s*(\d+)', stdout)
    if token_match:
        metrics['total_tokens'] = int(token_match.group(1))
    
    return metrics


def create_comparison_report(results, output_dir):
    """Create a comparison report of all layouts."""
    
    # Convert to DataFrame for analysis
    df = pd.DataFrame(results)
    
    # Sort by accuracy if available
    if 'accuracy' in df.columns:
        df = df.sort_values('accuracy', ascending=False)
    
    # Create report
    report = ["# Layout Experiment Results\n"]
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Summary table
    report.append("## Summary\n")
    report.append("| Layout | Accuracy | Duration (s) | Status |")
    report.append("|--------|----------|--------------|--------|")
    
    for _, row in df.iterrows():
        accuracy = f"{row.get('accuracy', 0):.3f}" if 'accuracy' in row else "N/A"
        duration = f"{row.get('duration_seconds', 0):.1f}" if 'duration_seconds' in row else "N/A"
        status = "✅" if row.get('exit_code', 1) == 0 else "❌"
        report.append(f"| {row['layout']} | {accuracy} | {duration} | {status} |")
    
    # Best performers
    if 'accuracy' in df.columns and len(df[df['accuracy'] > 0]) > 0:
        report.append("\n## Top 5 Performers\n")
        top5 = df[df['accuracy'] > 0].head(5)
        for i, (_, row) in enumerate(top5.iterrows(), 1):
            report.append(f"{i}. **{row['layout']}**: {row['accuracy']:.3f} accuracy")
    
    # Token efficiency
    if 'total_tokens' in df.columns:
        report.append("\n## Token Efficiency\n")
        token_df = df[df['total_tokens'] > 0].sort_values('total_tokens')
        report.append("| Layout | Total Tokens | Tokens per Accuracy |")
        report.append("|--------|--------------|---------------------|")
        for _, row in token_df.iterrows():
            if 'accuracy' in row and row['accuracy'] > 0:
                efficiency = row['total_tokens'] / row['accuracy']
                report.append(f"| {row['layout']} | {row['total_tokens']:,} | {efficiency:,.0f} |")
    
    # Save report
    report_text = '\n'.join(report)
    with open(output_dir / 'comparison_report.md', 'w') as f:
        f.write(report_text)
    
    # Save raw results
    df.to_csv(output_dir / 'results.csv', index=False)
    
    print(f"\n📊 Report saved to: {output_dir / 'comparison_report.md'}")
    
    return df


def main():
    parser = argparse.ArgumentParser(description='Run layout experiments')
    parser.add_argument('--layouts', nargs='+', choices=ALL_LAYOUTS + list(LAYOUT_GROUPS.keys()),
                        help='Layouts to test (or group names: position_based, structure_based, etc.)')
    parser.add_argument('--all', action='store_true', help='Test all 13 layouts')
    parser.add_argument('--output-dir', type=Path, 
                        default=Path('output/layout_experiments') / datetime.now().strftime('%Y%m%d_%H%M%S'),
                        help='Output directory for results')
    parser.add_argument('--sequential', action='store_true', 
                        help='Run layouts sequentially instead of using --layout-experiment')
    
    # Pass through arguments for the main command
    parser.add_argument('--input', required=True, help='Input CSV file')
    parser.add_argument('--gold-standard', help='Gold standard file (defaults to same as input)')
    parser.add_argument('--provider', default='gemini', help='LLM provider')
    parser.add_argument('--model', default='models/gemini-2.5-flash-preview-04-17', help='Model to use')
    parser.add_argument('--concurrency', type=int, default=20, help='Concurrency level')
    parser.add_argument('--batch-size', type=int, default=200, help='Batch size')
    parser.add_argument('--start', type=int, help='Start index')
    parser.add_argument('--end', type=int, help='End index')
    parser.add_argument('--regex-mode', default='live', choices=['live', 'shadow', 'off'])
    
    args = parser.parse_args()
    
    # Determine which layouts to test
    if args.all:
        layouts = ALL_LAYOUTS
    elif args.layouts:
        layouts = []
        for item in args.layouts:
            if item in LAYOUT_GROUPS:
                layouts.extend(LAYOUT_GROUPS[item])
            else:
                layouts.append(item)
        # Remove duplicates while preserving order
        layouts = list(dict.fromkeys(layouts))
    else:
        print("Error: Specify --all or --layouts")
        return 1
    
    print(f"Testing {len(layouts)} layouts: {', '.join(layouts)}")
    
    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    # Build base command
    base_cmd = [
        sys.executable, '-m', 'multi_coder_analysis.main',
        '--use-tot',
        '--input', str(args.input),
        '--provider', args.provider,
        '--model', args.model,
        '--concurrency', str(args.concurrency),
        '--batch-size', str(args.batch_size),
        '--regex-mode', args.regex_mode
    ]
    
    # Add gold standard
    if args.gold_standard:
        base_cmd.extend(['--gold-standard', str(args.gold_standard)])
    else:
        base_cmd.extend(['--gold-standard', str(args.input)])
    
    # Add range if specified
    if args.start:
        base_cmd.extend(['--start', str(args.start)])
    if args.end:
        base_cmd.extend(['--end', str(args.end)])
    
    # Run experiments
    results = []
    
    if args.sequential:
        # Run each layout individually
        for layout in layouts:
            result = run_single_layout(layout, base_cmd, args.output_dir)
            results.append(result)
    else:
        # Use built-in --layout-experiment flag
        print("\nRunning parallel layout experiment...")
        cmd = base_cmd + ['--layout-experiment', '--layout-workers', str(min(len(layouts), 5))]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            print("Experiment completed!")
            
            # Parse results from experiment output
            # (This would need to be implemented based on actual output format)
            
        except Exception as e:
            print(f"Error running experiment: {e}")
            return 1
    
    # Create comparison report
    if results:
        create_comparison_report(results, args.output_dir)
    
    print(f"\n✅ Experiment complete! Results in: {args.output_dir}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main()) 