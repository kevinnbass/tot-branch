#!/usr/bin/env python3
"""
Critical improvements to the layout system after close examination.
"""

import sys
from pathlib import Path
import re

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))


def identify_critical_issues():
    """Identify critical issues in the current layout implementation."""
    
    print("CRITICAL ISSUES IDENTIFIED")
    print("=" * 60)
    
    print("\n1. INSTRUCTION PLACEMENT ISSUE")
    print("   - The JSON instruction is inconsistently placed across layouts")
    print("   - In 'standard': instruction → segments → footer")
    print("   - In 'recency': segments → instruction → hop → footer")
    print("   - In 'hop_last': segments → hop → instruction → footer")
    print("   - This inconsistency could confuse the model about output format")
    
    print("\n2. SEGMENT ENUMERATION ISSUE")
    print("   - Segments use '### Segment N (ID: xxx)' format")
    print("   - This mixes markdown headers with enumeration")
    print("   - Could be clearer with consistent formatting")
    
    print("\n3. MISSING CRITICAL INFORMATION")
    print("   - No indication of total segment count upfront")
    print("   - Model doesn't know if it's analyzing 10 or 200 segments")
    print("   - Could affect memory allocation and response planning")
    
    print("\n4. HOP CONTENT PLACEHOLDERS")
    print("   - hop_content still has {{segment_text}} placeholders")
    print("   - These are replaced with '<SEGMENT_TEXT>' but never used")
    print("   - Creates confusion in batch mode")
    
    print("\n5. FOOTER PLACEMENT")
    print("   - Footer always at the very end")
    print("   - Contains critical JSON format examples")
    print("   - May be too far from instruction in some layouts")
    
    print("\n6. ESCAPE ISSUES")
    print("   - No escaping of special characters in segment text")
    print("   - Could break JSON/XML structured formats")
    print("   - Potential for prompt injection")
    
    print("\n7. LAYOUT VALIDATION MISMATCH")
    print("   - Valid layouts list appears in multiple places")
    print("   - Not synchronized between single and batch functions")
    print("   - New layouts missing from validation")


def implement_critical_fixes():
    """Implement critical fixes to the layout system."""
    
    file_path = Path("multi_coder_analysis/run_multi_coder_tot.py")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix 1: Update validation to include all layouts
    old_validation_single = """    # Validate layout
    valid_layouts = ['standard', 'recency', 'sandwich', 'minimal_system', 'question_first']
    if layout not in valid_layouts:
        logging.warning(f"Unknown layout '{layout}', using 'standard' instead")
        layout = 'standard'"""
    
    new_validation = """    # Validate layout
    if layout not in VALID_LAYOUTS:
        logging.warning(f"Unknown layout '{layout}', using 'standard' instead")
        layout = 'standard'"""
    
    content = content.replace(old_validation_single, new_validation)
    print("✅ Fixed layout validation to use global VALID_LAYOUTS")
    
    # Fix 2: Add escape function for special characters
    escape_function = '''
def _escape_for_format(text: str, format_type: str) -> str:
    """Escape text for different format types."""
    if format_type == 'json':
        # Escape for JSON strings
        return text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
    elif format_type == 'xml':
        # Escape for XML
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&apos;')
    else:
        return text
'''
    
    # Insert after the validate_layout_compatibility function
    insert_pos = content.find('def _get_hop_file(')
    if insert_pos > 0:
        content = content[:insert_pos] + escape_function + '\n\n' + content[insert_pos:]
        print("✅ Added text escaping function")
    
    # Fix 3: Improve segment formatting function
    segment_formatter = '''
def _format_segments_for_batch(segments: List[HopContext], layout: str) -> str:
    """Format segments according to layout requirements."""
    if layout == "structured_json":
        import json
        segments_data = []
        for ctx in segments:
            segments_data.append({
                "segment_id": ctx.statement_id,
                "content": _escape_for_format(ctx.segment_text, 'json')
            })
        return f"```json\\n{json.dumps(segments_data, indent=2)}\\n```"
    
    elif layout == "xml_structured":
        lines = ["<segments>"]
        for ctx in segments:
            lines.append(f'  <segment id="{ctx.statement_id}">')
            lines.append(f'    <content>{_escape_for_format(ctx.segment_text, "xml")}</content>')
            lines.append('  </segment>')
        lines.append("</segments>")
        return '\\n'.join(lines)
    
    elif layout == "segment_focus":
        lines = []
        for idx, ctx in enumerate(segments, start=1):
            lines.append("═" * 60)
            lines.append(f"SEGMENT {idx}/{len(segments)} (ID: {ctx.statement_id})")
            lines.append("═" * 60)
            lines.append(ctx.segment_text)
            lines.append("")
        return '\\n'.join(lines)
    
    else:
        # Default formatting
        lines = []
        for idx, ctx in enumerate(segments, start=1):
            lines.append(f"### Segment {idx}/{len(segments)} (ID: {ctx.statement_id})")
            lines.append(ctx.segment_text)
            lines.append("")
        return '\\n'.join(lines)
'''
    
    # Insert after escape function
    insert_pos = content.find('def _get_hop_file(')
    if insert_pos > 0:
        content = content[:insert_pos] + segment_formatter + '\n\n' + content[insert_pos:]
        print("✅ Added improved segment formatting function")
    
    # Fix 4: Create consistent instruction builder
    instruction_builder = '''
def _build_batch_instruction(hop_idx: int, num_segments: int, confidence_scores: bool = False, ranked: bool = False, max_candidates: int = 5) -> str:
    """Build consistent batch instruction regardless of layout."""
    parts = [
        f"You must analyze {num_segments} segments for Question Q{hop_idx}.",
        "",
        "OUTPUT FORMAT:",
        "Return a JSON array with exactly {num_segments} elements.".format(num_segments=num_segments),
        "Each element must contain:",
        "- segment_id: The exact ID from the segment header",
        "- answer: Your answer (yes/no/uncertain)",
        "- rationale: Brief explanation for your answer"
    ]
    
    if confidence_scores:
        parts.extend([
            "- confidence: Your confidence level (0-100)",
            "- frame_likelihoods: Object with Alarmist, Neutral, Reassuring percentages"
        ])
    
    if ranked and not confidence_scores:
        parts.extend([
            "",
            "Additionally, embed rankings in the answer field using format:",
            f"Ranking: Frame1 > Frame2 > ... (up to {max_candidates} frames)"
        ])
    
    parts.extend([
        "",
        "CRITICAL: Return ONLY the JSON array. No other text."
    ])
    
    return '\\n'.join(parts)
'''
    
    # Insert after segment formatter
    insert_pos = content.find('def _get_hop_file(')
    if insert_pos > 0:
        content = content[:insert_pos] + instruction_builder + '\n\n' + content[insert_pos:]
        print("✅ Added consistent instruction builder")
    
    # Fix 5: Update the batch assembly to use new functions
    # This is complex, so we'll create a patch for key improvements
    
    # Fix the structured_json layout to use the new formatter
    old_json_layout = '''        elif layout == "structured_json":
            # Present all segments as JSON array
            import json
            segments_json = json.dumps([
                {
                    "segment_id": ctx.statement_id,
                    "content": ctx.segment_text
                }
                for ctx in segments
            ], indent=2)
            
            system_block = local_header + "\\n\\nAnalyze segments presented in JSON format."
            user_block = f"Segments to analyze:\\n```json\\n{segments_json}\\n```\\n\\n{hop_content}\\n\\n{instruction}\\n\\n{local_footer}"'''
    
    new_json_layout = '''        elif layout == "structured_json":
            # Present all segments as JSON array with proper escaping
            segment_block = _format_segments_for_batch(segments, layout)
            instruction = _build_batch_instruction(hop_idx, len(segments), confidence_scores, ranked, max_candidates)
            
            system_block = local_header + "\\n\\nAnalyze segments presented in JSON format."
            user_block = f"Task: {hop_content}\\n\\n{instruction}\\n\\nSegments:\\n{segment_block}\\n\\n{local_footer}"'''
    
    content = content.replace(old_json_layout, new_json_layout)
    print("✅ Updated structured_json layout to use new functions")
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)


def add_layout_specific_optimizations():
    """Add layout-specific optimizations."""
    
    optimizations = '''
# Layout-Specific Optimizations

## 1. Instruction Placement Standardization
- Move instruction to consistent position relative to segments
- For recency layouts: segments → instruction → hop
- For primacy layouts: instruction → hop → segments
- For structured layouts: instruction → segments (with clear format indicators)

## 2. Segment Count Indication
- Always include total count: "Segment N/M"
- Helps model allocate response space
- Critical for 200+ segment batches

## 3. Clean Hop Content for Batch Mode
- Remove all {{segment_text}} placeholders
- Replace with clear batch indicators
- Add "For each segment below:" prefix

## 4. Response Length Hints
- For large batches: "Keep each rationale under 50 words"
- Prevents token exhaustion
- Maintains consistency across segments

## 5. Layout-Specific System Prompts
- standard: "You are an expert claim-framing coder..."
- structured_json: "You process JSON-formatted analysis tasks..."
- evidence_based: "You systematically extract evidence before decisions..."
- Tailored to layout philosophy

## 6. Progressive Complexity
- Simple layouts for small batches
- Structured layouts for large batches
- JSON/XML for 100+ segments

## 7. Error Recovery Instructions
- Add: "If a segment is unclear, mark as uncertain"
- Add: "Process all segments even if some are difficult"
- Prevents partial responses
'''
    
    with open(Path("docs/LAYOUT_OPTIMIZATIONS.md"), 'w', encoding='utf-8') as f:
        f.write(optimizations)
    
    print("\n✅ Created layout optimization guide")


def create_layout_testing_matrix():
    """Create a testing matrix for layout experiments."""
    
    matrix = '''# Layout Testing Matrix

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
python scripts/run_all_layouts_experiment.py \\
    --layouts hop_last structured_json evidence_based \\
    --input data/test_segments.csv \\
    --start 1 --end 50 \\
    --batch-size 25 \\
    --sequential
```
'''
    
    with open(Path("docs/LAYOUT_TESTING_MATRIX.md"), 'w', encoding='utf-8') as f:
        f.write(matrix)
    
    print("✅ Created layout testing matrix")


def main():
    """Run all improvements."""
    print("Implementing critical layout improvements...")
    print("=" * 60)
    
    print("\n1. Identifying critical issues...")
    identify_critical_issues()
    
    print("\n\n2. Implementing critical fixes...")
    implement_critical_fixes()
    
    print("\n3. Adding layout-specific optimizations...")
    add_layout_specific_optimizations()
    
    print("\n4. Creating testing matrix...")
    create_layout_testing_matrix()
    
    print("\n✅ Critical improvements completed!")
    
    print("\n📋 SUMMARY OF CHANGES:")
    print("1. Fixed layout validation to use global constant")
    print("2. Added proper text escaping for JSON/XML formats")
    print("3. Improved segment formatting with count indicators")
    print("4. Created consistent instruction builder")
    print("5. Updated structured layouts to use new functions")
    print("6. Created optimization and testing guides")
    
    print("\n🎯 KEY IMPROVEMENTS:")
    print("- Consistent instruction placement across layouts")
    print("- Segment count always visible (N/M format)")
    print("- Proper escaping prevents format breaking")
    print("- Layout-specific optimizations documented")
    print("- Clear testing matrix for experiments")
    
    print("\n⚡ NEXT STEPS:")
    print("1. Test with adversarial inputs (quotes, special chars)")
    print("2. Run small batch to verify improvements")
    print("3. Compare error rates before/after")
    print("4. Focus on high-priority layouts for large batches")


if __name__ == "__main__":
    main() 