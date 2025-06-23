#!/usr/bin/env python3
"""CI helper – verify hop_patterns.yml is syntactically valid and all regexes compile."""
from __future__ import annotations
import sys
import regex as re
from pathlib import Path

try:
    from ruamel.yaml import YAML  # type: ignore
except ImportError:
    sys.exit("ruamel.yaml not installed")

DEFAULT_YAML = "multi_coder_analysis/regex/hop_patterns.yml"

def main(path: str = DEFAULT_YAML):
    yaml = YAML()
    with Path(path).open("r", encoding="utf-8") as f:
        doc = yaml.load(f)
    errors = 0
    for hop, rules in doc.items():
        if not isinstance(hop, int):
            continue
        for entry in rules:
            if not isinstance(entry, dict):
                continue
            name = entry.get("name", "<unnamed>")
            pattern = entry.get("pattern")
            if not pattern:
                print(f"Hop {hop}/{name}: missing pattern", file=sys.stderr)
                errors += 1
                continue
            try:
                re.compile(pattern, flags=re.I)
            except re.error as e:
                print(f"Hop {hop}/{name}: invalid regex – {e}", file=sys.stderr)
                errors += 1
    if errors:
        print(f"❌ {errors} error(s) found in {path}", file=sys.stderr)
        sys.exit(1)
    print(f"✅ {path} is valid – all regexes compile.")

if __name__ == "__main__":
    main() 