# Unresolved Products Edge Summary

This pass targeted the 14 high-oracle products that previously had no confirmed executable edge. PEBBLES was not used.

## Group Probe Results

| Probe | Portal Kevin | Portal Xeeshan | Kevin Full | Xeeshan Full | Verdict |
|---|---:|---:|---:|---:|---|
| `unresolved_probe_portal_best_all.py` | 10227 | 10227 | 33771 | 33771 | keep as mixed unresolved-products breadth edge |
| `unresolved_probe_full_best_all.py` | -6824 | -6824 |  |  | reject; full-history-best signs do not transfer to portal |
| `unresolved_probe_sleep.py` | 4380 | 4380 | 1456 | 1456 | weak standalone, useful only as small component |
| `unresolved_probe_translator_galaxy_uv.py` | -494 | -494 |  |  | reject as group |
| `unresolved_probe_micro_robot_panel.py` | 3400 | 3400 | -20403 | -20403 | reject as group despite portal pass |

## Individual Product Results

| Product | Best Found Signal | Portal Replay | Edge Status |
|---|---|---:|---|
| `UV_VISOR_ORANGE` | 100-tick momentum | 4249 | confirmed standalone probe edge |
| `SLEEP_POD_COTTON` | 100-tick momentum | 3154 | confirmed standalone probe edge |
| `TRANSLATOR_GRAPHITE_MIST` | 100-tick momentum | 2630 | small positive edge |
| `SLEEP_POD_POLYESTER` | 100-tick reversal | 1976 | small positive edge |
| `PANEL_2X4` | 50-tick momentum | 1768 | small positive edge |
| `ROBOT_MOPPING` | 50-tick momentum | 1622 | small positive edge |
| `TRANSLATOR_VOID_BLUE` | 100-tick reversal | 1375 | small positive edge |
| `SLEEP_POD_COTTON` | 100-tick reversal | 1235 | alternate positive edge |
| `MICROCHIP_RECTANGLE` | 50-tick momentum | 859 | weak positive edge |
| `SLEEP_POD_NYLON` | 100-tick reversal | 760 | weak positive edge |
| `SLEEP_POD_LAMB_WOOL` | 100-tick momentum | 408 | weak positive edge |
| `TRANSLATOR_ASTRO_BLACK` | 50-tick reversal | 281 | too weak alone |
| `GALAXY_SOUNDS_SOLAR_WINDS` | 100-tick momentum | -884 | no standalone edge found |
| `TRANSLATOR_SPACE_GRAY` | 100-tick reversal | -1306 | no standalone edge found |
| `GALAXY_SOUNDS_DARK_MATTER` | 100-tick reversal | -3903 | no standalone edge found |

## Practical Takeaways

- We now have a viable non-PEBBLES breadth edge across the unresolved product set: use the portal-best mixed basket, not the full-best version.
- The best standalone additions are `UV_VISOR_ORANGE` and `SLEEP_POD_COTTON`.
- The next tier is small positive but probably only useful when combined: `TRANSLATOR_GRAPHITE_MIST`, `SLEEP_POD_POLYESTER`, `PANEL_2X4`, `ROBOT_MOPPING`, `TRANSLATOR_VOID_BLUE`, `MICROCHIP_RECTANGLE`, `SLEEP_POD_NYLON`, and `SLEEP_POD_LAMB_WOOL`.
- `GALAXY_SOUNDS_SOLAR_WINDS`, `TRANSLATOR_SPACE_GRAY`, and `GALAXY_SOUNDS_DARK_MATTER` still do not have a standalone edge. They may remain in the mixed basket only if later attribution proves they help portfolio timing.
- `TRANSLATOR_ASTRO_BLACK` is barely positive under its alternate signal and should not be considered confirmed.

## Next Probe Candidate

Create a formal standalone candidate from `unresolved_probe_portal_best_all.py` before integrating with candidate 16. It has enough breadth and both portal/full support to justify candidate-level testing.
