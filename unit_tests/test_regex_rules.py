import pytest

from multi_coder_analysis.regex_engine import match
from hop_context import HopContext


@pytest.mark.parametrize(
    "text,hop,expected_frame",
    [
        ("The flu is extremely deadly and spreading.", 1, "Alarmist"),
        ("Officials say situation is fully under control.", 5, "Reassuring"),
    ],
)
def test_positive_regex_matches(text, hop, expected_frame):
    ctx = HopContext(statement_id="TEST", segment_text=text)
    ctx.q_idx = hop
    ans = match(ctx)
    assert ans is not None, "Expected regex to match"
    assert ans["answer"] == "yes"
    assert ans["frame"] == expected_frame 