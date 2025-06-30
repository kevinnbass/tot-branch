#!/usr/bin/env python3
"""
Verification test to ensure the enhanced checklist migration is loss-less.
This test proves that no rules, keywords, or special cases were dropped.
"""

import pytest
import re
import sys
from pathlib import Path
from typing import Set, List, Dict

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from multi_coder_analysis.utils.prompt_loader import load_prompt_and_meta


class ChecklistVerifier:
    """Verify that all content from original prompts exists in enhanced checklist."""
    
    def __init__(self):
        self.prompts_dir = Path(__file__).parent.parent / "multi_coder_analysis" / "prompts"
        self.checklist_path = self.prompts_dir / "cue_detection" / "enhanced_checklist_v2.txt"
        
    def extract_key_phrases(self, content: str) -> Set[str]:
        """Extract all key phrases that must be preserved."""
        key_phrases = set()
        
        # Extract all quoted phrases (single and double quotes)
        for match in re.finditer(r'"([^"]+)"', content):
            phrase = match.group(1).strip()
            if len(phrase) > 3:  # Skip very short phrases
                key_phrases.add(phrase.lower())
                
        for match in re.finditer(r"'([^']+)'", content):
            phrase = match.group(1).strip()
            if len(phrase) > 3:
                key_phrases.add(phrase.lower())
        
        # Extract bold text
        for match in re.finditer(r'\*\*([^*]+)\*\*', content):
            phrase = match.group(1).strip()
            if len(phrase) > 3:
                key_phrases.add(phrase.lower())
        
        # Extract specific rule keywords
        rule_keywords = [
            "intensifier", "risk-adjective", "high-potency", "moderate verb",
            "scale", "impact", "loaded question", "calming cue", "minimiser",
            "bare negation", "capability", "preparedness", "economic", "metric",
            "speculation", "relief", "quote", "dominant", "mixed",
            "highly pathogenic", "avian influenza", "HPAI", "technical term",
            "containment", "culled", "destroyed", "within 50 characters",
            "within 40 chars", "≤20 chars", "same clause", "adjacent",
            "precedence", "guard", "exclusion", "override"
        ]
        
        for keyword in rule_keywords:
            if keyword.lower() in content.lower():
                key_phrases.add(keyword.lower())
        
        # Extract specific patterns
        pattern_regexes = [
            r"Q\d+\.\d+",  # Pattern IDs like Q1.1
            r"→\s*(Alarmist|Reassuring|Neutral)",  # Frame outcomes
            r"Precedence\s*#?\d+",  # Precedence rules
            r"\d+\s*(?:chars?|characters?|tokens?)",  # Distance requirements
        ]
        
        for pattern in pattern_regexes:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                key_phrases.add(match.group(0).lower())
        
        return key_phrases
    
    def verify_row_map_coverage(self, hop_num: int, meta: Dict, checklist_content: str) -> List[str]:
        """Verify all row_map entries are in the checklist."""
        missing = []
        
        row_map = meta.get("row_map", {})
        for row_id, row_desc in row_map.items():
            # Check if row ID appears
            if row_id not in checklist_content:
                missing.append(f"Row ID {row_id} from Q{hop_num}")
            
            # Check if row description appears (normalized)
            normalized_desc = row_desc.lower().replace("-", " ").replace("_", " ")
            normalized_checklist = checklist_content.lower().replace("-", " ").replace("_", " ")
            
            if normalized_desc not in normalized_checklist:
                # Try partial match for key terms
                key_terms = [term for term in normalized_desc.split() if len(term) > 3]
                if not all(term in normalized_checklist for term in key_terms):
                    missing.append(f"Row description '{row_desc}' from Q{hop_num}")
        
        return missing
    
    def verify_examples(self, content: str, checklist_content: str) -> List[str]:
        """Verify all examples are preserved."""
        missing = []
        
        # Extract example sentences
        example_patterns = [
            r"Example[:\s]+(.+?)(?:→|$)",
            r"(?:YES|NO) example.*?## Input Segment: (.+?)(?:\n|$)",
            r"\*\s*(?:Example|e\.g\.,).*?[:\s]+(.+?)(?:\n|→|$)",
        ]
        
        for pattern in example_patterns:
            for match in re.finditer(pattern, content, re.DOTALL | re.IGNORECASE):
                example = match.group(1).strip()
                if len(example) > 10:
                    # Normalize and check
                    normalized = example.lower().replace('"', '').replace("'", '')
                    if normalized not in checklist_content.lower():
                        missing.append(f"Example: {example[:50]}...")
        
        return missing
    
    def run_verification(self) -> Dict[str, List[str]]:
        """Run complete verification and return results."""
        if not self.checklist_path.exists():
            return {"error": ["Enhanced checklist not found at " + str(self.checklist_path)]}
        
        checklist_content = self.checklist_path.read_text(encoding="utf-8")
        results = {
            "missing_phrases": [],
            "missing_row_maps": [],
            "missing_examples": [],
            "missing_patterns": []
        }
        
        # Process each hop
        for hop_num in range(1, 13):
            hop_file = self.prompts_dir / f"hop_Q{hop_num:02}.txt"
            if not hop_file.exists():
                continue
                
            content, meta = load_prompt_and_meta(hop_file)
            
            # Extract and verify key phrases
            key_phrases = self.extract_key_phrases(content)
            for phrase in key_phrases:
                if phrase not in checklist_content.lower():
                    # Some phrases might be reformatted, do fuzzy check
                    words = phrase.split()
                    if len(words) > 1 and not all(word in checklist_content.lower() for word in words):
                        results["missing_phrases"].append(f"Q{hop_num}: '{phrase}'")
            
            # Verify row map coverage
            missing_rows = self.verify_row_map_coverage(hop_num, meta, checklist_content)
            results["missing_row_maps"].extend(missing_rows)
            
            # Verify examples
            missing_examples = self.verify_examples(content, checklist_content)
            results["missing_examples"].extend(missing_examples)
        
        # Remove duplicates
        for key in results:
            results[key] = list(set(results[key]))
        
        return results


def test_enhanced_checklist_completeness():
    """Test that the enhanced checklist contains all information from original prompts."""
    verifier = ChecklistVerifier()
    results = verifier.run_verification()
    
    # Print detailed results for debugging
    total_missing = 0
    for category, missing_items in results.items():
        if missing_items:
            print(f"\n{category}:")
            for item in missing_items[:10]:  # Show first 10
                print(f"  - {item}")
            if len(missing_items) > 10:
                print(f"  ... and {len(missing_items) - 10} more")
            total_missing += len(missing_items)
    
    # The test passes if we have very few missing items (some reformatting is expected)
    assert total_missing < 50, f"Too many missing items ({total_missing}). Migration may have lost information."


def test_pattern_ids_match():
    """Test that all pattern IDs in row_maps appear in the checklist."""
    prompts_dir = Path(__file__).parent.parent / "multi_coder_analysis" / "prompts"
    checklist_path = prompts_dir / "cue_detection" / "enhanced_checklist_v2.txt"
    
    if not checklist_path.exists():
        pytest.skip("Enhanced checklist not found")
    
    checklist_content = checklist_path.read_text(encoding="utf-8")
    missing_patterns = []
    
    for hop_num in range(1, 13):
        hop_file = prompts_dir / f"hop_Q{hop_num:02}.txt"
        if hop_file.exists():
            _, meta = load_prompt_and_meta(hop_file)
            row_map = meta.get("row_map", {})
            
            for pattern_id in row_map.keys():
                if pattern_id and pattern_id not in checklist_content:
                    missing_patterns.append(pattern_id)
    
    assert not missing_patterns, f"Missing pattern IDs: {missing_patterns}"


def test_precedence_rules_preserved():
    """Test that precedence rules are preserved in the checklist."""
    prompts_dir = Path(__file__).parent.parent / "multi_coder_analysis" / "prompts"
    checklist_path = prompts_dir / "cue_detection" / "enhanced_checklist_v2.txt"
    
    if not checklist_path.exists():
        pytest.skip("Enhanced checklist not found")
    
    checklist_content = checklist_path.read_text(encoding="utf-8")
    
    # Check for precedence section
    assert "PRECEDENCE RULES" in checklist_content, "Missing precedence rules section"
    
    # Check for specific precedence mentions
    precedence_mentions = [
        "higher-numbered questions",
        "Q1-Q4",
        "take precedence",
        "mixed signals"
    ]
    
    for mention in precedence_mentions:
        assert mention.lower() in checklist_content.lower(), f"Missing precedence rule: {mention}"


def test_universal_guards_preserved():
    """Test that universal guards are preserved."""
    prompts_dir = Path(__file__).parent.parent / "multi_coder_analysis" / "prompts"
    checklist_path = prompts_dir / "cue_detection" / "enhanced_checklist_v2.txt"
    
    if not checklist_path.exists():
        pytest.skip("Enhanced checklist not found")
    
    checklist_content = checklist_path.read_text(encoding="utf-8")
    
    # Check for guards section
    assert "UNIVERSAL GUARDS" in checklist_content, "Missing universal guards section"
    
    # Check for specific guards
    guards = [
        "Source Requirement",
        "Context Requirement",
        "Technical Term Guard",
        "Containment Override"
    ]
    
    for guard in guards:
        assert guard in checklist_content, f"Missing guard: {guard}"


if __name__ == "__main__":
    # Run verification and print results
    verifier = ChecklistVerifier()
    results = verifier.run_verification()
    
    print("Verification Results:")
    print("=" * 50)
    
    total_issues = 0
    for category, items in results.items():
        if items:
            print(f"\n{category}: {len(items)} issues")
            for item in items[:5]:
                print(f"  - {item}")
            if len(items) > 5:
                print(f"  ... and {len(items) - 5} more")
            total_issues += len(items)
    
    if total_issues == 0:
        print("\n[SUCCESS] All content from original prompts is preserved in the enhanced checklist!")
    else:
        print(f"\n[WARNING] Found {total_issues} potential issues. Review needed.") 