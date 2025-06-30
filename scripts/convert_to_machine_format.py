#!/usr/bin/env python3
"""Convert enhanced checklist to machine-readable format."""

import json
from pathlib import Path
import re

def extract_pattern_rules(content: dict, hop_id: str) -> dict:
    """Extract and structure pattern rules from hop content."""
    
    # Create rule IDs
    rules = {
        "inclusion": [],
        "exclusion": [],
        "special": [],
        "precedence": []
    }
    
    # Process inclusion criteria
    for i, rule in enumerate(content.get("inclusion_criteria", [])):
        if isinstance(rule, str) and rule.strip():
            rule_id = f"{hop_id}.I{i+1}"
            rules["inclusion"].append(rule_id)
    
    # Process exclusion criteria  
    for i, rule in enumerate(content.get("exclusion_criteria", [])):
        if isinstance(rule, str) and rule.strip():
            rule_id = f"{hop_id}.E{i+1}"
            rules["exclusion"].append(rule_id)
    
    # Process special rules
    for i, rule in enumerate(content.get("special_rules", [])):
        if isinstance(rule, str) and rule.strip():
            rule_id = f"{hop_id}.S{i+1}"
            rules["special"].append(rule_id)
    
    # Process precedence rules
    for i, rule in enumerate(content.get("precedence_rules", [])):
        if isinstance(rule, str) and rule.strip():
            rule_id = f"{hop_id}.P{i+1}"
            rules["precedence"].append(rule_id)
    
    return rules


def create_rule_definitions(content: dict, hop_id: str) -> dict:
    """Create rule definitions mapping."""
    definitions = {}
    
    # Inclusion rules
    for i, rule in enumerate(content.get("inclusion_criteria", [])):
        if isinstance(rule, str) and rule.strip():
            rule_id = f"{hop_id}.I{i+1}"
            definitions[rule_id] = {
                "type": "inclusion",
                "text": rule.strip()
            }
    
    # Exclusion rules
    for i, rule in enumerate(content.get("exclusion_criteria", [])):
        if isinstance(rule, str) and rule.strip():
            rule_id = f"{hop_id}.E{i+1}"
            definitions[rule_id] = {
                "type": "exclusion", 
                "text": rule.strip()
            }
    
    # Special rules
    for i, rule in enumerate(content.get("special_rules", [])):
        if isinstance(rule, str) and rule.strip():
            rule_id = f"{hop_id}.S{i+1}"
            definitions[rule_id] = {
                "type": "special",
                "text": rule.strip()
            }
    
    # Precedence rules
    for i, rule in enumerate(content.get("precedence_rules", [])):
        if isinstance(rule, str) and rule.strip():
            rule_id = f"{hop_id}.P{i+1}"
            definitions[rule_id] = {
                "type": "precedence",
                "text": rule.strip()
            }
    
    return definitions


def extract_structured_examples(content: dict) -> dict:
    """Extract and structure examples."""
    examples = {
        "positive": [],
        "negative": []
    }
    
    # Process examples array
    for example in content.get("examples", []):
        if not isinstance(example, str):
            continue
            
        # Try to identify positive vs negative examples
        if any(marker in example.lower() for marker in ["non-example", "neutral", "→ neutral"]):
            examples["negative"].append(example.strip())
        elif any(marker in example.lower() for marker in ["alarmist", "reassuring", "→ alarmist", "→ reassuring"]):
            examples["positive"].append(example.strip())
    
    return examples


def convert_hop_to_machine(hop_data: dict, hop_id: str) -> tuple[dict, dict, dict]:
    """Convert a single hop to machine-readable format."""
    meta = hop_data.get("meta", {})
    content = hop_data.get("content", {})
    
    # Main hop structure
    machine_hop = {
        "hop_id": hop_id,
        "frame": meta.get("frame", ""),
        "patterns": meta.get("row_map", {}),
        "rules": extract_pattern_rules(content, hop_id),
        "quick_check": {
            "type": "structured",
            "elements": []  # Would need more parsing to fully structure
        },
        "guards": content.get("guards", []),
        "constraints": []
    }
    
    # Extract constraints from special rules
    for rule in content.get("special_rules", []):
        if "distance" in rule.lower() or "adjacent" in rule.lower():
            machine_hop["constraints"].append({
                "type": "distance",
                "value": "40_chars" if "40" in rule else "adjacent"
            })
    
    # Create rule definitions
    rule_defs = create_rule_definitions(content, hop_id)
    
    # Extract examples
    examples = extract_structured_examples(content)
    
    return machine_hop, rule_defs, examples


def main():
    """Convert all hops to machine-readable format."""
    
    # Load enhanced checklist
    checklist_path = Path("multi_coder_analysis/prompts/cue_detection/enhanced_checklist_v2.json")
    with open(checklist_path, 'r', encoding='utf-8') as f:
        checklist = json.load(f)
    
    output_dir = Path("multi_coder_analysis/prompts/cue_detection/machine")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process each hop
    all_rule_definitions = {}
    
    for hop_id, hop_data in checklist.get("hops", {}).items():
        print(f"Converting {hop_id}...")
        
        # Normalize hop_id to Q01 format
        if hop_id.startswith("Q") and len(hop_id) == 2:
            normalized_id = f"Q0{hop_id[1]}"
        elif hop_id.startswith("Q") and len(hop_id) == 3:
            normalized_id = hop_id
        else:
            normalized_id = f"Q{int(hop_id):02d}"
        
        # Convert to machine format (returns machine_hop structure, rule_defs, examples)
        machine_hop, rule_defs, examples = convert_hop_to_machine(hop_data, hop_id)
        
        # ════════════════════════════════════════════════════════
        # Embed FULL information for loss-less precision
        # ════════════════════════════════════════════════════════
        machine_hop["definitions"] = rule_defs  # full rule bodies
        machine_hop["examples"] = examples  # keep full positive / negative lists
        
        # Remove external-file dependency by NOT collecting rule_defs globally
        # (We still keep all_rule_definitions for optional reference file)
        all_rule_definitions.update(rule_defs)
        
        # Save hop file with normalized name
        hop_file = output_dir / f"{normalized_id}.json"
        with open(hop_file, 'w', encoding='utf-8') as f:
            json.dump(machine_hop, f, ensure_ascii=False, separators=(',', ':'))
        
        # Optionally save per-hop example file no longer needed – skip
    
    # Save all rule definitions
    rules_file = output_dir / "rule_definitions.json"
    with open(rules_file, 'w', encoding='utf-8') as f:
        json.dump(all_rule_definitions, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Converted {len(checklist.get('hops', {}))} hops to machine format")
    print(f"📁 Output directory: {output_dir}")


if __name__ == "__main__":
    main() 