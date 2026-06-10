# Candidate 1 Notes

Edge hypothesis: `PEBBLES` products share a strong category factor; dynamic normalized residuals around that factor should mean-revert.

Products/categories traded: `PEBBLES_XS`, `PEBBLES_S`, `PEBBLES_M`, `PEBBLES_L`, `PEBBLES_XL`.

Hidden robustness rationale: uses online anchors and dynamic residual statistics instead of fixed fitted coefficients. Research showed Pebbles residuals are stationary and structurally linked across leave-one-day fits.

Inventory controls: hard limit 10, small order sizes, inventory relief near +/-7, stronger thresholds for less-favored Pebbles products.

Execution style: mostly passive inside-spread quotes in the residual reversion direction; no heavy taker reliance.

Likely failure modes: if hidden Pebbles relationship changes, if passive fills are sparse, or if residual signs continue to be mixed at short horizons.

Overfit risks: product set is category-specific but structurally justified. No timestamp/day/window hardcoding.
