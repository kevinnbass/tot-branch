#!/usr/bin/env python3
"""
Add the missing ranked and max_candidates parameters to run_tot_chain_batch.
"""

from pathlib import Path
import re


def add_missing_parameters():
    """Add ranked and max_candidates to run_tot_chain_batch signature."""
    
    file_path = Path("multi_coder_analysis/run_multi_coder_tot.py")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the run_tot_chain_batch function signature
    pattern = r'(def run_tot_chain_batch\([^)]+layout: str = "standard",\s*# NEW: Layout parameter)'
    
    match = re.search(pattern, content, re.DOTALL)
    if match:
        # Add the missing parameters after layout
        replacement = match.group(1) + '\n    ranked: bool = False,  # NEW: Ranking parameter\n    max_candidates: int = 5,  # NEW: Max candidates for ranking'
        content = content[:match.start()] + replacement + content[match.end():]
        print("✅ Added ranked and max_candidates parameters")
    else:
        print("⚠️  Could not find the exact location to add parameters")
        # Try alternative approach
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'layout: str = "standard",  # NEW: Layout parameter' in line:
                # Insert after this line
                lines.insert(i+1, '    ranked: bool = False,  # NEW: Ranking parameter')
                lines.insert(i+2, '    max_candidates: int = 5,  # NEW: Max candidates for ranking')
                content = '\n'.join(lines)
                print("✅ Added parameters using alternative method")
                break
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)


def verify_parameters():
    """Verify the parameters are now present."""
    
    file_path = Path("multi_coder_analysis/run_multi_coder_tot.py")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if both parameters are present in run_tot_chain_batch
    if 'ranked: bool = False' in content and 'max_candidates: int = 5' in content:
        # Make sure they're in the right function
        lines = content.split('\n')
        in_function = False
        has_ranked = False
        has_max_candidates = False
        
        for line in lines:
            if 'def run_tot_chain_batch(' in line:
                in_function = True
            elif in_function and '):' in line:
                break
            elif in_function:
                if 'ranked: bool = False' in line:
                    has_ranked = True
                if 'max_candidates: int = 5' in line:
                    has_max_candidates = True
        
        if has_ranked and has_max_candidates:
            print("✅ Both parameters verified in run_tot_chain_batch")
            return True
        else:
            print("❌ Parameters not found in run_tot_chain_batch function")
            return False
    else:
        print("❌ Parameters not found in file")
        return False


def main():
    """Add the missing parameters."""
    print("Adding missing parameters to run_tot_chain_batch...")
    print("=" * 60)
    
    print("\n1. Adding ranked and max_candidates parameters...")
    add_missing_parameters()
    
    print("\n2. Verifying parameters...")
    if verify_parameters():
        print("\n✅ Parameters added successfully!")
    else:
        print("\n⚠️  Failed to add parameters correctly.")


if __name__ == "__main__":
    main() 