#!/usr/bin/env python3
"""
Fixed layout experiment runner that tests layouts individually.
"""

import sys
import subprocess
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import concurrent.futures
from typing import Dict, List, Any, Optional
import re
import os

# All available layouts
ALL_LAYOUTS = [
    'standard', 'recency', 'sandwich', 'minimal_system', 'question_first',
    'hop_last', 'structured_json', 'segment_focus', 'instruction_first',
    'parallel_analysis', 'evidence_based', 'xml_structured', 'primacy_recency'
]

def run_single_layout(layout: str, base_args: List[str], output_dir: Path) -> Dict[str, Any]:
    """Run a single layout experiment."""
    print(f"\n{'='*60}")
    print(f"Testing layout: {layout}")
    print(f"{'='*60}")
    
    # Create layout-specific output directory
    layout_dir = output_dir / layout
    layout_dir.mkdir(parents=True, exist_ok=True)
    
    # Build command - use main.py with layout environment variable
    env = os.environ.copy()
    env['TOT_LAYOUT'] = layout  # Pass layout via environment variable
    
    cmd = [
        sys.executable, 
        '-m', 'multi_coder_analysis.main'
    ] + base_args
    
    start_time = datetime.now()
    try:
        # Run the command with modified environment
        result = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=str(Path.cwd()))
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Save outputs
        stdout_file = layout_dir / 'stdout.txt'
        stderr_file = layout_dir / 'stderr.txt'
        
        with open(stdout_file, 'w', encoding='utf-8') as f:
            f.write(result.stdout)
        with open(stderr_file, 'w', encoding='utf-8') as f:
            f.write(result.stderr)
        
        # Extract metrics from output
        metrics = {
            'layout': layout,
            'duration_seconds': duration,
            'exit_code': result.returncode,
            'status': 'success' if result.returncode == 0 else 'failed'
        }
        
        # Parse accuracy from output
        accuracy_match = re.search(r'OVERALL ACCURACY:\s*(\d+\.?\d*)%', result.stdout)
        if accuracy_match:
            metrics['accuracy'] = float(accuracy_match.group(1)) / 100
        
        # Parse F1 scores
        f1_matches = re.findall(r'(\w+)\s+P=\s*(\d+\.?\d*)%\s+R=\s*(\d+\.?\d*)%\s+F1=\s*(\d+\.?\d*)%', result.stdout)
        if f1_matches:
            metrics['frame_metrics'] = {}
            for frame, p, r, f1 in f1_matches:
                metrics['frame_metrics'][frame] = {
                    'precision': float(p) / 100,
                    'recall': float(r) / 100,
                    'f1': float(f1) / 100
                }
        
        # Count tokens
        token_match = re.search(r'Total tokens used:\s*(\d+)', result.stdout)
        if token_match:
            metrics['total_tokens'] = int(token_match.group(1))
        
        # Look for output files in the standard location
        # The main.py creates output in multi_coder_analysis/output/test/framing/[timestamp]/
        # We need to find the most recent directory
        output_base = Path('multi_coder_analysis/output/test/framing')
        if output_base.exists():
            # Find the most recent directory
            dirs = sorted([d for d in output_base.iterdir() if d.is_dir()], 
                         key=lambda x: x.stat().st_mtime, reverse=True)
            if dirs:
                latest_dir = dirs[0]
                # Copy relevant files to our layout directory
                for file_pattern in ['model_labels_tot.csv', 'comparison.csv', '*.jsonl']:
                    for src_file in latest_dir.glob(file_pattern):
                        dst_file = layout_dir / src_file.name
                        import shutil
                        shutil.copy2(src_file, dst_file)
                
                # Check if comparison.csv exists to get accuracy
                comparison_file = layout_dir / 'comparison.csv'
                if comparison_file.exists():
                    df_comp = pd.read_csv(comparison_file)
                    if 'Mismatch' in df_comp.columns:
                        accuracy = 1 - (df_comp['Mismatch'].sum() / len(df_comp))
                        metrics['accuracy'] = accuracy
        
        # Save metrics
        with open(layout_dir / 'metrics.json', 'w') as f:
            json.dump(metrics, f, indent=2)
        
        if result.returncode == 0:
            print(f"✅ {layout} completed in {duration:.1f}s")
            if 'accuracy' in metrics:
                print(f"   Accuracy: {metrics['accuracy']:.3f}")
        else:
            print(f"❌ {layout} failed with exit code {result.returncode}")
            print(f"   Error: {result.stderr[:200]}...")
            
        return metrics
        
    except Exception as e:
        print(f"❌ {layout} failed with exception: {e}")
        return {
            'layout': layout,
            'status': 'error',
            'error': str(e),
            'duration_seconds': (datetime.now() - start_time).total_seconds()
        }


def create_summary_report(results: List[Dict], output_dir: Path):
    """Create a summary report of all layout experiments."""
    
    # Convert to DataFrame
    df = pd.DataFrame(results)
    
    # Save raw results
    df.to_csv(output_dir / 'all_results.csv', index=False)
    
    # Create markdown report
    report = ["# Layout Experiment Results\n"]
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Summary table
    report.append("## Summary\n")
    report.append("| Layout | Status | Accuracy | Duration (s) |")
    report.append("|--------|--------|----------|--------------|")
    
    # Sort by accuracy if available
    if 'accuracy' in df.columns:
        df = df.sort_values('accuracy', ascending=False, na_position='last')
    
    for _, row in df.iterrows():
        status = "✅" if row.get('status') == 'success' else "❌"
        accuracy = f"{row.get('accuracy', 0):.3f}" if pd.notna(row.get('accuracy')) else "N/A"
        duration = f"{row.get('duration_seconds', 0):.1f}"
        report.append(f"| {row['layout']} | {status} | {accuracy} | {duration} |")
    
    # Best performers
    successful = df[df['status'] == 'success']
    if len(successful) > 0 and 'accuracy' in successful.columns:
        report.append("\n## Top Performers\n")
        top = successful.nlargest(5, 'accuracy')
        for i, (_, row) in enumerate(top.iterrows(), 1):
            report.append(f"{i}. **{row['layout']}**: {row['accuracy']:.3f} accuracy")
    
    # Save report
    with open(output_dir / 'summary_report.md', 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    print(f"\n📊 Summary report saved to: {output_dir / 'summary_report.md'}")
    
    return df


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Run layout experiments')
    parser.add_argument('--layouts', nargs='+', choices=ALL_LAYOUTS,
                        help='Specific layouts to test')
    parser.add_argument('--all', action='store_true', 
                        help='Test all layouts')
    parser.add_argument('--parallel', type=int, default=1,
                        help='Number of layouts to run in parallel')
    parser.add_argument('--output-dir', type=Path,
                        default=Path('output/layout_experiments') / datetime.now().strftime('%Y%m%d_%H%M%S'),
                        help='Output directory')
    
    # ToT arguments
    parser.add_argument('--input', required=True, help='Input CSV file')
    parser.add_argument('--gold-standard', help='Gold standard file')
    parser.add_argument('--provider', default='gemini', help='LLM provider')
    parser.add_argument('--model', default='models/gemini-2.0-flash-exp', help='Model to use')
    parser.add_argument('--concurrency', type=int, default=20, help='Concurrency level')
    parser.add_argument('--batch-size', type=int, default=200, help='Batch size')
    parser.add_argument('--start', type=int, help='Start index')
    parser.add_argument('--end', type=int, help='End index')
    parser.add_argument('--regex-mode', default='live', choices=['live', 'shadow', 'off'])
    
    args = parser.parse_args()
    
    # Determine layouts to test
    if args.all:
        layouts = ALL_LAYOUTS
    elif args.layouts:
        layouts = args.layouts
    else:
        print("Error: Specify --all or --layouts")
        return 1
    
    print(f"Testing {len(layouts)} layouts: {', '.join(layouts)}")
    
    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save experiment config
    config = {
        'timestamp': datetime.now().strftime('%Y%m%d_%H%M%S'),
        'layouts': layouts,
        'input_file': args.input,
        'gold_standard': args.gold_standard or args.input,
        'model': args.model,
        'provider': args.provider,
        'parallel': args.parallel
    }
    
    with open(args.output_dir / 'experiment_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    # Build base arguments for main.py
    base_args = [
        '--use-tot',
        '--input', args.input,
        '--gold-standard', args.gold_standard or args.input,
        '--provider', args.provider,
        '--model', args.model,
        '--concurrency', str(args.concurrency),
        '--batch-size', str(args.batch_size),
        '--regex-mode', args.regex_mode
    ]
    
    if args.start:
        base_args.extend(['--start', str(args.start)])
    if args.end:
        base_args.extend(['--end', str(args.end)])
    
    # Run experiments
    results = []
    
    if args.parallel > 1:
        # Run in parallel
        with concurrent.futures.ProcessPoolExecutor(max_workers=args.parallel) as executor:
            futures = {
                executor.submit(run_single_layout, layout, base_args, args.output_dir): layout
                for layout in layouts
            }
            
            for future in concurrent.futures.as_completed(futures):
                layout = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    print(f"❌ {layout} failed with exception: {e}")
                    results.append({
                        'layout': layout,
                        'status': 'error',
                        'error': str(e)
                    })
    else:
        # Run sequentially
        for layout in layouts:
            result = run_single_layout(layout, base_args, args.output_dir)
            results.append(result)
    
    # Create summary report
    create_summary_report(results, args.output_dir)
    
    print(f"\n✅ Experiment complete! Results in: {args.output_dir}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
