#  Auto-generated / hand-curated regex rules for deterministic hops.
#  Only absolutely unambiguous YES cues should live here.
#  If a rule matches, we answer "yes"; otherwise we defer to the LLM.
#  Initially we seed with a handful of high-precision patterns — extend via
#  the audit script.

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Dict, Pattern, Optional
from pathlib import Path

__all__ = [
    "PatternInfo",
    "RAW_RULES",
    "COMPILED_RULES",
]

@dataclass(frozen=True)
class PatternInfo:
    """Metadata + raw patterns for a single hop-specific rule.

    Attributes
    ----------
    hop: int
        Hop/question index (1-12).
    name: str
        Descriptive identifier (CamelCase).
    yes_frame: str | None
        Frame name to override when rule fires (e.g. "Alarmist").
    yes_regex: str
        Raw regex that, when **present**, guarantees the answer is "yes".
    veto_regex: str | None
        Optional regex that, when present, *cancels* an otherwise positive
        match — useful for conservative disambiguation.
    mode: str
        "live"  – rule is active and may short-circuit the LLM.
        "shadow" – rule only logs and will *not* short-circuit.
    """

    hop: int
    name: str
    yes_frame: Optional[str]
    yes_regex: str
    veto_regex: Optional[str] = None
    mode: str = "live"


# ----------------------------------------------------------------------------
# Raw rule list – ***KEEP EXTREMELY HIGH PRECISION***
# ----------------------------------------------------------------------------
RAW_RULES: List[PatternInfo] = [
    # Alarmist high-certainty cues
    PatternInfo(
        hop=1,
        name="Q1.DeadlyIntensifier",
        yes_frame="Alarmist",
        yes_regex=r"\b(extremely|highly|very)\s+(deadly|lethal|dangerous)\b",
    ),
    PatternInfo(
        hop=2,
        name="Q2.VividVerbRavaged",
        yes_frame="Alarmist",
        yes_regex=r"\bravaged\b",
    ),

    # Reassuring cues
    PatternInfo(
        hop=5,
        name="Q5.UnderControl",
        yes_frame="Reassuring",
        yes_regex=r"\bfully\s+under\s+control\b",
    ),
    PatternInfo(
        hop=6,
        name="Q6.OnlyFewCases",
        yes_frame="Reassuring",
        yes_regex=r"\b(?:only|just)\s+\d+\s+cases\b",
    ),
]


# ----------------------------------------------------------------------------
# Compile rules per hop for fast lookup
# ----------------------------------------------------------------------------
COMPILED_RULES: Dict[int, List[PatternInfo]] = {}
for rule in RAW_RULES:
    compiled_yes: Pattern = re.compile(rule.yes_regex, flags=re.I | re.UNICODE)
    compiled_veto: Optional[Pattern] = None
    if rule.veto_regex:
        compiled_veto = re.compile(rule.veto_regex, flags=re.I | re.UNICODE)

    # Replace raw strings with compiled patterns via object copy
    compiled_rule = PatternInfo(
        hop=rule.hop,
        name=rule.name,
        yes_frame=rule.yes_frame,
        yes_regex=compiled_yes,  # type: ignore[arg-type]
        veto_regex=compiled_veto,  # type: ignore[arg-type]
        mode=rule.mode,
    )

    COMPILED_RULES.setdefault(rule.hop, []).append(compiled_rule)


# ----------------------------------------------------------------------------
# Auto-extract additional patterns from the hop prompt files (optional).
# This scans multi_coder_analysis/prompts/hop_Q*.txt for ```regex ... ``` blocks
# and turns them into conservative PatternInfo objects (mode="shadow" by default)
# so they won't short-circuit unless promoted to live.
# ----------------------------------------------------------------------------

PROMPTS_DIR = Path(__file__).parent / "prompts"

_HOP_FILE_RE = re.compile(r"hop_Q(\d{2})\.txt")

def _infer_frame_from_hop(hop: int) -> str | None:
    if hop in {1, 2, 3, 4}:
        return "Alarmist"
    if hop in {5, 6}:
        return "Reassuring"
    return None  # leave to downstream logic


def _extract_patterns_from_prompts() -> list[PatternInfo]:
    patterns: list[PatternInfo] = []

    if not PROMPTS_DIR.exists():
        return patterns

    for path in PROMPTS_DIR.glob("hop_Q*.txt"):
        m = _HOP_FILE_RE.match(path.name)
        if not m:
            continue
        hop_idx = int(m.group(1))

        try:
            txt = path.read_text(encoding="utf-8")
        except Exception:
            continue

        # find fenced regex blocks
        for idx, block in enumerate(re.findall(r"```regex\s+([\s\S]*?)```", txt)):
            raw = block.strip()
            # super-conservative: skip if pattern seems empty or has lookbehinds (?<)
            if not raw or "?<-" in raw:
                continue

            name = f"Q{hop_idx:02}.Prompt#{idx+1}"

            patterns.append(
                PatternInfo(
                    hop=hop_idx,
                    name=name,
                    yes_frame=_infer_frame_from_hop(hop_idx),
                    yes_regex=raw,
                    mode="shadow",  # start in shadow mode for safety
                )
            )

    return patterns


# Integrate extracted patterns (shadow mode) ------------------------------------------------
RAW_RULES.extend(_extract_patterns_from_prompts())

# Re-compile dictionary with new additions
COMPILED_RULES.clear()
for rule in RAW_RULES:
    compiled_yes = re.compile(rule.yes_regex, flags=re.I | re.UNICODE)
    compiled_veto = re.compile(rule.veto_regex, flags=re.I | re.UNICODE) if rule.veto_regex else None
    COMPILED_RULES.setdefault(rule.hop, []).append(
        PatternInfo(
            hop=rule.hop,
            name=rule.name,
            yes_frame=rule.yes_frame,
            yes_regex=compiled_yes,  # type: ignore[arg-type]
            veto_regex=compiled_veto,  # type: ignore[arg-type]
            mode=rule.mode,
        )
    ) 