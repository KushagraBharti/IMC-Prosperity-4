# Candidate 10 Notes

Aggressive thesis: a stricter `PEBBLES_XL` variant may keep most official-window upside while cutting the worst low-conviction trades from Candidate 6.

Build source: alternative Candidate 6 / Candidate 9 `PEBBLES_XL` branch.

Products traded: `PEBBLES_XL` only.

Why more aggressive than 1-5: still uses 5-10 lot orders and full-limit inventory, but waits for stronger long/fast z-score agreement.

Position-limit use: can go to full +/-10; exits stale inventory at +/-5.

Why not hardcoded/overfit: uses rolling long z-score, fast z-score, recent move, and book imbalance; no day or timestamp rules.

Expected upside: cleaner single-product candidate with stronger official-window replay than Candidate 6 but weaker full-history score.

Expected failure mode: narrower trigger set can miss profitable fills or still lose if `PEBBLES_XL` enters a trending regime.

Promotable if: official result beats Candidate 6 without showing worse fill quality or terminal inventory.
