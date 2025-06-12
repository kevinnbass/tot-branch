"""
Data container for a single segment's journey through the 12-hop Tree-of-Thought chain.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

@dataclass
class HopContext:
    """
    Manages the state for a single text segment as it progresses through the 12-hop ToT chain.
    """
    # -------------- Static Data --------------
    statement_id: str
    segment_text: str

    # -------------- Dynamic State --------------
    q_idx: int = 0
    is_concluded: bool = False
    final_frame: Optional[str] = None           # The definitive frame once concluded (e.g., Alarmist, Neutral)
    final_justification: Optional[str] = None   # The rationale for the final decision

    # -------------- Logging & Audit Trails --------------
    analysis_history: List[str] = field(default_factory=list)      # Human-readable log (e.g., "Q1: no")
    reasoning_trace: List[Dict] = field(default_factory=list)      # Machine-readable JSON for replay/debug
    raw_llm_responses: List[Dict] = field(default_factory=list)    # Raw, unparsed LLM responses per hop

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