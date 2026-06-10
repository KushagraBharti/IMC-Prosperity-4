# Post-40k Mark Inventory Analysis

Purpose: use Marks to manage stale voucher inventory after the opening repricing has saturated positions.

## Recommended Weights

| Segment | Product | Mark | Weight | Avg Score | Events | Family |
|---|---|---|---:|---:|---:|---|
| `late` | `VEV_5200` | `Mark 22` | -0.3220 | -0.6441 | 140 | static_short |
| `late` | `VEV_5300` | `Mark 14` | 0.3230 | 0.6460 | 89 | static_short |
| `late` | `VEV_5400` | `Mark 14` | -0.3311 | -0.6623 | 30 | static_short |
| `post40` | `VEV_5200` | `Mark 22` | -0.3220 | -0.6441 | 140 | static_short |
| `post40` | `VEV_5300` | `Mark 14` | 0.3230 | 0.6460 | 89 | static_short |
| `post40` | `VEV_5400` | `Mark 14` | -0.3841 | -0.7681 | 36 | static_short |

Interpretation: positive weight means Mark buying predicts higher future voucher mid; if we are short, it is a cover signal. Negative weight means Mark buying predicts lower future voucher mid; if we are short, it is a hold/re-short signal.

Use this as a research signal, not a final production table; sparse rows still need portal validation.
