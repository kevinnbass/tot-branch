from __future__ import annotations

"""Backward compatibility shim for regex_engine module.

This module re-exports everything from multi_coder_analysis.core.regex.engine
to maintain compatibility with existing code.
"""

import warnings

warnings.warn(
    "`regex_engine` is deprecated; use `multi_coder_analysis.core.regex` instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export everything from the new location
from multi_coder_analysis.core.regex.engine import *  # noqa: F401,F403

# Specific re-exports for common usage patterns
from multi_coder_analysis.core.regex.engine import (
    Engine,
    Answer,
    match,
    set_global_enabled,
    set_force_shadow,
    get_rule_stats,
    set_hit_logger,
    _GLOBAL_ENABLE,
    _FORCE_SHADOW,
    _HIT_LOG_FN,
)

__all__ = [
    "Engine",
    "Answer", 
    "match",
    "set_global_enabled",
    "set_force_shadow", 
    "get_rule_stats",
    "set_hit_logger",
] 