# Worker Prompt: Multi-Engine Edge Expansion

Start the Round 5 multi-engine edge-expansion phase.

Do not start the iterative loop.
Do not create `round5_iterative_*.py`.
Do not create candidates 26-30 yet.
Do not modify candidates 23/24/25.
Do not run another shallow generic research pass.

## Context

Integration works.

Current benchmark branches:

- `round5_candidate_23.py`: about `183.8k` full, `37.2k` portal.
- `round5_candidate_24.py`: about `131.1k` full, `41.8k` portal.
- `round5_candidate_25.py`: about `156.8k` full, `38.9k` portal, official portal aligned with replay.

The next jump will not come from tiny parameter tweaks. It must come from specialized product/category engines and better extraction from products where oracle capacity is still much larger than executable PnL.

## Core Instruction

One submitted file can contain many independent engines.

Do not force all products into one global strategy. For each product/category, find the engine that fits it:

- fair-value / synthetic basket,
- passive market making,
- taker directional,
- long-horizon momentum,
- long-horizon reversal,
- breakout continuation,
- extreme mean reversion,
- semantic/name curve residual,
- category curve residual,
- pair/basket/factor residual,
- lead-lag,
- microprice / imbalance,
- regime-gated hybrid,
- inventory-aware hybrid,
- product-specific anomaly engine.

The goal is to design and validate as many executable product-specific engines as possible, then produce a candidate 26-30 plan. Do not create candidates 26-30 yet.

## Read First

Read:

- `ROUND5/research/README.md`
- `ROUND5/research/round5_learning_plan.md`
- `ROUND5/research/round5_missing_edge_research_plan.md`
- `ROUND5/research/outputs/candidate_21_25_attribution.md`
- `ROUND5/research/outputs/exhaustive_remaining_edge_summary.md`
- `ROUND5/research/outputs/exhaustive_remaining_edge_table.csv`
- `ROUND5/research/outputs/exhaustive_product_classification.csv`
- `ROUND5/research/outputs/exhaustive_candidate_26_30_inputs.md`

Use earlier outputs only as supporting evidence.

## Mindset

Be aggressive.

Do not reject high-oracle products just because the first generic probe failed.
Do not hide behind robustness as an excuse for low PnL.
Do not be satisfied with `+400` or `+800` if oracle says the product has tens of thousands of portal capacity.
Do not blindly trade all products either.

The standard is:

- build specialized engines,
- test them quickly,
- keep what produces executable PnL,
- explain what still fails.

## Priority

Prioritize high-oracle / under-captured products:

- `MICROCHIP_SQUARE`
- `MICROCHIP_TRIANGLE`
- `MICROCHIP_RECTANGLE`
- `ROBOT_DISHES`
- `ROBOT_MOPPING`
- `ROBOT_VACUUMING`
- `SLEEP_POD_POLYESTER`
- `SLEEP_POD_SUEDE`
- `SLEEP_POD_LAMB_WOOL`
- `SLEEP_POD_NYLON`
- `PANEL_2X4`
- `PANEL_4X4`
- `PANEL_2X2`
- `TRANSLATOR_GRAPHITE_MIST`
- `TRANSLATOR_VOID_BLUE`
- `TRANSLATOR_SPACE_GRAY`
- `TRANSLATOR_ECLIPSE_CHARCOAL`
- `GALAXY_SOUNDS_PLANETARY_RINGS`
- `GALAXY_SOUNDS_SOLAR_WINDS`
- `GALAXY_SOUNDS_DARK_MATTER`
- `GALAXY_SOUNDS_BLACK_HOLES`
- `UV_VISOR_ORANGE`
- `UV_VISOR_RED`
- `UV_VISOR_YELLOW`
- `UV_VISOR_MAGENTA`
- `OXYGEN_SHAKE_GARLIC`
- `OXYGEN_SHAKE_EVENING_BREATH`
- `OXYGEN_SHAKE_MORNING_BREATH`
- `OXYGEN_SHAKE_MINT`
- `OXYGEN_SHAKE_CHOCOLATE`
- all `SNACKPACK_*`

Also revisit currently validated products to see whether a better engine exists.

## Required Research

For each high-priority product/category, run multiple engine families. Use temporary probes freely.

At minimum, test:

- momentum/reversal horizons `1/2/5/10/25/50/100/200/500`,
- volatility-normalized variants,
- breakout high / breakout low / failed breakout,
- rolling mean reversion,
- category mean and category median reversion,
- semantic/name-curve residuals,
- leave-one-product synthetic fair value,
- pair residuals against best anchors,
- PCA/factor residuals where useful,
- lead-lag against category leaders,
- microprice and imbalance,
- spread/depth filters,
- passive versus taker execution,
- threshold sweeps,
- inventory-aware throttles,
- entry/exit asymmetry,
- regime-gated versions.

Use additional simulations where useful:

- horizon oracle,
- spread-adjusted oracle,
- passive-fill oracle,
- taker oracle,
- inventory-constrained oracle,
- regime oracle,
- markout/adverse-selection oracle,
- component ablation.

## Backtesting Rules

Use portal-window replay first because it is fast and aligns with official portal.

Run full Kevin/Xeeshan when:

- portal replay is promising,
- a product has high hidden-final importance,
- or a result looks suspiciously portal-fitted.

Do not run Rust unless explicitly asked.

## Outputs

Create:

- `ROUND5/research/outputs/multi_engine_edge_expansion/multi_engine_edge_expansion_summary.md`
- `ROUND5/research/outputs/multi_engine_edge_expansion/multi_engine_product_engine_table.csv`
- `ROUND5/research/outputs/multi_engine_edge_expansion/multi_engine_oracle_capture_table.csv`
- `ROUND5/research/outputs/multi_engine_edge_expansion/multi_engine_probe_score_table.csv`
- `ROUND5/research/outputs/multi_engine_edge_expansion/multi_engine_engine_family_results.csv`
- `ROUND5/research/outputs/multi_engine_edge_expansion/multi_engine_category_plan.md`
- `ROUND5/research/outputs/multi_engine_edge_expansion/multi_engine_candidate_26_30_plan.md`

The product table must include every one of the 50 products.

Each product must end with one of:

- `engine_validated`
- `engine_conditional`
- `engine_anchor_only`
- `engine_not_found_yet`

For `engine_not_found_yet`, explain what was tried and why it failed.

## Candidate 26-30 Plan

Stop after the plan. Do not create candidates 26-30.

The final candidate 26-30 plan should specify:

- which engines to include,
- which engines to gate,
- which engines to exclude,
- which current candidate to use as base,
- expected portal impact,
- expected full-history impact,
- main risks,
- exact validation test for each proposed candidate.

The plan should be ambitious. Candidates 26-30 should be multi-engine competition-grade files, not small candidate 24/25 parameter edits.
