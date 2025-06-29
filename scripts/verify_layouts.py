#!/usr/bin/env python3
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
    print("\nTesting batch layouts...")
    
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
    
    print("\nVerification complete!")
