# Non-PEBBLES Edge Discovery

Top online edge candidates after portal-window signal proxies:

- `MICROCHIP_SQUARE` (MICROCHIP): portal edge `100_tick_reversal` proxy `151402`, full edge `100_tick_momentum` proxy `522447`, model `statistical/time-series`, verdict `standalone_probe`.
- `GALAXY_SOUNDS_PLANETARY_RINGS` (GALAXY_SOUNDS): portal edge `100_tick_momentum` proxy `169709`, full edge `50_tick_reversal` proxy `446495`, model `statistical/time-series`, verdict `standalone_probe`.
- `ROBOT_LAUNDRY` (ROBOT): portal edge `100_tick_momentum` proxy `154118`, full edge `100_tick_reversal` proxy `1100966`, model `statistical/time-series`, verdict `standalone_probe`.
- `OXYGEN_SHAKE_EVENING_BREATH` (OXYGEN_SHAKE): portal edge `100_tick_reversal` proxy `121407`, full edge `25_tick_reversal` proxy `154049`, model `statistical/time-series`, verdict `standalone_probe`.
- `MICROCHIP_TRIANGLE` (MICROCHIP): portal edge `50_tick_reversal` proxy `78794`, full edge `100_tick_reversal` proxy `209920`, model `statistical/time-series`, verdict `standalone_probe`.
- `ROBOT_IRONING` (ROBOT): portal edge `100_tick_momentum` proxy `97017`, full edge `100_tick_momentum` proxy `551044`, model `statistical/time-series`, verdict `standalone_probe`.
- `UV_VISOR_AMBER` (UV_VISOR): portal edge `100_tick_momentum` proxy `120781`, full edge `50_tick_momentum` proxy `448903`, model `statistical/time-series`, verdict `standalone_probe`.
- `MICROCHIP_OVAL` (MICROCHIP): portal edge `100_tick_momentum` proxy `75983`, full edge `100_tick_reversal` proxy `201307`, model `statistical/time-series`, verdict `research_probe`.
- `TRANSLATOR_SPACE_GRAY` (TRANSLATOR): portal edge `100_tick_momentum` proxy `95110`, full edge `100_tick_reversal` proxy `319606`, model `statistical/time-series`, verdict `defer`.
- `GALAXY_SOUNDS_SOLAR_WINDS` (GALAXY_SOUNDS): portal edge `100_tick_momentum` proxy `99594`, full edge `100_tick_momentum` proxy `459604`, model `statistical/time-series`, verdict `defer`.
- `UV_VISOR_ORANGE` (UV_VISOR): portal edge `100_tick_momentum` proxy `96617`, full edge `100_tick_reversal` proxy `467780`, model `statistical/time-series`, verdict `defer`.
- `ROBOT_DISHES` (ROBOT): portal edge `100_tick_momentum` proxy `71970`, full edge `25_tick_reversal` proxy `699248`, model `statistical/time-series`, verdict `research_probe`.
- `GALAXY_SOUNDS_DARK_MATTER` (GALAXY_SOUNDS): portal edge `100_tick_reversal` proxy `87831`, full edge `100_tick_reversal` proxy `420448`, model `statistical/time-series`, verdict `defer`.
- `SLEEP_POD_SUEDE` (SLEEP_POD): portal edge `100_tick_reversal` proxy `67588`, full edge `50_tick_reversal` proxy `148118`, model `statistical/time-series`, verdict `research_probe`.
- `TRANSLATOR_ASTRO_BLACK` (TRANSLATOR): portal edge `100_tick_reversal` proxy `74634`, full edge `50_tick_reversal` proxy `332251`, model `statistical/time-series`, verdict `defer`.

## Rejections

- High oracle alone is insufficient: many products have large hindsight capacity but only weak online capture.
- MICROCHIP remains high-ceiling but the best online proxy is small relative to its oracle, so it should stay isolated.
- ROBOT_DISHES remains special: oracle and ret-reversal signal are large, but previous visible-depth/passive probes did not translate. It needs a standalone execution probe, not integration.
