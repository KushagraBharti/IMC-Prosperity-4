# Multi-Engine Candidate 26-30 Plan

Do not create candidates 26-30 until explicitly instructed. This plan is portal-first by design. Full backtests are deferred unless a candidate/probe clears a strong portal threshold, because full runs are too slow for the discovery loop.

## Evidence Base

Current benchmarks:

- `round5_candidate_23.py`: robust integrated branch, about `37.2k` portal and `183.8k` full.
- `round5_candidate_24.py`: current portal benchmark, about `41.8k` portal and `131.1k` full.
- `round5_candidate_25.py`: balanced official-aligned branch, about `38.9k` portal and `156.8k` full.

Best multi-engine portal probes:

- `me_validated_addons.py`: `20,330` portal.
- `me_galaxy_trends.py`: `14,356` portal.
- `me_galaxy_positive_ablation.py`: `13,960` portal.
- `me_sleep_material_curve.py`: `12,940` portal, existing full `-43,370`.
- `me_panel_positive_ablation.py`: `12,857` portal.
- `me_sleep_positive_ablation.py`: `12,238` portal.
- `me_microchip_shape_breakout.py`: `11,719` portal, existing full `28,536`.
- `me_microchip_positive_ablation.py`: `11,168` portal.
- `me_translator_positive_ablation.py`: `11,076` portal.
- `me_oxygen_positive_ablation.py`: `10,858` portal.
- `me_uv_positive_ablation.py`: `8,440` portal.

Best individual portal probes from the final expansion:

- `TRANSLATOR_SPACE_GRAY`: `7,925`.
- `GALAXY_SOUNDS_DARK_MATTER`: `4,254`.
- `SLEEP_POD_LAMB_WOOL`: `4,174`.
- `MICROCHIP_SQUARE`: `4,123`.
- `OXYGEN_SHAKE_MORNING_BREATH`: `3,446`.
- `GALAXY_SOUNDS_SOLAR_FLAMES`: `3,246`.
- `TRANSLATOR_ECLIPSE_CHARCOAL`: `3,152`.
- `PANEL_1X2`: `2,827`.
- `MICROCHIP_RECTANGLE`: `2,666`.
- `PANEL_1X4`: `2,427`.

## Candidate 26: Clean Validated Add-On Portfolio

- Base: `round5_candidate_25.py`.
- Objective: beat candidate 25 without adding broad fragile baskets.
- Include engines:
  - PEBBLES synthetic fair-value market making.
  - `OXYGEN_SHAKE_GARLIC`: 200-tick reversal, individual portal `3,442`, prior full `29,262`.
  - `PANEL_4X4`: 50-tick momentum, individual portal `6,026`, prior full `1,844`.
  - `MICROCHIP_OVAL`: MICROCHIP shape/breakout, portal product PnL `4,379`.
  - `UV_VISOR_ORANGE`: 200-tick momentum, portal `3,959`, candidate full-positive.
  - `ROBOT_IRONING`: 100-tick momentum, portal `2,524`, full-positive.
  - `SLEEP_POD_COTTON`: candidate 25 style only; do not use the standalone 200-tick variant unless full retested.
- Exclude/gate: `UV_VISOR_RED`, GALAXY basket, TRANSLATOR basket, small PANEL sizes.
- Expected portal impact: candidate 25 `38.9k` -> target `48k-55k`.
- Validation: Kevin/Xeeshan portal first; full only if portal beats candidate 25 by `5k+`.

## Candidate 27: MICROCHIP Specialist

- Base: candidate 23/25 hybrid.
- Objective: exploit huge MICROCHIP oracle with a dedicated engine instead of generic breadth.
- Include:
  - `MICROCHIP_OVAL`: validated leg.
  - `MICROCHIP_SQUARE`: individual portal `4,123`, high oracle `134.7k`, full-fragile in previous integration.
  - `MICROCHIP_RECTANGLE`: individual portal `2,666`, high oracle `63.9k`.
- Optional/gated:
  - `MICROCHIP_TRIANGLE`: positive in integrated full history but weak in the shape portal probe.
- Exclude:
  - `MICROCHIP_CIRCLE`: still no engine.
- Evidence:
  - `me_microchip_shape_breakout.py`: `11,719` portal, existing full `28,536`.
  - `me_microchip_positive_ablation.py`: `11,168` portal after removing weak triangle.
  - `me_microchip_taker_stress.py`: only `3,407`, so default should be passive/improved passive, not taker-heavy.
- Expected portal impact: `+8k-12k` if shape legs combine cleanly.
- Validation: product attribution must show `SQUARE + RECTANGLE + OVAL` positive together; if `SQUARE` hurts full again, gate it.

## Candidate 28: Robust Full-History Multi-Engine

- Base: `round5_candidate_23.py`.
- Objective: protect hidden-final robustness while adding only engines with prior full support or strong economic logic.
- Include:
  - PEBBLES core.
  - `GALAXY_SOUNDS_PLANETARY_RINGS`: candidate 23 full `29,042`, portal `2,296`, multi-engine portal `4,625`.
  - `ROBOT_IRONING`: full/portal positive.
  - `OXYGEN_SHAKE_EVENING_BREATH`: full-positive, portal-small.
  - `MICROCHIP_TRIANGLE`: full-positive, portal-small.
  - `SLEEP_POD_SUEDE`: full-positive in candidate 23.
  - `OXYGEN_SHAKE_GARLIC`: new single-product robust add-on.
  - `UV_VISOR_ORANGE`: full-positive from candidate 25.
- Exclude/gate:
  - `TRANSLATOR_SPACE_GRAY`, `GALAXY_DARK_MATTER`, `PANEL_1X2`, `PANEL_1X4`, `UV_VISOR_RED` until full-tested.
- Expected portal impact: target `42k-50k`; full target above candidate 23.
- Validation: portal first; full only if portal is competitive with 24/25.

## Candidate 29: Portal-Upside Multi-Engine

- Base: `round5_candidate_24.py`.
- Objective: maximize portal-window upside with independent engines, accepting higher overfit risk.
- Include high-portal cleaned engines:
  - `me_validated_addons.py` products: `OXYGEN_SHAKE_GARLIC`, `UV_VISOR_ORANGE`, `PANEL_4X4`, `ROBOT_IRONING`, `MICROCHIP_OVAL`.
  - GALAXY positive engine: `DARK_MATTER`, `SOLAR_FLAMES`, `SOLAR_WINDS`, `PLANETARY_RINGS`; cleaned probe `13,960`.
  - TRANSLATOR positive engine: `SPACE_GRAY`, `ECLIPSE_CHARCOAL`; cleaned probe `11,076`.
  - PANEL positive engine: `4X4`, `1X2`, `1X4`, `2X2`; cleaned probe `12,857`.
  - OXYGEN positive engine: `MORNING_BREATH`, `CHOCOLATE`, `EVENING_BREATH`, `GARLIC`, `MINT`; probe `10,858`.
  - UV positive engine: `YELLOW`, `RED`, `ORANGE`; probe `8,440`.
- Explicitly avoid toxic broad legs:
  - `TRANSLATOR_GRAPHITE_MIST` and `VOID_BLUE` in this new translator engine because the taker/colorway variants hurt them.
  - `PANEL_2X4` in the portal-upside panel engine because it was negative in geometry.
  - `UV_MAGENTA`, `UV_AMBER` in the portal-upside UV engine.
- Expected portal impact: target `55k-70k`.
- Main risk: portal overfit. This candidate needs full validation only after portal replay clears candidate 24 by a meaningful margin.

## Candidate 30: Balanced Competition Portfolio

- Base: `round5_candidate_25.py`.
- Objective: combine strong validated add-ons with the best conditional engines, but avoid the most obviously fragile products.
- Include:
  - PEBBLES core.
  - Existing candidate 25 stable engines: `UV_VISOR_ORANGE`, `SLEEP_POD_COTTON`, `ROBOT_IRONING`, `MICROCHIP_TRIANGLE`, `OXYGEN_SHAKE_EVENING_BREATH`.
  - New validated add-ons: `OXYGEN_SHAKE_GARLIC`, `PANEL_4X4`, `MICROCHIP_OVAL`.
  - Selective conditional engines: `MICROCHIP_SQUARE`, `MICROCHIP_RECTANGLE`, `GALAXY_SOUNDS_PLANETARY_RINGS`, `TRANSLATOR_SPACE_GRAY`, `TRANSLATOR_ECLIPSE_CHARCOAL`, `PANEL_1X2`, `PANEL_1X4`.
- Gate:
  - `SLEEP_POD_LAMB_WOOL`, `SLEEP_POD_NYLON`, `UV_VISOR_RED`, `GALAXY_DARK_MATTER`, `GALAXY_SOLAR_FLAMES`.
- Exclude:
  - `ROBOT_DISHES` standalone: individual probes `664`, `-91`, and `-6,237`; too weak for priority.
  - `SNACKPACK_*`: best cleaned total only `1,728`.
  - `ROBOT_VACUUMING`, `MICROCHIP_CIRCLE`, `UV_VISOR_MAGENTA`, `GALAXY_BLACK_HOLES`.
- Expected portal impact: target `50k-60k`.
- Validation: portal replay first, then product attribution; full only if it beats candidate 25 portal.

## Product Treatment Summary

### Include First

`PEBBLES_XS`, `PEBBLES_S`, `PEBBLES_M`, `PEBBLES_L`, `PEBBLES_XL`, `OXYGEN_SHAKE_GARLIC`, `PANEL_4X4`, `MICROCHIP_OVAL`, `UV_VISOR_ORANGE`, `ROBOT_IRONING`, `SLEEP_POD_COTTON`.

### Gate / Candidate-Specific

`MICROCHIP_SQUARE`, `MICROCHIP_RECTANGLE`, `MICROCHIP_TRIANGLE`, `TRANSLATOR_SPACE_GRAY`, `TRANSLATOR_ECLIPSE_CHARCOAL`, `GALAXY_SOUNDS_DARK_MATTER`, `GALAXY_SOUNDS_SOLAR_FLAMES`, `GALAXY_SOUNDS_SOLAR_WINDS`, `GALAXY_SOUNDS_PLANETARY_RINGS`, `PANEL_1X2`, `PANEL_1X4`, `PANEL_2X2`, `SLEEP_POD_LAMB_WOOL`, `SLEEP_POD_NYLON`, `SLEEP_POD_POLYESTER`, `SLEEP_POD_SUEDE`, `UV_VISOR_RED`, `UV_VISOR_YELLOW`, `OXYGEN_SHAKE_MORNING_BREATH`, `OXYGEN_SHAKE_CHOCOLATE`, `OXYGEN_SHAKE_MINT`, `OXYGEN_SHAKE_EVENING_BREATH`.

### Exclude Until New Evidence

`ROBOT_DISHES` standalone, `ROBOT_VACUUMING`, `MICROCHIP_CIRCLE`, `UV_VISOR_MAGENTA`, `GALAXY_SOUNDS_BLACK_HOLES`, all `SNACKPACK_*` as candidate-priority engines.

## Validation Order

1. Create candidates 26-30 only when instructed.
2. Run Kevin/Xeeshan portal replay for all five.
3. Attribute product PnL immediately.
4. Run full Kevin/Xeeshan only for candidates that beat candidate 25/24 portal or contain suspicious portal-only engines.
5. Submit official portal only after local portal and product attribution agree.
