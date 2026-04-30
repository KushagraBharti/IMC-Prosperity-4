# Round 5 Research Index

This folder contains historical research artifacts plus the active Round 5 plan.

## Active Source Of Truth

Read these in order:

1. `round5_150k_push_plan.md`
2. `round5_150k_executable_probe_plan.md`
3. `worker_prompt_150k_executable_probe_conversion.md`
4. `round5_backtester_usage.md`
5. `outputs/candidate_35_36_ceiling_gap.md`
6. `outputs/candidate_35_36_marginal_engine_table.csv`
7. `outputs/candidate_35_36_score_table.md`
8. `outputs/candidate_35_36_ablation_summary.md`
9. `outputs/candidate_31_34_reset_review.md`
10. `round5_iterative_learning_loop.md`

## Current Status

The active task is not iterative improvement and not final candidate construction.

The active task is:

**candidate 35/36 executable probe conversion to push toward 150k+ portal PnL.**

The ceiling-gap/oracle map exists. It is not enough by itself.

Candidates 35/36 already exist. Do not create candidates 37-40 until the top gaps have been converted into executable probe evidence and the blueprint has been revised from probe results.

## Important Current Benchmarks

- `round5_candidate_35.py`: current robust development base, about `91.9k` portal and `287.4k` full.
- `round5_candidate_36.py`: current portal-upside branch, about `105.5k` portal and `36.7k` full.
- `round5_candidate_34.py`: highest historical portal branch, about `105.9k` portal but `-49.8k` full.
- Current leaderboard top-100 cutoff is about `114k`; target is `150k+`, stretch is `200k+`.
- Final strategies should aim to trade at least `30` products only if the products have validated or gated executable edge. Do not add products for coverage alone.

## Useful Current Outputs

Use these as evidence:

- `outputs/candidate_35_36_score_table.md`
- `outputs/candidate_35_36_ablation_summary.md`
- `outputs/candidate_35_36_design_notes.md`
- `outputs/candidate_35_36_recommendation.md`
- `outputs/candidate_35_36_ceiling_gap.md`
- `outputs/candidate_35_36_oracle_gap_table.csv`
- `outputs/candidate_35_36_marginal_engine_table.csv`
- `outputs/candidate_35_36_regime_oracle_table.csv`
- `outputs/candidate_31_34_reset_review.md`
- `outputs/candidate_31_34_portal_product_pnl.csv`
- `outputs/candidate_31_34_portal_category_pnl.csv`
- `round5_backtester.py`

## Current Warning

The existing `candidate_37_40_blueprint.md` is a draft map, not build permission.

Known issues:

- It under-emphasizes `PEBBLES_M`, even though the marginal table flags it as the strongest practical undercapture.
- It recommends some portal-only/gated products without enough executable ablation proof.
- It includes products that may already be partially captured by candidate 36 but not proven additive to candidate 35.

The next worker should run executable probes first, then rewrite the blueprint.

## Historical Outputs

Most markdown files under `outputs/` are historical notes from candidate batches 1-34. They should not override the active root docs or candidate 35/36 outputs. Use them only when investigating a specific old candidate, probe, or failure mode.

Do not delete historical outputs; they preserve evidence and backtest context.
