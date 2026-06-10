# Candidate 35-36 Ablation Summary

Portal probes used Kevin official-window replay first. Full score-only Kevin probes were run only on the plausible finalist variants.

| Probe | Portal Kevin | Max State | Read |
|---|---:|---:|---|
| `base33` | 85930 | 23777 | candidate 33 benchmark |
| `base34` | 105940 | 19364 | candidate 34 benchmark |
| `probe_33_robot_uv` | 84772 | 26053 | rejected: robot/UV group reduced portal and introduced ROBOT_DISHES drag |
| `probe_33_trans_sleep` | 91912 | 25535 | kept for 35: best robust transplant, raised portal to 91.9k and Kevin full to 287.4k |
| `probe_33_panel_micro` | 86974 | 24945 | rejected for 35: small portal improvement only |
| `probe_33_all_targeted` | 91347 | 28978 | rejected: imports robot drag and underperforms narrow trans/sleep branch |
| `probe_34_no_snack_uvmag` | 105546 | 17918 | kept for 36: nearly preserves 34 portal and flips full from negative to positive |
| `probe_34_keep_lineage` | 103434 | 19364 | rejected: lower portal and retained snack drag from untouched config interactions |
| `probe_34_remove_toxic` | 85275 | 13951 | rejected: portal collapses to 85.3k and full probe stayed negative |
| `probe_34_no_anchor` | 101756 | 19364 | rejected: portal gives up about 4.2k; anchor removal not justified by portal evidence |

## Full Probe Results
- `probe_33_trans_sleep`: Kevin full `287,444`, materially above candidates 32/33.
- `probe_34_no_snack_uvmag`: Kevin full `36,673`, much better than candidate 34 full `-49,854` but not robust-base quality.
- `probe_34_remove_toxic`: Kevin full `-37,387`, rejected despite the cleanup intent.

## Component Decisions
- Kept for 35: candidate 33 core plus `TRANSLATOR_GRAPHITE_MIST`, `TRANSLATOR_VOID_BLUE`, `SLEEP_POD_POLYESTER`.
- Rejected from 35: `ROBOT_DISHES`, `ROBOT_LAUNDRY`, `UV_VISOR_AMBER`, `ROBOT_MOPPING`, `PANEL_2X4`, `MICROCHIP_TRIANGLE` as broad transplants because they did not beat the narrow branch and/or added drag.
- Kept for 36: candidate 34 core, anchor engine, PEBBLES, category-relative products, and main momentum extras except snack/UV-magenta.
- Removed from 36: `SNACKPACK_CHOCOLATE`, `SNACKPACK_VANILLA`, `UV_VISOR_MAGENTA` momentum extras.
