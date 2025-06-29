# Layout Experiment Configuration Guide

## Overview

The layout experiment system now supports configuration files for hierarchical batch testing of prompt layout variations. This allows you to:

1. Define multiple experimental phases
2. Control which layouts are tested
3. Set different sample sizes for different phases
4. Enable/disable batches without code changes
5. Optimize API costs through smart testing strategies

## Quick Start

### Using the Default Config

```bash
# Run with the default layout_experiment_config.yaml
python -m multi_coder_analysis.main \
    --use-tot \
    --input data/gold_standard.csv \
    --gold-standard data/gold_standard.csv \
    --provider gemini \
    --model "models/gemini-2.0-flash" \
    --layout-experiment \
    --layout-config layout_experiment_config.yaml
```

### Using Environment Variables

```bash
# Alternative: specify config via environment variable
export LAYOUT_CONFIG=my_experiment.yaml
python -m multi_coder_analysis.main --use-tot --layout-experiment ...
```

## Configuration File Structure

```yaml
# Layout Experiment Configuration
experiment:
  name: "minimal_system_variations_phase1"
  description: "Testing user prompt variations with minimal system prompt"
  base_config:
    batch_size: 259
    concurrency: 3
    regex_mode: "live"

# Define experimental batches
batches:
  phase1_batch1:
    enabled: true
    description: "Core structure tests"
    sample_size: 50  # Smaller sample for initial testing
    layouts:
      - name: "minimal_segment_first"
        description: "Segment before hop content"
        base_layout: "minimal_system"
      
      - name: "minimal_question_twice"
        description: "Question at start and end"
        base_layout: "minimal_system"
      # ... more layouts

  phase2_refinements:
    enabled: false  # Will enable after phase 1 results
    sample_size: 100
    layouts:
      # ... refinement layouts

execution:
  parallel_workers: 6  # Run 6 layouts simultaneously
  fail_fast: true     # Stop batch if any layout fails
  
analysis:
  primary_metrics: ["accuracy", "avg_f1"]
  comparison_threshold: 0.002  # 0.2% improvement threshold
```

## Hierarchical Testing Strategy

### Phase 1: High-Impact Structural Changes (6 variants)

Test fundamentally different approaches to identify the best structural paradigm:

1. **`minimal_segment_first`** - Tests recency effect
2. **`minimal_question_twice`** - Tests primacy-recency
3. **`minimal_json_segment`** - Tests structured format benefit
4. **`minimal_parallel_criteria`** - Tests explicit decision framing
5. **`minimal_hop_sandwich`** - Tests hop content repetition
6. **`minimal_system`** - Baseline for comparison

### Phase 2: Winner Refinements

Based on Phase 1 results, refine the winning approach:

- If segment-first wins → test highlighting, IDs, positioning
- If question-twice wins → test emphasis, compression, hints
- If JSON wins → test array vs object, metadata inclusion
- etc.

### Phase 3: Micro-Optimizations

Fine-tune the best variant from Phase 2 with small tweaks.

## New Layout Implementations

### Minimal System Variations

All variations use the minimal system prompt:
```
You are an expert claim-framing coder following a mandatory 12-step decision tree.
```

Then vary the user prompt structure:

**`minimal_segment_first`**:
```
[HEADER]
[SEGMENT]
[HOP CONTENT]
[FOOTER]
```

**`minimal_question_twice`**:
```
[HEADER]
[QUESTION]
[SEGMENT]
[HOP CONTENT]
REMEMBER: [QUESTION]
[FOOTER]
```

**`minimal_json_segment`**:
```
[HEADER]
Analyze this segment:
```json
{
  "segment_id": "...",
  "content": "...",
  "task": "Answer Question Q1"
}
```
[HOP CONTENT]
[FOOTER]
```

**`minimal_parallel_criteria`**:
```
[HEADER]
SEGMENT: ...
Analyze by considering:
• Would indicate YES if: [criteria]
• Would indicate NO if: [criteria]
• Would be UNCERTAIN if: [neither]
[HOP CONTENT]
[FOOTER]
```

**`minimal_hop_sandwich`**:
```
[HEADER]
[QUESTION]
[RULES]
[EXAMPLES]
=== ANALYZE THESE SEGMENTS ===
[SEGMENT]
=== REMEMBER THE QUESTION ===
[QUESTION]
REMINDER: [RULES]
[FOOTER]
```

## Running Specific Batches

### Run Only Phase 1
```yaml
batches:
  phase1_batch1:
    enabled: true
  phase2_refinements:
    enabled: false  # Disabled
```

### Run With Different Sample Sizes
```yaml
batches:
  quick_test:
    enabled: true
    sample_size: 10  # Very small for testing
  full_test:
    enabled: true 
    sample_size: 259  # Full dataset
```

## Analyzing Results

Results are saved to:
```
output/layout_experiments/[timestamp]/
├── layout_config.yaml          # Copy of config used
├── experiment_config.json      # Runtime parameters
├── all_results.csv            # Raw results
├── comparison_summary.csv     # Metrics summary
├── comparison_report.txt      # Human-readable report
├── summary.json              # Machine-readable summary
└── [layout_name]/            # Per-layout results
    ├── model_labels_tot.csv
    ├── comparison.csv
    └── traces_tot/
```

## Best Practices

1. **Start Small**: Use small sample_size (10-50) for initial tests
2. **Test Incrementally**: Enable one batch at a time
3. **Document Rationale**: Use descriptive names and descriptions
4. **Track Iterations**: Save config files with results
5. **Analyze Patterns**: Look for consistent improvements across metrics

## Example: Running a Quick Test

```bash
# 1. Create a test config
cat > quick_test.yaml << EOF
experiment:
  name: "quick_phase1_test"
  
batches:
  test_batch:
    enabled: true
    sample_size: 5  # Just 5 samples
    layouts:
      - name: "minimal_system"
      - name: "minimal_segment_first"
      - name: "minimal_question_twice"

execution:
  parallel_workers: 3
EOF

# 2. Run the test
python -m multi_coder_analysis.main \
    --use-tot \
    --input data/test.csv \
    --gold-standard data/test.csv \
    --layout-experiment \
    --layout-config quick_test.yaml \
    --provider gemini \
    --model "models/gemini-2.0-flash"

# 3. Check results
cat output/layout_experiments/*/comparison_report.txt
```

## Troubleshooting

### Layout Not Found
If you get "Unknown layout" warnings, ensure:
1. Layout name is in VALID_LAYOUTS in run_multi_coder_tot.py
2. Layout implementation exists in _assemble_prompt() 
3. Batch implementation exists in _assemble_prompt_batch()

### Config Not Loading
Check:
1. YAML syntax is valid
2. File path is correct
3. Required fields are present

### Performance Issues
- Reduce parallel_workers if hitting rate limits
- Decrease sample_size for faster iteration
- Use fail_fast=true to stop on errors 