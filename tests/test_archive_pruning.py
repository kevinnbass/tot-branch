def _simulate(ctx_cls, n_perm=8):
    # Build dummy concluded + unresolved contexts
    concluded = [ctx_cls(statement_id=f"s{i}", segment_text="x", permutation_idx=p, is_concluded=True)
                 for i in range(3) for p in range(n_perm)]
    alive = [ctx_cls(statement_id=f"s{i}", segment_text="x", permutation_idx=p)
             for i in range(3, 6) for p in range(n_perm)]
    return concluded + alive

def test_prune_step(tmp_path):
    from multi_coder_analysis.core.pipeline.consensus_tot import _ArchivePruneStep
    from multi_coder_analysis.models import HopContext

    step = _ArchivePruneStep(run_id="t1", archive_dir=tmp_path, tag="P1")
    survivors = step.run(_simulate(HopContext))

    # Only unresolved should survive
    assert all(not c.is_concluded for c in survivors)

    # Archive file created & contains 24 lines (3 segments × 8 perm.)
    f = tmp_path / "t1_P1.jsonl"
    assert f.exists() and sum(1 for _ in f.open()) == 24