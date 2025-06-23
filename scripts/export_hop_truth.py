#!/usr/bin/env python3
"""Export a CSV mapping StatementID → First_Firing_Hop using current regex rules.

This *static* approximation runs the regex catalogue (hop_patterns.yml)
against each segment and records the **lowest hop number** whose *live* or
*shadow* rule fires on that text.  It does **not** invoke the LLM, but it
is fast and sufficient for hop-specific regex mining.

Usage example
-------------
$ python scripts/export_hop_truth.py \
      --input multi_coder_analysis/data/gold_standard_modified.csv \
      --output tmp/hop_truth.csv
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Dict, List

import pandas as pd
import regex as re

try:
    from ruamel.yaml import YAML  # type: ignore
except ImportError:
    YAML = None

try:
    from multi_coder_analysis.preprocess import normalise_unicode
except Exception:

    def normalise_unicode(text: str):  # type: ignore
        return text

DEFAULT_PATTERNS = "multi_coder_analysis/regex/hop_patterns.yml"

###############################################################################
# Load regex catalogue
###############################################################################

def load_patterns(yaml_path: Path) -> Dict[int, List[re.Pattern]]:
    if YAML is None:
        sys.exit("ruamel.yaml required – pip install ruamel.yaml")
    yaml = YAML()
    with yaml_path.open("r", encoding="utf-8") as f:
        doc = yaml.load(f)
    hop_map: Dict[int, List[re.Pattern]] = {}
    for hop, rules in doc.items():
        if not isinstance(hop, int):
            continue
        compiled: List[re.Pattern] = []
        for entry in rules:
            if not isinstance(entry, dict):
                continue
            pat = entry.get("pattern")
            if not pat:
                continue
            try:
                compiled.append(re.compile(pat, flags=re.I))
            except re.error as e:
                print(f"⚠ Invalid regex in hop {hop} / {entry.get('name')}: {e}", file=sys.stderr)
        if compiled:
            hop_map[hop] = compiled
    return hop_map

###############################################################################
# Main
###############################################################################

def main():
    ap = argparse.ArgumentParser(description="Export StatementID → First_Firing_Hop via regex catalogue")
    ap.add_argument("--input", required=True, help="CSV with StatementID, Statement Text")
    ap.add_argument("--output", required=True, help="Output CSV path")
    ap.add_argument("--patterns", default=DEFAULT_PATTERNS, help="hop_patterns.yml path")
    args = ap.parse_args()

    hop_patterns = load_patterns(Path(args.patterns))
    if not hop_patterns:
        sys.exit("No patterns loaded – aborting")

    df = pd.read_csv(args.input, usecols=["StatementID", "Statement Text"], dtype=str)
    df["clean"] = df["Statement Text"].map(normalise_unicode).str.lower()

    results = []
    for _, row in df.iterrows():
        sid = row["StatementID"]
        text = row["clean"]
        first_hop = 0
        for hop in sorted(hop_patterns.keys()):
            if any(rx.search(text) for rx in hop_patterns[hop]):
                first_hop = hop
                break
        results.append((sid, first_hop))

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["StatementID", "First_Firing_Hop"])
        writer.writerows(results)
    print(f"✅ Wrote hop truth for {len(results)} rows → {out_path}")


if __name__ == "__main__":
    main() 