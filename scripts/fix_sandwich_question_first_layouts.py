#!/usr/bin/env python3
"""
Fix sandwich and question_first layouts by adding their batch implementations.
"""

import sys
from pathlib import Path
import re

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))


def add_batch_implementations():
    """Add batch implementations for sandwich and question_first layouts."""
    
    file_path = Path("multi_coder_analysis/run_multi_coder_tot.py")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the location where we need to insert the new implementations
    # This should be before the else clause that falls back to standard
    fallback_pattern = r'(\s+else:\s*\n\s*# For other layouts, fall back to standard in batch mode)'
    
    # Create the new implementations
    new_implementations = '''        elif layout == "sandwich":
            # Sandwich layout for batch: Quick check → Segments → Detailed analysis
            # Extract quick check section from hop content
            import re
            quick_check_match = re.search(r"(### ⚡ QUICK DECISION CHECK.*?)(?=### Detailed Analysis|$)", hop_content, re.DOTALL)
            detailed_match = re.search(r"(### Detailed Analysis.*?)$", hop_content, re.DOTALL)
            
            if quick_check_match and detailed_match:
                quick_check = quick_check_match.group(1).strip()
                detailed = detailed_match.group(1).strip()
                
                # Build sandwich structure
                sandwich_instruction = f"""
{quick_check}

Now examine these segments:
{segment_block}

{detailed}

{instruction}
"""
                system_block = local_header
                user_block = sandwich_instruction + "\\n\\n" + local_footer
            else:
                # Fallback if sandwich markers not found
                logging.warning(f"Sandwich layout markers not found in hop {hop_idx}, using standard structure")
                system_block = local_header + "\\n\\n" + hop_content
                user_block = instruction + segment_block + "\\n\\n" + local_footer
                
        elif layout == "question_first":
            # Question first layout for batch: Question → Segments → Analysis rules
            import re
            # Extract the question from hop content
            question_match = re.search(r"(### Question Q\\d+.*?)(?=\\n\\*\\*|\\n\\n|$)", hop_content, re.DOTALL)
            
            if question_match:
                question = question_match.group(1).strip()
                # Remove question from hop content to avoid duplication
                hop_content_no_q = hop_content.replace(question, "").strip()
                
                question_first_structure = f"""
{question}

Analyze each of these segments to answer the above question:
{segment_block}

{instruction}

Analysis Guidelines:
{hop_content_no_q}
"""
                system_block = local_header
                user_block = question_first_structure + "\\n\\n" + local_footer
            else:
                # Fallback if question not found
                logging.warning(f"Question not found in hop {hop_idx} for question_first layout, using standard structure")
                system_block = local_header + "\\n\\n" + hop_content
                user_block = instruction + segment_block + "\\n\\n" + local_footer
                
'''
    
    # Insert the new implementations before the else clause
    match = re.search(fallback_pattern, content)
    if match:
        insert_pos = match.start()
        content = content[:insert_pos] + new_implementations + content[insert_pos:]
        print("✅ Added batch implementations for sandwich and question_first layouts")
    else:
        print("❌ Could not find the insertion point for batch implementations")
        return False
    
    # Write back the modified content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True


def verify_implementations():
    """Verify that the implementations were added correctly."""
    
    file_path = Path("multi_coder_analysis/run_multi_coder_tot.py")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for sandwich batch implementation
    if 'elif layout == "sandwich":' in content and 'sandwich_instruction' in content:
        print("✅ Sandwich batch implementation found")
    else:
        print("❌ Sandwich batch implementation not found")
    
    # Check for question_first batch implementation
    if 'elif layout == "question_first":' in content and 'question_first_structure' in content:
        print("✅ Question_first batch implementation found")
    else:
        print("❌ Question_first batch implementation not found")
    
    # Count total layout implementations in batch function
    batch_func_match = re.search(r'def _assemble_prompt_batch\(.*?\n(.*?)(?=\ndef|\Z)', content, re.DOTALL)
    if batch_func_match:
        batch_content = batch_func_match.group(1)
        layout_count = len(re.findall(r'elif layout == "[^"]+":', batch_content))
        print(f"\n📊 Total layout implementations in batch mode: {layout_count + 1}")  # +1 for the initial if
        
        # List all implemented layouts
        implemented = re.findall(r'(?:if|elif) layout == "([^"]+)":', batch_content)
        print(f"📋 Implemented layouts: {', '.join(implemented)}")


def main():
    """Main function to fix the layouts."""
    print("Fixing sandwich and question_first layouts...")
    print("=" * 60)
    
    print("\n1. Adding batch implementations...")
    if add_batch_implementations():
        print("\n2. Verifying implementations...")
        verify_implementations()
        
        print("\n✅ Successfully fixed sandwich and question_first layouts!")
        print("\nThese layouts now have full batch support and won't fall back to standard.")
        print("\nYou can now run experiments with these layouts without seeing warnings.")
    else:
        print("\n❌ Failed to add implementations. Please check the file structure.")


if __name__ == "__main__":
    main() 