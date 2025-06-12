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

# Prefer the "regex" engine if available (supports variable-width look-behinds).
try:
    import regex as re  # type: ignore
except ImportError:  # pragma: no cover
    import re  # type: ignore
import logging
from typing import Optional, TypedDict
from collections import Counter, defaultdict

# Robust import that works whether this module is executed as part of the
# `multi_coder_analysis` package or as a loose script.
try:
    from .regex_rules import COMPILED_RULES, PatternInfo, RAW_RULES  # type: ignore
except ImportError:  # pragma: no cover
    # Fallback when the parent package context isn't available (e.g. the
    # file is imported directly via `python path/run_multi_coder_tot.py`).
    try:
        from regex_rules import COMPILED_RULES, PatternInfo, RAW_RULES  # type: ignore
    except ImportError:
        # Final attempt: assume package name is available
        from multi_coder_analysis.regex_rules import COMPILED_RULES, PatternInfo, RAW_RULES  # type: ignore

# ---------------------------------------------------------------------------
# Public typed structure returned to the pipeline when a rule fires
# ---------------------------------------------------------------------------
class Answer(TypedDict):
    answer: str
    rationale: str
    frame: Optional[str]
    regex: dict  # detailed match information


# ---------------------------------------------------------------------------
# Engine core
# ---------------------------------------------------------------------------

# Per-rule statistics
_RULE_STATS: dict[str, Counter] = defaultdict(Counter)  # name -> Counter(hit=, total=)

# Global switch (set at runtime via pipeline args)
_GLOBAL_ENABLE: bool = True
_FORCE_SHADOW: bool = False

def set_global_enabled(flag: bool) -> None:
    """Enable or disable regex matching globally (used for --regex-mode off)."""
    global _GLOBAL_ENABLE
    _GLOBAL_ENABLE = flag

def set_force_shadow(flag: bool) -> None:
    """When True, regex runs but never short-circuits (shadow mode)."""
    global _FORCE_SHADOW
    _FORCE_SHADOW = flag

def get_rule_stats() -> dict[str, Counter]:
    return _RULE_STATS

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

    if not _GLOBAL_ENABLE:
        return None

    # Fetch hop-specific rule list (already compiled)
    rules = COMPILED_RULES.get(hop, [])
    if not rules:
        return None

    winning_rule: Optional[PatternInfo] = None

    # Evaluate every rule to capture full coverage stats. Only allow
    # short-circuiting when ALL of the following hold:
    #   • the rule is in live mode
    #   • shadow-force flag is *not* active
    #   • exactly one live rule fires without ambiguity
    for rule in rules:
        fired = _rule_fires(rule, text)

        # --- Always update coverage counters ---
        _RULE_STATS[rule.name]["total"] += 1
        if fired:
            _RULE_STATS[rule.name]["hit"] += 1

        # --- Short-circuit only when permitted ---
        if (
            fired
            and not _FORCE_SHADOW  # shadow mode disables short-circuit altogether
            and (rule.mode == "live" or rule.mode == "shadow")
        ):
            if winning_rule is not None:
                # Multiple live rules fired ⇒ ambiguous → fall-through to LLM
                logging.debug(
                    "Regex engine ambiguity: >1 live rule fired for hop %s (%s, %s)",
                    hop,
                    winning_rule.name,
                    rule.name,
                )
                return None
            winning_rule = rule

    if winning_rule is None:
        # Record totals for live rules that did not fire (already counted)
        return None

    # Compute match object again to get span/captures (guaranteed match)
    m = winning_rule.yes_regex.search(text)  # type: ignore[arg-type]
    span = [m.start(), m.end()] if m else None
    captures = list(m.groups()) if m else []

    rationale = f"regex:{winning_rule.name} matched"
    return {
        "answer": "yes",
        "rationale": rationale,
        "frame": winning_rule.yes_frame,
        "regex": {
            "rule": winning_rule.name,
            "span": span,
            "captures": captures,
        },
    } 