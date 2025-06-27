#!/usr/bin/env python3
"""
Quick fix script for annotation system bugs

Addresses the main issues found in testing:
1. Null handling in validation
2. Database connection cleanup
3. Regex escape sequence warnings
"""

import re
from pathlib import Path

def fix_validation_null_handling():
    """Fix null handling in validation script."""
    validate_file = Path("scripts/validate_annotations.py")
    if not validate_file.exists():
        print("❌ validate_annotations.py not found")
        return
    
    content = validate_file.read_text(encoding='utf-8')
    
    # Fix null regex_map handling
    old_pattern = r"for row_id, rule_list in meta\['regex_map'\]\.items\(\):"
    new_pattern = """regex_map = meta['regex_map']
            if regex_map is None:
                self.warnings.append(f"Hop {hop_id} has null regex_map")
                continue
                
            for row_id, rule_list in regex_map.items():"""
    
    if old_pattern in content:
        content = re.sub(
            r"for row_id, rule_list in meta\['regex_map'\]\.items\(\):",
            new_pattern,
            content
        )
        validate_file.write_text(content, encoding='utf-8')
        print("✅ Fixed null handling in validate_annotations.py")
    else:
        print("ℹ️  Null handling already fixed in validate_annotations.py")

def fix_regex_escape_warnings():
    """Fix regex escape sequence warnings."""
    dev_tools_file = Path("scripts/annotation_dev_tools.py")
    if not dev_tools_file.exists():
        print("❌ annotation_dev_tools.py not found")
        return
    
    content = dev_tools_file.read_text(encoding='utf-8')
    
    # Fix escape sequences in vim config
    old_vim_regex = r"syntax match AnnotationComment /# \[Q\d\+\.\d\+\]/ containedin=yamlComment"
    new_vim_regex = r"syntax match AnnotationComment /# \\[Q\\d\\+\\.\\d\\+\\]/ containedin=yamlComment"
    
    if old_vim_regex in content:
        content = content.replace(old_vim_regex, new_vim_regex)
        dev_tools_file.write_text(content, encoding='utf-8')
        print("✅ Fixed regex escape sequences in annotation_dev_tools.py")
    else:
        print("ℹ️  Regex escape sequences already fixed in annotation_dev_tools.py")

def fix_database_cleanup():
    """Add database cleanup improvements."""
    analytics_file = Path("scripts/annotation_analytics.py")
    if not analytics_file.exists():
        print("❌ annotation_analytics.py not found")
        return
    
    content = analytics_file.read_text(encoding='utf-8')
    
    # Check if database cleanup is already improved
    if "finally:" in content and "conn.close()" in content:
        print("ℹ️  Database cleanup already improved in annotation_analytics.py")
        return
    
    # Add improved database handling
    old_store_metrics = """        except sqlite3.Error as e:
            print(f"Warning: Could not store metrics in database: {e}")"""
    
    new_store_metrics = """        except sqlite3.Error as e:
            print(f"Warning: Could not store metrics in database: {e}")
        finally:
            # Ensure database connection is properly closed
            if conn:
                try:
                    conn.close()
                except:
                    pass"""
    
    if old_store_metrics in content and "finally:" not in content:
        content = content.replace(old_store_metrics, new_store_metrics)
        analytics_file.write_text(content, encoding='utf-8')
        print("✅ Improved database cleanup in annotation_analytics.py")
    else:
        print("ℹ️  Database cleanup already improved or pattern not found")

def fix_test_cleanup():
    """Fix test cleanup for Windows compatibility."""
    test_file = Path("tests/test_annotation_system.py")
    if not test_file.exists():
        print("❌ test_annotation_system.py not found")
        return
    
    content = test_file.read_text(encoding='utf-8')
    
    # Check if Windows-compatible cleanup is already added
    if "max_retries" in content and "time.sleep" in content:
        print("ℹ️  Test cleanup already improved for Windows compatibility")
        return
    
    # Add Windows-compatible cleanup
    old_teardown = """    def tearDown(self):
        \"\"\"Clean up test environment.\"\"\"
        import shutil
        shutil.rmtree(self.temp_dir)"""
    
    new_teardown = """    def tearDown(self):
        \"\"\"Clean up test environment.\"\"\"
        import shutil
        import time
        
        # Add delay and retry logic for Windows
        max_retries = 3
        for attempt in range(max_retries):
            try:
                shutil.rmtree(self.temp_dir)
                break
            except PermissionError:
                if attempt < max_retries - 1:
                    time.sleep(0.2)
                    continue
                else:
                    print(f"Warning: Could not clean up {self.temp_dir}")
                    break"""
    
    if old_teardown in content:
        content = content.replace(old_teardown, new_teardown)
        test_file.write_text(content, encoding='utf-8')
        print("✅ Improved test cleanup for Windows compatibility")
    else:
        print("ℹ️  Test cleanup pattern not found or already improved")

def create_requirements_file():
    """Create requirements.txt if it doesn't exist."""
    req_file = Path("requirements.txt")
    if req_file.exists():
        print("ℹ️  requirements.txt already exists")
        return
    
    requirements = """# Annotation system requirements
pyyaml>=6.0
pytest>=7.0
"""
    
    req_file.write_text(requirements)
    print("✅ Created requirements.txt")

def main():
    """Run all fixes."""
    print("🔧 Running annotation system bug fixes...")
    print()
    
    fix_validation_null_handling()
    fix_regex_escape_warnings()
    fix_database_cleanup()
    fix_test_cleanup()
    create_requirements_file()
    
    print()
    print("🎉 Bug fixes completed!")
    print()
    print("📋 Summary of fixes:")
    print("   • Null handling in validation")
    print("   • Regex escape sequence warnings")
    print("   • Database connection cleanup")
    print("   • Windows-compatible test cleanup")
    print("   • Requirements file creation")
    print()
    print("✅ The annotation system should now work more reliably!")

if __name__ == "__main__":
    main() 