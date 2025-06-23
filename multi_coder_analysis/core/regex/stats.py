from __future__ import annotations

"""Regex engine statistics and reporting utilities."""

from collections import Counter
from typing import Dict, Any
import json
from pathlib import Path


def format_rule_stats(stats: Dict[str, Counter]) -> Dict[str, Any]:
    """Format rule statistics for human-readable output.
    
    Args:
        stats: Dictionary mapping rule names to hit/total counters.
        
    Returns:
        Formatted statistics with coverage percentages.
    """
    formatted = {}
    total_evaluations = 0
    total_hits = 0
    
    for rule_name, counter in stats.items():
        hits = counter.get("hit", 0)
        total = counter.get("total", 0)
        coverage = (hits / total * 100) if total > 0 else 0.0
        
        formatted[rule_name] = {
            "hits": hits,
            "total_evaluations": total,
            "coverage_percent": round(coverage, 2)
        }
        
        total_evaluations += total
        total_hits += hits
    
    # Add overall summary
    overall_coverage = (total_hits / total_evaluations * 100) if total_evaluations > 0 else 0.0
    formatted["_summary"] = {
        "total_rules": len(stats),
        "total_hits": total_hits,
        "total_evaluations": total_evaluations,
        "overall_coverage_percent": round(overall_coverage, 2)
    }
    
    return formatted


def export_stats_to_json(stats: Dict[str, Counter], output_path: Path) -> None:
    """Export rule statistics to a JSON file.
    
    Args:
        stats: Rule statistics from Engine.get_rule_stats().
        output_path: Path where to write the JSON file.
    """
    formatted = format_rule_stats(stats)
    
    with output_path.open('w', encoding='utf-8') as f:
        json.dump(formatted, f, indent=2, ensure_ascii=False)


def print_stats_summary(stats: Dict[str, Counter]) -> None:
    """Print a human-readable summary of rule statistics.
    
    Args:
        stats: Rule statistics from Engine.get_rule_stats().
    """
    formatted = format_rule_stats(stats)
    summary = formatted.pop("_summary")
    
    print(f"\n📊 Regex Engine Statistics Summary")
    print(f"{'='*50}")
    print(f"Total rules: {summary['total_rules']}")
    print(f"Total evaluations: {summary['total_evaluations']}")
    print(f"Total hits: {summary['total_hits']}")
    print(f"Overall coverage: {summary['overall_coverage_percent']:.2f}%")
    print()
    
    if formatted:
        print("Per-rule breakdown:")
        print(f"{'Rule Name':<30} {'Hits':<8} {'Total':<8} {'Coverage':<10}")
        print("-" * 60)
        
        # Sort by coverage descending
        sorted_rules = sorted(
            formatted.items(),
            key=lambda x: x[1]["coverage_percent"],
            reverse=True
        )
        
        for rule_name, data in sorted_rules:
            print(f"{rule_name:<30} {data['hits']:<8} {data['total_evaluations']:<8} {data['coverage_percent']:<10.2f}%")


__all__ = ["format_rule_stats", "export_stats_to_json", "print_stats_summary"] 