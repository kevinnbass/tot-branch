from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Tuple, Dict, Any, TypedDict
import re

import yaml

__all__ = ["parse_prompt", "PromptMeta"]


class PromptMeta(TypedDict, total=False):
    hop: int
    short_name: str
    description: str
    # Extend with other known keys as needed.


# Regex to match YAML front-matter at top of file
_FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


@lru_cache(maxsize=128)
def parse_prompt(path: Path) -> Tuple[str, PromptMeta]:
    """Return (prompt_body, front_matter) for *path*.

    The result is cached for the lifetime of the process to avoid unnecessary
    disk I/O during batch processing.
    """
    text = path.read_text(encoding="utf-8")

    m = _FM_RE.match(text)
    if not m:
        return text, {}  # type: ignore[return-value]

    meta_yaml = m.group(1)
    try:
        meta: PromptMeta = yaml.safe_load(meta_yaml) or {}
    except Exception:
        meta = {}  # type: ignore[assignment]

    body = text[m.end() :]
    # Normalise – drop the *single* blank line often left between '---' and
    # the actual prompt content so downstream tokenisers don't pay for it.
    if body.startswith("\n"):
        body = body.lstrip("\n")

    return body, meta 