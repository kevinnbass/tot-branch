"""Machine-readable JSON Prompt Builder (loss-less version)."""

import json
from pathlib import Path
from typing import Dict, Any, List

MACHINE_DIR = Path(__file__).parent.parent / "prompts" / "cue_detection" / "machine"

# ---------------------------------------------------------------------------
# Helper loaders
# ---------------------------------------------------------------------------

def _load_hop_data(q_id: str) -> Dict[str, Any]:
    """Load hop-specific JSON (already contains full definitions/examples)."""
    hop_path = MACHINE_DIR / f"{q_id}.json"
    if not hop_path.exists():
        raise FileNotFoundError(f"Hop file not found at {hop_path}")
    with hop_path.open("r", encoding="utf-8") as f:
        return json.load(f)

# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------

def _normalise_qid(q_id: str) -> str:
    q_id = q_id.upper().removeprefix("Q")
    return f"Q{int(q_id):02d}"


def build_json_prompt_machine(
    q_id: str,
    segment_text: str,
    statement_id: str,
    *,
    include_examples: bool = True,
) -> str:
    """Return loss-less machine prompt for a single segment."""
    q_id = _normalise_qid(q_id)
    hop = _load_hop_data(q_id)

    # Assemble prompt object (copy shallow to keep original intact)
    data: Dict[str, Any] = {
        "h": q_id,
        "f": hop["frame"][0],  # first letter A / N / R
        "frame": hop["frame"],  # full frame label, e.g. "Alarmist"
        "p": hop["patterns"],
        "r": hop["rules"],
        "d": hop["definitions"],  # full rule bodies
        "quick_check": hop.get("quick_check", {}),
        "g": hop.get("guards", []),
        "c": hop.get("constraints", []),
        "seg": {"id": statement_id, "txt": segment_text},
    }
    if include_examples and hop.get("examples"):
        data["e"] = hop["examples"]  # {positive/negative}

    prompt_lines = [
        f"[{statement_id}] {segment_text}",
        "",
        f"Apply {q_id} rules:",
        "",
        json.dumps(data, ensure_ascii=False, separators=(',', ':')),
        "",
        'Reply: {"a":"yes/no/uncertain","r":"<why>","c":{"pattern_id":"label"}}'
    ]
    return "\n".join(prompt_lines)


def build_json_prompt_batch_machine(
    q_id: str,
    segments: List[Dict[str, str]],
    *,
    include_examples: bool = True,
    group_size: int = 25,
) -> str:
    q_id = _normalise_qid(q_id)
    hop = _load_hop_data(q_id)

    # Common rule payload
    rule_blob = {
        "h": q_id,
        "f": hop["frame"][0],
        "frame": hop["frame"],
        "p": hop["patterns"],
        "r": hop["rules"],
        "d": hop["definitions"],
        "quick_check": hop.get("quick_check", {}),
        "g": hop.get("guards", []),
        "c": hop.get("constraints", []),
    }
    if include_examples and hop.get("examples"):
        rule_blob["e"] = hop["examples"]

    # Build segment batches
    batches: List[str] = []
    for i in range(0, len(segments), group_size):
        chunk = segments[i:i + group_size]
        seg_arr = [[s["statement_id"], s["text"]] for s in chunk]
        batches.append(json.dumps(seg_arr, ensure_ascii=False, separators=(',', ':')))
    
    prompt_parts = [f"Apply {q_id} rules across {len(segments)} segments."]
    for idx, b in enumerate(batches, 1):
        prompt_parts.extend([f"Batch {idx}:", b, ""])
    prompt_parts.append(json.dumps(rule_blob, ensure_ascii=False, separators=(',', ':')))
    prompt_parts.append("")
    prompt_parts.append(f'Reply: [{len(segments)} x {{"id":"<id>","a":"yes/no/uncertain","r":"<why>","c":{{}}}}]')
    return "\n".join(prompt_parts)


# Compatibility wrapper to match existing interface
def build_json_prompt(
    q_id: str,
    segment_text: str,
    statement_id: str = "",
    include_examples: bool = True,
    include_all_rules: bool = True
) -> str:
    """Compatibility wrapper for machine format."""
    return build_json_prompt_machine(
        q_id=q_id,
        segment_text=segment_text,
        statement_id=statement_id,
        include_examples=include_examples,
    )


def build_json_prompt_batch(
    q_id: str,
    segments: List[Dict[str, str]],
    include_examples: bool = True,
    group_size: int = 25
) -> str:
    """Compatibility wrapper for batch machine format."""
    return build_json_prompt_batch_machine(
        q_id=q_id,
        segments=segments,
        include_examples=include_examples,
        group_size=group_size
    ) 