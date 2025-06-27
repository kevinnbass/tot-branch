# Annotation System Documentation

A comprehensive annotation system that creates bidirectional traceability between regex rules and LLM prompts, enabling sophisticated development workflows, automated validation, and performance analytics.

## 🎯 Overview

This annotation system solves the challenge of maintaining consistency between regex patterns and LLM prompts in a multi-hop classification pipeline. It provides:

- **Fine-grained mapping** between regex rules and specific prompt patterns
- **Automated validation** to prevent inconsistencies
- **Comprehensive documentation** generation
- **Development workflow tools** for efficient iteration
- **Advanced analytics** for performance optimization
- **CI/CD integration** for continuous quality assurance

## 📁 System Architecture

```
annotation_system/
├── 🔧 Core Files
│   ├── multi_coder_analysis/regex/hop_patterns.yml    # Regex rules with [Qn.x] annotations
│   ├── multi_coder_analysis/prompts/hop_Q*.txt       # Prompts with YAML front-matter
│   └── multi_coder_analysis/utils/prompt_loader.py   # Enhanced with comment stripping
├── 🛠️ Tools & Scripts
│   ├── scripts/validate_annotations.py               # Consistency validation
│   ├── scripts/generate_coverage_report.py           # Documentation generation
│   ├── scripts/annotation_dev_tools.py               # Development workflow tools
│   └── scripts/annotation_analytics.py               # Advanced analytics
├── 🧪 Testing & CI/CD
│   ├── tests/test_annotation_system.py               # Comprehensive unit tests
│   ├── .github/workflows/annotation_validation.yml   # GitHub Actions workflow
│   └── Makefile                                      # Convenient command interface
└── 📚 Generated Documentation
    └── docs/annotations/                              # Auto-generated reports
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone and set up the project
git clone <repository>
cd <project>

# Set up development environment
make dev-setup
```

### 2. Basic Usage

```bash
# Validate annotation consistency
make validate

# Test pattern matching
make test-pattern

# Generate documentation
make docs

# Run analytics
make analytics
```

### 3. Development Workflow

```bash
# Edit regex rules or prompts
vim multi_coder_analysis/regex/hop_patterns.yml
vim multi_coder_analysis/prompts/hop_Q01.txt

# Validate changes
make validate

# Test specific patterns
echo "The virus is extremely dangerous" | make test-pattern

# Update documentation
make docs
```

## 📋 Annotation Format

### Regex File Annotations

```yaml
# ── Hop 1 – Intensifier / Comparative + Risk-Adjective ────────────
# [Q1.1]  Intensifier + Risk-Adj      ↔  hop_Q01 row "Intensifier + Risk-Adj"
# [Q1.2]  Comparative + Risk-Adj      ↔  hop_Q01 row "Comparative + Risk-Adj"
1:
- name: IntensifierRiskAdjV2          # [Q1.1] [Q1.2]
  mode: live
  frame: Alarmist
  pattern: |-
    (?i)\b(?:very|extremely|highly)\s+(?:dangerous|deadly|severe)\b
```

### Prompt File Annotations

```yaml
---
meta_id: Q1
row_map:
  Q1.1: Intensifier + Risk-Adj
  Q1.2: Comparative + Risk-Adj
regex_map:
  Q1.1: [1.IntensifierRiskAdjV2]
  Q1.2: [1.IntensifierRiskAdjV2]
frame: Alarmist
summary: "Intensifier / comparative + risk-adjective"
---
### QUICK DECISION CHECK
<!-- Q1.1 -->
| **Intensifier + Risk-Adj** | "very dangerous," "extremely deadly" | ✓ |
<!-- Q1.2 -->
| **Comparative + Risk-Adj** | "more dangerous," "deadlier" | ✓ |
```

## 🔧 Tools Reference

### Validation (`validate_annotations.py`)

Ensures consistency between regex rules and prompt annotations.

```bash
# Basic validation
python scripts/validate_annotations.py

# CI mode (exit on errors)
python scripts/validate_annotations.py --ci

# Specific project root
python scripts/validate_annotations.py --project-root /path/to/project
```

**Checks performed:**
- YAML syntax validation
- Annotation format consistency
- Orphaned annotations detection
- Regex rule references validation
- Naming convention compliance

### Documentation Generation (`generate_coverage_report.py`)

Creates comprehensive documentation from annotations.

```bash
# Generate all documentation
python scripts/generate_coverage_report.py

# Custom output directory
python scripts/generate_coverage_report.py --output-dir custom/path
```

**Generated reports:**
- **Coverage Matrix**: Complete regex-to-prompt mapping
- **Dependency Graph**: Visual Mermaid diagrams
- **Gap Analysis**: LLM-only patterns and optimization opportunities
- **Performance Insights**: Complexity analysis and recommendations

### Development Tools (`annotation_dev_tools.py`)

Workflow tools for efficient development.

```bash
# Test pattern matching
python scripts/annotation_dev_tools.py test "The virus is extremely dangerous"

# Validate file on save
python scripts/annotation_dev_tools.py validate path/to/file

# Analyze diff impact
python scripts/annotation_dev_tools.py diff file.yml --old old_content --new new_content

# Generate IDE configuration
python scripts/annotation_dev_tools.py ide-config --ide vscode
```

### Advanced Analytics (`annotation_analytics.py`)

Sophisticated analysis and performance insights.

```bash
# Run full analytics suite
python scripts/annotation_analytics.py

# Custom output format
python scripts/annotation_analytics.py --format yaml --output report.yml
```

**Analytics features:**
- Coverage metrics and trends
- Performance profiling
- Git history evolution tracking
- Precision/recall analysis
- Maintenance automation insights

## 🧪 Testing

### Unit Tests

```bash
# Run all tests
make test

# Run with coverage
make test-coverage

# Run specific test class
python -m pytest tests/test_annotation_system.py::TestAnnotationValidator -v
```

### Integration Testing

```bash
# Test complete workflow
python -m pytest tests/test_annotation_system.py::TestIntegration -v

# Performance benchmarks
make benchmark
```

### Pattern Testing

```bash
# Interactive pattern testing
make test-pattern

# Programmatic testing
python scripts/annotation_dev_tools.py test "Your test text here"
```

## 🔄 CI/CD Integration

### GitHub Actions Workflow

The system includes a comprehensive GitHub Actions workflow (`.github/workflows/annotation_validation.yml`) that:

- **Validates annotations** on every push/PR
- **Tests pattern matching** with sample inputs
- **Runs unit tests** for all components
- **Generates documentation** automatically
- **Performs analytics** on schedule
- **Checks for breaking changes** in PRs
- **Benchmarks performance** for optimization
- **Creates issues** on validation failures

### Workflow Triggers

```yaml
# On file changes
on:
  push:
    paths:
      - 'multi_coder_analysis/regex/hop_patterns.yml'
      - 'multi_coder_analysis/prompts/hop_Q*.txt'

# Scheduled analytics
- cron: '0 2 * * *'  # Daily at 2 AM UTC

# Manual triggers
workflow_dispatch:
  inputs:
    run_full_analytics: boolean
    update_documentation: boolean
```

### Git Hooks

```bash
# Install git hooks for local validation
make install-hooks

# Hooks installed:
# - pre-commit: validation
# - pre-push: validation + tests
```

## 📊 Analytics & Insights

### Coverage Metrics

Track annotation coverage across the system:

```bash
# Quick coverage check
make check-coverage

# Detailed analytics
make analytics

# View summary
make analytics-summary
```

**Key metrics:**
- Overall coverage percentage
- Coverage by hop and frame type
- LLM-only pattern identification
- Rule-to-pattern ratios

### Performance Profiling

Monitor regex complexity and performance:

```bash
# Performance benchmark
make benchmark

# Check for high-complexity rules
make analytics | grep "high_complexity_rules"
```

**Performance indicators:**
- Complexity scores for regex patterns
- Pattern length analysis
- Execution time estimates
- Optimization recommendations

### Evolution Tracking

Analyze system changes over time:

- Git commit history analysis
- Growth metrics tracking
- Stability analysis
- Change frequency monitoring

## 🛠️ Development Workflows

### Adding New Patterns

1. **Add regex rule** with annotation:
   ```yaml
   - name: NewPatternRule          # [Q1.3]
     mode: live
     frame: Alarmist
     pattern: |-
       (?i)\bnew\s+pattern\b
   ```

2. **Update prompt metadata**:
   ```yaml
   row_map:
     Q1.3: New Pattern Type
   regex_map:
     Q1.3: [1.NewPatternRule]
   ```

3. **Add HTML comment** in prompt:
   ```html
   <!-- Q1.3 -->
   | **New Pattern Type** | "new pattern" | ✓ |
   ```

4. **Validate and test**:
   ```bash
   make validate
   make test-pattern
   ```

### Modifying Existing Patterns

1. **Check current coverage**:
   ```bash
   make check-coverage
   ```

2. **Make changes** to regex or prompt

3. **Analyze impact**:
   ```bash
   python scripts/annotation_dev_tools.py diff file.yml --old old --new new
   ```

4. **Validate changes**:
   ```bash
   make validate
   make test
   ```

### Debugging Patterns

```bash
# Debug specific rule
make debug-rule RULE=RuleName TEXT="test text"

# Test pattern interactively
make test-pattern

# Check rule complexity
make analytics | grep -A5 "high_complexity_rules"
```

## 🔍 Troubleshooting

### Common Issues

#### Validation Errors

```bash
# Error: Orphaned annotation
# Solution: Add corresponding row_map entry
```

#### Pattern Not Matching

```bash
# Debug pattern matching
python scripts/annotation_dev_tools.py test "your test text"

# Check regex syntax
python -c "import re; re.compile('your_pattern')"
```

#### Performance Issues

```bash
# Identify slow patterns
make analytics | grep "performance_bottlenecks"

# Run benchmark
make benchmark
```

### Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `Invalid YAML syntax` | Malformed YAML | Check syntax with YAML validator |
| `Orphaned annotation` | Missing row_map entry | Add corresponding prompt row |
| `Non-existent regex rule` | Invalid rule reference | Check rule name in regex file |
| `Performance warning` | Slow pattern matching | Optimize complex regex patterns |

## 📈 Best Practices

### Annotation Guidelines

1. **Use consistent numbering**: `Q1.1`, `Q1.2`, etc.
2. **Descriptive row names**: Clear, concise pattern descriptions
3. **Logical grouping**: Related patterns share annotation prefixes
4. **Regular validation**: Run `make validate` frequently

### Regex Optimization

1. **Avoid excessive complexity**: Target complexity score < 25
2. **Use specific patterns**: Prefer `\bword\b` over `.*word.*`
3. **Minimize backtracking**: Avoid nested quantifiers
4. **Test performance**: Use `make benchmark` regularly

### Documentation Maintenance

1. **Auto-generate docs**: Use `make docs` for consistency
2. **Update on changes**: Regenerate after modifications
3. **Review analytics**: Check `make analytics` monthly
4. **Monitor coverage**: Maintain >80% regex coverage

## 🤝 Contributing

### Development Setup

```bash
# Fork and clone repository
git clone your-fork-url
cd project

# Set up development environment
make dev-setup

# Install git hooks
make install-hooks
```

### Contribution Workflow

1. **Create feature branch**
2. **Make changes** following annotation guidelines
3. **Validate changes**: `make validate`
4. **Run tests**: `make test`
5. **Update documentation**: `make docs`
6. **Submit pull request**

### Code Review Checklist

- [ ] Annotations follow established format
- [ ] Validation passes without errors
- [ ] Tests cover new functionality
- [ ] Documentation updated
- [ ] Performance impact assessed

## 📚 Additional Resources

### External Documentation

- [YAML Specification](https://yaml.org/spec/)
- [Python Regex Documentation](https://docs.python.org/3/library/re.html)
- [Mermaid Diagram Syntax](https://mermaid-js.github.io/mermaid/)

### Internal Documentation

- [`docs/annotations/README.md`](docs/annotations/README.md) - Generated documentation index
- [`docs/annotations/coverage_matrix.md`](docs/annotations/coverage_matrix.md) - Complete coverage mapping
- [`docs/annotations/dependency_graph.md`](docs/annotations/dependency_graph.md) - Visual system relationships
- [`docs/annotations/gap_analysis.md`](docs/annotations/gap_analysis.md) - Coverage gaps and recommendations
- [`docs/annotations/performance_insights.md`](docs/annotations/performance_insights.md) - Performance analysis

### Support

For questions or issues:

1. Check this documentation
2. Run `make help` for command reference
3. Use `make example-workflow` for workflow examples
4. Review generated analytics reports
5. Create GitHub issue for bugs/feature requests

---

**Last updated:** Auto-generated by annotation system
**Version:** 1.0.0
**Maintainers:** Annotation System Team 