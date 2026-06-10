# Exhaustive Candidate 26-30 Inputs

Do not create candidates from this file until explicitly instructed. This is the controlled input list after the remaining-edge scan.

## Add / Preserve

- `PEBBLES_S` (PEBBLES): class `validated_edge`, best family `breakout_low_reversal`, known portal `11490`, full `80507`, role `standalone-tradable`.
- `PEBBLES_XL` (PEBBLES): class `validated_edge`, best family `rolling_mean_reversion`, known portal `9560`, full `12827`, role `standalone-tradable`.
- `UV_VISOR_ORANGE` (UV_VISOR): class `validated_edge`, best family `momentum`, known portal `4270`, full `15394`, role `standalone-tradable`.
- `MICROCHIP_OVAL` (MICROCHIP): class `validated_edge`, best family `breakout_low_reversal`, known portal `3298`, full `1994`, role `standalone-tradable`.
- `SLEEP_POD_COTTON` (SLEEP_POD): class `validated_edge`, best family `vol_norm_momentum`, known portal `3154`, full `6212`, role `standalone-tradable`.
- `ROBOT_IRONING` (ROBOT): class `validated_edge`, best family `vol_norm_momentum`, known portal `2524`, full `16297`, role `standalone-tradable`.
- `PEBBLES_M` (PEBBLES): class `validated_edge`, best family `breakout_low_reversal`, known portal `1490`, full `22494`, role `standalone-tradable`.
- `PEBBLES_XS` (PEBBLES): class `validated_edge`, best family `breakout_low_reversal`, known portal `0`, full `0`, role `standalone-tradable`.
- `PEBBLES_L` (PEBBLES): class `validated_edge`, best family `rolling_mean_reversion`, known portal `0`, full `3216`, role `standalone-tradable`.
- `PANEL_4X4` (PANEL): class `validated_edge`, best family `momentum`, known portal `0`, full `0`, role `standalone-tradable`.
- `OXYGEN_SHAKE_GARLIC` (OXYGEN_SHAKE): class `validated_edge`, best family `reversal`, known portal `0`, full `0`, role `standalone-tradable`.

## Conditional, Gate Before Integration

- `GALAXY_SOUNDS_PLANETARY_RINGS` (GALAXY_SOUNDS): best family `breakout_low_reversal`, portal proxy `572065`, known portal `2296`, reason: edge appears in a component/probe but is too small or unstable to call standalone strategy-grade.
- `UV_VISOR_AMBER` (UV_VISOR): best family `breakout_low_reversal`, portal proxy `532984`, known portal `534`, reason: edge appears in a component/probe but is too small or unstable to call standalone strategy-grade.
- `MICROCHIP_SQUARE` (MICROCHIP): best family `breakout_low_reversal`, portal proxy `474126`, known portal `5022`, reason: portal/integration PnL is positive but full-history attribution is weak or negative; treat as portal-fragile and gate hard.
- `ROBOT_LAUNDRY` (ROBOT): best family `breakout_low_reversal`, portal proxy `439834`, known portal `502`, reason: portal/integration PnL is positive but full-history attribution is weak or negative; treat as portal-fragile and gate hard.
- `MICROCHIP_RECTANGLE` (MICROCHIP): best family `breakout_low_reversal`, portal proxy `428480`, known portal `859`, reason: portal/integration PnL is positive but full-history attribution is weak or negative; treat as portal-fragile and gate hard.
- `SLEEP_POD_LAMB_WOOL` (SLEEP_POD): best family `breakout_low_reversal`, portal proxy `405396`, known portal `2442`, reason: portal/integration PnL is positive but full-history attribution is weak or negative; treat as portal-fragile and gate hard.
- `SLEEP_POD_POLYESTER` (SLEEP_POD): best family `breakout_low_reversal`, portal proxy `369978`, known portal `2022`, reason: edge appears in a component/probe but is too small or unstable to call standalone strategy-grade.
- `PANEL_2X4` (PANEL): best family `breakout_low_reversal`, portal proxy `294470`, known portal `1996`, reason: portal/integration PnL is positive but full-history attribution is weak or negative; treat as portal-fragile and gate hard.
- `TRANSLATOR_VOID_BLUE` (TRANSLATOR): best family `breakout_low_reversal`, portal proxy `164090`, known portal `1456`, reason: edge appears in a component/probe but is too small or unstable to call standalone strategy-grade.
- `OXYGEN_SHAKE_EVENING_BREATH` (OXYGEN_SHAKE): best family `breakout_low_reversal`, portal proxy `135592`, known portal `270`, reason: full-history attribution is positive but portal-window capture is small; preserve only for robustness/diversification, not portal upside.
- `SLEEP_POD_SUEDE` (SLEEP_POD): best family `breakout_low_reversal`, portal proxy `132016`, known portal `1883`, reason: edge appears in a component/probe but is too small or unstable to call standalone strategy-grade.
- `TRANSLATOR_ASTRO_BLACK` (TRANSLATOR): best family `breakout_low_reversal`, portal proxy `116168`, known portal `0`, reason: prior individual probe status was `too weak alone`; keep only gated or as a basket component.
- `ROBOT_MOPPING` (ROBOT): best family `rolling_mean_reversion`, portal proxy `115242`, known portal `1622`, reason: edge appears in a component/probe but is too small or unstable to call standalone strategy-grade.
- `TRANSLATOR_GRAPHITE_MIST` (TRANSLATOR): best family `breakout_low_reversal`, portal proxy `110212`, known portal `3705`, reason: portal/integration PnL is positive but full-history attribution is weak or negative; treat as portal-fragile and gate hard.
- `SLEEP_POD_NYLON` (SLEEP_POD): best family `rolling_mean_reversion`, portal proxy `107863`, known portal `760`, reason: edge appears in a component/probe but is too small or unstable to call standalone strategy-grade.
- `MICROCHIP_TRIANGLE` (MICROCHIP): best family `rolling_mean_reversion`, portal proxy `90206`, known portal `1242`, reason: edge appears in a component/probe but is too small or unstable to call standalone strategy-grade.
- `UV_VISOR_RED` (UV_VISOR): best family `momentum`, portal proxy `81026`, known portal `0`, reason: targeted portal replay is positive but full-history replay failed; this is portal-fragile.

## Do Not Add Yet

- `ROBOT_DISHES` (ROBOT): gap `51425`, best family `breakout_low_reversal`, reason: large analytical oracle/proxy remains, but no executable replay has confirmed capture; treat as not currently capturable, not a tradable edge.
- `TRANSLATOR_SPACE_GRAY` (TRANSLATOR): gap `43320`, best family `breakout_high`, reason: prior executable replay status was `no standalone edge found` despite high oracle/proxy; do not integrate without a new mechanism.
- `TRANSLATOR_ECLIPSE_CHARCOAL` (TRANSLATOR): gap `40885`, best family `rolling_mean_reversion`, reason: large analytical oracle/proxy remains, but no executable replay has confirmed capture; treat as not currently capturable, not a tradable edge.
- `GALAXY_SOUNDS_BLACK_HOLES` (GALAXY_SOUNDS): gap `40195`, best family `rolling_mean_reversion`, reason: large analytical oracle/proxy remains, but no executable replay has confirmed capture; treat as not currently capturable, not a tradable edge.
- `PANEL_2X2` (PANEL): gap `39715`, best family `breakout_low_reversal`, reason: large analytical oracle/proxy remains, but no executable replay has confirmed capture; treat as not currently capturable, not a tradable edge.
- `ROBOT_VACUUMING` (ROBOT): gap `39460`, best family `breakout_low_reversal`, reason: large analytical oracle/proxy remains, but no executable replay has confirmed capture; treat as not currently capturable, not a tradable edge.
- `UV_VISOR_YELLOW` (UV_VISOR): gap `37460`, best family `breakout_low_reversal`, reason: large analytical oracle/proxy remains, but no executable replay has confirmed capture; treat as not currently capturable, not a tradable edge.
- `GALAXY_SOUNDS_SOLAR_WINDS` (GALAXY_SOUNDS): gap `37055`, best family `rolling_mean_reversion`, reason: prior executable replay status was `no standalone edge found` despite high oracle/proxy; do not integrate without a new mechanism. Portal block stability is weak, so timestamp-block concentration is a major overfit risk.
- `PANEL_1X4` (PANEL): gap `36000`, best family `breakout_low_reversal`, reason: large analytical oracle/proxy remains, but no executable replay has confirmed capture; treat as not currently capturable, not a tradable edge.
- `MICROCHIP_CIRCLE` (MICROCHIP): gap `35355`, best family `breakout_low_reversal`, reason: large analytical oracle/proxy remains, but no executable replay has confirmed capture; treat as not currently capturable, not a tradable edge.
- `UV_VISOR_MAGENTA` (UV_VISOR): gap `35125`, best family `breakout_low_reversal`, reason: large analytical oracle/proxy remains, but no executable replay has confirmed capture; treat as not currently capturable, not a tradable edge.
- `GALAXY_SOUNDS_DARK_MATTER` (GALAXY_SOUNDS): gap `34580`, best family `breakout_high`, reason: prior executable replay status was `no standalone edge found` despite high oracle/proxy; do not integrate without a new mechanism.
- `GALAXY_SOUNDS_SOLAR_FLAMES` (GALAXY_SOUNDS): gap `33875`, best family `rolling_mean_reversion`, reason: large analytical oracle/proxy remains, but no executable replay has confirmed capture; treat as not currently capturable, not a tradable edge.
- `OXYGEN_SHAKE_MINT` (OXYGEN_SHAKE): gap `30820`, best family `breakout_low_reversal`, reason: large analytical oracle/proxy remains, but no executable replay has confirmed capture; treat as not currently capturable, not a tradable edge.
- `OXYGEN_SHAKE_MORNING_BREATH` (OXYGEN_SHAKE): gap `30430`, best family `breakout_high`, reason: large analytical oracle/proxy remains, but no executable replay has confirmed capture; treat as not currently capturable, not a tradable edge.
- `PANEL_1X2` (PANEL): gap `27035`, best family `breakout_low_reversal`, reason: large analytical oracle/proxy remains, but no executable replay has confirmed capture; treat as not currently capturable, not a tradable edge.
- `OXYGEN_SHAKE_CHOCOLATE` (OXYGEN_SHAKE): gap `26785`, best family `rolling_mean_reversion`, reason: large analytical oracle/proxy remains, but no executable replay has confirmed capture; treat as not currently capturable, not a tradable edge.
- `SNACKPACK_RASPBERRY` (SNACKPACK): gap `13190`, best family `breakout_low_reversal`, reason: large analytical oracle/proxy remains, but no executable replay has confirmed capture; treat as not currently capturable, not a tradable edge.
- `SNACKPACK_STRAWBERRY` (SNACKPACK): gap `11755`, best family `breakout_low_reversal`, reason: large analytical oracle/proxy remains, but no executable replay has confirmed capture; treat as not currently capturable, not a tradable edge.
- `SNACKPACK_CHOCOLATE` (SNACKPACK): gap `7495`, best family `rolling_mean_reversion`, reason: large analytical oracle/proxy remains, but no executable replay has confirmed capture; treat as not currently capturable, not a tradable edge.
- `SNACKPACK_VANILLA` (SNACKPACK): gap `6535`, best family `rolling_mean_reversion`, reason: large analytical oracle/proxy remains, but no executable replay has confirmed capture; treat as not currently capturable, not a tradable edge.
- `SNACKPACK_PISTACHIO` (SNACKPACK): gap `3545`, best family `breakout_low_reversal`, reason: large analytical oracle/proxy remains, but no executable replay has confirmed capture; treat as not currently capturable, not a tradable edge.

## Concrete Candidate 26-30 Guidance

- Candidate 26 should refine candidate 24 by keeping validated unresolved legs and hard-gating weak conditional ones.
- Candidate 27 should restore only validated long-horizon products with positive full-history contribution.
- Candidate 28 should prioritize full-history robustness using validated long-horizon products and avoid portal-only conditional names.
- Candidate 29 may pursue portal upside from conditional SLEEP/TRANSLATOR/PANEL/UV legs, but only with product-level caps and adverse-inventory throttles.
- Candidate 30 should be the clean additive branch: PEBBLES plus validated non-PEBBLES only.
