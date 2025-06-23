# Regex Mining Report

## Promoted

| Rule | Hop | Frame | Prec | Rec | Support | Pattern |
|------|-----|-------|------|-----|---------|---------|
| H1.AutoIntensifierRiskAdj | 1 | Alarmist | 1.000 | 0.260 | 127 | `(?:highly|particularly)\s+(?:contagious|dangerous|deadly|infectious|lethal|transmissible)\b` |

## Rejected

| Desc | Hop | Frame | Prec | Rec | Pattern |
|------|-----|-------|------|-----|---------|
| ScaleCue | 3 | Alarmist | 1.000 | 0.016 | `\b(hit|soared)\b[^\.]{0,120}\b(largest|million|millions|unprecedented)\b` |
| ScaleCue | 6 | Alarmist | 1.000 | 0.016 | `\b(hit|soared)\b[^\.]{0,120}\b(largest|million|millions|unprecedented)\b` |
| DestructiveVerb | 2 | Alarmist | 1.000 | 0.047 | `\b(crippled|decimated|nosedived|overwhelmed|ravaged|skyrocketed|slammed|tanked|wreak(?:ed)?\s+havoc)\b` |
| PanicVerbNoun | 2 | Alarmist | 0.000 | 0.000 | `\b(spark|reignite|stoke|fuel|ignite)\b\s+(fear|outrage|anxiety|alarm|panic)\b` |
| KillNumber | 3 | Alarmist | 0.323 | 0.079 | `\b(?:kill(?:ed)?|cull(?:ed)?|destroy(?:ed)?|euthani[sz]ed)\b[^\.]{0,40}\b(?:\d{1,3}(?:,\d{3})+|millions?|thousands?)\b` |
| Preparedness | 5 | Reassuring | 0.000 | 0.000 | `\b(?:fully|well)\s+(?:prepared|ready)\b.{0,30}\b(?:handle|deal\s+with|for)\b` |
| NoCauseAlarm | 5 | Reassuring | 0.000 | 0.000 | `\bno\s+cause\s+for\s+alarm\b` |
| MinimiserPercent | 6 | Reassuring | 0.000 | 0.000 | `\b(?:only|just|merely)\s+\d{1,3}(?:\.\d+)?\s*%` |
| RiskNegation | 7 | Neutral | 1.000 | 0.008 | `\b(?:do|does|did|is|are|was|were|will|would|should)\s+(?:not|n't)\s+(?:pose|present|constitute)\s+(?:an?\s+)?(?:immediate\s+)?(?:public\s+)?health\s+concern\b` |
| FoodChainNeg | 7 | Neutral | 1.000 | 0.004 | `\b(?:will|would|can|could)\s+not\s+enter\s+the\s+food\s+(?:system|chain|supply)\b` |
| TestNegative | 7 | Neutral | 1.000 | 0.001 | `\b(?:tests?|samples?)\s+(?:came|come|were|was)\s+negative\b` |
| PricePercent | 9 | Neutral | 0.000 | 0.000 | `\b(soared)\b[^\.]{0,30}\d{1,3}(?:\.\d+)?\s*%` |
| PercentBaseline | 9 | Neutral | 0.000 | 0.000 | `\d{1,3}(?:\.\d+)?\s*%\s+of\s+(?:normal|capacity|last\s+year)` |
| HistoricalComp | 10 | Neutral | 1.000 | 0.001 | `\b(?:compared\s+with|versus|vs\.?|from)\s+(?:last|previous)\s+year\b` |
