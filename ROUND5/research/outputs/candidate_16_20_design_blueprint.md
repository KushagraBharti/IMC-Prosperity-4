# Candidate 16-20 Design Blueprint

Build candidates only from products with a clear scanner role. Candidate 13 is the benchmark branch.

## Candidate 16

Improve candidate 13's PEBBLES fair-value market maker. Keep all five PEBBLES, but add residual-volatility gates and avoid crossing unless fair-value edge is large. Purpose: preserve the 100k full-history path while reducing noisy official-window overtrading.

## Candidate 17

All-50 modeled, selective scanner. Implement category-specific fair values for PEBBLES, SLEEP_POD, MICROCHIP, PANEL, UV_VISOR, and category-mean fallback for the others, but only trade products whose current edge clears scanner thresholds. Purpose: test broad edge-gated architecture without Candidate 2-style broad basket toxicity.

## Candidate 18

MICROCHIP isolated test only if submitted as a learning probe. Focus on `MICROCHIP_SQUARE`, `MICROCHIP_RECTANGLE`, and `MICROCHIP_TRIANGLE`; use CIRCLE/OVAL as anchors. The scanner does not justify blending MICROCHIP into a best branch yet.

## Candidate 19

SLEEP/PANEL semantic curve candidate. Trade only selected material/geometry residuals with high thresholds; use other category members as anchors. This tests whether name-curve structure can add non-PEBBLES PnL.

## Candidate 20

Candidate 13 plus non-toxic additions. Start from aggressive PEBBLES MM and add only scanner-approved SLEEP/PANEL/MICROCHIP legs that clear dynamic edge thresholds. This is the practical combined branch if 17 is too broad.

## Products By Role

Tradeable: `PEBBLES_XL`, `PEBBLES_M`, `PEBBLES_XS`, `UV_VISOR_AMBER`, `MICROCHIP_SQUARE`, `PEBBLES_S`, `PEBBLES_L`

Anchor-only: `PANEL_2X2`, `SLEEP_POD_NYLON`, `SLEEP_POD_POLYESTER`, `SLEEP_POD_COTTON`

Excluded: `ROBOT_DISHES`, `ROBOT_IRONING`, `PANEL_1X4`, `MICROCHIP_RECTANGLE`, `OXYGEN_SHAKE_GARLIC`, `UV_VISOR_MAGENTA`, `SLEEP_POD_LAMB_WOOL`, `TRANSLATOR_VOID_BLUE`, `GALAXY_SOUNDS_PLANETARY_RINGS`, `TRANSLATOR_ASTRO_BLACK`, `OXYGEN_SHAKE_MINT`, `PANEL_2X4`, `ROBOT_LAUNDRY`, `UV_VISOR_ORANGE`, `UV_VISOR_YELLOW`, `ROBOT_MOPPING`, `TRANSLATOR_ECLIPSE_CHARCOAL`, `GALAXY_SOUNDS_DARK_MATTER`, `MICROCHIP_OVAL`, `GALAXY_SOUNDS_SOLAR_FLAMES`, `TRANSLATOR_GRAPHITE_MIST`, `MICROCHIP_TRIANGLE`, `OXYGEN_SHAKE_CHOCOLATE`, `MICROCHIP_CIRCLE`, `SLEEP_POD_SUEDE`, `OXYGEN_SHAKE_EVENING_BREATH`, `SNACKPACK_STRAWBERRY`, `UV_VISOR_RED`, `ROBOT_VACUUMING`, `SNACKPACK_RASPBERRY`, `PANEL_4X4`, `TRANSLATOR_SPACE_GRAY`, `GALAXY_SOUNDS_BLACK_HOLES`, `SNACKPACK_PISTACHIO`, `GALAXY_SOUNDS_SOLAR_WINDS`, `PANEL_1X2`, `SNACKPACK_CHOCOLATE`, `OXYGEN_SHAKE_MORNING_BREATH`, `SNACKPACK_VANILLA`
