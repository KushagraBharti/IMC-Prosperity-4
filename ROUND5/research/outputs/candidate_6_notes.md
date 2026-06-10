# Candidate 6 Notes

Aggressive thesis: `PEBBLES_XL` is the cleanest official-positive leg and also survives full Kevin/Xeeshan after pruning the weaker products. This candidate concentrates on that one product instead of diluting the edge.

Build source: repaired from Candidate 3/9 evidence and Candidate 5 official product PnL.

Products traded: `PEBBLES_XL` only.

Why more aggressive than 1-5: uses full-size 5-10 lot orders, allows spread crossing on strong normalized z-score dislocations, and is willing to sit at the full +/-10 limit.

Position-limit use: targets large inventory when rolling mean-reversion evidence is strong; exits stale inventory at +/-6.

Why not hardcoded/overfit: no timestamp/day constants or fixed price levels. It uses rolling volatility, long z-score, recent move, and current book imbalance.

Expected upside: lower breadth, higher utilization on the best official-positive and full-history-positive product.

Expected failure mode: `PEBBLES_XL` mean reversion can reverse by day/regime; day 2 was a large local drawdown.

Promotable if: official portal score beats Candidate 1/4 while maintaining a cleaner full-history profile than Candidate 7/9.
