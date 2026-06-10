# Candidate 12 Notes

Aggressive thesis: all five `PEBBLES` products follow an exact current cross-product synthetic fair value. Trade deviations from the online fair value rather than single-product rolling z-scores.

Build source: new high-ceiling PEBBLES candidate from missing-edge formula research.

Products traded: `PEBBLES_XS`, `PEBBLES_S`, `PEBBLES_M`, `PEBBLES_L`, `PEBBLES_XL`.

Online synthetic fair-value formula: assign size coordinates `XS=1, S=2, M=3, L=4, XL=5`. At each timestamp and for each target product, fit a linear price-vs-size line using the other four current mids only, then predict the target fair value. Residual is current mid minus predicted fair. This uses only current observable data and no fixed trained coefficients.

Position use: passive quotes scale to full 10-lot when fair-value edge is large relative to rolling residual noise.

Execution style: primarily passive inside-spread quotes; inventory-skewed fair value discourages adding to crowded inventory.

Not hardcoded/overfit: uses stable product-name size ordering, not future coefficients or window-specific constants.

Expected upside: should capture much more of the PEBBLES category ceiling than prior single-product or rolling-anchor candidates.

Expected failure mode: exact relation exists in mids but does not translate into fills, or residuals persist while inventory sits at limit.

Promotable if: portal-window replay and official logs show frequent favorable PEBBLES fills and manageable inventory.
