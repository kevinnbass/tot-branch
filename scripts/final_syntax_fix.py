#!/usr/bin/env python3
"""
Final fix for the syntax error - remove duplicate line.
"""

from pathlib import Path


def fix_duplicate_line():
    """Remove the duplicate 'this batch for consistency' line."""
    
    file_path = Path("multi_coder_analysis/run_multi_coder_tot.py")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find and remove the duplicate line
    fixed_lines = []
    for i, line in enumerate(lines):
        # Skip the standalone duplicate line
        if line.strip() == "this batch for consistency" and i > 0:
            # Check if this is the duplicate (not part of a comment)
            prev_line = lines[i-1].strip()
            if prev_line == "" or not prev_line.startswith("#"):
                print(f"✅ Removed duplicate line at line {i+1}")
                continue
        
        fixed_lines.append(line)
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)


def verify_fix():
    """Verify the syntax is now correct."""
    
    file_path = Path("multi_coder_analysis/run_multi_coder_tot.py")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try to compile
        compile(content, str(file_path), 'exec')
        print("✅ Syntax verification passed!")
        return True
    except SyntaxError as e:
        print(f"❌ Syntax error: {e}")
        print(f"   Line {e.lineno}: {e.text}")
        return False


def main():
    """Run the final fix."""
    print("Applying final syntax fix...")
    print("=" * 60)
    
    print("\n1. Removing duplicate line...")
    fix_duplicate_line()
    
    print("\n2. Verifying syntax...")
    if verify_fix():
        print("\n✅ Syntax error fixed successfully!")
    else:
        print("\n⚠️  Syntax error persists. Manual intervention needed.")


if __name__ == "__main__":
    main() 