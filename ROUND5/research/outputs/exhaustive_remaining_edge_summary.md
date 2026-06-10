# Exhaustive Remaining-Edge Summary

This pass re-scanned all 50 products against momentum/reversal horizons, volatility-normalized variants, breakouts, rolling/category mean reversion, category median deviation, semantic/name curves, basket and PCA residuals, lead-lag, order-book imbalance, microprice, spread/depth imbalance, and existing formal replay attribution. Candidate files were not modified.

## Validated Standalone Edges

`MICROCHIP_OVAL`, `OXYGEN_SHAKE_GARLIC`, `PANEL_4X4`, `PEBBLES_L`, `PEBBLES_M`, `PEBBLES_S`, `PEBBLES_XL`, `PEBBLES_XS`, `ROBOT_IRONING`, `SLEEP_POD_COTTON`, `UV_VISOR_ORANGE`

## Conditional / Basket / Anchor Edges

`GALAXY_SOUNDS_PLANETARY_RINGS`, `MICROCHIP_RECTANGLE`, `MICROCHIP_SQUARE`, `MICROCHIP_TRIANGLE`, `OXYGEN_SHAKE_EVENING_BREATH`, `PANEL_2X4`, `ROBOT_LAUNDRY`, `ROBOT_MOPPING`, `SLEEP_POD_LAMB_WOOL`, `SLEEP_POD_NYLON`, `SLEEP_POD_POLYESTER`, `SLEEP_POD_SUEDE`, `TRANSLATOR_ASTRO_BLACK`, `TRANSLATOR_GRAPHITE_MIST`, `TRANSLATOR_VOID_BLUE`, `UV_VISOR_AMBER`, `UV_VISOR_RED`

## Excluded / Not Currently Capturable

`ROBOT_DISHES`, `TRANSLATOR_SPACE_GRAY`, `TRANSLATOR_ECLIPSE_CHARCOAL`, `GALAXY_SOUNDS_BLACK_HOLES`, `PANEL_2X2`, `ROBOT_VACUUMING`, `UV_VISOR_YELLOW`, `GALAXY_SOUNDS_SOLAR_WINDS`, `PANEL_1X4`, `MICROCHIP_CIRCLE`, `UV_VISOR_MAGENTA`, `GALAXY_SOUNDS_DARK_MATTER`, `GALAXY_SOUNDS_SOLAR_FLAMES`, `OXYGEN_SHAKE_MINT`, `OXYGEN_SHAKE_MORNING_BREATH`, `PANEL_1X2`, `OXYGEN_SHAKE_CHOCOLATE`, `SNACKPACK_RASPBERRY`, `SNACKPACK_STRAWBERRY`, `SNACKPACK_CHOCOLATE`, `SNACKPACK_VANILLA`, `SNACKPACK_PISTACHIO`

## Largest Oracle-To-Executable Gaps

- `PEBBLES_XL` (PEBBLES): portal h1 oracle `174835`, best portal proxy `291008`, best known portal candidate `9560`, class `validated_edge`. candidate 16/23/24/25 validates all five through online synthetic fair-value market making; some individual PnL can be negative but category edge is structural.
- `MICROCHIP_SQUARE` (MICROCHIP): portal h1 oracle `134740`, best portal proxy `474126`, best known portal candidate `5022`, class `conditional_edge`. portal/integration PnL is positive but full-history attribution is weak or negative; treat as portal-fragile and gate hard.
- `PEBBLES_XS` (PEBBLES): portal h1 oracle `81490`, best portal proxy `344030`, best known portal candidate `0`, class `validated_edge`. candidate 16/23/24/25 validates all five through online synthetic fair-value market making; some individual PnL can be negative but category edge is structural.
- `MICROCHIP_TRIANGLE` (MICROCHIP): portal h1 oracle `74455`, best portal proxy `90206`, best known portal candidate `1242`, class `conditional_edge`. edge appears in a component/probe but is too small or unstable to call standalone strategy-grade.
- `PEBBLES_M` (PEBBLES): portal h1 oracle `64980`, best portal proxy `348616`, best known portal candidate `1490`, class `validated_edge`. candidate 16/23/24/25 validates all five through online synthetic fair-value market making; some individual PnL can be negative but category edge is structural.
- `MICROCHIP_RECTANGLE` (MICROCHIP): portal h1 oracle `63905`, best portal proxy `428480`, best known portal candidate `859`, class `conditional_edge`. portal/integration PnL is positive but full-history attribution is weak or negative; treat as portal-fragile and gate hard.
- `PEBBLES_L` (PEBBLES): portal h1 oracle `61395`, best portal proxy `246104`, best known portal candidate `0`, class `validated_edge`. candidate 16/23/24/25 validates all five through online synthetic fair-value market making; some individual PnL can be negative but category edge is structural.
- `PEBBLES_S` (PEBBLES): portal h1 oracle `70075`, best portal proxy `202151`, best known portal candidate `11490`, class `validated_edge`. candidate 16/23/24/25 validates all five through online synthetic fair-value market making; some individual PnL can be negative but category edge is structural.
- `ROBOT_MOPPING` (ROBOT): portal h1 oracle `58930`, best portal proxy `115242`, best known portal candidate `1622`, class `conditional_edge`. edge appears in a component/probe but is too small or unstable to call standalone strategy-grade.
- `SLEEP_POD_POLYESTER` (SLEEP_POD): portal h1 oracle `58200`, best portal proxy `369978`, best known portal candidate `2022`, class `conditional_edge`. edge appears in a component/probe but is too small or unstable to call standalone strategy-grade.
- `MICROCHIP_OVAL` (MICROCHIP): portal h1 oracle `55015`, best portal proxy `425606`, best known portal candidate `3298`, class `validated_edge`. positive integrated/formal replay attribution on portal and full-history support.
- `ROBOT_DISHES` (ROBOT): portal h1 oracle `51425`, best portal proxy `254653`, best known portal candidate `0`, class `not_currently_capturable`. large analytical oracle/proxy remains, but no executable replay has confirmed capture; treat as not currently capturable, not a tradable edge.

## Category Results

- `PEBBLES`: `multi-product strategy-grade`; validated `PEBBLES_XS,PEBBLES_S,PEBBLES_M,PEBBLES_L,PEBBLES_XL`; conditional `none`; excluded `none`; best family `breakout_low_reversal`.
- `MICROCHIP`: `selective product trading only`; validated `MICROCHIP_OVAL`; conditional `MICROCHIP_SQUARE,MICROCHIP_RECTANGLE,MICROCHIP_TRIANGLE`; excluded `MICROCHIP_CIRCLE`; best family `breakout_low_reversal`.
- `SLEEP_POD`: `selective product trading only`; validated `SLEEP_POD_COTTON`; conditional `SLEEP_POD_SUEDE,SLEEP_POD_LAMB_WOOL,SLEEP_POD_POLYESTER,SLEEP_POD_NYLON`; excluded `none`; best family `breakout_low_reversal`.
- `ROBOT`: `selective product trading only`; validated `ROBOT_IRONING`; conditional `ROBOT_MOPPING,ROBOT_LAUNDRY`; excluded `ROBOT_VACUUMING,ROBOT_DISHES`; best family `breakout_low_reversal`.
- `TRANSLATOR`: `conditional/anchor only`; validated `none`; conditional `TRANSLATOR_ASTRO_BLACK,TRANSLATOR_GRAPHITE_MIST,TRANSLATOR_VOID_BLUE`; excluded `TRANSLATOR_SPACE_GRAY,TRANSLATOR_ECLIPSE_CHARCOAL`; best family `breakout_high`.
- `PANEL`: `selective product trading only`; validated `PANEL_4X4`; conditional `PANEL_2X4`; excluded `PANEL_1X2,PANEL_2X2,PANEL_1X4`; best family `breakout_low_reversal`.
- `GALAXY_SOUNDS`: `conditional/anchor only`; validated `none`; conditional `GALAXY_SOUNDS_PLANETARY_RINGS`; excluded `GALAXY_SOUNDS_DARK_MATTER,GALAXY_SOUNDS_BLACK_HOLES,GALAXY_SOUNDS_SOLAR_WINDS,GALAXY_SOUNDS_SOLAR_FLAMES`; best family `breakout_low_reversal`.
- `UV_VISOR`: `selective product trading only`; validated `UV_VISOR_ORANGE`; conditional `UV_VISOR_AMBER,UV_VISOR_RED`; excluded `UV_VISOR_YELLOW,UV_VISOR_MAGENTA`; best family `breakout_low_reversal`.
- `OXYGEN_SHAKE`: `selective product trading only`; validated `OXYGEN_SHAKE_GARLIC`; conditional `OXYGEN_SHAKE_EVENING_BREATH`; excluded `OXYGEN_SHAKE_MORNING_BREATH,OXYGEN_SHAKE_MINT,OXYGEN_SHAKE_CHOCOLATE`; best family `breakout_low_reversal`.
- `SNACKPACK`: `exclude until new signal family appears`; validated `none`; conditional `none`; excluded `SNACKPACK_CHOCOLATE,SNACKPACK_VANILLA,SNACKPACK_PISTACHIO,SNACKPACK_STRAWBERRY,SNACKPACK_RASPBERRY`; best family `breakout_low_reversal`.

## Required Answers

1. Validated standalone edges are the PEBBLES fair-value group plus products with positive formal/probe replay and full-support in the product table.
2. Conditional products are those with component PnL or large proxies but not enough standalone replay evidence; these should be basket-only, regime-gated, or anchor-only.
3. Anchor/signal-only products are explicitly marked in `exhaustive_remaining_edge_table.csv` under `strategy_role`.
4. Excluded products are not currently capturable, usually because high oracle capacity collapses after spread/top-of-book costs or existing probes show adverse selection.
5. High-oracle failures are concentrated in products with large one-step hindsight capacity but no stable online signal; the gap table above lists the worst cases.
6. Largest remaining gaps should not be blindly traded; they require new execution ideas, not wider baskets.
7. Candidate 26-30 additions should come only from validated or strong conditional rows with positive candidate/probe attribution.
8. Products marked `not_currently_capturable` should not be touched despite high oracle unless a genuinely new signal family appears.
9. Best category families: PEBBLES synthetic fair value, long-horizon momentum/reversal for selected ROBOT/MICROCHIP/UV/GALAXY/OXYGEN, and selective unresolved-product momentum/reversal for SLEEP/TRANSLATOR/PANEL/UV.
10. Robust-enough integration discoveries are listed in `exhaustive_candidate_26_30_inputs.md`; anything else remains research-only.
