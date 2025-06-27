# Gap Analysis Report

*Generated: 2025-06-26 18:55:46*

## Patterns with No Regex Coverage (LLM-Only)

✅ All patterns have regex coverage!

## Over-Engineered Patterns (Multiple Regex Rules)

| Hop | Pattern | Description | Rule Count |
|-----|---------|-------------|------------|
| Q5 | Q5.1 | Direct Safety Assurances | 3 |
| Q5 | Q5.7 | Low-Risk Evaluation (+ Intensifier) | 3 |
| Q7 | Q7.3 | Risk Negations | 3 |
| Q1 | Q1.1 | Intensifier + Risk-Adj | 2 |
| Q2 | Q2.3 | Critical Alert Phrase | 2 |
| Q3 | Q3.1 | Moderate Verb (past-tense) + Scale | 2 |
| Q3 | Q3.2 | Moderate Verb (past-tense) + Quantity | 2 |
| Q4 | Q4.1 | Loaded Questions (Worry/Fear) | 2 |
| Q4 | Q4.2 | Loaded Questions (Inaction) | 2 |
| Q7 | Q7.1 | Expectation Negations | 2 |
| Q7 | Q7.2 | Evidence Negations | 2 |
| Q7 | Q7.4 | Capability Negations | 2 |

*Note: Multiple rules per pattern may indicate complexity or redundancy.*

## Recommendations

### High Priority
- Add regex rules for LLM-only patterns in hops Q1-Q3 (highest precedence)
- Review over-engineered patterns for potential consolidation

### Medium Priority
- Consider regex coverage for remaining LLM-only patterns
- Validate that multi-rule patterns don't have overlapping logic

### Low Priority
- Add performance benchmarks for complex regex rules
- Consider splitting complex patterns into sub-patterns
