from __future__ import annotations

"""Command-line interface entry point (Phase 7)."""

import typer
from pathlib import Path
from typing import Optional

from multi_coder_analysis.config.run_config import RunConfig
from multi_coder_analysis.runtime.tot_runner import execute
from multi_coder_analysis.providers.base import get_cost_accumulator

app = typer.Typer(help="Multi-Coder Analysis toolkit (ToT refactor)")


@app.command()
def run(
    input_csv: Path = typer.Argument(..., help="CSV file with statements"),
    output_dir: Path = typer.Argument(..., help="Directory for outputs"),
    provider: str = typer.Option("gemini", help="LLM provider: gemini|openrouter"),
    model: str = typer.Option("models/gemini-2.5-flash-preview-04-17", help="Model identifier"),
    batch_size: int = typer.Option(
        1,
        min=1,
        help="(DEPRECATED: pipeline mode is non-batching) Batch size for legacy LLM calls",
    ),
    concurrency: int = typer.Option(1, min=1, help="Thread pool size"),
    regex_mode: str = typer.Option("live", help="Regex mode: live|shadow|off"),
    shuffle_batches: bool = typer.Option(False, help="Randomise batch order"),
    phase: str = typer.Option(
        "pipeline",
        "--phase",
        help="Execution mode: legacy | pipeline",
        rich_help_panel="Execution mode",
    ),
    consensus: str = typer.Option(
        "final",
        help="Consensus mode: 'hop' for per-hop majority, 'final' for end-of-tree",
        rich_help_panel="Consensus",
    ),
    # ---- self-consistency decoding flags ----
    decode_mode: str = typer.Option(
        "normal",
        "--decode-mode",
        "-m",
        help="normal | self-consistency",
    ),
    votes: int = typer.Option(1, "--votes", "-n", help="# paths/votes for self-consistency"),
    sc_rule: str = typer.Option(
        "majority",
        "--sc-rule",
        help="majority | ranked | ranked-raw | irv | borda | mrr",
    ),
    sc_temperature: float = typer.Option(0.7, "--sc-temperature", help="Sampling temperature"),
    sc_top_k: int = typer.Option(40, "--sc-top-k", help="top-k sampling cutoff (0 disables)"),
    sc_top_p: float = typer.Option(0.95, "--sc-top-p", help="nucleus sampling p value"),
    print_cost: bool = typer.Option(
        False,
        "--print-cost",
        help="Print total USD cost when the run finishes",
        rich_help_panel="Cost",
    ),
    # ---- ranked-list flags ----
    ranked_list: bool = typer.Option(
        False,
        "--ranked-list",
        help="Prompt LLM to emit an ordered list of answers. "
              "Valid --sc-rule options in this mode: irv | borda | mrr.",
    ),
    max_candidates: int = typer.Option(
        5,
        "--max-candidates",
        help="How many candidates to retain from each ranked list (1 keeps only the top choice).",
    ),
):
    """Run the deterministic Tree-of-Thought coder."""

    cfg = RunConfig(
        input_csv=input_csv,
        output_dir=output_dir,
        provider=provider,
        model=model,
        batch_size=batch_size,
        concurrency=concurrency,
        regex_mode=regex_mode,
        shuffle_batches=shuffle_batches,
        phase=phase,
        consensus_mode=consensus,
        decode_mode=decode_mode,
        sc_votes=votes,
        sc_rule=sc_rule,
        sc_temperature=sc_temperature,
        sc_top_k=sc_top_k,
        sc_top_p=sc_top_p,
        ranked_list=ranked_list,
        max_candidates=max_candidates,
    )
    out_path = execute(cfg)
    if print_cost:
        typer.echo(f"\n💰  Run cost = ${get_cost_accumulator():.4f}\n")
    return out_path


if __name__ == "__main__":
    app() 