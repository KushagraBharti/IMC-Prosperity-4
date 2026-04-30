# Worker Prompt: Round 5 150k Executable Probe Conversion

Proceed to the Round 5 `150k+` executable probe conversion phase.

Do not start the iterative loop.
Do not create `round5_iterative_*.py`.
Do not create candidates 37-40 yet.
Do not blindly mutate candidates 35/36.
Do not stop at oracle/proxy tables.

The prior ceiling-gap phase produced a useful map, but it did not prove executable add-ons. Your job now is to convert the top gaps, unused products, and undercaptured products into real probe evidence.

## Read First

Read these files before running anything:

- `ROUND5/research/README.md`
- `ROUND5/research/round5_150k_push_plan.md`
- `ROUND5/research/round5_150k_executable_probe_plan.md`
- `ROUND5/research/round5_backtester.py`
- `ROUND5/research/round5_backtester_usage.md`
- `ROUND5/research/outputs/candidate_35_36_ceiling_gap.md`
- `ROUND5/research/outputs/candidate_35_36_oracle_gap_table.csv`
- `ROUND5/research/outputs/candidate_35_36_marginal_engine_table.csv`
- `ROUND5/research/outputs/candidate_35_36_regime_oracle_table.csv`
- `ROUND5/research/outputs/candidate_35_36_score_table.md`
- `ROUND5/research/outputs/candidate_35_36_ablation_summary.md`
- `ROUND5/strategies/round5_candidate_35.py`
- `ROUND5/strategies/round5_candidate_36.py`

## Current Truth

Candidate 35 is the current robust development base:

- portal: about `91.9k`
- full: about `287.4k`

Candidate 36 is the current portal-upside branch:

- portal: about `105.5k`
- full: about `36.7k`

Leaderboard target:

- top-100 cutoff: about `114k`
- immediate target: `150k+`
- stretch target: `200k+`

Final strategies should aim to trade at least `30` products if those products have validated or gated executable edge. Do not trade products merely for coverage, but do not leave products unused without testing.

## Main Objective

Fix all meaningful undercaptures and investigate all unused products.

This phase should answer:

- Which undercaptured products can be improved with executable strategy changes?
- Which currently unused products can become validated or gated additions?
- Which high-oracle products still fail, and exactly why?
- Which engines are additive to candidate 35 rather than only good standalone?
- Which engines should become candidates 37-40?
- Can we plausibly move from `91k-105k` toward `150k+` by stacking proven add-ons?

## Mandatory Probe Groups

Create temporary probe strategies/scripts as needed under `ROUND5/research/probes/` or another appropriate research path.

Do not create candidate 37-40 files yet.

### 1. PEBBLES Undercapture Probe

Products:

- `PEBBLES_M`
- `PEBBLES_XS`
- `PEBBLES_L`
- use `PEBBLES_S` and `PEBBLES_XL` as controls if needed

Required tests:

- preserve existing PEBBLES fair-value logic,
- threshold/sizing variants,
- passive versus taker/improved passive execution,
- inventory throttle variants,
- residual horizon variants,
- candidate 35-compatible stack test.

Goal:

- improve candidate 35 PEBBLES capture without breaking full robustness.

### 2. MICROCHIP / PANEL Probe

Products:

- `MICROCHIP_SQUARE`
- `MICROCHIP_CIRCLE`
- `MICROCHIP_TRIANGLE`
- `MICROCHIP_RECTANGLE`
- `PANEL_2X4`
- `PANEL_4X4`
- other PANEL products as anchors if useful

Required tests:

- product-specific momentum/reversal,
- breakout,
- shape/category formula residuals,
- pair residuals,
- passive fill versions,
- taker versions only when expected edge exceeds spread,
- regime gates by spread, imbalance, volatility, and depth.

Goal:

- convert high oracle capacity into real executable add-ons or prove why it is not capturable.

### 3. ROBOT Passive / Fill Probe

Products:

- `ROBOT_DISHES`
- `ROBOT_LAUNDRY`
- `ROBOT_VACUUMING`
- optionally `ROBOT_IRONING` and `ROBOT_MOPPING` as controls

Required tests:

- passive market making,
- improved passive,
- short-horizon reversal/liquidity,
- long-horizon momentum/reversal,
- taker trigger,
- fill/markout attribution.

Goal:

- determine whether the high-oracle ROBOT gap is an execution/fill-quality edge.

### 4. SLEEP / UV / SNACKPACK Conditional Probe

Products:

- `SLEEP_POD_SUEDE`
- `SLEEP_POD_LAMB_WOOL`
- `SLEEP_POD_POLYESTER`
- `SLEEP_POD_NYLON`
- `UV_VISOR_MAGENTA`
- `UV_VISOR_YELLOW`
- `UV_VISOR_AMBER`
- `SNACKPACK_STRAWBERRY`
- `SNACKPACK_RASPBERRY`
- `SNACKPACK_CHOCOLATE`
- `SNACKPACK_PISTACHIO`
- `SNACKPACK_VANILLA`

Required tests:

- material/color/flavor semantic curves,
- category residuals,
- product-specific momentum/reversal,
- regime-gated variants,
- basket-only variants,
- candidate 35 marginal stack variants.

Goal:

- identify real conditional additions and eliminate fake small positives.

### 5. Remaining High-Gap / Unused Product Probe

Include at minimum:

- `GALAXY_SOUNDS_BLACK_HOLES`
- `GALAXY_SOUNDS_DARK_MATTER`
- `GALAXY_SOUNDS_SOLAR_FLAMES`
- `GALAXY_SOUNDS_SOLAR_WINDS`
- `OXYGEN_SHAKE_EVENING_BREATH`
- `OXYGEN_SHAKE_CHOCOLATE`
- `OXYGEN_SHAKE_MINT`
- `OXYGEN_SHAKE_MORNING_BREATH`
- `TRANSLATOR_GRAPHITE_MIST`
- `TRANSLATOR_VOID_BLUE`
- `TRANSLATOR_SPACE_GRAY`
- `TRANSLATOR_ECLIPSE_CHARCOAL`

Goal:

- classify every unused or weakly used product with evidence,
- find any missed category-specific engines.

### 6. Candidate 35 Marginal Stack Probe

After group probes, build temporary stack probes that add only the best proven engines to candidate 35.

Required tests:

- additive stack with only robust/full-positive engines,
- portal-upside stack with gated portal-positive engines,
- broad 30+ product stack with strict gates,
- ablation to identify products that crowd out better trades.

Goal:

- prove whether stacked additions can move toward `150k+` without destroying candidate 35's full-history strength.

## Testing Requirements

Use `ROUND5/research/round5_backtester.py`.

Portal first:

```powershell
python ROUND5/research/round5_backtester.py <probe_files> --tools kevin xeeshan --suites portal --cap-check --jobs 10 --state portal --name <experiment_name>
```

Full score-only for promising portal-positive probes:

```powershell
python ROUND5/research/round5_backtester.py <probe_files> --tools kevin xeeshan --suites full --jobs 8 --state none --name <experiment_name>
```

Rules:

- Cap checks are mandatory for stateful probes.
- Full score-only is mandatory before calling a portal-positive probe robust.
- Avoid `--full-logs` unless needed for one finalist attribution.
- Keep returned `traderData` below `40k`; below `30k` is preferred.
- Kevin and Xeeshan should agree or the mismatch must be explained.

## Classification Standard

Every product must end with one of:

- `validated_add`: executable standalone or portfolio-additive engine exists,
- `gated_add`: product works only under explicit regimes or basket conditions,
- `anchor_only`: useful for signals/fair value but not direct trading,
- `exclude`: no executable edge found after defensible testing.

Do not classify a product as excluded after one generic failed signal.
Do not classify a product as validated because of one tiny portal-only positive.
Do not include portal-only products in the robust branch without a gate and full-history check.

## Required Outputs

Create or update:

- `ROUND5/research/outputs/candidate_35_36_executable_probe_summary.md`
- `ROUND5/research/outputs/candidate_35_36_probe_score_table.md`
- `ROUND5/research/outputs/candidate_35_36_probe_score_table.csv`
- `ROUND5/research/outputs/candidate_35_36_undercapture_fix_table.csv`
- `ROUND5/research/outputs/candidate_35_36_unused_product_table.csv`
- `ROUND5/research/outputs/candidate_35_36_product_coverage_plan.csv`
- `ROUND5/research/outputs/candidate_37_40_blueprint.md`

The updated candidate 37-40 blueprint must be based on executable probe results, not just oracle/proxy rows.

## Final Report Must Answer

1. Which undercaptures were actually fixed or improved?
2. Which unused products now have executable edges?
3. Which products remain excluded and why?
4. Which probe groups produced additive PnL versus standalone-only PnL?
5. Which additions survive full score-only validation?
6. Whether a 30+ product final strategy is now justified.
7. Whether `150k+` looks reachable from the probe evidence.
8. What exact candidates 37-40 should be after this phase.

Stop after executable probes, tables, classifications, and the revised blueprint.

Do not create candidates 37-40 until explicitly told.
