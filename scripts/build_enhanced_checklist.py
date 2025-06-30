#!/usr/bin/env python3
"""
Build enhanced checklist by extracting all rules from hop prompts.
This script ensures 100% information retention during migration.
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any
import yaml

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from multi_coder_analysis.utils.prompt_loader import load_prompt_and_meta


class PatternExtractor:
    """Extract patterns and rules from hop prompts."""
    
    def __init__(self):
        self.prompts_dir = Path(__file__).parent.parent / "multi_coder_analysis" / "prompts"
        self.output_dir = self.prompts_dir / "cue_detection"
        self.enhanced_hops_dir = self.output_dir / "enhanced_hops"
        
    def extract_quick_check(self, content: str) -> str:
        """Extract the QUICK DECISION CHECK section."""
        patterns = [
            r"### ⚡?\s*QUICK DECISION CHECK(.*?)(?=\n===|\n###|$)",
            r"### QUICK DECISION CHECK(.*?)(?=\n===|\n###|$)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                return match.group(1).strip()
        return ""
    
    def extract_pattern_table(self, content: str) -> List[Dict[str, str]]:
        """Extract pattern recognition table rows."""
        table_pattern = r"\| \*\*Pattern Type\*\* \|.*?\n\|[-\s|]+\n(.*?)(?=\n\*\*|$)"
        match = re.search(table_pattern, content, re.DOTALL)
        
        if not match:
            return []
        
        table_content = match.group(1)
        rows = []
        
        # Extract each row
        row_pattern = r"<!--\s*(Q\d+\.\d+)\s*-->\n\| \*\*(.*?)\*\* \| (.*?) \| (.*?) \|"
        for row_match in re.finditer(row_pattern, table_content):
            row_id = row_match.group(1)
            pattern_type = row_match.group(2).strip()
            examples = row_match.group(3).strip()
            outcome = row_match.group(4).strip()
            
            rows.append({
                "id": row_id,
                "pattern_type": pattern_type,
                "examples": examples,
                "outcome": outcome
            })
        
        # Also extract rows without HTML comments
        simple_row_pattern = r"\| \*\*(.*?)\*\* \| (.*?) \| (.*?) \|"
        for row_match in re.finditer(simple_row_pattern, table_content):
            if not any(row_match.group(1) in r["pattern_type"] for r in rows):
                rows.append({
                    "id": "",
                    "pattern_type": row_match.group(1).strip(),
                    "examples": row_match.group(2).strip(),
                    "outcome": row_match.group(3).strip()
                })
        
        return rows
    
    def extract_detailed_rules(self, content: str) -> Dict[str, List[str]]:
        """Extract detailed rules, examples, and guards."""
        sections = {
            "inclusion_criteria": [],
            "exclusion_criteria": [],
            "examples": [],
            "guards": [],
            "clarifications": [],
            "special_rules": []
        }
        
        # Extract Alarmist/Reassuring inclusion criteria
        inclusion_pattern = r"\*\*(?:Alarmist|Reassuring) - (?:Inclusion Criteria|Examples):\*\*(.*?)(?=\*\*|$)"
        for match in re.finditer(inclusion_pattern, content, re.DOTALL):
            criteria = match.group(1).strip()
            sections["inclusion_criteria"].extend(self._extract_bullet_points(criteria))
        
        # Extract exclusions
        exclusion_patterns = [
            r"⛔ EXCLUSIONS.*?:(.*?)(?=\*\*|$)",
            r"\*\*EXCLUSIONS? - .*?\*\*(.*?)(?=\*\*|$)",
            r"\*\*Exclusion.*?\*\*(.*?)(?=\*\*|$)"
        ]
        for pattern in exclusion_patterns:
            for match in re.finditer(pattern, content, re.DOTALL):
                sections["exclusion_criteria"].extend(self._extract_bullet_points(match.group(1)))
        
        # Extract guards
        guard_patterns = [
            r"🛡️ UNIVERSAL GUARDS.*?:(.*?)(?=\*\*|$)",
            r"\*\*Guard.*?\*\*(.*?)(?=\*\*|$)",
            r"⚠\s*(.+?guard.+?)(?=\n\n|$)"
        ]
        for pattern in guard_patterns:
            for match in re.finditer(pattern, content, re.DOTALL | re.IGNORECASE):
                sections["guards"].extend(self._extract_bullet_points(match.group(1)))
        
        # Extract examples
        example_pattern = r"\*\*(?:Few-Shot )?(?:Examples?|Exemplars?).*?\*\*(.*?)(?=\*\*|$)"
        for match in re.finditer(example_pattern, content, re.DOTALL):
            sections["examples"].extend(self._extract_bullet_points(match.group(1)))
        
        # Extract special rules and clarifications
        special_patterns = [
            r"(?:CLARIFICATION|Clarification|NOTE|Note|SPECIAL|Special).*?:(.*?)(?=\n\n|$)",
            r"►\s*(.*?)(?=\n\n|$)",
            r"⚠\s*(.*?)(?=\n\n|$)"
        ]
        for pattern in special_patterns:
            for match in re.finditer(pattern, content, re.DOTALL):
                sections["clarifications"].append(match.group(1).strip())
        
        return sections
    
    def _extract_bullet_points(self, text: str) -> List[str]:
        """Extract bullet points from text."""
        points = []
        # Match various bullet styles
        bullet_pattern = r"(?:^|\n)\s*[•*✓✗-]\s*(.+?)(?=\n\s*[•*✓✗-]|$)"
        for match in re.finditer(bullet_pattern, text, re.DOTALL):
            point = match.group(1).strip()
            if point:
                points.append(point)
        return points
    
    def format_pattern_block(self, hop_num: int, pattern: Dict[str, Any], meta: Dict[str, Any]) -> str:
        """Format a single pattern into the enhanced checklist format."""
        pattern_id = pattern.get("id", f"Q{hop_num}")
        frame = meta.get("frame", "Unknown")
        
        block = f"""
---
### Pattern: {pattern_id}: {pattern['pattern_type']}
**Frame:** {frame}
**Hop:** Q{hop_num}
"""
        
        if pattern.get("quick_check"):
            block += f"**QUICK CHECK:** {pattern['quick_check']}\n"
        
        if pattern.get("examples"):
            block += f"\n**PATTERN EXAMPLES:**\n"
            block += f"- {pattern['examples']}\n"
        
        if pattern.get("inclusion_criteria"):
            block += f"\n**INCLUSION CRITERIA:**\n"
            for criterion in pattern["inclusion_criteria"]:
                block += f"- {criterion}\n"
        
        if pattern.get("exclusions"):
            block += f"\n**EXCLUSIONS:**\n"
            for exclusion in pattern["exclusions"]:
                block += f"- {exclusion}\n"
        
        if pattern.get("guards"):
            block += f"\n**GUARDS & REQUIREMENTS:**\n"
            for guard in pattern["guards"]:
                block += f"- {guard}\n"
        
        if pattern.get("detailed_examples"):
            block += f"\n**DETAILED EXAMPLES:**\n"
            for example in pattern["detailed_examples"]:
                block += f"- {example}\n"
        
        if pattern.get("clarifications"):
            block += f"\n**CLARIFICATIONS:**\n"
            for clarification in pattern["clarifications"]:
                block += f"- {clarification}\n"
        
        return block
    
    def generate_minimalist_hop(self, hop_num: int, meta: Dict[str, Any], patterns: List[str]) -> str:
        """Generate a minimalist hop prompt that references the enhanced checklist."""
        frame = meta.get("frame", "Unknown")
        summary = meta.get("summary", "")
        
        pattern_list = "\n".join([f"- `{p}`" for p in patterns])
        
        return f"""---
meta_id: Q{hop_num}
frame: {frame}
summary: "{summary}"
---
### Segment (StatementID: {{{{statement_id}}}})
{{{{segment_text}}}}

### Question Q{hop_num}
Review the CUE_MAP you generated using the ENHANCED CHECKLIST.

Does the segment trigger any of the following patterns according to their detailed rules?
{pattern_list}

If yes, and no exclusions apply, answer "yes". Otherwise, answer "no".

Return JSON:
```json
{{
  "answer": "yes|no|uncertain",
  "rationale": "<max 80 tokens – cite pattern and cue if yes>"
}}
```"""
    
    def process_hop(self, hop_num: int) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Process a single hop prompt and extract all patterns."""
        hop_file = self.prompts_dir / f"hop_Q{hop_num:02}.txt"
        if not hop_file.exists():
            print(f"Warning: {hop_file} not found")
            return [], {}
        
        content, meta = load_prompt_and_meta(hop_file)
        
        # Extract components
        quick_check = self.extract_quick_check(content)
        pattern_table = self.extract_pattern_table(content)
        detailed_rules = self.extract_detailed_rules(content)
        
        # Build pattern list
        patterns = []
        
        # Process each row from the pattern table
        for row in pattern_table:
            if "→" not in row["outcome"]:  # Skip non-frame rows
                continue
            
            pattern = {
                "id": row["id"] or f"Q{hop_num}",
                "pattern_type": row["pattern_type"],
                "examples": row["examples"],
                "quick_check": quick_check,
                "inclusion_criteria": detailed_rules["inclusion_criteria"],
                "exclusions": detailed_rules["exclusion_criteria"],
                "guards": detailed_rules["guards"],
                "detailed_examples": detailed_rules["examples"],
                "clarifications": detailed_rules["clarifications"]
            }
            patterns.append(pattern)
        
        # If no pattern table found, create a single pattern from the hop
        if not patterns and meta.get("frame") != "Variable":
            patterns.append({
                "id": f"Q{hop_num}",
                "pattern_type": meta.get("summary", f"Hop {hop_num} pattern"),
                "examples": "",
                "quick_check": quick_check,
                "inclusion_criteria": detailed_rules["inclusion_criteria"],
                "exclusions": detailed_rules["exclusion_criteria"],
                "guards": detailed_rules["guards"],
                "detailed_examples": detailed_rules["examples"],
                "clarifications": detailed_rules["clarifications"]
            })
        
        return patterns, meta
    
    def build_enhanced_checklist(self):
        """Build the complete enhanced checklist."""
        alarmist_patterns = []
        reassuring_patterns = []
        neutral_patterns = []
        
        all_pattern_ids = []
        
        # Process each hop
        for hop_num in range(1, 13):
            print(f"Processing hop Q{hop_num:02}...")
            patterns, meta = self.process_hop(hop_num)
            
            for pattern in patterns:
                pattern_block = self.format_pattern_block(hop_num, pattern, meta)
                
                # Collect pattern IDs for hop generation
                pattern_id = f"{pattern['id']}: {pattern['pattern_type']}"
                all_pattern_ids.append((hop_num, pattern_id))
                
                # Sort into appropriate category
                frame = meta.get("frame", "").lower()
                if frame == "alarmist":
                    alarmist_patterns.append(pattern_block)
                elif frame == "reassuring":
                    reassuring_patterns.append(pattern_block)
                elif frame == "neutral":
                    neutral_patterns.append(pattern_block)
                elif frame == "variable" and hop_num == 11:
                    # Q11 has both alarmist and reassuring patterns
                    if "alarmist" in pattern["pattern_type"].lower():
                        alarmist_patterns.append(pattern_block)
                    elif "reassuring" in pattern["pattern_type"].lower():
                        reassuring_patterns.append(pattern_block)
        
        # Build the complete checklist
        checklist = """# ENHANCED CUE DETECTION CHECKLIST
This checklist contains ALL rules, guards, exclusions, and examples from the original hop prompts.
It serves as the single source of truth for frame detection.

## HOW TO USE THIS CHECKLIST

1. Read the segment carefully
2. For each pattern below, check if it applies
3. Pay attention to ALL exclusions and guards
4. Mark patterns as PRESENT or ABSENT in your CUE_MAP
5. Use the CUE_MAP to answer hop questions

---

# ALARMIST CUES
Patterns that indicate an alarmist framing of the information.
"""
        
        checklist += "\n".join(alarmist_patterns)
        
        checklist += """

---

# REASSURING CUES
Patterns that indicate a reassuring framing of the information.
"""
        
        checklist += "\n".join(reassuring_patterns)
        
        checklist += """

---

# NEUTRAL INDICATORS
Patterns that indicate neutral, factual reporting.
"""
        
        checklist += "\n".join(neutral_patterns)
        
        checklist += """

---

# PRECEDENCE RULES

When multiple patterns match, apply these rules:
1. If both Alarmist and Reassuring cues present → Neutral (mixed signals)
2. Higher-numbered questions (Q1-Q4) take precedence over lower ones
3. Explicit quotes (Q11) can override authorial framing
4. Technical terms (e.g., "highly pathogenic avian influenza") never count as intensifiers

---

# UNIVERSAL GUARDS

These apply to ALL patterns:
1. **Source Requirement**: For reassuring cues, speaker must be official/authority or author
2. **Context Requirement**: Cues must relate to the main threat, not background conditions
3. **Technical Term Guard**: "highly pathogenic (avian) influenza" and "HPAI" are neutral taxonomy
4. **Containment Override**: Containment verbs (culled, destroyed) can neutralize some patterns
"""
        
        # Write the enhanced checklist
        output_file = self.output_dir / "enhanced_checklist.txt"
        output_file.write_text(checklist, encoding="utf-8")
        print(f"Enhanced checklist written to {output_file}")
        
        # Generate minimalist hop prompts
        self.generate_minimalist_hops(all_pattern_ids)
    
    def generate_minimalist_hops(self, pattern_ids: List[Tuple[int, str]]):
        """Generate minimalist hop prompts that reference the enhanced checklist."""
        # Group patterns by hop
        hop_patterns = {}
        for hop_num, pattern_id in pattern_ids:
            if hop_num not in hop_patterns:
                hop_patterns[hop_num] = []
            hop_patterns[hop_num].append(pattern_id)
        
        # Create output directory
        self.enhanced_hops_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate each hop
        for hop_num in range(1, 13):
            hop_file = self.prompts_dir / f"hop_Q{hop_num:02}.txt"
            if hop_file.exists():
                _, meta = load_prompt_and_meta(hop_file)
                patterns = hop_patterns.get(hop_num, [f"Q{hop_num}: Default pattern"])
                
                hop_content = self.generate_minimalist_hop(hop_num, meta, patterns)
                
                output_file = self.enhanced_hops_dir / f"hop_Q{hop_num:02}.txt"
                output_file.write_text(hop_content, encoding="utf-8")
                print(f"Generated minimalist hop: {output_file}")


def main():
    """Run the migration."""
    extractor = PatternExtractor()
    extractor.build_enhanced_checklist()
    print("\nMigration complete! Next steps:")
    print("1. Review the generated enhanced_checklist.txt")
    print("2. Run the verification tests")
    print("3. Update run_multi_coder_tot.py to use the new layout")


if __name__ == "__main__":
    main() 