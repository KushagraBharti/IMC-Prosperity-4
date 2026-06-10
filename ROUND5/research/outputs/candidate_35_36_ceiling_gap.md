# Candidate 35/36 Ceiling Gap

This is an oracle/proxy research pass, not a submitted-strategy result. Raw oracle columns are hindsight capacity units and should not be read as achievable PnL. The practical columns use simple online engine proxies and current candidate 35/36 attribution.

## Main Read
- Candidate 35 current portal: `91.9k`; candidate 36 current portal: `105.5k`.
- Candidate 35 remains the best robust base. Candidate 36 is still the portal-upside idea mine.
- Raw taker/passive/inventory oracles show massive theoretical capacity, but practical online proxies are much smaller. This is the central gap: the data contains enough movement, but we do not yet have a clean online extractor for another 40k-100k.
- Practical marginal gaps point mostly to products where current candidates either undertrade or use the wrong family: `MICROCHIP_SQUARE`, `PEBBLES_M/XS`, `ROBOT_DISHES`, `PANEL_2X4`, `SLEEP_POD_SUEDE`, `MICROCHIP_TRIANGLE`, `ROBOT_LAUNDRY`, and selected OXYGEN/TRANSLATOR legs.
- The best route to 150k is not one product; it is a gated composite of multiple 2k-8k marginal edges plus a passive-fill engine probe.

## Practical Marginal Product Gaps

| Product | Category | Current Best | Practical Engine Proxy | Practical Marginal Proxy | Full Robust Proxy | Best Engine | Regime | Raw Oracle Units |
|---|---|---:|---:|---:|---:|---|---|---:|
| `PEBBLES_M` | PEBBLES | 1490 | 6780 | 5290 | 0 | reversal_200 | imbalance_extreme | 21735847 |
| `PEBBLES_L` | PEBBLES | 510 | 3550 | 3040 | 0 | reversal_50 | imbalance_extreme | 626232 |
| `UV_VISOR_MAGENTA` | UV_VISOR | 0 | 2380 | 2380 | 0 | momentum_50 | imbalance_extreme | 7245362 |
| `SLEEP_POD_SUEDE` | SLEEP_POD | 0 | 2150 | 2150 | 0 | reversal_100 | spread_low | 566912 |
| `SNACKPACK_STRAWBERRY` | SNACKPACK | 0 | 2000 | 2000 | 0 | reversal_200 | imbalance_extreme | 21589364 |
| `MICROCHIP_CIRCLE` | MICROCHIP | 0 | 1885 | 1885 | 0 | reversal_100 | spread_low | 296057 |
| `PEBBLES_XS` | PEBBLES | -672 | 1760 | 1760 | 0 | momentum_100 | imbalance_extreme | 192082938 |
| `GALAXY_SOUNDS_BLACK_HOLES` | GALAXY_SOUNDS | 0 | 1290 | 1290 | 0 | reversal_50 | imbalance_extreme | 29468696 |
| `SNACKPACK_RASPBERRY` | SNACKPACK | 0 | 950 | 950 | 0 | reversal_200 | imbalance_extreme | 4345472 |
| `ROBOT_VACUUMING` | ROBOT | 0 | 910 | 910 | 0 | reversal_200 | spread_low | 15768240 |
| `UV_VISOR_YELLOW` | UV_VISOR | 782 | 1620 | 838 | 0 | reversal_200 | spread_low | 29607340 |
| `SNACKPACK_CHOCOLATE` | SNACKPACK | 0 | 735 | 735 | 0 | momentum_200 | spread_low | 9185556 |
| `OXYGEN_SHAKE_EVENING_BREATH` | OXYGEN_SHAKE | 290 | 980 | 690 | 0 | reversal_100 | spread_low | 8419278 |
| `MICROCHIP_SQUARE` | MICROCHIP | 4123 | 4625 | 502 | 0 | reversal_200 | spread_low | 773646206 |
| `SNACKPACK_PISTACHIO` | SNACKPACK | 0 | 320 | 320 | 0 | reversal_200 | imbalance_extreme | 11590206 |

## Category Practical Gap

| Category | Current Best | Practical Marginal Proxy | Raw Oracle Units |
|---|---:|---:|---:|
| PEBBLES | 22607 | 10090 | 379105586 |
| SNACKPACK | 0 | 4250 | 47866464 |
| UV_VISOR | 12277 | 3218 | 157744434 |
| MICROCHIP | 16072 | 2387 | 847378790 |
| SLEEP_POD | 11754 | 2150 | 173110280 |
| GALAXY_SOUNDS | 14332 | 1290 | 76681380 |
| ROBOT | 12707 | 910 | 266496674 |
| OXYGEN_SHAKE | 10236 | 690 | 109388735 |
| PANEL | 19583 | 0 | 157882068 |
| TRANSLATOR | 14955 | 0 | 109431038 |

## Diagnostics That Mattered
- Taker oracle: useful for ranking high-movement products, but far too optimistic as literal PnL.
- Passive-fill oracle: confirms why leaderboard-scale strategies may be fill-quality harvesters, but needs an actual passive engine to convert capacity.
- Inventory-constrained oracle: shows many products can hold limit-size directional positions, but naive always-in switching is not enough.
- Residual/fair-value oracle: category structure exists outside PEBBLES, especially MICROCHIP/PANEL/TRANSLATOR, but not as cleanly as PEBBLES.
- Regime oracle: the important next lever. Candidate 36-style portal edges need spread/vol/trend/imbalance gating to avoid day2/day3 toxicity.
- Marginal-addition oracle: no single obvious +40k plug-in. Candidate 37-40 need multi-engine additions and an information candidate for passive fill.

## 150k / 200k Read
- `150k` is plausible but not yet proven. It likely requires stacking several gated additions on candidate 35 or finding a better passive-fill engine.
- `200k` likely requires a new structural/execution edge, not just adding known candidate 36 legs. The raw oracle says capacity exists; the practical engine proxies do not yet explain 200k.
- Candidate 37-40 should therefore include: one robust gated 35 extension, one portal-upside 36 cleanup, one passive-fill information candidate, and one aggressive composite.
