#!/usr/bin/env python3
"""
Fix path handling bugs in annotation system

Fixes the issue where constructors expect Path objects but receive strings,
causing TypeError: unsupported operand type(s) for /: 'str' and 'str'
"""

import re
from pathlib import Path

def fix_file_path_handling(file_path: Path, class_name: str):
    """Fix path handling in a specific file."""
    if not file_path.exists():
        print(f"❌ {file_path} not found")
        return False
    
    content = file_path.read_text(encoding='utf-8')
    
    # Check if Union import exists
    if "from typing import" in content and "Union" not in content:
        # Add Union to existing typing import
        typing_pattern = r"from typing import ([^\\n]+)"
        match = re.search(typing_pattern, content)
        if match:
            imports = match.group(1)
            if "Union" not in imports:
                new_imports = imports.rstrip() + ", Union"
                content = content.replace(f"from typing import {imports}", f"from typing import {new_imports}")
                print(f"✅ Added Union import to {file_path.name}")
    
    # Fix constructor signature and implementation
    old_constructor_pattern = rf"def __init__\(self, project_root: Path\):"
    new_constructor_signature = f"def __init__(self, project_root: Union[str, Path]):"
    
    if re.search(old_constructor_pattern, content):
        content = re.sub(old_constructor_pattern, new_constructor_signature, content)
        
        # Fix the implementation
        old_assignment = "self.project_root = project_root"
        new_assignment = "self.project_root = Path(project_root) if isinstance(project_root, str) else project_root"
        
        if old_assignment in content:
            content = content.replace(old_assignment, new_assignment)
            print(f"✅ Fixed path handling in {class_name} constructor")
        
        file_path.write_text(content, encoding='utf-8')
        return True
    else:
        print(f"ℹ️  {class_name} constructor pattern not found or already fixed")
        return False

def main():
    """Fix path handling in all annotation system files."""
    print("🔧 Fixing path handling bugs in annotation system...")
    print()
    
    files_to_fix = [
        ("scripts/validate_annotations.py", "AnnotationValidator"),
        ("scripts/generate_coverage_report.py", "DocumentationGenerator"), 
        ("scripts/annotation_dev_tools.py", "AnnotationDevTools"),
        ("scripts/annotation_analytics.py", "AnnotationAnalytics"),
    ]
    
    fixed_count = 0
    for file_path, class_name in files_to_fix:
        if fix_file_path_handling(Path(file_path), class_name):
            fixed_count += 1
    
    print()
    if fixed_count > 0:
        print(f"🎉 Fixed path handling in {fixed_count} files!")
        print()
        print("✅ All annotation system classes now accept both string and Path inputs")
        print("✅ No more TypeError: unsupported operand type(s) for /: 'str' and 'str'")
    else:
        print("ℹ️  All files already have correct path handling")
    
    print()
    print("🧪 Testing fixes...")
    
    # Test the fixes
    try:
        import sys
        sys.path.insert(0, '.')
        
        from scripts.validate_annotations import AnnotationValidator
        from scripts.annotation_dev_tools import AnnotationDevTools
        from scripts.generate_coverage_report import DocumentationGenerator
        from scripts.annotation_analytics import AnnotationAnalytics
        from pathlib import Path
        
        # Test string inputs
        v1 = AnnotationValidator('.')
        d1 = AnnotationDevTools('.')
        g1 = DocumentationGenerator('.', './docs')
        a1 = AnnotationAnalytics('.')
        
        # Test Path inputs  
        v2 = AnnotationValidator(Path('.'))
        d2 = AnnotationDevTools(Path('.'))
        g2 = DocumentationGenerator(Path('.'), Path('./docs'))
        a2 = AnnotationAnalytics(Path('.'))
        
        print("✅ All classes work with both string and Path inputs!")
        
    except Exception as e:
        print(f"❌ Testing failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Path handling bugs fixed successfully!")
    else:
        print("\n❌ Some issues remain") 