"""
Deterministic 12-hop Tree-of-Thought (ToT) coder.
This module is an alternative to run_multi_coder.py and is activated via --use-tot.
It processes an input CSV of statements through a sequential, rule-based reasoning
chain, producing a single, deterministic label for each statement.
"""
from __future__ import annotations
import json
import time
import logging
import os
from pathlib import Path
from typing import Generator, Callable,  Dict, Any, List, Tuple, Optional
from datetime import datetime
from collections import defaultdict
import collections
import re
import random  # For optional shuffling of segments before batching
import warnings  # added near top

import pandas as pd
from tqdm import tqdm
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import shutil
import uuid

# Add missing regex engine import
from multi_coder_analysis.core.regex import Engine as RegexEngine

# Default constants
DEFAULT_MODEL = "models/gemini-2.0-flash-exp"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_BATCH_SIZE = 10
VALID_LAYOUTS = [
    'standard', 'recency', 'sandwich', 'minimal_system', 'question_first',
    # New high-yield layouts
    'hop_last', 'structured_json', 'segment_focus', 'instruction_first',
    'parallel_analysis', 'evidence_based', 'xml_structured', 'primacy_recency',
    # Minimal system variations for Phase 1 experiments
    'minimal_segment_first', 'minimal_question_twice', 'minimal_json_segment',
    'minimal_parallel_criteria', 'minimal_hop_sandwich',
    # --- NEW cue-detection experiment ---
    'cue_detection',
    # --- Enhanced cue detection with complete checklist ---
    'cue_detection_enhanced',
    # --- Enhanced cue detection in batch mode ---
    'cue_detection_enhanced_batch',
    # --- NEW: Fully parameterized JSON layouts ---
    'cue_detection_enhanced_json',
    'cue_detection_enhanced_json_batch',
    # --- NEW: Machine-readable ultra-compact layouts ---
    'cue_detection_enhanced_machine',
    'cue_detection_enhanced_machine_batch'
]

# Local project imports
from hop_context import HopContext, BatchHopContext
from multi_coder_analysis.models import HopContext, BatchHopContext
from multi_coder_analysis.providers.gemini import GeminiProvider
from multi_coder_analysis.providers.openrouter import OpenRouterProvider
from multi_coder_analysis.providers import get_provider
from utils.tracing import write_trace_log
from utils.tracing import write_batch_trace
from multi_coder_analysis.core.prompt import parse_prompt
from multi_coder_analysis.utils.hop_prompt_builder import build_prompt
from multi_coder_analysis.utils.json_prompt_builder import build_json_prompt, build_json_prompt_batch

# Backward compatibility alias during refactor
load_prompt_and_meta = parse_prompt

# --- Hybrid Regex Engine ---
try:
    from . import regex_engine as _re_eng  # when imported as package
    from . import regex_rules as _re_rules
except ImportError:
    # Fallback when running as script
    import regex_engine as _re_eng  # type: ignore
    import regex_rules as _re_rules  # type: ignore

# Load environment variables from .env file
load_dotenv(Path(__file__).parent.parent / ".env")

# Constants can be moved to config.yaml if more flexibility is needed
TEMPERATURE = 0.0
MAX_RETRIES = 10
BACKOFF_FACTOR = 1.5
if "PROMPTS_DIR" not in globals():
    PROMPTS_DIR = Path(__file__).parent / "prompts"

# ---------------------------------------------------------------------------
# Global runtime knobs propagated from main.py (simplifies plumbing changes)
# ---------------------------------------------------------------------------

_EXAMPLES_POLICY: str = "full"   # 'full' | 'trim' | 'none'
_REPLY_SCHEMA: bool = False       # Inject JSON-Schema after response format

def retry_on_api_error(max_retries: int = 3, delay: float = 5.0):
    """Decorator to retry function calls on API errors."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    error_str = str(e).lower()
                    
                    # Check if it's a retryable error
                    retryable_errors = [
                        'rate limit', 'quota', 'timeout', 'connection',
                        'temporary', '429', '503', '504', 'unavailable'
                    ]
                    
                    if any(err in error_str for err in retryable_errors):
                        wait_time = delay * (2 ** attempt)  # Exponential backoff
                        logging.warning(
                            f"API error on attempt {attempt + 1}/{max_retries}: {e}. "
                            f"Retrying in {wait_time}s..."
                        )
                        time.sleep(wait_time)
                    else:
                        # Non-retryable error, raise immediately
                        raise
            
            # All retries exhausted
            logging.error(f"All {max_retries} retry attempts failed")
            raise last_error
        
        return wrapper
    return decorator


class ProgressTracker:
    """Track and report progress for batch processing."""
    
    def __init__(self, total_segments: int, total_hops: int = 12):
        self.total_segments = total_segments
        self.total_hops = total_hops
        self.total_operations = total_segments * total_hops
        self.completed_operations = 0
        self.start_time = time.time()
        self._lock = threading.Lock()
    
    def update(self, segments_processed: int, hop: int):
        """Update progress after processing a batch."""
        with self._lock:
            self.completed_operations += segments_processed
            self._report_progress(hop)
    
    def _report_progress(self, current_hop: int):
        """Report current progress and ETA."""
        progress = self.completed_operations / self.total_operations
        elapsed = time.time() - self.start_time
        
        if progress > 0:
            eta_seconds = (elapsed / progress) - elapsed
            eta_str = self._format_time(eta_seconds)
        else:
            eta_str = "calculating..."
        
        ops_per_sec = self.completed_operations / elapsed if elapsed > 0 else 0
        
        logging.info(
            f"Progress: {progress:.1%} | "
            f"Hop {current_hop}/12 | "
            f"Ops: {self.completed_operations}/{self.total_operations} | "
            f"Speed: {ops_per_sec:.1f} ops/s | "
            f"ETA: {eta_str}"
        )
    
    @staticmethod
    def _format_time(seconds: float) -> str:
        """Format seconds into human-readable time."""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds / 60)}m {int(seconds % 60)}s"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}h {minutes}m"


def read_csv_in_chunks(file_path: Path, chunk_size: int = 1000) -> Generator[pd.DataFrame, None, None]:
    """Read CSV file in chunks to handle large datasets efficiently."""
    for chunk in pd.read_csv(file_path, chunksize=chunk_size, dtype={'StatementID': str}):
        yield chunk


def process_dataframe_chunks(
    file_path: Path,
    processor_func: Callable,
    chunk_size: int = 1000,
    **kwargs
) -> List[Any]:
    """Process a large CSV file in chunks."""
    results = []
    chunk_num = 0
    
    for chunk_df in read_csv_in_chunks(file_path, chunk_size):
        chunk_num += 1
        logging.info(f"Processing chunk {chunk_num} ({len(chunk_df)} rows)")
        
        chunk_results = processor_func(chunk_df, **kwargs)
        results.extend(chunk_results)
        
        # Allow garbage collection between chunks
        import gc
        gc.collect()
    
    return results


def validate_layout_compatibility(layout: str, template: str, batch_size: int) -> List[str]:
    """Validate that a layout is compatible with current settings."""
    warnings = []
    
    # Check batch compatibility
    if batch_size > 1:
        if layout in ["sandwich", "question_first"]:
            warnings.append(
                f"Layout '{layout}' may not work optimally with batch_size > 1. "
                "Consider using batch_size=1 for best results."
            )
    
    # Check template compatibility
    if template == "lean" and layout != "standard":
        warnings.append(
            f"Layout '{layout}' has not been tested with lean templates. "
            "Results may be unpredictable."
        )
    
    # Check for required prompt sections
    required_sections = {
        "sandwich": ["QUICK DECISION CHECK", "⚡"],
        "question_first": ["### Question Q"],
        "recency": ["{{segment_text}}"],
    }
    
    if layout in required_sections:
        # This would need actual prompt validation in production
        warnings.append(
            f"Layout '{layout}' requires specific prompt sections. "
            "Ensure your prompts are compatible."
        )
    
    return warnings

# ---------------------------------------------------------------------------
# Template switcher – returns correct prompt path based on --template flag
# ---------------------------------------------------------------------------


def _escape_for_format(text: str, format_type: str) -> str:
    """Escape text for different format types."""
    if format_type == 'json':
        # Escape for JSON strings
        return text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
    elif format_type == 'xml':
        # Escape for XML
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&apos;')
    else:
        return text



def _format_segments_for_batch(segments: List[HopContext], layout: str) -> str:
    """Format segments according to layout requirements."""
    if layout == "structured_json":
        import json
        segments_data = []
        for ctx in segments:
            segments_data.append({
                "segment_id": ctx.statement_id,
                "content": _escape_for_format(ctx.segment_text, 'json')
            })
        return f"```json\n{json.dumps(segments_data, indent=2)}\n```"
    
    elif layout == "xml_structured":
        lines = ["<segments>"]
        for ctx in segments:
            lines.append(f'  <segment id="{ctx.statement_id}">')
            lines.append(f'    <content>{_escape_for_format(ctx.segment_text, "xml")}</content>')
            lines.append('  </segment>')
        lines.append("</segments>")
        return '\n'.join(lines)
    
    elif layout == "segment_focus":
        lines = []
        for idx, ctx in enumerate(segments, start=1):
            lines.append("═" * 60)
            lines.append(f"SEGMENT {idx}/{len(segments)} (ID: {ctx.statement_id})")
            lines.append("═" * 60)
            lines.append(ctx.segment_text)
            lines.append("")
        return '\n'.join(lines)
    
    else:
        # Default formatting
        lines = []
        for idx, ctx in enumerate(segments, start=1):
            lines.append(f"### Segment {idx}/{len(segments)} (ID: {ctx.statement_id})")
            lines.append(ctx.segment_text)
            lines.append("")
        return '\n'.join(lines)



def _build_batch_instruction(hop_idx: int, num_segments: int, confidence_scores: bool = False, ranked: bool = False, max_candidates: int = 5) -> str:
    """Build consistent batch instruction regardless of layout."""
    parts = [
        f"You must analyze {num_segments} segments for Question Q{hop_idx}.",
        "",
        "OUTPUT FORMAT:",
        "Return a JSON array with exactly {num_segments} elements.".format(num_segments=num_segments),
        "Each element must contain:",
        "- segment_id: The exact ID from the segment header",
        "- answer: Your answer (yes/no/uncertain)",
        "- rationale: Brief explanation for your answer"
    ]
    
    if confidence_scores:
        parts.extend([
            "- confidence: Your confidence level (0-100)",
            "- frame_likelihoods: Object with Alarmist, Neutral, Reassuring percentages"
        ])
    
    if ranked and not confidence_scores:
        parts.extend([
            "",
            "Additionally, embed rankings in the answer field using format:",
            f"Ranking: Frame1 > Frame2 > ... (up to {max_candidates} frames)"
        ])
    
    parts.extend([
        "",
        "CRITICAL: Return ONLY the JSON array. No other text."
    ])
    
    return '\n'.join(parts)

# ---------------------------------------------------------------------------
# Updated prompt-resolution helpers supporting new sub-folder layout
# ---------------------------------------------------------------------------


def _resolve_prompt_path(hop_idx: int, suffix: str) -> Path:
    """Return *Path* to the first prompt file that exists.

    Search order (left-to-right):
        1. legacy root           prompts/hop_Q01.txt
        2. confidence_lean       prompts/confidence_lean/hop_Q01.confidence.lean.txt
        3. confidence            prompts/confidence/hop_Q01.confidence.txt
        4. lean                  prompts/lean/hop_Q01.lean.txt

    This allows a gradual migration without breaking callers that still
    rely on the old flat structure.
    """

    for sub in ["", "confidence_lean", "confidence", "lean"]:
        candidate = PROMPTS_DIR / sub / f"hop_Q{hop_idx:02}{suffix}"
        if candidate.exists():
            return candidate

    # Final fallback – keep original path for clearer error messages
    return PROMPTS_DIR / f"hop_Q{hop_idx:02}{suffix}"


def _get_hop_file(hop_idx: int, template: str = "legacy") -> Path:  # noqa: D401
    """Return path to the requested prompt template (legacy vs lean)."""
    if template == "lean":
        return _resolve_prompt_path(hop_idx, ".lean.txt")
    else:
        return _resolve_prompt_path(hop_idx, ".txt")


def _get_hop_file_with_confidence(
    hop_idx: int,
    template: str = "legacy",
    confidence_mode: bool = False,
) -> Path:
    """Return path to confidence-enhanced or standard prompt template."""

    if confidence_mode:
        # Prefer confidence-lean when template=lean
        if template == "lean":
            path = _resolve_prompt_path(hop_idx, ".confidence.lean.txt")
            if path.exists():
                return path
        # Fallback to full confidence template
        path = _resolve_prompt_path(hop_idx, ".confidence.txt")
        if path.exists():
            return path

    # Not in confidence mode or not found – fall back to standard template
    return _get_hop_file(hop_idx, template)

# ---------------------------------------------------------------------------
# Helpers to (lazily) read header / footer each time so that tests that monkey-
# patch PROMPTS_DIR *after* import still pick up the temporary files.
# ---------------------------------------------------------------------------


def _load_global_header() -> str:  # noqa: D401
    path = PROMPTS_DIR / "GLOBAL_HEADER.txt"
    if not path.exists():
        # Legacy support – remove once all deployments updated
        path = PROMPTS_DIR / "global_header.txt"
    try:
        # Track that this prompt was used
        try:
            from multi_coder_analysis.utils.prompt_tracker import get_prompt_tracker
            tracker = get_prompt_tracker()
            if tracker:
                tracker.track_prompt(path)
        except ImportError:
            pass
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logging.debug("Global header file not found at %s", path)
        return ""


def _load_global_footer() -> str:
    path = PROMPTS_DIR / "GLOBAL_FOOTER.txt"
    try:
        # Track that this prompt was used
        try:
            from multi_coder_analysis.utils.prompt_tracker import get_prompt_tracker
            tracker = get_prompt_tracker()
            if tracker:
                tracker.track_prompt(path)
        except ImportError:
            pass
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logging.debug("Global footer file not found at %s", path)
        return ""

# Map question index to the frame assigned if the answer is "yes"
Q_TO_FRAME = {
    1: "Alarmist", 2: "Alarmist", 3: "Alarmist", 4: "Alarmist",
    5: "Reassuring", 6: "Reassuring",
    7: "Neutral", 8: "Neutral", 9: "Neutral", 10: "Neutral",
    # Hop 11 (dominant‑quote check) is now *strictly* resolved by an explicit
    # "||FRAME=Alarmist / Reassuring" token in the LLM reply.  When that token
    # is missing we *always* drop to Neutral and log a warning.  Never map to
    # a pseudo‑label such as "Variable".
    11: "Neutral",
    12: "Neutral",
}

# --- LLM Interaction ---

def _assemble_prompt(
    ctx: HopContext,
    *,
    template: str = "legacy",
    ranked: bool = False,
    max_candidates: int = 5,
    confidence_scores: bool = False,
    layout: str = "standard",  # NEW: Layout strategy parameter
) -> Tuple[str, str]:
    """Return system/user prompt pair for a single segment.

    The *template* selector chooses between legacy (full) and lean prompts.
    The *confidence_scores* flag enables confidence-enhanced RLSC prompts.
    The *layout* parameter controls prompt structure for empirical testing.
    
    Layout options:
    - standard: Current baseline (hop in both system and user)
    - recency: Segment before hop instructions
    - sandwich: Quick check → segment → detailed rules
    - minimal_system: Minimal system prompt, everything in user
    - question_first: Question → segment → rules/examples
    """
    # Validate layout
    if layout not in VALID_LAYOUTS:
        logging.warning(f"Unknown layout '{layout}', using 'standard' instead")
        layout = 'standard'
    
    try:
        # Use confidence-enhanced templates if requested
        hop_file = _get_hop_file_with_confidence(ctx.q_idx, template, confidence_scores)
        # Register hop template to prompt tracker
        try:
            from multi_coder_analysis.utils.prompt_tracker import get_prompt_tracker
            trk = get_prompt_tracker()
            if trk:
                trk.track_prompt(hop_file)
        except Exception:
            pass

        # --- NEW: strip YAML front-matter and capture metadata ---
        hop_body, meta = load_prompt_and_meta(hop_file)
        ctx.prompt_meta = meta  # save for downstream consumers

        # Load header and footer
        header_path = hop_file.parent / "GLOBAL_HEADER.txt"
        if not header_path.exists():
            header_path = hop_file.parent / "global_header.txt"
        try:
            # Track that this prompt was used
            try:
                from multi_coder_analysis.utils.prompt_tracker import get_prompt_tracker
                tracker = get_prompt_tracker()
                if tracker and header_path.exists():
                    tracker.track_prompt(header_path)
            except ImportError:
                pass
            local_header = header_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            local_header = _load_global_header()

        local_footer = ""
        footer_path = hop_file.parent / "GLOBAL_FOOTER.txt"
        try:
            # Track that this prompt was used
            try:
                from multi_coder_analysis.utils.prompt_tracker import get_prompt_tracker
                tracker = get_prompt_tracker()
                if tracker and footer_path.exists():
                    tracker.track_prompt(footer_path)
            except ImportError:
                pass
            local_footer = footer_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            local_footer = _load_global_footer()

        # --- Layout-specific prompt assembly ---
        if layout == "standard":
            # Current baseline: hop in both system and user
            system_block = local_header + "\n\n" + hop_body
            
            user_prompt = hop_body.replace(
                "{{segment_text}}", ctx.segment_text
            ).replace("{{statement_id}}", ctx.statement_id)
            
        elif layout == "recency":
            # Segment before hop instructions for recency bias
            system_block = local_header
            
            segment_section = f"### Segment (StatementID: {ctx.statement_id})\n{ctx.segment_text}\n\n"
            user_prompt = segment_section + hop_body.replace(
                "### Segment (StatementID: {{statement_id}})\n{{segment_text}}", ""
            ).replace("{{statement_id}}", ctx.statement_id)
            
        elif layout == "sandwich":
            # Extract quick check and detailed sections
            import re
            quick_check_match = re.search(r"### ⚡? ?QUICK DECISION CHECK.*?(?=\n===|$)", hop_body, re.DOTALL)
            quick_check = quick_check_match.group(0) if quick_check_match else ""
            
            # Remove quick check from hop body to get detailed rules
            detailed_rules = hop_body.replace(quick_check, "") if quick_check else hop_body
            
            system_block = local_header
            
            segment_section = f"\n\n### Segment (StatementID: {ctx.statement_id})\n{ctx.segment_text}\n\n"
            user_prompt = quick_check + segment_section + detailed_rules.replace(
                "### Segment (StatementID: {{statement_id}})\n{{segment_text}}", ""
            ).replace("{{statement_id}}", ctx.statement_id)
            
        elif layout == "minimal_system":
            # Minimal system, everything in user
            system_block = "You are an expert claim-framing coder following a mandatory 12-step decision tree."
            
            user_prompt = local_header + "\n\n" + hop_body.replace(
                "{{segment_text}}", ctx.segment_text
            ).replace("{{statement_id}}", ctx.statement_id)
            
        elif layout == "question_first":
            # Extract just the question
            import re
            question_match = re.search(r"### Question Q\d+.*?(?=\n\*\*|$)", hop_body, re.DOTALL)
            question_only = question_match.group(0) if question_match else ""
            
            # Get everything after the question
            if question_match:
                rules_and_examples = hop_body[question_match.end():]
            else:
                rules_and_examples = hop_body
            
            system_block = local_header
            
            segment_section = f"\n\n### Segment (StatementID: {ctx.statement_id})\n{ctx.segment_text}\n\n"
            user_prompt = question_only + segment_section + rules_and_examples.replace(
                "### Segment (StatementID: {{statement_id}})\n{{segment_text}}", ""
            ).replace("{{statement_id}}", ctx.statement_id)
            
        elif layout == "hop_last":
            # Hop at the very end to maximize recency effect
            system_block = local_header
            
            segment_section = f"### Segment (StatementID: {ctx.statement_id})\n{ctx.segment_text}\n\n"
            # Remove segment placeholder from hop_body
            hop_clean = hop_body.replace("### Segment (StatementID: {{statement_id}})\n{{segment_text}}", "").replace("{{statement_id}}", ctx.statement_id)
            user_prompt = segment_section + "\n" + hop_clean
            
        elif layout == "structured_json":
            # Present segment in JSON structure for clarity
            system_block = local_header + "\n\nYou will analyze segments presented in JSON format."
            
            import json
            segment_json = json.dumps({
                "segment_id": ctx.statement_id,
                "content": ctx.segment_text,
                "task": f"Answer Question Q{ctx.q_idx}"
            }, indent=2)
            
            hop_clean = hop_body.replace("### Segment (StatementID: {{statement_id}})\n{{segment_text}}", "").replace("{{statement_id}}", ctx.statement_id)
            user_prompt = f"Analyze this segment:\n```json\n{segment_json}\n```\n\n{hop_clean}"
            
        elif layout == "segment_focus":
            # Segment prominently displayed with visual separation
            system_block = local_header
            
            segment_section = f"""
═══════════════════════════════════════════════════════════════
SEGMENT TO ANALYZE (ID: {ctx.statement_id})
═══════════════════════════════════════════════════════════════
{ctx.segment_text}
═══════════════════════════════════════════════════════════════

"""
            hop_clean = hop_body.replace("### Segment (StatementID: {{statement_id}})\n{{segment_text}}", "").replace("{{statement_id}}", ctx.statement_id)
            user_prompt = segment_section + hop_clean
            
        elif layout == "instruction_first":
            # Clear instructions before segment
            system_block = "Follow the instructions exactly. Analyze each segment systematically."
            
            # Extract question and key instruction
            import re
            question_match = re.search(r"### Question Q\d+.*?(?=\n)", hop_body, re.DOTALL)
            question = question_match.group(0) if question_match else f"Question Q{ctx.q_idx}"
            
            instruction_section = f"""
INSTRUCTION: You must answer the following question for the segment below.
{question}

SEGMENT (ID: {ctx.statement_id}):
{ctx.segment_text}

ANALYSIS GUIDELINES:
"""
            hop_clean = hop_body.replace("### Segment (StatementID: {{statement_id}})\n{{segment_text}}", "").replace("{{statement_id}}", ctx.statement_id)
            if question_match:
                hop_clean = hop_clean.replace(question, "")
            
            user_prompt = local_header + "\n" + instruction_section + hop_clean
            
        elif layout == "parallel_analysis":
            # Present positive and negative indicators in parallel
            system_block = local_header
            
            # This layout works best with modified hop content
            # For now, use standard structure with parallel framing
            segment_section = f"SEGMENT (ID: {ctx.statement_id}): {ctx.segment_text}\n\n"
            analysis_frame = """
Analyze the segment above by considering:
• Would indicate YES if: [Apply positive criteria from question]
• Would indicate NO if: [Apply negative criteria from question]
• Would be UNCERTAIN if: [Neither clearly applies]

"""
            hop_clean = hop_body.replace("### Segment (StatementID: {{statement_id}})\n{{segment_text}}", "").replace("{{statement_id}}", ctx.statement_id)
            user_prompt = segment_section + analysis_frame + hop_clean
            
        elif layout == "evidence_based":
            # Force evidence extraction before decision
            system_block = local_header + "\n\nALWAYS extract evidence before making decisions."
            
            evidence_template = f"""
Step 1: Read this segment (ID: {ctx.statement_id}):
{ctx.segment_text}

Step 2: Extract relevant evidence:
[You will identify specific quotes and facts]

Step 3: Apply the following question based on evidence:
"""
            hop_clean = hop_body.replace("### Segment (StatementID: {{statement_id}})\n{{segment_text}}", "").replace("{{statement_id}}", ctx.statement_id)
            user_prompt = evidence_template + hop_clean
            
        elif layout == "xml_structured":
            # Use XML for clear structure
            system_block = local_header + "\n\nSegments and questions are presented in XML format."
            
            xml_segment = f"""<analysis_task>
    <segment id="{ctx.statement_id}">
        <content>{ctx.segment_text}</content>
    </segment>
    
    <question number="{ctx.q_idx}">
"""
            hop_clean = hop_body.replace("### Segment (StatementID: {{statement_id}})\n{{segment_text}}", "").replace("{{statement_id}}", ctx.statement_id)
            # Close the XML properly
            user_prompt = xml_segment + hop_clean + "\n    </question>\n</analysis_task>"
            
        elif layout == "primacy_recency":
            # Question at beginning AND end for maximum salience
            system_block = local_header
            
            # Extract question
            import re
            question_match = re.search(r"### Question Q\d+.*?(?=\n\*\*|\n\n|$)", hop_body, re.DOTALL)
            question = question_match.group(0) if question_match else f"Question Q{ctx.q_idx}"
            
            primacy_section = f"""
{question}

Now analyze this segment (ID: {ctx.statement_id}):
{ctx.segment_text}

"""
            hop_clean = hop_body.replace("### Segment (StatementID: {{statement_id}})\n{{segment_text}}", "").replace("{{statement_id}}", ctx.statement_id)
            if question_match:
                hop_clean = hop_clean.replace(question, "")
            
            recency_section = f"\n\nREMEMBER: {question}"
            
            user_prompt = primacy_section + hop_clean + recency_section
            
        # NEW: Minimal system variations for Phase 1 experiments
        elif layout == "minimal_segment_first":
            # Minimal system + segment before hop content (recency effect)
            system_block = "You are an expert claim-framing coder following a mandatory 12-step decision tree."
            
            segment_section = f"### Segment (StatementID: {ctx.statement_id})\n{ctx.segment_text}\n\n"
            hop_clean = hop_body.replace("### Segment (StatementID: {{statement_id}})\n{{segment_text}}", "").replace("{{statement_id}}", ctx.statement_id)
            user_prompt = local_header + "\n\n" + segment_section + hop_clean
            
        elif layout == "minimal_question_twice":
            # Minimal system + question at start and end (primacy-recency)
            system_block = "You are an expert claim-framing coder following a mandatory 12-step decision tree."
            
            # Extract question
            import re
            question_match = re.search(r"### Question Q\d+.*?(?=\n\*\*|\n\n|$)", hop_body, re.DOTALL)
            question = question_match.group(0) if question_match else f"Question Q{ctx.q_idx}"
            
            primacy_section = f"{local_header}\n\n{question}\n\nNow analyze this segment (ID: {ctx.statement_id}):\n{ctx.segment_text}\n\n"
            hop_clean = hop_body.replace("### Segment (StatementID: {{statement_id}})\n{{segment_text}}", "").replace("{{statement_id}}", ctx.statement_id)
            if question_match:
                hop_clean = hop_clean.replace(question, "")
            
            recency_section = f"\n\nREMEMBER: {question}"
            user_prompt = primacy_section + hop_clean + recency_section
            
        elif layout == "minimal_json_segment":
            # Minimal system + JSON structure for segment
            system_block = "You are an expert claim-framing coder following a mandatory 12-step decision tree."
            
            import json
            segment_json = json.dumps({
                "segment_id": ctx.statement_id,
                "content": ctx.segment_text,
                "task": f"Answer Question Q{ctx.q_idx}"
            }, indent=2)
            
            hop_clean = hop_body.replace("### Segment (StatementID: {{statement_id}})\n{{segment_text}}", "").replace("{{statement_id}}", ctx.statement_id)
            user_prompt = f"{local_header}\n\nAnalyze this segment:\n```json\n{segment_json}\n```\n\n{hop_clean}"
            
        elif layout == "minimal_parallel_criteria":
            # Minimal system + YES/NO/UNCERTAIN criteria upfront
            system_block = "You are an expert claim-framing coder following a mandatory 12-step decision tree."
            
            segment_section = f"SEGMENT (ID: {ctx.statement_id}): {ctx.segment_text}\n\n"
            analysis_frame = """Analyze the segment above by considering:
• Would indicate YES if: [Apply positive criteria from question]
• Would indicate NO if: [Apply negative criteria from question]
• Would be UNCERTAIN if: [Neither clearly applies]
```
</region_of_file_to_rewritten_file>

"""
            hop_clean = hop_body.replace("### Segment (StatementID: {{statement_id}})\n{{segment_text}}", "").replace("{{statement_id}}", ctx.statement_id)
            user_prompt = local_header + "\n\n" + segment_section + analysis_frame + hop_clean
            
            # Optional JSON-Schema injection for experimental flag
            if _REPLY_SCHEMA and layout.startswith("cue_detection_enhanced_json"):
                schema_block = """\n### Reply schema\n```json\n{\n  \"$schema\": \"https://json-schema.org/draft/2020-12/schema\",\n  \"type\": \"object\",\n  \"properties\": {\n    \"cue_map\": {\"type\": \"object\"},\n    \"answer\": {\"type\": \"string\"},\n    \"rationale\": {\"type\": \"string\"}\n  },\n  \"required\": [\"cue_map\", \"answer\", \"rationale\"]\n}\n```"""
                user_prompt += schema_block

            user_block = user_prompt + "\n\n" + local_footer

        elif layout == "minimal_hop_sandwich":
            # Minimal system + hop content before and after segments
            system_block = "You are an expert claim-framing coder following a mandatory 12-step decision tree."
            
            # Extract question and key rules for the "sandwich"
            import re
            question_match = re.search(r"### Question Q\d+.*?(?=\n\*\*|\n\n|$)", hop_body, re.DOTALL)
            question = question_match.group(0) if question_match else f"Question Q{ctx.q_idx}"
            
            # Get rules section
            rules_match = re.search(r"\*\*Rules?\*\*:?.*?(?=\n\*\*|\n###|$)", hop_body, re.DOTALL)
            rules = rules_match.group(0) if rules_match else ""
            
            # Get examples section
            examples_match = re.search(r"\*\*Examples?\*\*:?.*?(?=\n\*\*|\n###|$)", hop_body, re.DOTALL)
            examples = examples_match.group(0) if examples_match else ""
            
            segment_section = f"\n\n=== ANALYZE THESE SEGMENTS ===\n\nSegment (ID: {ctx.statement_id}):\n{ctx.segment_text}\n\n=== REMEMBER THE QUESTION ===\n\n"
            
            user_prompt = f"{local_header}\n\n{question}\n\n{rules}\n\n{examples}{segment_section}{question}\n\n{rules}"
            
        elif layout == "cue_detection":
            # New two-step cue-detection structure
            # 1) Segment comes first (recency), then cue-detection instructions and checklist,
            #    then hop-specific question trimmed for CUE_MAP logic, finally global footer.
            segment_section = f"### Segment (StatementID: {ctx.statement_id})\n{ctx.segment_text}\n\n"

            # Shared components
            comp_dir = PROMPTS_DIR / "cue_detection"
            instruction_txt = (comp_dir / "cue_detection_instructions.txt").read_text(encoding="utf-8")
            checklist_txt = (comp_dir / "cue_checklist.txt").read_text(encoding="utf-8")
            frame_decision_txt = (comp_dir / "frame_decision_instructions.txt").read_text(encoding="utf-8")

            # Hop-specific trimmed prompt
            hop_trimmed = comp_dir / "hops" / f"hop_Q{ctx.q_idx:02}.txt"
            if hop_trimmed.exists():
                hop_body_trimmed, _ = load_prompt_and_meta(hop_trimmed)
            else:
                # Fallback to original hop file (will still work but longer)
                hop_trimmed = _get_hop_file(ctx.q_idx, template)
                hop_body_trimmed, _ = load_prompt_and_meta(hop_trimmed)
                # Remove segment placeholder because we already injected segment
                hop_body_trimmed = hop_body_trimmed.replace("### Segment (StatementID: {{statement_id}})\n{{segment_text}}", "")
                hop_body_trimmed = hop_body_trimmed.replace("{{statement_id}}", ctx.statement_id)

            # Assemble
            system_block = local_header  # Header stays in system prompt for consistency

            user_prompt_parts = [
                segment_section,
                instruction_txt,
                "\n\n",
                checklist_txt,
                "\n\n",
                frame_decision_txt,
                "\n\n",
                hop_body_trimmed
            ]
            user_prompt = "".join(user_prompt_parts)
        
        elif layout == "cue_detection_enhanced":
            # Place header inside user prompt just like minimal_system;
            # keep a minimal system role sentence.

            system_block = "You are an expert claim-framing coder following a mandatory 12-step decision tree."

            user_prompt = local_header + "\n\n" + build_prompt(
                f"Q{ctx.q_idx}",
                ctx.segment_text,
                statement_id=ctx.statement_id,
                examples_policy=_EXAMPLES_POLICY,
            )
        
        elif layout == "cue_detection_enhanced_json":
            # Parameterised JSON version – move header to user prompt.

            system_block = "You are an expert claim-framing coder following a mandatory 12-step decision tree."

            user_prompt = local_header + "\n\n" + build_json_prompt(
                f"Q{ctx.q_idx}",
                ctx.segment_text,
                statement_id=ctx.statement_id,
                include_examples=(_EXAMPLES_POLICY != "none"),
                include_all_rules=True
            )
        
        elif layout == "cue_detection_enhanced_machine":
            # Ultra-compact machine-readable – header moves to user prompt
            from multi_coder_analysis.utils.json_prompt_builder_machine import build_json_prompt_machine

            system_block = "You are an expert claim-framing coder following a mandatory 12-step decision tree."

            user_prompt = local_header + "\n\n" + build_json_prompt_machine(
                f"Q{ctx.q_idx}",
                ctx.segment_text,
                statement_id=ctx.statement_id,
                include_examples=(_EXAMPLES_POLICY != "none"),
                include_all_rules=True
            )
        
        elif layout == "cue_detection_enhanced_batch":
            """Mirror layout: markdown checklist injected every GROUP_SIZE segments"""

            import re as _re
            from multi_coder_analysis.utils.hop_prompt_builder import build_prompt as _build_slice

            GROUP_SIZE = 25  # keep aligned with single-segment stub

            # Build rule slice once
            tmp_prompt = _build_slice(f"Q{hop_idx}", "<SEG>", statement_id="<ID>", examples_policy=_EXAMPLES_POLICY)
            m = _re.search(r"### Q\d+ Rule Slice.*?```json.*?```", tmp_prompt, _re.DOTALL)
            rule_slice_block = m.group(0) if m else ""

            system_block = local_header

            parts: list[str] = []
            for i in range(0, len(segments), GROUP_SIZE):
                chunk = segments[i : i + GROUP_SIZE]
                for ctx_ in chunk:
                    parts.append(f"### Segment (StatementID: {ctx_.statement_id})\n{ctx_.segment_text}\n\n")
                parts.append(rule_slice_block + "\n\n")

            instruction = _build_batch_instruction(hop_idx, len(segments), confidence_scores, ranked, max_candidates)
            user_block = "".join(parts) + instruction + "\n\n" + local_footer

            return system_block, user_block
        
        elif layout == "cue_detection_enhanced_json_batch":
            # NEW: JSON parameterized batch version
            # Uses json_prompt_builder to create structured JSON prompts
            
            system_block = local_header
            
            # Build segment data for batch
            segment_data = []
            for ctx in segments:
                segment_data.append({
                    "statement_id": ctx.statement_id,
                    "text": ctx.segment_text
                })
            
            # Build JSON-structured batch prompt
            user_prompt = build_json_prompt_batch(
                f"Q{hop_idx}",
                segment_data,
                include_examples=(_EXAMPLES_POLICY != "none"),
                group_size=25  # Same as enhanced_batch
            )
            
            user_block = user_prompt + "\n\n" + local_footer
            return system_block, user_block
        
        elif layout == "cue_detection_enhanced_machine_batch":
            # NEW: Ultra-compact machine-readable batch format
            from multi_coder_analysis.utils.json_prompt_builder_machine import build_json_prompt_batch_machine
            
            system_block = "Follow the JSON specification exactly."
            
            # Build segment data for batch
            segment_data = []
            for ctx in segments:
                segment_data.append({
                    "statement_id": ctx.statement_id,
                    "text": ctx.segment_text
                })
            
            # Build machine-readable batch prompt
            user_prompt = build_json_prompt_batch_machine(
                f"Q{hop_idx}",
                segment_data,
                include_examples=(_EXAMPLES_POLICY != "none"),
                group_size=25
            )
            
            user_block = user_prompt + "\n\n" + local_footer
            return system_block, user_block
        
        elif layout == "cue_detection_enhanced_json_batch":
            # NEW: JSON parameterized batch version
            # Process all segments in a single batch per hop
            
            for hop_idx in range(1, 13):
                _log_hop(hop_idx, len(df), token_accumulator.get('regex_yes', 0), len(df))
                
                # Skip regex for batch JSON layouts
                sys_prompt, user_prompt = _assemble_prompt_batch(
                    batch.contexts, hop_idx, template=template, layout=layout
                )
                
                # Make batch API call
                raw_text = provider.generate(
                    sys_prompt, user_prompt, model, temperature,
                    top_k=top_k, top_p=top_p
                )
                
                # Parse batch response
                try:
                    if raw_text.strip().startswith('```') and raw_text.strip().endswith('```'):
                        json_content = raw_text.strip()[3:-3]
                        if json_content.startswith('json'):
                            json_content = json_content[4:].strip()
                    else:
                        json_content = raw_text.strip()
                    
                    batch_results = json.loads(json_content)
                    
                    # Process results
                    for i, result in enumerate(batch_results):
                        if i >= len(batch.contexts):
                            break
                        
                        ctx = batch.contexts[i]
                        ctx.q_idx = hop_idx
                        
                        # Apply result
                        answer = result.get("answer", "uncertain").lower().strip()
                        rationale = result.get("rationale", "No rationale provided.")
                        
                        if answer == "yes":
                            if hop_idx == 11:
                                token = re.search(r"\|\|FRAME=(Alarmist|Reassuring)", rationale)
                                if token:
                                    ctx.final_frame = token.group(1)
                                    ctx.final_justification = f"Frame determined by Q11 explicit token {token.group(0)}."
                                else:
                                    ctx.final_frame = "Neutral"
                                    ctx.final_justification = "Hop 11 'yes' without explicit token – forced Neutral."
                            else:
                                ctx.final_frame = Q_TO_FRAME[hop_idx]
                                ctx.final_justification = f"Frame determined by Q{hop_idx} trigger. Rationale: {rationale}"
                            ctx.is_concluded = True
                            break
                    
                except Exception as e:
                    logging.error(f"Failed to parse batch JSON response for hop {hop_idx}: {e}")
                    # Fall back to uncertain for all
                    for ctx in batch.contexts:
                        ctx.q_idx = hop_idx
                        ctx.analysis_history.append(f"Q{hop_idx}: uncertain")
            
            # Finalize any unresolved contexts
            for ctx in batch.contexts:
                if not ctx.is_concluded:
                    ctx.final_frame = "Neutral"
                    ctx.final_justification = "Default to Neutral: No specific framing cue triggered in Q1-Q12."
                    ctx.is_concluded = True
        
        elif layout == "cue_detection_enhanced_machine_batch":
            # Same as JSON batch but with machine format
            # Process all segments in a single batch per hop
            
            for hop_idx in range(1, 13):
                _log_hop(hop_idx, len(df), token_accumulator.get('regex_yes', 0), len(df))
                
                # Skip regex for batch machine layouts
                sys_prompt, user_prompt = _assemble_prompt_batch(
                    batch.contexts, hop_idx, template=template, layout=layout
                )
                
                # Make batch API call
                raw_text = provider.generate(
                    sys_prompt, user_prompt, model, temperature,
                    top_k=top_k, top_p=top_p
                )
                
                # Parse batch response (expecting compact format)
                try:
                    if raw_text.strip().startswith('```') and raw_text.strip().endswith('```'):
                        json_content = raw_text.strip()[3:-3]
                        if json_content.startswith('json'):
                            json_content = json_content[4:].strip()
                    else:
                        json_content = raw_text.strip()
                    
                    batch_results = json.loads(json_content)
                    
                    # Process results
                    for i, result in enumerate(batch_results):
                        if i >= len(batch.contexts):
                            break
                        
                        ctx = batch.contexts[i]
                        ctx.q_idx = hop_idx
                        
                        # Apply result (machine format uses short keys)
                        answer = result.get("a", "uncertain").lower().strip()
                        rationale = result.get("r", "No rationale provided.")
                        
                        if answer == "yes":
                            if hop_idx == 11:
                                token = re.search(r"\|\|FRAME=(Alarmist|Reassuring)", rationale)
                                if token:
                                    ctx.final_frame = token.group(1)
                                    ctx.final_justification = f"Frame determined by Q11 explicit token {token.group(0)}."
                                else:
                                    ctx.final_frame = "Neutral"
                                    ctx.final_justification = "Hop 11 'yes' without explicit token – forced Neutral."
                            else:
                                ctx.final_frame = Q_TO_FRAME[hop_idx]
                                ctx.final_justification = f"Frame determined by Q{hop_idx} trigger. Rationale: {rationale}"
                            ctx.is_concluded = True
                            break
                    
                except Exception as e:
                    logging.error(f"Failed to parse batch machine response for hop {hop_idx}: {e}")
                    # Fall back to uncertain for all
                    for ctx in batch.contexts:
                        ctx.q_idx = hop_idx
                        ctx.analysis_history.append(f"Q{hop_idx}: uncertain")
            
            # Finalize any unresolved contexts
            for ctx in batch.contexts:
                if not ctx.is_concluded:
                    ctx.final_frame = "Neutral"
                    ctx.final_justification = "Default to Neutral: No specific framing cue triggered in Q1-Q12."
                    ctx.is_concluded = True

        # Add ranking instruction if needed
        if ranked and not confidence_scores:
            ranking_instr = (
                "\nAfter the JSON object, add a new line starting with the word 'Ranking:' "
                "followed by up to {n} frame labels in descending order of likelihood, "
                "separated by the ' > ' character.  For example:\n"
                "Ranking: Alarmist > Neutral > Reassuring\n".format(n=max_candidates)
            )
            user_prompt = user_prompt + "\n\n" + ranking_instr

        # Optional: append explicit JSON-Schema to aid validation when flag is set
        if _REPLY_SCHEMA and layout.startswith("cue_detection_enhanced_json"):
            user_prompt += (
                "\n\n### Reply schema\n```json\n{\n  \"$schema\": \"https://json-schema.org/draft/2020-12/schema\",\n  \"type\": \"object\",\n  \"properties\": {\n    \"cue_map\": {\"type\": \"object\"},\n    \"answer\": {\"type\": \"string\"},\n    \"rationale\": {\"type\": \"string\"}\n  },\n  \"required\": [\"cue_map\", \"answer\", \"rationale\"]\n}\n```"
            )

        user_block = user_prompt + "\n\n" + local_footer

        # --- Confidence score add-on (modular, no prompt template change) ---
        if confidence_scores:
            conf_instr = (
                "\n\nIn your JSON you **may** include an optional numeric field \"confidence\" "
                "(0-100) representing your certainty.  If confidence < 100 also add "
                "\"confidence_explanation\" – one short sentence explaining the main "
                "source of uncertainty.  If you are fully certain (100) omit the "
                "explanation."
            )
            user_block += conf_instr

        # Capture for offline inspection
        _capture_prompt(ctx.q_idx, system_block, user_block)
        return system_block, user_block

    except FileNotFoundError:
        logging.error(f"Error: Prompt file not found for hop {hop_idx}")
        raise
    except Exception as e:
        logging.error(f"Error assembling batch prompt for hop {hop_idx}: {e}")
        raise

@retry_on_api_error(max_retries=3, delay=5.0)
def _call_llm_single_hop(
    ctx: HopContext,
    provider,
    model: str,
    temperature: float = TEMPERATURE,
    *,
    top_k: int | None = None,
    top_p: float | None = None,
    template: str = "legacy",
    ranked: bool = False,
    max_candidates: int = 5,
    confidence_scores: bool = False,
    layout: str = "standard",  # NEW: Layout parameter
) -> Dict[str, str]:
    """Makes a single, retrying API call to the LLM for one hop."""
    sys_prompt, user_prompt = _assemble_prompt(
        ctx, 
        template=template, 
        ranked=ranked, 
        max_candidates=max_candidates,
        confidence_scores=confidence_scores,
        layout=layout  # Pass layout parameter
    )
    
    for attempt in range(MAX_RETRIES):
        try:
            # Use provider abstraction
            raw_text = provider.generate(sys_prompt, user_prompt, model, temperature, top_k=top_k, top_p=top_p)
            
            # Handle cases where content might be empty
            if not raw_text.strip():
                logging.warning(f"Q{ctx.q_idx} for {ctx.statement_id}: Response content is empty. This may indicate a token limit or safety issue.")
                raise ValueError("Response content is empty")
            
            content = raw_text.strip()
            
            # Handle markdown-wrapped JSON responses
            if content.startswith('```json') and content.endswith('```'):
                # Extract JSON from markdown code block
                json_content = content[7:-3].strip()  # Remove ```json and ```
            elif content.startswith('```') and content.endswith('```'):
                # Handle generic code block
                json_content = content[3:-3].strip()  # Remove ``` and ```
            else:
                json_content = content
            
            # The model is instructed to reply with JSON only.
            parsed_json = json.loads(json_content)
            
            # Basic validation of the parsed JSON structure
            if "answer" in parsed_json and "rationale" in parsed_json:
                result = {
                    "answer": str(parsed_json["answer"]), 
                    "rationale": str(parsed_json["rationale"])
                }
                # Preserve cue_map if present for downstream validation
                if "cue_map" in parsed_json:
                    result["cue_map"] = parsed_json["cue_map"]
                # Note: Thoughts handling removed for simplicity in provider abstraction
                return result
            else:
                logging.warning(f"Q{ctx.q_idx} for {ctx.statement_id}: LLM response missing 'answer' or 'rationale'. Content: {content}")
                # Fall through to retry logic

        except json.JSONDecodeError as e:
            logging.warning(f"Q{ctx.q_idx} for {ctx.statement_id}: Failed to parse LLM JSON response on attempt {attempt + 1}. Error: {e}. Content: {content}")
        except Exception as e:
            logging.warning(f"Q{ctx.q_idx} for {ctx.statement_id}: API error on attempt {attempt + 1}: {e}. Retrying after backoff.")

        time.sleep(BACKOFF_FACTOR * (2 ** attempt)) # Exponential backoff

    # If all retries fail
    logging.error(f"Q{ctx.q_idx} for {ctx.statement_id}: All {MAX_RETRIES} retries failed.")
    return {"answer": "uncertain", "rationale": f"LLM call failed after {MAX_RETRIES} retries."}

# --- Response Processing Helper ---

def _apply_llm_response(ctx: HopContext, llm_response: dict) -> None:
    """Apply LLM response to HopContext, handling hop 11 token guard logic."""
    answer = llm_response.get("answer", "uncertain").lower().strip()
    rationale = llm_response.get("rationale", "No rationale provided.")
    hop_idx = getattr(ctx, 'current_hop', None) or getattr(ctx, 'q_idx', 11)
    
    if answer == "yes":
        # ──────────────────────────────────────────────────────────
        # HOP‑11 SPECIAL‑CASE — token‑guard then safe fallback
        # ──────────────────────────────────────────────────────────
        if hop_idx == 11:
            token = re.search(r"\|\|FRAME=(Alarmist|Reassuring)\b", rationale)
            if token:
                ctx.final_frame = token.group(1)
                ctx.final_justification = (
                    f"Frame determined by Q11 explicit token {token.group(0)}."
                )
            else:
                logging.warning(
                    "Q11 answered 'yes' but missing ||FRAME token; "
                    "defaulting to Neutral  (SID=%s)", ctx.statement_id
                )
                ctx.final_frame = "Neutral"
                ctx.final_justification = (
                    "Hop 11 'yes' without explicit token – forced Neutral."
                )
            ctx.is_concluded = True
            ctx._resolved_by_llm_this_hop = True

        # All other hops use the static map
        elif hop_idx in Q_TO_FRAME:
            ctx.final_frame = Q_TO_FRAME[hop_idx]
            ctx.final_justification = f"Frame determined by Q{hop_idx} trigger. Rationale: {rationale}"
            ctx.is_concluded = True
            ctx._resolved_by_llm_this_hop = True

# --- Core Orchestration ---

def run_tot_chain(segment_row: pd.Series, provider, trace_dir: Path, model: str, token_accumulator: dict, token_lock: threading.Lock, temperature: float = TEMPERATURE, *, template: str = "legacy", layout: str = "standard") -> HopContext:
    """Orchestrates the 12-hop reasoning chain for a single text segment."""
    ctx = HopContext(
        statement_id=segment_row["StatementID"],
        segment_text=segment_row["Statement Text"],
        article_id=segment_row.get("ArticleID", "")
    )
    
    # Ensure positional metadata exists even when processed individually
    ctx.batch_size = 1
    ctx.batch_pos = 1
    
    # Assign a sentinel batch_id for single-segment path
    ctx.batch_id = "single"  # type: ignore[attr-defined]
    
    uncertain_streak = 0

    for q_idx in range(1, 13):
        # Log progress for single-segment execution
        _log_hop(q_idx, 1, token_accumulator.get('regex_yes', 0), 0)
        ctx.q_idx = q_idx
        # --- metrics counter ---
        with token_lock:
            token_accumulator['total_hops'] += 1
        
        # --------------------------------------
        # 1. Try conservative regex short-circuit
        # --------------------------------------
        regex_ans = None
        try:
            regex_ans = _re_eng.match(ctx)
        except Exception as exc:
            logging.warning(f"Regex engine error on {ctx.statement_id} Q{q_idx}: {exc}")

        provider_called = False

        if regex_ans:
            llm_response = {
                "answer": regex_ans["answer"],
                "rationale": regex_ans["rationale"],
            }
            frame_override = regex_ans.get("frame")
            via = "regex"
            regex_meta = regex_ans.get("regex", {})
            with token_lock:
                if _re_eng._FORCE_SHADOW:
                    token_accumulator['regex_hit_shadow'] += 1
                else:
                    token_accumulator['regex_yes'] += 1
        else:
            llm_response = _call_llm_single_hop(ctx, provider, model, temperature, template=template, layout=layout)
            frame_override = None
            provider_called = True
            via = "llm"
            regex_meta = None
            with token_lock:
                token_accumulator['llm_calls'] += 1
        
        ctx.raw_llm_responses.append(llm_response)
        
        # --------------------------------------------------------------
        # NEW: Support ranked-list output
        # --------------------------------------------------------------
        raw_answer_text = llm_response.get("answer", "") or ""
        result = _extract_frame_and_ranking(raw_answer_text)
        if result:
            choice, ranking = result
        else:
            choice, ranking = None, None

        if ranking:
            _MAX_KEEP = 5  # fallback when pipeline config not available in this scope
            ctx.ranking = ranking[:_MAX_KEEP]
            # fall back to top choice for downstream yes/uncertain logic
            choice = ranking[0] if ranking else choice

        choice = (choice or "uncertain").lower().strip()
        rationale = llm_response.get("rationale", "No rationale provided.")
        
        # Update logs and traces
        trace_entry = {
            "Q": q_idx,
            "answer": choice,
            "rationale": rationale,
            "via": via,
            "regex": regex_meta,
            "batch_id": ctx.batch_id,
            "batch_size": ctx.batch_size,
            "batch_pos": ctx.batch_pos,
            # Include raw statement text and article ID for easier debugging across all traces
            "statement_text": ctx.segment_text,
            "article_id": ctx.article_id,
        }
        
        # Add thinking traces if available
        thoughts = provider.get_last_thoughts()
        if thoughts:
            trace_entry["thoughts"] = thoughts
        
        # --- Token accounting ---
        if provider_called:
            usage = provider.get_last_usage()
            if usage:
                with token_lock:
                    token_accumulator['prompt_tokens'] += usage.get('prompt_tokens', 0)
                    token_accumulator['response_tokens'] += usage.get('response_tokens', 0)
                    token_accumulator['thought_tokens'] += usage.get('thought_tokens', 0)
                    token_accumulator['total_tokens'] += usage.get('total_tokens', 0)
        
        ctx.analysis_history.append(f"Q{q_idx}: {choice}")
        ctx.reasoning_trace.append(trace_entry)
        write_trace_log(trace_dir, ctx.statement_id, trace_entry)

        if choice == "uncertain":
            uncertain_streak += 1
            if uncertain_streak >= 3:
                ctx.final_frame = "LABEL_UNCERTAIN"
                ctx.is_concluded = True
                ctx.final_justification = f"ToT chain terminated at Q{q_idx} due to 3 consecutive 'uncertain' responses."
                break
        else:
            uncertain_streak = 0 # Reset streak on a clear answer

        if choice == "yes":
            # ──────────────────────────────────────────────────────────
            # HOP‑11 SPECIAL‑CASE — token‑guard then safe fallback
            # ──────────────────────────────────────────────────────────
            if q_idx == 11 and not frame_override:
                token = re.search(r"\|\|FRAME=(Alarmist|Reassuring)\b", rationale)
                if token:
                    ctx.final_frame = token.group(1)
                    ctx.final_justification = (
                        f"Frame determined by Q11 explicit token {token.group(0)}."
                    )
                else:
                    logging.warning(
                        "Q11 answered 'yes' but missing ||FRAME token; "
                        "defaulting to Neutral  (SID=%s)", ctx.statement_id
                    )
                    ctx.final_frame = "Neutral"
                    ctx.final_justification = (
                        "Hop 11 'yes' without explicit token – forced Neutral."
                    )
                ctx.is_concluded = True
                ctx._resolved_by_llm_this_hop = True

            # All other hops use the static map or frame override
            else:
                ctx.final_frame = frame_override or Q_TO_FRAME[q_idx]
                ctx.is_concluded = True
                # Frame override from regex, else standard mapping
                if frame_override:
                    ctx.final_justification = f"Frame determined by Q{q_idx} trigger. Rationale: {rationale}"
                else:
                    ctx.final_justification = f"Frame determined by Q{q_idx} trigger. Rationale: {rationale}"
                ctx._resolved_by_llm_this_hop = True
            break # Exit the loop on the first 'yes'

    # If loop completes without any 'yes' answers
    if not ctx.is_concluded:
        ctx.final_frame = "Neutral" # Default outcome
        ctx.final_justification = "Default to Neutral: No specific framing cue triggered in Q1-Q12."
        ctx.is_concluded = True

    return ctx

# --- NEW: Batch Prompt Assembly ---

def _assemble_prompt_batch(
    segments: List[HopContext],
    hop_idx: int,
    *,
    template: str = "legacy",
    ranked: bool = False,
    max_candidates: int = 5,
    confidence_scores: bool = False,
    layout: str = "standard",  # NEW: Layout parameter
) -> Tuple[str, str]:
    """Assemble a prompt that contains multiple segments for the same hop."""
    # Validate layout
    if layout not in VALID_LAYOUTS:
        logging.warning(f"Unknown layout '{layout}', using 'standard' instead")
        layout = 'standard'
    
    try:
        # Use confidence-enhanced templates if requested
        hop_file = _get_hop_file_with_confidence(hop_idx, template, confidence_scores)
        # Track hop template usage for later copying
        try:
            from multi_coder_analysis.utils.prompt_tracker import get_prompt_tracker
            trk2 = get_prompt_tracker()
            if trk2:
                trk2.track_prompt(hop_file)
        except Exception:
            pass

        hop_content, meta = load_prompt_and_meta(hop_file)

        # Attach same meta to every HopContext in this batch for consistency
    
        for ctx in segments:
            ctx.prompt_meta = meta

        # Remove any single-segment placeholders
        hop_content = hop_content.replace("{{segment_text}}", "<SEGMENT_TEXT>")
        hop_content = hop_content.replace("{{statement_id}}", "<STATEMENT_ID>")

        # Format segments using layout-specific formatter
        segment_block = _format_segments_for_batch(segments, layout)

        # Build consistent instruction using the new builder
        instruction = _build_batch_instruction(hop_idx, len(segments), confidence_scores, ranked, max_candidates)

        # Prefer new canonical filename; fallback to legacy if absent
        header_path = hop_file.parent / "GLOBAL_HEADER.txt"
        if not header_path.exists():
            header_path = hop_file.parent / "global_header.txt"
        try:
            # Track that this prompt was used
            try:
                from multi_coder_analysis.utils.prompt_tracker import get_prompt_tracker
                tracker = get_prompt_tracker()
                if tracker and header_path.exists():
                    tracker.track_prompt(header_path)
            except ImportError:
                pass
            local_header = header_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            local_header = _load_global_header()

        local_footer = ""
        footer_path = hop_file.parent / "GLOBAL_FOOTER.txt"
        try:
            # Track that this prompt was used
            try:
                from multi_coder_analysis.utils.prompt_tracker import get_prompt_tracker
                tracker = get_prompt_tracker()
                if tracker and footer_path.exists():
                    tracker.track_prompt(footer_path)
            except ImportError:
                pass
            local_footer = footer_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            local_footer = _load_global_footer()

        # Apply layout-specific formatting for batch prompts
        if layout == "standard":
            system_block = local_header + "\n\n" + hop_content
            user_block = instruction + segment_block + "\n\n" + local_footer
        elif layout == "recency":
            # Put segments first for recency bias
            system_block = local_header
            user_block = segment_block + "\n\n" + instruction + "\n\n" + hop_content + "\n\n" + local_footer
        elif layout == "minimal_system":
            # Minimal system, everything in user
            system_block = "You are an expert claim-framing coder following a mandatory 12-step decision tree."
            user_block = local_header + "\n\n" + hop_content + "\n\n" + instruction + segment_block + "\n\n" + local_footer
        elif layout == "hop_last":
            # All segments first, then hop question at the very end
            system_block = local_header
            user_block = segment_block + "\n\n" + hop_content + "\n\n" + instruction + "\n\n" + local_footer
            
        elif layout == "structured_json":
            # Present all segments as JSON array with proper escaping
            segment_block = _format_segments_for_batch(segments, layout)
            instruction = _build_batch_instruction(hop_idx, len(segments), confidence_scores, ranked, max_candidates)
            
            system_block = local_header + "\n\nAnalyze segments presented in JSON format."
            user_block = f"Task: {hop_content}\n\n{instruction}\n\nSegments:\n{segment_block}\n\n{local_footer}"
            
        elif layout == "segment_focus":
            # Each segment clearly separated with visual boundaries
            segment_formatted_lines = []
            for idx, ctx in enumerate(segments, start=1):
                segment_formatted_lines.append("═" * 60)
                segment_formatted_lines.append(f"SEGMENT {idx} (ID: {ctx.statement_id})")
                segment_formatted_lines.append("═" * 60)
                segment_formatted_lines.append(ctx.segment_text)
                segment_formatted_lines.append("")
            segment_formatted = "\n".join(segment_formatted_lines)
            
            system_block = local_header
            user_block = segment_formatted + "\n\n" + hop_content + "\n\n" + instruction + "\n\n" + local_footer
            
        elif layout == "instruction_first":
            # Instructions and question before all segments
            import re
            question_match = re.search(r"### Question Q\d+.*?(?=\n)", hop_content)
            question = question_match.group(0) if question_match else f"Question Q{hop_idx}"
            
            instruction_enhanced = f"""
BATCH INSTRUCTION: Answer the following question for EACH segment below.
{question}

{instruction}

SEGMENTS TO ANALYZE:
"""
            system_block = "Follow the instructions exactly. Analyze each segment systematically."
            user_block = local_header + "\n" + instruction_enhanced + segment_block + "\n\n" + hop_content + "\n\n" + local_footer
            
        elif layout == "parallel_analysis":
            # Table format for parallel comparison
            system_block = local_header
            
            parallel_instruction = f"""
Analyze each segment below using this framework:
- YES indicators: [Look for affirmative evidence per the question]
- NO indicators: [Look for negative evidence per the question]  
- UNCERTAIN: [When evidence is ambiguous or missing]

{instruction}

SEGMENTS:
"""
            user_block = parallel_instruction + segment_block + "\n\n" + hop_content + "\n\n" + local_footer
            
        elif layout == "evidence_based":
            # Structured evidence extraction for batch
            system_block = local_header + "\n\nFor EACH segment: 1) Extract evidence 2) Apply criteria 3) Decide"
            
            evidence_instruction = f"""
{instruction}

For each segment below, you must:
1. Identify relevant evidence (quotes, facts)
2. Apply the question criteria
3. Provide your answer with rationale

SEGMENTS FOR ANALYSIS:
"""
            user_block = evidence_instruction + segment_block + "\n\n" + hop_content + "\n\n" + local_footer
            
        elif layout == "xml_structured":
            # XML batch structure
            xml_segments = "<analysis_batch>\n"
            for ctx in segments:
                xml_segments += f'    <segment id="{ctx.statement_id}">\n'
                xml_segments += f'        <content>{ctx.segment_text}</content>\n'
                xml_segments += '    </segment>\n'
            xml_segments += f'    <question number="{hop_idx}">\n        '
            xml_segments += hop_content.replace("\n", "\n        ")
            xml_segments += f'\n    </question>\n'
            xml_segments += f'    <instruction>{instruction}</instruction>\n'
            xml_segments += '</analysis_batch>'
            
            system_block = local_header + "\n\nProcess the XML-structured analysis batch."
            user_block = xml_segments + "\n\n" + local_footer
            
        elif layout == "primacy_recency":
            # Question at start and end of batch
            import re
            question_match = re.search(r"### Question Q\d+.*?(?=\n\*\*|\n\n|$)", hop_content, re.DOTALL)
            question = question_match.group(0) if question_match else f"Question Q{hop_idx}"
            
            primacy = f"{question}\n\n{instruction}\n\nSEGMENTS:\n"
            recency = f"\n\nREMINDER - Answer this for EACH segment above: {question}"
            
            system_block = local_header
            user_block = primacy + segment_block + "\n\n" + hop_content + recency + "\n\n" + local_footer
            
        elif layout == "sandwich":
            # Sandwich layout for batch: Quick check → Segments → Detailed analysis
            # Extract quick check section from hop content
            import re
            # Look for QUICK DECISION CHECK with or without emoji
            quick_check_match = re.search(r"(### (?:⚡ )?QUICK DECISION CHECK.*?)(?=### Segment|### Question|$)", hop_content, re.DOTALL)
            # Extract everything after the segment placeholder as the detailed section
            detailed_match = re.search(r"(### Question Q\d+.*?)$", hop_content, re.DOTALL)
            
            if quick_check_match and detailed_match:
                quick_check = quick_check_match.group(1).strip()
                detailed = detailed_match.group(1).strip()
                
                # Build sandwich structure
                sandwich_instruction = f"""
{quick_check}

Now examine these segments:
{segment_block}

{detailed}

{instruction}
"""
                system_block = local_header
                user_block = sandwich_instruction + "\n\n" + local_footer
            else:
                # Fallback if sandwich markers not found
                logging.warning(f"Sandwich layout markers not found in hop {hop_idx}, using standard structure")
                system_block = local_header + "\n\n" + hop_content
                user_block = instruction + segment_block + "\n\n" + local_footer
                
        elif layout == "question_first":
            # Question first layout for batch: Question → Segments → Analysis rules
            import re
            # Extract the question from hop content
            question_match = re.search(r"(### Question Q\d+.*?)(?=\n\*\*|\n\n|$)", hop_content, re.DOTALL)
            
            if question_match:
                question = question_match.group(1).strip()
                # Remove question from hop content to avoid duplication
                hop_content_no_q = hop_content.replace(question, "").strip()
                
                question_first_structure = f"""
{question}

Analyze each of these segments to answer the above question:
{segment_block}

{instruction}

Analysis Guidelines:
{hop_content_no_q}
"""
                system_block = local_header
                user_block = question_first_structure + "\n\n" + local_footer
            else:
                # Fallback if question not found
                logging.warning(f"Question not found in hop {hop_idx} for question_first layout, using standard structure")
                system_block = local_header + "\n\n" + hop_content
                user_block = instruction + segment_block + "\n\n" + local_footer
                
        # NEW: Minimal system variations for batch mode
        elif layout == "minimal_segment_first":
            # Minimal system + segments before hop content
            system_block = "You are an expert claim-framing coder following a mandatory 12-step decision tree."
            user_block = local_header + "\n\n" + segment_block + "\n\n" + hop_content + "\n\n" + instruction + "\n\n" + local_footer
            
        elif layout == "minimal_question_twice":
            # Minimal system + question at start and end
            system_block = "You are an expert claim-framing coder following a mandatory 12-step decision tree."
            
            import re
            question_match = re.search(r"### Question Q\d+.*?(?=\n\*\*|\n\n|$)", hop_content, re.DOTALL)
            question = question_match.group(0) if question_match else f"Question Q{hop_idx}"
            
            primacy = f"{local_header}\n\n{question}\n\n{instruction}\n\nSEGMENTS:\n"
            recency = f"\n\nREMINDER - Answer this for EACH segment above: {question}"
            
            user_block = primacy + segment_block + "\n\n" + hop_content + recency + "\n\n" + local_footer
            
        elif layout == "minimal_json_segment":
            # Minimal system + JSON structure for segments
            system_block = "You are an expert claim-framing coder following a mandatory 12-step decision tree."
            
            # Format segments as JSON array
            segment_block = _format_segments_for_batch(segments, "structured_json")  # Reuse JSON formatting
            
            user_block = f"{local_header}\n\nTask: {hop_content}\n\n{instruction}\n\nSegments:\n{segment_block}\n\n{local_footer}"
            
        elif layout == "minimal_parallel_criteria":
            # Minimal system + parallel YES/NO/UNCERTAIN framework
            system_block = "You are an expert claim-framing coder following a mandatory 12-step decision tree."
            
            parallel_instruction = f"""
{local_header}

Analyze each segment below using this framework:
- YES indicators: [Look for affirmative evidence per the question]
- NO indicators: [Look for negative evidence per the question]  
- UNCERTAIN: [When evidence is ambiguous or missing]

{instruction}

SEGMENTS:
"""
            user_block = parallel_instruction + segment_block + "\n\n" + hop_content + "\n\n" + local_footer
            
        elif layout == "minimal_hop_sandwich":
            # Minimal system + hop content before and after segments
            system_block = "You are an expert claim-framing coder following a mandatory 12-step decision tree."
            
            import re
            question_match = re.search(r"### Question Q\d+.*?(?=\n\*\*|\n\n|$)", hop_content, re.DOTALL)
            question = question_match.group(0) if question_match else f"Question Q{hop_idx}"
            
            # Extract rules and examples
            rules_match = re.search(r"\*\*Rules?\*\*:?.*?(?=\n\*\*|\n###|$)", hop_content, re.DOTALL)
            rules = rules_match.group(0) if rules_match else ""
            
            examples_match = re.search(r"\*\*Examples?\*\*:?.*?(?=\n\*\*|\n###|$)", hop_content, re.DOTALL)
            examples = examples_match.group(0) if examples_match else ""
            
            sandwich_structure = f"""
{local_header}

{question}
{rules}

Analyze these segments:
{segment_block}

{examples}

{instruction}
"""
            user_block = sandwich_structure + "\n\n" + local_footer
            
        else:
            raise ValueError(f"Unknown layout: {layout}")

        # Add ranking instruction if needed
        if ranked and not confidence_scores:
            ranking_instr = (
                "\nAfter the JSON object, add a new line starting with the word 'Ranking:' "
                "followed by up to {n} frame labels in descending order of likelihood, "
                "separated by the ' > ' character.  For example:\n"
                "Ranking: Alarmist > Neutral > Reassuring\n".format(n=max_candidates)
            )
            user_block = user_block + "\n\n" + ranking_instr

        # Optional: append explicit JSON-Schema to aid validation when flag is set
        if _REPLY_SCHEMA and layout.startswith("cue_detection_enhanced_json"):
            user_block += (
                "\n\n### Reply schema\n```json\n{\n  \"$schema\": \"https://json-schema.org/draft/2020-12/schema\",\n  \"type\": \"object\",\n  \"properties\": {\n    \"cue_map\": {\"type\": \"object\"},\n    \"answer\": {\"type\": \"string\"},\n    \"rationale\": {\"type\": \"string\"}\n  },\n  \"required\": [\"cue_map\", \"answer\", \"rationale\"]\n}\n```"
            )

        # --- Confidence score add-on (modular, no prompt template change) ---
        if confidence_scores:
            conf_instr = (
                "\n\nIn your JSON you **may** include an optional numeric field \"confidence\" "
                "(0-100) representing your certainty.  If confidence < 100 also add "
                "\"confidence_explanation\" – one short sentence explaining the main "
                "source of uncertainty.  If you are fully certain (100) omit the "
                "explanation."
            )
            user_block += conf_instr

        # Capture for offline inspection
        _capture_prompt(hop_idx, system_block, user_block)
        return system_block, user_block

    except FileNotFoundError:
        logging.error(f"Error: Prompt file not found for hop {hop_idx}")
        raise
    except Exception as e:
        logging.error(f"Error assembling batch prompt for hop {hop_idx}: {e}")
        raise

# Add the missing run_coding_step_tot function
def run_coding_step_tot(
    config: Dict, 
    input_csv_path: Path, 
    output_dir: Path, 
    limit: Optional[int] = None, 
    start: Optional[int] = None, 
    end: Optional[int] = None, 
    concurrency: int = 1, 
    model: str = "models/gemini-2.5-flash-preview-04-17", 
    provider: str = "gemini", 
    batch_size: int = 1, 
    regex_mode: str = "live", 
    shuffle_batches: bool = False, 
    shuffle_segments: bool = False,
    skip_eval: bool = False, 
    only_hop: Optional[int] = None,
    gold_standard_file: Optional[str] = None,
    *, 
    router: bool = False,
    template: str = "legacy",
    layout: str = "standard",
    print_summary: bool = True,
    token_accumulator: Optional[Dict] = None,
    token_lock: Optional[threading.Lock] = None,
    shutdown_event: Optional[threading.Event] = None,
    examples_policy: str = "full",
    reply_schema: bool = False,
) -> Tuple[None, Path]:
    """
    Main function to run the ToT pipeline on an input CSV and save results.
    Matches the expected return signature for a coding step in main.py.
    """
    if not _load_global_header():
        logging.critical("ToT pipeline cannot run because GLOBAL_HEADER.txt is missing or empty.")
        raise FileNotFoundError("prompts/GLOBAL_HEADER.txt is missing.")

    # --- Configure regex layer mode ---
    if regex_mode == "off":
        _re_eng.set_global_enabled(False)
        logging.info("Regex layer DISABLED via --regex-mode off")
    else:
        _re_eng.set_global_enabled(True)
        if regex_mode == "shadow":
            _re_eng.set_force_shadow(True)
            logging.info("Regex layer set to SHADOW mode: rules will not short-circuit")
        else:
            logging.info("Regex layer in LIVE mode (default)")

    df = pd.read_csv(input_csv_path, dtype={'StatementID': str})
    
    # ------------------------------------------------------------------
    # Evaluation control: if the caller explicitly requests evaluation to
    # be skipped, we *pretend* the gold column is not present to ensure
    # all downstream evaluation logic is bypassed cleanly.
    # ------------------------------------------------------------------
    if skip_eval and 'Gold Standard' in df.columns:
        df = df.drop(columns=['Gold Standard'])

    # Evaluation is enabled only when the column exists *and* skip_eval is False
    has_gold_standard = (not skip_eval) and ('Gold Standard' in df.columns)
    
    # Store original dataframe size for logging
    original_size = len(df)
    
    # Apply range filtering if start/end specified
    if start is not None or end is not None:
        # Convert to 0-based indexing for pandas
        start_idx = (start - 1) if start is not None else 0
        end_idx = end if end is not None else len(df)
        
        # Validate range
        if start_idx < 0:
            logging.warning(f"Start index {start} is less than 1, using 1 instead")
            start_idx = 0
        if end_idx > len(df):
            logging.warning(f"End index {end} exceeds dataset size {len(df)}, using {len(df)} instead")
            end_idx = len(df)
        if start_idx >= end_idx:
            logging.error(f"Invalid range: start {start} >= end {end}")
            raise ValueError(f"Start index must be less than end index")
        
        # Apply range slice
        df = df.iloc[start_idx:end_idx].copy()
        logging.info(f"Applied range filter: processing rows {start_idx + 1}-{end_idx} ({len(df)} statements from original {original_size})")
        
    # Apply limit if specified (after range filtering)
    elif limit is not None:
        df = df.head(limit)
        logging.info(f"Applied limit: processing {len(df)} statements (limited from {original_size})")
    else:
        logging.info(f"Processing all {len(df)} statements")
    
    # Select and initialize provider
    provider_name = config.get("runtime_provider", provider)  # Use runtime config if available
    
    if provider_name == "openrouter":
        llm_provider = OpenRouterProvider()
        logging.info("Initialized OpenRouter provider")
    else:
        llm_provider = GeminiProvider()
        logging.info("Initialized Gemini provider")

    results = []
    
    # Use provided token accumulator or create new one
    if token_accumulator is None:
        token_accumulator = {
            'prompt_tokens': 0,
            'response_tokens': 0,
            'thought_tokens': 0,
            'total_tokens': 0,
            # Regex vs LLM utilisation counters
            'total_hops': 0,
            'regex_yes': 0,   # times regex produced a definitive yes
            'regex_hit_shadow': 0,  # regex fired in shadow mode (does not short-circuit)
            'llm_calls': 0,   # times we hit the LLM
            'segments_regex_ids': set(),  # unique statement IDs resolved by regex at least once
        }
    
    if token_lock is None:
        token_lock = threading.Lock()

    trace_dir = output_dir / "traces_tot"
    trace_dir.mkdir(parents=True, exist_ok=True)
    logging.info(f"ToT trace files will be saved in: {trace_dir}")

    # Processing logic here - batch vs single
    if batch_size > 1:
        logging.info(f"Processing with batch size = {batch_size} and concurrency={concurrency}")
        # For batch processing, we need to implement the batch logic
        # This is a simplified version - the full implementation would be more complex
        logging.warning("Batch processing not fully implemented in this version")
        
    # Single-segment processing
    if concurrency == 1:
        # Sequential processing
        for _, row in df.iterrows():
            if shutdown_event and shutdown_event.is_set():
                logging.info("Shutdown requested, stopping processing...")
                break
                
            final_context = run_tot_chain(
                row, llm_provider, trace_dir, model, 
                token_accumulator, token_lock, TEMPERATURE,
                template=template, layout=layout
            )
            final_json = {
                "StatementID": final_context.statement_id,
                "Pipeline_Result": final_context.final_frame,
                "Pipeline_Justification": final_context.final_justification,
                "Full_Reasoning_Trace": json.dumps(final_context.reasoning_trace)
            }
            results.append(final_json)
    else:
        # Concurrent processing
        logging.info(f"Using concurrent processing with {concurrency} workers")
        def process_single_statement(row_tuple):
            _, row = row_tuple
            if provider_name == "openrouter":
                thread_provider = OpenRouterProvider()
            else:
                thread_provider = GeminiProvider()
            final_context = run_tot_chain(
                row, thread_provider, trace_dir, model, 
                token_accumulator, token_lock, TEMPERATURE,
                template=template, layout=layout
            )
            final_json = {
                "StatementID": final_context.statement_id,
                "Pipeline_Result": final_context.final_frame,
                "Pipeline_Justification": final_context.final_justification,
                "Full_Reasoning_Trace": json.dumps(final_context.reasoning_trace)
            }
            return final_json
            
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            future_to_row = {
                executor.submit(process_single_statement, row_tuple): row_tuple[1]['StatementID'] 
                for row_tuple in df.iterrows()
            }
            
            for future in as_completed(future_to_row):
                if shutdown_event and shutdown_event.is_set():
                    logging.info("Shutdown requested, cancelling remaining tasks...")
                    for f in future_to_row:
                        f.cancel()
                    break
                    
                statement_id = future_to_row[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as exc:
                    logging.error(f"Statement {statement_id} generated an exception: {exc}")
                    results.append({
                        "StatementID": statement_id,
                        "Pipeline_Result": "LABEL_UNCERTAIN",
                        "Pipeline_Justification": f"Processing failed: {exc}",
                        "Full_Reasoning_Trace": "[]"
                    })

    # Save final labels to CSV
    df_results = pd.DataFrame(results)
    majority_labels_path = output_dir / f"model_labels_tot.csv"
    df_results.to_csv(majority_labels_path, index=False)
    
    # In this deterministic (VOTES=1) setup, there is no separate raw votes file.
    raw_votes_path = None

    logging.info(f"ToT processing complete. Labels saved to: {majority_labels_path}")
    
    # --- Token usage summary ---
    if print_summary:
        print("\n📏 Token usage:")
        print(f"Prompt  : {token_accumulator.get('prompt_tokens', 0)}")
        print(f"Response: {token_accumulator.get('response_tokens', 0)}")
        print(f"Thought : {token_accumulator.get('thought_tokens', 0)}")
        print(f"Total   : {token_accumulator.get('total_tokens', 0)}")

    # --- Dump captured prompts for debugging ---
    try:
        _dump_captured_prompts(output_dir)
    except Exception as exc:
        logging.error("Failed to dump captured prompts: %s", exc)

    return raw_votes_path, majority_labels_path

# Add regex engine instance
_re_eng = RegexEngine.default()

# Add missing constants
START_TIME = time.perf_counter()

# Progress tracking constant
_MISS_PATH: Optional[Path] = None

# Extract frame from answer if it's a ranking list
def _extract_frame_and_ranking(answer_text: str) -> Tuple[Optional[str], Optional[List[str]]]:
    """Extract frame label and optional ranking from answer text.
    
    Returns:
        Tuple of (frame_label, ranking_list)
        - frame_label: The primary frame label (first in ranking or standalone)
        - ranking_list: List of frames in order of likelihood, or None if not ranked
    """
    if not answer_text:
        return None, None
        
    # Check if this is a ranking response
    lines = answer_text.strip().split('\n')
    
    # Look for explicit ranking line
    for line in lines:
        if line.strip().startswith('Ranking:'):
            ranking_text = line.replace('Ranking:', '').strip()
            # Parse ranking like "Alarmist > Neutral > Reassuring"
            frames = [f.strip() for f in ranking_text.split('>')]
            if frames:
                return frames[0], frames
    
    # If no ranking, treat the entire answer as the frame
    frame = answer_text.strip()
    
    # Validate frame is one of the expected values
    valid_frames = {"Alarmist", "Reassuring", "Neutral", "Variable", "LABEL_UNCERTAIN"}
    if frame in valid_frames:
        return frame, None
    
    # Try to extract frame from common patterns
    # e.g., "The frame is Alarmist" or "Frame: Neutral"
    import re
    frame_pattern = r'(?:frame\s*(?:is|:)\s*)?(Alarmist|Reassuring|Neutral|Variable|LABEL_UNCERTAIN)'
    match = re.search(frame_pattern, answer_text, re.IGNORECASE)
    if match:
        return match.group(1).capitalize(), None
    
    # If we can't parse it, return None
    return None, None

# Add missing _log_hop function
def _log_hop(hop_idx: int, active: int, regex_yes: int, batch_size: int = 0):
    """Log hop progress with timing information."""
    elapsed = time.perf_counter() - START_TIME
    if batch_size > 0:
        msg = f"Hop {hop_idx:02} → active:{active:<4} regex_yes:{regex_yes:<3} batch_size:{batch_size:<3} ({elapsed:5.1f}s)"
    else:
        msg = f"Hop {hop_idx:02} → active:{active:<4} regex_yes:{regex_yes:<3} ({elapsed:5.1f}s)"
    logging.info(msg)

# ---------------------------------------------------------------------------
# Prompt capture for post-mortem debugging
# ---------------------------------------------------------------------------

# Store the *first* fully-assembled prompt we build for each hop index so we
# can save them to disk at the end of the run.  This lets users inspect the
# exact prompt the LLM received (including substituted segment text, header,
# footer, etc.) without turning on verbose logging.

_CAPTURED_PROMPTS: dict[int, str] = {}
_CAPTURE_LOCK = threading.Lock()


def _capture_prompt(hop_idx: int, system_block: str, user_prompt: str) -> None:
    """Save the very first fully-constructed prompt for *hop_idx*.

    Thread-safe and idempotent – once a hop index is stored we keep the first
    version to avoid redundant disk usage (prompts are usually identical per
    hop anyway).
    """
    if hop_idx in _CAPTURED_PROMPTS:
        return
    with _CAPTURE_LOCK:
        if hop_idx in _CAPTURED_PROMPTS:  # double-check after locking
            return
        full = f"""===== SYSTEM PROMPT =====\n{system_block}\n\n===== USER PROMPT =====\n{user_prompt}\n"""
        _CAPTURED_PROMPTS[hop_idx] = full


def _dump_captured_prompts(output_dir: Path) -> None:
    """Write captured prompts (max 12) to <output_dir>/assembled_prompts."""
    if not _CAPTURED_PROMPTS:
        logging.info("No prompts captured – skip dump.")
        return

    dump_dir = output_dir / "assembled_prompts"
    dump_dir.mkdir(parents=True, exist_ok=True)
    for hop_idx, prompt_txt in sorted(_CAPTURED_PROMPTS.items()):
        file_path = dump_dir / f"hop_Q{hop_idx:02}_prompt.txt"
        try:
            file_path.write_text(prompt_txt, encoding="utf-8")
        except Exception as exc:
            logging.error("Failed to write prompt dump for hop %s: %s", hop_idx, exc)
    logging.info("Saved %s assembled prompts to %s", len(_CAPTURED_PROMPTS), dump_dir)

