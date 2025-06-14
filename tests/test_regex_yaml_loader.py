"""Verifies that regex rules are loaded correctly from hop_patterns.yml."""

import importlib
import textwrap
from pathlib import Path


yaml_stub = textwrap.dedent(
    """
    3:
      - name: TestRule
        mode: live
        frame: Alarmist
        pattern: |-
          \\bjust\\s+a\\s+stub\\b
    """
)


def test_yaml_loader(monkeypatch, tmp_path: Path):
    # Create expected folder hierarchy …/regex/hop_patterns.yml
    regex_dir = tmp_path / "regex"
    regex_dir.mkdir()
    pattern_file = regex_dir / "hop_patterns.yml"
    pattern_file.write_text(yaml_stub, encoding="utf-8")

    import multi_coder_analysis.regex_rules as rr

    # Redirect loader to our temp YAML and reload
    monkeypatch.setattr(rr, "PATTERN_FILE", pattern_file, raising=False)
    rr = importlib.reload(rr)

    rule = next(r for r in rr.RAW_RULES if r.name == "TestRule")
    assert rule.hop == 3
    assert rule.mode == "live"
    assert rule.yes_frame == "Alarmist"
    assert rule.yes_regex.pattern == r"\bjust\s+a\s+stub\b" 