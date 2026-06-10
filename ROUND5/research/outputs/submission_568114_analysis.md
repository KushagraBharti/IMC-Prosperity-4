# Official Submission 568114 Analysis

## Files

- Official bundle: `ROUND5/official_submissions/568114.zip`
- Extracted files:
  - `ROUND5/official_submissions/568114/568114.py`
  - `ROUND5/official_submissions/568114/568114.json`
  - `ROUND5/official_submissions/568114/568114.log`
- Backtest outputs:
  - `ROUND5/research/outputs/backtests/submission_568114/568114_kevin_full.log`
  - `ROUND5/research/outputs/backtests/submission_568114/568114_xeeshan_full.log`
  - `ROUND5/research/outputs/backtests/submission_568114/568114_50kcap_kevin_full.log`
  - `ROUND5/research/outputs/backtests/submission_568114/568114_50kcap_xeeshan_full.log`

## Scores

| Test | Kevin | Xeeshan |
|---|---:|---:|
| Official portal | 77,710.56 | 77,710.56 |
| Portal replay, uncapped `traderData` | 87,593 | 87,633 |
| Portal replay, 50k `traderData` cap | 77,720 | 77,730 |
| Full backtest, uncapped `traderData` | 95,145 | 95,404 |
| Full backtest, 50k `traderData` cap | 115,882 | 116,014 |

The official portal result matches the 50k-cap portal replay. The old uncapped replay remains inflated and should not be trusted for broad stateful strategies.

## Official Portal Attribution

Official score: `77,710.56`.

| Category | Official PnL |
|---|---:|
| PEBBLES | 22,517 |
| MICROCHIP | 13,207 |
| ROBOT | 10,441 |
| TRANSLATOR | 9,322 |
| UV_VISOR | 8,049 |
| GALAXY_SOUNDS | 7,446 |
| SLEEP_POD | 3,970 |
| OXYGEN_SHAKE | 1,812 |
| SNACKPACK | 936 |
| PANEL | 10 |

Top products:

| Product | Official PnL |
|---|---:|
| PEBBLES_S | 10,956.78 |
| PEBBLES_XL | 9,561.25 |
| GALAXY_SOUNDS_PLANETARY_RINGS | 7,445.89 |
| MICROCHIP_OVAL | 5,561.20 |
| ROBOT_LAUNDRY | 4,806.00 |
| MICROCHIP_SQUARE | 4,378.36 |
| ROBOT_DISHES | 4,350.79 |
| UV_VISOR_AMBER | 4,112.06 |
| UV_VISOR_ORANGE | 3,936.66 |
| TRANSLATOR_SPACE_GRAY | 3,793.36 |
| TRANSLATOR_ECLIPSE_CHARCOAL | 3,670.70 |
| MICROCHIP_TRIANGLE | 3,267.81 |

Only material official losers:

| Product | Official PnL |
|---|---:|
| PANEL_1X2 | -909.77 |
| SNACKPACK_RASPBERRY | -93.14 |

## Execution Health

- Status: `FINISHED`
- Runtime/log errors: none found.
- Submission trades: `181`
- Filled quantity: `952`
- Average fill quantity: `5.26`
- Traded products: `27`
- Official graph max drawdown: about `7,631`
- Official recovery factor: about `10.2`

Portal cumulative PnL by timestamp block:

| Timestamp Block | Cumulative PnL |
|---:|---:|
| 0 | -489 |
| 10,000 | 13,044 |
| 20,000 | 19,841 |
| 30,000 | 24,749 |
| 40,000 | 33,728 |
| 50,000 | 36,029 |
| 60,000 | 48,877 |
| 70,000 | 51,050 |
| 80,000 | 66,084 |
| 90,000 | 77,711 |

## Code Structure

The strategy is a broad multi-engine portfolio:

- Anchor/fixed fair-value engine around `10_000` for selected products.
- PEBBLES synthetic fair-value engine, but only trades `PEBBLES_S`, `PEBBLES_M`, and `PEBBLES_XL`.
- Product-specific momentum/reversal engines.
- Category-relative residual engine for selected MICRO/PANEL/OXYGEN/UV products.
- Additional momentum extras for translator, galaxy, UV, robot, panel, and microchip products.

## Hardcoding / Overfit Read

Not timestamp-hardcoded:

- No timestamp branches.
- No local file reads.
- No official-log parsing.
- No future data usage visible in code.
- Uses only current/past price histories and current order book.

But it is heavily product/parameter selected:

- Product lists and thresholds are hand-selected.
- The comment says components were added where they survived an uploaded randomized run.
- `ANCHOR = 10_000` is a structural assumption and may be valid for several products, but it is also an explicit fixed fair-value anchor.
- It still crosses the official `traderData` cap, though only slightly: max local state about `52,232`, first crossing around timestamp `28,600`.

This is not disqualifying hardcoding, but it is definitely competition-tuned. It should be treated as a strong candidate, not as a fully general long-term market model.

## Verdict

This is a good strategy relative to our current Round 5 work:

- It is broad without collapsing.
- It fixed most of the candidate 29/30 failure mode.
- It gets official-scale PnL near the top-100 threshold.
- It has positive full replay and positive capped full replay.
- It has clean portal execution and no runtime errors.

Main risks:

- Still slightly over the 50k `traderData` cap.
- Some engines look portal-window tuned.
- Several full-history product contributions are unstable or sign-flipping.
- `PANEL_1X2`, `OXYGEN_SHAKE_MINT`, `MICROCHIP_SQUARE`, `GALAXY_SOUNDS_PLANETARY_RINGS`, and `ROBOT_DISHES` need careful treatment depending on whether the target is official portal or hidden robustness.

Recommended next action:

Use `568114.py` as the new best benchmark and repair base. The next candidate should keep the broad architecture, compress or hard-cap state safely below 40k, and ablate/gate the unstable branches rather than reverting to a narrow PEBBLES-only strategy.
