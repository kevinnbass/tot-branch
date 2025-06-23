from __future__ import annotations

import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd


THRESHOLD = 7  # default ratio threshold


def load_majority_file(root_dir: Path) -> pd.DataFrame:
    path = root_dir / "majority_vote_comparison.csv"
    if not path.exists():
        raise FileNotFoundError(f"majority_vote_comparison.csv not found in {root_dir}")
    return pd.read_csv(path)


def find_trace_file(perm_dir: Path, statement_id: str) -> Optional[Path]:
    """Return first trace file path for statement in *perm_dir* (recursive glob)."""
    trace_root = perm_dir / "traces_tot"
    if not trace_root.exists():
        return None
    # Direct path
    direct = trace_root / f"{statement_id}.jsonl"
    if direct.exists():
        return direct
    # Look under reorganized directories (traces_tot_match / mismatch / individual etc.)
    for pattern in ["traces_tot_match", "traces_tot_mismatch", "traces_tot_individual_*", "**"]:
        for p in trace_root.glob(f"{pattern}/{statement_id}.jsonl"):
            if p.exists():
                return p
    return None


def read_trace_entries(trace_path: Path) -> List[Any]:
    try:
        with trace_path.open("r", encoding="utf-8") as fh:
            return [json.loads(l) for l in fh if l.strip()]
    except Exception:
        # Fallback to raw lines if JSON fails
        with trace_path.open("r", encoding="utf-8") as fh:
            return [l.rstrip("\n") for l in fh]


def collect_traces(root_dir: Path, threshold: float = THRESHOLD) -> List[Dict[str, Any]]:
    df = load_majority_file(root_dir)
    low_rows = df[df["Majority_Label_Ratio"] < threshold]
    if low_rows.empty:
        print(f"No StatementIDs found with Majority_Label_Ratio < {threshold} in {root_dir}")
        return []

    low_ids = set(low_rows["StatementID"].astype(str))

    collected: List[Dict[str, Any]] = []

    # Identify permutation subfolders (start with 'P')
    for perm_dir in sorted([p for p in root_dir.iterdir() if p.is_dir() and p.name.startswith("P")]):
        perm_tag = perm_dir.name
        for sid in low_ids:
            trace_file = find_trace_file(perm_dir, sid)
            if trace_file is None:
                continue
            entries = read_trace_entries(trace_file)

            # Extract statement text and article ID from first trace entry (if available)
            stmt_text = ""
            article_id = ""
            for ent in entries:
                if isinstance(ent, dict):
                    stmt_text = ent.get("statement_text", stmt_text)
                    article_id = ent.get("article_id", article_id)
                    if stmt_text and article_id:
                        break

            collected.append({
                "statement_id": sid,
                "article_id": article_id,
                "statement_text": stmt_text,
                "permutation": perm_tag,
                "trace_path": str(trace_file.relative_to(root_dir)),
                "trace_entries": entries,
            })
    return collected


def write_output(root_dir: Path, data: List[Dict[str, Any]]):
    """Write two standalone CSV files:

    1. low_ratio_traces_standalone.csv   – one row per <statement, permutation> pair with
       a JSON-encoded string of the full trace entries.
    2. low_ratio_segments_standalone.csv – de-duplicated list of StatementIDs with
       their ArticleID and raw statement text.
    """

    # ----- 1. Detailed trace records ------------------------------------
    traces_jsonl_path = root_dir / "low_ratio_traces_standalone.jsonl"
    with traces_jsonl_path.open("w", encoding="utf-8") as fh:
        for obj in data:
            fh.write(json.dumps(obj, ensure_ascii=False) + "\n")

    # ----- 2. Unique segment list ---------------------------------------
    unique_rows: Dict[str, Dict[str, str]] = {}
    for obj in data:
        sid = obj["statement_id"]
        if sid not in unique_rows:
            unique_rows[sid] = {
                "ArticleID": obj.get("article_id", ""),
                "StatementID": sid,
                "StatementText": obj.get("statement_text", ""),
            }

    df_segments = pd.DataFrame(list(unique_rows.values()))
    segments_csv_path = root_dir / "low_ratio_segments_standalone.csv"
    df_segments.to_csv(segments_csv_path, index=False)

    # --------------------------------------------------------------------
    print(f"✅ Trace records → {traces_jsonl_path.relative_to(root_dir)}  ({len(data)} lines)")
    print(f"✅ Segment list  → {segments_csv_path.relative_to(root_dir)}  ({len(df_segments)} rows)")


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_low_ratio_traces.py <permutation_root> [threshold]", file=sys.stderr)
        sys.exit(1)

    root_dir = Path(sys.argv[1])
    if not root_dir.exists():
        print(f"Root directory not found: {root_dir}", file=sys.stderr)
        sys.exit(1)

    threshold = float(sys.argv[2]) if len(sys.argv) > 2 else THRESHOLD

    traces = collect_traces(root_dir, threshold)
    if traces:
        write_output(root_dir, traces)
    else:
        print("No trace records collected.")


if __name__ == "__main__":
    main() 