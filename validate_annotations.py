#!/usr/bin/env python3
"""
Annotation Coverage Validation Tool

Validates that regex annotations and prompt front-matter are consistent:
- Every [Qn.x] in regex file has corresponding prompt row_map entry
- Every regex_map entry points to existing regex rules
- No orphaned annotations
- Naming consistency checks
"""

import re
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Union
from collections import defaultdict

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.annotation_prompt_loader import load_prompt_and_meta

class AnnotationValidator:
    def __init__(self, project_root: Union[str, Path]):
        self.project_root = Path(project_root) if isinstance(project_root, str) else project_root
        self.regex_file = self.project_root / "data" / "regex" / "hop_patterns.yml"
        self.prompts_dir = self.project_root / "data" / "prompts"
        
        # Storage for parsed data
        self.regex_annotations: Dict[str, List[str]] = {}  # rule_name -> [annotations]
        self.prompt_metadata: Dict[str, Dict[str, Any]] = {}  # hop_id -> metadata
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    def run_validation(self) -> bool:
        """Run all validation checks. Returns True if all checks pass."""
        print("🔍 Starting annotation validation...")
        
        # Parse files
        self._parse_regex_file()
        self._parse_prompt_files()
        
        # Run validation checks
        self._check_regex_to_prompt_mapping()
        self._check_prompt_to_regex_mapping()
        self._check_orphaned_annotations()
        self._check_naming_consistency()
        self._check_dead_regex_rules()
        
        # Report results
        self._print_results()
        
        return len(self.errors) == 0
    
    def _parse_regex_file(self):
        """Parse regex file and extract annotations."""
        print("📖 Parsing regex file...")
        
        if not self.regex_file.exists():
            self.errors.append(f"Regex file not found: {self.regex_file}")
            return
            
        with open(self.regex_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError as e:
            self.errors.append(f"Invalid YAML in regex file: {e}")
            return
            
        # Extract annotations from comments
        annotation_pattern = re.compile(r'#\s*\[([Q\d\.]+)\]')
        lines = content.split('\n')
        
        current_rule = None
        for line in lines:
            # Check for rule name - handle both formats: "- name:" and "  name:"
            if 'name:' in line and not line.strip().startswith('#'):
                rule_match = re.search(r'name:\s*(\S+)', line)
                if rule_match:
                    current_rule = rule_match.group(1)
                    if current_rule not in self.regex_annotations:
                        self.regex_annotations[current_rule] = []
            
            # Extract annotations from comments - store them with the last seen rule
            # or as orphaned if no rule context
            if '#' in line:
                annotations = annotation_pattern.findall(line)
                for annotation in annotations:
                    if current_rule:
                        self.regex_annotations[current_rule].append(annotation)
                    else:
                        # Handle orphaned annotations
                        if '__orphaned__' not in self.regex_annotations:
                            self.regex_annotations['__orphaned__'] = []
                        self.regex_annotations['__orphaned__'].append(annotation)
    
    def _parse_prompt_files(self):
        """Parse all prompt files and extract metadata."""
        print("📖 Parsing prompt files...")
        
        for prompt_file in self.prompts_dir.glob("hop_Q*.txt"):
            try:
                _, meta = load_prompt_and_meta(prompt_file)
                if meta and 'meta_id' in meta:
                    self.prompt_metadata[meta['meta_id']] = meta
                else:
                    self.warnings.append(f"No metadata found in {prompt_file.name}")
            except Exception as e:
                self.errors.append(f"Error parsing {prompt_file.name}: {e}")
    
    def _check_regex_to_prompt_mapping(self):
        """Check that every regex annotation has corresponding prompt row."""
        print("🔗 Checking regex → prompt mapping...")
        
        for rule_name, annotations in self.regex_annotations.items():
            for annotation in annotations:
                # Parse annotation (e.g., "Q1.1" -> hop="Q1", row="Q1.1")
                if '.' not in annotation:
                    self.warnings.append(f"Malformed annotation '{annotation}' in rule {rule_name}")
                    continue
                    
                hop_id = annotation.split('.')[0]
                
                if hop_id not in self.prompt_metadata:
                    self.errors.append(f"Regex rule '{rule_name}' references non-existent hop '{hop_id}'")
                    continue
                    
                meta = self.prompt_metadata[hop_id]
                if 'row_map' not in meta or meta['row_map'] is None or annotation not in meta['row_map']:
                    self.errors.append(f"Regex annotation '{annotation}' in rule '{rule_name}' has no corresponding row_map entry")
    
    def _check_prompt_to_regex_mapping(self):
        """Check that every prompt regex_map entry points to existing rules."""
        print("🔗 Checking prompt → regex mapping...")
        
        all_regex_rules = set(self.regex_annotations.keys())
        
        for hop_id, meta in self.prompt_metadata.items():
            if 'regex_map' not in meta:
                self.warnings.append(f"Hop {hop_id} has no regex_map")
                continue
            
            regex_map = meta['regex_map']
            if regex_map is None:
                self.warnings.append(f"Hop {hop_id} has null regex_map")
                continue
                
            for row_id, rule_list in regex_map.items():
                if not isinstance(rule_list, list):
                    self.errors.append(f"Hop {hop_id} row {row_id}: regex_map value must be a list")
                    continue
                    
                for rule_ref in rule_list:
                    # Parse rule reference (e.g., "1.IntensifierRiskAdjV2" -> "IntensifierRiskAdjV2")
                    if '.' in rule_ref:
                        rule_name = rule_ref.split('.', 1)[1]
                    else:
                        rule_name = rule_ref
                        
                    if rule_name not in all_regex_rules:
                        self.errors.append(f"Hop {hop_id} row {row_id}: references non-existent regex rule '{rule_name}'")
    
    def _check_orphaned_annotations(self):
        """Check for orphaned annotations (regex without prompt coverage, or vice versa)."""
        print("🔍 Checking for orphaned annotations...")
        
        # Collect all annotations from regex side
        regex_annotations = set()
        for annotations in self.regex_annotations.values():
            regex_annotations.update(annotations)
            
        # Collect all annotations from prompt side
        prompt_annotations = set()
        for meta in self.prompt_metadata.values():
            if 'row_map' in meta and meta['row_map'] is not None:
                prompt_annotations.update(meta['row_map'].keys())
        
        # Check for orphans
        orphaned_regex = regex_annotations - prompt_annotations
        orphaned_prompts = prompt_annotations - regex_annotations
        
        for annotation in orphaned_regex:
            self.warnings.append(f"Regex annotation '{annotation}' has no corresponding prompt row")
            
        for annotation in orphaned_prompts:
            self.warnings.append(f"Prompt row '{annotation}' has no corresponding regex annotation")
    
    def _check_naming_consistency(self):
        """Check naming consistency between row_map descriptions and prompt content."""
        print("📝 Checking naming consistency...")
        
        # This would require parsing prompt content to extract table rows
        # For now, just check that row_map keys follow expected pattern
        for hop_id, meta in self.prompt_metadata.items():
            if 'row_map' not in meta or meta['row_map'] is None:
                continue
                
            expected_prefix = hop_id
            for row_id in meta['row_map'].keys():
                if not row_id.startswith(expected_prefix):
                    self.warnings.append(f"Hop {hop_id}: row_map key '{row_id}' doesn't match expected prefix '{expected_prefix}'")
    
    def _check_dead_regex_rules(self):
        """Check for regex rules that are never referenced in prompts."""
        print("🧹 Checking for dead regex rules...")
        
        # Collect all referenced rules from prompts
        referenced_rules = set()
        for meta in self.prompt_metadata.values():
            if 'regex_map' in meta and meta['regex_map'] is not None:
                for rule_list in meta['regex_map'].values():
                    for rule_ref in rule_list:
                        if '.' in rule_ref:
                            rule_name = rule_ref.split('.', 1)[1]
                        else:
                            rule_name = rule_ref
                        referenced_rules.add(rule_name)
        
        # Check for unreferenced rules
        all_rules = set(self.regex_annotations.keys())
        dead_rules = all_rules - referenced_rules
        
        for rule in dead_rules:
            self.warnings.append(f"Regex rule '{rule}' is never referenced in any prompt")
    
    def _print_results(self):
        """Print validation results."""
        print("\n" + "="*60)
        print("📊 VALIDATION RESULTS")
        print("="*60)
        
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"   • {error}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   • {warning}")
        
        # Print success/failure
        if self.errors:
            print(f"\n❌ Validation failed ({len(self.errors)} errors, {len(self.warnings)} warnings)")
        elif self.warnings:
            print(f"\n⚠️  Validation passed with warnings ({len(self.warnings)} warnings)")
        else:
            print(f"\n✅ Validation passed! (0 errors, 0 warnings)")
        
        # Print statistics
        print(f"\n📈 STATISTICS:")
        print(f"   • Regex rules: {len(self.regex_annotations)}")
        print(f"   • Prompt hops: {len(self.prompt_metadata)}")
        total_annotations = sum(len(anns) for anns in self.regex_annotations.values())
        print(f"   • Total regex annotations: {total_annotations}")
        total_rows = sum(len(meta.get('row_map') or {}) for meta in self.prompt_metadata.values())
        print(f"   • Total prompt rows: {total_rows}")


def main():
    """Main CLI interface."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate annotation consistency")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(),
                       help="Root directory of the project")
    
    args = parser.parse_args()
    
    validator = AnnotationValidator(args.project_root)
    success = validator.run_validation()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 