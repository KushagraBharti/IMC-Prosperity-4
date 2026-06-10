# Candidate 15 Notes

Aggressive thesis: top leaderboard profiles look like fair-value-filtered market making across a small set of structurally modeled categories. Combine only the strongest formula/name-curve structures instead of broad baskets.

Build source: new combined fair-value market-making candidate.

Products traded: all five `PEBBLES`, `SLEEP_POD_POLYESTER`, `SLEEP_POD_COTTON`, and `MICROCHIP_SQUARE` when their category fair-value residuals rank highest.

Fair-value formulas: online leave-one linear curves by semantic coordinate: PEBBLES size, SLEEP_POD material ordinal/premium, and MICROCHIP shape coordinate. Only current/past observable mids are used.

Why high-ceiling: targets PEBBLES exact structure plus high-oracle SLEEP and MICROCHIP products, but caps active products to strongest current residuals.

Position use: up to full 10-lot per selected product when edge clears spread/noise thresholds.

Execution style: passive inside-spread fair-value market making with inventory-skewed fair values.

Not hardcoded/overfit: product-name semantic coordinates only; no file reads, timestamps, or future-fitted constants.

Expected upside: lower single-edge purity than candidates 11-13, but more paths to repeated fills if multiple category formulas transfer.

Expected failure mode: adding SLEEP/MICROCHIP residuals dilutes the exact PEBBLES edge or creates adverse selection.

Promotable if: official-window score improves while logs show the non-PEBBLES additions are net positive rather than dead weight.
