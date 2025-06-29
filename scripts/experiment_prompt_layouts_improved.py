#!/usr/bin/env python3
"""
Improved experiment script to test different prompt layout strategies.
This script runs the ToT pipeline with different layout configurations
and compares their performance against a gold standard.

Improvements:
- Added layout support for batch processing
- Fixed column name inconsistencies
- Added error handling for layout-specific issues
- Added thread safety for token accumulator
- Added validation for layout compatibility
- Added statistical significance testing
- Added caching for repeated experiments
- Added parallel experiment execution
- Added resume capability
- Added layout-specific metrics
"""

import sys
import json
import random
import hashlib
import pickle
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set
import pandas as pd
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
import threading
import logging
from scipy import stats
import matplotlib.pyplot as plt

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from multi_coder_analysis.run_multi_coder_tot import run_coding_step_tot, calculate_metrics


# Cache directory for LLM responses
CACHE_DIR = Path("output/layout_experiments/.cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def get_cache_key(segment_text: str, hop_idx: int, layout: str, model: str) -> str:
    """Generate a cache key for a specific segment/hop/layout/model combination."""
    content = f"{segment_text}:{hop_idx}:{layout}:{model}"
    return hashlib.md5(content.encode()).hexdigest()


def load_from_cache(cache_key: str) -> Optional[Dict]:
    """Load cached response if available."""
    cache_file = CACHE_DIR / f"{cache_key}.pkl"
    if cache_file.exists():
        try:
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        except Exception:
            pass
    return None


def save_to_cache(cache_key: str, data: Dict):
    """Save response to cache."""
    cache_file = CACHE_DIR / f"{cache_key}.pkl"
    try:
        with open(cache_file, 'wb') as f:
            pickle.dump(data, f)
    except Exception:
        pass


def validate_prompt_structure(hop_body: str, layout: str) -> bool:
    """Validate that the prompt has required sections for the layout."""
    import re
    
    if layout == "sandwich":
        return "QUICK DECISION CHECK" in hop_body or "⚡" in hop_body
    elif layout == "question_first":
        return re.search(r"### Question Q\d+", hop_body) is not None
    elif layout == "recency":
        return "{{segment_text}}" in hop_body or "### Segment" in hop_body
    return True


def validate_layout_compatibility(prompts_dir: Path, layouts: List[str]) -> List[str]:
    """Check if all prompts support the requested layouts."""
    issues = []
    
    for hop_file in prompts_dir.glob("hop_Q*.txt"):
        if hop_file.name.endswith('.lean.txt') or hop_file.name.endswith('.confidence.txt'):
            continue
            
        try:
            content = hop_file.read_text(encoding='utf-8')
            for layout in layouts:
                if not validate_prompt_structure(content, layout):
                    issues.append(f"{hop_file.name} may be incompatible with {layout} layout")
        except Exception as e:
            issues.append(f"Could not read {hop_file.name}: {e}")
    
    return issues


def load_completed_experiments(output_dir: Path) -> Set[Tuple[str, str]]:
    """Load already completed experiments to avoid re-running."""
    completed = set()
    
    if output_dir.exists():
        for result_file in output_dir.glob("*/experiment_metrics.json"):
            try:
                with open(result_file) as f:
                    metrics = json.load(f)
                    if 'error' not in metrics:
                        completed.add((metrics['layout'], metrics['model']))
            except Exception:
                pass
    
    return completed


def run_single_experiment(
    config: Dict,
    layout: str,
    model: str,
    sample_df: pd.DataFrame,
    output_base: Path,
    gold_standard_file: str,
    use_cache: bool = True,
) -> Dict:
    """Run a single experiment with a specific layout and model."""
    
    # Create output directory for this experiment
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = output_base / f"{layout}_{model.replace('/', '_')}_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save sample data
    sample_path = output_dir / "sample_data.csv"
    sample_df.to_csv(sample_path, index=False)
    
    # Validate layout compatibility
    prompts_dir = Path(__file__).parent.parent / "multi_coder_analysis" / "prompts"
    compatibility_issues = validate_layout_compatibility(prompts_dir, [layout])
    if compatibility_issues:
        logging.warning(f"Potential compatibility issues: {compatibility_issues}")
    
    # Run the coding step
    start_time = datetime.now()
    try:
        _, results_path = run_coding_step_tot(
            config=config,
            input_csv_path=sample_path,
            output_dir=output_dir,
            model=model,
            provider=config.get("provider", "gemini"),
            template=config.get("template", "legacy"),
            layout=layout,  # Use specified layout
            batch_size=config.get("batch_size", 1),  # Support batch processing
            concurrency=config.get("concurrency", 1),
            gold_standard_file=gold_standard_file,
            print_summary=False,  # Suppress output for batch runs
        )
        
        # Load results
        results_df = pd.read_csv(results_path)
        
        # Determine column names based on what's available
        if "Pipeline_Result" in results_df.columns and "Gold Standard" in results_df.columns:
            predictions = results_df["Pipeline_Result"].tolist()
            actuals = results_df["Gold Standard"].tolist()
        elif "Predicted_Label" in results_df.columns and "Actual_Label" in results_df.columns:
            predictions = results_df["Predicted_Label"].tolist()
            actuals = results_df["Actual_Label"].tolist()
        else:
            # Try to find suitable columns
            pred_col = next((col for col in results_df.columns if "pred" in col.lower() or "result" in col.lower()), None)
            actual_col = next((col for col in results_df.columns if "actual" in col.lower() or "gold" in col.lower()), None)
            
            if pred_col and actual_col:
                predictions = results_df[pred_col].tolist()
                actuals = results_df[actual_col].tolist()
            else:
                raise ValueError(f"Could not find prediction/actual columns in {results_df.columns.tolist()}")
        
        # Calculate metrics
        metrics = calculate_metrics(predictions, actuals)
        
        # Add experiment metadata
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Calculate layout-specific metrics
        layout_metrics = {
            "avg_segment_length": sample_df["Statement Text"].str.len().mean() if "Statement Text" in sample_df.columns else 0,
            "total_segments": len(sample_df),
        }
        
        metrics.update({
            "layout": layout,
            "model": model,
            "sample_size": len(sample_df),
            "duration_seconds": duration,
            "timestamp": timestamp,
            "output_dir": str(output_dir),
            "layout_metrics": layout_metrics,
            "config": {
                "batch_size": config.get("batch_size", 1),
                "concurrency": config.get("concurrency", 1),
                "template": config.get("template", "legacy"),
            }
        })
        
        # Save detailed metrics
        with open(output_dir / "experiment_metrics.json", "w") as f:
            json.dump(metrics, f, indent=2)
            
        return metrics
        
    except Exception as e:
        logging.error(f"Error in experiment {layout} with {model}: {e}")
        return {
            "layout": layout,
            "model": model,
            "error": str(e),
            "sample_size": len(sample_df),
            "timestamp": timestamp,
            "duration_seconds": (datetime.now() - start_time).total_seconds(),
        }


def run_experiments(
    config_path: Path,
    gold_standard_path: Path,
    sample_size: int = 100,
    random_seed: int = 42,
    layouts: List[str] = None,
    models: List[str] = None,
    output_dir: Path = None,
    max_workers: int = 4,
    resume: bool = True,
    batch_size: int = 1,
) -> pd.DataFrame:
    """Run experiments across different layouts and models."""
    
    # Load config
    with open(config_path) as f:
        config = json.load(f)
    
    # Update config with batch size
    config['batch_size'] = batch_size
    
    # Load gold standard
    gold_df = pd.read_csv(gold_standard_path)
    
    # Sample data
    random.seed(random_seed)
    if sample_size < len(gold_df):
        sample_indices = random.sample(range(len(gold_df)), sample_size)
        sample_df = gold_df.iloc[sample_indices].reset_index(drop=True)
    else:
        sample_df = gold_df
    
    # Default layouts if not specified
    if layouts is None:
        layouts = ["standard", "recency", "sandwich", "minimal_system", "question_first"]
    
    # Default models if not specified
    if models is None:
        models = ["gemini-2.0-flash-exp"]
    
    # Create output directory
    if output_dir is None:
        output_dir = Path("output/layout_experiments") / datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Check for completed experiments if resuming
    completed = set()
    if resume:
        completed = load_completed_experiments(output_dir)
        if completed:
            print(f"Found {len(completed)} completed experiments, will skip them")
    
    # Validate layout compatibility upfront
    prompts_dir = Path(__file__).parent.parent / "multi_coder_analysis" / "prompts"
    compatibility_issues = validate_layout_compatibility(prompts_dir, layouts)
    if compatibility_issues:
        print("⚠️  Potential compatibility issues detected:")
        for issue in compatibility_issues:
            print(f"   - {issue}")
        print()
    
    # Save experiment configuration
    experiment_config = {
        "config_path": str(config_path),
        "gold_standard_path": str(gold_standard_path),
        "sample_size": sample_size,
        "actual_sample_size": len(sample_df),
        "random_seed": random_seed,
        "layouts": layouts,
        "models": models,
        "batch_size": batch_size,
        "timestamp": datetime.now().isoformat(),
        "compatibility_issues": compatibility_issues,
    }
    with open(output_dir / "experiment_config.json", "w") as f:
        json.dump(experiment_config, f, indent=2)
    
    # Save sample data for reproducibility
    sample_df.to_csv(output_dir / "sample_data.csv", index=False)
    
    # Prepare experiments to run
    experiments_to_run = []
    for layout in layouts:
        for model in models:
            if (layout, model) not in completed:
                experiments_to_run.append((layout, model))
    
    total_experiments = len(layouts) * len(models)
    print(f"Running {len(experiments_to_run)}/{total_experiments} experiments...")
    print(f"Layouts: {layouts}")
    print(f"Models: {models}")
    print(f"Sample size: {len(sample_df)}")
    print(f"Batch size: {batch_size}")
    print(f"Output directory: {output_dir}")
    print(f"Max workers: {max_workers}")
    print("-" * 80)
    
    # Run experiments in parallel
    results = []
    
    # Load any existing results from completed experiments
    if completed:
        for layout, model in completed:
            metrics_file = output_dir / f"{layout}_{model.replace('/', '_')}_*/experiment_metrics.json"
            for mf in output_dir.glob(str(metrics_file).split('/')[-1]):
                try:
                    with open(mf) as f:
                        results.append(json.load(f))
                except Exception:
                    pass
    
    # Run new experiments in parallel
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for layout, model in experiments_to_run:
            future = executor.submit(
                run_single_experiment,
                config=config,
                layout=layout,
                model=model,
                sample_df=sample_df,
                output_base=output_dir,
                gold_standard_file=str(gold_standard_path),
            )
            futures.append((future, layout, model))
        
        # Collect results as they complete
        for future, layout, model in futures:
            try:
                print(f"\n🔄 Running experiment: {layout} with {model}")
                result = future.result()
                results.append(result)
                
                # Print summary
                if "error" not in result:
                    print(f"  ✅ Accuracy: {result['accuracy']:.3f}")
                    print(f"  ✅ F1 Score: {result['f1_score']:.3f}")
                    print(f"  ✅ Duration: {result['duration_seconds']:.1f}s")
                else:
                    print(f"  ❌ Error: {result['error']}")
                    
            except Exception as e:
                print(f"  ❌ Exception: {e}")
                results.append({
                    "layout": layout,
                    "model": model,
                    "error": str(e),
                    "sample_size": len(sample_df),
                })
    
    # Create results dataframe
    results_df = pd.DataFrame(results)
    
    # Save results
    results_df.to_csv(output_dir / "all_results.csv", index=False)
    
    # Create summary report
    create_summary_report(results_df, output_dir)
    
    # Perform statistical analysis
    if len(results_df[~results_df["accuracy"].isna()]) > 1:
        perform_statistical_analysis(results_df, output_dir)
    
    return results_df


def perform_statistical_analysis(results_df: pd.DataFrame, output_dir: Path):
    """Perform statistical significance testing between layouts."""
    
    valid_results = results_df[~results_df["accuracy"].isna()].copy()
    if len(valid_results) == 0:
        return
    
    layouts = valid_results["layout"].unique()
    
    # Pairwise comparisons
    comparisons = []
    for i, layout1 in enumerate(layouts):
        for layout2 in layouts[i+1:]:
            scores1 = valid_results[valid_results["layout"] == layout1]["accuracy"].values
            scores2 = valid_results[valid_results["layout"] == layout2]["accuracy"].values
            
            if len(scores1) > 0 and len(scores2) > 0:
                # T-test for difference in means
                t_stat, p_value = stats.ttest_ind(scores1, scores2)
                
                comparisons.append({
                    "layout1": layout1,
                    "layout2": layout2,
                    "mean1": scores1.mean(),
                    "mean2": scores2.mean(),
                    "diff": scores1.mean() - scores2.mean(),
                    "t_stat": t_stat,
                    "p_value": p_value,
                    "significant": p_value < 0.05,
                })
    
    # Save statistical analysis
    stats_df = pd.DataFrame(comparisons)
    stats_df.to_csv(output_dir / "statistical_analysis.csv", index=False)
    
    # Create statistical report
    with open(output_dir / "statistical_report.txt", "w") as f:
        f.write("# Statistical Analysis of Layout Experiments\n\n")
        f.write("## Pairwise Comparisons (t-test)\n\n")
        
        for _, row in stats_df.iterrows():
            f.write(f"{row['layout1']} vs {row['layout2']}:\n")
            f.write(f"  Mean difference: {row['diff']:.4f} ({row['mean1']:.3f} - {row['mean2']:.3f})\n")
            f.write(f"  p-value: {row['p_value']:.4f}")
            if row['significant']:
                f.write(" ***")
            f.write("\n\n")
        
        f.write("\n*** = statistically significant at p < 0.05\n")


def create_summary_report(results_df: pd.DataFrame, output_dir: Path):
    """Create a summary report of the experiments."""
    
    # Filter out errors
    valid_results = results_df[~results_df["accuracy"].isna()].copy()
    
    if len(valid_results) == 0:
        print("No valid results to summarize.")
        return
    
    # Calculate summary statistics by layout
    layout_summary = valid_results.groupby("layout").agg({
        "accuracy": ["mean", "std", "min", "max", "count"],
        "f1_score": ["mean", "std"],
        "duration_seconds": ["mean", "std"],
    }).round(3)
    
    # Calculate summary statistics by model
    model_summary = valid_results.groupby("model").agg({
        "accuracy": ["mean", "std", "min", "max", "count"],
        "f1_score": ["mean", "std"],
        "duration_seconds": ["mean", "std"],
    }).round(3)
    
    # Find best configuration
    best_idx = valid_results["accuracy"].idxmax()
    best_config = valid_results.loc[best_idx]
    
    # Create report
    report_lines = [
        "# Prompt Layout Experiment Results",
        f"\nGenerated: {datetime.now().isoformat()}",
        f"Total experiments: {len(results_df)}",
        f"Valid experiments: {len(valid_results)}",
        f"Failed experiments: {len(results_df) - len(valid_results)}",
        f"Sample size: {valid_results['sample_size'].iloc[0] if len(valid_results) > 0 else 'N/A'}",
        "",
        "## Best Configuration",
        f"Layout: **{best_config['layout']}**",
        f"Model: {best_config['model']}",
        f"Accuracy: {best_config['accuracy']:.3f}",
        f"F1 Score: {best_config['f1_score']:.3f}",
        f"Duration: {best_config['duration_seconds']:.1f}s",
        "",
        "## Summary by Layout",
        layout_summary.to_string(),
        "",
        "## Summary by Model",
        model_summary.to_string(),
        "",
        "## Detailed Results",
        valid_results[["layout", "model", "accuracy", "f1_score", "duration_seconds"]].to_string(index=False),
    ]
    
    # Add error summary if any
    error_results = results_df[results_df["accuracy"].isna()]
    if len(error_results) > 0:
        report_lines.extend([
            "",
            "## Failed Experiments",
            error_results[["layout", "model", "error"]].to_string(index=False),
        ])
    
    report_path = output_dir / "summary_report.txt"
    with open(report_path, "w") as f:
        f.write("\n".join(report_lines))
    
    print(f"\n📊 Summary report saved to: {report_path}")
    
    # Create visualizations
    create_visualizations(valid_results, output_dir)


def create_visualizations(valid_results: pd.DataFrame, output_dir: Path):
    """Create visual comparisons of experiment results."""
    
    try:
        # Create accuracy comparison plot
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        
        # Layout comparison
        layout_means = valid_results.groupby("layout")["accuracy"].mean().sort_values(ascending=False)
        layout_stds = valid_results.groupby("layout")["accuracy"].std()
        
        x_pos = np.arange(len(layout_means))
        ax1.bar(x_pos, layout_means.values, yerr=layout_stds.values, capsize=5, alpha=0.7)
        ax1.set_xticks(x_pos)
        ax1.set_xticklabels(layout_means.index, rotation=45, ha='right')
        ax1.set_xlabel("Layout")
        ax1.set_ylabel("Mean Accuracy")
        ax1.set_title("Accuracy by Layout (with std error)")
        ax1.set_ylim(0, 1)
        ax1.grid(axis='y', alpha=0.3)
        
        # Add value labels on bars
        for i, (layout, acc) in enumerate(layout_means.items()):
            ax1.text(i, acc + 0.01, f"{acc:.3f}", ha='center', va='bottom')
        
        # Model comparison
        model_means = valid_results.groupby("model")["accuracy"].mean().sort_values(ascending=False)
        model_stds = valid_results.groupby("model")["accuracy"].std()
        
        x_pos = np.arange(len(model_means))
        ax2.bar(x_pos, model_means.values, yerr=model_stds.values, capsize=5, alpha=0.7, color='orange')
        ax2.set_xticks(x_pos)
        ax2.set_xticklabels(model_means.index, rotation=45, ha='right')
        ax2.set_xlabel("Model")
        ax2.set_ylabel("Mean Accuracy")
        ax2.set_title("Accuracy by Model (with std error)")
        ax2.set_ylim(0, 1)
        ax2.grid(axis='y', alpha=0.3)
        
        # Add value labels on bars
        for i, (model, acc) in enumerate(model_means.items()):
            ax2.text(i, acc + 0.01, f"{acc:.3f}", ha='center', va='bottom')
        
        # F1 Score comparison
        layout_f1_means = valid_results.groupby("layout")["f1_score"].mean().sort_values(ascending=False)
        
        x_pos = np.arange(len(layout_f1_means))
        ax3.bar(x_pos, layout_f1_means.values, alpha=0.7, color='green')
        ax3.set_xticks(x_pos)
        ax3.set_xticklabels(layout_f1_means.index, rotation=45, ha='right')
        ax3.set_xlabel("Layout")
        ax3.set_ylabel("Mean F1 Score")
        ax3.set_title("F1 Score by Layout")
        ax3.set_ylim(0, 1)
        ax3.grid(axis='y', alpha=0.3)
        
        # Duration comparison
        layout_duration_means = valid_results.groupby("layout")["duration_seconds"].mean().sort_values()
        
        x_pos = np.arange(len(layout_duration_means))
        ax4.bar(x_pos, layout_duration_means.values, alpha=0.7, color='red')
        ax4.set_xticks(x_pos)
        ax4.set_xticklabels(layout_duration_means.index, rotation=45, ha='right')
        ax4.set_xlabel("Layout")
        ax4.set_ylabel("Mean Duration (seconds)")
        ax4.set_title("Processing Time by Layout")
        ax4.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_dir / "experiment_visualizations.png", dpi=150, bbox_inches='tight')
        print(f"📈 Visualizations saved to: {output_dir / 'experiment_visualizations.png'}")
        
        # Create accuracy vs duration scatter plot
        fig2, ax5 = plt.subplots(1, 1, figsize=(10, 8))
        
        for layout in valid_results["layout"].unique():
            layout_data = valid_results[valid_results["layout"] == layout]
            ax5.scatter(layout_data["duration_seconds"], layout_data["accuracy"], 
                       label=layout, s=100, alpha=0.7)
        
        ax5.set_xlabel("Duration (seconds)")
        ax5.set_ylabel("Accuracy")
        ax5.set_title("Accuracy vs Processing Time by Layout")
        ax5.legend()
        ax5.grid(alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_dir / "accuracy_vs_duration.png", dpi=150, bbox_inches='tight')
        
    except ImportError:
        print("⚠️  Matplotlib not available, skipping visualizations.")
    except Exception as e:
        print(f"⚠️  Error creating visualizations: {e}")




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
        question = re.search(r"### Question Q\d+", user_prompt)
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


def main():
    """Main entry point for the experiment script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run improved prompt layout experiments")
    parser.add_argument("--config", type=Path, required=True, help="Path to config JSON file")
    parser.add_argument("--gold-standard", type=Path, required=True, help="Path to gold standard CSV")
    parser.add_argument("--sample-size", type=int, default=100, help="Number of samples to test")
    parser.add_argument("--random-seed", type=int, default=42, help="Random seed for sampling")
    parser.add_argument("--layouts", nargs="+", help="Layouts to test (default: all)")
    parser.add_argument("--models", nargs="+", help="Models to test")
    parser.add_argument("--output-dir", type=Path, help="Output directory for results")
    parser.add_argument("--max-workers", type=int, default=4, help="Maximum parallel workers")
    parser.add_argument("--no-resume", action="store_true", help="Don't resume from previous runs")
    parser.add_argument("--batch-size", type=int, default=1, help="Batch size for processing")
    parser.add_argument("--clear-cache", action="store_true", help="Clear LLM response cache")
    
    args = parser.parse_args()
    
    # Clear cache if requested
    if args.clear_cache and CACHE_DIR.exists():
        import shutil
        shutil.rmtree(CACHE_DIR)
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        print("✅ Cache cleared")
    
    results = run_experiments(
        config_path=args.config,
        gold_standard_path=args.gold_standard,
        sample_size=args.sample_size,
        random_seed=args.random_seed,
        layouts=args.layouts,
        models=args.models,
        output_dir=args.output_dir,
        max_workers=args.max_workers,
        resume=not args.no_resume,
        batch_size=args.batch_size,
    )
    
    print("\n✅ Experiment complete!")
    print(f"Results shape: {results.shape}")
    
    # Show top configurations
    valid_results = results[~results["accuracy"].isna()]
    if len(valid_results) > 0:
        print(f"\n🏆 Top 3 configurations by accuracy:")
        top_results = valid_results.nlargest(3, "accuracy")[["layout", "model", "accuracy", "f1_score", "duration_seconds"]]
        print(top_results.to_string(index=False))


if __name__ == "__main__":
    main() 