# Round 4 Product-Specific Attack Report

Generated after the first plateau and commodity red-flag pass.

## Objective

Do not run broad sweeps yet. The current work targets three named problems:

1. Repair `VEV_4000`, because the global option-size reduction made official `VEV_4000` worse.
2. Isolate `VEV_5000` / `VEV_5100`, because they are the only vouchers with meaningful post-40k active trading.
3. Diagnose Hydrogel, because official Hydrogel PnL is almost flat and post-40k negative.

## Stable Product-Attack Candidates

| Strategy | Full Kevin | Full Xeeshan | Window Kevin | Window Xeeshan | Official |
|---|---:|---:|---:|---:|---:|
| `round4_candidate_1_522830_base.py` | 363,494 | 364,966 | 76,040 | 76,040 | 75,988.86 |
| `round4_candidate_4_vev4000_repair_mid9_hydrofairoff.py` | 377,844 | 379,622 | 76,936 | 76,936 | pending |
| `round4_candidate_5_static_exit_86600.py` | 377,142 | 378,920 | 77,752 | 77,752 | pending |
| `round4_candidate_6_hydro_more_mid9.py` | 382,820 | 384,080 | 76,660 | 76,660 | pending |

Run directory:

```text
ROUND4/research/outputs/strategy_runs/r4_product_attack_candidates_20260427_201848
```

## Candidate 4: VEV_4000 Repair

File:

```text
ROUND4/strategies/round4_candidate_4_vev4000_repair_mid9_hydrofairoff.py
```

Changes:

- Keeps baseline `OPTION_SIZE = 20` for the static voucher shorts.
- Uses smaller size `9` only for `VEV_5000` and `VEV_5100`.
- Disables Hydrogel Mark fair adjustment, matching the better Hydrogel behavior seen in candidate 2/3 official attribution.

Why this exists:

- Candidate 2/3 official lost mostly because `VEV_4000` ended only `-247` instead of baseline `-300`.
- Candidate 4 should preserve the `VEV_5100` improvement from smaller active sizing while restoring `VEV_4000` max-short behavior.

Official heuristic:

```text
candidate 2 official                     = 75,728.53
candidate 2 VEV_4000 deficit vs baseline =  1,537.56
rough repaired estimate                  = 77,266.09
```

This is not a guaranteed score, but it is the cleanest red-flag repair.

## Candidate 5: Static-Short Exit At 86.6k

File:

```text
ROUND4/strategies/round4_candidate_5_static_exit_86600.py
```

Changes:

- Starts from candidate 4.
- At timestamp `86,600`, exits the higher static shorts:

```text
VEV_5200
VEV_5300
VEV_5400
VEV_5500
```

Why this exists:

- Official baseline/candidate data show these products peak around timestamp `86,600`, then give back:

| Product | Candidate 2 Max PnL | Final PnL | Giveback |
|---|---:|---:|---:|
| `VEV_5200` | 10,521.07 | 8,949.20 | -1,571.88 |
| `VEV_5300` | 6,386.27 | 5,460.96 | -925.31 |
| `VEV_5400` | 2,787.45 | 2,412.71 | -374.74 |
| `VEV_5500` | 1,120.39 | 998.45 | -121.94 |

Local window improves from `76,936` to `77,752`, but full historical score falls slightly. This is a high-official-specific, higher-overfit-risk candidate.

## Candidate 6: Hydrogel-Heavy Diagnostic

File:

```text
ROUND4/strategies/round4_candidate_6_hydro_more_mid9.py
```

Changes:

- Starts from candidate 4's voucher repair.
- Makes Hydrogel more aggressive:
  - lower take edge,
  - tighter maker edge,
  - larger quote/take size,
  - larger passive Mark size,
  - Hydrogel Mark fair override disabled.

Why this exists:

- Hydrogel is almost flat officially, but full historical backtests like more aggressive Hydrogel behavior.
- This is diagnostic. It has the highest full backtest score, but weaker official-window score than candidate 4.

Interpretation:

- If candidate 6 improves official, Hydrogel had unused capacity.
- If it does not, Hydrogel historical edge is not portable to this official path.

## Rejected Focused Experiments

| Experiment | Result | Reason |
|---|---:|---|
| Global `OPTION_SIZE = 9` | official 75,728.53 | Fixed `VEV_5100`, broke `VEV_4000`. |
| Exit `VEV_5000/5100` at 85.2k | window 73,998 | Active middle strikes still add value after this; blunt exit is bad. |
| Exit `VEV_5000/5100` at 90k | window 73,914 | Same issue. |
| Exit `VEV_4000/4500` at 43k | window 73,700 | Closing low-strike shorts is too expensive / forfeits too much. |
| No Hydrogel | full Kevin 338,480 | Hydrogel removal hurts historical replay badly. |
| Hydrogel flatten after 40k | full Kevin 335,528 | Worse than no Hydrogel. |

## Current Priority

Portal-test order:

1. `round4_candidate_4_vev4000_repair_mid9_hydrofairoff.py`
2. `round4_candidate_5_static_exit_86600.py`
3. `round4_candidate_6_hydro_more_mid9.py`

Candidate 4 is the clean repair. Candidate 5 tests the plateau/giveback thesis. Candidate 6 tests whether Hydrogel has hidden official capacity.
