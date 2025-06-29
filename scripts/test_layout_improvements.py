#!/usr/bin/env python3
"""
Test script to verify that prompt layout improvements are working correctly.
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from multi_coder_analysis.run_multi_coder_tot import _assemble_prompt, _assemble_prompt_batch
from multi_coder_analysis.models import HopContext


def test_single_segment_layouts():
    """Test that different layouts produce different prompt structures."""
    
    # Create a test context
    ctx = HopContext(
        statement_id="TEST001",
        segment_text="This is a test segment about climate change causing severe weather.",
        article_id="ARTICLE001"
    )
    ctx.q_idx = 1
    
    layouts = ["standard", "recency", "sandwich", "minimal_system", "question_first"]
    
    print("Testing single-segment prompt layouts:\n")
    
    for layout in layouts:
        try:
            sys_prompt, user_prompt = _assemble_prompt(ctx, layout=layout)
            
            print(f"Layout: {layout}")
            print(f"System prompt length: {len(sys_prompt)} chars")
            print(f"User prompt length: {len(user_prompt)} chars")
            
            # Check for specific characteristics
            if layout == "minimal_system":
                assert len(sys_prompt) < 100, f"Minimal system prompt too long: {len(sys_prompt)}"
                print("✓ Minimal system prompt is short")
            
            if layout == "recency":
                segment_pos = user_prompt.find(ctx.segment_text)
                assert segment_pos >= 0, "Segment not found in user prompt"
                assert segment_pos < len(user_prompt) / 2, "Segment should be early in recency layout"
                print("✓ Segment appears early in prompt")
            
            print()
            
        except Exception as e:
            print(f"❌ Error with layout {layout}: {e}\n")


def test_batch_layouts():
    """Test that batch processing supports layouts."""
    
    # Create test contexts
    contexts = [
        HopContext(
            statement_id=f"TEST{i:03d}",
            segment_text=f"Test segment {i} about topic.",
            article_id="ARTICLE001"
        )
        for i in range(1, 4)
    ]
    
    hop_idx = 1
    layouts = ["standard", "recency", "minimal_system"]
    
    print("\nTesting batch prompt layouts:\n")
    
    for layout in layouts:
        try:
            sys_prompt, user_prompt = _assemble_prompt_batch(
                contexts, 
                hop_idx, 
                layout=layout
            )
            
            print(f"Layout: {layout}")
            print(f"System prompt length: {len(sys_prompt)} chars")
            print(f"User prompt length: {len(user_prompt)} chars")
            
            # Verify all segments are included
            for ctx in contexts:
                assert ctx.statement_id in user_prompt, f"Missing {ctx.statement_id}"
            
            print("✓ All segments included in batch prompt")
            print()
            
        except Exception as e:
            print(f"❌ Error with batch layout {layout}: {e}\n")


def test_layout_validation():
    """Test prompt structure validation."""
    from scripts.experiment_prompt_layouts_improved import validate_prompt_structure
    
    print("\nTesting layout validation:\n")
    
    # Test prompt with sandwich layout markers
    sandwich_prompt = """
    ### ⚡ QUICK DECISION CHECK
    Some quick check content
    
    ### Detailed Analysis
    More content here
    """
    
    assert validate_prompt_structure(sandwich_prompt, "sandwich"), "Sandwich validation failed"
    print("✓ Sandwich layout validation works")
    
    # Test prompt with question marker
    question_prompt = """
    ### Question Q01: Is this about climate?
    
    Some analysis content
    """
    
    assert validate_prompt_structure(question_prompt, "question_first"), "Question layout validation failed"
    print("✓ Question-first layout validation works")
    
    # Test prompt with segment placeholder
    recency_prompt = """
    Some intro text
    {{segment_text}}
    More content
    """
    
    assert validate_prompt_structure(recency_prompt, "recency"), "Recency layout validation failed"
    print("✓ Recency layout validation works")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Prompt Layout Improvements")
    print("=" * 60)
    
    test_single_segment_layouts()
    test_batch_layouts()
    test_layout_validation()
    
    print("\n✅ All tests completed!")


if __name__ == "__main__":
    main() 