# Performance Insights

*Generated: 2025-06-26 18:55:46*

## Regex Rule Complexity Analysis

### Most Complex Rules (Top 10)

| Hop | Rule Name | Pattern Length | Complexity Score | Has Veto |
|-----|-----------|----------------|------------------|----------|
| Q2 | `HighPotencyVerbMetaphor` | 2069 | 186 | ✓ |
| Q5 | `ExplicitCalming` | 1526 | 157 | — |
| Q7 | `BareNegationHealthConcern` | 1019 | 137 | — |
| Q9 | `NeutralPriceMetrics` | 841 | 91 | — |
| Q1 | `IntensifierRiskAdjV2` | 895 | 83 | ✓ |
| Q6 | `MinimiserScaleContrast` | 807 | 74 | — |
| Q4 | `LoadedQuestionAlarm` | 697 | 67 | — |
| Q8 | `CapabilityNoReassurance` | 357 | 52 | — |
| Q3 | `ModerateVerbPlusScale` | 527 | 50 | ✓ |
| Q7 | `BareNegation.NothingSuggests.Live` | 279 | 31 | — |

## Coverage Distribution by Hop

| Hop | Total Patterns | Regex Covered | Coverage % | Status |
|-----|----------------|---------------|------------|--------|
| Q1 | 3 | 3 | 100.0% | 🟢 |
| Q2 | 5 | 5 | 100.0% | 🟢 |
| Q3 | 2 | 2 | 100.0% | 🟢 |
| Q4 | 2 | 2 | 100.0% | 🟢 |
| Q5 | 8 | 8 | 100.0% | 🟢 |
| Q6 | 2 | 2 | 100.0% | 🟢 |
| Q7 | 4 | 4 | 100.0% | 🟢 |
| Q8 | 4 | 4 | 100.0% | 🟢 |
| Q9 | 4 | 4 | 100.0% | 🟢 |
| Q10 | 3 | 3 | 100.0% | 🟢 |
| Q11 | 4 | 4 | 100.0% | 🟢 |
| Q12 | 4 | 4 | 100.0% | 🟢 |

## Optimization Recommendations

### High Complexity Rules
Consider optimizing these rules for better performance:

- **HighPotencyVerbMetaphor** (Hop Q2): Complexity score 186
- **ExplicitCalming** (Hop Q5): Complexity score 157
- **BareNegationHealthConcern** (Hop Q7): Complexity score 137
- **NeutralPriceMetrics** (Hop Q9): Complexity score 91
- **IntensifierRiskAdjV2** (Hop Q1): Complexity score 83

### Long Pattern Rules
Consider breaking these into smaller, more focused rules:

- **HighPotencyVerbMetaphor** (Hop Q2): 2743 characters
- **ExplicitCalming** (Hop Q5): 1526 characters
- **BareNegationHealthConcern** (Hop Q7): 1019 characters
- **IntensifierRiskAdjV2** (Hop Q1): 1419 characters

### General Recommendations

1. **Profile regex performance** in production to identify bottlenecks
2. **Consider caching** compiled regex patterns for frequently used rules
3. **Monitor false positive rates** for complex rules with high complexity scores
4. **Implement timeout handling** for regex evaluation to prevent ReDoS attacks
