from pathlib import Path

# Default directory points to the project prompts folder.
_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

__all__ = ["build_prompts"]


def build_prompts(question: str, *, ranked: bool) -> tuple[str, str]:
    """Return (system, user) prompt pair.

    Parameters
    ----------
    question : str
        The raw question or hop prompt body (with placeholders already filled).
    ranked : bool
        When True, instructs the model to emit a ranked list of answers.  When
        False, the legacy single-answer format is used.
    """
    # Load global header once for both modes.
    try:
        system_block = (_PROMPTS_DIR / "global_header.txt").read_text(encoding="utf-8")
    except FileNotFoundError:
        # Fallback to new canonical name if legacy not found.
        system_block = (_PROMPTS_DIR / "GLOBAL_HEADER.txt").read_text(encoding="utf-8")

    # Mode-specific few-shot examples and footer.
    flavour = "ranked" if ranked else "single"
    examples_path = _PROMPTS_DIR / f"examples_{flavour}.txt"
    footer_path = _PROMPTS_DIR / f"footer_{flavour}.txt"

    examples = examples_path.read_text(encoding="utf-8") if examples_path.exists() else ""
    footer = footer_path.read_text(encoding="utf-8") if footer_path.exists() else ""

    user_block_parts = []
    if examples:
        user_block_parts.append(examples)
    user_block_parts.append(question)
    if footer:
        user_block_parts.append(footer)

    user_block = "\n\n".join(user_block_parts)

    return system_block, user_block 