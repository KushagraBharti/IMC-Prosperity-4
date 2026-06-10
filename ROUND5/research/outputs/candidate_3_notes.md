# Candidate 3 Notes

Edge hypothesis: the cost-stressed research grid found a concentrated subset of signals that stayed positive after spread-cost penalties.

Products/categories traded: `PEBBLES_XL`, `ROBOT_LAUNDRY`, `PEBBLES_L`, `OXYGEN_SHAKE_CHOCOLATE`, `PANEL_1X4`.

Hidden robustness rationale: uses only a small subset of cost-stressed directions and caps participation. It deliberately tests whether the high-conviction stressed-screen products survive actual backtesting.

Inventory controls: hard limit 10, product-specific small max sizes, exits when stale inventory exceeds +/-6.

Execution style: primarily passive; limited taker action only for strong signals and acceptable spreads.

Likely failure modes: `PEBBLES_XL` and `PANEL_1X4` were flagged for parameter-selection risk; this candidate may be fragile if the cost-stressed screen overfit public data.

Overfit risks: higher than Candidates 1 and 2 because it directly tests the cost-stressed grid. No exact timestamp or day hardcoding.
