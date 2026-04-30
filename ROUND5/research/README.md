# Round 5 Research Index

This folder contains historical research artifacts plus the active Round 5 plan.

## Active Source Of Truth

Read these in order:

1. `round5_learning_plan.md`
2. `round5_missing_edge_research_plan.md`
3. `worker_prompt_multi_engine_edge_expansion.md`
4. `round5_iterative_learning_loop.md`

## Current Status

The active task is not candidate tuning and not iterative improvement.

The active task is:

**multi-engine edge expansion before final integration.**

Candidates 23/24/25 prove that integration works. Candidates 26-30 do not exist yet and should not be created until the multi-engine edge expansion is complete.

## Important Current Benchmarks

- `round5_candidate_23.py`: robust integrated branch, about `183.8k` full and `37.2k` portal.
- `round5_candidate_24.py`: highest portal branch, about `41.8k` portal and `131.1k` full.
- `round5_candidate_25.py`: balanced official-validated branch, about `38.9k` portal and `156.8k` full.

## Useful Current Outputs

Use these as evidence:

- `outputs/candidate_21_25_attribution.md`
- `outputs/candidate_21_25_product_pnl.csv`
- `outputs/candidate_21_25_component_matrix.csv`
- `outputs/exhaustive_remaining_edge_summary.md`
- `outputs/exhaustive_remaining_edge_table.csv`
- `outputs/exhaustive_product_classification.csv`
- `outputs/exhaustive_candidate_26_30_inputs.md`

## Historical Outputs

Most markdown files under `outputs/` are historical notes from candidate batches 1-25. They should not override the active root docs. Use them only when investigating a specific old candidate, probe, or failure mode.

Do not delete historical outputs; they preserve evidence and backtest context.
