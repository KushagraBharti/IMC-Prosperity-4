# Round 5 Multi-Engine Missing-Edge Plan

This document replaces the older missing-edge plan. The previous plan found the PEBBLES core and non-PEBBLES breadth integrations. The active problem is now larger:

**Find stronger specialized engines for more products, then integrate them into one competition-grade strategy file.**

## Current Benchmark

Use these as benchmarks:

- `round5_candidate_23.py`: best full-history robustness, about `183.8k` full and `37.2k` portal.
- `round5_candidate_24.py`: best portal-window score, about `41.8k` portal and `131.1k` full.
- `round5_candidate_25.py`: official-validated balanced branch, about `38.9k` portal and `156.8k` full.

Any new engine must eventually improve one of these:

- higher portal score,
- higher full-history score,
- better hidden-final robustness,
- lower drawdown,
- or cleaner product attribution.

## Why More Edge Discovery Is Needed

The current strategy is still not using enough of the 50-product universe. The best teams are likely exploiting multiple independent product/category structures. A submitted strategy can run separate logic per product; therefore, there is no reason to force one global signal or one category model.

Products that currently produce only `+400` to `+2k` may still have much larger extractable edge if their current engine is wrong. Products labeled `not_currently_capturable` may need a new representation, not permanent exclusion.

## Correct Mindset

Do:

- design product-specific engines,
- test many execution styles,
- use oracle as a map to prioritize high-potential products,
- push position limits when signal quality is high,
- let each product have its own lookback, threshold, execution style, and inventory rules,
- build temporary probes freely,
- accept complexity if it remains online-only and platform-safe.

Do not:

- blindly trade all 50,
- blindly reject high-oracle products after one generic probe,
- force all products into PEBBLES-style fair value,
- force all products into generic momentum/reversal,
- call tiny portal positives strategy-grade without replay/attribution,
- optimize only to one portal window,
- hardcode exact timestamps or future data.

## Edge Discovery Simulations

Oracle-style studies are useful, but use multiple variants:

### Price-Movement Oracles

- one-step direction oracle,
- horizon direction oracle for `1/2/5/10/25/50/100/200/500`,
- volatility-normalized oracle,
- breakout continuation oracle,
- reversal-after-extreme oracle,
- trend persistence oracle,
- regime-conditioned oracle.

### Execution Oracles

- taker-only oracle after spread,
- passive-fill oracle using top-of-book availability,
- market-making oracle with inventory constraints,
- quote-placement oracle at bid/ask/improved prices,
- fill-quality oracle with markout,
- adverse-selection oracle,
- liquidation/end-window sensitivity oracle.

### Structural Oracles

- category synthetic fair-value oracle,
- leave-one-product basket oracle,
- semantic/name-curve residual oracle,
- pair residual oracle,
- PCA/factor residual oracle,
- lead-lag oracle,
- anchor-product oracle.

### Strategy-Family Probes

Every high-potential product should be tested against several families:

- passive market making,
- taker directional,
- long-horizon momentum,
- long-horizon reversal,
- breakout continuation,
- extreme mean reversion,
- category residual,
- semantic curve residual,
- lead-lag follower,
- imbalance/microprice,
- regime-gated hybrid,
- inventory-aware hybrid.

## Priority Products

Start with products that are high-oracle and either weakly captured or unsolved:

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

The list is not exclusive. If a lower-oracle product shows a strong engine, test it.

## Output Requirements

The next worker should create outputs under:

- `ROUND5/research/outputs/multi_engine_edge_expansion/`

Required files:

- `multi_engine_edge_expansion_summary.md`
- `multi_engine_product_engine_table.csv`
- `multi_engine_oracle_capture_table.csv`
- `multi_engine_probe_score_table.csv`
- `multi_engine_engine_family_results.csv`
- `multi_engine_category_plan.md`
- `multi_engine_candidate_26_30_plan.md`

The final plan must say exactly which engines should go into candidates 26-30, but candidates 26-30 should not be created until explicitly instructed.
