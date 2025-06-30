# JSON Layout Implementation for Enhanced Cue Detection

## Overview

This implementation adds fully parameterized JSON layouts for the enhanced cue detection system. The JSON layouts provide a more systematic and structured approach compared to the existing markdown-based layouts, while maintaining all the same rule information.

## New Layouts Added

1. **`cue_detection_enhanced_json`** - Single segment processing with JSON-structured rules
2. **`cue_detection_enhanced_json_batch`** - Batch processing with JSON-structured rules

## Key Components

### 1. JSON Prompt Builder (`multi_coder_analysis/utils/json_prompt_builder.py`)

A new module that:
- Loads the `enhanced_checklist_v2.json` file
- Extracts hop-specific rules and metadata
- Structures all information into a clean JSON format
- Eliminates loose prose in favor of structured data

Key functions:
- `build_json_prompt()` - Builds prompts for single segments
- `build_json_prompt_batch()` - Builds prompts for batch processing

### 2. Integration in `run_multi_coder_tot.py`

Added support for the new layouts in:
- `_assemble_prompt()` - For single segment processing
- `_assemble_prompt_batch()` - For batch processing

### 3. Structured JSON Format

The JSON structure includes:
```json
{
  "hop_id": "Q1",
  "frame": "Alarmist",
  "summary": "Intensifier / comparative + risk-adjective",
  "quick_check": "• Contains INTENSIFIER...",
  "patterns": {
    "Q1.1": {"id": "Q1.1", "label": "Intensifier + Risk-Adj", "active": true},
    "Q1.2": {"id": "Q1.2", "label": "Comparative + Risk-Adj", "active": true}
  },
  "pattern_table": [...],
  "rules": {
    "inclusion": [{"text": "...", "type": "general"}],
    "exclusion": [{"text": "...", "type": "general"}],
    "special": [...],
    "precedence": [...]
  },
  "examples": {
    "positive": [...],
    "negative": [...]
  },
  "guards": [...],
  "clarifications": [...]
}
```

## Benefits of JSON Layout

1. **Systematic Structure** - All rules are parameterized, no loose prose
2. **Programmatic Control** - Easy to add/remove sections for experiments
3. **Token Efficiency** - Can selectively include/exclude sections
4. **Consistency** - Same structure across all hops
5. **A/B Testing** - Easy to compare with enhanced layout performance

## Usage

To use the JSON layouts, specify the layout parameter in your command:

```bash
# Single segment processing
python -m multi_coder_analysis.main --layout cue_detection_enhanced_json ...

# Batch processing
python -m multi_coder_analysis.main --layout cue_detection_enhanced_json_batch --batch-size 10 ...
```

## Comparison with Enhanced Layout

| Feature | Enhanced Layout | JSON Layout |
|---------|----------------|-------------|
| Rule Format | Markdown with prose | Structured JSON |
| Token Count | ~7,670 chars | ~9,531 chars (includes structure) |
| Modifiability | Edit text files | Programmatic control |
| Consistency | Varies by hop | Uniform structure |
| Examples | Inline prose | Structured array |

## Future Enhancements

1. **Selective Inclusion** - Add CLI flags to include/exclude sections:
   - `--include-examples=false` - Remove examples to save tokens
   - `--include-guards=false` - Remove guard conditions
   - `--minimal-rules` - Include only essential rules

2. **Compression** - The JSON format is currently verbose but could be compressed

3. **Caching** - Pre-compute structured data for faster prompt generation

## Testing

Run the test script to see the difference between layouts:

```bash
python test_json_layouts.py
```

This will show side-by-side comparisons of:
- Single segment prompts (enhanced vs JSON)
- Batch prompts (JSON format)
- Token/character counts for each 