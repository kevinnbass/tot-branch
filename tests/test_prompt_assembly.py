"""Tests the _assemble_prompt helper for header/footer plumbing."""

import importlib
from pathlib import Path
import textwrap

from multi_coder_analysis.hop_context import HopContext


PROMPT_BODY = textwrap.dedent(
    """
    ### Segment (StatementID: {{statement_id}})
    {{segment_text}}

    Some question…
    """
)

HEADER = "# HEADER"
FOOTER = "# FOOTER"


def test_prompt_assembly(monkeypatch, tmp_path: Path):
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    (prompts_dir / "GLOBAL_HEADER.txt").write_text(HEADER, encoding="utf-8")
    (prompts_dir / "GLOBAL_FOOTER.txt").write_text(FOOTER, encoding="utf-8")
    (prompts_dir / "hop_Q01.txt").write_text(PROMPT_BODY, encoding="utf-8")

    import multi_coder_analysis.run_multi_coder_tot as tot
    monkeypatch.setattr(tot, "PROMPTS_DIR", prompts_dir, raising=False)

    # Force reload so module-level constants re-resolve paths
    tot = importlib.reload(tot)  # noqa: F811

    ctx = HopContext(statement_id="ABC123", segment_text="hello world")
    ctx.q_idx = 1

    sys_prompt, user_prompt = tot._assemble_prompt(ctx)  # pylint: disable=protected-access

    assert HEADER in sys_prompt
    assert FOOTER in user_prompt
    assert "ABC123" in user_prompt
    assert "hello world" in user_prompt 