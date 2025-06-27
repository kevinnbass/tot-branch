#!/usr/bin/env python3
"""
Advanced Annotation Analytics

Provides sophisticated analytics for the annotation system:
- Coverage metrics and trends
- Performance profiling
- Evolution tracking via git history
- Precision/recall analysis
- Maintenance automation
"""

import re
import sys
import yaml
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional, Union
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import subprocess
import tempfile
import statistics

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from multi_coder_analysis.utils.prompt_loader import load_prompt_and_meta

class AnnotationAnalytics:
    def __init__(self, project_root: Union[str, Path], db_path: Optional[Union[str, Path]] = None):
        self.project_root = Path(project_root) if isinstance(project_root, str) else project_root
        self.regex_file = self.project_root / "multi_coder_analysis" / "regex" / "hop_patterns.yml"
        self.prompts_dir = self.project_root / "multi_coder_analysis" / "prompts"
        
        # Initialize database for tracking metrics over time
        if db_path:
            self.db_path = Path(db_path) if isinstance(db_path, str) else db_path
        else:
            self.db_path = self.project_root / "docs" / "annotations" / "analytics.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        
        # Cache for parsed data
        self.regex_data = {}
        self.prompt_metadata = {}
        
    def run_full_analysis(self) -> Dict[str, Any]:
        """Run complete analytics suite."""
        print("📊 Running comprehensive annotation analytics...")
        
        # Load current data
        self._load_current_data()
        
        # Run all analyses
        results = {
            'timestamp': datetime.now().isoformat(),
            'coverage_metrics': self._analyze_coverage_metrics(),
            'performance_profile': self._analyze_performance_profile(),
            'evolution_tracking': self._analyze_evolution_tracking(),
            'precision_analysis': self._analyze_precision_patterns(),
            'maintenance_insights': self._analyze_maintenance_needs(),
            'trend_analysis': self._analyze_trends()
        }
        
        # Store results in database
        self._store_metrics(results)
        
        return results
    
    def _init_database(self):
        """Initialize SQLite database for metrics tracking."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS metrics_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    metric_type TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    value REAL NOT NULL,
                    metadata TEXT
                );
                
                CREATE TABLE IF NOT EXISTS coverage_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    hop_id TEXT NOT NULL,
                    total_patterns INTEGER NOT NULL,
                    covered_patterns INTEGER NOT NULL,
                    coverage_percentage REAL NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS rule_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    rule_name TEXT NOT NULL,
                    complexity_score INTEGER NOT NULL,
                    pattern_length INTEGER NOT NULL,
                    execution_time_ms REAL,
                    false_positive_rate REAL,
                    false_negative_rate REAL
                );
                
                CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics_history(timestamp);
                CREATE INDEX IF NOT EXISTS idx_coverage_timestamp ON coverage_snapshots(timestamp);
                CREATE INDEX IF NOT EXISTS idx_performance_timestamp ON rule_performance(timestamp);
            """)
    
    def _load_current_data(self):
        """Load current regex and prompt data."""
        # Load regex data
        with open(self.regex_file, 'r', encoding='utf-8') as f:
            self.regex_data = yaml.safe_load(f)
        
        # Load prompt metadata
        for prompt_file in self.prompts_dir.glob("hop_Q*.txt"):
            try:
                _, meta = load_prompt_and_meta(prompt_file)
                if meta and 'meta_id' in meta:
                    self.prompt_metadata[meta['meta_id']] = meta
            except Exception as e:
                print(f"Warning: Error loading {prompt_file.name}: {e}")
    
    def _analyze_coverage_metrics(self) -> Dict[str, Any]:
        """Analyze current coverage metrics."""
        metrics = {
            'overall': {},
            'by_hop': {},
            'by_frame': {},
            'trends': {}
        }
        
        # Overall coverage
        total_patterns = sum(len(meta.get('row_map', {})) for meta in self.prompt_metadata.values())
        total_rules = sum(len(rules) if isinstance(rules, list) else 0 
                         for rules in self.regex_data.values())
        
        # Count covered patterns
        covered_patterns = 0
        llm_only_patterns = 0
        
        for meta in self.prompt_metadata.values():
            row_map = meta.get('row_map', {})
            regex_map = meta.get('regex_map', {})
            
            for row_id in row_map:
                if regex_map.get(row_id):
                    covered_patterns += 1
                else:
                    llm_only_patterns += 1
        
        metrics['overall'] = {
            'total_patterns': total_patterns,
            'total_rules': total_rules,
            'covered_patterns': covered_patterns,
            'llm_only_patterns': llm_only_patterns,
            'coverage_percentage': (covered_patterns / total_patterns * 100) if total_patterns > 0 else 0,
            'rules_per_pattern': total_rules / total_patterns if total_patterns > 0 else 0
        }
        
        # Coverage by hop
        for hop_id, meta in self.prompt_metadata.items():
            row_map = meta.get('row_map', {})
            regex_map = meta.get('regex_map', {})
            
            hop_total = len(row_map)
            hop_covered = len([r for r in regex_map.values() if r])
            
            metrics['by_hop'][hop_id] = {
                'total_patterns': hop_total,
                'covered_patterns': hop_covered,
                'coverage_percentage': (hop_covered / hop_total * 100) if hop_total > 0 else 0,
                'frame': meta.get('frame', 'Unknown')
            }
        
        # Coverage by frame type
        frame_stats = defaultdict(lambda: {'total': 0, 'covered': 0})
        
        for hop_id, hop_metrics in metrics['by_hop'].items():
            frame = hop_metrics['frame']
            frame_stats[frame]['total'] += hop_metrics['total_patterns']
            frame_stats[frame]['covered'] += hop_metrics['covered_patterns']
        
        for frame, stats in frame_stats.items():
            metrics['by_frame'][frame] = {
                'total_patterns': stats['total'],
                'covered_patterns': stats['covered'],
                'coverage_percentage': (stats['covered'] / stats['total'] * 100) if stats['total'] > 0 else 0
            }
        
        return metrics
    
    def _analyze_performance_profile(self) -> Dict[str, Any]:
        """Analyze performance characteristics of regex rules."""
        profile = {
            'complexity_distribution': {},
            'high_complexity_rules': [],
            'performance_bottlenecks': [],
            'optimization_candidates': []
        }
        
        rule_complexities = []
        
        for hop_num, rules in self.regex_data.items():
            if not isinstance(rules, list):
                continue
                
            for rule in rules:
                name = rule.get('name', 'Unknown')
                pattern = rule.get('pattern', '')
                veto_pattern = rule.get('veto_pattern', '')
                mode = rule.get('mode', 'live')
                
                if mode == 'shadow':
                    continue
                
                # Calculate complexity metrics
                complexity_score = self._calculate_complexity_score(pattern, veto_pattern)
                pattern_length = len(pattern) + len(veto_pattern)
                
                rule_complexities.append(complexity_score)
                
                rule_info = {
                    'hop': f"Q{hop_num}",
                    'name': name,
                    'complexity_score': complexity_score,
                    'pattern_length': pattern_length,
                    'has_veto': bool(veto_pattern.strip()),
                    'estimated_performance': self._estimate_performance(pattern, veto_pattern)
                }
                
                # Flag high complexity rules
                if complexity_score > 25:
                    profile['high_complexity_rules'].append(rule_info)
                
                # Flag potential bottlenecks
                if pattern_length > 1000 or complexity_score > 30:
                    profile['performance_bottlenecks'].append(rule_info)
                
                # Suggest optimization candidates
                if self._needs_optimization(pattern, veto_pattern):
                    profile['optimization_candidates'].append({
                        **rule_info,
                        'optimization_suggestions': self._suggest_optimizations(pattern, veto_pattern)
                    })
        
        # Complexity distribution
        if rule_complexities:
            profile['complexity_distribution'] = {
                'mean': statistics.mean(rule_complexities),
                'median': statistics.median(rule_complexities),
                'std_dev': statistics.stdev(rule_complexities) if len(rule_complexities) > 1 else 0,
                'min': min(rule_complexities),
                'max': max(rule_complexities),
                'percentiles': {
                    '25th': statistics.quantiles(rule_complexities, n=4)[0],
                    '75th': statistics.quantiles(rule_complexities, n=4)[2],
                    '90th': statistics.quantiles(rule_complexities, n=10)[8]
                }
            }
        
        return profile
    
    def _analyze_evolution_tracking(self) -> Dict[str, Any]:
        """Track evolution of annotations through git history."""
        evolution = {
            'recent_changes': [],
            'growth_metrics': {},
            'stability_analysis': {},
            'contributor_stats': {}
        }
        
        try:
            # Get recent commits affecting annotation files
            cmd = [
                'git', 'log', '--oneline', '--since=30 days ago',
                '--', str(self.regex_file.relative_to(self.project_root)),
                str(self.prompts_dir.relative_to(self.project_root))
            ]
            
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
            
            if result.returncode == 0:
                commits = result.stdout.strip().split('\n')
                evolution['recent_changes'] = [
                    {'commit': line.split(' ', 1)[0], 'message': line.split(' ', 1)[1]}
                    for line in commits if line.strip()
                ]
            
            # Analyze growth over time
            evolution['growth_metrics'] = self._analyze_growth_metrics()
            
            # Stability analysis
            evolution['stability_analysis'] = self._analyze_stability()
            
        except Exception as e:
            evolution['error'] = f"Git analysis failed: {e}"
        
        return evolution
    
    def _analyze_precision_patterns(self) -> Dict[str, Any]:
        """Analyze patterns for precision and recall characteristics."""
        analysis = {
            'high_precision_patterns': [],
            'broad_patterns': [],
            'specificity_scores': {},
            'overlap_analysis': {}
        }
        
        # Analyze each pattern for specificity
        for hop_num, rules in self.regex_data.items():
            if not isinstance(rules, list):
                continue
                
            for rule in rules:
                name = rule.get('name', 'Unknown')
                pattern = rule.get('pattern', '')
                
                if not pattern:
                    continue
                
                specificity = self._calculate_specificity_score(pattern)
                analysis['specificity_scores'][name] = specificity
                
                if specificity > 0.8:
                    analysis['high_precision_patterns'].append({
                        'rule': name,
                        'hop': f"Q{hop_num}",
                        'specificity': specificity
                    })
                elif specificity < 0.3:
                    analysis['broad_patterns'].append({
                        'rule': name,
                        'hop': f"Q{hop_num}",
                        'specificity': specificity,
                        'recommendation': 'Consider adding more specific constraints'
                    })
        
        # Analyze potential overlaps
        analysis['overlap_analysis'] = self._analyze_pattern_overlaps()
        
        return analysis
    
    def _analyze_maintenance_needs(self) -> Dict[str, Any]:
        """Analyze maintenance needs and automation opportunities."""
        maintenance = {
            'dead_code': [],
            'inconsistencies': [],
            'automation_opportunities': [],
            'technical_debt': []
        }
        
        # Find potentially dead regex rules
        referenced_rules = set()
        for meta in self.prompt_metadata.values():
            regex_map = meta.get('regex_map', {})
            for rule_list in regex_map.values():
                for rule_ref in rule_list:
                    rule_name = rule_ref.split('.', 1)[1] if '.' in rule_ref else rule_ref
                    referenced_rules.add(rule_name)
        
        all_rules = set()
        for rules in self.regex_data.values():
            if isinstance(rules, list):
                for rule in rules:
                    all_rules.add(rule.get('name', ''))
        
        dead_rules = all_rules - referenced_rules
        maintenance['dead_code'] = list(dead_rules)
        
        # Find naming inconsistencies
        maintenance['inconsistencies'] = self._find_naming_inconsistencies()
        
        # Suggest automation opportunities
        maintenance['automation_opportunities'] = [
            {
                'type': 'pattern_generation',
                'description': 'Generate regex patterns from LLM-only annotations',
                'priority': 'medium'
            },
            {
                'type': 'performance_monitoring',
                'description': 'Add runtime performance tracking for regex rules',
                'priority': 'high'
            },
            {
                'type': 'coverage_alerts',
                'description': 'Alert when coverage drops below threshold',
                'priority': 'low'
            }
        ]
        
        # Technical debt analysis
        maintenance['technical_debt'] = self._analyze_technical_debt()
        
        return maintenance
    
    def _analyze_trends(self) -> Dict[str, Any]:
        """Analyze trends from historical data."""
        trends = {
            'coverage_trend': [],
            'complexity_trend': [],
            'activity_trend': []
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Coverage trends
                cursor = conn.execute("""
                    SELECT timestamp, AVG(coverage_percentage) as avg_coverage
                    FROM coverage_snapshots 
                    WHERE timestamp >= datetime('now', '-30 days')
                    GROUP BY date(timestamp)
                    ORDER BY timestamp
                """)
                
                trends['coverage_trend'] = [
                    {'date': row[0], 'coverage': row[1]}
                    for row in cursor.fetchall()
                ]
                
                # Complexity trends
                cursor = conn.execute("""
                    SELECT timestamp, AVG(complexity_score) as avg_complexity
                    FROM rule_performance 
                    WHERE timestamp >= datetime('now', '-30 days')
                    GROUP BY date(timestamp)
                    ORDER BY timestamp
                """)
                
                trends['complexity_trend'] = [
                    {'date': row[0], 'complexity': row[1]}
                    for row in cursor.fetchall()
                ]
        
        except sqlite3.Error as e:
            trends['error'] = f"Database analysis failed: {e}"
        
        return trends
    
    def _calculate_complexity_score(self, pattern: str, veto_pattern: str = "") -> int:
        """Calculate complexity score for a regex pattern."""
        total_pattern = pattern + veto_pattern
        score = 0
        
        # Basic complexity indicators
        score += total_pattern.count('(?:') * 2  # Non-capturing groups
        score += total_pattern.count('(?=') * 3  # Lookaheads
        score += total_pattern.count('(?!') * 3  # Negative lookaheads
        score += total_pattern.count('(?<=') * 4  # Lookbehinds
        score += total_pattern.count('(?<!') * 4  # Negative lookbehinds
        score += total_pattern.count('|') * 1  # Alternations
        score += total_pattern.count('{') * 1  # Quantifiers
        score += total_pattern.count('[') * 1  # Character classes
        score += total_pattern.count('\\') * 0.5  # Escape sequences
        
        # Nesting complexity
        max_nesting = 0
        current_nesting = 0
        for char in total_pattern:
            if char == '(':
                current_nesting += 1
                max_nesting = max(max_nesting, current_nesting)
            elif char == ')':
                current_nesting -= 1
        
        score += max_nesting * 2
        
        return int(score)
    
    def _estimate_performance(self, pattern: str, veto_pattern: str = "") -> str:
        """Estimate performance characteristics of a pattern."""
        total_length = len(pattern) + len(veto_pattern)
        complexity = self._calculate_complexity_score(pattern, veto_pattern)
        
        # Check for potentially expensive constructs
        expensive_constructs = [
            r'\.\*', r'\.\+',  # Greedy quantifiers
            r'\(\?\=', r'\(\?\!',  # Lookarounds
            r'\(\?\<\=', r'\(\?\<\!',  # Lookbehinds
        ]
        
        has_expensive = any(re.search(construct, pattern + veto_pattern) 
                           for construct in expensive_constructs)
        
        if complexity > 30 or total_length > 1000 or has_expensive:
            return "slow"
        elif complexity > 15 or total_length > 500:
            return "moderate"
        else:
            return "fast"
    
    def _needs_optimization(self, pattern: str, veto_pattern: str = "") -> bool:
        """Determine if a pattern needs optimization."""
        return (self._calculate_complexity_score(pattern, veto_pattern) > 25 or
                len(pattern + veto_pattern) > 800 or
                self._estimate_performance(pattern, veto_pattern) == "slow")
    
    def _suggest_optimizations(self, pattern: str, veto_pattern: str = "") -> List[str]:
        """Suggest optimizations for a pattern."""
        suggestions = []
        
        total_pattern = pattern + veto_pattern
        
        if '.*' in total_pattern:
            suggestions.append("Consider replacing .* with more specific patterns")
        
        if total_pattern.count('|') > 10:
            suggestions.append("Consider breaking into multiple rules")
        
        if len(total_pattern) > 1000:
            suggestions.append("Pattern is very long, consider modularization")
        
        if '(?=' in total_pattern and '(?!' in total_pattern:
            suggestions.append("Multiple lookarounds may impact performance")
        
        return suggestions
    
    def _calculate_specificity_score(self, pattern: str) -> float:
        """Calculate how specific a pattern is (0=very broad, 1=very specific)."""
        score = 0.5  # Base score
        
        # Specific word boundaries increase specificity
        score += pattern.count(r'\b') * 0.05
        
        # Literal strings increase specificity
        literal_chars = len(re.sub(r'[\\()\[\]{}.*+?|^$]', '', pattern))
        score += min(literal_chars * 0.01, 0.3)
        
        # Character classes decrease specificity
        score -= pattern.count('[') * 0.1
        
        # Wildcards decrease specificity
        score -= pattern.count('.*') * 0.2
        score -= pattern.count('.+') * 0.15
        
        # Length constraints increase specificity
        if '{' in pattern:
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _analyze_pattern_overlaps(self) -> Dict[str, Any]:
        """Analyze potential overlaps between patterns."""
        # This is a simplified analysis - full overlap detection would require
        # complex regex intersection algorithms
        overlaps = {
            'potential_overlaps': [],
            'similar_patterns': []
        }
        
        patterns = []
        for hop_num, rules in self.regex_data.items():
            if isinstance(rules, list):
                for rule in rules:
                    patterns.append({
                        'hop': f"Q{hop_num}",
                        'name': rule.get('name', ''),
                        'pattern': rule.get('pattern', '')
                    })
        
        # Simple similarity check based on common substrings
        for i, p1 in enumerate(patterns):
            for p2 in patterns[i+1:]:
                if p1['hop'] != p2['hop']:  # Only check across different hops
                    similarity = self._calculate_pattern_similarity(p1['pattern'], p2['pattern'])
                    if similarity > 0.7:
                        overlaps['similar_patterns'].append({
                            'pattern1': f"{p1['hop']}.{p1['name']}",
                            'pattern2': f"{p2['hop']}.{p2['name']}",
                            'similarity': similarity
                        })
        
        return overlaps
    
    def _calculate_pattern_similarity(self, pattern1: str, pattern2: str) -> float:
        """Calculate similarity between two patterns."""
        # Simple Jaccard similarity on character bigrams
        def get_bigrams(s):
            return set(s[i:i+2] for i in range(len(s)-1))
        
        bigrams1 = get_bigrams(pattern1.lower())
        bigrams2 = get_bigrams(pattern2.lower())
        
        if not bigrams1 and not bigrams2:
            return 1.0
        if not bigrams1 or not bigrams2:
            return 0.0
        
        intersection = len(bigrams1 & bigrams2)
        union = len(bigrams1 | bigrams2)
        
        return intersection / union if union > 0 else 0.0
    
    def _find_naming_inconsistencies(self) -> List[Dict[str, Any]]:
        """Find naming inconsistencies in rules and annotations."""
        inconsistencies = []
        
        # Check for inconsistent naming patterns
        rule_names = []
        for rules in self.regex_data.values():
            if isinstance(rules, list):
                for rule in rules:
                    rule_names.append(rule.get('name', ''))
        
        # Check naming conventions
        camel_case_pattern = re.compile(r'^[A-Z][a-zA-Z0-9]*$')
        snake_case_pattern = re.compile(r'^[a-z][a-z0-9_]*$')
        
        camel_case_count = sum(1 for name in rule_names if camel_case_pattern.match(name))
        snake_case_count = sum(1 for name in rule_names if snake_case_pattern.match(name))
        
        if camel_case_count > 0 and snake_case_count > 0:
            inconsistencies.append({
                'type': 'naming_convention',
                'description': f'Mixed naming conventions: {camel_case_count} CamelCase, {snake_case_count} snake_case',
                'severity': 'medium'
            })
        
        return inconsistencies
    
    def _analyze_growth_metrics(self) -> Dict[str, Any]:
        """Analyze growth metrics from git history."""
        metrics = {
            'total_commits': 0,
            'files_added': 0,
            'lines_added': 0,
            'lines_removed': 0
        }
        
        try:
            # Get commit statistics
            cmd = [
                'git', 'log', '--oneline', '--numstat',
                '--', str(self.regex_file.relative_to(self.project_root)),
                str(self.prompts_dir.relative_to(self.project_root))
            ]
            
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                metrics['total_commits'] = len([l for l in lines if re.match(r'^[a-f0-9]+', l)])
                
                for line in lines:
                    if '\t' in line:  # numstat line
                        parts = line.split('\t')
                        if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
                            metrics['lines_added'] += int(parts[0])
                            metrics['lines_removed'] += int(parts[1])
        
        except Exception as e:
            metrics['error'] = f"Git analysis failed: {e}"
        
        return metrics
    
    def _analyze_stability(self) -> Dict[str, Any]:
        """Analyze stability of the annotation system."""
        stability = {
            'change_frequency': {},
            'volatility_score': 0.0,
            'stable_components': [],
            'volatile_components': []
        }
        
        try:
            # Analyze change frequency per file
            for file_pattern in [self.regex_file, self.prompts_dir / "*.txt"]:
                cmd = ['git', 'log', '--oneline', '--since=90 days ago', '--', str(file_pattern)]
                result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
                
                if result.returncode == 0:
                    commit_count = len([l for l in result.stdout.strip().split('\n') if l.strip()])
                    stability['change_frequency'][str(file_pattern)] = commit_count
        
        except Exception as e:
            stability['error'] = f"Stability analysis failed: {e}"
        
        return stability
    
    def _analyze_technical_debt(self) -> List[Dict[str, Any]]:
        """Analyze technical debt in the annotation system."""
        debt_items = []
        
        # Check for TODO/FIXME comments
        try:
            with open(self.regex_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            todo_pattern = re.compile(r'#.*?(TODO|FIXME|XXX|HACK).*', re.IGNORECASE)
            todos = todo_pattern.findall(content)
            
            if todos:
                debt_items.append({
                    'type': 'todo_comments',
                    'count': len(todos),
                    'description': f'{len(todos)} TODO/FIXME comments in regex file',
                    'priority': 'medium'
                })
        
        except Exception:
            pass
        
        # Check for deprecated patterns
        shadow_rules = []
        for hop_num, rules in self.regex_data.items():
            if isinstance(rules, list):
                for rule in rules:
                    if rule.get('mode') == 'shadow':
                        shadow_rules.append(f"{hop_num}.{rule.get('name', 'Unknown')}")
        
        if shadow_rules:
            debt_items.append({
                'type': 'deprecated_rules',
                'count': len(shadow_rules),
                'description': f'{len(shadow_rules)} shadow/deprecated rules',
                'priority': 'low',
                'items': shadow_rules
            })
        
        return debt_items
    
    def _store_metrics(self, results: Dict[str, Any]):
        """Store analysis results in database for trend tracking."""
        timestamp = datetime.now().isoformat()
        
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            # Store coverage metrics
            coverage_metrics = results.get('coverage_metrics', {})
            for hop_id, metrics in coverage_metrics.get('by_hop', {}).items():
                conn.execute("""
                    INSERT INTO coverage_snapshots 
                    (timestamp, hop_id, total_patterns, covered_patterns, coverage_percentage)
                    VALUES (?, ?, ?, ?, ?)
                """, (timestamp, hop_id, metrics['total_patterns'], 
                      metrics['covered_patterns'], metrics['coverage_percentage']))
            
            # Store performance metrics
            performance = results.get('performance_profile', {})
            complexity_dist = performance.get('complexity_distribution', {})
            if complexity_dist:
                conn.execute("""
                    INSERT INTO metrics_history 
                    (timestamp, metric_type, metric_name, value, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """, (timestamp, 'complexity', 'mean', complexity_dist.get('mean', 0), 
                      json.dumps(complexity_dist)))
            
            conn.commit()
            
        except sqlite3.Error as e:
            print(f"Warning: Could not store metrics in database: {e}")
        finally:
            # Ensure database connection is properly closed
            if conn:
                try:
                    conn.close()
                except:
                    pass


def main():
    """Main CLI interface."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Advanced annotation analytics")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, help="Output file for results")
    parser.add_argument("--format", choices=['json', 'yaml'], default='json')
    
    args = parser.parse_args()
    
    analytics = AnnotationAnalytics(args.project_root)
    results = analytics.run_full_analysis()
    
    # Output results
    if args.format == 'yaml':
        output_text = yaml.dump(results, default_flow_style=False, indent=2)
    else:
        output_text = json.dumps(results, indent=2)
    
    if args.output:
        args.output.write_text(output_text, encoding='utf-8')
        print(f"Analytics results written to: {args.output}")
    else:
        print(output_text)


if __name__ == "__main__":
    main() 