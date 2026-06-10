# Candidate 4 Notes

Edge hypothesis: selected `ROBOT` and `SNACKPACK` products have small but measurable microstructure and short/medium-horizon directional effects.

Products/categories traded: `ROBOT_DISHES`, `ROBOT_IRONING`, `SNACKPACK_VANILLA`, `SNACKPACK_RASPBERRY`, `SNACKPACK_CHOCOLATE`.

Hidden robustness rationale: uses simple order-book imbalance, microprice, and a lightweight Snackpack relative factor instead of deploying ML. This tests the microstructure direction independently from mean-reversion candidates.

Inventory controls: hard limit 10, order size 1-2, inventory relief near +/-8.

Execution style: mixed passive/aggressive; crosses only when spread is tight and microstructure signal is strong.

Likely failure modes: ML diagnostics were modest; backtester disagreement is possible if edge depends on favorable passive fills.

Overfit risks: avoids fitted model objects and exact thresholds from research. Product set is narrow and evidence-backed.
