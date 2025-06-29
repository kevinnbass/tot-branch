from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, TypedDict

__all__ = [
    "HopContext",
    "BatchHopContext",
]

# ---------------------------------------------------------------------------
# Typed aliases help downstream static analysis without dict[str, Any] noise.
# ---------------------------------------------------------------------------
AnalysisHistory = List[str]
ReasoningTrace = List[Dict[str, Any]]
RawLLMResponses = List[Dict[str, Any]]


@dataclass
class HopContext:
    """State container for a single segment as it progresses through the 12-hop ToT chain."""

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
    ranking: Optional[list[str]] = None         # ordered list when ranked_list=True

    # Track consecutive "uncertain" responses to support early termination.
    uncertain_count: int = 0

    # -------------- Confidence-Enhanced RLSC Fields --------------
    confidence_score: Optional[float] = None   # Confidence score 0-100 for binary decision
    frame_likelihoods: Optional[Dict[str, float]] = None  # Frame likelihood percentages (Alarmist, Neutral, Reassuring)

    # -------------- Logging & Audit Trails --------------
    analysis_history: AnalysisHistory = field(default_factory=list)
    reasoning_trace: ReasoningTrace = field(default_factory=list)
    raw_llm_responses: RawLLMResponses = field(default_factory=list)

    # ───────── Batch Positional Meta ─────────
    batch_pos: Optional[int] = None  # 1-based index within API call
    batch_size: Optional[int] = None  # total number of segments in API call

    # -------------- Parsed prompt metadata --------------
    prompt_meta: Dict[str, Any] = field(default_factory=dict, repr=False)

    # ───────── Permutation bookkeeping ─────────
    permutation_idx: int | None = None

    # -------------- Convenience Properties --------------
    @property
    def dim1_frame(self) -> Optional[str]:
        """Alias retained for backward compatibility with downstream scripts."""
        return self.final_frame


@dataclass
class BatchHopContext:
    """Container for a batch of segments processed together at a single hop."""

    batch_id: str
    hop_idx: int
    segments: List[HopContext]

    # Raw LLM I/O for debugging
    raw_prompt: str = ""
    raw_response: str = ""
    thoughts: Optional[str] = None 