"""
Regression tests for the Hop 11 token‑guard.
Run:  pytest tests/test_hop11_token_guard.py
"""

import multi_coder_analysis.run_multi_coder_tot as tot


def _ctx(answer: str, rationale: str):
    c = tot.HopContext(statement_id="T‑000", segment_text='"Quote."')
    c.current_hop = 11
    tot._apply_llm_response(c, {"answer": answer, "rationale": rationale})
    return c.final_frame


def test_missing_token_defaults_to_neutral():
    assert _ctx("yes", "dominant quote but token absent") == "Neutral"


def test_alarmist_token_yields_alarmist():
    assert _ctx("yes", "very concerning ||FRAME=Alarmist") == "Alarmist"


def test_reassuring_token_yields_reassuring():
    assert _ctx("yes", "public can rest easy ||FRAME=Reassuring") == "Reassuring" 