# Non-PEBBLES Probe Blueprint

Probe only these non-PEBBLES ideas before any integration with candidate 16.

## Fast Portal-Window Probes Already Run

- `non_pebbles_probe_microchip.py`: Kevin `2063`, Xeeshan `2063`.
- `non_pebbles_probe_robot.py`: Kevin `-744`, Xeeshan `-744`.
- `non_pebbles_probe_uv_oxygen_panel.py`: Kevin `587`, Xeeshan `587`.
- `non_pebbles_probe_breadth.py`: Kevin `-7752`, Xeeshan `-7752`.
- `non_pebbles_probe_longhorizon_breadth.py`: Kevin `17304`, Xeeshan `17304`.
- `non_pebbles_probe_longhorizon_microchip.py`: Kevin `9564`, Xeeshan `9564`.

Interpretation: the first short-horizon probes mostly failed, but the exact long-horizon breadth and MICROCHIP variants passed the portal-window threshold. Breadth is viable only when product-gated by the long-horizon signals; the earlier broad aggregation lost money.

## Full Backtests For Promising Probes

- `non_pebbles_probe_longhorizon_breadth.py`: Kevin full `62069`, Xeeshan full `62495`.
- `non_pebbles_probe_longhorizon_microchip.py`: Kevin full `4865`, Xeeshan full `5291`.

Interpretation: the long-horizon breadth probe is now the first non-PEBBLES standalone probe with both strong portal-window replay and strong full-history PnL. It is worth turning into a formal candidate before any integration with candidate 16.

## `MICROCHIP_SQUARE` / `MICROCHIP`

- Edge to test: `100_tick_reversal`.
- Execution: passive-first.
- Ceiling: portal oracle `134735`, full oracle `3345559`.
- Hindsight risk control: enough ceiling across portal and full data.
- Justification: portal proxy `151402` and full proxy `522447` using online features only.
- Quick pass condition: Kevin portal-window replay above `3000` standalone, or positive product PnL with clear fill/markout evidence.

## `GALAXY_SOUNDS_PLANETARY_RINGS` / `GALAXY_SOUNDS`

- Edge to test: `100_tick_momentum`.
- Execution: passive-first.
- Ceiling: portal oracle `35762`, full oracle `1044624`.
- Hindsight risk control: enough ceiling across portal and full data.
- Justification: portal proxy `169709` and full proxy `446495` using online features only.
- Quick pass condition: Kevin portal-window replay above `3000` standalone, or positive product PnL with clear fill/markout evidence.

## `ROBOT_LAUNDRY` / `ROBOT`

- Edge to test: `100_tick_momentum`.
- Execution: passive-first.
- Ceiling: portal oracle `44194`, full oracle `1433976`.
- Hindsight risk control: enough ceiling across portal and full data.
- Justification: portal proxy `154118` and full proxy `1100966` using online features only.
- Quick pass condition: Kevin portal-window replay above `3000` standalone, or positive product PnL with clear fill/markout evidence.

## `OXYGEN_SHAKE_EVENING_BREATH` / `OXYGEN_SHAKE`

- Edge to test: `100_tick_reversal`.
- Execution: passive-first.
- Ceiling: portal oracle `36855`, full oracle `1149632`.
- Hindsight risk control: enough ceiling across portal and full data.
- Justification: portal proxy `121407` and full proxy `154049` using online features only.
- Quick pass condition: Kevin portal-window replay above `3000` standalone, or positive product PnL with clear fill/markout evidence.

## `MICROCHIP_TRIANGLE` / `MICROCHIP`

- Edge to test: `50_tick_reversal`.
- Execution: passive-first.
- Ceiling: portal oracle `74433`, full oracle `2316760`.
- Hindsight risk control: enough ceiling across portal and full data.
- Justification: portal proxy `78794` and full proxy `209920` using online features only.
- Quick pass condition: Kevin portal-window replay above `3000` standalone, or positive product PnL with clear fill/markout evidence.

## `ROBOT_IRONING` / `ROBOT`

- Edge to test: `100_tick_momentum`.
- Execution: passive-first.
- Ceiling: portal oracle `46104`, full oracle `1530467`.
- Hindsight risk control: enough ceiling across portal and full data.
- Justification: portal proxy `97017` and full proxy `551044` using online features only.
- Quick pass condition: Kevin portal-window replay above `3000` standalone, or positive product PnL with clear fill/markout evidence.

## `UV_VISOR_AMBER` / `UV_VISOR`

- Edge to test: `100_tick_momentum`.
- Execution: passive-first.
- Ceiling: portal oracle `23389`, full oracle `748316`.
- Hindsight risk control: enough ceiling across portal and full data.
- Justification: portal proxy `120781` and full proxy `448903` using online features only.
- Quick pass condition: Kevin portal-window replay above `3000` standalone, or positive product PnL with clear fill/markout evidence.

## `MICROCHIP_OVAL` / `MICROCHIP`

- Edge to test: `100_tick_momentum`.
- Execution: passive-first.
- Ceiling: portal oracle `55006`, full oracle `1949916`.
- Hindsight risk control: enough ceiling across portal and full data.
- Justification: portal proxy `75983` and full proxy `201307` using online features only.
- Quick pass condition: Kevin portal-window replay above `3000` standalone, or positive product PnL with clear fill/markout evidence.

## `ROBOT_DISHES` / `ROBOT`

- Edge to test: `100_tick_momentum`.
- Execution: passive-first.
- Ceiling: portal oracle `51356`, full oracle `1721124`.
- Hindsight risk control: enough ceiling across portal and full data.
- Justification: portal proxy `71970` and full proxy `699248` using online features only.
- Quick pass condition: Kevin portal-window replay above `3000` standalone, or positive product PnL with clear fill/markout evidence.

## `SLEEP_POD_SUEDE` / `SLEEP_POD`

- Edge to test: `100_tick_reversal`.
- Execution: passive-first.
- Ceiling: portal oracle `52559`, full oracle `1490631`.
- Hindsight risk control: enough ceiling across portal and full data.
- Justification: portal proxy `67588` and full proxy `148118` using online features only.
- Quick pass condition: Kevin portal-window replay above `3000` standalone, or positive product PnL with clear fill/markout evidence.

Do not integrate any of these into candidate 16 until a standalone portal probe passes.
