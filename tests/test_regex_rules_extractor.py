"""Verifies YAML + fenced regex extraction logic."""

import importlib
import textwrap
from pathlib import Path

import pytest


# ––– helpers –––––––––––––––––––––––––––––––––––––––––––––––
PROMPT_STUB = textwrap.dedent(
    """
    ---                       # YAML front-matter
    name: TestRule
    hop: 3
    mode: live
    frame: Alarmist
    ---
    Some explanatory prose …

    ```regex
    \\bjust\\s+a\\s+stub\\b
    ```
    """
)


@pytest.fixture()
def tmp_prompts_dir(tmp_path: Path) -> Path:
    p = tmp_path / "prompts"
    p.mkdir()
    (p / "hop_Q03.txt").write_text(PROMPT_STUB, encoding="utf-8")
    return p


def test_extractor_loads_yml_meta(tmp_prompts_dir, monkeypatch):
    """Ensure metadata and pattern body are correctly parsed."""
    import multi_coder_analysis.regex_rules as rr

    # Patch module-level PROMPTS_DIR before reload
    monkeypatch.setattr(rr, "PROMPTS_DIR", tmp_prompts_dir, raising=False)

    # Reload the module so that extraction runs against our tmp prompts
    rr = importlib.reload(rr)  # noqa: PLW2901  (shadowing acceptable in test)

    extracted = [r for r in rr.RAW_RULES if r.name == "TestRule"]
    assert extracted, "Rule not extracted"

    rule = extracted[0]
    assert rule.hop == 3
    assert rule.mode == "live"
    assert rule.yes_frame == "Alarmist"
    assert rule.yes_regex.pattern == r"\bjust\s+a\s+stub\b" 