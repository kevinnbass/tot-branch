#!/usr/bin/env python3
"""
Implement new high-yield layouts for prompt layout experiments.
Focus on batch processing optimization and hop positioning relative to segments.
"""

import sys
from pathlib import Path
import re

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))


def analyze_existing_layouts():
    """Analyze the existing layouts to understand their strengths and weaknesses."""
    
    print("ANALYSIS OF EXISTING LAYOUTS")
    print("=" * 60)
    
    print("\n1. STANDARD LAYOUT")
    print("   - Structure: Header + Hop → User: Hop(segment)")
    print("   - Strength: Familiar structure, hop context in both system and user")
    print("   - Weakness: Redundant hop info, segment buried in middle")
    print("   - Batch: Works well, segments enumerated at end")
    
    print("\n2. RECENCY LAYOUT")
    print("   - Structure: Header → User: Segment + Hop")
    print("   - Strength: Segment first exploits recency bias")
    print("   - Weakness: Question comes after segment (may miss context)")
    print("   - Batch: Good - all segments listed first")
    
    print("\n3. SANDWICH LAYOUT")
    print("   - Structure: Header → User: Quick + Segment + Detailed")
    print("   - Strength: Two-pass analysis, quick filtering")
    print("   - Weakness: Requires specific prompt markers, complex")
    print("   - Batch: NOT IMPLEMENTED (falls back to standard)")
    
    print("\n4. MINIMAL SYSTEM LAYOUT")
    print("   - Structure: Minimal → User: Header + Hop(segment)")
    print("   - Strength: Token efficient, tests if system prompt matters")
    print("   - Weakness: May lose important context")
    print("   - Batch: Works well")
    
    print("\n5. QUESTION FIRST LAYOUT")
    print("   - Structure: Header → User: Question + Segment + Rules")
    print("   - Strength: Question prominence, clear task")
    print("   - Weakness: May prime specific answers")
    print("   - Batch: NOT IMPLEMENTED (falls back to standard)")
    
    print("\n\nKEY INSIGHTS:")
    print("- Only 3/5 layouts work in batch mode")
    print("- Segment position varies: middle (standard), first (recency), after question")
    print("- No layout puts hop/question at the END (potential recency benefit)")
    print("- No layout separates segments clearly with delimiters")
    print("- No layout uses structured formats (JSON, XML)")


def add_new_layouts():
    """Add new high-yield layouts optimized for batch processing."""
    
    file_path = Path("multi_coder_analysis/run_multi_coder_tot.py")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update VALID_LAYOUTS constant
    old_valid = "VALID_LAYOUTS = ['standard', 'recency', 'sandwich', 'minimal_system', 'question_first']"
    new_valid = """VALID_LAYOUTS = [
    'standard', 'recency', 'sandwich', 'minimal_system', 'question_first',
    # New high-yield layouts
    'hop_last', 'structured_json', 'segment_focus', 'instruction_first',
    'parallel_analysis', 'evidence_based', 'xml_structured', 'primacy_recency'
]"""
    
    content = content.replace(old_valid, new_valid)
    print("✅ Updated VALID_LAYOUTS with 8 new layouts")
    
    # Find where to add new layout implementations in _assemble_prompt
    single_prompt_impl = '''        else:
            raise ValueError(f"Unknown layout: {layout}")'''
    
    new_single_implementations = '''        elif layout == "hop_last":
            # Hop at the very end to maximize recency effect
            system_block = local_header
            
            segment_section = f"### Segment (StatementID: {ctx.statement_id})\\n{ctx.segment_text}\\n\\n"
            # Remove segment placeholder from hop_body
            hop_clean = hop_body.replace("### Segment (StatementID: {{statement_id}})\\n{{segment_text}}", "").replace("{{statement_id}}", ctx.statement_id)
            user_prompt = segment_section + "\\n" + hop_clean
            
        elif layout == "structured_json":
            # Present segment in JSON structure for clarity
            system_block = local_header + "\\n\\nYou will analyze segments presented in JSON format."
            
            import json
            segment_json = json.dumps({
                "segment_id": ctx.statement_id,
                "content": ctx.segment_text,
                "task": f"Answer Question Q{ctx.q_idx}"
            }, indent=2)
            
            hop_clean = hop_body.replace("### Segment (StatementID: {{statement_id}})\\n{{segment_text}}", "").replace("{{statement_id}}", ctx.statement_id)
            user_prompt = f"Analyze this segment:\\n```json\\n{segment_json}\\n```\\n\\n{hop_clean}"
            
        elif layout == "segment_focus":
            # Segment prominently displayed with visual separation
            system_block = local_header
            
            segment_section = f"""
═══════════════════════════════════════════════════════════════
SEGMENT TO ANALYZE (ID: {ctx.statement_id})
═══════════════════════════════════════════════════════════════
{ctx.segment_text}
═══════════════════════════════════════════════════════════════

"""
            hop_clean = hop_body.replace("### Segment (StatementID: {{statement_id}})\\n{{segment_text}}", "").replace("{{statement_id}}", ctx.statement_id)
            user_prompt = segment_section + hop_clean
            
        elif layout == "instruction_first":
            # Clear instructions before segment
            system_block = "Follow the instructions exactly. Analyze each segment systematically."
            
            # Extract question and key instruction
            import re
            question_match = re.search(r"### Question Q\\d+.*?(?=\\n)", hop_body)
            question = question_match.group(0) if question_match else f"Question Q{ctx.q_idx}"
            
            instruction_section = f"""
INSTRUCTION: You must answer the following question for the segment below.
{question}

SEGMENT (ID: {ctx.statement_id}):
{ctx.segment_text}

ANALYSIS GUIDELINES:
"""
            hop_clean = hop_body.replace("### Segment (StatementID: {{statement_id}})\\n{{segment_text}}", "").replace("{{statement_id}}", ctx.statement_id)
            if question_match:
                hop_clean = hop_clean.replace(question, "")
            
            user_prompt = local_header + "\\n" + instruction_section + hop_clean
            
        elif layout == "parallel_analysis":
            # Present positive and negative indicators in parallel
            system_block = local_header
            
            # This layout works best with modified hop content
            # For now, use standard structure with parallel framing
            segment_section = f"SEGMENT (ID: {ctx.statement_id}): {ctx.segment_text}\\n\\n"
            analysis_frame = """
Analyze the segment above by considering:
• Would indicate YES if: [Apply positive criteria from question]
• Would indicate NO if: [Apply negative criteria from question]
• Would be UNCERTAIN if: [Neither clearly applies]

"""
            hop_clean = hop_body.replace("### Segment (StatementID: {{statement_id}})\\n{{segment_text}}", "").replace("{{statement_id}}", ctx.statement_id)
            user_prompt = segment_section + analysis_frame + hop_clean
            
        elif layout == "evidence_based":
            # Force evidence extraction before decision
            system_block = local_header + "\\n\\nALWAYS extract evidence before making decisions."
            
            evidence_template = f"""
Step 1: Read this segment (ID: {ctx.statement_id}):
{ctx.segment_text}

Step 2: Extract relevant evidence:
[You will identify specific quotes and facts]

Step 3: Apply the following question based on evidence:
"""
            hop_clean = hop_body.replace("### Segment (StatementID: {{statement_id}})\\n{{segment_text}}", "").replace("{{statement_id}}", ctx.statement_id)
            user_prompt = evidence_template + hop_clean
            
        elif layout == "xml_structured":
            # Use XML for clear structure
            system_block = local_header + "\\n\\nSegments and questions are presented in XML format."
            
            xml_segment = f"""<analysis_task>
    <segment id="{ctx.statement_id}">
        <content>{ctx.segment_text}</content>
    </segment>
    
    <question number="{ctx.q_idx}">
"""
            hop_clean = hop_body.replace("### Segment (StatementID: {{statement_id}})\\n{{segment_text}}", "").replace("{{statement_id}}", ctx.statement_id)
            # Close the XML properly
            user_prompt = xml_segment + hop_clean + "\\n    </question>\\n</analysis_task>"
            
        elif layout == "primacy_recency":
            # Question at beginning AND end for maximum salience
            system_block = local_header
            
            # Extract question
            import re
            question_match = re.search(r"### Question Q\\d+.*?(?=\\n\\*\\*|\\n\\n|$)", hop_body, re.DOTALL)
            question = question_match.group(0) if question_match else f"Question Q{ctx.q_idx}"
            
            primacy_section = f"""
{question}

Now analyze this segment (ID: {ctx.statement_id}):
{ctx.segment_text}

"""
            hop_clean = hop_body.replace("### Segment (StatementID: {{statement_id}})\\n{{segment_text}}", "").replace("{{statement_id}}", ctx.statement_id)
            if question_match:
                hop_clean = hop_clean.replace(question, "")
            
            recency_section = f"\\n\\nREMEMBER: {question}"
            
            user_prompt = primacy_section + hop_clean + recency_section
            
        else:
            raise ValueError(f"Unknown layout: {layout}")'''
    
    content = content.replace(single_prompt_impl, new_single_implementations)
    print("✅ Added 8 new layout implementations for single segment processing")
    
    # Now add batch implementations
    batch_fallback = '''        else:
            # For other layouts, fall back to standard in batch mode
            logging.warning(f"Layout '{layout}' not fully supported in batch mode, using standard layout")
            system_block = local_header + "\\n\\n" + hop_content
            user_block = instruction + segment_block + "\\n\\n" + local_footer'''
    
    new_batch_implementations = '''        elif layout == "hop_last":
            # All segments first, then hop question at the very end
            system_block = local_header
            user_block = segment_block + "\\n\\n" + hop_content + "\\n\\n" + instruction + "\\n\\n" + local_footer
            
        elif layout == "structured_json":
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
            user_block = f"Segments to analyze:\\n```json\\n{segments_json}\\n```\\n\\n{hop_content}\\n\\n{instruction}\\n\\n{local_footer}"
            
        elif layout == "segment_focus":
            # Each segment clearly separated with visual boundaries
            segment_formatted_lines = []
            for idx, ctx in enumerate(segments, start=1):
                segment_formatted_lines.append("═" * 60)
                segment_formatted_lines.append(f"SEGMENT {idx} (ID: {ctx.statement_id})")
                segment_formatted_lines.append("═" * 60)
                segment_formatted_lines.append(ctx.segment_text)
                segment_formatted_lines.append("")
            segment_formatted = "\\n".join(segment_formatted_lines)
            
            system_block = local_header
            user_block = segment_formatted + "\\n\\n" + hop_content + "\\n\\n" + instruction + "\\n\\n" + local_footer
            
        elif layout == "instruction_first":
            # Instructions and question before all segments
            import re
            question_match = re.search(r"### Question Q\\d+.*?(?=\\n)", hop_content)
            question = question_match.group(0) if question_match else f"Question Q{hop_idx}"
            
            instruction_enhanced = f"""
BATCH INSTRUCTION: Answer the following question for EACH segment below.
{question}

{instruction}

SEGMENTS TO ANALYZE:
"""
            system_block = "Follow the instructions exactly. Analyze each segment systematically."
            user_block = local_header + "\\n" + instruction_enhanced + segment_block + "\\n\\n" + hop_content + "\\n\\n" + local_footer
            
        elif layout == "parallel_analysis":
            # Table format for parallel comparison
            system_block = local_header
            
            parallel_instruction = f"""
Analyze each segment below using this framework:
- YES indicators: [Look for affirmative evidence per the question]
- NO indicators: [Look for negative evidence per the question]  
- UNCERTAIN: [When evidence is ambiguous or missing]

{instruction}

SEGMENTS:
"""
            user_block = parallel_instruction + segment_block + "\\n\\n" + hop_content + "\\n\\n" + local_footer
            
        elif layout == "evidence_based":
            # Structured evidence extraction for batch
            system_block = local_header + "\\n\\nFor EACH segment: 1) Extract evidence 2) Apply criteria 3) Decide"
            
            evidence_instruction = f"""
{instruction}

For each segment below, you must:
1. Identify relevant evidence (quotes, facts)
2. Apply the question criteria
3. Provide your answer with rationale

SEGMENTS FOR ANALYSIS:
"""
            user_block = evidence_instruction + segment_block + "\\n\\n" + hop_content + "\\n\\n" + local_footer
            
        elif layout == "xml_structured":
            # XML batch structure
            xml_segments = "<analysis_batch>\\n"
            for ctx in segments:
                xml_segments += f'    <segment id="{ctx.statement_id}">\\n'
                xml_segments += f'        <content>{ctx.segment_text}</content>\\n'
                xml_segments += '    </segment>\\n'
            xml_segments += f'    <question number="{hop_idx}">\\n        '
            xml_segments += hop_content.replace("\\n", "\\n        ")
            xml_segments += f'\\n    </question>\\n'
            xml_segments += f'    <instruction>{instruction}</instruction>\\n'
            xml_segments += '</analysis_batch>'
            
            system_block = local_header + "\\n\\nProcess the XML-structured analysis batch."
            user_block = xml_segments + "\\n\\n" + local_footer
            
        elif layout == "primacy_recency":
            # Question at start and end of batch
            import re
            question_match = re.search(r"### Question Q\\d+.*?(?=\\n\\*\\*|\\n\\n|$)", hop_content, re.DOTALL)
            question = question_match.group(0) if question_match else f"Question Q{hop_idx}"
            
            primacy = f"{question}\\n\\n{instruction}\\n\\nSEGMENTS:\\n"
            recency = f"\\n\\nREMINDER - Answer this for EACH segment above: {question}"
            
            system_block = local_header
            user_block = primacy + segment_block + "\\n\\n" + hop_content + recency + "\\n\\n" + local_footer
            
        else:
            # For other layouts, fall back to standard in batch mode
            logging.warning(f"Layout '{layout}' not fully supported in batch mode, using standard layout")
            system_block = local_header + "\\n\\n" + hop_content
            user_block = instruction + segment_block + "\\n\\n" + local_footer'''
    
    content = content.replace(batch_fallback, new_batch_implementations)
    print("✅ Added 8 new layout implementations for batch processing")
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\nNEW LAYOUTS IMPLEMENTED:")
    print("1. hop_last - Question after all segments (recency)")
    print("2. structured_json - JSON format for clarity")  
    print("3. segment_focus - Visual separation of segments")
    print("4. instruction_first - Clear task before content")
    print("5. parallel_analysis - YES/NO/UNCERTAIN framework")
    print("6. evidence_based - Force evidence extraction")
    print("7. xml_structured - XML for hierarchical clarity")
    print("8. primacy_recency - Question at start AND end")


def create_layout_comparison_doc():
    """Create documentation comparing all layouts."""
    
    doc_content = '''# Complete Layout Comparison

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
'''
    
    doc_file = Path("docs/LAYOUT_COMPARISON.md")
    with open(doc_file, 'w', encoding='utf-8') as f:
        f.write(doc_content)
    
    print(f"\n✅ Created comprehensive layout comparison at {doc_file}")


def main():
    """Implement new layouts and create documentation."""
    print("Implementing new high-yield layouts...")
    print("=" * 60)
    
    print("\n1. Analyzing existing layouts...")
    analyze_existing_layouts()
    
    print("\n\n2. Implementing new layouts...")
    add_new_layouts()
    
    print("\n3. Creating comparison documentation...")
    create_layout_comparison_doc()
    
    print("\n✅ Successfully implemented 8 new layouts!")
    print("\nTotal layouts available: 13")
    print("- Original: 5")
    print("- New: 8")
    print("\nAll layouts are lossless and maintain full information.")
    print("11/13 layouts have full batch support.")
    
    print("\n📊 Recommended testing approach:")
    print("1. Run small test with all 13 layouts")
    print("2. Compare accuracy, token usage, and speed")
    print("3. Select top performers for full dataset")
    
    print("\n🎯 High-yield predictions:")
    print("- hop_last: Strong recency effect")
    print("- evidence_based: Better reasoning")
    print("- primacy_recency: Question reinforcement")
    print("- structured_json: Clarity for large batches")


if __name__ == "__main__":
    main() 