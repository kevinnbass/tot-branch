# Annotation System Documentation

*Generated: 2025-06-26 18:55:46*

This directory contains comprehensive documentation for the regex-prompt annotation system.

## 📊 Reports

- **[Coverage Matrix](coverage_matrix.md)**: Complete mapping between regex rules and prompt patterns
- **[Dependency Graph](dependency_graph.md)**: Visual representation of system relationships
- **[Gap Analysis](gap_analysis.md)**: Identifies patterns without regex coverage and optimization opportunities
- **[Performance Insights](performance_insights.md)**: Complexity analysis and optimization recommendations

## 📈 Quick Statistics

- **Hops**: 12
- **Regex Rules**: 29
- **Pattern Rows**: 45
- **Average Patterns per Hop**: 3.8

## 🔧 Maintenance

To regenerate this documentation:

```bash
python scripts/generate_coverage_report.py
```

To validate annotation consistency:

```bash
python scripts/validate_annotations.py --ci
```
