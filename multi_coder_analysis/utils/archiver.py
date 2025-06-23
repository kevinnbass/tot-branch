from __future__ import annotations

import json, gzip
from pathlib import Path
from typing import Iterable

from multi_coder_analysis.models import HopContext

# ------------------------------------------------------------------
# Public helper – *process-local* (no cross-process locks required)
# ------------------------------------------------------------------
def archive_resolved(
    ctxs: Iterable[HopContext],
    *,
    run_id: str,
    tag: str,
    archive_dir: Path,
) -> None:
    """
    Append concluded segments to a worker-local JSONL (.gz optional) file.

    File name:  <run_id>_<tag>.jsonl[.gz]
    """
    if not archive_dir:
        return

    archive_dir.mkdir(parents=True, exist_ok=True)
    file_path = archive_dir / f"{run_id}_{tag}.jsonl"

    # Transparent compression when suffix = .gz
    opener = gzip.open if file_path.suffix == ".gz" else open   # type: ignore[assignment]

    with opener(file_path, "at", encoding="utf-8") as fh:       # type: ignore[arg-type]
        for ctx in ctxs:
            if not ctx.is_concluded:
                continue

            fh.write(
                json.dumps(
                    {
                        "statement_id": ctx.statement_id,
                        "permutation": ctx.permutation_idx,
                        "hop": ctx.q_idx,
                        "frame": ctx.final_frame,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            ) 