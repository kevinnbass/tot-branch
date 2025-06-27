# Regex-Prompt Coverage Matrix

*Generated: 2025-06-26 18:55:46*

## Complete Coverage Mapping

| Hop | Pattern Row | Description | Regex Rules | Mode | Frame |
|-----|-------------|-------------|-------------|------|-------|
| Q1 | Q1.1 | Intensifier + Risk-Adj | `IntensifierRiskAdjV2` (live, Alarmist)<br>`H1.AutoIntensifierRiskAdj` (live, Alarmist) | | |
| Q1 | Q1.2 | Comparative + Risk-Adj | `IntensifierRiskAdjV2` (live, Alarmist) | | |
| Q1 | Q1.3 | Fixed Lethal-from-Outset Idiom | `IntensifierRiskAdjV2` (live, Alarmist) | | |
| Q2 | Q2.1 | High-Potency Verbs | `HighPotencyVerbMetaphor` (live, Alarmist) | | |
| Q2 | Q2.2 | Superlative + Negative Noun | `HighPotencyVerbMetaphor` (live, Alarmist) | | |
| Q2 | Q2.3 | Critical Alert Phrase | `OnHighAlert.Live` (live, Alarmist)<br>`HighPotencyVerbMetaphor` (live, Alarmist) | | |
| Q2 | Q2.4 | Potent Metaphors | `HighPotencyVerbMetaphor` (live, Alarmist) | | |
| Q2 | Q2.5 | Intensifier + Harm Noun | `HighPotencyVerbMetaphor` (live, Alarmist) | | |
| Q3 | Q3.1 | Moderate Verb (past-tense) + Scale | `ModerateVerbPlusScale` (live, Alarmist)<br>`ScaleMultiplier` (live, Alarmist) | | |
| Q3 | Q3.2 | Moderate Verb (past-tense) + Quantity | `ModerateVerbPlusScale` (live, Alarmist)<br>`ScaleMultiplier` (live, Alarmist) | | |
| Q4 | Q4.1 | Loaded Questions (Worry/Fear) | `LoadedQuestionAlarm` (live, Alarmist)<br>`WhatIfQuestion` (live, Alarmist) | | |
| Q4 | Q4.2 | Loaded Questions (Inaction) | `LoadedQuestionAlarm` (live, Alarmist)<br>`IgnoreDisasterQ` (live, Alarmist) | | |
| Q5 | Q5.1 | Direct Safety Assurances | `ExplicitCalming` (live, Reassuring)<br>`DirectNoConcern.Live` (live, Reassuring)<br>`NothingToWorry.Live` (live, Reassuring) | | |
| Q5 | Q5.2 | Supply-Safety Assurances | `ExplicitCalming` (live, Reassuring) | | |
| Q5 | Q5.3 | Confidence Statements | `ExplicitCalming` (live, Reassuring) | | |
| Q5 | Q5.4 | Calming Idioms | `ExplicitCalming` (live, Reassuring) | | |
| Q5 | Q5.5 | Direct Consumption Safety | `ExplicitCalming.SafeToEat.Live` (live, Reassuring) | | |
| Q5 | Q5.6 | Preparedness Calming Cue | `ExplicitCalming` (live, Reassuring) | | |
| Q5 | Q5.7 | Low-Risk Evaluation (+ Intensifier) | `ExplicitCalming` (live, Reassuring)<br>`LowRiskEval.Theoretical` (live, Reassuring)<br>`LowRiskSimple` (live, Reassuring) | | |
| Q5 | Q5.8 | Positive Amplification | `ExplicitCalming` (live, Reassuring) | | |
| Q6 | Q6.1 | Minimiser + Scale Contrast | `MinimiserScaleContrast` (live, Reassuring) | | |
| Q6 | Q6.2 | Minimiser + Explicit Comparison | `MinimiserScaleContrast` (live, Reassuring) | | |
| Q7 | Q7.1 | Expectation Negations | `BareNegationHealthConcern` (live, Neutral)<br>`BareNegation.NothingSuggests.Live` (live, Neutral) | | |
| Q7 | Q7.2 | Evidence Negations | `BareNegationHealthConcern` (live, Neutral)<br>`BareNegation.NoFurtherCases.Live` (live, Neutral) | | |
| Q7 | Q7.3 | Risk Negations | `BareNegationHealthConcern` (live, Neutral)<br>`BareNegation.PosesNoRisk.Live` (live, Neutral)<br>`NoThreatNeutral.Live` (live, Neutral) | | |
| Q7 | Q7.4 | Capability Negations | `BareNegationHealthConcern` (live, Neutral)<br>`BareNegation.NotContaminate.Live` (live, Reassuring) | | |
| Q8 | Q8.1 | Development Capabilities | `CapabilityNoReassurance` (shadow, Neutral) | | |
| Q8 | Q8.2 | Response Measures | `CapabilityNoReassurance` (shadow, Neutral) | | |
| Q8 | Q8.3 | Preparedness Statements | `CapabilityNoReassurance` (shadow, Neutral) | | |
| Q8 | Q8.4 | Future Possibilities | `CapabilityNoReassurance` (shadow, Neutral) | | |
| Q9 | Q9.1 | Standard Economic Verbs | `NeutralPriceMetrics` (live, Neutral) | | |
| Q9 | Q9.2 | Neutral Adverbs | `NeutralPriceMetrics` (live, Neutral) | | |
| Q9 | Q9.3 | Factual Quantification | `NeutralPriceMetrics` (live, Neutral) | | |
| Q9 | Q9.4 | Volatility adjective (mild) | `NeutralPriceMetrics` (live, Neutral) | | |
| Q10 | Q10.1 | Future Relief Speculation | `ReliefSpeculation` (live, Neutral) | | |
| Q10 | Q10.2 | Hopeful Predictions | `ReliefSpeculation` (live, Neutral) | | |
| Q10 | Q10.3 | Timeline Speculation | `ReliefSpeculation` (live, Neutral) | | |
| Q11 | Q11.1 | Alarmist – Dominant Quote | `DominantQuoteAlarmist` (live, Alarmist) | | |
| Q11 | Q11.2 | Alarmist – Intensified High-Risk | `DominantQuoteAlarmist` (live, Alarmist) | | |
| Q11 | Q11.3 | Dominant Reassuring Quote | `DominantQuoteReassuring` (live, Reassuring) | | |
| Q11 | Q11.4 | Neutral – Bare risk-adj in quote | `BaseRiskAdjQuoteNeutral` (live, Neutral) | | |
| Q12 | Q12.1 | Factual Reporting | `NeutralStats` (live, Neutral) | | |
| Q12 | Q12.2 | Technical Descriptions | `NeutralStats` (live, Neutral) | | |
| Q12 | Q12.3 | Standard Procedures | `NeutralStats` (live, Neutral) | | |
| Q12 | Q12.4 | Neutral Metrics | `NeutralStats` (live, Neutral) | | |

## Coverage Statistics

- **Total Pattern Rows**: 45
- **Total Regex Rules**: 29
- **LLM-Only Patterns**: 0
- **Regex Coverage**: 100.0%
