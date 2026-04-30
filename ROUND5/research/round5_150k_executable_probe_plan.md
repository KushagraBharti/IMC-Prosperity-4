# Round 5 150k Executable Probe Plan

This is the active plan after the candidate 35/36 ceiling-gap pass.

The ceiling-gap pass produced a useful map, but not enough proof to build final candidates 37-40. The next step is executable probe conversion: take the top undercaptures, unused products, and conditional products, then prove which ones can actually add PnL to candidate 35/36.

## Objective

Push toward `150k+` official portal PnL by converting oracle/proxy gaps into executable engines.

Stretch target remains `200k+`, but 200k likely requires a new structural or execution edge beyond current engines.

## Current Benchmarks

| Strategy | Portal | Full | Role |
|---|---:|---:|---|
| `round5_candidate_35.py` | 91.9k | 287.4k | robust development base |
| `round5_candidate_36.py` | 105.5k | 36.7k | portal-upside branch / idea mine |
| `round5_candidate_34.py` | 105.9k | -49.8k | fragile portal exploit / component library |

The immediate goal is not to build candidate 37-40 yet. The immediate goal is to prove the engines that should go into candidate 37-40.

## Product Coverage Target

The final competition strategy should aim to actively trade at least `30` products if executable edge supports it.

This is not a license to trade bad products.

For every unused or weakly used product, the worker must decide one of:

- `validated_add`: executable standalone or portfolio-additive engine exists,
- `gated_add`: product can trade only under specific regimes or as part of a basket,
- `anchor_only`: useful for signals/fair value but not direct trading,
- `exclude`: no executable edge found after defensible tests.

Unused products must be investigated, not silently ignored.

## Known Ceiling-Gap Issues To Fix

The prior ceiling-gap blueprint is not build-ready.

Specific inconsistencies:

- `PEBBLES_M` is the strongest practical marginal gap but was not emphasized enough.
- `PEBBLES_XS` and `PEBBLES_L` still show undercapture and need direct repair probes.
- `UV_VISOR_AMBER`, `UV_VISOR_MAGENTA`, and `SLEEP_POD_LAMB_WOOL` have portal-positive or conditional evidence but negative or fragile full proxies; they need gating proof, not blind inclusion.
- `PANEL_2X4` appears already captured by candidate 36 but has unclear marginal value versus candidate 35; it needs ablation proof.
- `ROBOT_DISHES` remains high-oracle but historically hard to execute; it needs a specialized passive/fill probe, not another generic signal.

## Mandatory Probe Groups

### 1. PEBBLES Undercapture Probe

Products:

- `PEBBLES_M`
- `PEBBLES_XS`
- `PEBBLES_L`
- include `PEBBLES_S` and `PEBBLES_XL` as controls if needed

Goal:

- improve candidate 35 PEBBLES capture without damaging full-history robustness,
- test whether undercapture is caused by threshold, sizing, passive/taker mix, residual horizon, or inventory throttling,
- preserve the proven PEBBLES structural fair-value edge.

### 2. MICROCHIP / PANEL Probe

Products:

- `MICROCHIP_SQUARE`
- `MICROCHIP_CIRCLE`
- `MICROCHIP_TRIANGLE`
- `MICROCHIP_RECTANGLE`
- `PANEL_2X4`
- `PANEL_4X4`
- optional: other PANEL geometry products as anchors

Goal:

- convert high oracle capacity into executable engines,
- test shape/category formulas, residuals, momentum/reversal, breakout, passive fill, and regime gates,
- prove whether PANEL/MICROCHIP are true add-ons or portal-only noise.

### 3. ROBOT Passive / Fill Probe

Products:

- `ROBOT_DISHES`
- `ROBOT_LAUNDRY`
- `ROBOT_VACUUMING`
- optional: `ROBOT_IRONING`, `ROBOT_MOPPING` as controls

Goal:

- test whether the high-oracle ROBOT opportunity is passive/fill-quality rather than directional prediction,
- explicitly compare passive, improved passive, and taker versions,
- determine if `ROBOT_DISHES` is capturable or should remain excluded.

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

Goal:

- determine whether these are real conditional edges, basket-only products, or false positives,
- test color/material/flavor semantic curves, category residuals, regime gates, and product-specific momentum/reversal,
- avoid carrying tiny standalone positives that collapse in full history.

### 5. Other High-Gap / Unused Product Probe

Products include at minimum:

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

- fix unused product coverage,
- identify category-specific engines that current candidates miss,
- classify every product with executable evidence.

### 6. Candidate 35 Marginal Stack Probe

Goal:

- add only probe-proven pieces to candidate 35,
- test whether ranking/crowding/inventory interaction destroys theoretical gains,
- produce the evidence base for candidate 37-40.

This should be done after the group probes, not before.

## Required Testing

Use `ROUND5/research/round5_backtester.py`.

Portal-first:

```powershell
python ROUND5/research/round5_backtester.py <probe_files> --tools kevin xeeshan --suites portal --cap-check --jobs 10 --state portal --name <name>
```

Full score-only for promising probes:

```powershell
python ROUND5/research/round5_backtester.py <probe_files> --tools kevin xeeshan --suites full --jobs 8 --state none --name <name>
```

Rules:

- Cap checks are mandatory for stateful probes.
- Full score-only is mandatory for portal-positive probes before they can be called robust.
- Avoid `--full-logs` unless one finalist needs detailed attribution.
- State should stay below `40k`; below `30k` is preferred.

## Required Outputs

Create or update:

- `ROUND5/research/outputs/candidate_35_36_executable_probe_summary.md`
- `ROUND5/research/outputs/candidate_35_36_probe_score_table.md`
- `ROUND5/research/outputs/candidate_35_36_probe_score_table.csv`
- `ROUND5/research/outputs/candidate_35_36_undercapture_fix_table.csv`
- `ROUND5/research/outputs/candidate_35_36_unused_product_table.csv`
- `ROUND5/research/outputs/candidate_35_36_product_coverage_plan.csv`
- `ROUND5/research/outputs/candidate_37_40_blueprint.md`

The candidate 37-40 blueprint must be rewritten from executable probe results, not copied from the prior proxy blueprint.

## Stop Condition

Stop after:

- executable probe tables are complete,
- every product has a defensible role,
- undercaptured PEBBLES legs have been directly tested,
- unused products have been classified,
- candidate 37-40 blueprint has been revised from probe evidence.

Do not create candidates 37-40 until explicitly told.
