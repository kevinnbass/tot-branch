"""Basic smoke test for regex_engine.match."""

from multi_coder_analysis.regex_engine import (
    match,
    COMPILED_RULES,
)
from multi_coder_analysis.regex_rules import PatternInfo
from multi_coder_analysis.hop_context import HopContext
import regex as re


def test_regex_engine_positive_hit(monkeypatch):
    """Inject a synthetic live rule and assert deterministic yes."""
    rule = PatternInfo(
        hop=1,
        name="UnitTestRule",
        yes_frame="Alarmist",
        yes_regex=re.compile(r"unit-test-cue", re.I),
        mode="live",
    )

    # Monkey-patch compiled rule table
    monkeypatch.setitem(COMPILED_RULES, 1, [rule])

    ctx = HopContext(statement_id="UT_001", segment_text="This is a UNIT-TEST-CUE.")
    ctx.q_idx = 1

    res = match(ctx)
    assert res is not None, "Rule should have fired"
    assert res["answer"] == "yes"
    assert res["frame"] == "Alarmist" 