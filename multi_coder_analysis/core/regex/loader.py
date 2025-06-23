"""Regex rule loader with plugin support (Phase 3)."""

from __future__ import annotations

import re
import yaml
from importlib import resources
from typing import List, Pattern

__all__ = ["load_rules"]


def load_rules() -> List[List[Pattern[str]]]:
    """Load regex rules from YAML files.
    
    Returns:
        List of rule lists, indexed by hop number (1-12)
    """
    # --------------------------------------------------
    # Locate the bundled YAML via importlib.resources – this works regardless
    # of whether the package is executed from an unpacked directory tree *or*
    # an installed, zipped wheel.
    # --------------------------------------------------
    try:
        # Fallback to package *root* then sub-path because 'multi_coder_analysis.regex'
        # is not a Python package (no __init__.py).
        rules_text = resources.files("multi_coder_analysis").joinpath("regex", "hop_patterns.yml").read_text("utf-8")
    except (FileNotFoundError, ModuleNotFoundError):
        # Package wasn't shipped with rules – treat as "no-op" engine.
        return [[] for _ in range(13)]  # 0-12, using 1-12

    try:
        data = yaml.safe_load(rules_text)
        
        # Convert to compiled patterns
        rules = [[] for _ in range(13)]  # 0-12, using 1-12
        
        if data and isinstance(data, dict):
            for hop_key, patterns in data.items():
                try:
                    hop_num = int(str(hop_key).lstrip("Qq"))
                    if 1 <= hop_num <= 12 and isinstance(patterns, list):
                        rules[hop_num] = [
                            re.compile(pattern, re.IGNORECASE)
                            for pattern in patterns
                            if isinstance(pattern, str)
                        ]
                except (ValueError, IndexError):
                    continue
        
        return rules
        
    except Exception:
        # Fallback to empty rules on any error
        return [[] for _ in range(13)] 