#!/usr/bin/env python3
"""
Fix the syntax error in run_multi_coder_tot.py caused by incorrect placement of validation code.
"""

from pathlib import Path


def fix_syntax_error():
    """Fix the syntax error by removing the misplaced validation code."""
    
    file_path = Path("multi_coder_analysis/run_multi_coder_tot.py")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find and remove the misplaced validation code
    # Look for the problematic lines around line 570
    fixed_lines = []
    skip_mode = False
    
    for i, line in enumerate(lines):
        # Check if this is the misplaced validation code
        if i >= 569 and i <= 575:
            if "# Validate layout" in line and "Attach same meta" in lines[i-1]:
                # This is the misplaced code, skip it
                skip_mode = True
                continue
            elif skip_mode and "this batch for consistency" in line:
                # This line should be joined with the previous comment
                fixed_lines[-1] = fixed_lines[-1].rstrip() + " this batch for consistency\n"
                skip_mode = False
                continue
            elif skip_mode and line.strip() in ["valid_layouts = ['standard', 'recency', 'sandwich', 'minimal_system', 'question_first']",
                                                  "if layout not in valid_layouts:",
                                                  "logging.warning(f\"Unknown layout '{layout}', using 'standard' instead\")",
                                                  "layout = 'standard'"]:
                # Skip these lines
                continue
            elif skip_mode and line.strip() == "":
                skip_mode = False
                continue
        
        fixed_lines.append(line)
    
    # Write back the fixed content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    print("✅ Fixed syntax error in run_multi_coder_tot.py")
    
    # Now properly add the validation code to the right functions
    add_validation_properly()


def add_validation_properly():
    """Add the validation code to the proper locations."""
    
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
    if "# Validate layout" not in content:
        # Add to _assemble_prompt after the docstring
        import re
        
        # Find _assemble_prompt function
        pattern = r'(def _assemble_prompt\([^)]+\) -> Tuple\[str, str\]:\s*\n\s*"""[^"]*"""\s*\n)'
        match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
        if match:
            # Insert validation after docstring
            insert_pos = match.end()
            content = content[:insert_pos] + validation_code + content[insert_pos:]
            print("✅ Added layout validation to _assemble_prompt")
        
        # Also add to _assemble_prompt_batch
        pattern_batch = r'(def _assemble_prompt_batch\([^)]+\) -> Tuple\[str, str\]:\s*\n\s*"""[^"]*"""\s*\n)'
        match_batch = re.search(pattern_batch, content, re.MULTILINE | re.DOTALL)
        if match_batch:
            insert_pos_batch = match_batch.end()
            # Adjust for the previous insertion
            if match and match.end() < match_batch.end():
                insert_pos_batch += len(validation_code)
            content = content[:insert_pos_batch] + validation_code + content[insert_pos_batch:]
            print("✅ Added layout validation to _assemble_prompt_batch")
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)


def main():
    """Fix the syntax error."""
    print("Fixing syntax error in run_multi_coder_tot.py...")
    print("=" * 60)
    
    fix_syntax_error()
    
    print("\n✅ Syntax error fixed!")
    print("\nYou can now run the test script again.")


if __name__ == "__main__":
    main() 