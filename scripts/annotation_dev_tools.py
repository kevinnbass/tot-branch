#!/usr/bin/env python3
"""
Annotation Development Tools

Provides development workflow improvements:
- Real-time validation
- Diff impact analysis
- Pattern testing harness
- IDE integration helpers
"""

import re
import sys
import yaml
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional, Union
from collections import defaultdict
import subprocess
import tempfile

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.annotation_prompt_loader import load_prompt_and_meta

class AnnotationDevTools:
    def __init__(self, project_root: Union[str, Path]):
        self.project_root = Path(project_root) if isinstance(project_root, str) else project_root
        self.regex_file = self.project_root / "multi_coder_analysis" / "regex" / "hop_patterns.yml"
        self.prompts_dir = self.project_root / "multi_coder_analysis" / "prompts"
        
    def validate_on_save(self, file_path: Path) -> Dict[str, Any]:
        """Validate annotations when a file is saved."""
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'affected_files': []
        }
        
        if file_path.name == "hop_patterns.yml":
            result.update(self._validate_regex_changes(file_path))
        elif file_path.name.startswith("hop_Q") and file_path.suffix == ".txt":
            result.update(self._validate_prompt_changes(file_path))
        
        return result
    
    def analyze_diff_impact(self, file_path: Path, old_content: str, new_content: str) -> Dict[str, Any]:
        """Analyze the impact of changes to a file."""
        impact = {
            'changed_annotations': [],
            'affected_prompts': [],
            'affected_regex_rules': [],
            'breaking_changes': [],
            'recommendations': []
        }
        
        if file_path.name == "hop_patterns.yml":
            impact.update(self._analyze_regex_diff(old_content, new_content))
        elif file_path.name.startswith("hop_Q"):
            impact.update(self._analyze_prompt_diff(old_content, new_content))
        
        return impact
    
    def test_pattern_matching(self, test_text: str, show_annotations: bool = True) -> Dict[str, Any]:
        """Test which regex rules and annotations would match given text."""
        results = {
            'matches': [],
            'annotations_triggered': [],
            'hop_sequence': [],
            'explanation': ""
        }
        
        # Load regex rules
        try:
            with open(self.regex_file, 'r', encoding='utf-8') as f:
                regex_data = yaml.safe_load(f)
        except Exception as e:
            results['explanation'] = f"Error loading regex file: {e}"
            return results
        
        # Test against each hop's rules
        for hop_num in sorted(regex_data.keys()):
            if not isinstance(regex_data[hop_num], list):
                continue
                
            hop_matches = []
            for rule_data in regex_data[hop_num]:
                rule_name = rule_data.get('name', 'Unknown')
                pattern = rule_data.get('pattern', '')
                veto_pattern = rule_data.get('veto_pattern', '')
                frame = rule_data.get('frame', 'Neutral')
                mode = rule_data.get('mode', 'live')
                
                if mode == 'shadow':
                    continue  # Skip shadow rules
                
                try:
                    # Test main pattern
                    if pattern and re.search(pattern, test_text, re.IGNORECASE | re.MULTILINE):
                        # Check veto pattern
                        if veto_pattern and re.search(veto_pattern, test_text, re.IGNORECASE | re.MULTILINE):
                            hop_matches.append({
                                'rule': rule_name,
                                'frame': frame,
                                'status': 'vetoed',
                                'pattern_matched': True,
                                'veto_matched': True
                            })
                        else:
                            hop_matches.append({
                                'rule': rule_name,
                                'frame': frame,
                                'status': 'matched',
                                'pattern_matched': True,
                                'veto_matched': False
                            })
                            
                            # Add to results
                            results['matches'].append({
                                'hop': f"Q{hop_num}",
                                'rule': rule_name,
                                'frame': frame
                            })
                            
                            # Get annotations if requested
                            if show_annotations:
                                annotations = self._get_rule_annotations(rule_name)
                                results['annotations_triggered'].extend(annotations)
                
                except re.error as e:
                    hop_matches.append({
                        'rule': rule_name,
                        'frame': frame,
                        'status': 'regex_error',
                        'error': str(e)
                    })
            
            if hop_matches:
                results['hop_sequence'].append({
                    'hop': f"Q{hop_num}",
                    'matches': hop_matches
                })
        
        # Generate explanation
        if results['matches']:
            frames = [m['frame'] for m in results['matches']]
            frame_counts = {f: frames.count(f) for f in set(frames)}
            dominant_frame = max(frame_counts.items(), key=lambda x: x[1])[0]
            
            results['explanation'] = f"Text would likely be classified as '{dominant_frame}' based on {len(results['matches'])} regex matches."
        else:
            results['explanation'] = "No regex rules matched. Classification would depend on LLM evaluation."
        
        return results
    
    def generate_ide_config(self, ide: str = "vscode") -> str:
        """Generate IDE configuration for annotation validation."""
        if ide == "vscode":
            return self._generate_vscode_config()
        elif ide == "vim":
            return self._generate_vim_config()
        else:
            return "# IDE configuration not available for: " + ide
    
    def _validate_regex_changes(self, file_path: Path) -> Dict[str, Any]:
        """Validate changes to regex file."""
        result = {'errors': [], 'warnings': [], 'affected_files': []}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse YAML
            try:
                yaml.safe_load(content)
            except yaml.YAMLError as e:
                result['errors'].append(f"Invalid YAML syntax: {e}")
                result['valid'] = False
                return result
            
            # Extract and validate annotations
            annotation_pattern = re.compile(r'#\s*\[([Q\d\.]+)\]')
            annotations = annotation_pattern.findall(content)
            
            # Check annotation format
            for annotation in annotations:
                if not re.match(r'^Q\d+\.\d+$', annotation):
                    result['warnings'].append(f"Non-standard annotation format: {annotation}")
            
            # Find affected prompt files
            hop_ids = set()
            for annotation in annotations:
                if '.' in annotation:
                    hop_id = annotation.split('.')[0]
                    hop_ids.add(hop_id)
            
            for hop_id in hop_ids:
                prompt_file = self.prompts_dir / f"hop_{hop_id}.txt"
                if prompt_file.exists():
                    result['affected_files'].append(str(prompt_file))
        
        except Exception as e:
            result['errors'].append(f"Error validating regex file: {e}")
            result['valid'] = False
        
        return result
    
    def _validate_prompt_changes(self, file_path: Path) -> Dict[str, Any]:
        """Validate changes to prompt file."""
        result = {'errors': [], 'warnings': [], 'affected_files': []}
        
        try:
            _, meta = load_prompt_and_meta(file_path)
            
            if not meta:
                result['warnings'].append("No metadata found in prompt file")
                return result
            
            # Validate metadata structure
            required_fields = ['meta_id', 'row_map', 'regex_map', 'frame', 'summary']
            for field in required_fields:
                if field not in meta:
                    result['errors'].append(f"Missing required metadata field: {field}")
            
            # Validate row_map and regex_map consistency
            if 'row_map' in meta and 'regex_map' in meta:
                row_ids = set(meta['row_map'].keys())
                regex_ids = set(meta['regex_map'].keys())
                
                missing_regex = row_ids - regex_ids
                extra_regex = regex_ids - row_ids
                
                for row_id in missing_regex:
                    result['warnings'].append(f"Row '{row_id}' has no regex mapping")
                
                for row_id in extra_regex:
                    result['warnings'].append(f"Regex mapping '{row_id}' has no corresponding row")
            
            # Mark regex file as affected
            result['affected_files'].append(str(self.regex_file))
        
        except Exception as e:
            result['errors'].append(f"Error validating prompt file: {e}")
            result['valid'] = False
        
        return result
    
    def _analyze_regex_diff(self, old_content: str, new_content: str) -> Dict[str, Any]:
        """Analyze impact of regex file changes."""
        impact = {}
        
        # Extract annotations from both versions
        annotation_pattern = re.compile(r'#\s*\[([Q\d\.]+)\]')
        old_annotations = set(annotation_pattern.findall(old_content))
        new_annotations = set(annotation_pattern.findall(new_content))
        
        added_annotations = new_annotations - old_annotations
        removed_annotations = old_annotations - new_annotations
        
        impact['changed_annotations'] = {
            'added': list(added_annotations),
            'removed': list(removed_annotations)
        }
        
        # Find affected prompts
        affected_hops = set()
        for annotation in added_annotations | removed_annotations:
            if '.' in annotation:
                hop_id = annotation.split('.')[0]
                affected_hops.add(hop_id)
        
        impact['affected_prompts'] = [f"hop_{hop_id}.txt" for hop_id in affected_hops]
        
        # Check for breaking changes
        if removed_annotations:
            impact['breaking_changes'].append(f"Removed annotations: {', '.join(removed_annotations)}")
        
        return impact
    
    def _analyze_prompt_diff(self, old_content: str, new_content: str) -> Dict[str, Any]:
        """Analyze impact of prompt file changes."""
        impact = {}
        
        # Parse metadata from both versions
        try:
            old_meta = self._extract_metadata(old_content)
            new_meta = self._extract_metadata(new_content)
            
            # Compare row_map changes
            old_rows = set(old_meta.get('row_map', {}).keys())
            new_rows = set(new_meta.get('row_map', {}).keys())
            
            added_rows = new_rows - old_rows
            removed_rows = old_rows - new_rows
            
            if added_rows or removed_rows:
                impact['changed_annotations'] = {
                    'added_rows': list(added_rows),
                    'removed_rows': list(removed_rows)
                }
                
                impact['affected_regex_rules'] = ["hop_patterns.yml"]
                
                if removed_rows:
                    impact['breaking_changes'].append(f"Removed pattern rows: {', '.join(removed_rows)}")
        
        except Exception as e:
            impact['recommendations'] = [f"Could not analyze metadata changes: {e}"]
        
        return impact
    
    def _get_rule_annotations(self, rule_name: str) -> List[str]:
        """Get annotations for a specific rule."""
        try:
            with open(self.regex_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find rule section and extract annotations
            lines = content.split('\n')
            in_rule = False
            annotations = []
            
            for line in lines:
                if f"name: {rule_name}" in line:
                    in_rule = True
                elif in_rule and line.strip().startswith('- name:'):
                    break  # Next rule started
                elif in_rule and '#' in line:
                    annotation_pattern = re.compile(r'#\s*\[([Q\d\.]+)\]')
                    found = annotation_pattern.findall(line)
                    annotations.extend(found)
            
            return annotations
        except Exception:
            return []
    
    def _extract_metadata(self, content: str) -> Dict[str, Any]:
        """Extract YAML metadata from prompt content."""
        fm_pattern = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
        match = fm_pattern.match(content)
        
        if match:
            try:
                return yaml.safe_load(match.group(1)) or {}
            except yaml.YAMLError:
                pass
        
        return {}
    
    def _generate_vscode_config(self) -> str:
        """Generate VS Code configuration for annotation validation."""
        config = {
            "tasks": {
                "version": "2.0.0",
                "tasks": [
                    {
                        "label": "Validate Annotations",
                        "type": "shell",
                        "command": "python",
                        "args": ["scripts/validate_annotations.py", "--project-root", "${workspaceFolder}"],
                        "group": "build",
                        "presentation": {
                            "echo": True,
                            "reveal": "always",
                            "focus": False,
                            "panel": "shared"
                        },
                        "problemMatcher": []
                    },
                    {
                        "label": "Test Pattern",
                        "type": "shell",
                        "command": "python",
                        "args": ["scripts/annotation_dev_tools.py", "test", "${input:testText}"],
                        "group": "test",
                        "presentation": {
                            "echo": True,
                            "reveal": "always",
                            "focus": True,
                            "panel": "shared"
                        }
                    }
                ]
            },
            "inputs": [
                {
                    "id": "testText",
                    "description": "Text to test against regex patterns",
                    "default": "The virus is extremely dangerous and spreading rapidly.",
                    "type": "promptString"
                }
            ]
        }
        
        return json.dumps(config, indent=2)
    
    def _generate_vim_config(self) -> str:
        """Generate Vim configuration for annotation validation."""
        return '''
" Annotation validation for Vim
" Add to your .vimrc

" Auto-validate on save for annotation files
autocmd BufWritePost hop_patterns.yml !python scripts/validate_annotations.py
autocmd BufWritePost hop_Q*.txt !python scripts/validate_annotations.py

" Quick pattern testing
command! -nargs=1 TestPattern !python scripts/annotation_dev_tools.py test <args>

" Syntax highlighting for annotation comments
syntax match AnnotationComment /# \\[Q\\d\\+\\.\\d\\+\\]/ containedin=yamlComment
highlight AnnotationComment ctermfg=yellow guifg=yellow
'''


def main():
    """Main CLI interface for dev tools."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Annotation development tools")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate file on save')
    validate_parser.add_argument('file', type=Path, help='File to validate')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test pattern matching')
    test_parser.add_argument('text', help='Text to test')
    test_parser.add_argument('--no-annotations', action='store_true', help='Hide annotation details')
    
    # Diff command
    diff_parser = subparsers.add_parser('diff', help='Analyze diff impact')
    diff_parser.add_argument('file', type=Path, help='File that changed')
    diff_parser.add_argument('--old', required=True, help='Old content (or file path)')
    diff_parser.add_argument('--new', required=True, help='New content (or file path)')
    
    # IDE config command
    ide_parser = subparsers.add_parser('ide-config', help='Generate IDE configuration')
    ide_parser.add_argument('--ide', choices=['vscode', 'vim'], default='vscode')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    tools = AnnotationDevTools(args.project_root)
    
    if args.command == 'validate':
        result = tools.validate_on_save(args.file)
        print(json.dumps(result, indent=2))
        sys.exit(0 if result.get('valid', True) else 1)
    
    elif args.command == 'test':
        result = tools.test_pattern_matching(args.text, not args.no_annotations)
        print(json.dumps(result, indent=2))
    
    elif args.command == 'diff':
        # Read old and new content
        if Path(args.old).exists():
            old_content = Path(args.old).read_text(encoding='utf-8')
        else:
            old_content = args.old
            
        if Path(args.new).exists():
            new_content = Path(args.new).read_text(encoding='utf-8')
        else:
            new_content = args.new
        
        result = tools.analyze_diff_impact(args.file, old_content, new_content)
        print(json.dumps(result, indent=2))
    
    elif args.command == 'ide-config':
        config = tools.generate_ide_config(args.ide)
        print(config)


if __name__ == "__main__":
    main() 