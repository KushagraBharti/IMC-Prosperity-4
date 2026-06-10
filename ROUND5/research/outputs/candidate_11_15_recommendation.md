# Candidate 11-15 Recommendation

## Scores

| Strategy | Kevin Full | Xeeshan Full | Portal Window Kevin | Portal Window Xeeshan | Official Portal Score |
|---|---:|---:|---:|---:|---:|
| `round5_candidate_11.py` | 9028 | 9028 | -631 | -631 | pending |
| `round5_candidate_12.py` | 81253 | 81253 | 10202 | 10202 | pending |
| `round5_candidate_13.py` | 101009 | 100874 | 18470 | 18470 | pending |
| `round5_candidate_14.py` | -29302 | -29302 | 1448 | 1448 | pending |
| `round5_candidate_15.py` | 45193 | 45193 | 3589 | 3589 | pending |

## Submission Priority

Submit `round5_candidate_13.py` first. It is the strongest high-ceiling path in local evidence: exact PEBBLES online fair-value market making, 101k full Kevin, 100.9k full Xeeshan, and 18.5k official-window replay.

Submit `round5_candidate_12.py` second. It is a cleaner, slightly less aggressive all-PEBBLES fair-value arbitrage with 81.3k full and 10.2k official-window replay. If candidate 13 overtrades officially, candidate 12 is the lower-turnover control.

Submit `round5_candidate_15.py` only after 12/13 if extra portal slots are available. It is positive full-history but the combined category additions dilute the PEBBLES edge on the official window.

Do not prioritize `round5_candidate_11.py` yet. The ROBOT_DISHES reversal thesis remains high-ceiling in research, but this passive implementation did not transfer in official-window replay. It needs fill/order-log diagnosis before submission.

Do not prioritize `round5_candidate_14.py` yet. MICROCHIP has huge oracle capacity, but this simple shape-curve implementation is not enough: negative full-history and low portal-window replay.

## 100k Path Assessment

Candidate 13 is the first built strategy in this phase that reaches 100k-scale local full-history PnL while also improving official-window replay over candidates 1-10. That is a plausible path, not proof of a 100k official score. The remaining gap to leaderboard scale likely requires either better passive fill capture from the exact PEBBLES formula or a separate solved MICROCHIP/ROBOT_DISHES execution mechanism.

Next best work after official results: analyze candidate 13 product-level official fills and inventory paths, then amplify only the profitable PEBBLES legs. If official 13 underperforms replay, the issue is execution/fill translation, not broad edge discovery.
