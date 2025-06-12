"""
Lightweight helper for writing per-segment, per-hop JSON-Lines audit files.
"""
import json
from pathlib import Path
from typing import Dict, Any

def write_trace_log(trace_dir: Path, statement_id: str, trace_entry: Dict[str, Any], subdirectory: str = ""):
    """
    Appends a single JSON line entry to the trace file for a given statement.

    Args:
        trace_dir: The base directory for all trace files (e.g., .../traces/).
        statement_id: The ID of the statement, used for the filename.
        trace_entry: The dictionary to be written as a JSON line.
        subdirectory: Optional subdirectory name (e.g., "match", "mismatch").
    """
    try:
        # Determine final trace directory (with optional subdirectory)
        if subdirectory:
            final_trace_dir = trace_dir / subdirectory
        else:
            final_trace_dir = trace_dir
            
        # Ensure the trace directory exists.
        final_trace_dir.mkdir(parents=True, exist_ok=True)
        
        # Define the full path for the statement's trace file.
        trace_file_path = final_trace_dir / f"{statement_id}.jsonl"

        # Append the JSON line to the file.
        with open(trace_file_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(trace_entry, ensure_ascii=False) + '\n')
            
    except Exception as e:
        # Using print here as this is a non-critical utility and shouldn't crash the main pipeline.
        # A more advanced implementation could use the main logger.
        print(f"Warning: Could not write trace log for {statement_id}. Error: {e}") 

def write_batch_trace(trace_dir: Path, batch_id: str, hop_idx: int, batch_payload: Dict[str, Any]):
    """Write a single JSON file that captures the full prompt/response/CoT for a batch-level LLM call.

    Args:
        trace_dir: Base directory for trace output (same as for per-segment logs).
        batch_id: Unique identifier for this batch (e.g. "batch_02_123456").
        hop_idx: The hop/question number in the ToT chain.
        batch_payload: Dictionary with keys like 'prompt', 'response', 'thoughts', 'segments'.
    """
    try:
        # Keep batch traces separate so they do not clutter per-segment files
        batch_dir = trace_dir / "batch_traces"
        batch_dir.mkdir(parents=True, exist_ok=True)

        file_path = batch_dir / f"{batch_id}_Q{hop_idx:02}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(batch_payload, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Warning: Could not write batch trace for {batch_id}. Error: {e}") 