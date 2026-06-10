# Candidate 11 Notes

Aggressive thesis: `ROBOT_DISHES` has the only discovered single-product signal with leaderboard-scale official-window capacity: a 10-tick reversal. The candidate quotes liquidity on the reversal side after a large 10-tick move.

Build source: new high-ceiling candidate from missing-edge research, loosely informed by candidate 4's ROBOT official-window transfer.

Products traded: only `ROBOT_DISHES`.

Why passive execution: the missing-edge taker simulation failed despite the full-fill reversal proxy reaching about 235k. This implies the edge is not blind spread crossing; it needs passive/inside-spread liquidity provision after displacement.

Position use: scales from 7-lot to full 10-lot when the normalized 10-tick reversal signal is strong.

Not hardcoded/overfit: no timestamps, no file reads, no future data. Uses only rolling current/past mid, spread, and top-book imbalance.

Expected upside: official-window upside is large if passive fills occur around the reversal points.

Expected failure mode: too few fills, or fills only when reversal continues against us.

Promotable if: official portal PnL materially exceeds the first two batches or product-level logs show correct directional markouts with underfilled orders.
