# Round 5 Active Learning Plan

This is the active source of truth for Round 5 research. Older markdown files under `ROUND5/research/outputs/` are historical artifacts unless this file references them directly.

## Objective

Maximize hidden final-round algorithmic PnL.

Do not optimize for academic cleanliness, small isolated edges, or a single strategy family. One submitted Python file can and should contain many independent product/category-specific engines if they are online-only and executable.

## Current State

The strongest current integrated strategies are:

| Strategy | Role | Portal replay | Full replay |
|---|---:|---:|---:|
| `round5_candidate_23.py` | robust integrated branch | ~37.2k | ~183.8k |
| `round5_candidate_24.py` | highest portal branch | ~41.8k | ~131.1k |
| `round5_candidate_25.py` | balanced official-validated branch | ~38.9k | ~156.8k |

Candidate 25 official portal matched local portal replay closely, so Kevin/Xeeshan portal-window replay is a usable fast proxy.

Candidates 26-30 do not exist yet. Do not create them until the active edge-expansion phase is complete.

## Core Strategic Correction

The correct architecture is not one generic scanner.

The correct architecture is one submitted `Trader` with multiple specialized engines:

- PEBBLES: optimized synthetic fair-value / passive market-making engine.
- MICROCHIP: shape/formula/residual/regime engines by product.
- ROBOT: product-specific engines; `ROBOT_DISHES` needs its own specialized search, not generic rejection.
- SLEEP_POD: material/name-curve and per-product momentum/reversal/regime engines.
- PANEL: geometry/product-specific engines.
- UV_VISOR: color-curve and product-specific momentum/regime engines.
- TRANSLATOR: product-specific momentum/reversal/anchor engines.
- OXYGEN_SHAKE: per-product reversal/momentum/regime engines.
- GALAXY_SOUNDS: product-specific trend/reversal/anchor engines.
- SNACKPACK: currently weak, but still eligible for specialized edge search.

Position limit is per product. Product count is not the limiting factor. Edge quality, online observability, fill quality, cache size, and platform safety are the limiting factors.

## Product Classifications

Use these files for the latest classifications:

- `ROUND5/research/outputs/exhaustive_remaining_edge_summary.md`
- `ROUND5/research/outputs/exhaustive_remaining_edge_table.csv`
- `ROUND5/research/outputs/exhaustive_product_classification.csv`
- `ROUND5/research/outputs/candidate_21_25_attribution.md`

Current high-level state:

### Validated Standalone / Strategy-Grade

- `PEBBLES_XS`
- `PEBBLES_S`
- `PEBBLES_M`
- `PEBBLES_L`
- `PEBBLES_XL`
- `MICROCHIP_OVAL`
- `ROBOT_IRONING`
- `SLEEP_POD_COTTON`
- `UV_VISOR_ORANGE`
- `OXYGEN_SHAKE_GARLIC`
- `PANEL_4X4`

### Conditional / Basket / Regime Edge

- `GALAXY_SOUNDS_PLANETARY_RINGS`
- `MICROCHIP_RECTANGLE`
- `MICROCHIP_SQUARE`
- `MICROCHIP_TRIANGLE`
- `OXYGEN_SHAKE_EVENING_BREATH`
- `PANEL_2X4`
- `ROBOT_LAUNDRY`
- `ROBOT_MOPPING`
- `SLEEP_POD_LAMB_WOOL`
- `SLEEP_POD_NYLON`
- `SLEEP_POD_POLYESTER`
- `SLEEP_POD_SUEDE`
- `TRANSLATOR_ASTRO_BLACK`
- `TRANSLATOR_GRAPHITE_MIST`
- `TRANSLATOR_VOID_BLUE`
- `UV_VISOR_AMBER`
- `UV_VISOR_RED`

### Not Currently Capturable

These are not permanently dead. They need specialized engines or a different research representation:

- `ROBOT_DISHES`
- `TRANSLATOR_SPACE_GRAY`
- `TRANSLATOR_ECLIPSE_CHARCOAL`
- `GALAXY_SOUNDS_BLACK_HOLES`
- `PANEL_2X2`
- `ROBOT_VACUUMING`
- `UV_VISOR_YELLOW`
- `GALAXY_SOUNDS_SOLAR_WINDS`
- `PANEL_1X4`
- `MICROCHIP_CIRCLE`
- `UV_VISOR_MAGENTA`
- `GALAXY_SOUNDS_DARK_MATTER`
- `GALAXY_SOUNDS_SOLAR_FLAMES`
- `OXYGEN_SHAKE_MINT`
- `OXYGEN_SHAKE_MORNING_BREATH`
- `PANEL_1X2`
- `OXYGEN_SHAKE_CHOCOLATE`
- all `SNACKPACK_*`

## Active Next Phase

Do not start the iterative loop.
Do not create `round5_iterative_*.py`.
Do not create candidates 26-30 yet.

The active phase is:

**Multi-engine edge expansion before final integration.**

The worker must search for stronger product/category-specific engines, especially for high-oracle products where current capture is weak. The target is not to force trades in all 50 products. The target is to design and test specialized engines for as many products as possible and only later integrate the engines that produce executable PnL.

## Edge Discovery Standards

An edge is not validated by oracle alone.

An edge is validated by:

- online-only signal construction,
- realistic portal-window replay,
- full replay when promising,
- product-level attribution,
- plausible execution economics,
- no timestamp hardcoding,
- no future leakage,
- platform-safe implementation path.

Oracle is a priority map, not truth.

## Required Research Style

Use many temporary probes. Be aggressive. Do not stop at generic 50/100 tick momentum/reversal.

Useful discovery methods include:

- hindsight oracle by product/category/horizon,
- achievable oracle after spread and depth costs,
- passive-fill oracle,
- taker oracle,
- inventory-constrained oracle,
- threshold-sweep oracle,
- regime oracle,
- trend/reversal horizon surface,
- breakout and breakdown surfaces,
- rolling mean and category mean reversion,
- semantic/name curve residuals,
- category synthetic fair values,
- pair/basket/PCA/factor residuals,
- lead-lag graph search,
- microprice and imbalance alpha,
- adverse-selection markouts,
- fill-quality estimates,
- endpoint/liquidation sensitivity,
- component ablations,
- product-specific execution style tests.

If a product remains unsolved, the final explanation must say what failed and why.

## Final Integration Comes Later

After multi-engine expansion, create candidates 26-30 as serious multi-engine competition files. Those candidates should not be minor refinements. They should combine the best specialized engines while preserving candidate 23/24/25 lessons.
