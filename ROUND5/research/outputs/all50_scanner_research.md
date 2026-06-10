# All-50 Scanner Research

This targeted sprint modeled all 50 Round 5 products as signal candidates and separated modeling coverage from trading selection. Candidate 13 remains the benchmark, but the scanner does not assume its PEBBLES market-making logic applies everywhere.

## Highest-Confidence Trade Set

- `PEBBLES_XL` (PEBBLES): role `trade`, signal `50_tick_reversal`, model `structural`, proxy `21561`, portal proxy `6110`, confidence `medium`, risk `timestamp-block concentration`.
- `PEBBLES_M` (PEBBLES): role `trade`, signal `25_tick_reversal`, model `structural`, proxy `12551`, portal proxy `3000`, confidence `high`, risk `execution/fill translation`.
- `PEBBLES_XS` (PEBBLES): role `trade`, signal `10_tick_reversal`, model `structural`, proxy `7011`, portal proxy `1702`, confidence `high`, risk `execution/fill translation`.
- `UV_VISOR_AMBER` (UV_VISOR): role `trade`, signal `50_tick_momentum`, model `semantic/name-based`, proxy `6886`, portal proxy `1235`, confidence `high`, risk `execution/fill translation`.
- `MICROCHIP_SQUARE` (MICROCHIP): role `trade`, signal `25_tick_reversal`, model `semantic/name-based`, proxy `5867`, portal proxy `1794`, confidence `high`, risk `timestamp-block concentration`.
- `PEBBLES_S` (PEBBLES): role `trade`, signal `50_tick_momentum`, model `structural`, proxy `4419`, portal proxy `1587`, confidence `medium`, risk `execution/fill translation`.
- `PEBBLES_L` (PEBBLES): role `trade`, signal `50_tick_momentum`, model `structural`, proxy `1393`, portal proxy `1994`, confidence `medium`, risk `execution/fill translation`.

## Anchor-Only Products

- `PANEL_2X2` (PANEL): semantic fair/model evidence or lead-lag evidence, but insufficient executable proxy/stability.
- `SLEEP_POD_COTTON` (SLEEP_POD): semantic fair/model evidence or lead-lag evidence, but insufficient executable proxy/stability.
- `SLEEP_POD_NYLON` (SLEEP_POD): semantic fair/model evidence or lead-lag evidence, but insufficient executable proxy/stability.
- `SLEEP_POD_POLYESTER` (SLEEP_POD): semantic fair/model evidence or lead-lag evidence, but insufficient executable proxy/stability.

## Excluded Products

`ROBOT_DISHES`, `ROBOT_IRONING`, `PANEL_1X4`, `MICROCHIP_RECTANGLE`, `OXYGEN_SHAKE_GARLIC`, `UV_VISOR_MAGENTA`, `SLEEP_POD_LAMB_WOOL`, `TRANSLATOR_VOID_BLUE`, `GALAXY_SOUNDS_PLANETARY_RINGS`, `TRANSLATOR_ASTRO_BLACK`, `OXYGEN_SHAKE_MINT`, `PANEL_2X4`, `ROBOT_LAUNDRY`, `UV_VISOR_ORANGE`, `UV_VISOR_YELLOW`, `ROBOT_MOPPING`, `TRANSLATOR_ECLIPSE_CHARCOAL`, `GALAXY_SOUNDS_DARK_MATTER`, `MICROCHIP_OVAL`, `GALAXY_SOUNDS_SOLAR_FLAMES`, `TRANSLATOR_GRAPHITE_MIST`, `MICROCHIP_TRIANGLE`, `OXYGEN_SHAKE_CHOCOLATE`, `MICROCHIP_CIRCLE`, `SLEEP_POD_SUEDE`, `OXYGEN_SHAKE_EVENING_BREATH`, `SNACKPACK_STRAWBERRY`, `UV_VISOR_RED`, `ROBOT_VACUUMING`, `SNACKPACK_RASPBERRY`, `PANEL_4X4`, `TRANSLATOR_SPACE_GRAY`, `GALAXY_SOUNDS_BLACK_HOLES`, `SNACKPACK_PISTACHIO`, `GALAXY_SOUNDS_SOLAR_WINDS`, `PANEL_1X2`, `SNACKPACK_CHOCOLATE`, `OXYGEN_SHAKE_MORNING_BREATH`, `SNACKPACK_VANILLA`

## Category Findings

- `PEBBLES`: oracle `13463353`, tradeable `PEBBLES_XL,PEBBLES_M,PEBBLES_XS,PEBBLES_S,PEBBLES_L`, anchors `none`, integration: core candidate 13 improvement; trade all five via exact fair-value scanner.
- `MICROCHIP`: oracle `10883851`, tradeable `MICROCHIP_SQUARE`, anchors `none`, integration: candidate 18 only as MICROCHIP-specific test; do not blend blindly.
- `ROBOT`: oracle `7659700`, tradeable `none`, anchors `none`, integration: anchor/exclude unless new evidence appears.
- `SLEEP_POD`: oracle `7215947`, tradeable `none`, anchors `SLEEP_POD_NYLON,SLEEP_POD_POLYESTER,SLEEP_POD_COTTON`, integration: anchor/exclude unless new evidence appears.
- `TRANSLATOR`: oracle `6440575`, tradeable `none`, anchors `none`, integration: anchor/exclude unless new evidence appears.
- `PANEL`: oracle `6101462`, tradeable `none`, anchors `PANEL_2X2`, integration: anchor/exclude unless new evidence appears.
- `OXYGEN_SHAKE`: oracle `5254023`, tradeable `none`, anchors `none`, integration: anchor/exclude unless new evidence appears.
- `GALAXY_SOUNDS`: oracle `5187310`, tradeable `none`, anchors `none`, integration: anchor/exclude unless new evidence appears.
- `UV_VISOR`: oracle `4928752`, tradeable `UV_VISOR_AMBER`, anchors `none`, integration: candidate 17 scanner only; product-specific edge-gated.
- `SNACKPACK`: oracle `1177342`, tradeable `none`, anchors `none`, integration: anchor/exclude unless new evidence appears.

## Main Conclusions

- `PEBBLES` is still the only structural, all-products, high-confidence category. It deserves an improved candidate 13 branch.
- `SLEEP_POD` has semantic/name-curve evidence, but only selected products should be traded and only through strong edge gates.
- `MICROCHIP` has huge oracle capacity but the simple shape-curve signal is not stable enough to blend into PEBBLES. If tested, it should be isolated.
- `PANEL` has name/geometry structure but weaker execution evidence; it belongs in a gated name-curve test, not a core branch.
- Broad unmanaged baskets remain toxic. A broad scanner is justified only if it computes product-specific edges and skips weak products.
