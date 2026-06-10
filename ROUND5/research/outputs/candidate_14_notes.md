# Candidate 14 Notes

Aggressive thesis: `MICROCHIP_SQUARE`, `MICROCHIP_RECTANGLE`, and `MICROCHIP_TRIANGLE` have enormous oracle capacity. Use `CIRCLE` and `OVAL` as current anchors to form a shape-curve fair value.

Build source: new MICROCHIP formula/residual candidate from missing-edge research.

Products traded: `MICROCHIP_TRIANGLE`, `MICROCHIP_SQUARE`, `MICROCHIP_RECTANGLE`; `MICROCHIP_OVAL` and `MICROCHIP_CIRCLE` are anchors.

Formula: encode shape coordinates as `TRIANGLE=3`, `SQUARE=4`, `RECTANGLE=4.6`, `OVAL=5.5`, `CIRCLE=6`. At each timestamp, fit a leave-one current linear shape curve and trade only large residuals in the target geometric products.

Position use: full 10-lot when shape residual edge is large relative to rolling residual volatility.

Execution style: passive inside-spread quotes, with inventory-skewed fair value and no broad MICROCHIP basket.

Not hardcoded/overfit: coefficients are estimated online from current observable mids; static coordinates come from product names only.

Expected upside: high if the large MICROCHIP oracle ceiling is caused by a hidden shape-curve fair value.

Expected failure mode: shape ordering is too crude, or oracle ceiling is directional rather than formula-residual.

Promotable if: `MICROCHIP_SQUARE` or the shape trio generates strong official-window PnL without large stuck inventory.
