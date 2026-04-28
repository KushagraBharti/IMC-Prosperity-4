# Round 4 Portal Candidate Packet

Generated on 2026-04-27 after the first Round 4 learning and mini-experiment pass.

## Candidate Files

| Candidate | File | Thesis |
|---|---|---|
| 1 | `ROUND4/strategies/round4_candidate_1_522830_base.py` | Exact 522830 baseline, kept as the control and official calibration anchor. |
| 2 | `ROUND4/strategies/round4_candidate_2_option9_hydrofairoff.py` | Keeps the Round 3/Round 4 architecture, lowers voucher clip size from 20 to 9, and disables Hydrogel Mark fair-value adjustment while keeping Hydrogel passive flow logic. |
| 3 | `ROUND4/strategies/round4_candidate_3_option9_nohydro.py` | Same voucher-size improvement, but removes Hydrogel Mark fair and passive Mark quoting entirely. This isolates whether Hydrogel Mark flow is helping or overfitting official fills. |

## Backtest Table

| Strategy | Full Kevin | Full Xeeshan | Window Kevin | Window Xeeshan | Official |
|---|---:|---:|---:|---:|---:|
| `round4_candidate_1_522830_base.py` | 363,494 | 364,966 | 76,040 | 76,040 | 75,988.86 |
| `round4_candidate_2_option9_hydrofairoff.py` | 373,294 | 375,070 | 77,496 | 77,496 | 75,728.53 |
| `round4_candidate_3_option9_nohydro.py` | 373,694 | 374,606 | 77,496 | 77,496 | 75,728.53 |

Run directory:

```text
ROUND4/research/outputs/strategy_runs/r4_three_portal_candidates_20260427_192330
```

Official feedback parse:

```text
ROUND4/research/outputs/official_feedback
```

## Portal Feedback

| Submission | Strategy | Official | Trades |
|---|---|---:|---:|
| `522830 (rohan)` | `round4_candidate_1_522830_base.py` | 75,988.86 | 624 |
| `524123 (kush)` | `round4_candidate_1_522830_base.py` | 75,988.86 | 624 |
| `524290 (kush)` | `round4_candidate_2_option9_hydrofairoff.py` | 75,728.53 | 682 |
| `524413 (kush)` | `round4_candidate_3_option9_nohydro.py` | 75,728.53 | 682 |

The tuned candidates failed official despite strong local and official-window backtests. Do not start the full iterative loop until the red flags below are handled.

## Red Flags Before Full Loop

### Red Flag 1: Official-window backtest is not trustworthy yet

The `Window Kevin`/`Window Xeeshan` table reproduced the baseline headline, but the fill internals are not aligned with official fills. Trying alternate `match-trades` modes did not fix the ranking problem:

| Strategy | Match Trades | Kevin | Xeeshan |
|---|---|---:|---:|
| `round4_candidate_1_522830_base.py` | `none` | 75,425 | 75,425 |
| `round4_candidate_1_522830_base.py` | `worse` | 75,353 | 75,353 |
| `round4_candidate_1_522830_base.py` | `all` | 76,040 | 76,040 |
| `round4_candidate_2_option9_hydrofairoff.py` | `none` | 76,928 | 76,928 |
| `round4_candidate_2_option9_hydrofairoff.py` | `worse` | 76,916 | 76,916 |
| `round4_candidate_2_option9_hydrofairoff.py` | `all` | 77,496 | 77,496 |

All three replay modes liked candidate 2, while official did not. For candidate 2:

| Source | VEV_4000 sell qty | VEV_4000 PnL | Total |
|---|---:|---:|---:|
| Official `524290` | 247 | 7,844.84 | 75,728.53 |
| Kevin window replay | 595 | 9,371.50 | 77,496 |

The replay is effectively using too much fill information and overstates the value of the smaller option clip. This created a false positive.

Immediate fix:

- Build an official-calibrated replay mode or scoring adjustment.
- Treat portal result as truth and local window score as diagnostic only.
- Inspect whether `match-trades=worse`, `all`, or a custom filter best predicts official across known uploads.

### Red Flag 2: VEV_4000 position change erased the expected gain

Candidate 2 and 3 lowered `OPTION_SIZE` from 20 to 9. Officially, that left the strategy less short `VEV_4000`:

| Strategy | Official VEV_4000 position | Official VEV_4000 PnL |
|---|---:|---:|
| Baseline | -300 | 9,382.41 |
| Candidate 2/3 | -247 | 7,844.84 |

The tuned candidates improved several products slightly, especially `VEV_5100`, but the `VEV_4000` loss alone was about -1,538 versus baseline and dominated the result.

Immediate fix:

- Do not globally reduce voucher size.
- Keep aggressive/max-short behavior for `VEV_4000`.
- Retest smaller clip sizing only for the middle voucher strikes where it helped.

### Red Flag 3: Candidate 2 and 3 produced identical official fills

Candidate 2 kept Hydrogel passive Mark logic while candidate 3 removed all Hydrogel Mark logic. Official results and trade histories were identical:

```text
candidate 2 official = 75,728.53
candidate 3 official = 75,728.53
```

That means the Hydrogel Mark toggle did not actually create differentiated live behavior in this window. Hydrogel conclusions from this pair are weak.

Immediate fix:

- Stop treating Hydrogel Mark fair/passive toggles as a validated edge.
- Use explicit official-fill comparisons before accepting Hydrogel changes.
- Prioritize voucher execution and VEV_4000 behavior first.

## What Converged

The highest ROI improvement was voucher execution sizing. The existing strategy's `OPTION_SIZE = 20` was too aggressive for the Round 4 official-window replay. The sweep showed a clean peak around 9-10 units:

| Variant | Window Kevin | Window Xeeshan |
|---|---:|---:|
| `OPTION_SIZE = 6` | 75,617 | 75,617 |
| `OPTION_SIZE = 8` | 76,854 | 76,854 |
| `OPTION_SIZE = 9` | 77,414 | 77,414 |
| `OPTION_SIZE = 10` | 77,320 | 77,320 |
| `OPTION_SIZE = 12` | 76,922 | 76,922 |
| `OPTION_SIZE = 14` | 76,690 | 76,690 |
| `OPTION_SIZE = 18` | 76,292 | 76,292 |
| `OPTION_SIZE = 20` baseline | 76,040 | 76,040 |

Hydrogel Mark fair-value adjustment was the second converged improvement. With `OPTION_SIZE = 9`, disabling Hydrogel Mark fair lifted the window result from 77,414 to 77,496. Removing Hydrogel passive Mark quoting produced the same official-window score, but changed full-history engine behavior slightly:

| Variant | Full Kevin | Full Xeeshan | Window Kevin | Window Xeeshan |
|---|---:|---:|---:|---:|
| `OPTION_SIZE = 9`, Hydro fair off | 373,294 | 375,070 | 77,496 | 77,496 |
| `OPTION_SIZE = 9`, all Hydro Mark off | 373,694 | 374,606 | 77,496 | 77,496 |

## What Did Not Work

Stronger Mark alpha did not help. Raising `VELVET_MARK_FAIR_WEIGHT` or adding `OPTION_MARK_SPOT_WEIGHT` reduced the official-window replay sharply. The Mark IDs are useful for diagnostics, but the current strategy should not push them harder until official post-upload trade data confirms a cleaner Mark edge.

Removing whole voucher regions was bad. Mid-voucher-only and lower/mid-voucher-only variants dropped into the 53k-57k official-window range. The baseline needs the full voucher surface, especially the deep and high strikes, even when individual Black-Scholes marks look noisy.

Conservative VFE sizing was not useful in the optimized family. The official-window score fell to roughly 75.6k when VFE relative trades were made smaller and stricter.

## Current Upload Guidance

Do not submit either tuned candidate again unchanged. The known official anchor remains `round4_candidate_1_522830_base.py` at 75,988.86.

The next candidate should be a targeted repair, not a broad new Mark experiment:

1. Restore or force `VEV_4000` max-short behavior.
2. Keep reduced option sizing only where official product attribution says it helped.
3. Recalibrate the window replay before trusting another local +1k result.
