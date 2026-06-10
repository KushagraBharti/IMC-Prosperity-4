# Candidate 16-20 Recommendation

## Scores

| Strategy | Kevin Full | Xeeshan Full | Portal Window Kevin | Portal Window Xeeshan | Official Portal Score |
|---|---:|---:|---:|---:|---:|
| `round5_candidate_16.py` | 118231 | 117875 | 19935 | 19935 | pending |
| `round5_candidate_17.py` | 41966 | 41966 | 9879 | 9879 | pending |
| `round5_candidate_18.py` | -30437 | -30437 | 1448 | 1448 | pending |
| `round5_candidate_19.py` | -16762 | -16762 | -14924 | -14924 | pending |
| `round5_candidate_20.py` | 22212 | 22193 | 17753 | 17753 | pending |

## Interpretation

`round5_candidate_16.py` is the clear winner of this sprint. It improves candidate 13 from about 101k/18.5k to about 118k/19.9k while preserving Kevin/Xeeshan agreement. This is the current best local branch.

`round5_candidate_17.py` is a useful broad-scanner test, but it does not beat the pure PEBBLES branch. It supports the all-50 modeling architecture, not a broad trading conclusion.

`round5_candidate_18.py` confirms MICROCHIP is not solved. `MICROCHIP_SQUARE` remains high-ceiling, but this shape/reversal implementation is not executable enough.

`round5_candidate_19.py` should be rejected. SLEEP/PANEL/UV name-curve structure did not survive as a standalone tradable branch.

`round5_candidate_20.py` is interesting but not better than candidate 16 or candidate 13. The non-PEBBLES additions preserve much of the portal-window behavior but damage full-history robustness.

## Submit / Promote

Submit to the official portal in this order if slots are available:

1. `round5_candidate_16.py`
2. `round5_candidate_20.py` as a combined-edge probe
3. `round5_candidate_17.py` only if testing broad scanner transfer is valuable

If starting the iterative loop after this sprint, promote:

1. `round5_candidate_16.py` as the primary refined PEBBLES market-making branch.
2. `round5_candidate_12.py` as the cleaner all-PEBBLES fair-value control branch.
3. `round5_candidate_17.py` as the diversified all-50 modeled scanner branch.

Keep `round5_candidate_13.py` as the benchmark reference, but candidate 16 supersedes it for active promotion unless official portal results disagree.
