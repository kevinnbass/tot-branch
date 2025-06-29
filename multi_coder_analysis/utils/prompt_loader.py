from __future__ import annotations

"""Utility to load hop prompts and their YAML front-matter.

A prompt file **may** begin with a YAML front-matter block delimited by

---\n
<yaml>\n
---\n
If present, the front-matter is parsed with `yaml.safe_load` and removed from
what is returned to the caller.  The helper therefore guarantees that the
string you pass to the LLM never contains header metadata while still making
that metadata available as a Python dict for downstream logic.

The helper is tolerant: if the file has no front-matter or if the YAML cannot
be parsed, it silently falls back to an empty meta-dict and returns the whole
file contents as the prompt body.

Example
-------
>>> from pathlib import Path
>>> body, meta = load_prompt_and_meta(Path("prompts/hop_Q01.txt"))
>>> print(meta["hop"], meta["short_name"])
1 IntensifierRiskAdj
"""

from pathlib import Path
from typing import Tuple, Dict, Any
import re

import yaml

# Import prompt tracker
try:
    from .prompt_tracker import get_prompt_tracker
except ImportError:
    # Fallback if prompt_tracker is not available
    def get_prompt_tracker():
        return None

# Regex to match leading front-matter.  We anchor at the very start of the
# file so that only a header at the top is considered.
_FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)

# Regex to strip HTML-style comments used for row annotations
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


def load_prompt_and_meta(path: Path) -> Tuple[str, Dict[str, Any]]:
    """Return *(prompt_body, meta_dict)* for the file at *path*.

    The function never raises on YAML errors – instead it returns an empty
    dictionary so that the calling code can proceed unaffected.
    """
    # Track that this prompt was used
    tracker = get_prompt_tracker()
    if tracker:
        tracker.track_prompt(path)
    
    text = path.read_text(encoding="utf-8")

    m = _FM_RE.match(text)
    if not m:  # No front-matter found – send the entire file to the model.
        body = text
        meta = {}
    else:
        meta_yaml = m.group(1)
        try:
            meta: Dict[str, Any] = yaml.safe_load(meta_yaml) or {}
        except Exception:
            meta = {}

        body = text[m.end() :]  # strip the header including closing delimiter

    # Strip HTML comments used for row-level annotations
    body = _HTML_COMMENT_RE.sub("", body)
    
    return body, meta 