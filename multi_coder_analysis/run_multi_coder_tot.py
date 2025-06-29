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
    'minimal_parallel_criteria', 'minimal_hop_sandwich'
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
            question_match = re.search(r"### Question Q\d+.*?(?=\n)", hop_body)
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

"""
            hop_clean = hop_body.replace("### Segment (StatementID: {{statement_id}})\n{{segment_text}}", "").replace("{{statement_id}}", ctx.statement_id)
            user_prompt = local_header + "\n\n" + segment_section + analysis_frame + hop_clean
            
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
            user_prompt = user_prompt + "\n\n" + ranking_instr

        user_block = user_prompt + "\n\n" + local_footer
        return system_block, user_block

    except FileNotFoundError:
        logging.error(f"Error: Prompt file not found for Q{ctx.q_idx} at {hop_file}")
        raise
    except Exception as e:
        logging.error(f"Error assembling prompt for Q{ctx.q_idx}: {e}")
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
        choice, ranking = _extract_frame_and_ranking(raw_answer_text)

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

{examples}

{instruction}

=== ANALYZE THESE SEGMENTS ===
{segment_block}
=== REMEMBER THE QUESTION ===

{question}

REMINDER: {rules}
"""
            user_block = sandwich_structure + "\n\n" + local_footer
                
        else:
            # For other layouts, fall back to standard in batch mode
            logging.warning(f"Layout '{layout}' not fully supported in batch mode, using standard layout")
            system_block = local_header + "\n\n" + hop_content
            user_block = instruction + segment_block + "\n\n" + local_footer
            
        return system_block, user_block
    except Exception as e:
        logging.error(f"Error assembling batch prompt for Q{hop_idx}: {e}")
        raise

# --- NEW: Batch LLM Call ---

def _call_llm_batch(batch_ctx, provider, model: str, temperature: float = TEMPERATURE, *, template: str = "legacy", ranked: bool = False, max_candidates: int = 5, confidence_scores: bool = False, layout: str = "standard"):
    """Call the LLM on a batch of segments for a single hop and parse the JSON list response."""
    sys_prompt, user_prompt = _assemble_prompt_batch(
        batch_ctx.segments, 
        batch_ctx.hop_idx, 
        template=template, 
        ranked=ranked, 
        max_candidates=max_candidates,
        confidence_scores=confidence_scores,
        layout=layout
    )
    batch_ctx.raw_prompt = sys_prompt

    unresolved = list(batch_ctx.segments)
    collected: list[dict] = []

    attempt = 0
    consecutive_none = 0  # track consecutive None/empty responses
    while unresolved and attempt < MAX_RETRIES:
        attempt += 1
        sys_prompt, user_prompt = _assemble_prompt_batch(
            unresolved, 
            batch_ctx.hop_idx, 
            template=template, 
            ranked=ranked, 
            max_candidates=max_candidates,
            confidence_scores=confidence_scores,
            layout=layout
        )
        try:
            size_requested = len(unresolved)

            try:
                raw_text = provider.generate(sys_prompt, user_prompt, model, temperature)
            except Exception as e:
                logging.warning(f"Error generating batch response: {e}")
                raise

            if not raw_text.strip():
                raise ValueError("Empty response from LLM")

            content = raw_text.strip()
            if content.startswith('```json') and content.endswith('```'):
                content = content[7:-3].strip()
            elif content.startswith('```') and content.endswith('```'):
                content = content[3:-3].strip()

            try:
                parsed = json.loads(content)
                if not isinstance(parsed, list):
                    raise ValueError("Batch response is not a JSON array")
            except json.JSONDecodeError as dex:
                # ------------------------------------------------------
                # Truncated / malformed JSON – attempt best-effort salvage
                # ------------------------------------------------------
                import re as _re, json as _json

                obj_txts = _re.findall(r"\{[^{}]*\}", content)
                parsed = []
                for _frag in obj_txts:
                    try:
                        parsed.append(_json.loads(_frag))
                    except Exception:
                        # Skip fragments that still fail to parse
                        continue

                logging.warning(
                    f"Batch {batch_ctx.batch_id} Q{batch_ctx.hop_idx:02}: salvaged {len(parsed)} objects from truncated JSON (original error: {dex})"
                )

                if not parsed:
                    raise  # re-raise to trigger retry logic

            # Basic validation & matching
            valid_objs = []
            returned_ids = set()
            for obj in parsed:
                if not all(k in obj for k in ("segment_id", "answer", "rationale")):
                    continue  # skip malformed entry
                sid = str(obj["segment_id"]).strip()
                returned_ids.add(sid)
                valid_objs.append(obj)

            collected.extend(valid_objs)

            # Filter unresolved list to those still missing
            unresolved = [c for c in unresolved if c.statement_id not in returned_ids]

            # store raw for first attempt only to keep size small
            if attempt == 1:
                batch_ctx.raw_http = raw_text  # type: ignore[attr-defined]

            # Include the original `size_requested` denominator so users can easily
            # spot discrepancies across batches/permutations (helpful when regex
            # pre-filtering removes items before the LLM call).
            logging.info(
                f"Batch {batch_ctx.batch_id} Q{batch_ctx.hop_idx:02}: attempt {attempt} succeeded for {len(valid_objs)}/{size_requested} objects; still missing {len(unresolved)}/{size_requested}"
            )

        except Exception as e:
            # Preserve raw response for diagnostics even when parsing fails or provider errors
            if attempt == 1 and not hasattr(batch_ctx, 'raw_http'):
                # Best-effort capture of whatever content we have
                try:
                    batch_ctx.raw_http = raw_text  # type: ignore[attr-defined]
                except Exception:
                    batch_ctx.raw_http = f"<no response captured – {e}>"  # type: ignore[attr-defined]

            # Track consecutive None-type failures to trigger cool-down
            if isinstance(e, TypeError) and "NoneType" in str(e):
                consecutive_none += 1
            else:
                consecutive_none = 0

            logging.warning(
                f"Batch {batch_ctx.batch_id} Q{batch_ctx.hop_idx:02}: attempt {attempt} failed: {e} (missing {len(unresolved)} segments)"
            )

            # Short-circuit: after 2 consecutive None failures, signal caller
            if consecutive_none >= 2:
                batch_ctx._cooldown_required = True  # type: ignore[attr-defined]
                break

            time.sleep(BACKOFF_FACTOR * (2 ** (attempt - 1)))

    # mark any still-unresolved segments as uncertain
    for ctx in unresolved:
        collected.append({
            "segment_id": ctx.statement_id,
            "answer": "uncertain",
            "rationale": "LLM call failed after incremental retries."})

    # NEW: expose attempts used to caller
    batch_ctx.attempts_used = attempt

    return collected

# --- NEW: Batch Orchestration with Concurrency ---

def run_tot_chain_batch(
    df: pd.DataFrame,
    provider_name: str,
    trace_dir: Path,
    model: str,
    batch_size: int = 10,
    concurrency: int = 1,
    token_accumulator: dict = None,
    token_lock: threading.Lock = None,
    temperature: float = TEMPERATURE,
    *,
    template: str = "legacy",
    shuffle_batches: bool = False,
    shuffle_segments: bool = False,  # NEW: Fine-grained segment shuffling
    hop_range: Optional[list[int]] = None,
    layout: str = "standard",  # NEW: Layout parameter
    ranked: bool = False,  # NEW: Ranking parameter
    max_candidates: int = 5,  # NEW: Max candidates for ranking
    confidence_scores: bool = False,  # NEW: Confidence scores parameter
) -> List[HopContext]:
    """Process dataframe through the 12-hop chain using batching with optional concurrency.
    Returns (contexts, summary_dict).
    The summary dict aggregates high-level stats (batches, duplicates, residuals, tokens …) that
    the caller can serialize into a run-level report.
    """
    # Build HopContext objects
    contexts: List[HopContext] = [
        HopContext(
            statement_id=row["StatementID"],
            segment_text=row["Statement Text"],
            article_id=row.get("ArticleID", "")
        )
        for _, row in df.iterrows()
    ]
    
    # Initialize progress tracker
    progress_tracker = ProgressTracker(len(contexts), len(hop_range) if hop_range else 12)


    # NEW: collect batches that ultimately failed after MAX_RETRIES so we can write a run-level summary later
    failed_batches: List[dict] = []
    long_retry_batches: List[dict] = []

    def _provider_factory():
        return get_provider(provider_name)

    # --- aggregated run-level counters -------------------------------------------
    # (run-level summary aggregation removed; will be handled after processing)

    def _process_batch(batch_segments: List[HopContext], hop_idx: int):
        """Process a single batch of segments for the given hop."""
        batch_id = f"batch_{hop_idx}_{uuid.uuid4().hex[:6]}"
        
        # Assign batch metadata to each segment
        for i, seg in enumerate(batch_segments):
            seg.batch_id = batch_id  # type: ignore[attr-defined]
            seg.batch_size = len(batch_segments)  # type: ignore[attr-defined] 
            seg.batch_pos = i  # type: ignore[attr-defined]

        # Clear hop tracking flags
        for seg in batch_segments:
            seg._resolved_by_regex_this_hop = False  # type: ignore[attr-defined]
            seg._resolved_by_llm_this_hop = False  # type: ignore[attr-defined]

        # Track LLM calls for token accumulator
        token_accumulator['llm_calls'] += 1
        
        # Step 1: Check regex patterns for early resolution
        regex_resolved: List[HopContext] = []
        unresolved_segments: List[HopContext] = []
        regex_matches_meta: List[Dict] = []

        for seg_ctx in batch_segments:
            # Skip if already concluded from a previous hop
            if seg_ctx.is_concluded:
                continue
                
            # Query regex engine for this hop/segment combo
            seg_ctx.q_idx = hop_idx
            token_accumulator['total_hops'] += 1
            
            r_answer = None
            try:
                r_answer = _re_eng.match(seg_ctx)
            except Exception as e:
                logging.warning(f"Regex engine error on {seg_ctx.statement_id} Q{hop_idx}: {e}")
            
            if r_answer and r_answer.get("answer") == "yes":
                # Track that this segment was resolved by regex
                seg_ctx._resolved_by_regex_this_hop = True  # type: ignore[attr-defined]
                
                # Update token accumulator
                if _re_eng._FORCE_SHADOW:
                    token_accumulator['regex_hit_shadow'] += 1
                else:
                    token_accumulator['regex_yes'] += 1
                
                # Regex provided a definitive answer
                trace_entry = {
                    "Q": hop_idx,
                    "answer": r_answer["answer"],
                    "rationale": r_answer.get("rationale", "Regex match"),
                    "method": "regex",
                    "batch_id": batch_id,
                    "batch_size": seg_ctx.batch_size,
                    "batch_pos": seg_ctx.batch_pos,
                    "regex": r_answer.get("regex", {}),
                    # Include raw statement text and article ID for easier debugging across all traces
                    "statement_text": seg_ctx.segment_text,
                    "article_id": seg_ctx.article_id,
                }
                write_trace_log(trace_dir, seg_ctx.statement_id, trace_entry)
                
                seg_ctx.analysis_history.append(f"Q{hop_idx}: yes (regex)")
                seg_ctx.reasoning_trace.append(trace_entry)
                
                # Set final frame if this is a frame-determining hop and answer is yes
                if r_answer["answer"] == "yes" and hop_idx in Q_TO_FRAME:
                    seg_ctx.final_frame = r_answer.get("frame") or Q_TO_FRAME[hop_idx]
                    seg_ctx.is_concluded = True
                
                regex_resolved.append(seg_ctx)
                regex_matches_meta.append({
                    "statement_id": seg_ctx.statement_id,
                    "regex": r_answer.get("regex", {}),
                    "frame": r_answer.get("frame"),
                    "answer": r_answer["answer"],
                })
            else:
                # No definitive regex answer → send to LLM later
                unresolved_segments.append(seg_ctx)
        
        
        # Update progress
        progress_tracker.update(len(batch_segments), hop_idx)
        
        # Step 2: If any segments remain unresolved, call LLM for the batch
        # Before LLM call, dump regex matches for this batch (if any)
        if regex_matches_meta:
            import json as _json
            batch_dir = trace_dir / "batch_traces"
            batch_dir.mkdir(parents=True, exist_ok=True)
            regex_path = batch_dir / f"{batch_id}_Q{hop_idx:02}_regex.json"
            try:
                with regex_path.open("w", encoding="utf-8") as fh:
                    _json.dump({
                        "batch_id": batch_id,
                        "hop_idx": hop_idx,
                        "segment_count": len(regex_matches_meta),
                        "matches": regex_matches_meta,
                    }, fh, ensure_ascii=False, indent=2)
            except Exception as e:
                logging.warning("Could not write regex batch trace %s: %s", regex_path, e)

        if unresolved_segments:
            # Create batch context
            batch_ctx = BatchHopContext(batch_id=batch_id, hop_idx=hop_idx, segments=unresolved_segments)
            
            # Call LLM for the batch
            provider_inst = _provider_factory()

            # --------------------------------------------------
            # Cool-down logic: if _call_llm_batch marks the batch
            # with `_cooldown_required`, we wait 5 minutes and then
            # retry *once*. If the subsequent call again sets the
            # flag we repeat (max 3 cycles to avoid infinite loop).
            # --------------------------------------------------
            cooldown_cycles = 0
            while True:
                batch_responses = _call_llm_batch(batch_ctx, provider_inst, model, temperature, template=template, ranked=ranked, max_candidates=max_candidates, confidence_scores=confidence_scores, layout=layout)

                if getattr(batch_ctx, "_cooldown_required", False):
                    cooldown_cycles += 1
                    if cooldown_cycles > 3:
                        logging.warning(
                            "Batch %s Q%02d: exceeded max cool-down cycles (%s) – marking remaining %s segments uncertain",
                            batch_id,
                            hop_idx,
                            cooldown_cycles,
                            len(unresolved_segments),
                        )
                        break  # give up after marking uncertain later in code

                    # Clear flag for next attempt
                    delattr(batch_ctx, "_cooldown_required")
                    delay_sec = {1: 300, 2: 600, 3: 900}.get(cooldown_cycles, 900)
                    human_delay = f"{delay_sec//60} minute(s)"
                    logging.info(
                        "Batch %s Q%02d: entering %s cool-down (cycle %s)…",
                        batch_id,
                        hop_idx,
                        human_delay,
                        cooldown_cycles,
                    )
                    time.sleep(delay_sec)
                    provider_inst = _provider_factory()  # fresh client after wait
                    continue  # retry batch

                break  # normal path – no cool-down requested

            # NEW: record batches that consumed >3 retries
            attempts_used = getattr(batch_ctx, 'attempts_used', None)
            if attempts_used and attempts_used > 3:
                retry_stat = {
                    "batch_id": batch_id,
                    "hop_idx": hop_idx,
                    "retries_used": attempts_used,
                }
                if token_lock:
                    with token_lock:
                        long_retry_batches.append(retry_stat)
                else:
                    long_retry_batches.append(retry_stat)

            # Token accounting (prompt/response/thought)
            usage = provider_inst.get_last_usage()
            if usage and token_lock:
                with token_lock:
                    token_accumulator['prompt_tokens'] += usage.get('prompt_tokens', 0)
                    token_accumulator['response_tokens'] += usage.get('response_tokens', 0)
                    token_accumulator['thought_tokens'] += usage.get('thought_tokens', 0)
                    token_accumulator['total_tokens'] += usage.get('total_tokens', 0)
            
            # Build lookup for faster association
            sid_to_ctx = {c.statement_id: c for c in unresolved_segments}
            unknown_responses = []  # responses whose segment_id not in batch
            # Track duplicate answers for the same segment_id within this batch
            processed_sid_answers: dict[str, list[str]] = {}
            duplicates_meta: list[dict] = []

            for resp_obj in batch_responses:
                sid = str(resp_obj.get("segment_id", "")).strip()
                ctx = sid_to_ctx.get(sid)
                if ctx is None:
                    unknown_responses.append(resp_obj)
                    continue  # skip unknown ids

                # Check for duplicate answers with conflicting content
                answer_raw = str(resp_obj.get("answer", "uncertain")).lower().strip()
                prev_answers = processed_sid_answers.get(sid)
                if prev_answers is not None and answer_raw not in prev_answers:
                    logging.warning(
                        f"Duplicate responses for {sid} in batch {batch_id} Q{hop_idx}: prev='{prev_answers}' new='{answer_raw}'. Keeping last."
                    )
                    duplicates_meta.append({
                        "segment_id": sid,
                        "prev_answers": prev_answers,
                        "new_answer": answer_raw,
                    })
                # Append current answer to list (deduplicated)
                processed_sid_answers.setdefault(sid, [])
                if answer_raw not in processed_sid_answers[sid]:
                    processed_sid_answers[sid].append(answer_raw)

                answer = answer_raw
                rationale = str(resp_obj.get("rationale", "No rationale provided"))
                
                trace_entry = {
                    "Q": hop_idx,
                    "answer": answer,
                    "rationale": rationale,
                    "method": "llm_batch",
                    "batch_id": batch_id,
                    "batch_size": ctx.batch_size,
                    "batch_pos": ctx.batch_pos,
                    # Include raw statement text and article ID for easier debugging across all traces
                    "statement_text": ctx.segment_text,
                    "article_id": ctx.article_id,
                }
                write_trace_log(trace_dir, ctx.statement_id, trace_entry)
                
                ctx.analysis_history.append(f"Q{hop_idx}: {answer}")
                ctx.reasoning_trace.append(trace_entry)
                
                # Check for early termination
                if answer == "uncertain":
                    ctx.uncertain_count += 1
                    if ctx.uncertain_count >= 3:
                        logging.warning(
                            f"ToT chain terminated at Q{hop_idx} due to 3 consecutive 'uncertain' responses."
                        )
                        ctx.final_frame = "LABEL_UNCERTAIN"
                        ctx.final_justification = "Three consecutive uncertain responses"
                        continue
                
                # ──────────────────────────────────────────────────────────
                # HOP‑11 SPECIAL‑CASE — token‑guard then safe fallback
                # ──────────────────────────────────────────────────────────
                if answer == "yes" and hop_idx == 11:
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
                elif answer == "yes" and hop_idx in Q_TO_FRAME:
                    ctx.final_frame = Q_TO_FRAME[hop_idx]
                    ctx.final_justification = (
                        f"Frame determined by Q{hop_idx} trigger. Rationale: {rationale}"
                    )
                    ctx.is_concluded = True
                    ctx._resolved_by_llm_this_hop = True

            # Any ctx not covered by response → mark uncertain
            for ctx in unresolved_segments:
                if ctx.statement_id not in sid_to_ctx or all(r.get("segment_id") != ctx.statement_id for r in batch_responses):
                    trace_entry = {
                        "hop_idx": hop_idx,
                        "answer": "uncertain",
                        "rationale": "Missing response from batch",
                        "method": "fallback",
                        "batch_id": batch_id,
                        "batch_size": ctx.batch_size,
                        "batch_pos": ctx.batch_pos,
                        # Include raw statement text and article ID for easier debugging across all traces
                        "statement_text": ctx.segment_text,
                        "article_id": ctx.article_id,
                    }
                    write_trace_log(trace_dir, ctx.statement_id, trace_entry)
            
            # Write batch trace
            batch_payload = {
                "batch_id": batch_id,
                "hop_idx": hop_idx,
                "segment_count": len(unresolved_segments),
                "responses": batch_responses,
                "timestamp": datetime.now().isoformat(),
            }
            write_batch_trace(trace_dir, batch_id, hop_idx, batch_payload)

            # Dump raw HTTP body if available
            raw_http_text = getattr(batch_ctx, 'raw_http', None)
            if raw_http_text:
                raw_dir = trace_dir / 'batch_traces'
                raw_dir.mkdir(parents=True, exist_ok=True)
                raw_path = raw_dir / f"{batch_id}_Q{hop_idx:02}_raw_http.txt"
                try:
                    raw_path.write_text(raw_http_text, encoding='utf-8')
                except Exception as e:
                    logging.warning('Could not write raw HTTP trace %s: %s', raw_path, e)

            # --------------------------------------------------------------
            # Retry path for any segments that failed to return a response
            # --------------------------------------------------------------
            MAX_MISS_RETRY = 3
            missing_ctxs = [c for c in unresolved_segments if c.statement_id not in sid_to_ctx or all(r.get("segment_id") != c.statement_id for r in batch_responses)]

            for retry_idx in range(1, MAX_MISS_RETRY + 1):
                if not missing_ctxs:
                    break  # all accounted for

                retry_batch_id = f"{batch_id}_r{retry_idx}"
                for ctx in missing_ctxs:
                    ctx.batch_id = retry_batch_id  # type: ignore[attr-defined]

                retry_ctx = BatchHopContext(batch_id=retry_batch_id, hop_idx=hop_idx, segments=missing_ctxs)

                provider_retry = _provider_factory()
                retry_resps = _call_llm_batch(retry_ctx, provider_retry, model, temperature, template=template, ranked=ranked, max_candidates=max_candidates, confidence_scores=confidence_scores, layout=layout)

                # token accounting
                usage_r = provider_retry.get_last_usage()
                if usage_r and token_lock:
                    with token_lock:
                        token_accumulator['prompt_tokens'] += usage_r.get('prompt_tokens', 0)
                        token_accumulator['response_tokens'] += usage_r.get('response_tokens', 0)
                        token_accumulator['thought_tokens'] += usage_r.get('thought_tokens', 0)
                        token_accumulator['total_tokens'] += usage_r.get('total_tokens', 0)

                # Map again
                sid_to_ctx_retry = {c.statement_id: c for c in missing_ctxs}
                new_missing = []

                for r_obj in retry_resps:
                    sid_r = str(r_obj.get("segment_id", "")).strip()
                    ctx_r = sid_to_ctx_retry.get(sid_r)
                    if ctx_r is None:
                        unknown_responses.append(r_obj)
                        continue
                    answer_r = str(r_obj.get("answer", "uncertain")).lower().strip()
                    rationale_r = str(r_obj.get("rationale", "No rationale provided"))

                    trace_entry_r = {
                        "Q": hop_idx,
                        "answer": answer_r,
                        "rationale": rationale_r,
                        "method": "llm_batch_retry",
                        "retry": retry_idx,
                        "batch_id": retry_batch_id,
                        "batch_size": ctx_r.batch_size,
                        "batch_pos": ctx_r.batch_pos,
                        # Include raw statement text and article ID for easier debugging across all traces
                        "statement_text": ctx_r.segment_text,
                        "article_id": ctx_r.article_id,
                    }
                    write_trace_log(trace_dir, ctx_r.statement_id, trace_entry_r)

                    ctx_r.analysis_history.append(f"Q{hop_idx}: {answer_r} (retry{retry_idx})")
                    ctx_r.reasoning_trace.append(trace_entry_r)

                    # ──────────────────────────────────────────────────────────
                    # HOP‑11 SPECIAL‑CASE — token‑guard then safe fallback (retry)
                    # ──────────────────────────────────────────────────────────
                    if answer_r == "yes" and hop_idx == 11:
                        token = re.search(r"\|\|FRAME=(Alarmist|Reassuring)\b", rationale_r)
                        if token:
                            ctx_r.final_frame = token.group(1)
                            ctx_r.final_justification = (
                                f"Frame determined by Q11 explicit token {token.group(0)}."
                            )
                        else:
                            logging.warning(
                                "Q11 answered 'yes' but missing ||FRAME token; "
                                "defaulting to Neutral  (SID=%s)", ctx_r.statement_id
                            )
                            ctx_r.final_frame = "Neutral"
                            ctx_r.final_justification = (
                                "Hop 11 'yes' without explicit token – forced Neutral."
                            )
                        ctx_r.is_concluded = True
                        ctx_r._resolved_by_llm_this_hop = True

                    # All other hops use the static map
                    elif answer_r == "yes" and hop_idx in Q_TO_FRAME:
                        ctx_r.final_frame = Q_TO_FRAME[hop_idx]
                        ctx_r.is_concluded = True
                        ctx_r._resolved_by_llm_this_hop = True
                # dump retry batch trace and raw http
                retry_payload = {
                    "batch_id": retry_batch_id,
                    "hop_idx": hop_idx,
                    "segment_count": len(missing_ctxs),
                    "responses": retry_resps,
                    "timestamp": datetime.now().isoformat(),
                }
                write_batch_trace(trace_dir, retry_batch_id, hop_idx, retry_payload)
                raw_http_retry = getattr(retry_ctx, 'raw_http', None)
                if raw_http_retry:
                    raw_path_r = trace_dir / 'batch_traces' / f"{retry_batch_id}_Q{hop_idx:02}_raw_http.txt"
                    try:
                        raw_path_r.write_text(raw_http_retry, encoding='utf-8')
                    except Exception as e:
                        logging.warning('Could not write raw HTTP retry trace %s: %s', raw_path_r, e)

                # determine still missing
                missing_ctxs = [c for c in missing_ctxs if not any(resp.get('segment_id') == c.statement_id for resp in retry_resps)]

            # If still missing after retries, they'll retain fallback uncertain entry set earlier

            # Dump residual unknown responses if any
            if unknown_responses:
                import json as _json
                residual_path = trace_dir / "batch_traces" / f"{batch_id}_Q{hop_idx:02}_residual.json"
                try:
                    with residual_path.open("w", encoding="utf-8") as fh:
                        _json.dump({
                            "batch_id": batch_id,
                            "hop_idx": hop_idx,
                            "unknown_count": len(unknown_responses),
                            "unknown_responses": unknown_responses,
                        }, fh, ensure_ascii=False, indent=2)
                except Exception as e:
                    logging.warning("Could not write residual file %s: %s", residual_path, e)

            # Dump duplicate-answer diagnostics if any were detected
            if duplicates_meta:
                import json as _json
                dup_path = trace_dir / "batch_traces" / f"{batch_id}_Q{hop_idx:02}_duplicates.json"
                try:
                    with dup_path.open("w", encoding="utf-8") as fh:
                        _json.dump({
                            "batch_id": batch_id,
                            "hop_idx": hop_idx,
                            "duplicate_count": len(duplicates_meta),
                            "duplicates": duplicates_meta,
                        }, fh, ensure_ascii=False, indent=2)
                except Exception as e:
                    logging.warning("Could not write duplicate file %s: %s", dup_path, e)

            # ------------------------------------------------------------------
            # 📝  NEW: human-readable summary file for the batch
            # ------------------------------------------------------------------
            try:
                summary_path = trace_dir / "batch_traces" / f"{batch_id}_Q{hop_idx:02}_summary.txt"

                batch_ids = [c.statement_id for c in batch_segments]
                regex_ids = [c.statement_id for c in regex_resolved]
                llm_sent_ids = [c.statement_id for c in unresolved_segments]
                returned_ids = list(processed_sid_answers.keys())
                missing_ids = [sid for sid in llm_sent_ids if sid not in returned_ids]
                residual_ids = [str(r.get("segment_id")) for r in unknown_responses]

                with summary_path.open("w", encoding="utf-8") as sf:
                    sf.write(f"Batch ID         : {batch_id}\n")
                    sf.write(f"Hop              : Q{hop_idx:02}\n")
                    sf.write(f"Total segments   : {len(batch_ids)}\n")
                    sf.write(f"Regex-resolved   : {len(regex_ids)}\n")
                    sf.write(f"Sent to LLM      : {len(llm_sent_ids)}\n")
                    sf.write(f"Returned by LLM  : {len(returned_ids)}\n")
                    sf.write(f"Missing in reply : {len(missing_ids)}\n")
                    sf.write(f"Residual (extra) : {len(residual_ids)}\n")
                    sf.write("\n=== ID LISTS ===\n")
                    def _dump(name, ids):
                        sf.write(f"\n{name} ({len(ids)}):\n")
                        for _id in ids:
                            sf.write(f"  {_id}\n")

                    _dump("Batch IDs", batch_ids)
                    _dump("Regex-resolved IDs", regex_ids)
                    _dump("Sent to LLM IDs", llm_sent_ids)
                    _dump("Returned IDs", returned_ids)
                    _dump("Missing IDs", missing_ids)
                    _dump("Residual IDs", residual_ids)
                    sf.write(f"Duplicate conflicts : {len(duplicates_meta)}\n")

                # NEW: capture batches that still have missing IDs after final retry
                if missing_ids:
                    failed_rec = {
                        "batch_id": batch_id,
                        "hop_idx": hop_idx,
                        "missing_count": len(missing_ids),
                        "missing_ids": missing_ids,
                    }
                    if token_lock:
                        with token_lock:
                            failed_batches.append(failed_rec)
                    else:
                        failed_batches.append(failed_rec)
            except Exception as e:
                logging.warning("Could not write batch summary %s: %s", summary_path, e)
        
        # Return all segments (resolved + unresolved)
        return regex_resolved + unresolved_segments

    active_contexts: List[HopContext] = contexts[:]

    _hop_iter = hop_range if hop_range else range(1, 13)
    for hop_idx in _hop_iter:
        active_contexts = [c for c in active_contexts if not c.is_concluded]
        if not active_contexts:
            break

        # Optional randomisation to spread heavy segments across batches
        if shuffle_batches:
            random.shuffle(active_contexts)

        # Build batches of current active segments
        batches: List[List[HopContext]] = [
            active_contexts[i : i + batch_size] for i in range(0, len(active_contexts), batch_size)
        ]

        # NEW: Enhanced stochasticity - shuffle segments within each batch
        if shuffle_segments:
            for batch in batches:
                random.shuffle(batch)
        
        # NEW: Alternative approach - shuffle batch order for load balancing
        if shuffle_batches and len(batches) > 1:
            random.shuffle(batches)

        logging.info(
            f"Hop {hop_idx}: processing {len(batches)} batches (size={batch_size}) with concurrency={concurrency}"
        )

        # Print START banner
        print(f"*** START Hop {hop_idx:02} → start:{len(active_contexts)} regex:0 llm:0 remain:{len(active_contexts)} ***", flush=True)

        # PHASE 1: Process ALL regex first across all segments
        regex_resolved_segments: List[HopContext] = []
        llm_pending_segments: List[HopContext] = []
        
        for seg_ctx in active_contexts:
            if seg_ctx.is_concluded:
                continue
                
            # Query regex engine for this hop/segment combo
            seg_ctx.q_idx = hop_idx
            token_accumulator['total_hops'] += 1
            
            r_answer = None
            try:
                r_answer = _re_eng.match(seg_ctx)
            except Exception as e:
                logging.warning(f"Regex engine error on {seg_ctx.statement_id} Q{hop_idx}: {e}")
            
            if r_answer and r_answer.get("answer") == "yes":
                # Track regex resolution
                seg_ctx._resolved_by_regex_this_hop = True  # type: ignore[attr-defined]
                
                # Update token accumulator
                if _re_eng._FORCE_SHADOW:
                    token_accumulator['regex_hit_shadow'] += 1
                else:
                    token_accumulator['regex_yes'] += 1
                
                # Create trace entry
                trace_entry = {
                    "Q": hop_idx,
                    "answer": r_answer["answer"],
                    "rationale": r_answer.get("rationale", "Regex match"),
                    "method": "regex",
                    "regex": r_answer.get("regex", {}),
                    "statement_text": seg_ctx.segment_text,
                    "article_id": seg_ctx.article_id,
                }
                write_trace_log(trace_dir, seg_ctx.statement_id, trace_entry)
                
                seg_ctx.analysis_history.append(f"Q{hop_idx}: yes (regex)")
                seg_ctx.reasoning_trace.append(trace_entry)
                
                # Set final frame if this is a frame-determining hop
                if hop_idx in Q_TO_FRAME:
                    seg_ctx.final_frame = r_answer.get("frame") or Q_TO_FRAME[hop_idx]
                    seg_ctx.is_concluded = True
                
                regex_resolved_segments.append(seg_ctx)
            else:
                # No regex match → needs LLM processing
                llm_pending_segments.append(seg_ctx)

        # Print REGEX banner immediately after regex processing
        regex_count = len(regex_resolved_segments)
        if regex_count > 0:
            print(f"*** REGEX HIT Hop {hop_idx:02} → regex:{regex_count} ***", flush=True)
        else:
            print(f"*** REGEX MISS Hop {hop_idx:02} ***", flush=True)

        # PHASE 2: Process LLM batches only for unresolved segments
        llm_resolved_count = 0
        
        if llm_pending_segments:
            # Build batches from LLM-pending segments only
            batches: List[List[HopContext]] = [
                llm_pending_segments[i : i + batch_size] for i in range(0, len(llm_pending_segments), batch_size)
            ]
            
            # NEW: Enhanced stochasticity for LLM batches
            if shuffle_segments:
                for batch in batches:
                    random.shuffle(batch)
            
            if shuffle_batches and len(batches) > 1:
                random.shuffle(batches)

            logging.info(
                f"Hop {hop_idx}: {regex_count} resolved by regex, processing {len(batches)} LLM batches (size={batch_size}) with concurrency={concurrency}"
            )

            def _process_llm_batch(batch_segments: List[HopContext]):
                """Process a batch for LLM only (regex already done)."""
                nonlocal llm_resolved_count
                
                batch_id = f"batch_{hop_idx}_{uuid.uuid4().hex[:6]}"
                
                # Assign batch metadata to each segment
                for i, seg in enumerate(batch_segments):
                    seg.batch_id = batch_id  # type: ignore[attr-defined]
                    seg.batch_size = len(batch_segments)  # type: ignore[attr-defined] 
                    seg.batch_pos = i  # type: ignore[attr-defined]
                    seg._resolved_by_llm_this_hop = False  # type: ignore[attr-defined]

                # Track LLM calls for token accumulator
                token_accumulator['llm_calls'] += 1

                # Create batch context (all segments need LLM)
                batch_ctx = BatchHopContext(batch_id=batch_id, hop_idx=hop_idx, segments=batch_segments)
                
                # Call LLM for the batch
                provider_inst = _provider_factory()
                batch_responses = _call_llm_batch(batch_ctx, provider_inst, model, temperature, template=template, ranked=ranked, max_candidates=max_candidates, confidence_scores=confidence_scores, layout=layout)

                # Token accounting
                usage = provider_inst.get_last_usage()
                if usage and token_lock:
                    with token_lock:
                        token_accumulator['prompt_tokens'] += usage.get('prompt_tokens', 0)
                        token_accumulator['response_tokens'] += usage.get('response_tokens', 0)
                        token_accumulator['thought_tokens'] += usage.get('thought_tokens', 0)
                        token_accumulator['total_tokens'] += usage.get('total_tokens', 0)
                
                # Process responses
                sid_to_ctx = {c.statement_id: c for c in batch_segments}
                
                for resp_obj in batch_responses:
                    sid = str(resp_obj.get("segment_id", "")).strip()
                    ctx = sid_to_ctx.get(sid)
                    if ctx is None:
                        continue
                    
                    answer = str(resp_obj.get("answer", "uncertain")).lower().strip()
                    rationale = str(resp_obj.get("rationale", "No rationale provided"))
                    
                    trace_entry = {
                        "Q": hop_idx,
                        "answer": answer,
                        "rationale": rationale,
                        "method": "llm_batch",
                        "batch_id": batch_id,
                        "batch_size": ctx.batch_size,
                        "batch_pos": ctx.batch_pos,
                        "statement_text": ctx.segment_text,
                        "article_id": ctx.article_id,
                    }
                    write_trace_log(trace_dir, ctx.statement_id, trace_entry)
                    
                    ctx.analysis_history.append(f"Q{hop_idx}: {answer}")
                    ctx.reasoning_trace.append(trace_entry)
                    
                    # Check for early termination
                    if answer == "uncertain":
                        ctx.uncertain_count += 1
                        if ctx.uncertain_count >= 3:
                            ctx.final_frame = "LABEL_UNCERTAIN"
                            ctx.final_justification = "Three consecutive uncertain responses"
                            continue
                    
                    # ──────────────────────────────────────────────────────────
                    # HOP‑11 SPECIAL‑CASE — token‑guard then safe fallback
                    # ──────────────────────────────────────────────────────────
                    if answer == "yes" and hop_idx == 11:
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
                        with token_lock:
                            llm_resolved_count += 1

                    # All other hops use the static map
                    elif answer == "yes" and hop_idx in Q_TO_FRAME:
                        ctx.final_frame = Q_TO_FRAME[hop_idx]
                        ctx.final_justification = f"Frame determined by Q{hop_idx} trigger. Rationale: {rationale}"
                        ctx.is_concluded = True
                        ctx._resolved_by_llm_this_hop = True
                        with token_lock:
                            llm_resolved_count += 1

                return batch_segments

            # Process LLM batches
        if concurrency == 1:
            for batch in batches:
                _process_llm_batch(batch)
        else:
            with ThreadPoolExecutor(max_workers=concurrency) as pool:
                futs = [pool.submit(_process_llm_batch, batch) for batch in batches]
                for fut in as_completed(futs):
                    try:
                        fut.result()
                    except Exception as exc:
                        logging.error(f"LLM batch processing error in hop {hop_idx}: {exc}")

        # Count remaining active contexts after this hop
        remaining_contexts = [c for c in active_contexts if not c.is_concluded]
        
        # Print FINISH banner
        print(f"*** FINISH Hop {hop_idx:02} → start:{len(active_contexts)} regex:{regex_count} llm:{llm_resolved_count} remain:{len(remaining_contexts)} ***", flush=True)

    # Final neutral assignment for any still-active contexts
    for ctx in contexts:
        if not ctx.is_concluded:
            ctx.final_frame = "Neutral"
            ctx.final_justification = "Default to Neutral: No specific framing cue triggered in Q1-Q12."
            ctx.is_concluded = True

    # NEW: write consolidated failure summary to main output folder
    if failed_batches:
        _fail_path = trace_dir.parent / "batch_failures.jsonl"
        try:
            import json as _json
            with _fail_path.open("w", encoding="utf-8") as _fh:
                for _rec in failed_batches:
                    _json.dump(_rec, _fh, ensure_ascii=False)
                    _fh.write("\n")
            logging.info("Batch failure summary written → %s", _fail_path)
        except Exception as _e:
            logging.warning("Could not write batch failure summary (%s): %s", _fail_path, _e)

    # NEW: write summary of batches that required >3 retries
    if long_retry_batches:
        _retry_path = trace_dir.parent / "batch_retries_over3.jsonl"
        try:
            import json as _json
            with _retry_path.open("w", encoding="utf-8") as _fh:
                for _rec in long_retry_batches:
                    _json.dump(_rec, _fh, ensure_ascii=False)
                    _fh.write("\n")
            logging.info("Long-retry batch summary written → %s", _retry_path)
        except Exception as _e:
            logging.warning("Could not write long-retry summary (%s): %s", _retry_path, _e)

    return contexts

# --- Main Entry Point for `main.py` ---

def run_coding_step_tot(
    config: Dict,
    input_csv_path: Path,
    output_dir: Path,
    limit: Optional[int] = None,
    start: Optional[int] = None,
    end: Optional[int] = None,
    concurrency: int = 1,
    model: str = "DEFAULT_MODEL",
    provider: str = "gemini",
    batch_size: int = 1,
    regex_mode: str = "live",
    *,
    router: bool = False,
    template: str = "legacy",
    layout: str = "standard",  # NEW: Layout parameter
    shuffle_batches: bool = False,
    shuffle_segments: bool = False,  # NEW: Fine-grained segment shuffling
    skip_eval: bool = False,
    only_hop: Optional[int] = None,
    gold_standard_file: Optional[str] = None,
    print_summary: bool = True,
    shutdown_event: threading.Event = None,  # NEW: Shutdown event
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
    # Load gold standard from separate file if provided
    # ------------------------------------------------------------------
    if gold_standard_file and not skip_eval:
        try:
            gold_standard_path = Path(gold_standard_file)
            if not gold_standard_path.exists():
                logging.error(f"Gold standard file not found: {gold_standard_file}")
                raise FileNotFoundError(f"Gold standard file not found: {gold_standard_file}")
            
            logging.info(f"Loading gold standard from: {gold_standard_file}")
            df_gold = pd.read_csv(gold_standard_path, dtype={'StatementID': str})
            
            # Verify gold standard file has required columns
            if 'StatementID' not in df_gold.columns:
                raise ValueError("Gold standard file must contain 'StatementID' column")
            if 'Gold Standard' not in df_gold.columns:
                raise ValueError("Gold standard file must contain 'Gold Standard' column")
            
            # Check if the input file already has Gold Standard column
            if 'Gold Standard' in df.columns:
                logging.info("Input file already contains 'Gold Standard' column, skipping merge")
                # Log statistics about existing gold standard
                total_input = len(df)
                has_gold = df['Gold Standard'].notna().sum()
                missing_gold = total_input - has_gold
                logging.info(f"Gold standard stats: {has_gold}/{total_input} statements have gold labels, {missing_gold} missing")
            else:
                # Merge gold standard with input data based on StatementID
                df = df.merge(df_gold[['StatementID', 'Gold Standard']], on='StatementID', how='left')
                
                # Log merge statistics
                total_input = len(df)
                has_gold = df['Gold Standard'].notna().sum()
                missing_gold = total_input - has_gold
                logging.info(f"Gold standard merge: {has_gold}/{total_input} statements have gold labels, {missing_gold} missing")
                
                if missing_gold > 0:
                    missing_ids = df[df['Gold Standard'].isna()]['StatementID'].tolist()
                    logging.warning(f"Statements missing gold standard labels: {missing_ids[:10]}{'...' if len(missing_ids) > 10 else ''}")
                
        except Exception as e:
            logging.error(f"Error loading gold standard file: {e}")
            raise
    
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
    # --- Helper to extract hop and method for final decision ---
    def _get_decision_info(ctx):
        """Return (hop_idx, method) where the final 'yes' was triggered.
        Method is 'regex' or 'llm'. If no definitive 'yes' exists, returns (None, None)."""
        for entry in ctx.reasoning_trace:
            if entry.get("answer") == "yes":
                return entry.get("Q"), entry.get("via")
        return None, None
    # --- Token accounting ---
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
    token_lock = threading.Lock()

    trace_dir = output_dir / "traces_tot"
    trace_dir.mkdir(parents=True, exist_ok=True)
    logging.info(f"ToT trace files will be saved in: {trace_dir}")

    # ------------------------------------------------------------------
    # 🛠️  Attach file-handler so the full terminal log is captured next to
    #      the other artefacts (requested by user).
    # ------------------------------------------------------------------
    log_file_path = output_dir / "run.log"
    try:
        _fh = logging.FileHandler(log_file_path, encoding="utf-8")
        _fh.setLevel(logging.INFO)
        _fh.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logging.getLogger().addHandler(_fh)
        logging.info("File logging enabled → %s", log_file_path)
    except Exception as e:
        logging.warning("Could not attach file handler %s: %s", log_file_path, e)

    # Path for false-negative corpus (regex miss + LLM yes)
    miss_path = output_dir / "regex_miss_llm_yes.jsonl"
    global _MISS_PATH
    _MISS_PATH = miss_path  # make accessible to inner functions
    # ensure empty file
    open(miss_path, 'w', encoding='utf-8').close()

    # Path for regex *hits* that short-circuited the hop deterministically
    hit_path = output_dir / "regex_hits.jsonl"
    open(hit_path, 'w', encoding='utf-8').close()

    # Register hit logger with regex_engine so every deterministic match is captured
    try:
        import multi_coder_analysis.regex_engine as _re  # package context
    except ImportError:
        import regex_engine as _re  # standalone script

    def _log_regex_hit(payload: dict) -> None:  # noqa: D401
        # payload contains statement_id, hop, segment, rule, frame, mode, span
        try:
            with token_lock:
                with open(hit_path, 'a', encoding='utf-8') as _f:
                    _f.write(json.dumps(payload, ensure_ascii=False) + "\n")
                # Record segment-level utilisation
                token_accumulator['segments_regex_ids'].add(payload.get('statement_id'))
        except Exception as _e:
            logging.debug("Could not write regex hit log: %s", _e)

    _re.set_hit_logger(_log_regex_hit)

    # helper function to log miss safely
    def _log_regex_miss(statement_id: str, hop: int, segment: str, rationale: str, token_lock: threading.Lock, miss_path: Path):
        payload = {
            "statement_id": statement_id,
            "hop": hop,
            "segment": segment,
            "rationale": rationale,
        }
        with token_lock:
            with open(miss_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(payload, ensure_ascii=False) + "\n")

    # ------------------------------------------------------------------
    # Default counters – these will be overwritten when a gold standard
    # file is available. Initialising them prevents UnboundLocalError when
    # the evaluation branch is skipped (e.g., production runs without gold
    # labels). 2025-06-18.
    # ------------------------------------------------------------------
    initial_mismatch_count: int = 0
    fixed_by_fallback: int = 0
    final_mismatch_count: int = 0
    regex_mismatch_count: int = 0
    llm_mismatch_count: int = 0

    # --- Processing Path Selection ---
    if batch_size > 1:
        logging.info(f"Processing with batch size = {batch_size} and concurrency={concurrency}")
        hop_range = [only_hop] if only_hop else None
        final_contexts = run_tot_chain_batch(
            df,
            provider_name,
            trace_dir,
            model,
            batch_size=batch_size,
            concurrency=concurrency,
            token_accumulator=token_accumulator,
            token_lock=token_lock,
            template=template,
            shuffle_batches=shuffle_batches,
            shuffle_segments=shuffle_segments,  # NEW: Fine-grained segment shuffling
            hop_range=hop_range,
            layout=layout,  # NEW: Layout parameter
        )
        for ctx in final_contexts:
            hop_idx, method = _get_decision_info(ctx)
            final_json = {
                "StatementID": ctx.statement_id,
                "Pipeline_Result": ctx.dim1_frame,
                "Decision_Hop": hop_idx,
                "Decision_Method": method,
                "Pipeline_Justification": ctx.final_justification,
                "Full_Reasoning_Trace": json.dumps(ctx.reasoning_trace)
            }
            results.append(final_json)
    else:
        # Existing single-segment path
        if concurrency == 1:
            # Disable tqdm progress bar for cleaner console output
            for _, row in tqdm(
                df.iterrows(),
                total=df.shape[0],
                desc="Processing Statements (ToT)",
                disable=True,
            ):
                # Check for shutdown
                if shutdown_event and shutdown_event.is_set():
                    logging.info("Shutdown requested, stopping processing...")
                    break
                
                final_context = run_tot_chain(row, llm_provider, trace_dir, model, token_accumulator, token_lock, TEMPERATURE, template=template, layout=layout)
                hop_idx, method = _get_decision_info(final_context)
                final_json = {
                    "StatementID": final_context.statement_id,
                    "Pipeline_Result": final_context.dim1_frame,
                    "Decision_Hop": hop_idx,
                    "Decision_Method": method,
                    "Pipeline_Justification": final_context.final_justification,
                    "Full_Reasoning_Trace": json.dumps(final_context.reasoning_trace)
                }
                results.append(final_json)
        else:
            # Concurrent processing path as previously implemented
            logging.info(f"Using concurrent processing with {concurrency} workers")
            def process_single_statement(row_tuple):
                _, row = row_tuple
                if provider_name == "openrouter":
                    thread_provider = OpenRouterProvider()
                else:
                    thread_provider = GeminiProvider()
                final_context = run_tot_chain(row, thread_provider, trace_dir, model, token_accumulator, token_lock, TEMPERATURE, template=template, layout=layout)
                hop_idx, method = _get_decision_info(final_context)
                final_json = {
                    "StatementID": final_context.statement_id,
                    "Pipeline_Result": final_context.dim1_frame,
                    "Decision_Hop": hop_idx,
                    "Decision_Method": method,
                    "Pipeline_Justification": final_context.final_justification,
                    "Full_Reasoning_Trace": json.dumps(final_context.reasoning_trace)
                }
                return final_json
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                future_to_row = {executor.submit(process_single_statement, row_tuple): row_tuple[1]['StatementID'] for row_tuple in df.iterrows()}
                # Disable tqdm progress bar for cleaner console output
                for future in tqdm(
                    as_completed(future_to_row),
                    total=len(future_to_row),
                    desc="Processing Statements (ToT)",
                    disable=True,
                ):
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
    # This filename should match the pattern expected by the merge step
    # Using a simple filename for now - this should be made configurable
    majority_labels_path = output_dir / f"model_labels_tot.csv"
    df_results.to_csv(majority_labels_path, index=False)
    
    # In this deterministic (VOTES=1) setup, there is no separate raw votes file.
    # The trace files serve as the detailed record.
    raw_votes_path = None

    logging.info(f"ToT processing complete. Labels saved to: {majority_labels_path}")
    
    # --- Evaluation Logic (if gold standard available) ---
    if has_gold_standard:
        # Create comparison CSV first to ensure proper alignment
        comparison_path = create_comparison_csv(df, results, output_dir)
        df_comparison = pd.read_csv(comparison_path)
        
        # Reorganize trace files by match/mismatch status
        reorganize_traces_by_match_status(trace_dir, df_comparison)
        
        # Record initial mismatch count before any fallback corrections
        initial_mismatch_count = int(df_comparison["Mismatch"].sum())

        # Base predictions/actuals — ensure they exist even when no fallback is run
        predictions = df_comparison['Pipeline_Result'].tolist()
        actuals = df_comparison['Gold_Standard'].tolist()

        # --- Mismatch attribution (regex vs. LLM) -----------------------
        seg_regex_ids = token_accumulator.get('segments_regex_ids', set())
        mismatch_ids = set(df_comparison[df_comparison["Mismatch"]].StatementID)
        regex_mismatch_count = len(seg_regex_ids & mismatch_ids)
        llm_mismatch_count = initial_mismatch_count - regex_mismatch_count

        # --- NEW: evaluate and print metrics BEFORE individual fallback ----
        predictions_pre = df_comparison['Pipeline_Result'].tolist()
        actuals_pre = df_comparison['Gold_Standard'].tolist()
        metrics_pre = calculate_metrics(predictions_pre, actuals_pre)

        print("\n🧮  Evaluation BEFORE individual fallback")
        print(f"Regex-driven mismatches : {regex_mismatch_count}")
        print(f"LLM-driven mismatches   : {llm_mismatch_count}")

        print_evaluation_report(metrics_pre, input_csv_path, output_dir, concurrency, limit, start, end)

        # --- Optional: individual fallback rerun for mismatches (batch-sensitive check) ---
        if config.get("individual_fallback", False):
            logging.info("🔄 Running individual fallback for batched mismatches …")

            # Prepare directories
            indiv_root = trace_dir / "traces_tot_individual"
            match_dir = indiv_root / "traces_tot_individual_match"
            mismatch_dir = indiv_root / "traces_tot_individual_mismatch"
            match_dir.mkdir(parents=True, exist_ok=True)
            mismatch_dir.mkdir(parents=True, exist_ok=True)

            indiv_match_entries = []
            indiv_mismatch_entries = []

            # We will update df_comparison in-place if a batch-sensitive fix occurs
            def _run_single(row_tuple):
                idx, row = row_tuple
                statement_id = row['StatementID']
                segment_text = row['Statement Text']
                gold_label = row['Gold_Standard']

                # Build minimal Series for run_tot_chain
                single_series = pd.Series({
                    'StatementID': statement_id,
                    'Statement Text': segment_text,
                    'ArticleID': row.get('ArticleID', ''),
                })

                provider_obj = OpenRouterProvider() if provider_name == "openrouter" else GeminiProvider()

                single_ctx = run_tot_chain(
                    single_series,
                    provider_obj,
                    indiv_root,
                    model,
                    token_accumulator,
                    token_lock,
                    TEMPERATURE,
                    template=template,
                    layout=layout,
                )

                single_label = single_ctx.dim1_frame

                trace_file_path = indiv_root / f"{statement_id}.jsonl"
                try:
                    with open(trace_file_path, 'r', encoding='utf-8') as tf:
                        trace_entries = [json.loads(l.strip()) for l in tf if l.strip()]
                except FileNotFoundError:
                    trace_entries = []

                entry_payload = {
                    "statement_id": statement_id,
                    "expected": gold_label,
                    "batched_result": row['Pipeline_Result'],
                    "single_result": single_label,
                    "statement_text": segment_text,
                    "trace_count": len(trace_entries),
                    "full_trace": trace_entries,
                }

                return idx, single_label, entry_payload

            mismatch_rows = list(df_comparison[df_comparison['Mismatch'] == True].iterrows())

            if mismatch_rows:
                with ThreadPoolExecutor(max_workers=concurrency) as pool:
                    futures = [pool.submit(_run_single, rt) for rt in mismatch_rows]
                    for fut in as_completed(futures):
                        idx, single_label, entry_payload = fut.result()

                        if single_label == entry_payload['expected']:
                            indiv_match_entries.append(entry_payload)
                            df_comparison.at[idx, 'Pipeline_Result'] = single_label
                            df_comparison.at[idx, 'Mismatch'] = False
                        else:
                            indiv_mismatch_entries.append(entry_payload)

            # Write consolidated files
            if indiv_match_entries:
                with open(match_dir / "consolidated_individual_match_traces.jsonl", 'w', encoding='utf-8') as f:
                    for e in indiv_match_entries:
                        f.write(json.dumps(e, ensure_ascii=False) + "\n")

            if indiv_mismatch_entries:
                with open(mismatch_dir / "consolidated_individual_mismatch_traces.jsonl", 'w', encoding='utf-8') as f:
                    for e in indiv_mismatch_entries:
                        f.write(json.dumps(e, ensure_ascii=False) + "\n")

            fixed_by_fallback = len(indiv_match_entries)
            final_mismatch_count = len(indiv_mismatch_entries)
            logging.info(f"🗂️  Individual fallback complete. Fixed: {fixed_by_fallback}, Still mismatched: {final_mismatch_count}")

            # ------------------------------------------------------------------
            # Print concise summaries for fixed and remaining mismatches
            # ------------------------------------------------------------------
            if indiv_match_entries:
                print("\n✅ Fixed mismatches (batch → single):")
                for e in indiv_match_entries:
                    print(
                        f"  • {e['statement_id']}: batched={e['batched_result']} » single={e['single_result']} (expected={e['expected']})"
                    )

                # Tally by hop where the corrected 'yes' fired
                hop_tally: dict[int, int] = {}
                for e in indiv_match_entries:
                    for tr in e.get('full_trace', []):
                        if tr.get('answer') == 'yes':
                            hop = int(tr.get('Q', 0))
                            hop_tally[hop] = hop_tally.get(hop, 0) + 1
                            break
                if hop_tally:
                    print("\n🔢  Hop tally for fixed mismatches (first YES hop):")
                    for h, cnt in sorted(hop_tally.items()):
                        print(f"    Q{h:02}: {cnt}")

            if indiv_mismatch_entries:
                print("\n❌ Still mismatched after fallback:")
                for e in indiv_mismatch_entries:
                    print(
                        f"  • {e['statement_id']}: expected={e['expected']} but got={e['single_result']}"
                    )

            # Final metrics (after any fallback) and reporting
            if has_gold_standard:
                # Recompute mismatch attribution post-fallback
                mismatch_ids_post = set(df_comparison[df_comparison["Mismatch"]].StatementID)
                regex_mismatch_post = len(seg_regex_ids & mismatch_ids_post)
                llm_mismatch_post = len(mismatch_ids_post) - regex_mismatch_post

                predictions = df_comparison['Pipeline_Result'].tolist()
                actuals = df_comparison['Gold_Standard'].tolist()
                metrics = calculate_metrics(predictions, actuals)

                print("\n🧮  Evaluation AFTER individual fallback")
                print(f"Regex-driven mismatches : {regex_mismatch_post}")
                print(f"LLM-driven mismatches   : {llm_mismatch_post}")

                print_evaluation_report(metrics, input_csv_path, output_dir, concurrency, limit, start, end)
                print(f"✍️  All evaluation data written to {comparison_path}")
                print_mismatches(df_comparison)
                print(f"\n✅ Evaluation complete. Full telemetry in {output_dir}")
        
        # If fallback was not run, set mismatch stats accordingly
        if not config.get("individual_fallback", False):
            fixed_by_fallback = 0
            final_mismatch_count = initial_mismatch_count
        
        # Calculate metrics
        metrics = calculate_metrics(predictions, actuals)
        
        # Print evaluation report
        print_evaluation_report(metrics, input_csv_path, output_dir, concurrency, limit, start, end)
        
        print(f"✍️  All evaluation data written to {comparison_path}")
        
        # Print mismatches
        print_mismatches(df_comparison)
        
        print(f"\n✅ Evaluation complete. Full telemetry in {output_dir}")
    
    # --- Token usage summary ---
    # Downgrade duplicate token usage logs to DEBUG to avoid redundant console output
    logging.debug("=== TOKEN USAGE SUMMARY ===")
    logging.debug(f"Prompt tokens   : {token_accumulator['prompt_tokens']}")
    logging.debug(f"Response tokens : {token_accumulator['response_tokens']}")
    logging.debug(f"Thought tokens  : {token_accumulator['thought_tokens']}")
    logging.debug(f"Total tokens    : {token_accumulator['total_tokens']}")
    if print_summary:
        print("\n📏 Token usage:")
        print(f"Prompt  : {token_accumulator['prompt_tokens']}")
        print(f"Response: {token_accumulator['response_tokens']}")
        print(f"Thought : {token_accumulator['thought_tokens']}")
        print(f"Total   : {token_accumulator['total_tokens']}")

    # --- Regex vs LLM usage summary ---
    # Recompute shadow-hit tally based on per-rule statistics so that all shadow
    # matches are counted even when no live rules exist (post-v2.20 change).
    stats_snapshot = _re_eng.get_rule_stats()
    rules_index_snapshot = {r.name: r for r in _re_eng.RAW_RULES}

    # In SHADOW pipeline mode we want to know **all** regex hits because
    # short-circuiting was disabled globally.  Counting only the rules whose
    # YAML mode is already "shadow" hides hits from the main "live" rules and
    # produces near-zero coverage numbers.  Instead:
    #   • if the run was invoked with --regex-mode shadow → count every rule hit
    #   • else (live/off)        → keep the original behaviour (shadow-rules only)

    if regex_mode == "shadow":
        shadow_total = sum(counter.get("hit", 0) for counter in stats_snapshot.values())
    else:
        shadow_total = sum(
            counter.get("hit", 0)
            for name, counter in stats_snapshot.items()
            if rules_index_snapshot.get(name) and rules_index_snapshot[name].mode == "shadow"
        )

    # Store aggregate hits. In SHADOW mode we switch from per-rule hit counts
    # to *unique segments* that triggered at least one regex rule so the
    # metric is not inflated when a segment matches multiple rules/hops.
    if regex_mode == "shadow":
        token_accumulator['regex_hit_shadow'] = len(token_accumulator.get('segments_regex_ids', set()))
    else:
        token_accumulator['regex_hit_shadow'] = shadow_total

    regex_yes = token_accumulator.get('regex_yes', 0)
    regex_hit_shadow = token_accumulator.get('regex_hit_shadow', 0)
    llm_calls = token_accumulator.get('llm_calls', 0)
    total_hops = token_accumulator.get('total_hops', 0)

    # Downgrade duplicate regex/LLM utilisation logs to DEBUG
    logging.debug("=== REGEX / LLM UTILISATION ===")
    logging.debug(f"Total hops          : {total_hops}")
    logging.debug(f"Regex definitive YES : {regex_yes}")
    logging.debug(f"Regex hits (shadow) : {regex_hit_shadow}")
    logging.debug(f"LLM calls made       : {llm_calls}")
    logging.debug(f"Regex coverage       : {regex_yes / total_hops:.2%}" if total_hops else "Regex coverage: n/a")

    if print_summary:
        print("\n⚡ Hybrid stats:")
        print(f"Total hops          : {total_hops}")
        print(f"Regex definitive YES: {regex_yes}")
        print(f"Regex hits (shadow) : {regex_hit_shadow}")
        print(f"LLM calls made      : {llm_calls}")
        if total_hops:
            print(f"Regex coverage      : {regex_yes / total_hops:.2%}")

        # Segment-level utilisation
        total_segments = len(df)
        segments_regex = len(token_accumulator.get('segments_regex_ids', set()))
        segments_llm = total_segments - segments_regex

        print(f"Segments total      : {total_segments}")
        print(f"Segments regex      : {segments_regex}  ({segments_regex / total_segments:.2%})")
        print(f"Segments LLM        : {segments_llm}  ({segments_llm / total_segments:.2%})")

    summary_path = output_dir / "token_usage_summary.json"
    try:
        # Convert non-serialisable objects (like sets) to serialisable forms
        _safe_token_acc = {k: (list(v) if isinstance(v, set) else v) for k, v in token_accumulator.items()}
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(_safe_token_acc, f, indent=2)
        logging.info(f"Token summary written to {summary_path}")
    except Exception as e:
        logging.error(f"Failed to write token summary: {e}")

    # --- Regex per-rule stats CSV ---
    import csv

    stats = _re_eng.get_rule_stats()
    rules_index = {r.name: r for r in _re_eng.RAW_RULES}

    stats_path = output_dir / "regex_rule_stats.csv"
    try:
        with open(stats_path, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(["rule", "hop", "mode", "hit", "total", "coverage"])
            for name, counter in sorted(stats.items()):
                rule = rules_index.get(name)
                hop = rule.hop if rule else "?"
                mode = rule.mode if rule else "?"
                hit = counter.get("hit", 0)
                total = counter.get("total", 0)
                cov = f"{hit/total:.2%}" if total else "0%"
                w.writerow([name, hop, mode, hit, total, cov])
        logging.info(f"Regex rule stats written to {stats_path}")
    except Exception as e:
        logging.error(f"Failed to write regex rule stats: {e}")

    # --- NEW: export full regex rule definitions (useful for debugging) ---
    import json as _json

    rules_snapshot_path = output_dir / "regex_rules_snapshot.jsonl"

    try:
        with open(rules_snapshot_path, "w", encoding="utf-8") as fp:
            for r in _re_eng.RAW_RULES:
                # yes_regex may be a compiled pattern or raw string depending on origin
                pattern_str = (
                    r.yes_regex.pattern if hasattr(r.yes_regex, "pattern") else str(r.yes_regex)
                )
                _json.dump(
                    {
                        "name": r.name,
                        "hop": r.hop,
                        "mode": r.mode,
                        "frame": r.yes_frame,
                        "pattern": pattern_str,
                    },
                    fp,
                    ensure_ascii=False,
                )
                fp.write("\n")
        logging.info(f"Regex rules snapshot written to {rules_snapshot_path}")
    except Exception as e:
        logging.error(f"Failed to export regex rules snapshot: {e}")

    # --- Run parameters summary ---
    params_summary = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "input_file": str(input_csv_path),
        "total_statements": len(df),
        "provider": provider_name,
        "model": model,
        "temperature": TEMPERATURE,
        "top_p": 0.1,
        "top_k": 1 if provider_name != "openrouter" else None,
        "batch_size": batch_size,
        "concurrency": concurrency,
        "individual_fallback_enabled": bool(config.get("individual_fallback", False)),
        "individual_fallback_note": "--individual-fallback flag WAS used" if config.get("individual_fallback", False) else "--individual-fallback flag NOT used",
        "token_usage": _safe_token_acc,
        "regex_yes": regex_yes,
        "regex_hit_shadow": regex_hit_shadow,
        "llm_calls": llm_calls,
        "regex_coverage": (regex_yes / total_hops) if total_hops else None,
        "initial_mismatch_count": initial_mismatch_count,
        "fixed_by_individual_fallback": fixed_by_fallback,
        "final_mismatch_count": final_mismatch_count,
        "regex_mismatch_count": regex_mismatch_count,
        "llm_mismatch_count": llm_mismatch_count,
    }
    if has_gold_standard:
        params_summary.update({
            "accuracy": metrics.get("accuracy"),
            "mismatch_count": int(df_comparison["Mismatch"].sum()),
        })

    params_file = output_dir / "run_parameters_summary.json"
    try:
        with open(params_file, "w", encoding="utf-8") as f:
            json.dump(params_summary, f, indent=2)
        logging.info(f"Run parameter summary written to {params_file}")
    except Exception as e:
        logging.error(f"Failed to write run parameters summary: {e}")

    # ------------------------------------------------------------------
    # 📊  RUN-LEVEL SUMMARY DOCUMENT
    # ------------------------------------------------------------------
    try:
        summary_lines: list[str] = []
        summary_lines.append("=== RUN SUMMARY ===")
        summary_lines.append(f"Total statements          : {len(df)}")
        summary_lines.append(f"Total hops processed      : {token_accumulator.get('total_hops', 0)}")
        summary_lines.append(f"Regex deterministic hits  : {token_accumulator.get('regex_yes', 0)}")
        summary_lines.append(f"Regex hits in shadow mode : {token_accumulator.get('regex_hit_shadow', 0)}")
        summary_lines.append(f"LLM batch calls           : {token_accumulator.get('llm_calls', 0)}")
        summary_lines.append("-- Token usage --")
        summary_lines.append(f"  Prompt tokens   : {token_accumulator.get('prompt_tokens', 0)}")
        summary_lines.append(f"  Response tokens : {token_accumulator.get('response_tokens', 0)}")
        summary_lines.append(f"  Thought tokens  : {token_accumulator.get('thought_tokens', 0)}")
        summary_lines.append(f"  Total tokens    : {token_accumulator.get('total_tokens', 0)}")

        # Aggregate batch-level numbers by reading *_summary.txt inside batch_traces
        batch_tr_dir = trace_dir / "batch_traces"
        dup_total = 0
        residual_total = 0
        missing_total = 0
        if batch_tr_dir.exists():
            for txt_path in batch_tr_dir.glob("*_summary.txt"):
                try:
                    with open(txt_path, 'r', encoding='utf-8') as fh:
                        for line in fh:
                            if line.startswith("Duplicate conflicts"):
                                dup_total += int(line.split(":", 1)[1].strip())
                            elif line.startswith("Residual (extra)"):
                                residual_total += int(line.split(":", 1)[1].strip())
                            elif line.startswith("Missing in reply"):
                                missing_total += int(line.split(":", 1)[1].strip())
                except Exception:
                    continue

        summary_lines.append("-- Batch anomalies --")
        summary_lines.append(f"  Duplicate conflicts : {dup_total}")
        summary_lines.append(f"  Residual extras     : {residual_total}")
        summary_lines.append(f"  Missing in replies  : {missing_total}")

        run_summary_path = output_dir / "run_summary.txt"
        with open(run_summary_path, 'w', encoding='utf-8') as sf:
            sf.write("\n".join(summary_lines))
        logging.info(f"Run-level summary written to: {run_summary_path}")
    except Exception as e:
        logging.warning("Could not write run-level summary: %s", e)

    # ------------------------------------------------------------------
    # 🧹  Detach file handler to avoid duplicate logs if function is called
    #      again within the same Python process.
    # ------------------------------------------------------------------
    try:
        if '_fh' in locals():
            logging.getLogger().removeHandler(_fh)
            _fh.close()
    except Exception:
        pass

    return raw_votes_path, majority_labels_path

# --- Evaluation Functions ---

def calculate_metrics(predictions: List[str], actuals: List[str]) -> Dict[str, Any]:
    """Calculate precision, recall, F1 for each frame and overall accuracy."""
    # Filter out "Unknown" predictions from evaluation (v2.16 upgrade)
    filtered_pairs = [(p, a) for p, a in zip(predictions, actuals) if p.lower() != "unknown"]
    
    if not filtered_pairs:
        # All predictions were "Unknown" - return empty metrics
        return {
            'accuracy': 0.0,
            'frame_metrics': {},
            'total_samples': len(predictions),
            'correct_samples': 0,
            'excluded_unknown': len(predictions)
        }
    
    filtered_predictions, filtered_actuals = zip(*filtered_pairs)
    
    # Get unique labels (excluding Unknown)
    all_labels = sorted(set(filtered_predictions + filtered_actuals))
    
    # Calculate per-frame metrics
    frame_metrics = {}
    for label in all_labels:
        tp = sum(1 for p, a in zip(filtered_predictions, filtered_actuals) if p == label and a == label)
        fp = sum(1 for p, a in zip(filtered_predictions, filtered_actuals) if p == label and a != label)
        fn = sum(1 for p, a in zip(filtered_predictions, filtered_actuals) if p != label and a == label)
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        
        frame_metrics[label] = {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'tp': tp,
            'fp': fp,
            'fn': fn
        }
    
    # Overall accuracy (excluding Unknown predictions)
    correct = sum(1 for p, a in zip(filtered_predictions, filtered_actuals) if p == a)
    accuracy = correct / len(filtered_predictions) if len(filtered_predictions) > 0 else 0.0
    
    return {
        'accuracy': accuracy,
        'frame_metrics': frame_metrics,
        'total_samples': len(predictions),
        'correct_samples': correct,
        'excluded_unknown': len(predictions) - len(filtered_pairs)
    }

def print_evaluation_report(metrics: Dict[str, Any], input_file: Path, output_dir: Path, 
                          concurrency: int, limit: Optional[int] = None, start: Optional[int] = None, end: Optional[int] = None):
    """Print formatted evaluation report to terminal."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print(f"\n📊 Reports → {output_dir}")
    print(f"📂 Loading data from CSV: {input_file}")
    
    # Show processing range info
    if start is not None or end is not None:
        range_desc = f"rows {start if start else 1}-{end if end else 'end'}"
        print(f"✅ Loaded {metrics['total_samples']} examples ({range_desc}).")
    elif limit:
        print(f"✅ Loaded {metrics['total_samples']} examples (segments 1-{limit}).")
    else:
        print(f"✅ Loaded {metrics['total_samples']} examples.")
    
    print(f"🔄 Running evaluation with {concurrency} concurrent threads...")
    
    # Show Unknown exclusion info (v2.16 upgrade)
    excluded_count = metrics.get('excluded_unknown', 0)
    if excluded_count > 0:
        evaluated_count = metrics['total_samples'] - excluded_count
        print(f"🔍 Excluded {excluded_count} 'Unknown' labels from evaluation")
        print(f"📊 Evaluating {evaluated_count}/{metrics['total_samples']} samples")
    
    print(f"\n🎯 OVERALL ACCURACY: {metrics['accuracy']:.2%}")
    print(f"\n=== Per-Frame Precision / Recall ===")
    
    for frame, stats in metrics['frame_metrics'].items():
        if stats['tp'] + stats['fp'] + stats['fn'] == 0:
            continue  # Skip frames not present in the data
            
        p_str = f"{stats['precision']:.2%}" if stats['precision'] > 0 else "nan%"
        r_str = f"{stats['recall']:.2%}" if stats['recall'] > 0 else "0.00%"
        f1_str = f"{stats['f1']:.2%}" if stats['f1'] > 0 else "nan%"
        
        print(f"{frame:<12} P={p_str:<8} R={r_str:<8} F1={f1_str:<8} "
              f"(tp={stats['tp']}, fp={stats['fp']}, fn={stats['fn']})")

def create_comparison_csv(df_original: pd.DataFrame, results: List[Dict], 
                         output_dir: Path) -> Path:
    """Create CSV comparing gold standard to pipeline results."""
    # Convert results to DataFrame for easier merging
    df_results = pd.DataFrame(results)
    
    # Merge with original data, preserving decision metadata
    merge_cols = ['StatementID', 'Pipeline_Result']
    if 'Decision_Hop' in df_results.columns and 'Decision_Method' in df_results.columns:
        merge_cols += ['Decision_Hop', 'Decision_Method']
    
    df_comparison = df_original.merge(
        df_results[merge_cols],
        on='StatementID',
        how='inner'
    )
    
    # Rename columns for clarity
    df_comparison = df_comparison.rename(columns={
        'Gold Standard': 'Gold_Standard'
    })
    
    # Add mismatch column
    df_comparison['Mismatch'] = df_comparison['Gold_Standard'] != df_comparison['Pipeline_Result']
    
    # Save comparison CSV
    comparison_path = output_dir / "comparison_with_gold_standard.csv"
    df_comparison.to_csv(comparison_path, index=False)
    
    return comparison_path

def print_mismatches(df_comparison: pd.DataFrame):
    """Print detailed mismatch information."""
    mismatches = df_comparison[df_comparison['Mismatch'] == True]
    
    if len(mismatches) == 0:
        print(f"🎉 Perfect match! All {len(df_comparison)} statements consistent with gold standard.")
        return
    
    print(f"\n❌ INCONSISTENT STATEMENTS ({len(mismatches)}/{len(df_comparison)}):")
    print("=" * 80)
    
    for _, row in mismatches.iterrows():
        print(f"StatementID: {row['StatementID']}")
        print(f"Text: {row['Statement Text']}")
        print(f"Gold Standard: {row['Gold_Standard']}")
        print(f"Pipeline Result: {row['Pipeline_Result']}")
        print(f"Inconsistency: Expected '{row['Gold_Standard']}' but got '{row['Pipeline_Result']}'")
        print("-" * 80)

def reorganize_traces_by_match_status(trace_dir: Path, df_comparison: pd.DataFrame):
    """
    Reorganize trace files into match/mismatch subdirectories based on evaluation results.
    Also creates consolidated files for easy analysis.
    
    Args:
        trace_dir: Directory containing the original trace files
        df_comparison: DataFrame with comparison results including 'Mismatch' column
    """
    # Create subdirectories
    match_dir = trace_dir / "traces_tot_match"
    mismatch_dir = trace_dir / "traces_tot_mismatch"
    match_dir.mkdir(exist_ok=True)
    mismatch_dir.mkdir(exist_ok=True)
    
    moved_files = {"match": 0, "mismatch": 0}
    mismatch_traces = []  # For consolidation
    match_traces = []     # For consolidation
    
    for _, row in df_comparison.iterrows():
        statement_id = row['StatementID']
        is_mismatch = row['Mismatch']
        
        # Find the original trace file
        original_file = trace_dir / f"{statement_id}.jsonl"
        
        if original_file.exists():
            # Read trace entries for consolidation
            trace_entries = []
            try:
                with open(original_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            trace_entries.append(json.loads(line))
            except Exception as e:
                logging.warning(f"Error reading trace file {original_file}: {e}")
                trace_entries = []
            
            if is_mismatch:
                # Move to mismatch directory
                dest_file = mismatch_dir / f"{statement_id}.jsonl"
                shutil.move(str(original_file), str(dest_file))
                moved_files["mismatch"] += 1
                
                # Add to mismatch consolidation
                mismatch_traces.append({
                    "statement_id": statement_id,
                    "expected": row['Gold_Standard'],
                    "predicted": row['Pipeline_Result'],
                    "statement_text": row.get('Statement Text', ''),
                    "trace_count": len(trace_entries),
                    "full_trace": trace_entries
                })
            else:
                # Move to match directory
                dest_file = match_dir / f"{statement_id}.jsonl"
                shutil.move(str(original_file), str(dest_file))
                moved_files["match"] += 1
                
                # Add to match consolidation
                match_traces.append({
                    "statement_id": statement_id,
                    "expected": row['Gold_Standard'],
                    "predicted": row['Pipeline_Result'],
                    "statement_text": row.get('Statement Text', ''),
                    "trace_count": len(trace_entries),
                    "full_trace": trace_entries
                })
    
    # Create consolidated files
    if mismatch_traces:
        mismatch_consolidated_path = mismatch_dir / "consolidated_mismatch_traces.jsonl"
        with open(mismatch_consolidated_path, 'w', encoding='utf-8') as f:
            for entry in mismatch_traces:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        logging.info(f"📋 Created consolidated mismatch file: {mismatch_consolidated_path} ({len(mismatch_traces)} entries)")
    
    if match_traces:
        match_consolidated_path = match_dir / "consolidated_match_traces.jsonl"
        with open(match_consolidated_path, 'w', encoding='utf-8') as f:
            for entry in match_traces:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        logging.info(f"📋 Created consolidated match file: {match_consolidated_path} ({len(match_traces)} entries)")
    
    logging.info(f"📁 Reorganized traces: {moved_files['match']} matches → {match_dir}")
    logging.info(f"📁 Reorganized traces: {moved_files['mismatch']} mismatches → {mismatch_dir}")
    
    return moved_files

START_TIME = time.perf_counter()

# Helper to log hop progress
def _log_hop(
    hop_idx: int,
    start_active: int,
    regex_yes: int,
    llm_yes: int = 0,
    end_active: int | None = None,
):
    """Progress logger used by both legacy and pipeline code.
 
    start_active – distinct unresolved StatementIDs entering the hop
    regex_yes – number concluded by regex layer for this hop
    llm_yes   – number concluded by LLM responses for this hop
    end_active – optional: unresolved StatementIDs after this hop (if provided)
    """
    elapsed = time.perf_counter() - START_TIME
    if end_active is None:
        end_active = max(0, start_active - regex_yes - llm_yes)

    msg_plain = (
        f"Hop {hop_idx:02} → "
        f"start:{start_active:<3} "
        f"regex:{regex_yes:<2} "
        f"llm:{llm_yes:<2} "
        f"remain:{end_active:<3} "
        f"({elapsed:5.1f}s)"
    )

    # keep existing INFO log for file handlers
    logging.info(msg_plain)

    # Also emit human-readable banner with asterisks once to stdout
    try:
        print(f"*** {msg_plain} ***", flush=True)
    except Exception:
        pass

# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------
# Capture text following "Ranking:" until the next blank line or end of text
_RANK_RE = re.compile(r"ranking\s*[:\-]?\s*(.*?)(?:\n\s*\n|$)", re.I | re.S)

# Bullet / numbering token at *token* start, e.g. "1)", "1.", "-", "•"
_BULLET_RE = re.compile(r"^\s*(?:\d+[\)\.\-]?|[\u2022\*\-])\s*")

_DELIMS_RE = re.compile(r"[>\u2192\u279C\u27A1]|->|=>|,|\n|\r")


def _clean_token(tok: str) -> str:
    """Normalise *tok* by stripping bullet/numbering prefixes and punctuation."""
    tok = _BULLET_RE.sub("", tok)  # remove leading numbering/bullets
    return tok.strip(" .:-→")


def _extract_frame_and_ranking(text: str) -> tuple[str | None, list[str] | None]:
    """Return ``(top_frame, ranking_list)`` parsed from *text*.

    Supported reply formats::

        Ranking: Alarmist > Neutral > Reassuring
        ranking – Alarmist → Neutral → Reassuring
        Ranking:
        1. Alarmist
        2. Neutral
        3. Reassuring

    The function tolerates various arrow symbols (">", "→", "->", "⇒") and
    newline-separated or comma-separated lists.  Numbering/bullet prefixes are
    stripped automatically.
    """
    if not text:
        return None, None

    # 1. Standard "Ranking:" prefix --------------------------------------
    m = _RANK_RE.search(text)
    captured: str | None = None
    if m:
        captured = m.group(1)

    # 2. Fallback – whole answer *looks* like a list ----------------------
    if captured is None:
        first_line = text.strip().splitlines()[0]
        if any(d in first_line for d in (">", "->", "→", ",")):
            captured = first_line

    # 3. Legacy single-answer "Answer:" ----------------------------------
    if captured is None:
        m_ans = re.search(r"answer\s*[:\-]\s*([\w\s]+)", text, re.I)
        if m_ans:
            top = m_ans.group(1).strip()
            return top, None
        return None, None

    # ------------------------------------------------------------------
    raw_seq = _DELIMS_RE.split(captured)
    seq = [_clean_token(s) for s in raw_seq if _clean_token(s)]

    if not seq:
        return None, None
    return seq[0], seq

# ---------------------------------------------------------------------------
# Backwards-compat shim – keep the old symbol name but point to the canonical
# implementation to avoid import errors while eliminating duplicate logic.
# ---------------------------------------------------------------------------
# Only emit deprecation warning when the deprecated function is actually used, not on import
def _extract_frame_and_ranking_dupe(text: str) -> tuple[str | None, list[str] | None]:
    """Deprecated: use _extract_frame_and_ranking instead."""
    warnings.warn(
        "_extract_frame_and_ranking_dupe is deprecated; use _extract_frame_and_ranking instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return _extract_frame_and_ranking(text)

def _extract_confidence_and_ranking(text: str) -> tuple[str | None, list[str] | None, dict | None]:
    """Return (top_frame, ranking_list, confidence_data) parsed from confidence-enhanced response.
    
    Confidence-enhanced responses include:
    - answer: yes/no/uncertain
    - confidence: 0-100  
    - frame_likelihoods: {Alarmist: X, Neutral: Y, Reassuring: Z}
    - Optional ranking line: "Ranking: Frame1 > Frame2 > Frame3"
    """
    if not text:
        return None, None, None
    
    confidence_data = {}
    
    # Try to parse JSON for confidence data
    try:
        # Find JSON object using brace counting for proper nesting
        start_idx = text.find('{')
        if start_idx == -1:
            raise ValueError("No JSON object found")
        
        brace_count = 0
        end_idx = start_idx
        
        for i, char in enumerate(text[start_idx:], start_idx):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i
                    break
        
        if brace_count != 0:
            raise ValueError("Unmatched braces in JSON")
        
        json_text = text[start_idx:end_idx + 1]
        parsed_json = json.loads(json_text)
        
        # Extract confidence and frame likelihoods
        if 'confidence' in parsed_json:
            confidence_data['confidence'] = float(parsed_json['confidence'])
        
        if 'frame_likelihoods' in parsed_json:
            confidence_data['frame_likelihoods'] = parsed_json['frame_likelihoods']
            
            # Generate ranking from frame likelihoods
            frame_likes = parsed_json['frame_likelihoods']
            sorted_frames = sorted(frame_likes.items(), key=lambda x: x[1], reverse=True)
            ranking = [frame for frame, _ in sorted_frames]
            top_frame = ranking[0] if ranking else None
            
            return top_frame, ranking, confidence_data
        else:
            # Check if we have an answer field to use as top_frame
            if 'answer' in parsed_json:
                answer = parsed_json['answer'].lower().strip()
                if answer == 'yes':
                    # Determine frame from context - we'll need to handle this more sophisticatedly
                    # For now, fallback to standard parsing
                    pass
    
    except (json.JSONDecodeError, KeyError, ValueError):
        pass
    
    # Fallback to standard parsing
    top_frame, ranking = _extract_frame_and_ranking(text)
    return top_frame, ranking, confidence_data if confidence_data else None


def _extract_frame_and_ranking_enhanced(text: str, confidence_mode: bool = False) -> tuple[str | None, list[str] | None, dict | None]:
    """Enhanced frame extraction that handles both standard and confidence-enhanced responses."""
    if confidence_mode:
        return _extract_confidence_and_ranking(text)
    else:
        top_frame, ranking = _extract_frame_and_ranking(text)
        return top_frame, ranking, None