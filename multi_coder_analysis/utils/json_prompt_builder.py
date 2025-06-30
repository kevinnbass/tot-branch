"""JSON Prompt Builder for fully parameterized cue detection prompts."""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Path to the enhanced checklist
CHECKLIST_PATH = Path(__file__).parent.parent / "prompts" / "cue_detection" / "enhanced_checklist_v2.json"


def _load_checklist() -> Dict[str, Any]:
    """Load the enhanced checklist JSON file."""
    if not CHECKLIST_PATH.exists():
        raise FileNotFoundError(f"Enhanced checklist not found at {CHECKLIST_PATH}")
    
    with open(CHECKLIST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _get_hop_entry(checklist: Dict[str, Any], q_id: str) -> Dict[str, Any]:
    """Get hop entry from checklist, handling both padded and unpadded keys."""
    hops = checklist.get("hops", {})
    
    # Try exact match first
    if q_id in hops:
        return hops[q_id]
    
    # Handle Q01 -> Q1 conversion
    if q_id.startswith("Q0") and len(q_id) == 3:
        unpadded = "Q" + q_id[2]
        if unpadded in hops:
            return hops[unpadded]
    
    # Handle Q1 -> Q01 conversion
    if len(q_id) == 2 and q_id[1].isdigit():
        padded = f"Q0{q_id[1]}"
        if padded in hops:
            return hops[padded]
    
    # If still not found, raise error with available keys
    available = ", ".join(sorted(hops.keys()))
    raise KeyError(f"Hop {q_id} not found in checklist. Available: {available}")


def _structure_rules(hop_data: Dict[str, Any], q_id: str) -> Dict[str, Any]:
    """Convert hop data into a structured JSON format."""
    # Get meta and content sections
    meta = hop_data.get("meta", {})
    content = hop_data.get("content", {})
    
    structured = {
        # Ensure hop_id always present – fall back to the explicit q_id if meta is missing
        "hop_id": meta.get("meta_id") or meta.get("id") or q_id,
        "frame": meta.get("frame", ""),
        "summary": meta.get("summary", ""),
        "quick_check": content.get("quick_check", ""),
        "patterns": {},
        "pattern_table": content.get("pattern_table", []),
        "rules": {
            "inclusion": [],
            "exclusion": [],
            "special": [],
            "precedence": []
        },
        "examples": {
            "positive": [],
            "negative": []
        },
        "guards": content.get("guards", []),
        "clarifications": content.get("clarifications", [])
    }
    
    # Process row_map into structured patterns
    row_map = content.get("row_map", meta.get("row_map", {}))
    for pattern_id, label in row_map.items():
        structured["patterns"][pattern_id] = {
            "id": pattern_id,
            "label": label,
            "active": True
        }
    
    # Process inclusion criteria
    inclusion = content.get("inclusion_criteria", [])
    if isinstance(inclusion, list):
        for rule in inclusion:
            if isinstance(rule, str):
                structured["rules"]["inclusion"].append({
                    "text": rule,
                    "type": "general"
                })
    
    # Process exclusion criteria
    exclusion = content.get("exclusion_criteria", [])
    if isinstance(exclusion, list):
        for rule in exclusion:
            if isinstance(rule, str):
                structured["rules"]["exclusion"].append({
                    "text": rule,
                    "type": "general"
                })
    
    # Process special rules
    special = content.get("special_rules", [])
    if isinstance(special, list):
        for rule in special:
            if isinstance(rule, str):
                structured["rules"]["special"].append({
                    "text": rule,
                    "type": "special"
                })
    
    # Process precedence rules
    precedence = content.get("precedence_rules", [])
    if isinstance(precedence, list):
        for rule in precedence:
            if isinstance(rule, str):
                structured["rules"]["precedence"].append({
                    "text": rule,
                    "type": "precedence"
                })
    
    # Process examples
    examples = content.get("examples", [])
    if isinstance(examples, list):
        for i, example in enumerate(examples):
            # --- CASE 1: Simple string (legacy) ----------------------------------
            if isinstance(example, str):
                bucket = "negative" if ("NON-EXAMPLE" in example or "Neutral" in example) else "positive"
                structured["examples"][bucket].append({
                    "text": example,
                    "explanation": "",
                    "patterns": []
                })

            # --- CASE 2: Already-structured dict provided in checklist ----------
            elif isinstance(example, dict):
                # Expected keys: text, label (pos/neg), explanation(optional)
                text_val = example.get("text", "")
                bucket = example.get("label", "positive").lower()
                bucket = "negative" if bucket.startswith("neg") else "positive"
                structured["examples"][bucket].append({
                    "text": text_val,
                    "explanation": example.get("explanation", ""),
                    "patterns": example.get("patterns", [])
                })
    
    return structured


def build_json_prompt(
    q_id: str,
    segment_text: str,
    statement_id: str = "",
    include_examples: bool = True,
    include_all_rules: bool = True
) -> str:
    """Build a fully parameterized JSON prompt for a specific hop."""
    # Load checklist
    checklist = _load_checklist()
    
    # Get hop data
    hop_data = _get_hop_entry(checklist, q_id)
    
    # Structure the rules
    structured_data = _structure_rules(hop_data, q_id)
    
    # Remove examples if not needed
    if not include_examples:
        structured_data["examples"] = {"positive": [], "negative": []}
    
    # Build the prompt
    prompt_parts = []
    
    # Add segment
    prompt_parts.append(f"### Segment (StatementID: {statement_id})")
    prompt_parts.append(segment_text)
    prompt_parts.append("")
    
    # Add question
    prompt_parts.append(f"### Question {q_id}")
    prompt_parts.append(hop_data.get("content", {}).get("question", f"Apply the rules for {q_id}"))
    prompt_parts.append("")
    
    # Add structured JSON data
    prompt_parts.append("### Rule Data (JSON)")
    prompt_parts.append("```json")
    prompt_parts.append(json.dumps(structured_data, indent=2))
    prompt_parts.append("```")
    prompt_parts.append("")
    
    # Add response format
    prompt_parts.append("### Response Format")
    prompt_parts.append("Return a JSON object with the following structure:")
    prompt_parts.append("```json")
    prompt_parts.append(json.dumps({
        "answer": "yes/no/uncertain",
        "rationale": "Your reasoning here",
        "cue_map": {
            "pattern_id": "label"
        },
        "confidence": 85,
        "frame_likelihoods": {
            "Alarmist": 70,
            "Neutral": 20,
            "Reassuring": 10
        }
    }, indent=2))
    prompt_parts.append("```")
    
    return "\n".join(prompt_parts)


def build_json_prompt_batch(
    q_id: str,
    segments: List[Dict[str, str]],
    include_examples: bool = True,
    group_size: int = 25
) -> str:
    """Build a batch JSON prompt for multiple segments."""
    # Load checklist
    checklist = _load_checklist()
    
    # Get hop data
    hop_data = _get_hop_entry(checklist, q_id)
    
    # Structure the rules
    structured_data = _structure_rules(hop_data, q_id)
    
    # Remove examples if not needed
    if not include_examples:
        structured_data["examples"] = {"positive": [], "negative": []}
    
    # Build the prompt
    prompt_parts = []
    
    # Add instruction
    prompt_parts.append("### Batch Analysis Task")
    prompt_parts.append(f"Analyze {len(segments)} segments for Question {q_id}")
    prompt_parts.append("")
    
    # Process segments in groups
    for i in range(0, len(segments), group_size):
        group = segments[i:i + group_size]
        
        # Add segments
        prompt_parts.append("### Segments")
        prompt_parts.append("```json")
        segment_data = []
        for seg in group:
            segment_data.append({
                "id": seg["statement_id"],
                "text": seg["text"]
            })
        prompt_parts.append(json.dumps(segment_data, indent=2))
        prompt_parts.append("```")
        prompt_parts.append("")
        
        # Add rule data
        prompt_parts.append("### Rule Data (JSON)")
        prompt_parts.append("```json")
        prompt_parts.append(json.dumps(structured_data, indent=2))
        prompt_parts.append("```")
        prompt_parts.append("")
    
    # Add response format
    prompt_parts.append("### Response Format")
    prompt_parts.append(f"Return a JSON array with {len(segments)} elements:")
    prompt_parts.append("```json")
    prompt_parts.append(json.dumps([{
        "segment_id": "exact_id_from_input",
        "answer": "yes/no/uncertain",
        "rationale": "Your reasoning",
        "cue_map": {"pattern_id": "label"},
        "confidence": 85,
        "frame_likelihoods": {"Alarmist": 70, "Neutral": 20, "Reassuring": 10}
    }], indent=2))
    prompt_parts.append("```")
    
    return "\n".join(prompt_parts) 