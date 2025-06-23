import pytest

from multi_coder_analysis.core.regex import Engine
from multi_coder_analysis.models import HopContext

match = Engine.default().match


@pytest.mark.parametrize(
    "text,hop,expected_frame",
    [
        ("The flu is extremely deadly and spreading.", 1, "Alarmist"),
        ("Officials say situation is fully under control.", 5, "Reassuring"),
        ("USDA confirmed chicken products remain safe to eat.", 5, "Reassuring"),
        ("Poultry is safe for human consumption according to health officials.", 5, "Reassuring"),
        ("The new variant poses no risk to public health.", 7, "Neutral"),
        ("Officials said the outbreak presents no risk to consumers.", 7, "Neutral"),
        # 2025-06-20 • Zero-FP rules promoted to live - positive cases
        ("Health officials say there is no cause for alarm.", 5, "Reassuring"),
        ("Experts stated there is nothing to worry about.", 5, "Reassuring"),
        ("The region is on high alert for potential outbreaks.", 2, "Alarmist"),
        ("The virus does not pose a threat to humans.", 7, "Neutral"),
    ],
)
def test_positive_regex_matches(text, hop, expected_frame):
    ctx = HopContext(statement_id="TEST", segment_text=text)
    ctx.q_idx = hop
    ans = match(ctx)
    assert ans is not None, "Expected regex to match"
    assert ans["answer"] == "yes"
    assert ans["frame"] == expected_frame


@pytest.mark.parametrize(
    "text,hop",
    [
        # 2025-06-20 • Zero-FP rules promoted to live - negative cases
        ("There is no cause for the delay.", 5),  # "no cause for alarm" should not match
        ("Nothing to worry about safety regulations.", 5),  # "nothing to worry about" should not match
        ("The alert is high priority.", 2),  # "on high alert" should not match
        ("This poses no direct threat to the business.", 7),  # "does not pose a threat" should not match
    ],
)
def test_negative_regex_matches(text, hop):
    """Test that patterns do not match when they shouldn't (zero false positives)"""
    ctx = HopContext(statement_id="TEST", segment_text=text)
    ctx.q_idx = hop
    ans = match(ctx)
    # Should either not match or match with different pattern
    if ans is not None:
        # If it matches, it should not be from our new zero-FP patterns
        assert "Live" not in ans.get("pattern_name", ""), f"Zero-FP pattern should not match: {text}" 