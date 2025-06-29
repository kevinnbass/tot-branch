"""
Layout experiment runner for testing different prompt layout strategies.
Runs multiple layouts in parallel and compares their performance.
"""

import logging
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import threading
import os

from .run_multi_coder_tot import run_coding_step_tot, calculate_metrics
from .layout_config import LayoutExperimentConfig


# All 13 available layouts
ALL_LAYOUTS = [
    # Original 5
    'standard', 'recency', 'sandwich', 'minimal_system', 'question_first',
    # New 8
    'hop_last', 'structured_json', 'segment_focus', 'instruction_first',
    'parallel_analysis', 'evidence_based', 'xml_structured', 'primacy_recency'
]

# New minimal_system variations for Phase 1
MINIMAL_SYSTEM_VARIATIONS = [
    'minimal_segment_first',
    'minimal_question_twice', 
    'minimal_json_segment',
    'minimal_parallel_criteria',
    'minimal_hop_sandwich',
    'minimal_system',  # baseline
]


def run_layout_experiment(
    config: Dict,
    args,
    layout: str,
    output_base: Path,
    shutdown_event: threading.Event = None,
    layout_info: Optional[Dict] = None,
) -> Dict:
    """Run a single layout experiment."""
    
    # Create layout-specific output directory
    layout_dir = output_base / layout
    layout_dir.mkdir(parents=True, exist_ok=True)
    
    logging.info(f"🧪 Starting layout experiment: {layout}")
    if layout_info and layout_info.get('description'):
        logging.info(f"   Description: {layout_info['description']}")
    
    start_time = datetime.now()
    
    # Check for early shutdown
    if shutdown_event and shutdown_event.is_set():
        return {
            'layout': layout,
            'status': 'skipped',
            'error': 'Shutdown requested before start',
            'duration_seconds': 0,
        }
    
    try:
        # Determine sample size from layout_info or args
        sample_size = None
        if layout_info and 'sample_size' in layout_info:
            sample_size = layout_info['sample_size']
            # Adjust end parameter based on sample size
            # Safety check for None values
            if args.start is not None and args.end is not None and sample_size < args.end - args.start + 1:
                actual_end = args.start + sample_size - 1
                logging.info(f"   Using sample size: {sample_size} (rows {args.start}-{actual_end})")
            else:
                actual_end = args.end
        else:
            actual_end = args.end
        
        # Run the ToT pipeline with this specific layout
        _, results_path = run_coding_step_tot(
            config=config,
            input_csv_path=Path(args.input),
            output_dir=layout_dir,
            limit=args.limit,
            start=args.start,
            end=actual_end,
            concurrency=args.concurrency,
            model=args.model,
            provider=args.provider,
            batch_size=args.batch_size,
            regex_mode=args.regex_mode,
            router=args.router if hasattr(args, 'router') else False,
            template=args.template if hasattr(args, 'template') else 'legacy',
            layout=layout,  # Specific layout for this experiment
            shuffle_batches=args.shuffle_batches if hasattr(args, 'shuffle_batches') else False,
            shuffle_segments=args.shuffle_segments if hasattr(args, 'shuffle_segments') else False,
            skip_eval=True,  # Skip individual evaluation, we'll do it at the end
            only_hop=args.only_hop if hasattr(args, 'only_hop') else None,
            gold_standard_file=args.gold_standard,
            print_summary=False,  # Reduce output noise
            shutdown_event=shutdown_event,
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Load results
        df_results = pd.read_csv(results_path, dtype={'StatementID': str})
        
        # Calculate metrics if gold standard is available
        metrics = None
        if args.gold_standard:
            df_gold = pd.read_csv(args.gold_standard, dtype={'StatementID': str})
            
            # Merge with gold standard
            df_comparison = df_results.merge(
                df_gold[['StatementID', 'Gold Standard']], 
                on='StatementID', 
                how='left'
            )
            
            # Filter to only results with gold standard
            df_comparison = df_comparison[df_comparison['Gold Standard'].notna()].copy()
            
            if len(df_comparison) > 0:
                predictions = df_comparison['Pipeline_Result'].tolist()
                actuals = df_comparison['Gold Standard'].tolist()
                metrics = calculate_metrics(predictions, actuals)
                
                # Save comparison
                comparison_path = layout_dir / "comparison.csv"
                df_comparison.to_csv(comparison_path, index=False)
                
                # Create mismatch analysis files
                mismatches = df_comparison[df_comparison['Gold Standard'] != df_comparison['Pipeline_Result']].copy()
                if len(mismatches) > 0:
                    # Save mismatch CSV
                    mismatch_csv_path = layout_dir / "mismatches.csv"
                    mismatches.to_csv(mismatch_csv_path, index=False)
                    
                    # Create consolidated mismatch JSONL with traces
                    mismatch_traces = []
                    trace_dir = layout_dir / "traces_tot"
                    
                    if trace_dir.exists():
                        for _, row in mismatches.iterrows():
                            statement_id = row['StatementID']
                            trace_file = trace_dir / f"{statement_id}.jsonl"
                            
                            trace_entries = []
                            if trace_file.exists():
                                try:
                                    with open(trace_file, 'r', encoding='utf-8') as f:
                                        for line in f:
                                            line = line.strip()
                                            if line:
                                                trace_entries.append(json.loads(line))
                                except Exception as e:
                                    logging.warning(f"Error reading trace file {trace_file}: {e}")
                            
                            mismatch_traces.append({
                                "statement_id": statement_id,
                                "statement_text": row.get('Statement Text', ''),
                                "expected": row['Gold Standard'],
                                "predicted": row['Pipeline_Result'],
                                "trace_count": len(trace_entries),
                                "full_trace": trace_entries
                            })
                    
                    # Save consolidated mismatch traces
                    if mismatch_traces:
                        consolidated_path = layout_dir / "consolidated_mismatch_traces.jsonl"
                        with open(consolidated_path, 'w', encoding='utf-8') as f:
                            for entry in mismatch_traces:
                                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
                        
                        logging.info(f"   Created {len(mismatches)} mismatch files: mismatches.csv & consolidated_mismatch_traces.jsonl")
        
        # Return experiment results
        return {
            'layout': layout,
            'status': 'success',
            'duration_seconds': duration,
            'num_results': len(df_results),
            'output_dir': str(layout_dir),
            'results_path': str(results_path),
            'metrics': metrics,
            'layout_info': layout_info,
        }
        
    except Exception as e:
        logging.error(f"Layout experiment {layout} failed: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return {
            'layout': layout,
            'status': 'failed',
            'error': str(e),
            'duration_seconds': (datetime.now() - start_time).total_seconds(),
        }


def run_layout_experiments(config: Dict, args, shutdown_event: threading.Event) -> Path:
    """Run all layout experiments using threading (to avoid pickle errors) and create comparison report."""
    
    # Check for config file
    config_file = None
    layout_config = None
    
    # First check command line argument
    if hasattr(args, 'layout_config') and args.layout_config:
        config_file = Path(args.layout_config)
    # Then check environment variable
    elif os.environ.get('LAYOUT_CONFIG'):
        config_file = Path(os.environ.get('LAYOUT_CONFIG'))
    # Default config file
    elif Path('layout_experiment_config.yaml').exists():
        config_file = Path('layout_experiment_config.yaml')
    
    # Load config if available
    if config_file and config_file.exists():
        logging.info(f"Loading layout experiment config from: {config_file}")
        layout_config = LayoutExperimentConfig(config_file)
        layouts = layout_config.get_enabled_layouts()
        
        # Log experiment info
        exp_config = layout_config.get_experiment_config()
        if exp_config:
            logging.info(f"Experiment: {exp_config.get('name', 'Unnamed')}")
            logging.info(f"Description: {exp_config.get('description', 'No description')}")
    else:
        # Fall back to original behavior
        layouts_to_test = getattr(args, 'layouts', None)
        if layouts_to_test:
            # If specific layouts are provided via args
            layouts = [l for l in layouts_to_test if l in ALL_LAYOUTS + MINIMAL_SYSTEM_VARIATIONS]
            invalid_layouts = [l for l in layouts_to_test if l not in ALL_LAYOUTS + MINIMAL_SYSTEM_VARIATIONS]
            if invalid_layouts:
                logging.warning(f"Invalid layouts will be skipped: {invalid_layouts}")
        else:
            # Check environment variable for layout override
            env_layouts = os.environ.get('TOT_LAYOUTS', '').strip()
            if env_layouts:
                if env_layouts.lower() == 'all':
                    layouts = ALL_LAYOUTS
                else:
                    layouts = [l.strip() for l in env_layouts.split(',') if l.strip() in ALL_LAYOUTS + MINIMAL_SYSTEM_VARIATIONS]
            else:
                # Default to testing all layouts
                layouts = ALL_LAYOUTS
    
    # Create experiment output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    experiment_dir = Path("output") / "layout_experiments" / timestamp
    experiment_dir.mkdir(parents=True, exist_ok=True)
    
    logging.info(f"🧪 Starting layout experiments in: {experiment_dir}")
    logging.info(f"📊 Testing {len(layouts)} layouts: {layouts}")
    logging.info(f"🔧 Batch size: {args.batch_size}")
    
    # Save experiment configuration
    experiment_config = {
        'timestamp': timestamp,
        'layouts': layouts,
        'input_file': str(args.input),
        'gold_standard': str(args.gold_standard) if args.gold_standard else None,
        'batch_size': args.batch_size,
        'model': args.model,
        'provider': args.provider,
        'start': args.start,
        'end': args.end,
        'limit': args.limit,
        'concurrency': args.concurrency,
        'regex_mode': args.regex_mode,
    }
    
    # Add config file info if used
    if layout_config:
        experiment_config['config_file'] = str(config_file)
        experiment_config['experiment_name'] = layout_config.get_experiment_config().get('name', 'Unnamed')
    
    with open(experiment_dir / 'experiment_config.json', 'w') as f:
        json.dump(experiment_config, f, indent=2)
    
    # Save the config file if used
    if config_file and config_file.exists():
        import shutil
        shutil.copy(config_file, experiment_dir / 'layout_config.yaml')
    
    # Run experiments using ThreadPoolExecutor (avoids pickle issues)
    results = []
    
    # Determine max workers
    if layout_config:
        exec_config = layout_config.get_execution_config()
        max_workers = exec_config.get('parallel_workers', 5)
    else:
        max_workers = min(getattr(args, 'layout_workers', 5), len(layouts))
    
    max_workers = min(max_workers, len(layouts))
    
    # Create a thread-local storage for shutdown checking
    def run_with_shutdown_check(layout):
        if shutdown_event.is_set():
            return {
                'layout': layout,
                'status': 'skipped',
                'error': 'Shutdown requested',
            }
        
        # Get layout info if using config
        layout_info = None
        if layout_config:
            layout_info = layout_config.get_layout_info(layout)
        
        return run_layout_experiment(config, args, layout, experiment_dir, shutdown_event, layout_info)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all experiments
        future_to_layout = {
            executor.submit(run_with_shutdown_check, layout): layout
            for layout in layouts
        }
        
        # Collect results as they complete
        completed = 0
        for future in as_completed(future_to_layout):
            layout = future_to_layout[future]
            completed += 1
            
            try:
                result = future.result()
                results.append(result)
                
                # Progress update
                progress = f"[{completed}/{len(layouts)}]"
                
                if result['status'] == 'success' and result.get('metrics'):
                    metrics = result['metrics']
                    logging.info(
                        f"✅ {progress} Layout {layout} completed: "
                        f"Accuracy={metrics['accuracy']:.3f}, "
                        f"Duration={result['duration_seconds']:.1f}s"
                    )
                elif result['status'] == 'failed':
                    logging.error(f"❌ {progress} Layout {layout} failed: {result.get('error', 'Unknown error')}")
                elif result['status'] == 'skipped':
                    logging.info(f"⏭️  {progress} Layout {layout} skipped: {result.get('error', 'Unknown reason')}")
                    
            except Exception as e:
                logging.error(f"❌ {progress} Layout {layout} failed with exception: {e}")
                results.append({
                    'layout': layout,
                    'status': 'failed',
                    'error': str(e),
                })
            
            # Check for shutdown
            if shutdown_event.is_set():
                logging.info("Shutdown requested, cancelling remaining experiments...")
                # Cancel all pending futures
                for f in future_to_layout:
                    if not f.done():
                        f.cancel()
                # Force shutdown the executor
                executor.shutdown(wait=False)
                break
    
    # Create comparison report
    create_comparison_report(results, experiment_dir)
    
    return experiment_dir


def create_comparison_report(results: List[Dict], output_dir: Path):
    """Create a comprehensive comparison report of all layout experiments."""
    
    # Save raw results
    results_df = pd.DataFrame(results)
    results_df.to_csv(output_dir / 'all_results.csv', index=False)
    
    # Filter successful experiments with metrics
    successful_results = [r for r in results if r.get('status') == 'success' and r.get('metrics')]
    
    if not successful_results:
        logging.warning("No successful experiments with metrics to compare")
        
        # Create a simple summary for failed experiments
        summary_lines = [
            "# Layout Experiment Results",
            f"\nGenerated: {datetime.now().isoformat()}",
            f"Total experiments: {len(results)}",
            f"Successful experiments: 0",
            "",
            "## All Results",
            results_df.to_string(index=False),
        ]
        
        with open(output_dir / 'comparison_report.txt', 'w') as f:
            f.write('\n'.join(summary_lines))
        
        return
    
    # Create comparison summary
    summary_data = []
    for result in successful_results:
        metrics = result['metrics']
        summary_data.append({
            'Layout': result['layout'],
            'Accuracy': metrics['accuracy'],
            'Precision_Alarmist': metrics['frame_metrics'].get('Alarmist', {}).get('precision', 0),
            'Recall_Alarmist': metrics['frame_metrics'].get('Alarmist', {}).get('recall', 0),
            'F1_Alarmist': metrics['frame_metrics'].get('Alarmist', {}).get('f1', 0),
            'Precision_Neutral': metrics['frame_metrics'].get('Neutral', {}).get('precision', 0),
            'Recall_Neutral': metrics['frame_metrics'].get('Neutral', {}).get('recall', 0),
            'F1_Neutral': metrics['frame_metrics'].get('Neutral', {}).get('f1', 0),
            'Precision_Reassuring': metrics['frame_metrics'].get('Reassuring', {}).get('precision', 0),
            'Recall_Reassuring': metrics['frame_metrics'].get('Reassuring', {}).get('recall', 0),
            'F1_Reassuring': metrics['frame_metrics'].get('Reassuring', {}).get('f1', 0),
            'Duration_Seconds': result['duration_seconds'],
        })
    
    summary_df = pd.DataFrame(summary_data)
    summary_df = summary_df.sort_values('Accuracy', ascending=False)
    summary_df.to_csv(output_dir / 'comparison_summary.csv', index=False)
    
    # Calculate average F1 across all frames for each layout
    for row in summary_data:
        f1_scores = [
            row.get('F1_Alarmist', 0),
            row.get('F1_Neutral', 0),
            row.get('F1_Reassuring', 0)
        ]
        # Filter out zeros (frames that might not be present)
        f1_scores = [s for s in f1_scores if s > 0]
        row['Avg_F1'] = sum(f1_scores) / len(f1_scores) if f1_scores else 0
    
    # Re-create DataFrame with average F1
    summary_df = pd.DataFrame(summary_data)
    summary_df = summary_df.sort_values('Accuracy', ascending=False)
    
    # Find best layout
    best_layout = summary_df.iloc[0]
    
    # Create text report
    report_lines = [
        "# Layout Experiment Results",
        f"\nGenerated: {datetime.now().isoformat()}",
        f"Total experiments: {len(results)}",
        f"Successful experiments: {len(successful_results)}",
        f"Failed experiments: {len(results) - len(successful_results)}",
        "",
        "## Best Layout",
        f"**{best_layout['Layout']}**",
        f"- Accuracy: {best_layout['Accuracy']:.3f}",
        f"- Average F1: {best_layout['Avg_F1']:.3f}",
        f"- Duration: {best_layout['Duration_Seconds']:.1f}s",
        "",
        "## All Results (sorted by accuracy)",
        summary_df[['Layout', 'Accuracy', 'Avg_F1', 'Duration_Seconds']].to_string(index=False, float_format='%.3f'),
        "",
        "## Per-Frame Performance",
    ]
    
    # Add per-frame comparison
    for frame in ['Alarmist', 'Neutral', 'Reassuring']:
        report_lines.append(f"\n### {frame}")
        frame_data = summary_df[['Layout', f'Precision_{frame}', f'Recall_{frame}', f'F1_{frame}']].copy()
        frame_data.columns = ['Layout', 'Precision', 'Recall', 'F1']
        # Only show non-zero rows
        frame_data = frame_data[(frame_data['Precision'] > 0) | (frame_data['Recall'] > 0) | (frame_data['F1'] > 0)]
        if not frame_data.empty:
            report_lines.append(frame_data.to_string(index=False, float_format='%.3f'))
        else:
            report_lines.append("No data for this frame")
    
    # Add failed experiments section if any
    failed_results = [r for r in results if r.get('status') == 'failed']
    if failed_results:
        report_lines.extend([
            "",
            "## Failed Experiments",
        ])
        for result in failed_results:
            report_lines.append(f"- {result['layout']}: {result.get('error', 'Unknown error')}")
    
    # Write report
    report_path = output_dir / 'comparison_report.txt'
    with open(report_path, 'w') as f:
        f.write('\n'.join(report_lines))
    
    # Print summary to console
    print("\n" + "="*80)
    print("🎯 LAYOUT EXPERIMENT RESULTS")
    print("="*80)
    print(f"\n📊 Best Layout: **{best_layout['Layout']}**")
    print(f"   Accuracy: {best_layout['Accuracy']:.3f}")
    print(f"   Average F1: {best_layout['Avg_F1']:.3f}")
    print(f"   Duration: {best_layout['Duration_Seconds']:.1f}s")
    print("\n📈 All Results:")
    print(summary_df[['Layout', 'Accuracy', 'Avg_F1', 'Duration_Seconds']].to_string(index=False, float_format='%.3f'))
    print(f"\n📁 Full report saved to: {report_path}")
    print("="*80)
    
    # Also create a JSON summary for easy programmatic access
    json_summary = {
        'best_layout': best_layout['Layout'],
        'best_accuracy': float(best_layout['Accuracy']),
        'best_avg_f1': float(best_layout['Avg_F1']),
        'results': summary_data,
        'experiment_dir': str(output_dir),
        'total_experiments': len(results),
        'successful_experiments': len(successful_results),
        'failed_experiments': len(failed_results),
    }
    
    with open(output_dir / 'summary.json', 'w') as f:
        json.dump(json_summary, f, indent=2) 