# Complete Layout Comparison

## Overview
This document provides a detailed comparison of all 13 prompt layouts (5 original + 8 new).

## Layout Comparison Table

| Layout | Segment Position | Question Position | Batch Support | Key Feature |
|--------|-----------------|-------------------|---------------|-------------|
| standard | Middle of prompt | Beginning | ✅ Full | Baseline |
| recency | Beginning | After segment | ✅ Full | Recency bias |
| sandwich | Middle | Quick→Segment→Detail | ⚠️ Fallback | Two-pass |
| minimal_system | Middle | Beginning | ✅ Full | Token efficient |
| question_first | After question | Beginning | ⚠️ Fallback | Question prominence |
| **hop_last** | Beginning | End | ✅ Full | Maximum recency |
| **structured_json** | JSON format | After JSON | ✅ Full | Structured data |
| **segment_focus** | Visual box | After segment | ✅ Full | Visual clarity |
| **instruction_first** | After instruction | Beginning | ✅ Full | Task clarity |
| **parallel_analysis** | Beginning | Framework format | ✅ Full | Decision framework |
| **evidence_based** | Step 1 | Step 3 | ✅ Full | Evidence first |
| **xml_structured** | XML element | XML element | ✅ Full | Hierarchical |
| **primacy_recency** | Middle | Start + End | ✅ Full | Dual emphasis |

## Detailed Analysis

### Position-Based Layouts

**Recency Group** (segment last or question last):
- `recency`: Segment → Question
- `hop_last`: Segment → Question (at very end)
- Good for: Recent information bias, segment-focused tasks

**Primacy Group** (question first):
- `question_first`: Question → Segment
- `instruction_first`: Instruction → Question → Segment
- `primacy_recency`: Question → Segment → Question
- Good for: Task clarity, question-focused analysis

### Structure-Based Layouts

**Formatted Data**:
- `structured_json`: JSON format
- `xml_structured`: XML format
- Good for: Clear data boundaries, parser-friendly

**Visual Separation**:
- `segment_focus`: Box drawing characters
- `sandwich`: Section markers
- Good for: Human readability, clear sections

### Process-Based Layouts

**Analytical Framework**:
- `parallel_analysis`: YES/NO/UNCERTAIN framework
- `evidence_based`: Extract → Apply → Decide
- Good for: Systematic analysis, reasoning transparency

## Recommendations by Use Case

### For Maximum Accuracy
1. `primacy_recency` - Question reinforcement
2. `evidence_based` - Forced evidence extraction
3. `parallel_analysis` - Clear decision framework

### For Large Batches (200+ segments)
1. `structured_json` - Efficient parsing
2. `xml_structured` - Clear hierarchy
3. `hop_last` - Simple and effective

### For Token Efficiency
1. `minimal_system` - Minimal system prompt
2. `hop_last` - No redundancy
3. `instruction_first` - Compressed instructions

### For Debugging
1. `evidence_based` - Shows reasoning steps
2. `segment_focus` - Visual clarity
3. `xml_structured` - Machine-parseable

## Implementation Notes

- All layouts are **lossless** - no information is removed
- 11/13 layouts have full batch support
- Batch size may affect optimal layout choice
- Some layouts may work better with specific question types

## Testing Strategy

1. Start with small subset (20-50 segments)
2. Test all 13 layouts in parallel
3. Measure: accuracy, F1, token usage, response time
4. Select top 3-5 for larger dataset
5. Consider question-specific optimization
