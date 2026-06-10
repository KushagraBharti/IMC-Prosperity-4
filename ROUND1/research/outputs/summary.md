# Round 1 dataset summary

## Files

- `prices_round_1_day_-1.csv`
- `prices_round_1_day_-2.csv`
- `prices_round_1_day_0.csv`
- `trades_round_1_day_-1.csv`
- `trades_round_1_day_-2.csv`
- `trades_round_1_day_0.csv`

## Product stats

| product | rows | mean mid | std mid | mean spread | corr(imbalance, next mid change) | corr(wall deviation, next mid change) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ASH_COATED_OSMIUM | 27644 | 10000.209 | 4.858 | 16.175 | 0.5867 | 0.5884 |
| INTARIAN_PEPPER_ROOT | 27688 | 11502.316 | 866.152 | 13.047 | 0.5630 | 0.5649 |

## Pepper drift check

| day | fitted slope | detrended mean | detrended std |
| --- | ---: | ---: | ---: |
| -2 | 0.001000 | 9999.994 | 2.010 |
| -1 | 0.001000 | 11000.004 | 2.221 |
| 0 | 0.001000 | 11999.990 | 2.360 |

## Trade counts

| product | trades | total qty | mean price | std price |
| --- | ---: | ---: | ---: | ---: |
| ASH_COATED_OSMIUM | 1265 | 6593 | 10000.213 | 9.398 |
| INTARIAN_PEPPER_ROOT | 1011 | 5230 | 11495.942 | 879.806 |

## Generated plots

- `mid_paths.png`
- `pepper_detrended.png`
- `spread_boxplot.png`
- `imbalance_signal.png`
- `trade_overlay.png`

## High-confidence takeaways

- ASH_COATED_OSMIUM behaves like a stable market-making product around 10,000.
- INTARIAN_PEPPER_ROOT shows a highly consistent positive linear drift of about 0.001 per timestamp plus a tight residual process.
- Top-of-book imbalance is strongly predictive for both products and should be used as a short-horizon alpha input.
- The spread is wide enough that quote placement and inventory management matter more than small fair-value estimation errors.