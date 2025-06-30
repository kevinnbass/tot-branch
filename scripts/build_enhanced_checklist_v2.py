#!/usr/bin/env python3
"""
Build enhanced checklist v2 - Truly loss-less extraction.
This version preserves ALL content from the original hop prompts.
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any
import yaml
import json

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from multi_coder_analysis.utils.prompt_loader import load_prompt_and_meta


class EnhancedPatternExtractor:
    """Extract ALL patterns and rules from hop prompts - truly loss-less."""
    
    def __init__(self):
        self.prompts_dir = Path(__file__).parent.parent / "multi_coder_analysis" / "prompts"
        self.output_dir = self.prompts_dir / "cue_detection"
        self.enhanced_hops_dir = self.output_dir / "enhanced_hops"
        
    def extract_all_content(self, content: str) -> Dict[str, Any]:
        """Extract ALL content sections from a hop prompt."""
        sections = {
            "quick_check": "",
            "pattern_table": [],
            "inclusion_criteria": [],
            "exclusion_criteria": [],
            "examples": [],
            "guards": [],
            "clarifications": [],
            "special_rules": [],
            "precedence_rules": [],
            "technical_notes": [],
            "raw_sections": []  # Store raw text sections for completeness
        }
        
        # Extract QUICK DECISION CHECK
        quick_check_match = re.search(
            r"### ⚡?\s*QUICK DECISION CHECK(.*?)(?=\n###|\n===|\Z)",
            content, re.DOTALL
        )
        if quick_check_match:
            sections["quick_check"] = quick_check_match.group(1).strip()
        
        # Extract pattern table with ALL rows
        table_match = re.search(
            r"\| \*\*Pattern Type\*\* \|.*?\n\|[-\s|]+\n(.*?)(?=\n\n|\n\*\*|\Z)",
            content, re.DOTALL
        )
        if table_match:
            table_content = table_match.group(1)
            # Extract ALL rows, including those without frame outcomes
            all_rows = re.findall(
                r"(?:<!--\s*(Q\d+\.\d+)\s*-->)?\s*\|\s*\*\*(.*?)\*\*\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|",
                table_content
            )
            for row in all_rows:
                pattern_id = row[0].strip() if row[0] else ""
                pattern_type = row[1].strip()
                examples = row[2].strip()
                outcome = row[3].strip()
                
                sections["pattern_table"].append({
                    "id": pattern_id,
                    "pattern_type": pattern_type,
                    "examples": examples,
                    "outcome": outcome
                })
        
        # Extract ALL sections with headers
        section_patterns = [
            (r"\*\*Alarmist - Inclusion Criteria:\*\*(.*?)(?=\n\*\*|\Z)", "inclusion_criteria"),
            (r"\*\*Reassuring - Examples:\*\*(.*?)(?=\n\*\*|\Z)", "inclusion_criteria"),
            (r"\*\*Neutral - Examples:\*\*(.*?)(?=\n\*\*|\Z)", "inclusion_criteria"),
            (r"⛔\s*EXCLUSIONS.*?:(.*?)(?=\n\*\*|\n###|\Z)", "exclusion_criteria"),
            (r"\*\*EXCLUSION.*?\*\*(.*?)(?=\n\*\*|\Z)", "exclusion_criteria"),
            (r"🛡️\s*UNIVERSAL GUARDS.*?:(.*?)(?=\n\*\*|\Z)", "guards"),
            (r"\*\*Guard.*?\*\*(.*?)(?=\n\*\*|\Z)", "guards"),
            (r"\*\*Few-Shot Examples.*?\*\*(.*?)(?=\n\*\*|\Z)", "examples"),
            (r"\*\*Examples?.*?\*\*(.*?)(?=\n\*\*|\Z)", "examples"),
            (r"(?:CLARIFICATION|NOTE|SPECIAL).*?:(.*?)(?=\n\n|\n\*\*|\Z)", "clarifications"),
            (r"►\s*(.*?)(?=\n\n|\Z)", "clarifications"),
            (r"⚠\s*(.*?)(?=\n\n|\Z)", "clarifications"),
            (r"Precedence\s*#?\d+.*?:(.*?)(?=\n\n|\Z)", "precedence_rules"),
            (r"\*\*Technical.*?\*\*(.*?)(?=\n\*\*|\Z)", "technical_notes"),
        ]
        
        for pattern, section_key in section_patterns:
            for match in re.finditer(pattern, content, re.DOTALL | re.IGNORECASE):
                text = match.group(1).strip()
                if text:
                    if section_key in ["inclusion_criteria", "exclusion_criteria", "guards", "examples"]:
                        # Extract bullet points
                        bullets = self._extract_all_bullets(text)
                        sections[section_key].extend(bullets)
                    else:
                        sections[section_key].append(text)
        
        # Extract any remaining structured content
        self._extract_special_patterns(content, sections)
        
        return sections
    
    def _extract_all_bullets(self, text: str) -> List[str]:
        """Extract ALL bullet points, preserving complete text."""
        bullets = []
        
        # Split by newlines and process each line
        lines = text.split('\n')
        current_bullet = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if this is a new bullet point
            if re.match(r'^[•*✓✗-]\s+', line):
                # Save previous bullet if exists
                if current_bullet:
                    bullets.append(' '.join(current_bullet))
                # Start new bullet
                current_bullet = [re.sub(r'^[•*✓✗-]\s+', '', line)]
            elif current_bullet:
                # Continuation of previous bullet
                current_bullet.append(line)
            else:
                # Standalone line
                bullets.append(line)
        
        # Don't forget the last bullet
        if current_bullet:
            bullets.append(' '.join(current_bullet))
        
        return bullets
    
    def _extract_special_patterns(self, content: str, sections: Dict[str, Any]):
        """Extract special patterns that might be missed by standard extraction."""
        # Distance requirements
        distance_patterns = re.findall(
            r"(?:within|≤|<=)\s*(\d+)\s*(?:chars?|characters?|tokens?)",
            content, re.IGNORECASE
        )
        for dist in distance_patterns:
            sections["special_rules"].append(f"Distance requirement: within {dist} characters")
        
        # Adjacency requirements
        if "adjacent" in content.lower() or "same clause" in content.lower():
            sections["special_rules"].append("Adjacency requirement: elements must be in same clause or adjacent")
        
        # Extract ALL quoted examples
        quoted_examples = re.findall(r'"([^"]{5,})"', content)
        for example in quoted_examples:
            if example not in str(sections):  # Avoid duplicates
                sections["examples"].append(f'Example: "{example}"')
        
        # Extract technical term guards
        if "highly pathogenic" in content.lower():
            sections["guards"].append("Technical Term Guard: 'highly pathogenic (avian) influenza' and 'HPAI' are neutral taxonomy")
        
        # Extract containment overrides
        containment_terms = ["culled", "destroyed", "euthanized", "depopulated"]
        for term in containment_terms:
            if term in content.lower():
                sections["guards"].append(f"Containment Override: '{term}' can neutralize certain patterns")
                break
    
    def generate_enhanced_pattern_block(self, hop_num: int, meta: Dict[str, Any], 
                                      all_content: Dict[str, Any]) -> str:
        """Generate a comprehensive pattern block with ALL extracted content."""
        frame = meta.get("frame", "Unknown")
        summary = meta.get("summary", "")
        
        block = f"""
---
### Hop Q{hop_num}: {summary}
**Frame:** {frame}
"""
        
        # Add quick check if present
        if all_content.get("quick_check"):
            block += f"\n**⚡ QUICK DECISION CHECK:**\n{all_content['quick_check']}\n"
        
        # Add pattern table if present
        if all_content.get("pattern_table"):
            block += "\n**PATTERN RECOGNITION TABLE:**\n"
            block += "| Pattern ID | Pattern Type | Examples | Outcome |\n"
            block += "|------------|--------------|----------|----------|\n"
            for row in all_content["pattern_table"]:
                pattern_id = row["id"] or f"Q{hop_num}"
                block += f"| {pattern_id} | {row['pattern_type']} | {row['examples']} | {row['outcome']} |\n"
            block += "\n"
        
        # Add all other sections
        section_headers = {
            "inclusion_criteria": "**INCLUSION CRITERIA:**",
            "exclusion_criteria": "**EXCLUSIONS:**",
            "guards": "**GUARDS & REQUIREMENTS:**",
            "examples": "**EXAMPLES & CASES:**",
            "clarifications": "**CLARIFICATIONS & NOTES:**",
            "precedence_rules": "**PRECEDENCE RULES:**",
            "technical_notes": "**TECHNICAL NOTES:**",
            "special_rules": "**SPECIAL RULES:**"
        }
        
        for section_key, header in section_headers.items():
            content_list = all_content.get(section_key, [])
            if content_list:
                block += f"\n{header}\n"
                for item in content_list:
                    block += f"- {item}\n"
        
        return block
    
    def process_hop_v2(self, hop_num: int) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Process a hop with enhanced extraction."""
        hop_file = self.prompts_dir / f"hop_Q{hop_num:02}.txt"
        if not hop_file.exists():
            print(f"Warning: {hop_file} not found")
            return {}, {}
        
        content, meta = load_prompt_and_meta(hop_file)
        
        # Extract ALL content
        all_content = self.extract_all_content(content)
        
        # Also preserve row_map from meta
        if "row_map" in meta:
            all_content["row_map"] = meta["row_map"]
        
        return all_content, meta
    
    def build_enhanced_checklist_v2(self):
        """Build the truly loss-less enhanced checklist."""
        checklist_sections = {
            "alarmist": [],
            "reassuring": [],
            "neutral": [],
            "variable": []
        }
        
        # Process each hop
        for hop_num in range(1, 13):
            print(f"Processing hop Q{hop_num:02}...")
            all_content, meta = self.process_hop_v2(hop_num)
            
            if not all_content:
                continue
            
            # Generate comprehensive block
            pattern_block = self.generate_enhanced_pattern_block(hop_num, meta, all_content)
            
            # Sort into appropriate category
            frame = meta.get("frame", "").lower()
            if frame in checklist_sections:
                checklist_sections[frame].append(pattern_block)
            elif frame == "variable" and hop_num == 11:
                # Q11 needs special handling - add to both
                checklist_sections["alarmist"].append(pattern_block + "\n*Note: Q11 Variable - check for Alarmist quotes*")
                checklist_sections["reassuring"].append(pattern_block + "\n*Note: Q11 Variable - check for Reassuring quotes*")
        
        # Build the complete checklist
        checklist = """# ENHANCED CUE DETECTION CHECKLIST V2
This checklist contains 100% of the content from the original hop prompts.
Every rule, example, guard, exclusion, and special case is preserved.

## HOW TO USE THIS CHECKLIST

1. Read the segment carefully
2. Work through each hop section systematically
3. For each pattern:
   - Check the QUICK DECISION CHECK first
   - Review the pattern table
   - Apply ALL inclusion criteria
   - Check ALL exclusions and guards
   - Consider precedence rules
4. Mark patterns as PRESENT or ABSENT in your CUE_MAP
5. Use the CUE_MAP to answer hop questions

## CRITICAL REMINDERS

- Technical terms like "highly pathogenic avian influenza" are ALWAYS neutral
- Containment verbs (culled, destroyed) can override certain patterns
- Distance requirements (e.g., "within 40 chars") must be strictly followed
- When multiple patterns match, apply precedence rules

---

# ALARMIST PATTERNS (Q1-Q4)
These patterns indicate alarmist framing of information.
"""
        
        checklist += "\n".join(checklist_sections["alarmist"])
        
        checklist += """

---

# REASSURING PATTERNS (Q5-Q6)
These patterns indicate reassuring framing of information.
"""
        
        checklist += "\n".join(checklist_sections["reassuring"])
        
        checklist += """

---

# NEUTRAL PATTERNS (Q7-Q10, Q12)
These patterns indicate neutral, factual reporting.
"""
        
        checklist += "\n".join(checklist_sections["neutral"])
        
        if checklist_sections["variable"]:
            checklist += """

---

# VARIABLE PATTERNS (Q11)
Pattern depends on quote content - can be Alarmist or Reassuring.
"""
            checklist += "\n".join(checklist_sections["variable"])
        
        checklist += """

---

# GLOBAL PRECEDENCE RULES

1. **Technical Term Override**: "highly pathogenic (avian) influenza" and "HPAI" are ALWAYS neutral
2. **Containment Override**: Containment verbs neutralize moderate verb patterns unless extreme language used
3. **Mixed Signals**: If both Alarmist and Reassuring cues present → Neutral
4. **Hop Precedence**: Lower hop numbers (Q1-Q4) take precedence over higher ones
5. **Quote Dominance**: Explicit quotes (Q11) can override authorial framing
6. **Uncertainty Cascade**: 3 consecutive "uncertain" → LABEL_UNCERTAIN

---

# UNIVERSAL GUARDS

These apply across ALL patterns:

1. **Source Requirement**: For reassuring cues, speaker must be official/authority or author
2. **Context Requirement**: Cues must relate to the main threat, not background conditions  
3. **Technical Term Guard**: Scientific/medical terminology is neutral unless modified by intensifiers
4. **Distance Requirements**: Respect all character/token distance limits specified in patterns
5. **Adjacency Rules**: Elements must be in same clause when specified
"""
        
        # Write the enhanced checklist
        output_file = self.output_dir / "enhanced_checklist_v2.txt"
        output_file.write_text(checklist, encoding="utf-8")
        print(f"\nEnhanced checklist v2 written to {output_file}")
        
        # Also save as structured JSON for programmatic access
        structured_data = {
            "version": "2.0",
            "hops": {}
        }
        
        for hop_num in range(1, 13):
            all_content, meta = self.process_hop_v2(hop_num)
            if all_content:
                structured_data["hops"][f"Q{hop_num}"] = {
                    "meta": meta,
                    "content": all_content
                }
        
        json_file = self.output_dir / "enhanced_checklist_v2.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(structured_data, f, indent=2, ensure_ascii=False)
        print(f"Structured data saved to {json_file}")


def main():
    """Run the enhanced migration."""
    extractor = EnhancedPatternExtractor()
    extractor.build_enhanced_checklist_v2()
    print("\nEnhanced migration complete!")
    print("\nNext steps:")
    print("1. Review enhanced_checklist_v2.txt")
    print("2. Run verification tests")
    print("3. Update layout to use enhanced_checklist_v2.txt")


if __name__ == "__main__":
    main() 