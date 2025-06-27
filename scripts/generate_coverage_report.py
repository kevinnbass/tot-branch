#!/usr/bin/env python3
"""
Documentation Generation Tool

Generates comprehensive documentation for the annotation system:
- Coverage matrix showing regex-to-prompt mappings
- Visual dependency graphs in Mermaid format
- Gap analysis reports
- Performance insights
"""

import re
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Union
from collections import defaultdict, Counter
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from multi_coder_analysis.utils.prompt_loader import load_prompt_and_meta

class DocumentationGenerator:
    def __init__(self, project_root: Union[str, Path], output_dir: Union[str, Path]):
        self.project_root = Path(project_root) if isinstance(project_root, str) else project_root
        self.output_dir = Path(output_dir) if isinstance(output_dir, str) else output_dir
        self.regex_file = self.project_root / "multi_coder_analysis" / "regex" / "hop_patterns.yml"
        self.prompts_dir = self.project_root / "multi_coder_analysis" / "prompts"
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Storage for parsed data
        self.regex_data: Dict[str, Any] = {}
        self.regex_annotations: Dict[str, List[str]] = {}
        self.prompt_metadata: Dict[str, Dict[str, Any]] = {}
        
    def generate_all_docs(self):
        """Generate all documentation."""
        print("📚 Generating comprehensive documentation...")
        
        # Parse data
        self._parse_regex_file()
        self._parse_prompt_files()
        
        # Generate documentation
        self._generate_coverage_matrix()
        self._generate_dependency_graph()
        self._generate_gap_analysis()
        self._generate_performance_insights()
        self._generate_index_page()
        
        print(f"✅ Documentation generated in: {self.output_dir}")
    
    def _parse_regex_file(self):
        """Parse regex file and extract data."""
        with open(self.regex_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        self.regex_data = yaml.safe_load(content)
        
        # Extract annotations from comments
        annotation_pattern = re.compile(r'#\s*\[([Q\d\.]+)\]')
        lines = content.split('\n')
        
        current_rule = None
        for line in lines:
            if line.strip().startswith('- name:'):
                rule_match = re.search(r'name:\s*(\S+)', line)
                if rule_match:
                    current_rule = rule_match.group(1)
                    self.regex_annotations[current_rule] = []
            
            if current_rule and '#' in line:
                annotations = annotation_pattern.findall(line)
                self.regex_annotations[current_rule].extend(annotations)
    
    def _parse_prompt_files(self):
        """Parse all prompt files."""
        for prompt_file in self.prompts_dir.glob("hop_Q*.txt"):
            try:
                _, meta = load_prompt_and_meta(prompt_file)
                if meta and 'meta_id' in meta:
                    self.prompt_metadata[meta['meta_id']] = meta
            except Exception as e:
                print(f"Warning: Error parsing {prompt_file.name}: {e}")
    
    def _generate_coverage_matrix(self):
        """Generate coverage matrix markdown table."""
        print("📊 Generating coverage matrix...")
        
        output_file = self.output_dir / "coverage_matrix.md"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Regex-Prompt Coverage Matrix\n\n")
            f.write(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
            
            f.write("## Complete Coverage Mapping\n\n")
            f.write("| Hop | Pattern Row | Description | Regex Rules | Mode | Frame |\n")
            f.write("|-----|-------------|-------------|-------------|------|-------|\n")
            
            # Sort by hop number
            sorted_hops = sorted(self.prompt_metadata.items(), 
                               key=lambda x: int(x[0][1:]) if x[0][1:].isdigit() else 999)
            
            for hop_id, meta in sorted_hops:
                row_map = meta.get('row_map', {})
                regex_map = meta.get('regex_map', {})
                
                for row_id in sorted(row_map.keys()):
                    description = row_map[row_id]
                    rules = regex_map.get(row_id, [])
                    
                    # Get rule details
                    rule_details = []
                    for rule_ref in rules:
                        rule_name = rule_ref.split('.', 1)[1] if '.' in rule_ref else rule_ref
                        hop_num = int(hop_id[1:]) if hop_id[1:].isdigit() else 0
                        
                        # Find rule in regex data
                        if hop_num in self.regex_data:
                            for rule_data in self.regex_data[hop_num]:
                                if rule_data.get('name') == rule_name:
                                    mode = rule_data.get('mode', 'live')
                                    frame = rule_data.get('frame', 'Neutral')
                                    rule_details.append(f"`{rule_name}` ({mode}, {frame})")
                                    break
                            else:
                                rule_details.append(f"`{rule_name}` (not found)")
                        else:
                            rule_details.append(f"`{rule_name}` (hop not found)")
                    
                    rules_str = "<br>".join(rule_details) if rule_details else "*LLM only*"
                    
                    f.write(f"| {hop_id} | {row_id} | {description} | {rules_str} | | |\n")
            
            # Summary statistics
            f.write("\n## Coverage Statistics\n\n")
            total_rows = sum(len(meta.get('row_map', {})) for meta in self.prompt_metadata.values())
            total_rules = len(self.regex_annotations)
            
            # Count LLM-only patterns
            llm_only_count = 0
            for meta in self.prompt_metadata.values():
                row_map = meta.get('row_map', {})
                regex_map = meta.get('regex_map', {})
                for row_id in row_map:
                    if not regex_map.get(row_id):
                        llm_only_count += 1
            
            f.write(f"- **Total Pattern Rows**: {total_rows}\n")
            f.write(f"- **Total Regex Rules**: {total_rules}\n")
            f.write(f"- **LLM-Only Patterns**: {llm_only_count}\n")
            f.write(f"- **Regex Coverage**: {((total_rows - llm_only_count) / total_rows * 100):.1f}%\n")
    
    def _generate_dependency_graph(self):
        """Generate Mermaid dependency graph."""
        print("🕸️  Generating dependency graph...")
        
        output_file = self.output_dir / "dependency_graph.md"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# System Dependency Graph\n\n")
            f.write(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
            
            f.write("## Hop-to-Pattern Relationships\n\n")
            f.write("```mermaid\n")
            f.write("graph TD\n")
            
            # Generate hop nodes
            for hop_id, meta in sorted(self.prompt_metadata.items()):
                hop_num = hop_id[1:] if hop_id.startswith('Q') else hop_id
                frame = meta.get('frame', 'Neutral')
                summary = meta.get('summary', 'Unknown')
                
                # Color by frame
                color = {
                    'Alarmist': '#ff6b6b',
                    'Reassuring': '#51cf66', 
                    'Neutral': '#74c0fc',
                    'Variable': '#ffd43b'
                }.get(frame, '#74c0fc')
                
                f.write(f'  {hop_id}["{hop_id}<br/>{summary}"]:::frame{frame}\n')
            
            # Generate pattern relationships
            for hop_id, meta in sorted(self.prompt_metadata.items()):
                row_map = meta.get('row_map', {})
                regex_map = meta.get('regex_map', {})
                
                for row_id, description in row_map.items():
                    # Truncate long descriptions
                    short_desc = description[:30] + "..." if len(description) > 30 else description
                    f.write(f'  {row_id}["{row_id}<br/>{short_desc}"]:::pattern\n')
                    f.write(f'  {hop_id} --> {row_id}\n')
                    
                    # Connect to regex rules
                    rules = regex_map.get(row_id, [])
                    for rule_ref in rules:
                        rule_name = rule_ref.split('.', 1)[1] if '.' in rule_ref else rule_ref
                        f.write(f'  {rule_name}["{rule_name}"]:::regex\n')
                        f.write(f'  {row_id} --> {rule_name}\n')
            
            # Add styling
            f.write('\n  classDef frameAlarmist fill:#ff6b6b,stroke:#c92a2a,color:#fff\n')
            f.write('  classDef frameReassuring fill:#51cf66,stroke:#37b24d,color:#fff\n')
            f.write('  classDef frameNeutral fill:#74c0fc,stroke:#339af0,color:#fff\n')
            f.write('  classDef frameVariable fill:#ffd43b,stroke:#fab005,color:#000\n')
            f.write('  classDef pattern fill:#e9ecef,stroke:#adb5bd\n')
            f.write('  classDef regex fill:#f8f9fa,stroke:#dee2e6\n')
            
            f.write("```\n\n")
            
            # Add legend
            f.write("## Legend\n\n")
            f.write("- **Rectangles**: Hop questions (colored by expected frame)\n")
            f.write("- **Rounded rectangles**: Pattern rows within each hop\n")
            f.write("- **Plain rectangles**: Regex rules that implement patterns\n")
    
    def _generate_gap_analysis(self):
        """Generate gap analysis report."""
        print("🔍 Generating gap analysis...")
        
        output_file = self.output_dir / "gap_analysis.md"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Gap Analysis Report\n\n")
            f.write(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
            
            # LLM-only patterns
            f.write("## Patterns with No Regex Coverage (LLM-Only)\n\n")
            llm_only_patterns = []
            
            for hop_id, meta in sorted(self.prompt_metadata.items()):
                row_map = meta.get('row_map', {})
                regex_map = meta.get('regex_map', {})
                
                for row_id, description in row_map.items():
                    if not regex_map.get(row_id):
                        llm_only_patterns.append((hop_id, row_id, description))
            
            if llm_only_patterns:
                f.write("| Hop | Pattern | Description | Priority |\n")
                f.write("|-----|---------|-------------|----------|\n")
                
                for hop_id, row_id, description in llm_only_patterns:
                    # Estimate priority based on hop number (earlier = higher priority)
                    hop_num = int(hop_id[1:]) if hop_id[1:].isdigit() else 999
                    priority = "High" if hop_num <= 3 else "Medium" if hop_num <= 7 else "Low"
                    f.write(f"| {hop_id} | {row_id} | {description} | {priority} |\n")
                
                f.write(f"\n**Total LLM-only patterns**: {len(llm_only_patterns)}\n\n")
            else:
                f.write("✅ All patterns have regex coverage!\n\n")
            
            # Over-engineered patterns (multiple regex rules for one pattern)
            f.write("## Over-Engineered Patterns (Multiple Regex Rules)\n\n")
            over_engineered = []
            
            for hop_id, meta in sorted(self.prompt_metadata.items()):
                regex_map = meta.get('regex_map', {})
                row_map = meta.get('row_map', {})
                
                for row_id, rules in regex_map.items():
                    if len(rules) > 1:
                        description = row_map.get(row_id, "Unknown")
                        over_engineered.append((hop_id, row_id, description, len(rules)))
            
            if over_engineered:
                f.write("| Hop | Pattern | Description | Rule Count |\n")
                f.write("|-----|---------|-------------|------------|\n")
                
                for hop_id, row_id, description, count in sorted(over_engineered, key=lambda x: x[3], reverse=True):
                    f.write(f"| {hop_id} | {row_id} | {description} | {count} |\n")
                
                f.write(f"\n*Note: Multiple rules per pattern may indicate complexity or redundancy.*\n\n")
            else:
                f.write("All patterns have single regex rule coverage.\n\n")
            
            # Recommendations
            f.write("## Recommendations\n\n")
            f.write("### High Priority\n")
            f.write("- Add regex rules for LLM-only patterns in hops Q1-Q3 (highest precedence)\n")
            f.write("- Review over-engineered patterns for potential consolidation\n\n")
            
            f.write("### Medium Priority\n")
            f.write("- Consider regex coverage for remaining LLM-only patterns\n")
            f.write("- Validate that multi-rule patterns don't have overlapping logic\n\n")
            
            f.write("### Low Priority\n")
            f.write("- Add performance benchmarks for complex regex rules\n")
            f.write("- Consider splitting complex patterns into sub-patterns\n")
    
    def _generate_performance_insights(self):
        """Generate performance and optimization insights."""
        print("⚡ Generating performance insights...")
        
        output_file = self.output_dir / "performance_insights.md"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Performance Insights\n\n")
            f.write(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
            
            # Rule complexity analysis
            f.write("## Regex Rule Complexity Analysis\n\n")
            
            rule_stats = []
            for hop_num, rules in self.regex_data.items():
                if isinstance(rules, list):
                    for rule in rules:
                        name = rule.get('name', 'Unknown')
                        pattern = rule.get('pattern', '')
                        veto_pattern = rule.get('veto_pattern', '')
                        
                        # Calculate complexity metrics
                        pattern_length = len(pattern)
                        veto_length = len(veto_pattern)
                        total_length = pattern_length + veto_length
                        
                        # Count regex complexity indicators
                        complexity_score = 0
                        complexity_score += pattern.count('(?:') * 2  # Non-capturing groups
                        complexity_score += pattern.count('(?=') * 3  # Lookaheads
                        complexity_score += pattern.count('(?!') * 3  # Negative lookaheads
                        complexity_score += pattern.count('(?<=') * 4  # Lookbehinds
                        complexity_score += pattern.count('(?<!') * 4  # Negative lookbehinds
                        complexity_score += pattern.count('|') * 1  # Alternations
                        complexity_score += pattern.count('{') * 1  # Quantifiers
                        
                        rule_stats.append({
                            'hop': f"Q{hop_num}",
                            'name': name,
                            'pattern_length': pattern_length,
                            'veto_length': veto_length,
                            'total_length': total_length,
                            'complexity_score': complexity_score,
                            'has_veto': bool(veto_pattern.strip())
                        })
            
            # Sort by complexity
            rule_stats.sort(key=lambda x: x['complexity_score'], reverse=True)
            
            f.write("### Most Complex Rules (Top 10)\n\n")
            f.write("| Hop | Rule Name | Pattern Length | Complexity Score | Has Veto |\n")
            f.write("|-----|-----------|----------------|------------------|----------|\n")
            
            for rule in rule_stats[:10]:
                veto_mark = "✓" if rule['has_veto'] else "—"
                f.write(f"| {rule['hop']} | `{rule['name']}` | {rule['pattern_length']} | {rule['complexity_score']} | {veto_mark} |\n")
            
            # Coverage distribution
            f.write("\n## Coverage Distribution by Hop\n\n")
            
            hop_coverage = {}
            for hop_id, meta in self.prompt_metadata.items():
                row_map = meta.get('row_map', {})
                regex_map = meta.get('regex_map', {})
                
                total_patterns = len(row_map)
                covered_patterns = len([r for r in regex_map.values() if r])
                coverage_pct = (covered_patterns / total_patterns * 100) if total_patterns > 0 else 0
                
                hop_coverage[hop_id] = {
                    'total': total_patterns,
                    'covered': covered_patterns,
                    'percentage': coverage_pct
                }
            
            f.write("| Hop | Total Patterns | Regex Covered | Coverage % | Status |\n")
            f.write("|-----|----------------|---------------|------------|--------|\n")
            
            for hop_id in sorted(hop_coverage.keys(), key=lambda x: int(x[1:]) if x[1:].isdigit() else 999):
                stats = hop_coverage[hop_id]
                status = "🟢" if stats['percentage'] == 100 else "🟡" if stats['percentage'] >= 50 else "🔴"
                f.write(f"| {hop_id} | {stats['total']} | {stats['covered']} | {stats['percentage']:.1f}% | {status} |\n")
            
            # Optimization recommendations
            f.write("\n## Optimization Recommendations\n\n")
            
            # Find high-complexity rules
            high_complexity = [r for r in rule_stats if r['complexity_score'] > 20]
            if high_complexity:
                f.write("### High Complexity Rules\n")
                f.write("Consider optimizing these rules for better performance:\n\n")
                for rule in high_complexity[:5]:
                    f.write(f"- **{rule['name']}** (Hop {rule['hop']}): Complexity score {rule['complexity_score']}\n")
                f.write("\n")
            
            # Find rules with long patterns
            long_patterns = [r for r in rule_stats if r['total_length'] > 1000]
            if long_patterns:
                f.write("### Long Pattern Rules\n")
                f.write("Consider breaking these into smaller, more focused rules:\n\n")
                for rule in long_patterns[:5]:
                    f.write(f"- **{rule['name']}** (Hop {rule['hop']}): {rule['total_length']} characters\n")
                f.write("\n")
            
            f.write("### General Recommendations\n\n")
            f.write("1. **Profile regex performance** in production to identify bottlenecks\n")
            f.write("2. **Consider caching** compiled regex patterns for frequently used rules\n")
            f.write("3. **Monitor false positive rates** for complex rules with high complexity scores\n")
            f.write("4. **Implement timeout handling** for regex evaluation to prevent ReDoS attacks\n")
    
    def _generate_index_page(self):
        """Generate main index page linking to all reports."""
        print("📋 Generating index page...")
        
        output_file = self.output_dir / "README.md"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Annotation System Documentation\n\n")
            f.write(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
            
            f.write("This directory contains comprehensive documentation for the regex-prompt annotation system.\n\n")
            
            f.write("## 📊 Reports\n\n")
            f.write("- **[Coverage Matrix](coverage_matrix.md)**: Complete mapping between regex rules and prompt patterns\n")
            f.write("- **[Dependency Graph](dependency_graph.md)**: Visual representation of system relationships\n")
            f.write("- **[Gap Analysis](gap_analysis.md)**: Identifies patterns without regex coverage and optimization opportunities\n")
            f.write("- **[Performance Insights](performance_insights.md)**: Complexity analysis and optimization recommendations\n\n")
            
            # Quick stats
            total_hops = len(self.prompt_metadata)
            total_rules = len(self.regex_annotations)
            total_patterns = sum(len(meta.get('row_map', {})) for meta in self.prompt_metadata.values())
            
            f.write("## 📈 Quick Statistics\n\n")
            f.write(f"- **Hops**: {total_hops}\n")
            f.write(f"- **Regex Rules**: {total_rules}\n")
            f.write(f"- **Pattern Rows**: {total_patterns}\n")
            f.write(f"- **Average Patterns per Hop**: {total_patterns / total_hops:.1f}\n\n")
            
            f.write("## 🔧 Maintenance\n\n")
            f.write("To regenerate this documentation:\n\n")
            f.write("```bash\n")
            f.write("python scripts/generate_coverage_report.py\n")
            f.write("```\n\n")
            
            f.write("To validate annotation consistency:\n\n")
            f.write("```bash\n")
            f.write("python scripts/validate_annotations.py --ci\n")
            f.write("```\n")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate annotation documentation")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(),
                       help="Project root directory")
    parser.add_argument("--output-dir", type=Path, default=Path.cwd() / "docs" / "annotations",
                       help="Output directory for documentation")
    
    args = parser.parse_args()
    
    generator = DocumentationGenerator(args.project_root, args.output_dir)
    generator.generate_all_docs()


if __name__ == "__main__":
    main() 