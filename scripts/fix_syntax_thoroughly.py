#!/usr/bin/env python3
"""
Thoroughly fix the syntax error in run_multi_coder_tot.py.
"""

from pathlib import Path
import re


def fix_broken_comment():
    """Fix the broken comment and misplaced validation code."""
    
    file_path = Path("multi_coder_analysis/run_multi_coder_tot.py")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix the broken comment and misplaced validation
    # Look for the problematic pattern
    broken_pattern = r'# Attach same meta to every HopContext in\s+# Validate layout\s+valid_layouts[^}]+this batch for consistency'
    
    if re.search(broken_pattern, content, re.DOTALL):
        # Replace with the correct code
        fixed_comment = "# Attach same meta to every HopContext in this batch for consistency"
        content = re.sub(broken_pattern, fixed_comment, content, flags=re.DOTALL)
        print("✅ Fixed broken comment and removed misplaced validation code")
    else:
        print("⚠️  Could not find the exact broken pattern, trying alternative fix...")
        
        # Alternative: look for the specific lines
        lines = content.split('\n')
        fixed_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check for the broken comment
            if "# Attach same meta to every HopContext in" in line and "# Validate layout" in line:
                # Fix this line
                fixed_lines.append("        # Attach same meta to every HopContext in this batch for consistency")
                # Skip the validation code that shouldn't be here
                i += 1
                while i < len(lines) and ("valid_layouts" in lines[i] or 
                                         "if layout not in" in lines[i] or
                                         "logging.warning" in lines[i] or
                                         "layout = 'standard'" in lines[i] or
                                         "this batch for consistency" in lines[i]):
                    i += 1
                continue
            
            fixed_lines.append(line)
            i += 1
        
        content = '\n'.join(fixed_lines)
        print("✅ Applied alternative fix")
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)


def ensure_validation_in_right_place():
    """Ensure validation code is in the right functions."""
    
    file_path = Path("multi_coder_analysis/run_multi_coder_tot.py")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    validation_code = '''    # Validate layout
    valid_layouts = ['standard', 'recency', 'sandwich', 'minimal_system', 'question_first']
    if layout not in valid_layouts:
        logging.warning(f"Unknown layout '{layout}', using 'standard' instead")
        layout = 'standard'
    
'''
    
    # Check if validation is already in _assemble_prompt
    if "def _assemble_prompt" in content and "# Validate layout" not in content.split("def _assemble_prompt_batch")[0]:
        # Add to _assemble_prompt after the docstring
        pattern = r'(def _assemble_prompt\([^)]+\) -> Tuple\[str, str\]:\s*\n\s*"""[^"]*"""\s*\n)'
        match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
        if match:
            insert_pos = match.end()
            content = content[:insert_pos] + validation_code + content[insert_pos:]
            print("✅ Added layout validation to _assemble_prompt")
    
    # Check if validation is already in _assemble_prompt_batch
    parts = content.split("def _assemble_prompt_batch")
    if len(parts) > 1 and "# Validate layout" not in parts[1].split("def ")[0]:
        # Add to _assemble_prompt_batch after the docstring
        pattern = r'(def _assemble_prompt_batch\([^)]+\) -> Tuple\[str, str\]:\s*\n\s*"""[^"]*"""\s*\n)'
        match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
        if match:
            insert_pos = match.end()
            content = content[:insert_pos] + validation_code + content[insert_pos:]
            print("✅ Added layout validation to _assemble_prompt_batch")
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)


def fix_provider_factory_params():
    """Remove incorrect parameters from _provider_factory."""
    
    file_path = Path("multi_coder_analysis/run_multi_coder_tot.py")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix the _provider_factory definition inside run_tot_chain_batch
    pattern = r'def _provider_factory\(\s*ranked: bool = False,\s*# NEW: Ranking parameter\s*max_candidates: int = 5,\s*# NEW: Max candidates for ranking\s*\):'
    
    if re.search(pattern, content):
        content = re.sub(pattern, 'def _provider_factory():', content)
        print("✅ Fixed _provider_factory signature")
    else:
        print("ℹ️  _provider_factory signature already correct or not found")
    
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
    """Run all fixes."""
    print("Thoroughly fixing syntax errors...")
    print("=" * 60)
    
    print("\n1. Fixing broken comment and misplaced code...")
    fix_broken_comment()
    
    print("\n2. Ensuring validation code is in the right place...")
    ensure_validation_in_right_place()
    
    print("\n3. Fixing _provider_factory parameters...")
    fix_provider_factory_params()
    
    print("\n4. Verifying syntax...")
    if verify_syntax():
        print("\n✅ All syntax errors fixed successfully!")
    else:
        print("\n⚠️  There may still be syntax errors. Please check manually.")


if __name__ == "__main__":
    main() 