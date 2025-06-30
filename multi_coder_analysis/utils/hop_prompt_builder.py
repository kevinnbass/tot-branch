from __future__ import annotations

"""hop_prompt_builder
=====================
Generate a **self-contained hop prompt** for cue-detection.

The helper reads the canonical rules from
``multi_coder_analysis/prompts/cue_detection/enhanced_checklist_v2.json`` and
injects the rule slice (row_map, quick_check, criteria, examples, …) right after
the short question block so that it stays close to the LLM's prediction point.
This avoids information loss that occurs when rules sit thousands of tokens
away in very long prompts or batch calls.

Example
-------
>>> from multi_coder_analysis.utils.hop_prompt_builder import build_prompt
>>> prompt = build_prompt("Q3", "The virus swept across three states, …")
>>> print(prompt[:300])  # doctest: +ELLIPSIS
---
meta_id: Q03
frame: Alarmist
summary: "Moderate verbs + scale/impact"
---
### Segment (StatementID: {statement_id})
The virus swept across three states, …

### Question Q03
Does the segment trigger any of the patterns listed below?  \
If yes and no exclusions apply, answer "yes"; otherwise "no".
"""

from pathlib import Path
from typing import Dict, Any
import json
import textwrap

__all__ = ["build_prompt"]

# ---------------------------------------------------------------------------
# Defaults & helpers
# ---------------------------------------------------------------------------

_DEFAULT_CHECKLIST = (
    Path(__file__).resolve().parent.parent
    / "prompts"
    / "cue_detection"
    / "enhanced_checklist_v2.json"
)

_ESSENTIAL_KEYS = [
    # Complete list for loss-less prompt slices
    "row_map",            # canonical pattern→label map
    "quick_check",        # concise heuristic
    "inclusion_criteria", # positive rules
    "exclusion_criteria", # negative rules / guards
    "examples",           # illustrative examples
    "special_rules",      # hop-specific caveats (distance, precedence…)
    "pattern_table",      # tabular summary (was previously omitted)
    "guards",             # technical / taxonomy guards
    "clarifications",     # additional prose explanations
    "precedence_rules",   # explicit precedence notes
    "technical_notes",    # extra implementation notes
    "raw_sections",       # untouched markdown blocks (if any)
]


def _load_checklist(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Checklist not found at {path}") from e
    except json.JSONDecodeError as e:
        raise ValueError(f"Checklist at {path} is not valid JSON: {e}") from e


def _get_hop_entry(ck: Dict[str, Any], q_id: str) -> Dict[str, Any]:
    """Return hop entry allowing for both padded (Q01) and non-padded (Q1) keys."""
    hops = ck.get("hops", {})
    if q_id in hops:
        return hops[q_id]

    # Fallback: try non-padded representation (e.g. Q1)
    if q_id.startswith("Q0") and len(q_id) == 3:
        q_id_unpad = "Q" + q_id[2]
        if q_id_unpad in hops:
            return hops[q_id_unpad]

    # Also attempt padded version if non-padded requested
    if len(q_id) == 2 and q_id[1].isdigit():
        q_id_pad = f"Q{int(q_id[1]):02d}"
        if q_id_pad in hops:
            return hops[q_id_pad]

    valid = ", ".join(sorted(hops.keys()))
    raise KeyError(f"Hop {q_id} not in checklist. Valid keys: {valid}")


def _trim_examples(content: Dict[str, Any]) -> Dict[str, Any]:
    if "examples" in content and isinstance(content["examples"], list):
        if len(content["examples"]) > 3:
            new_c = dict(content)
            new_c["examples"] = content["examples"][:3]
            return new_c
    return content


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_prompt(
    q_id: str,
    segment_text: str,
    *,
    statement_id: str | None = None,
    checklist_path: str | Path | None = None,
    include_examples: bool | None = None,
    fmt: str = "markdown",
    examples_policy: str = "full",
) -> str:
    """Return a fully formatted prompt for *q_id* and *segment_text*.

    Parameters
    ----------
    q_id
        Hop ID ("Q1"–"Q12", case-insensitive; leading "Q" optional).
    segment_text
        The raw text of the segment to annotate.
    statement_id
        Concrete ID or *None* to keep the ``{statement_id}`` placeholder.
    checklist_path
        Optional alternative path to the checklist JSON.
    include_examples
        Deprecated.  If provided, overrides *examples_policy* (``True`` → "full", ``False`` → "trim").
    fmt
        Currently only "markdown" is supported.  Parameter reserved for future JSON/XML support.
    examples_policy
        "full" (keep all examples – default), "trim" (keep first 3), or "none" (omit the array).
    """
    # Normalise q_id → "Q03"
    q_id_norm = q_id.upper().lstrip("Q")
    if not q_id_norm.isdigit() or not (1 <= int(q_id_norm) <= 12):
        raise ValueError("q_id must be between Q1 and Q12")
    q_id_fmt = f"Q{int(q_id_norm):02d}"

    ck_path = Path(checklist_path) if checklist_path else _DEFAULT_CHECKLIST
    checklist = _load_checklist(ck_path)
    hop_entry = _get_hop_entry(checklist, q_id_fmt)

    meta = hop_entry.get("meta", {})
    content = hop_entry.get("content", {})

    # Back-compat: map *include_examples* into examples_policy when caller still uses it
    if include_examples is not None:
        examples_policy = "full" if include_examples else "trim"

    if examples_policy not in {"full", "trim", "none"}:
        raise ValueError("examples_policy must be 'full', 'trim', or 'none'")

    if examples_policy == "trim":
        content = _trim_examples(content)
    elif examples_policy == "none":
        # Remove the key entirely first, then ensure empty list later for JSON stability
        content = dict(content)
        content.pop("examples", None)

    # Ensure essential keys always present (insert empty list/dict as needed)
    for key in _ESSENTIAL_KEYS:
        content.setdefault(key, [] if key.endswith("criteria") or key == "examples" else {})

    slice_dict = {k: content.get(k, [] if k == "examples" else {}) for k in _ESSENTIAL_KEYS}
    if "examples" not in slice_dict:
        slice_dict["examples"] = []

    slice_json = json.dumps(slice_dict, ensure_ascii=False, indent=2)

    stmt_id_placeholder = statement_id if statement_id is not None else "{statement_id}"

    if fmt != "markdown":
        raise NotImplementedError("Only markdown output is currently supported by build_prompt")

    prompt = textwrap.dedent(
        f"""
        ---
        meta_id: {q_id_fmt}
        frame: {meta.get('frame', '')}
        summary: "{meta.get('summary', '').replace('"', '\"')}"
        ---
        ### Segment (StatementID: {stmt_id_placeholder})
        {segment_text}

        ### Question {q_id_fmt}
        Does the segment trigger any of the patterns listed below?  \
        If yes and no exclusions apply, answer "yes"; otherwise "no".

        When you reply **first output a `cue_map` object** listing each pattern
        in `row_map` with a boolean string value (`"yes"` or `"no"`).  Then
        output `answer` and `rationale`.

        ### {q_id_fmt} Rule Slice (checklist v2)
        ```json
        {slice_json}
        ```
        ### Your JSON reply
        ```json
        {{
          "cue_map": {{
            // keys from row_map, e.g. "{list(content.get('row_map', {}).keys())[0] if content.get('row_map') else 'Qx.y'}": "yes|no",
            // ...
          }},
          "answer": "yes|no|uncertain",
          "rationale": "<max 80 tokens – quote the decisive cue(s) if yes>"
        }}
        ```
        """
    ).strip()

    return prompt 