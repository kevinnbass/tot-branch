#!/usr/bin/env python3
"""
Script to fix additional bugs found in the prompt layout experiment code.
"""

import re
from pathlib import Path


def fix_missing_tqdm_import():
    """Add missing tqdm import."""
    file_path = Path("multi_coder_analysis/run_multi_coder_tot.py")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if tqdm is already imported
    if "from tqdm import tqdm" not in content and "import tqdm" not in content:
        # Find the import section and add tqdm
        import_section = re.search(r'(import.*?\n)+', content)
        if import_section:
            end_pos = import_section.end()
            # Add the import after other imports
            content = content[:end_pos] + "from tqdm import tqdm\n" + content[end_pos:]
            print("✅ Added missing tqdm import")
        else:
            print("⚠️  Could not find import section")
    else:
        print("ℹ️  tqdm already imported")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)


def fix_provider_factory():
    """Fix the _provider_factory function signature."""
    file_path = Path("multi_coder_analysis/run_multi_coder_tot.py")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find and fix the _provider_factory definition
    for i, line in enumerate(lines):
        if "def _provider_factory(" in line and ("ranked:" in line or "max_candidates:" in line):
            # Check if it's the nested function (should just return provider)
            if i > 0 and "def run_tot_chain_batch" in ''.join(lines[max(0, i-20):i]):
                # This is the nested function, fix it
                lines[i] = "    def _provider_factory():\n"
                print("✅ Fixed _provider_factory signature")
                break
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)


def fix_confidence_scores_param():
    """Add confidence_scores parameter to run_tot_chain_batch."""
    file_path = Path("multi_coder_analysis/run_multi_coder_tot.py")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if confidence_scores is already in the signature
    if "run_tot_chain_batch" in content and "confidence_scores: bool = False" not in content:
        # Add it after layout parameter
        content = re.sub(
            r'(layout: str = "standard",\s*# NEW: Layout parameter)',
            r'\1\n    confidence_scores: bool = False,  # NEW: Confidence scores parameter',
            content
        )
        print("✅ Added confidence_scores parameter to run_tot_chain_batch")
    else:
        print("ℹ️  confidence_scores parameter already present")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)


def fix_global_miss_path():
    """Fix missing global declaration for _MISS_PATH."""
    file_path = Path("multi_coder_analysis/run_multi_coder_tot.py")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find where _MISS_PATH is assigned
    for i, line in enumerate(lines):
        if "_MISS_PATH = miss_path" in line and "global _MISS_PATH" not in lines[i-1]:
            # Insert global declaration
            lines.insert(i, "    global _MISS_PATH\n")
            print("✅ Added global _MISS_PATH declaration")
            break
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)


def add_layout_validation():
    """Add validation for unknown layouts in _assemble_prompt functions."""
    file_path = Path("multi_coder_analysis/run_multi_coder_tot.py")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add validation at the start of _assemble_prompt
    validation_code = '''    # Validate layout
    valid_layouts = ['standard', 'recency', 'sandwich', 'minimal_system', 'question_first']
    if layout not in valid_layouts:
        logging.warning(f"Unknown layout '{layout}', using 'standard' instead")
        layout = 'standard'
    
'''
    
    # Find _assemble_prompt function
    pattern = r'(def _assemble_prompt\([^)]+\) -> Tuple\[str, str\]:\s*\n\s*"""[^"]*"""\s*\n)'
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    if match:
        # Insert validation after docstring
        insert_pos = match.end()
        content = content[:insert_pos] + validation_code + content[insert_pos:]
        print("✅ Added layout validation to _assemble_prompt")
    
    # Do the same for _assemble_prompt_batch
    pattern_batch = r'(def _assemble_prompt_batch\([^)]+\) -> Tuple\[str, str\]:\s*\n\s*"""[^"]*"""\s*\n)'
    match_batch = re.search(pattern_batch, content, re.MULTILINE | re.DOTALL)
    if match_batch:
        insert_pos_batch = match_batch.end()
        # Adjust for the previous insertion
        if match and match.end() < match_batch.end():
            insert_pos_batch += len(validation_code)
        content = content[:insert_pos_batch] + validation_code + content[insert_pos_batch:]
        print("✅ Added layout validation to _assemble_prompt_batch")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)


def fix_layout_experiment_confidence():
    """Add confidence_scores parameter to layout experiment."""
    file_path = Path("multi_coder_analysis/layout_experiment.py")
    
    if not file_path.exists():
        print("⚠️  layout_experiment.py not found")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add confidence_scores to run_coding_step_tot call
    if "confidence_scores=" not in content:
        # Find the run_coding_step_tot call
        pattern = r'(run_coding_step_tot\([^)]+)'
        match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
        if match:
            # Add confidence_scores parameter
            content = content[:match.end()] + ",\n            confidence_scores=args.confidence_scores if hasattr(args, 'confidence_scores') else False" + content[match.end():]
            print("✅ Added confidence_scores to layout experiment")
    else:
        print("ℹ️  confidence_scores already in layout experiment")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)


def add_constants_for_defaults():
    """Add constants for commonly used default values."""
    file_path = Path("multi_coder_analysis/run_multi_coder_tot.py")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find where to add constants (after imports)
    import_end = 0
    for i, line in enumerate(lines):
        if line.strip() and not line.startswith('import') and not line.startswith('from') and i > 10:
            import_end = i
            break
    
    # Check if constants already exist
    constants_exist = any("DEFAULT_MODEL" in line for line in lines)
    
    if not constants_exist:
        constants = [
            "\n# Default constants\n",
            "DEFAULT_MODEL = \"models/gemini-2.0-flash-exp\"\n",
            "DEFAULT_TEMPERATURE = 0.7\n",
            "DEFAULT_BATCH_SIZE = 10\n",
            "VALID_LAYOUTS = ['standard', 'recency', 'sandwich', 'minimal_system', 'question_first']\n",
            "\n"
        ]
        
        # Insert constants
        lines[import_end:import_end] = constants
        print("✅ Added default constants")
        
        # Replace hardcoded values
        for i, line in enumerate(lines):
            if "models/gemini-2.5-flash-preview-04-17" in line:
                lines[i] = line.replace("models/gemini-2.5-flash-preview-04-17", "DEFAULT_MODEL")
        
        print("✅ Replaced hardcoded model names with constant")
    else:
        print("ℹ️  Constants already defined")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)


def main():
    """Run all fixes."""
    print("Fixing additional bugs...")
    print("=" * 60)
    
    print("\n1. Adding missing tqdm import...")
    fix_missing_tqdm_import()
    
    print("\n2. Fixing _provider_factory signature...")
    fix_provider_factory()
    
    print("\n3. Adding confidence_scores parameter...")
    fix_confidence_scores_param()
    
    print("\n4. Fixing global _MISS_PATH declaration...")
    fix_global_miss_path()
    
    print("\n5. Adding layout validation...")
    add_layout_validation()
    
    print("\n6. Fixing layout experiment confidence scores...")
    fix_layout_experiment_confidence()
    
    print("\n7. Adding constants for default values...")
    add_constants_for_defaults()
    
    print("\n✅ Additional bug fixes completed!")
    print("\nModified files:")
    print("  - multi_coder_analysis/run_multi_coder_tot.py")
    print("  - multi_coder_analysis/layout_experiment.py (if exists)")
    
    print("\nRecommended next steps:")
    print("  1. Run the test script to verify fixes")
    print("  2. Run a small experiment to test all layouts")
    print("  3. Check for any remaining warnings or errors")


if __name__ == "__main__":
    main() 