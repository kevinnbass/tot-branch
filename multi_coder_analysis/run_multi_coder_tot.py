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
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
from collections import defaultdict
import collections
import re

import pandas as pd
from tqdm import tqdm
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import shutil

# Local project imports
from hop_context import HopContext, BatchHopContext
from llm_providers.gemini_provider import GeminiProvider
from llm_providers.openrouter_provider import OpenRouterProvider
from utils.tracing import write_trace_log
from utils.tracing import write_batch_trace
from utils.prompt_loader import load_prompt_and_meta  # New helper

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
MAX_RETRIES = 3
BACKOFF_FACTOR = 1.5
if "PROMPTS_DIR" not in globals():
    PROMPTS_DIR = Path(__file__).parent / "prompts"

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
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logging.debug("Global header file not found at %s", path)
        return ""


def _load_global_footer() -> str:
    path = PROMPTS_DIR / "GLOBAL_FOOTER.txt"
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logging.debug("Global footer file not found at %s", path)
        return ""

# Map question index to the frame assigned if the answer is "yes"
Q_TO_FRAME = {
    1: "Alarmist", 2: "Alarmist", 3: "Alarmist", 4: "Alarmist",
    5: "Reassuring", 6: "Reassuring",
    7: "Neutral", 8: "Neutral", 9: "Neutral", 10: "Neutral",
    11: "Variable",  # Special case handled in run_tot_chain
    12: "Neutral"
}

# --- LLM Interaction ---

def _assemble_prompt(ctx: HopContext) -> Tuple[str, str]:
    """Dynamically assembles the full prompt for the LLM for a given hop."""
    try:
        hop_file = PROMPTS_DIR / f"hop_Q{ctx.q_idx:02}.txt"

        # --- NEW: strip YAML front-matter and capture metadata ---
        hop_body, meta = load_prompt_and_meta(hop_file)
        ctx.prompt_meta = meta  # save for downstream consumers

        # Simple template replacement
        user_prompt = hop_body.replace(
            "{{segment_text}}", ctx.segment_text
        ).replace("{{statement_id}}", ctx.statement_id)

        # Prefer new canonical filename; fallback to legacy if absent
        header_path = hop_file.parent / "GLOBAL_HEADER.txt"
        if not header_path.exists():
            header_path = hop_file.parent / "global_header.txt"
        try:
            local_header = header_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            local_header = _load_global_header()

        local_footer = ""
        try:
            local_footer = (hop_file.parent / "GLOBAL_FOOTER.txt").read_text(encoding="utf-8")
        except FileNotFoundError:
            local_footer = _load_global_footer()

        system_block = local_header + "\n\n" + hop_body
        user_block = user_prompt + "\n\n" + local_footer
        return system_block, user_block

    except FileNotFoundError:
        logging.error(f"Error: Prompt file not found for Q{ctx.q_idx} at {hop_file}")
        raise
    except Exception as e:
        logging.error(f"Error assembling prompt for Q{ctx.q_idx}: {e}")
        raise

def _call_llm_single_hop(ctx: HopContext, provider, model: str, temperature: float = TEMPERATURE) -> Dict[str, str]:
    """Makes a single, retrying API call to the LLM for one hop."""
    sys_prompt, user_prompt = _assemble_prompt(ctx)
    
    for attempt in range(MAX_RETRIES):
        try:
            # Use provider abstraction
            raw_text = provider.generate(sys_prompt, user_prompt, model, temperature)
            
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

# --- Core Orchestration ---

def run_tot_chain(segment_row: pd.Series, provider, trace_dir: Path, model: str, token_accumulator: dict, token_lock: threading.Lock, temperature: float = TEMPERATURE) -> HopContext:
    """Orchestrates the 12-hop reasoning chain for a single text segment."""
    ctx = HopContext(
        statement_id=segment_row["StatementID"],
        segment_text=segment_row["Statement Text"]
    )
    
    uncertain_streak = 0

    for q_idx in range(1, 13):
        # Log progress for single-segment execution
        _log_hop(q_idx, 1, token_accumulator.get('regex_yes', 0))
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
            llm_response = _call_llm_single_hop(ctx, provider, model, temperature)
            frame_override = None
            provider_called = True
            via = "llm"
            regex_meta = None
            with token_lock:
                token_accumulator['llm_calls'] += 1
        
        ctx.raw_llm_responses.append(llm_response)
        
        choice = llm_response.get("answer", "uncertain").lower().strip()
        rationale = llm_response.get("rationale", "No rationale provided.")
        
        # Update logs and traces
        trace_entry = {
            "Q": q_idx,
            "answer": choice,
            "rationale": rationale,
            "via": via,
            "regex": regex_meta,
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
            ctx.final_frame = frame_override or Q_TO_FRAME[q_idx]
            ctx.is_concluded = True
            # Frame override from regex, else Hop 11 logic
            if frame_override:
                ctx.final_justification = f"Frame determined by Q{q_idx} trigger. Rationale: {rationale}"
            else:
                ctx.final_justification = f"Frame determined by Q{q_idx} trigger. Rationale: {rationale}"
            break # Exit the loop on the first 'yes'

    # If loop completes without any 'yes' answers
    if not ctx.is_concluded:
        ctx.final_frame = "Neutral" # Default outcome
        ctx.final_justification = "Default to Neutral: No specific framing cue triggered in Q1-Q12."
        ctx.is_concluded = True

    return ctx

# --- NEW: Batch Prompt Assembly ---

def _assemble_prompt_batch(segments: List[HopContext], hop_idx: int) -> Tuple[str, str]:
    """Assemble a prompt that contains multiple segments for the same hop."""
    try:
        hop_file = PROMPTS_DIR / f"hop_Q{hop_idx:02}.txt"
        hop_content, meta = load_prompt_and_meta(hop_file)

        # Attach same meta to every HopContext in this batch for consistency
        for ctx in segments:
            ctx.prompt_meta = meta

        # Remove any single-segment placeholders
        hop_content = hop_content.replace("{{segment_text}}", "<SEGMENT_TEXT>")
        hop_content = hop_content.replace("{{statement_id}}", "<STATEMENT_ID>")

        # Enumerate the segments
        segment_block_lines = []
        for idx, ctx in enumerate(segments, start=1):
            segment_block_lines.append(f"### Segment {idx} (ID: {ctx.statement_id})")
            segment_block_lines.append(ctx.segment_text)
            segment_block_lines.append("")
        segment_block = "\n".join(segment_block_lines)

        instruction = (
            f"\nYou will answer the **same question** (Q{hop_idx}) for EACH segment listed below.\n"
            "Respond with **one JSON array**. Each element must contain: `segment_id`, `answer`, `rationale`.\n"
            "Return NOTHING except valid JSON.\n\n"
        )

        # Prefer new canonical filename; fallback to legacy if absent
        header_path = hop_file.parent / "GLOBAL_HEADER.txt"
        if not header_path.exists():
            header_path = hop_file.parent / "global_header.txt"
        try:
            local_header = header_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            local_header = _load_global_header()

        local_footer = ""
        try:
            local_footer = (hop_file.parent / "GLOBAL_FOOTER.txt").read_text(encoding="utf-8")
        except FileNotFoundError:
            local_footer = _load_global_footer()

        system_block = local_header + "\n\n" + hop_content
        user_block = instruction + segment_block + "\n\n" + local_footer
        return system_block, user_block
    except Exception as e:
        logging.error(f"Error assembling batch prompt for Q{hop_idx}: {e}")
        raise

# --- NEW: Batch LLM Call ---

def _call_llm_batch(batch_ctx, provider, model: str, temperature: float = TEMPERATURE):
    """Call the LLM on a batch of segments for a single hop and parse the JSON list response."""
    sys_prompt, user_prompt = _assemble_prompt_batch(batch_ctx.segments, batch_ctx.hop_idx)
    batch_ctx.raw_prompt = sys_prompt

    for attempt in range(MAX_RETRIES):
        try:
            raw_text = provider.generate(sys_prompt, user_prompt, model, temperature)
            if not raw_text.strip():
                raise ValueError("Empty response from LLM")

            content = raw_text.strip()
            if content.startswith('```json') and content.endswith('```'):
                content = content[7:-3].strip()
            elif content.startswith('```') and content.endswith('```'):
                content = content[3:-3].strip()

            parsed = json.loads(content)
            if not isinstance(parsed, list):
                raise ValueError("Batch response is not a JSON array")
            # basic validation: ensure each dict has required keys
            for obj in parsed:
                if not all(k in obj for k in ("segment_id", "answer", "rationale")):
                    raise ValueError("Batch JSON object missing keys")
            batch_ctx.raw_response = content
            batch_ctx.thoughts = provider.get_last_thoughts()
            return parsed
        except Exception as e:
            logging.warning(f"Batch Q{batch_ctx.hop_idx}: attempt {attempt+1} failed: {e}")
            time.sleep(BACKOFF_FACTOR * (2 ** attempt))
    logging.error(f"Batch Q{batch_ctx.hop_idx}: All retries failed – marking all segments uncertain")
    # create fallback uncertain list
    fallback = []
    for ctx in batch_ctx.segments:
        fallback.append({"segment_id": ctx.statement_id, "answer": "uncertain", "rationale": "LLM call failed."})
    return fallback

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
) -> List[HopContext]:
    """Process dataframe through the 12-hop chain using batching with optional concurrency."""
    # Build HopContext objects
    contexts: List[HopContext] = [
        HopContext(statement_id=row["StatementID"], segment_text=row["Statement Text"]) for _, row in df.iterrows()
    ]

    def _provider_factory():
        if provider_name == "openrouter":
            return OpenRouterProvider()
        return GeminiProvider()

    def _process_batch(batch_segments: List[HopContext], hop_idx: int):
        token_accumulator['llm_calls'] += 1
        
        # Step 1: Apply regex rules to all segments in this batch
        regex_resolved: List[HopContext] = []
        unresolved_segments: List[HopContext] = []
        
        for seg_ctx in batch_segments:
            seg_ctx.q_idx = hop_idx  # ensure hop set
            
            token_accumulator['total_hops'] += 1
            
            try:
                r_answer = _re_eng.match(seg_ctx)
            except Exception as exc:
                logging.warning(
                    f"Regex engine error in batch {hop_idx} on {seg_ctx.statement_id}: {exc}"
                )
                r_answer = None
            
            if r_answer:
                if _re_eng._FORCE_SHADOW:
                    token_accumulator['regex_hit_shadow'] += 1
                else:
                    token_accumulator['regex_yes'] += 1
                
                # Log the regex hit
                trace_entry = {
                    "Q": hop_idx,
                    "answer": r_answer["answer"],
                    "rationale": r_answer["rationale"],
                    "method": "regex",
                    "regex": r_answer.get("regex", {}),
                }
                write_trace_log(trace_dir, seg_ctx.statement_id, trace_entry)
                
                seg_ctx.analysis_history.append(f"Q{hop_idx}: yes (regex)")
                seg_ctx.reasoning_trace.append(trace_entry)
                
                # Set final frame if this is a frame-determining hop and answer is yes
                if r_answer["answer"] == "yes" and hop_idx in Q_TO_FRAME:
                    seg_ctx.final_frame = r_answer.get("frame") or Q_TO_FRAME[hop_idx]
                    seg_ctx.is_concluded = True
                
                regex_resolved.append(seg_ctx)
            else:
                unresolved_segments.append(seg_ctx)
        
        # Step 2: If any segments remain unresolved, call LLM for the batch
        if unresolved_segments:
            # Create batch context
            batch_id = f"batch_{hop_idx}_{threading.get_ident()}"
            batch_ctx = BatchHopContext(batch_id=batch_id, hop_idx=hop_idx, segments=unresolved_segments)
            
            # Call LLM for the batch
            provider_inst = _provider_factory()
            batch_responses = _call_llm_batch(batch_ctx, provider_inst, model, temperature)
            
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

            for resp_obj in batch_responses:
                sid = str(resp_obj.get("segment_id", "")).strip()
                ctx = sid_to_ctx.get(sid)
                if ctx is None:
                    continue  # skip unknown ids

                answer = str(resp_obj.get("answer", "uncertain")).lower().strip()
                rationale = str(resp_obj.get("rationale", "No rationale provided"))
                
                trace_entry = {
                    "Q": hop_idx,
                    "answer": answer,
                    "rationale": rationale,
                    "method": "llm_batch",
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
                
                # Check for frame override (Q11 special case)
                if hop_idx == 11 and "||FRAME=" in rationale:
                    frame_match = re.search(r'\|\|FRAME=([^|]+)', rationale)
                    if frame_match:
                        ctx.final_frame = frame_match.group(1).strip()
                        continue
                
                # Set final frame if this is a frame-determining hop and answer is yes
                if answer == "yes" and hop_idx in Q_TO_FRAME:
                    ctx.final_frame = Q_TO_FRAME[hop_idx]
                    ctx.final_justification = (
                        f"Frame determined by Q{hop_idx} trigger. Rationale: {rationale}"
                    )
                    ctx.is_concluded = True

            # Any ctx not covered by response → mark uncertain
            for ctx in unresolved_segments:
                if ctx.statement_id not in sid_to_ctx or all(r.get("segment_id") != ctx.statement_id for r in batch_responses):
                    trace_entry = {
                        "hop_idx": hop_idx,
                        "answer": "uncertain",
                        "rationale": "Missing response from batch",
                        "method": "fallback",
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
        
        # Return all segments (resolved + unresolved)
        return regex_resolved + unresolved_segments

    active_contexts: List[HopContext] = contexts[:]

    for hop_idx in range(1, 13):
        active_contexts = [c for c in active_contexts if not c.is_concluded]
        if not active_contexts:
            break

        # Log hop start from main thread
        _log_hop(hop_idx, len(active_contexts), token_accumulator.get('regex_yes', 0))

        # Build batches of current active segments
        batches: List[List[HopContext]] = [
            active_contexts[i : i + batch_size] for i in range(0, len(active_contexts), batch_size)
        ]

        logging.info(
            f"Hop {hop_idx}: processing {len(batches)} batches (size={batch_size}) with concurrency={concurrency}"
        )

        if concurrency == 1:
            for batch in batches:
                _process_batch(batch, hop_idx)
        else:
            # Concurrency handled within run_tot_chain_batch
            # logging.warning("Concurrency >1 is not yet supported with batching. Defaulting concurrency to 1.")
            with ThreadPoolExecutor(max_workers=concurrency) as pool:
                futs = [pool.submit(_process_batch, batch, hop_idx) for batch in batches]
                for fut in as_completed(futs):
                    try:
                        fut.result()
                    except Exception as exc:
                        logging.error(f"Batch processing error in hop {hop_idx}: {exc}")

    # Final neutral assignment for any still-active contexts
    for ctx in contexts:
        if not ctx.is_concluded:
            ctx.final_frame = "Neutral"
            ctx.final_justification = "Default to Neutral: No specific framing cue triggered in Q1-Q12."
            ctx.is_concluded = True

    return contexts

# --- Main Entry Point for `main.py` ---

def run_coding_step_tot(config: Dict, input_csv_path: Path, output_dir: Path, limit: Optional[int] = None, start: Optional[int] = None, end: Optional[int] = None, concurrency: int = 1, model: str = "models/gemini-2.5-flash-preview-04-17", provider: str = "gemini", batch_size: int = 1, regex_mode: str = "live") -> Tuple[None, Path]:
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
    
    # Check if this is an evaluation run (has Gold Standard column)
    has_gold_standard = 'Gold Standard' in df.columns
    
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

    # --- Processing Path Selection ---
    if batch_size > 1:
        logging.info(f"Processing with batch size = {batch_size} and concurrency={concurrency}")
        final_contexts = run_tot_chain_batch(df, provider_name, trace_dir, model, batch_size=batch_size, concurrency=concurrency, token_accumulator=token_accumulator, token_lock=token_lock)
        for ctx in final_contexts:
            final_json = {
                "StatementID": ctx.statement_id,
                "Pipeline_Result": ctx.dim1_frame,
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
                final_context = run_tot_chain(row, llm_provider, trace_dir, model, token_accumulator, token_lock, TEMPERATURE)
                final_json = {
                    "StatementID": final_context.statement_id,
                    "Pipeline_Result": final_context.dim1_frame,
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
                final_context = run_tot_chain(row, thread_provider, trace_dir, model, token_accumulator, token_lock, TEMPERATURE)
                final_json = {
                    "StatementID": final_context.statement_id,
                    "Pipeline_Result": final_context.dim1_frame,
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

            # Calculate metrics AFTER fallback
            predictions = df_comparison['Pipeline_Result'].tolist()
            actuals = df_comparison['Gold_Standard'].tolist()
            metrics = calculate_metrics(predictions, actuals)

            print("\n🧮  Evaluation AFTER individual fallback")

            print_evaluation_report(metrics, input_csv_path, output_dir, concurrency, limit, start, end)
            
            print(f"✍️  All evaluation data written to {comparison_path}")
            
            # Print mismatches
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
    shadow_total = sum(
        counter.get("hit", 0)
        for name, counter in stats_snapshot.items()
        if rules_index_snapshot.get(name) and rules_index_snapshot[name].mode == "shadow"
    )

    # Store the aggregate for downstream logging/JSON
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
    
    # Merge with original data
    df_comparison = df_original.merge(
        df_results[['StatementID', 'Pipeline_Result']], 
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
def _log_hop(hop_idx: int, active: int, regex_yes: int):
    elapsed = time.perf_counter() - START_TIME
    msg = f"Hop {hop_idx:02} → active:{active:<4} regex_yes:{regex_yes:<3} ({elapsed:5.1f}s)"
    logging.info(msg)
    # Remove duplicate tqdm.write and print to avoid doubled output
    # try:
    #     from tqdm import tqdm  # local import to avoid hard dep elsewhere
    #     tqdm.write(msg)
    # except Exception:
    #     print(msg) 