# Candidate 35/36 Executable Probe Conversion

This phase converted the 150k ceiling-gap map into executable probes. It did not create candidates 37-40.

## Main Results

- Best portal probe: `probe_branch_portal_vanilla_micro_uv_robot_pair.py` at `121,620` Kevin / `121,630` Xeeshan, with capped replay matching.
- Best full-validated robust branch: `probe_c35_anchor_both_micro_uv_conservative.py` at `111,868` portal and `379,278`/`379,319` full.
- Best pure full score among conservative-anchor probes: `probe_increment_snackpack_micro_uv_conservative.py` at `111,490`/`111,500` portal and `379,776`/`379,726` full; it improves full slightly but gives up portal versus the robust branch.
- Best intermediate blend: `probe_grid_robust_micro_uv_uv_hybrid_micro_passive.py` at `116,408` portal and `332,888`/`332,928` full.
- Best portal/full upside branch before robot toxicity: `probe_increment_vanilla_micro_uv_loose.py` at `120,300`/`120,310` portal and `263,754`/`263,918` full.
- Best fresh-category pivot add-on: `probe_pivot_portal_all_fresh_no_robot_micro_uv.py` at `121,436`/`121,446` portal and `254,379`/`254,543` full; it is a small portal lift, not an independent 10k mechanism.
- Best robust fresh-category add-on: `probe_pivot_robust_panel.py` at `112,884` portal and `371,384`/`371,426` full; it improves portal but gives up about `8k` full versus the robust branch.
- Highest raw portal branch: `probe_branch_portal_vanilla_micro_uv_robot_pair.py` at `121,620`/`121,630` portal, but full collapses to `114,755`/`114,557`; use as official-window information, not robust base.
- Candidate 36 remains below the best new portal probe (`105.5k` vs `120.0k`) and far weaker on full history.
- No executable probe reached `150k`; the gap is reduced from roughly `40k` to roughly `30k`, but still real.

## What Was Actually Fixed

- `TRANSLATOR_ECLIPSE_CHARCOAL`: old signal was negative, but the candidate-36-style `10,000` anchor engine adds about `+5k` portal and keeps full strong.
- `PEBBLES_L`: direct fair-value overlay remains weak, but adding it to the `10,000` anchor engine adds another `+1.2k` portal and improves full.
- `TRANSLATOR_ASTRO_BLACK`: previously unused; clean stack adds `+2.6k` portal.
- `GALAXY_SOUNDS_BLACK_HOLES`: previously unused; clean stack adds `+2.2k` portal.
- `SLEEP_POD_SUEDE`: previously unused; clean stack adds `+1.9k` portal.
- `PANEL_2X4`: converted into a real add-on at about `+1.8k` portal.
- `ROBOT_VACUUMING`: low-weight reversal add-on contributes about `+1.4k` portal.
- `SNACKPACK_STRAWBERRY/RASPBERRY/PISTACHIO`: small but real low-weight additions in the clean stack, and full history improves.
- `MICROCHIP_TRIANGLE` and `UV_VISOR_AMBER`: together move portal from `110.97k` to `120.03k`; individually they are `113.98k` and `114.68k`. Both are portal-upside/gated, not robust defaults, because full drops to about `305k-308k` alone and `266k` together.

## Rejected Or Still Conditional

- `PEBBLES_M/XS`: oracle undercapture is real, but direct boost/taker repairs did not improve the robust base. Keep the current fair-value core; do not force an overlay yet.
- `MICROCHIP_CIRCLE`: high oracle but toxic in executable probes.
- `MICROCHIP_TRIANGLE`: useful as portal-upside, not robust default.
- `ROBOT_LAUNDRY`: toxic when grafted into candidate 35.
- `ROBOT_DISHES`: hybrid can make portal PnL and lifted the raw portal branch to `121.6k`, but full drops as low as `114k`; this is official-window-fragile until a better regime/fill gate is found.
- `UV_VISOR_MAGENTA`: tiny portal contribution and poor full proxy; exclude.
- `SNACKPACK_CHOCOLATE`: no usable executable edge. `SNACKPACK_VANILLA` is not a standalone edge, but remains conditional as a 10k-anchor add-on in the portal-upside branch.

## Highest-ROI Next Profit Actions

The phase should not be treated as merely documentation-complete. Four unresolved mechanisms still justify focused work before candidate construction if the goal remains `150k+`:

1. `MICROCHIP_TRIANGLE + UV_VISOR_AMBER` portal gate: already adds about `+8.4k` portal over the conservative robust branch, but costs roughly `115k` full-history PnL when run loose.
2. `ROBOT_DISHES` execution/fill gate: adds about `+1.3k` over the best portal-upside branch when paired with `ROBOT_MOPPING`, but full-history toxicity means the current trigger is too broad.
3. Candidate-36 PANEL/TRANSLATOR/ROBOT machinery: broad transplants failed, but product attribution shows sizeable portal-positive pieces; the next probe should transplant those mechanics one family at a time, not all together.
4. Anchor/fair-value expansion: `TRANSLATOR_ECLIPSE_CHARCOAL` and `PEBBLES_L` proved anchor execution can convert weak signals into robust PnL. Other anchor-like products should be tested only with explicit cap/full validation.

Fresh-category pivot result: SLEEP, PANEL, TRANSLATOR/GALAXY, OXYGEN/SNACKPACK signal retunes and category residual engines did not reveal a new `10k-40k` mechanism. PANEL/fresh-signal additions add roughly `+1k` portal but reduce full-history robustness; category residuals and oracle-mimic overrides generally hurt. This suggests the remaining 150k gap is not explained by simple undertraded fresh-category momentum/reversal or same-category residuals.

Post-pivot high-ROI exhaustion:

- Lead-lag and semantic/name curves across PANEL, SLEEP, TRANSLATOR/GALAXY, and OXYGEN/SNACKPACK were rejected; all tested variants underperformed both active bases.
- Passive fill / rolling-fair market making did not convert the passive oracle. Skip variants were baseline; replacement variants degraded heavily.
- Microstructure imbalance/fill quoting was rejected; replacing fresh-category engines with imbalance quoting cut portal to roughly `71k-104k`.
- Regime-gated practical-gap probes produced baseline/no lift, so the simple spread/imbalance gates did not unlock the high-oracle products.
- PEBBLES quadratic/spline-like fair-value variants were rejected; current linear leave-one-out FV remains materially better.
- Broad `10,000` anchor families were rejected; the anchor edge appears narrow (`TRANSLATOR_ECLIPSE_CHARCOAL`, `PEBBLES_L`, and conditional `SNACKPACK_VANILLA` in portal branch), not a universal product rule.

## Coverage Read

- Validated direct/active products: `37`.
- Conditional/gated products: `9`.
- Excluded products: `4`.
- A 30+ product strategy is now justified if it uses the clean stack architecture. The validated/gated set is broad enough, but products must keep separate engines; a generic all-product scanner is still wrong.

## 150k Read

`150k` is closer but not proven. The best executable conversion moved the portal benchmark from candidate 35's `91.9k` and candidate 36's `105.5k` to `121.6k`; the best robust-full branch is `111.9k` portal with `379k` full. A fresh-category pivot, structural lead-lag/curve search, passive-fill search, regime-gated search, PEBBLES formula search, and broad-anchor search all failed to find an independent high-ROI mechanism. The remaining official-window gap is still roughly `28k`; based on current executable evidence, it is not reachable through the tested oracle-list families.

`200k` still likely requires another structural/execution edge, most likely passive/fill quality or a better candidate-36-style portal engine.
