# Round 4 Official Plateau Analysis

## Submission Summary

| Submission | Strategy | Final | At 40k | Pre-40k | Post-40k | First >=70k | Max | Max TS | Drawdown |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `522830 (rohan)` | `round4_candidate_1_522830_base.py` | 75,988.86 | 55,018.26 | 55,018.26 | 20,970.60 | 41000 | 79,601.79 | 85200 | 18,007.90 |
| `524123 (kush)` | `round4_candidate_1_522830_base.py` | 75,988.86 | 55,018.26 | 55,018.26 | 20,970.60 | 41000 | 79,601.79 | 85200 | 18,007.90 |
| `524290 (kush)` | `` | 75,728.53 | 54,107.96 | 54,107.96 | 21,620.57 | 41800 | 79,277.48 | 86600 | 17,438.42 |
| `524413 (kush)` | `` | 75,728.53 | 54,107.96 | 54,107.96 | 21,620.57 | 41800 | 79,277.48 | 86600 | 17,438.42 |
| `530880` | `` | 87,114.39 | 55,761.44 | 55,761.44 | 31,352.95 | 40800 | 89,882.25 | 85200 | 20,117.07 |

## Baseline 38k-43k Transition

| Timestamp | Total | Delta 100 | Delta 500 |
|---:|---:|---:|---:|
| 38000 | 40,615.44 | -54.56 | 488.52 |
| 38500 | 48,054.05 | 3,688.52 | 7,438.62 |
| 39000 | 50,176.34 | -983.63 | 2,122.29 |
| 39500 | 56,369.20 | 2,557.86 | 6,192.86 |
| 40000 | 55,018.26 | 550.79 | -1,350.94 |
| 40500 | 60,624.85 | 3,163.92 | 5,606.59 |
| 41000 | 70,299.98 | 780.56 | 9,675.13 |
| 41500 | 67,842.55 | -1,327.71 | -2,457.43 |
| 42000 | 71,556.02 | -601.70 | 3,713.47 |
| 42500 | 72,737.86 | -77.81 | 1,181.84 |
| 43000 | 73,970.33 | 848.20 | 1,232.47 |

## Baseline Product Delta From 40k To 41k

| Product | PnL 40k | PnL 41k | Delta | Pos 40k | Pos 41k | Mid 40k | Mid 41k |
|---|---:|---:|---:|---:|---:|---:|---:|
| `HYDROGEL_PACK` | 428.31 | 543.39 | 115.08 | 19 | 19 | 10,030.00 | 10,036.00 |
| `VELVETFRUIT_EXTRACT` | 6,640.00 | 8,456.69 | 1,816.69 | -196 | -196 | 5,260.50 | 5,250.50 |
| `VEV_4000` | 7,478.72 | 10,259.31 | 2,780.59 | -300 | -300 | 1,260.50 | 1,250.50 |
| `VEV_4500` | 7,931.72 | 10,690.88 | 2,759.16 | -300 | -297 | 760.00 | 751.00 |
| `VEV_5000` | 9,404.10 | 11,699.26 | 2,295.16 | -300 | -197 | 262.00 | 253.00 |
| `VEV_5100` | 8,801.41 | 10,830.67 | 2,029.27 | -300 | -183 | 170.00 | 162.00 |
| `VEV_5200` | 7,162.75 | 8,948.55 | 1,785.80 | -300 | -300 | 94.50 | 88.50 |
| `VEV_5300` | 4,484.67 | 5,550.42 | 1,065.75 | -300 | -300 | 42.00 | 39.00 |
| `VEV_5400` | 1,899.61 | 2,360.16 | 460.55 | -300 | -300 | 13.50 | 11.50 |
| `VEV_5500` | 786.97 | 960.65 | 173.68 | -300 | -300 | 4.50 | 3.50 |
| `VEV_6000` | 0.00 | 0.00 | 0.00 | 0 | 0 | 0.50 | 0.50 |
| `VEV_6500` | 0.00 | 0.00 | 0.00 | 0 | 0 | 0.50 | 0.50 |

## Baseline Product Edge Report

| Product | PnL 40k | Final PnL | Post-40k | Pos 40k | Final Pos | Post-40k Trades | Role |
|---|---:|---:|---:|---:|---:|---:|---|
| `HYDROGEL_PACK` | 428.31 | 232.25 | -196.06 | 19 | 31 | 10 | low contribution |
| `VELVETFRUIT_EXTRACT` | 6,640.00 | 10,005.50 | 3,365.50 | -196 | 200 | 20 | core contributor |
| `VEV_4000` | 7,478.72 | 9,382.41 | 1,903.69 | -300 | -300 | 0 | core contributor |
| `VEV_4500` | 7,931.72 | 9,892.47 | 1,960.75 | -300 | -282 | 6 | core contributor |
| `VEV_5000` | 9,404.10 | 13,740.82 | 4,336.72 | -300 | 300 | 79 | core contributor |
| `VEV_5100` | 8,801.41 | 15,111.10 | 6,309.70 | -300 | 76 | 155 | core contributor |
| `VEV_5200` | 7,162.75 | 8,866.20 | 1,703.45 | -300 | -300 | 0 | core contributor |
| `VEV_5300` | 4,484.67 | 5,411.96 | 927.29 | -300 | -300 | 0 | saturated inventory hold |
| `VEV_5400` | 1,899.61 | 2,383.71 | 484.09 | -300 | -300 | 0 | saturated inventory hold |
| `VEV_5500` | 786.97 | 962.45 | 175.48 | -300 | -300 | 0 | flat / underused |
| `VEV_6000` | 0.00 | 0.00 | 0.00 | 0 | 0 | 0 | dead optionality / no realized edge |
| `VEV_6500` | 0.00 | 0.00 | 0.00 | 0 | 0 | 0 | dead optionality / no realized edge |

## Files

- `submission_plateau_summary.csv`: high-level plateau metrics.
- `checkpoint_pnl.csv`: total and product PnL at fixed timestamps.
- `product_edge_report.csv`: product-level PnL, inventory, saturation, and fills.
- `tenk_segment_pnl.csv`: PnL by 10k timestamp block.
- `post40_rolling_windows.csv`: best/worst post-40k rolling windows.
- `transition_38k_43k.csv`: exact transition around the jump into the plateau.
- `transition_product_40k_41k.csv`: product attribution for the key 40k to 41k jump.
- `position_checkpoints.csv`: position snapshots through the plateau.
- `mid_checkpoints.csv`: market mid snapshots at the same checkpoints.
