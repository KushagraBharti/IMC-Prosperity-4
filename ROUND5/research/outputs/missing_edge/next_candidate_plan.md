# Next Candidate Plan

Do not build another low-ceiling z-score batch. The next candidates should directly target the newly found high-ceiling mechanisms.

1. `ROBOT_DISHES` reversal-liquidity candidate. Signal: 10-tick past move reversal. Entry: after an extreme 10-tick move, quote 10-lot liquidity on the reversal side rather than blindly crossing. Exit: flatten/flip when the 10-tick move normalizes or reverses. This is the only tested signal with 100k+ official-window scale in the full-fill simulation.

2. Exact `PEBBLES` synthetic-fair-value candidate. Signal: current product deviation from online five-product synthetic fair value, not rolling single-product z-score. Entry: full-size passive quotes when residual is beyond spread-adjusted threshold. Exit: residual convergence or inventory pressure. Trade all five PEBBLES if the fair value ranks them clearly.

3. `MICROCHIP` formula candidate. Start with `MICROCHIP_SQUARE`, `RECTANGLE`, and `TRIANGLE`. Build shape-family fair values and only trade large residuals. The ceiling is huge, but current simple signals do not justify a submission yet.

4. Name-curve fair-value candidate. Use semantic encodings for `SLEEP_POD`, `PANEL`, `UV_VISOR`, and `PEBBLES`. Trade deviations from the category curve with full size only when residual reversion appears online.

5. Fair-value market-making candidate. Combine the best formula categories and quote 10-lot passive orders around synthetic fair value. This is the most leaderboard-like structure: many fills, low drawdown, high recovery factor.

Old ideas to abandon as primary paths: broad nested survivor basket, generic ROBOT microstructure, Snackpack relative factor, broad diversified blend, single-product PEBBLES as final answer, and raw full-history screens. They do not explain 100k+.

Immediate build order if asked to create new candidates: ROBOT_DISHES reversal-liquidity first, exact PEBBLES basket second, MICROCHIP formula third.
