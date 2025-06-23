"""
Data container for a single segment's journey through the 12-hop Tree-of-Thought chain.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import sys as _sys  # Compatibility shim needs sys access

# ---------------------------------------------------------------------------
# Compatibility shim ---------------------------------------------------------
# Some legacy (and current) code does:
#     import hop_context
# *before* the package root has been imported.  To keep that working we
# register *this* module object under the bare name **immediately**.
# ---------------------------------------------------------------------------
if "hop_context" not in _sys.modules:  # pragma: no cover – infrastructure only
    _sys.modules["hop_context"] = _sys.modules[__name__]
# ---------------------------------------------------------------------------

import warnings as _warnings
from importlib import import_module as _import_module

_warnings.warn(
    "`hop_context` is deprecated; please import from `multi_coder_analysis.models` instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export everything from the new canonical location
_new_mod = _import_module("multi_coder_analysis.models.hop")
globals().update(_new_mod.__dict__)

__all__ = _new_mod.__all__

@dataclass
class HopContext:
    """
    Manages the state for a single text segment as it progresses through the 12-hop ToT chain.
    """
    # -------------- Static Data --------------
    statement_id: str
    segment_text: str
    # Optional article identifier (source document) – used for trace exports
    article_id: Optional[str] = None

    # -------------- Dynamic State --------------
    q_idx: int = 0
    is_concluded: bool = False
    final_frame: Optional[str] = None           # The definitive frame once concluded (e.g., Alarmist, Neutral)
    final_justification: Optional[str] = None   # The rationale for the final decision
    
    # NEW: Track how many consecutive 'uncertain' responses we have seen so far. This is
    # used by run_multi_coder_tot.py to decide when to terminate early (after 3). Adding
    # it here prevents attribute-access crashes observed during batch processing.
    uncertain_count: int = 0

    # -------------- Logging & Audit Trails --------------
    analysis_history: List[str] = field(default_factory=list)      # Human-readable log (e.g., "Q1: no")
    reasoning_trace: List[Dict] = field(default_factory=list)      # Machine-readable JSON for replay/debug
    raw_llm_responses: List[Dict] = field(default_factory=list)    # Raw, unparsed LLM responses per hop

    # ───────── Batch Positional Meta (populated when segments are processed in a batch) ─────────
    # 1-based index of this segment within its API call (or 1 when processed individually)
    batch_pos: Optional[int] = None
    # Total number of segments in that API call (or 1 when processed individually)
    batch_size: Optional[int] = None

    # -------------- Parsed prompt metadata (from YAML front-matter) --------------
    prompt_meta: Dict[str, Any] = field(default_factory=dict, repr=False)

    # -------------- Convenience Properties for Downstream Compatibility --------------
    @property
    def dim1_frame(self) -> Optional[str]:
        """Alias used by downstream merge/stats scripts."""
        return self.final_frame 

@dataclass
class BatchHopContext:
    """Container for a batch of segments being processed together at a single hop."""
    batch_id: str
    hop_idx: int
    segments: List[HopContext]  # The HopContext objects inside this batch

    # Raw LLM I/O for debugging
    raw_prompt: str = ""
    raw_response: str = ""
    thoughts: Optional[str] = None 