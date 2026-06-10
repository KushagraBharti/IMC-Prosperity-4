# Candidate 8 Notes

Aggressive thesis: isolate the Candidate 4 ROBOT idea by dropping Snackpack dilution and pushing `ROBOT_DISHES`/`ROBOT_IRONING` harder.

Build source: concentrated Candidate 4 repair.

Products traded: `ROBOT_DISHES`, `ROBOT_IRONING`.

Why more aggressive than 1-5: larger order sizes than Candidate 4 and no diversification into weak Snackpack legs.

Position-limit use: allows repeated inventory near +/-10 when microstructure signal persists.

Why not hardcoded/overfit: uses only live order-book imbalance, microprice, and rolling trend. No day/window constants.

Expected upside: official Candidate 4 made most of its money on these two products, so this tests whether removing Snackpack increases portal transfer.

Expected failure mode: full-history ROBOT behavior is very poor; this is an official-window/execution hypothesis, not a robust full-history branch.

Promotable if: official portal result beats Candidate 4 and confirms ROBOT-only transfer.
