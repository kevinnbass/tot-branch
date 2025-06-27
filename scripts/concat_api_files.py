#!/usr/bin/env python3
"""Concatenate the **minimal LLM provider layer** into one standalone text file.

Usage:
    python scripts/concat_api_files.py [OUTPUT_FILE]

If *OUTPUT_FILE* is omitted the script writes to
`concatenated_codebase/llm_provider_bundle_<timestamp>.txt`.

The bundle contains (in order):
    • multi_coder_analysis/providers/base.py
    • multi_coder_analysis/providers/__init__.py
    • multi_coder_analysis/providers/gemini.py
    • multi_coder_analysis/providers/openrouter.py
    • multi_coder_analysis/pricing.py  (cost helper – optional but nice)

Each file is separated by a clear markdown fence so you can copy/paste the
whole block into an AI coding assistant or plaintext doc.
"""
from __future__ import annotations

import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List

# ---------------------------------------------------------------------------
# Configuration – edit the list below if you add/remove provider modules
# ---------------------------------------------------------------------------

FILE_LIST: List[Path] = [
    Path("multi_coder_analysis/providers/base.py"),
    Path("multi_coder_analysis/providers/__init__.py"),
    Path("multi_coder_analysis/providers/gemini.py"),
    Path("multi_coder_analysis/providers/openrouter.py"),
    Path("multi_coder_analysis/pricing.py"),
]

# Output destination directory (created on-demand if not passed explicitly)
DEFAULT_OUT_DIR = Path("concatenated_codebase")

# ---------------------------------------------------------------------------
# Implementation
# ---------------------------------------------------------------------------

def _validate_inputs() -> None:
    """Ensure every path in *FILE_LIST* exists before we start writing."""
    missing = [str(p) for p in FILE_LIST if not p.exists()]
    if missing:
        print("❌  The following files are missing:")
        for m in missing:
            print(f"   – {m}")
        sys.exit(1)


def _generate_output_path(arg: str | None) -> Path:
    if arg:
        return Path(arg).expanduser().resolve()
    # auto-name with timestamp
    DEFAULT_OUT_DIR.mkdir(exist_ok=True, parents=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return DEFAULT_OUT_DIR / f"llm_provider_bundle_{ts}.txt"


def main() -> None:
    _validate_inputs()

    # Parse optional argv[1]
    out_path = _generate_output_path(sys.argv[1] if len(sys.argv) > 1 else None)

    try:
        rel_path = out_path.relative_to(Path.cwd())
    except ValueError:
        # Fallback to absolute path when paths are on different drives or otherwise unrelated
        rel_path = out_path

    print(f"📦  Creating provider bundle → {rel_path}")

    try:
        with out_path.open("w", encoding="utf-8") as outf:
            outf.write(
                f"# LLM Provider Bundle – generated {datetime.now().isoformat(timespec='seconds')}\n"
            )
            outf.write("# Copy & paste into your AI coding assistant.\n\n")

            for idx, fp in enumerate(FILE_LIST, start=1):
                rel = fp.as_posix()
                print(f"   [{idx}/{len(FILE_LIST)}] adding {rel}")

                outf.write("""```python\n""")
                outf.write(f"# BEGIN {rel}\n")
                outf.write("# " + "-" * (72 - len(rel)) + "\n")

                with fp.open("r", encoding="utf-8") as inf:
                    outf.write(inf.read().rstrip())

                outf.write("\n# END " + rel + "\n")
                outf.write("""```\n\n""")

        size = out_path.stat().st_size
        print(f"✅  Done – {size:,} bytes written.")
    except Exception as exc:
        print(f"❌  Failed to write bundle: {exc}")
        if out_path.exists():
            try:
                out_path.unlink()
            except Exception:
                pass
        sys.exit(1)


if __name__ == "__main__":
    main() 