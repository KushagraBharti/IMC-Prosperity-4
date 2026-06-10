# Candidate 13 Notes

Aggressive thesis: the same exact `PEBBLES` synthetic fair value should be traded as market making, not only residual entry. Quote whenever bid or ask is favorable versus leave-one fair value.

Build source: aggressive PEBBLES market-making version of candidate 12.

Products traded: all five `PEBBLES`.

Fair-value formula: same online leave-one current-size linear formula as candidate 12: each product's fair value is predicted from the other four current PEBBLES mids using size coordinates `1..5`.

Why more aggressive: lower edge threshold, more frequent inside-spread quoting, full-size orders when bid/fair or ask/fair edge is large, and limited crossing only when fair value clears the visible spread by a meaningful margin.

Inventory controls: fair value is skewed against current inventory, pushing exits before deeper accumulation.

Not hardcoded/overfit: current cross-section only; no day-specific coefficients or files.

Expected upside: higher fill count and better leaderboard-like recovery profile than candidate 12 if the PEBBLES formula is executable.

Expected failure mode: overtrading residual noise or adverse selection at inside-spread quote prices.

Promotable if: PEBBLES product-level PnL is positive across multiple products, even if full-history score is noisy.
