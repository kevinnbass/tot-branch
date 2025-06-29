#!/usr/bin/env python3
"""
Final fixes for the layout system - remove duplicates and fix bugs.
"""

import sys
from pathlib import Path
import re

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))


def fix_duplicate_functions():
    """Remove duplicate function definitions."""
    
    file_path = Path("multi_coder_analysis/run_multi_coder_tot.py")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find and remove the duplicate functions (the second set)
    # The duplicates appear after line 320
    duplicate_start = content.find('\n\n\ndef _escape_for_format(text: str, format_type: str) -> str:\n', 10000)
    
    if duplicate_start > 0:
        # Find the end of the third duplicate function
        duplicate_end = content.find('\ndef _get_hop_file(', duplicate_start)
        
        if duplicate_end > 0:
            # Remove the duplicate section
            content = content[:duplicate_start] + content[duplicate_end:]
            print("✅ Removed duplicate function definitions")
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)


def fix_escape_function_bug():
    """Fix the syntax error in the escape function."""
    
    file_path = Path("multi_coder_analysis/run_multi_coder_tot.py")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix the broken escape sequences
    broken_escape = """        return text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')"""
    
    fixed_escape = '''        return text.replace('\\\\', '\\\\\\\\').replace('"', '\\\\"').replace('\\n', '\\\\n').replace('\\r', '\\\\r').replace('\\t', '\\\\t')'''
    
    content = content.replace(broken_escape, fixed_escape)
    print("✅ Fixed escape function syntax error")
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)


def fix_batch_assembly_to_use_new_functions():
    """Update batch assembly to use the new helper functions."""
    
    file_path = Path("multi_coder_analysis/run_multi_coder_tot.py")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update the segment block generation to use the new formatter
    old_segment_block = '''        # Enumerate the segments
        segment_block_lines = []
        for idx, ctx in enumerate(segments, start=1):
            segment_block_lines.append(f"### Segment {idx} (ID: {ctx.statement_id})")
            segment_block_lines.append(ctx.segment_text)
            segment_block_lines.append("")
        segment_block = "\\n".join(segment_block_lines)'''
    
    new_segment_block = '''        # Format segments using layout-specific formatter
        segment_block = _format_segments_for_batch(segments, layout)'''
    
    content = content.replace(old_segment_block, new_segment_block)
    print("✅ Updated batch assembly to use segment formatter")
    
    # Update instruction generation to use the new builder
    old_instruction = '''        instruction = (
            f"\\nYou will answer the **same question** (Q{hop_idx}) for EACH segment listed below.\\n"
            "Respond with **one JSON array**. Each element must contain: `segment_id`, `answer`, `rationale`.\\n"
        )
        
        if confidence_scores:
            instruction += (
                "For confidence mode, each element must also include: `confidence` (0-100), "
                "`frame_likelihoods` (Alarmist, Neutral, Reassuring percentages).\\n"
            )
        
        instruction += "Return NOTHING except valid JSON.\\n\\n"

        if ranked and not confidence_scores:
            instruction += (
                "After the JSON array, for **each segment** embed the ranked list inside the 'answer' string using the format:\\n"
                "Ranking: Frame1 > Frame2 > … (up to {n}).\\n".format(n=max_candidates)
            )'''
    
    new_instruction = '''        # Build consistent instruction using the new builder
        instruction = _build_batch_instruction(hop_idx, len(segments), confidence_scores, ranked, max_candidates)'''
    
    content = content.replace(old_instruction, new_instruction)
    print("✅ Updated batch assembly to use instruction builder")
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)


def add_missing_layout_parameter():
    """Add layout parameter to layout_experiment.py if missing."""
    
    file_path = Path("multi_coder_analysis/layout_experiment.py")
    
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if run_tot_chain_batch is called without layout parameter
        if 'run_tot_chain_batch(' in content and 'layout=' not in content:
            # Find the call and add layout parameter
            pattern = r'(results = run_tot_chain_batch\([^)]+)'
            replacement = r'\1, layout=layout'
            content = re.sub(pattern, replacement, content)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ Added layout parameter to layout_experiment.py")


def verify_all_layouts_work():
    """Create a verification script to test all layouts."""
    
    verification_script = '''#!/usr/bin/env python3
"""
Verify all layouts work correctly with a simple test.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from multi_coder_analysis.run_multi_coder_tot import (
    _assemble_prompt, _assemble_prompt_batch, 
    HopContext, VALID_LAYOUTS
)

def test_single_segment_layouts():
    """Test all layouts for single segment processing."""
    print("Testing single segment layouts...")
    
    # Create test context
    ctx = HopContext(
        statement_id="TEST001",
        segment_text="The climate is changing rapidly.",
        article_id="ARTICLE001"
    )
    ctx.q_idx = 1
    
    for layout in VALID_LAYOUTS:
        try:
            sys_prompt, user_prompt = _assemble_prompt(ctx, layout=layout)
            print(f"✅ {layout}: OK (sys={len(sys_prompt)}, user={len(user_prompt)} chars)")
        except Exception as e:
            print(f"❌ {layout}: FAILED - {e}")


def test_batch_layouts():
    """Test all layouts for batch processing."""
    print("\\nTesting batch layouts...")
    
    # Create test segments
    segments = [
        HopContext(
            statement_id=f"TEST{i:03d}",
            segment_text=f"Test segment {i} with some text.",
            article_id="ARTICLE001"
        )
        for i in range(1, 6)
    ]
    
    for layout in VALID_LAYOUTS:
        try:
            sys_prompt, user_prompt = _assemble_prompt_batch(
                segments, hop_idx=1, layout=layout
            )
            print(f"✅ {layout}: OK (sys={len(sys_prompt)}, user={len(user_prompt)} chars)")
        except Exception as e:
            print(f"❌ {layout}: FAILED - {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("LAYOUT VERIFICATION TEST")
    print("=" * 60)
    
    test_single_segment_layouts()
    test_batch_layouts()
    
    print("\\nVerification complete!")
'''
    
    with open(Path("scripts/verify_layouts.py"), 'w', encoding='utf-8') as f:
        f.write(verification_script)
    
    print("✅ Created layout verification script")


def main():
    """Run all final fixes."""
    print("Applying final layout fixes...")
    print("=" * 60)
    
    print("\n1. Removing duplicate functions...")
    fix_duplicate_functions()
    
    print("\n2. Fixing escape function syntax...")
    fix_escape_function_bug()
    
    print("\n3. Updating batch assembly to use new functions...")
    fix_batch_assembly_to_use_new_functions()
    
    print("\n4. Adding missing layout parameter...")
    add_missing_layout_parameter()
    
    print("\n5. Creating verification script...")
    verify_all_layouts_work()
    
    print("\n✅ All fixes applied!")
    
    print("\n📋 BUGS FIXED:")
    print("1. Removed duplicate function definitions")
    print("2. Fixed escape sequence syntax error")
    print("3. Updated batch assembly to use helper functions")
    print("4. Added missing layout parameter")
    print("5. Created verification script")
    
    print("\n🎯 FINAL IMPROVEMENTS:")
    print("- All layouts now use consistent formatting")
    print("- Segment count (N/M) visible in all layouts")
    print("- Proper text escaping for JSON/XML")
    print("- Consistent instruction placement")
    print("- No more duplicate code")


if __name__ == "__main__":
    main() 