# Round 5 Iterative Loop

Do not start this loop yet.

The iterative loop begins only after the active multi-engine edge-expansion phase is complete and candidates 26-30 have been created and scored.

## Current Blocker

Candidates 23/24/25 prove integration works:

- `round5_candidate_23.py`: robust branch, about `183.8k` full and `37.2k` portal.
- `round5_candidate_24.py`: portal branch, about `41.8k` portal and `131.1k` full.
- `round5_candidate_25.py`: balanced official-validated branch, about `38.9k` portal and `156.8k` full.

However, these are not final. The next gain must come from more specialized product/category engines, not minor parameter tuning.

## Preconditions Before Iteration

Before creating `round5_iterative_*.py`, complete:

1. Multi-engine edge expansion.
2. Candidate 26-30 construction.
3. Kevin/Xeeshan portal replay for candidates 26-30.
4. Kevin/Xeeshan full replay for promising candidates.
5. Product/category/component attribution for candidates 26-30.
6. Official portal testing for the best candidates if time allows.

Only then promote the top three branches into:

- `ROUND5/strategies/round5_iterative_1.py`
- `ROUND5/strategies/round5_iterative_2.py`
- `ROUND5/strategies/round5_iterative_3.py`

## Promotion Criteria

Pick top branches by:

- portal-window score,
- full-history score,
- official portal alignment,
- product-level attribution quality,
- robustness across Kevin/Xeeshan,
- diversity of edge engines,
- repair potential,
- hidden-final plausibility.

Do not pick purely by highest portal score if the branch is obviously fragile. Do not pick purely by full score if it fails portal alignment.

## Iteration Style

Once started:

- make one strategic change at a time,
- preserve product-specific engines,
- test portal replay first,
- run full replay for promising changes,
- perform product-level attribution,
- keep changes only if they improve PnL or reveal a useful failure mode,
- avoid timestamp hardcoding,
- avoid future leakage,
- avoid heavy dependencies in submitted files.

## Current Non-Iterative Next Step

Read:

- `ROUND5/research/round5_learning_plan.md`
- `ROUND5/research/round5_missing_edge_research_plan.md`
- `ROUND5/research/worker_prompt_multi_engine_edge_expansion.md`

Then run the multi-engine edge-expansion phase. Do not start the iterative loop until that phase and candidates 26-30 are complete.
