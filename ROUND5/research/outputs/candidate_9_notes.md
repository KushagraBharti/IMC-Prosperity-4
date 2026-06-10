# Candidate 9 Notes

Aggressive thesis: exploit the strongest official PEBBLES/PANEL upside by combining full-limit `PEBBLES_XL`, gated `PEBBLES_L`, and `PANEL_1X4` momentum.

Build source: product-pruned Candidate 3 salvage, with `ROBOT_LAUNDRY` and `OXYGEN_SHAKE_CHOCOLATE` removed.

Products traded: `PEBBLES_XL`, `PEBBLES_L`, `PANEL_1X4`.

Why more aggressive than 1-5: pushes concentrated max-size orders into the products that carried official PnL and accepts full drawdown risk instead of smoothing with broad baskets.

Position-limit use: all three products can hit full +/-10 when signals are strong.

Why not hardcoded/overfit: rolling z-score, rolling volatility, past-move momentum, and imbalance only; no timestamp, price, or portal-score constants.

Expected upside: highest local official-window replay in the second batch.

Expected failure mode: full-history loss is meaningful; `PEBBLES_L` and `PANEL_1X4` are regime-sensitive.

Promotable if: official portal score confirms the high replay result and product-level PnL is not carried by a one-off fill.
