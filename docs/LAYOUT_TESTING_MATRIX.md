# Layout Testing Matrix

## Test Dimensions

### Batch Size Categories
- Small: 1-10 segments
- Medium: 11-50 segments  
- Large: 51-100 segments
- XLarge: 101-200 segments
- XXLarge: 200+ segments

### Segment Complexity
- Simple: Single sentence, clear claim
- Medium: Paragraph with context
- Complex: Multiple claims, nuanced
- Adversarial: Contradictory information

### Question Types
- Binary: Clear yes/no questions (Q1-Q10)
- Token-based: Requires specific token (Q11)
- Default: No triggers expected (Q12)

## Recommended Test Combinations

| Layout | Best For | Avoid For | Priority |
|--------|----------|-----------|----------|
| hop_last | Large batches, Binary questions | Token-based (Q11) | HIGH |
| structured_json | XLarge batches, All questions | Small batches | HIGH |
| evidence_based | Complex segments, All questions | Speed critical | HIGH |
| primacy_recency | Medium batches, Important questions | XXLarge batches | MEDIUM |
| xml_structured | Large batches, Structured analysis | Simple segments | MEDIUM |
| parallel_analysis | Binary questions, Clear criteria | Token-based | MEDIUM |
| segment_focus | Visual debugging, All sizes | Production use | LOW |
| instruction_first | Clear tasks, Medium batches | Complex questions | LOW |

## Performance Metrics to Track

1. **Accuracy Metrics**
   - Overall accuracy
   - Per-frame F1 scores
   - Uncertain response rate

2. **Consistency Metrics**
   - Cross-segment consistency
   - Batch position bias
   - Layout stability

3. **Efficiency Metrics**
   - Tokens per segment
   - Response time
   - Retry rate

4. **Error Metrics**
   - JSON parsing errors
   - Missing segments
   - Timeout rate

## Quick Test Command

```bash
# Test high-priority layouts on medium batch
python scripts/run_all_layouts_experiment.py \
    --layouts hop_last structured_json evidence_based \
    --input data/test_segments.csv \
    --start 1 --end 50 \
    --batch-size 25 \
    --sequential
```
