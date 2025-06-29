#!/usr/bin/env python3
"""
Standalone Prompt Loader for Annotation System

This is a self-contained version of the prompt loader specifically for the
annotation system. It can be extracted with the annotation tools without
affecting the main codebase.
"""

from pathlib import Path
from typing import Tuple, Dict, Any
import re
import yaml

# Regex to match leading front-matter
_FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)

# Regex to strip HTML-style comments used for row annotations
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


def load_prompt_and_meta(path: Path) -> Tuple[str, Dict[str, Any]]:
    """Return (prompt_body, meta_dict) for the file at path.
    
    Extracts YAML front-matter from prompt files for annotation validation.
    Never raises on YAML errors - returns empty dict to allow graceful fallback.
    """
    text = path.read_text(encoding="utf-8")

    m = _FM_RE.match(text)
    if not m:  # No front-matter found
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