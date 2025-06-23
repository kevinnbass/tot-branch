from __future__ import annotations

"""Class-based regex engine for the 12-hop Tree-of-Thought pipeline.

The Engine class encapsulates regex matching logic as a stateless, first-class
object that can be instantiated with different rule sets.
"""

# Prefer the "regex" engine if available (supports variable-width look-behinds).
try:
    import regex as re  # type: ignore
except ImportError:  # pragma: no cover
    import re  # type: ignore

import logging
from typing import Optional, TypedDict, Callable
from collections import Counter
import threading
import importlib

# Import rules - handle both package and script contexts
try:
    from ...regex_rules import COMPILED_RULES, PatternInfo, RAW_RULES  # type: ignore
except ImportError:  # pragma: no cover
    try:
        from multi_coder_analysis.regex_rules import COMPILED_RULES, PatternInfo, RAW_RULES  # type: ignore
    except ImportError:
        # Final fallback for script execution
        from regex_rules import COMPILED_RULES, PatternInfo, RAW_RULES  # type: ignore

__all__ = ["Engine", "Answer"]


class Answer(TypedDict):
    """Typed structure returned when a regex rule fires."""
    answer: str
    rationale: str
    frame: Optional[str]
    regex: dict  # detailed match information


class Engine:
    """Stateless regex matching engine with configurable rule sets.
    
    Each Engine instance encapsulates its own rule statistics and configuration,
    enabling multiple engines with different behaviors to coexist.
    """
    
    # Class-level singleton for the default engine
    _DEFAULT: Optional["Engine"] = None
    
    def __init__(
        self,
        rules: Optional[dict[int, list[PatternInfo]]] = None,
        global_enabled: bool = True,
        force_shadow: bool = False,
        hit_logger: Optional[Callable[[dict], None]] = None,
    ):
        """Initialize a new Engine instance.
        
        Args:
            rules: Hop -> PatternInfo mapping. If None, uses COMPILED_RULES.
            global_enabled: Whether regex matching is enabled.
            force_shadow: If True, regex runs but never short-circuits.
            hit_logger: Optional callback for successful matches.
        """
        self._rules = rules if rules is not None else COMPILED_RULES
        self._global_enabled = global_enabled
        self._force_shadow = force_shadow
        self._hit_logger = hit_logger
        self._rule_stats: dict[str, Counter] = {}
        self._stat_lock = threading.Lock()
    
    @classmethod
    def default(cls) -> "Engine":
        """Get the default singleton Engine instance.
        
        This provides backward compatibility with the module-level API.
        """
        if cls._DEFAULT is None:
            cls._DEFAULT = cls()
        return cls._DEFAULT
    
    def set_global_enabled(self, flag: bool) -> None:
        """Enable or disable regex matching globally."""
        self._global_enabled = flag
    
    def set_force_shadow(self, flag: bool) -> None:
        """When True, regex runs but never short-circuits (shadow mode)."""
        self._force_shadow = flag
    
    def set_hit_logger(self, fn: Optional[Callable[[dict], None]]) -> None:
        """Register a callback to receive detailed match information."""
        self._hit_logger = fn
    
    def get_rule_stats(self) -> dict[str, Counter]:
        """Get per-rule statistics for this engine instance."""
        return dict(self._rule_stats)
    
    def _rule_fires(self, rule: PatternInfo, text: str) -> bool:
        """Return True iff rule matches positively and is not vetoed."""
        if not isinstance(rule.yes_regex, re.Pattern):
            logging.error("COMPILED_RULES must contain compiled patterns")
            return False

        positive = bool(rule.yes_regex.search(text))
        if not positive:
            return False

        if rule.veto_regex and isinstance(rule.veto_regex, re.Pattern):
            if rule.veto_regex.search(text):
                return False
        return True
    
    def match(self, ctx) -> Optional[Answer]:  # noqa: ANN001
        """Attempt to answer the current hop deterministically.

        Parameters
        ----------
        ctx : HopContext
            The current hop context (expects attributes: `q_idx`, `segment_text`).

        Returns
        -------
        Optional[Answer]
            • Dict with keys {answer, rationale, frame} when a single live rule
              fires with certainty.
            • None when no rule (or >1 rules) fire, or hop not covered, or rule is
              in shadow mode.
        """
        hop: int = getattr(ctx, "q_idx")
        text: str = getattr(ctx, "segment_text")

        if not self._global_enabled:
            return None

        rules = self._rules.get(hop, [])
        if not rules:
            # Try lazy reload for robustness
            try:
                from ... import regex_rules as _rr  # type: ignore
                importlib.reload(_rr)
                rules = _rr.COMPILED_RULES.get(hop, [])
            except Exception:  # pragma: no cover
                rules = []

        if not rules:
            return None

        # Safety net: merge missing canonical rules
        try:
            from ... import regex_rules as _rr  # package context
        except ImportError:  # script context
            try:
                from multi_coder_analysis import regex_rules as _rr  # type: ignore
            except ImportError:
                import regex_rules as _rr  # type: ignore

        _master_rules = _rr.COMPILED_RULES.get(hop, [])
        if _master_rules:
            existing_names = {r.name for r in rules}
            for _r in _master_rules:
                if _r.name not in existing_names:
                    rules.append(_r)

        winning_rule: Optional[PatternInfo] = None
        first_hit_rule: Optional[PatternInfo] = None

        # Evaluate every rule for statistics
        for rule in rules:
            fired = self._rule_fires(rule, text)

            # Thread-safe stats update
            with self._stat_lock:
                ctr = self._rule_stats.setdefault(rule.name, Counter())
                ctr["total"] += 1
                if fired:
                    ctr["hit"] += 1

            # Record first hit for shadow-mode logging
            if fired and first_hit_rule is None:
                first_hit_rule = rule

            if (
                fired
                and not self._force_shadow
                and (rule.mode == "live" or rule.mode == "shadow")
            ):
                if winning_rule is not None:
                    # Tolerate multiple hits if they agree on frame
                    if rule.yes_frame == winning_rule.yes_frame:
                        continue

                    # Conflicting frames → fall-through to LLM
                    logging.debug(
                        "Regex engine ambiguity: >1 conflicting rule fired for hop %s (%s vs %s)",
                        hop,
                        winning_rule.name,
                        rule.name,
                    )
                    return None
                winning_rule = rule

        # Shadow-mode logging
        if winning_rule is None:
            logging.debug("No regex rule matched for hop %s", hop)

            # shadow mode accounting
            from multi_coder_analysis.providers.base import _USAGE_ACCUMULATOR as _ACC  # avoid cycle
            _ACC["total_hops"] = _ACC.get("total_hops", 0) + 1
            if self._force_shadow:
                _ACC["regex_hit_shadow"] = _ACC.get("regex_hit_shadow", 0) + 1

            return None

        # ---- counters ----
        from multi_coder_analysis.providers.base import _USAGE_ACCUMULATOR as _ACC  # local import
        _ACC["regex_yes"] = _ACC.get("regex_yes", 0) + 1
        _ACC["total_hops"] = _ACC.get("total_hops", 0) + 1

        # Compute match details
        m = winning_rule.yes_regex.search(text)  # type: ignore[arg-type]
        span = [m.start(), m.end()] if m else None
        captures = list(m.groups()) if m else []

        rationale = f"regex:{winning_rule.name} matched"

        # Emit hit record
        if self._hit_logger is not None:
            try:
                self._hit_logger({
                    "statement_id": getattr(ctx, "statement_id", None),
                    "hop": hop,
                    "segment": text,
                    "rule": winning_rule.name,
                    "frame": winning_rule.yes_frame,
                    "mode": winning_rule.mode,
                    "span": span,
                })
            except Exception as e:  # pragma: no cover
                logging.debug("Regex hit logger raised error: %s", e, exc_info=True)

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


# Backward compatibility: module-level functions delegate to default engine
def match(ctx) -> Optional[Answer]:  # noqa: ANN001
    """Backward compatibility function - delegates to Engine.default().match()."""
    return Engine.default().match(ctx)


def set_global_enabled(flag: bool) -> None:
    """Backward compatibility function."""
    Engine.default().set_global_enabled(flag)


def set_force_shadow(flag: bool) -> None:
    """Backward compatibility function."""
    Engine.default().set_force_shadow(flag)


def get_rule_stats() -> dict[str, Counter]:
    """Backward compatibility function."""
    return Engine.default().get_rule_stats()


def set_hit_logger(fn: Callable[[dict], None]) -> None:
    """Backward compatibility function."""
    Engine.default().set_hit_logger(fn)


# Expose module-level globals for backward compatibility
_GLOBAL_ENABLE = True
_FORCE_SHADOW = False
_HIT_LOG_FN: Optional[Callable[[dict], None]] = None 