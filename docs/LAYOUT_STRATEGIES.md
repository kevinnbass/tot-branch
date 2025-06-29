# Prompt Layout Strategies Documentation

## Overview

The prompt layout system allows you to experiment with different ways of structuring prompts to optimize LLM performance. Each layout strategy arranges the system prompt, user prompt, question, and segment text in different orders to test various cognitive biases and processing patterns.

## Available Layouts

### 1. Standard Layout (Default)
- **Structure**: System prompt → Question → Segment → Footer
- **Use Case**: Baseline configuration, follows traditional prompt structure
- **Characteristics**: 
  - Clear separation between system and user roles
  - Question presented before segment for context
  - Well-tested and stable

### 2. Recency Layout
- **Structure**: System prompt → Segment → Question → Footer
- **Use Case**: Tests recency bias by placing segment before question
- **Characteristics**:
  - May improve attention to segment details
  - Could reduce question-guided bias
  - Useful for exploratory analysis

### 3. Sandwich Layout
- **Structure**: System prompt → Quick Check → Question → Segment → Detailed Analysis → Footer
- **Use Case**: Two-pass analysis with quick decision followed by detailed reasoning
- **Characteristics**:
  - Enables fast filtering with quick check
  - Provides structured reasoning flow
  - Good for hierarchical decision making
- **Requirements**: Prompts must include "QUICK DECISION CHECK" or "⚡" markers

### 4. Minimal System Layout
- **Structure**: Minimal system prompt → All content in user prompt
- **Use Case**: Tests impact of minimal system instructions
- **Characteristics**:
  - Reduces system prompt to bare minimum
  - May improve token efficiency
  - Tests LLM's ability to follow instructions without extensive system context

### 5. Question First Layout
- **Structure**: System prompt → Question (highlighted) → Instructions → Segment → Footer
- **Use Case**: Emphasizes the question by presenting it first and prominently
- **Characteristics**:
  - May improve question comprehension
  - Reduces chance of missing the question
  - Good for complex questions
- **Requirements**: Prompts must include "### Question Q" markers

## Usage Examples

### Basic Usage
```python
# Single layout
run_coding_step_tot(
    config=config,
    input_csv_path=input_file,
    output_dir=output_dir,
    layout="recency",  # Specify layout
    # ... other parameters
)
```

### Layout Experiment
```python
# Run all layouts and compare
python main.py --use-tot --layout-experiment --gold-standard data/gold.csv
```

### Batch Processing Considerations
- Some layouts work better with `batch_size=1`
- Sandwich and question_first layouts may need single-segment processing
- Standard and minimal_system layouts work well with batching

## Best Practices

1. **Start with Standard**: Always establish baseline with standard layout
2. **Single Variable Testing**: Change only layout when comparing
3. **Sufficient Sample Size**: Use at least 100 samples for meaningful comparison
4. **Statistical Significance**: Use built-in statistical tests to validate differences
5. **Prompt Compatibility**: Ensure prompts are compatible with chosen layout

## Performance Considerations

- **Token Usage**: Minimal system layout uses fewer tokens
- **Processing Time**: Sandwich layout may take longer due to two-pass structure
- **Accuracy**: Results vary by task; no universal "best" layout
- **Caching**: Results are cached to avoid rerunning identical experiments

## Troubleshooting

### Common Issues

1. **"Unknown layout" warning**
   - Ensure layout name is spelled correctly
   - Valid options: standard, recency, sandwich, minimal_system, question_first

2. **Poor performance with specific layout**
   - Check prompt compatibility
   - Verify batch_size settings
   - Review layout requirements

3. **Batch processing errors**
   - Some layouts require batch_size=1
   - Check error logs for specific issues

## Advanced Configuration

### Custom Layouts
To add a custom layout:

1. Modify `_assemble_prompt()` in `run_multi_coder_tot.py`
2. Add layout logic in the function
3. Update `VALID_LAYOUTS` constant
4. Test thoroughly with various prompts

### Layout-Specific Metrics
The system tracks layout-specific metrics:
- Segment position ratios
- System/user prompt ratios
- Quick check effectiveness (sandwich layout)
- Question prominence (question_first layout)

## Future Enhancements

- Dynamic layout selection based on segment characteristics
- Layout ensembling for improved accuracy
- Automatic layout optimization
- Custom layout builder UI
