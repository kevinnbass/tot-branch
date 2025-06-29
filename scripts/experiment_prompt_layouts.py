#!/usr/bin/env python3
"""
Experiment script to test different prompt layout strategies.
This script runs the ToT pipeline with different layout configurations
and compares their performance against a gold standard.
"""

import sys
import json
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from multi_coder_analysis.run_multi_coder_tot import run_coding_step_tot, calculate_metrics


def run_single_experiment(
    config: Dict,
    layout: str,
    model: str,
    sample_df: pd.DataFrame,
    output_base: Path,
    gold_standard_file: str,
) -> Dict:
    """Run a single experiment with a specific layout and model."""
    
    # Create output directory for this experiment
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = output_base / f"{layout}_{model.replace('/', '_')}_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save sample data
    sample_path = output_dir / "sample_data.csv"
    sample_df.to_csv(sample_path, index=False)
    
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
            batch_size=1,  # Single segment processing for layout testing
            concurrency=1,
            gold_standard_file=gold_standard_file,
            print_summary=False,  # Suppress output for batch runs
        )
        
        # Load results
        results_df = pd.read_csv(results_path)
        
        # Calculate metrics
        predictions = results_df["Predicted_Label"].tolist()
        actuals = results_df["Actual_Label"].tolist()
        metrics = calculate_metrics(predictions, actuals)
        
        # Add experiment metadata
        end_time = datetime.now()
        metrics.update({
            "layout": layout,
            "model": model,
            "sample_size": len(sample_df),
            "duration_seconds": (end_time - start_time).total_seconds(),
            "timestamp": timestamp,
            "output_dir": str(output_dir),
        })
        
        # Save detailed metrics
        with open(output_dir / "experiment_metrics.json", "w") as f:
            json.dump(metrics, f, indent=2)
            
        return metrics
        
    except Exception as e:
        print(f"Error in experiment {layout} with {model}: {e}")
        return {
            "layout": layout,
            "model": model,
            "error": str(e),
            "sample_size": len(sample_df),
            "timestamp": timestamp,
        }


def run_experiments(
    config_path: Path,
    gold_standard_path: Path,
    sample_size: int = 100,
    random_seed: int = 42,
    layouts: List[str] = None,
    models: List[str] = None,
    output_dir: Path = None,
) -> pd.DataFrame:
    """Run experiments across different layouts and models."""
    
    # Load config
    with open(config_path) as f:
        config = json.load(f)
    
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
    
    # Save experiment configuration
    experiment_config = {
        "config_path": str(config_path),
        "gold_standard_path": str(gold_standard_path),
        "sample_size": sample_size,
        "actual_sample_size": len(sample_df),
        "random_seed": random_seed,
        "layouts": layouts,
        "models": models,
        "timestamp": datetime.now().isoformat(),
    }
    with open(output_dir / "experiment_config.json", "w") as f:
        json.dump(experiment_config, f, indent=2)
    
    # Run experiments
    results = []
    total_experiments = len(layouts) * len(models)
    
    print(f"Running {total_experiments} experiments...")
    print(f"Layouts: {layouts}")
    print(f"Models: {models}")
    print(f"Sample size: {len(sample_df)}")
    print(f"Output directory: {output_dir}")
    print("-" * 80)
    
    for layout in layouts:
        for model in models:
            print(f"\nRunning experiment: {layout} with {model}")
            result = run_single_experiment(
                config=config,
                layout=layout,
                model=model,
                sample_df=sample_df,
                output_base=output_dir,
                gold_standard_file=str(gold_standard_path),
            )
            results.append(result)
            
            # Print summary
            if "error" not in result:
                print(f"  Accuracy: {result['accuracy']:.3f}")
                print(f"  F1 Score: {result['f1_score']:.3f}")
                print(f"  Duration: {result['duration_seconds']:.1f}s")
            else:
                print(f"  Error: {result['error']}")
    
    # Create results dataframe
    results_df = pd.DataFrame(results)
    
    # Save results
    results_df.to_csv(output_dir / "all_results.csv", index=False)
    
    # Create summary report
    create_summary_report(results_df, output_dir)
    
    return results_df


def create_summary_report(results_df: pd.DataFrame, output_dir: Path):
    """Create a summary report of the experiments."""
    
    # Filter out errors
    valid_results = results_df[~results_df["accuracy"].isna()].copy()
    
    if len(valid_results) == 0:
        print("No valid results to summarize.")
        return
    
    # Calculate summary statistics by layout
    layout_summary = valid_results.groupby("layout").agg({
        "accuracy": ["mean", "std", "min", "max"],
        "f1_score": ["mean", "std"],
        "duration_seconds": ["mean", "std"],
    }).round(3)
    
    # Calculate summary statistics by model
    model_summary = valid_results.groupby("model").agg({
        "accuracy": ["mean", "std", "min", "max"],
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
        f"Sample size: {valid_results['sample_size'].iloc[0] if len(valid_results) > 0 else 'N/A'}",
        "",
        "## Best Configuration",
        f"Layout: {best_config['layout']}",
        f"Model: {best_config['model']}",
        f"Accuracy: {best_config['accuracy']:.3f}",
        f"F1 Score: {best_config['f1_score']:.3f}",
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
    
    report_path = output_dir / "summary_report.txt"
    with open(report_path, "w") as f:
        f.write("\n".join(report_lines))
    
    print(f"\nSummary report saved to: {report_path}")
    
    # Also create a visual comparison if matplotlib is available
    try:
        import matplotlib.pyplot as plt
        
        # Create accuracy comparison plot
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Layout comparison
        layout_means = valid_results.groupby("layout")["accuracy"].mean().sort_values(ascending=False)
        ax1.bar(layout_means.index, layout_means.values)
        ax1.set_xlabel("Layout")
        ax1.set_ylabel("Mean Accuracy")
        ax1.set_title("Accuracy by Layout")
        ax1.set_ylim(0, 1)
        
        # Add value labels on bars
        for i, (layout, acc) in enumerate(layout_means.items()):
            ax1.text(i, acc + 0.01, f"{acc:.3f}", ha='center')
        
        # Model comparison
        model_means = valid_results.groupby("model")["accuracy"].mean().sort_values(ascending=False)
        ax2.bar(model_means.index, model_means.values)
        ax2.set_xlabel("Model")
        ax2.set_ylabel("Mean Accuracy")
        ax2.set_title("Accuracy by Model")
        ax2.set_ylim(0, 1)
        
        # Add value labels on bars
        for i, (model, acc) in enumerate(model_means.items()):
            ax2.text(i, acc + 0.01, f"{acc:.3f}", ha='center')
        
        plt.tight_layout()
        plt.savefig(output_dir / "accuracy_comparison.png", dpi=150)
        print(f"Visualization saved to: {output_dir / 'accuracy_comparison.png'}")
        
    except ImportError:
        print("Matplotlib not available, skipping visualization.")


def main():
    """Main entry point for the experiment script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run prompt layout experiments")
    parser.add_argument("--config", type=Path, required=True, help="Path to config JSON file")
    parser.add_argument("--gold-standard", type=Path, required=True, help="Path to gold standard CSV")
    parser.add_argument("--sample-size", type=int, default=100, help="Number of samples to test")
    parser.add_argument("--random-seed", type=int, default=42, help="Random seed for sampling")
    parser.add_argument("--layouts", nargs="+", help="Layouts to test (default: all)")
    parser.add_argument("--models", nargs="+", help="Models to test")
    parser.add_argument("--output-dir", type=Path, help="Output directory for results")
    
    args = parser.parse_args()
    
    results = run_experiments(
        config_path=args.config,
        gold_standard_path=args.gold_standard,
        sample_size=args.sample_size,
        random_seed=args.random_seed,
        layouts=args.layouts,
        models=args.models,
        output_dir=args.output_dir,
    )
    
    print("\nExperiment complete!")
    print(f"Results shape: {results.shape}")
    print(f"\nTop 3 configurations by accuracy:")
    top_results = results.nlargest(3, "accuracy")[["layout", "model", "accuracy", "f1_score"]]
    print(top_results.to_string(index=False))


if __name__ == "__main__":
    main() 