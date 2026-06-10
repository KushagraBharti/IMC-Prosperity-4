# Candidate 17 Notes

Thesis: test the all-50 scanner architecture without repeating candidate 2's broad basket mistake. The strategy models semantic/fair-value curves across PEBBLES, SLEEP, MICROCHIP, PANEL, and UV, but trades only scanner-approved products.

Products traded: all PEBBLES plus `MICROCHIP_SQUARE` and `UV_VISOR_AMBER` when current fair-value edge clears thresholds. Other modeled products are anchors.

Evidence: all-50 table marked `PEBBLES_XL`, `PEBBLES_M`, `MICROCHIP_SQUARE`, and `UV_VISOR_AMBER` as tradeable; many other high-oracle products were excluded for one-day or block-fragile signals.

Execution: passive edge-gated quotes, with a cap on active opportunities.

Failure mode: non-PEBBLES additions may dilute the clean PEBBLES branch, or semantic curves may not translate into fills.
