#!/usr/bin/env python3
"""
Fix the syntax error in the progress tracker initialization.
"""

from pathlib import Path
import re


def fix_progress_tracker_syntax():
    """Fix the syntax error caused by incorrect placement of progress tracker initialization."""
    
    file_path = Path("multi_coder_analysis/run_multi_coder_tot.py")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find and fix the problematic section
    # The issue is that the progress tracker initialization is placed in the wrong position
    problematic_pattern = r'''contexts: List\[HopContext\] = \[
        HopContext\(
            statement_id=row\["StatementID"\]
    
    # Initialize progress tracker
    progress_tracker = ProgressTracker\(len\(contexts\), len\(hop_range\) if hop_range else 12\)
,'''
    
    # Fix by moving the progress tracker initialization after the list comprehension
    fixed_pattern = '''contexts: List[HopContext] = [
        HopContext(
            statement_id=row["StatementID"],'''
    
    content = re.sub(problematic_pattern, fixed_pattern, content, flags=re.DOTALL)
    
    # Now add the progress tracker initialization in the correct place
    # Find where contexts list is completed
    contexts_end_pattern = r'(for _, row in df\.iterrows\(\)\s*\])'
    match = re.search(contexts_end_pattern, content)
    
    if match:
        insert_pos = match.end()
        # Add progress tracker initialization after contexts list
        progress_init = '''
    
    # Initialize progress tracker
    progress_tracker = ProgressTracker(len(contexts), len(hop_range) if hop_range else 12)
'''
        content = content[:insert_pos] + progress_init + content[insert_pos:]
        print("✅ Fixed progress tracker initialization placement")
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)


def verify_syntax():
    """Verify the file has valid Python syntax."""
    
    file_path = Path("multi_coder_analysis/run_multi_coder_tot.py")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try to compile the code
        compile(content, str(file_path), 'exec')
        print("✅ Syntax verification passed!")
        return True
    except SyntaxError as e:
        print(f"❌ Syntax error still present: {e}")
        print(f"   Line {e.lineno}: {e.text}")
        return False


def main():
    """Run the fix."""
    print("Fixing progress tracker syntax error...")
    print("=" * 60)
    
    fix_progress_tracker_syntax()
    
    print("\nVerifying syntax...")
    if verify_syntax():
        print("\n✅ Syntax error fixed successfully!")
    else:
        print("\n⚠️  There may still be syntax errors. Please check manually.")


if __name__ == "__main__":
    main() 