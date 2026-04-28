# Round 4 Commodity Edge Diagnosis

This is the first official-log-backed commodity breakdown after the 522830 baseline and the two option-size variants.

Primary data:

```text
ROUND4/research/outputs/official_plateau
ROUND4/research/outputs/official_feedback
```

## Portfolio-Level Diagnosis

The official charts are accurately showing a structural plateau.

For the baseline official run:

- Timestamp 40,000 total PnL: 55,018.26.
- Timestamp 41,000 total PnL: 70,299.98.
- Final total PnL: 75,988.86.
- Max total PnL: 79,601.79 at timestamp 85,200.
- Final giveback from max: about 3,613.

The biggest post-40k jump is 40,000 to 45,000. After that, most of the book is already at limits, and total PnL largely ranges between the high 60k and high 70k area.

The key structural issue:

```text
The strategy has an opening/early-session edge, but not a strong second-phase edge.
```

By 45,000 the baseline is already near static:

```text
VEV_4000 = -300
VEV_5200 = -300
VEV_5300 = -300
VEV_5400 = -300
VEV_5500 = -300
VEV_5000 = +289
VEV_5100 = +300
```

After 40,000, the baseline has no own trades in `VEV_4000`, `VEV_5200`, `VEV_5300`, `VEV_5400`, or `VEV_5500`. Those are inventory holds, not active late-session alpha.

## Product Breakdown

| Product | Final PnL | Post-40k PnL | Final Pos | First Diagnosis |
|---|---:|---:|---:|---|
| `HYDROGEL_PACK` | 232.25 | -196.06 | 31 | Severe underperformer. Low trade count, low inventory use, no clear monetized edge. |
| `VELVETFRUIT_EXTRACT` | 10,005.50 | 3,365.50 | 200 | Real core contributor. Stronger than Hydrogel, but still possibly under-optimized after the flip from short to long. |
| `VEV_4000` | 9,382.41 | 1,903.69 | -300 | Core early short edge. Must stay max-short or near max-short; reducing global option size broke this. |
| `VEV_4500` | 9,892.47 | 1,960.75 | -282 | Core contributor, mostly early short edge. Slight post-40k position adjustment. |
| `VEV_5000` | 13,740.82 | 4,336.72 | 300 | Core active product. Starts short, flips long, keeps trading after 40k. Needs deeper regime/exit study. |
| `VEV_5100` | 15,111.10 | 6,309.70 | 76 | Best product by final PnL and post-40k contribution. Active late-session edge exists here. |
| `VEV_5200` | 8,866.20 | 1,703.45 | -300 | Core early short/static hold. No post-40k trading. |
| `VEV_5300` | 5,411.96 | 927.29 | -300 | Secondary static short. Useful but not active. |
| `VEV_5400` | 2,383.71 | 484.09 | -300 | Small static short. Likely capacity-limited and lower priority. |
| `VEV_5500` | 962.45 | 175.48 | -300 | Very low contribution despite max short. Questionable unless it comes for free with surface logic. |
| `VEV_6000` | 0.00 | 0.00 | 0 | Dead in official fills. Ignore unless there is genuine free optionality. |
| `VEV_6500` | 0.00 | 0.00 | 0 | Dead in official fills. Ignore unless there is genuine free optionality. |

## Hydrogel Red Flag

Hydrogel is the clearest non-option underperformer.

Official baseline:

- Final PnL: 232.25.
- Post-40k PnL: -196.06.
- Own trades before 40k: 16.
- Own trades after 40k: 10.
- Final position: 31 out of 200.
- It never gets close to the position limit.

The current Hydrogel code is too timid or too poorly aligned with the actual source of edge. Mark diagnostics show `Mark 14` and `Mark 38` have some signal at 5k horizons, but the live strategy did not turn that into meaningful PnL.

Hydrogel next experiments:

1. Baseline no-Hydrogel strategy to measure whether it is harmless or net distracting.
2. Pure Hydrogel market-making branch with controlled inventory skew.
3. Mark14/Mark38 follow/fade branch using threshold/size changes, not direct fair overrides first.
4. Late-session Hydrogel branch, because Hydrogel loses money after 40k in the baseline.

## VFE/Voucher Complex

The visible edge is mostly the VFE/voucher repricing from timestamp 0 to 41k.

Market mid changes from 0 to 40k:

| Product | Mid 0 | Mid 40k | Change |
|---|---:|---:|---:|
| `VELVETFRUIT_EXTRACT` | 5295.5 | 5260.5 | -35.0 |
| `VEV_4000` | 1296.0 | 1260.5 | -35.5 |
| `VEV_4500` | 795.5 | 760.0 | -35.5 |
| `VEV_5000` | 296.5 | 262.0 | -34.5 |
| `VEV_5100` | 201.5 | 170.0 | -31.5 |
| `VEV_5200` | 119.5 | 94.5 | -25.0 |
| `VEV_5300` | 58.0 | 42.0 | -16.0 |
| `VEV_5400` | 20.5 | 13.5 | -7.0 |
| `VEV_5500` | 7.0 | 4.5 | -2.5 |

The baseline is heavily short most vouchers during this decline, which explains the early PnL ramp.

The issue is not that the opening edge is weak. The issue is that the strategy becomes mostly static after expressing it.

Voucher next experiments:

1. Restore aggressive `VEV_4000` sizing while keeping smaller clip logic only for selected active strikes.
2. Study `VEV_5000` and `VEV_5100` as separate active trading products; they are not behaving like the static short voucher set.
3. Build a second-phase rule after 40k or after first 70k crossing: rebalance, flatten, or switch edge thresholds based on trend/surface state.
4. Test a late-session stop/lock branch around the 83k to 86k surge. Official baseline peaked near 85,200 and gave back about 3,613 by final.
5. Do not rely on local backtest ranking for these changes until official fill alignment is understood.

## Current Hypothesis

Round 4 may require two different strategies inside one algorithm:

1. **Opening repricing capture:** aggressively take the known VFE/voucher surface dislocation and fill the high-confidence static shorts/longs.
2. **Post-repricing management:** once the surface move is mostly harvested, stop behaving like the same opening strategy. Manage inventory, exit weak positions, and focus only on products with active late-session edge, especially `VEV_5000`, `VEV_5100`, and maybe VFE.

This is why a broad parameter sweep is dangerous right now. We need product-specific strategy roles before tuning.
