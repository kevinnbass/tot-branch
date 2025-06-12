from __future__ import annotations

"""Light-weight conservative regex engine for the 12-hop Tree-of-Thought pipeline.

Usage
-----
>>> from regex_engine import match
>>> ans = match(ctx)
>>> if ans: ...

The engine stays **conservative**:
• Only rules marked `mode="live"` can short-circuit the LLM.
• If multiple live rules fire, or veto patterns trigger, we
  return `None` to defer to the LLM.
• We never attempt to prove a definite "no"; absence of a match
  or any ambiguity ⇒ fall-through.
"""

import logging
import time
import re
from typing import Optional, TypedDict, Any

from .regex_rules import COMPILED_RULES, PatternInfo  # local absolute import

# ---------------------------------------------------------------------------
# Public typed structure returned to the pipeline when a rule fires
# ---------------------------------------------------------------------------
class Answer(TypedDict):
    answer: str
    rationale: str
    frame: Optional[str]


# ---------------------------------------------------------------------------
# Engine core
# ---------------------------------------------------------------------------

def _rule_fires(rule: PatternInfo, text: str) -> bool:
    """Return True iff rule matches positively **and** is not vetoed."""
    # yes_regex is compiled already (see regex_rules.py)
    if not isinstance(rule.yes_regex, re.Pattern):
        logging.error("regex_rules COMPILED_RULES must contain compiled patterns")
        return False

    positive = bool(rule.yes_regex.search(text))
    if not positive:
        return False

    if rule.veto_regex and isinstance(rule.veto_regex, re.Pattern):
        if rule.veto_regex.search(text):
            return False
    return True


def match(ctx) -> Optional[Answer]:  # noqa: ANN001  (HopContext is dynamically typed)
    """Attempt to answer the current hop deterministically.

    Parameters
    ----------
    ctx : HopContext
        The current hop context (expects attributes: `q_idx`, `segment_text`).

    Returns
    -------
    Optional[Answer]
        • Dict with keys {answer, rationale, frame} when a *single* live rule
          fires with certainty.
        • None when no rule (or >1 rules) fire, or hop not covered, or rule is
          in shadow mode.
    """

    hop: int = getattr(ctx, "q_idx")
    text: str = getattr(ctx, "segment_text")

    # Fetch hop-specific rule list (already compiled)
    rules = COMPILED_RULES.get(hop, [])
    if not rules:
        return None

    winning_rule: Optional[PatternInfo] = None

    for rule in rules:
        if rule.mode != "live":
            continue  # conservative: ignore shadow rules

        if _rule_fires(rule, text):
            if winning_rule is not None:
                # Multiple rules fired ⇒ ambiguous → fall-through to LLM
                logging.debug(
                    "Regex engine ambiguity: >1 rule fired for hop %s (%s, %s)",
                    hop,
                    winning_rule.name,
                    rule.name,
                )
                return None
            winning_rule = rule

    if winning_rule is None:
        return None

    rationale = f"regex:{winning_rule.name} matched"
    return {
        "answer": "yes",
        "rationale": rationale,
        "frame": winning_rule.yes_frame,
    } 