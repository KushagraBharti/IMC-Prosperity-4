# Round 3 Iterative Results

## Current Best Files

| Branch | File | Source | Current role |
|---|---|---|---|
| Iterative 1 | `ROUND3/strategies/round3_iterative_1.py` | `official_443820_rohan.py` | Official-style branch with stronger VFE sizing |
| Iterative 2 | `ROUND3/strategies/round3_iterative_2.py` | `round3_combined_aggressive.py` | Best current branch; stronger VFE plus cleaner voucher set |

## Final Scores

| Strategy | Kevin full | Xeeshan full | Portal-window Kevin | Portal-window Xeeshan |
|---|---:|---:|---:|---:|
| `official_443820_rohan.py` baseline | 294,010 | 293,376 | 20,899 | 20,984 |
| `round3_combined_aggressive.py` baseline | 428,756 | 429,808 | 13,152 | 13,337 |
| `round3_iterative_1.py` final | 317,270 | 317,656 | 29,384 | 29,414 |
| `round3_iterative_2.py` final | 334,534 | 334,922 | 29,720 | 29,750 |

Portal-window source:
`outputs/official-windows/round3_day2_0_99900_from_442527`

Final deep diagnostics:
`outputs/diagnostics/round3_iterative_final_deep`

## Accepted Changes

| Change | Branches | Reason |
|---|---|---|
| Use dynamic Hydrogel fair from official-style branch in Iterative 2 | Iterative 2 | Fixed the original max-long Hydrogel failure on the portal window. |
| Remove option inventory and delta dampening in Iterative 2 | Iterative 2 | Restored profitable 5000/5100 voucher rotation. |
| Use `VEV_5300` and drop `VEV_5500` | Iterative 2 | 5300 had realized edge; 5500 was model-rich but lost in replay. |
| Aggressive but selective VFE sizing | Both | Deep-voucher-implied VFE signal showed strong directional edge; higher size with better threshold produced large gains. |
| VFE take edge `5.0` | Both | Better than `3.5`, `4.0`, `4.5`, and `5.5` on portal-window proxy, and improved full-data totals. |
| VFE skew `0.005` | Both | Captures more signal persistence while retaining minimal inventory control. |
| Remove `VEV_5400` from Iterative 2 | Iterative 2 | Small portal improvement and removes a noisy weak leg with minimal full-data cost. |

## Rejected Changes

| Change | Result |
|---|---|
| Add `VEV_5500` | Portal dropped by about 150; rejected despite apparent BS richness. |
| Brute-force VFE max aggression (`edge=2.0`, larger size, lower skew) | Portal dropped materially; rejected. |
| Option clip size `100` | No portal impact; reverted to smaller size. |
| Static Hydrogel overlay | Portal dropped by more than 10k; rejected. |
| VFE passive size `36` | No portal impact; reverted. |
| VFE skew `0.0` | Tiny portal gain but weaker full-data robustness than `0.005`; rejected. |
| VFE take edge `5.5` | Worse than `5.0`; rejected. |

## Main Interpretation

The largest robust edge found is VFE selectivity. The initial instinct was to loosen VFE execution, but diagnostics showed the profitable regime is more selective: larger size is useful only when the deep-voucher-implied fair clears the book by roughly 5 XIRECs.

The Hydrogel edge is regime-sensitive. Static fair models score well on full public data but fail badly on the official-style portal window. The dynamic official-style Hydrogel engine is safer for portal alignment.

For vouchers, realized replay matters more than raw Black-Scholes residuals. 5500 and 5400 can look rich on the surface table, but 5500 loses in replay and 5400 is too small/noisy for Iterative 2.
