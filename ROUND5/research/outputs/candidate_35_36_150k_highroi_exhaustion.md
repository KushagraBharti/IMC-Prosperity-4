# Candidate 35/36 150k High-ROI Exhaustion Check

Active bases only:

- Robust-full: `probe_c35_anchor_both_micro_uv_conservative.py`, `111,868` portal, `379,278`/`379,319` full.
- Balanced portal-upside: `probe_increment_vanilla_micro_uv_loose.py`, `120,300`/`120,310` portal, `263,754`/`263,918` full.

## Best Current Results

- Highest raw portal remains `probe_branch_portal_vanilla_micro_uv_robot_pair.py`: `121,620`/`121,630` portal, but full falls to about `115k`.
- Best portal/full tradeoff remains `probe_increment_vanilla_micro_uv_loose.py`: `120.3k` portal and about `264k` full.
- Best robust branch remains `probe_c35_anchor_both_micro_uv_conservative.py`: `111.9k` portal and about `379k` full.
- Fresh-category PANEL add-ons reached only about `+1.0k` portal and reduced full by about `8k-9k`.

## High-ROI Mechanisms Tested And Rejected

- Fresh-category standalone retunes: only small PANEL/fresh-stack gains; no `10k+` mechanism.
- Category residual/fair-value outside PEBBLES: SLEEP/PANEL/TRANSLATOR/GALAXY/OXYGEN/SNACKPACK residuals degraded both bases.
- Oracle-mimic product engines: long-horizon best-proxy overrides mostly degraded, sometimes severely.
- Lead-lag and semantic/name curves: all tested variants underperformed both bases.
- Passive fill / rolling-fair market making: skip variants were baseline; replacement variants degraded heavily.
- Microstructure imbalance/fill quoting: degraded both bases, down to roughly `71k-104k` portal.
- Regime-gated practical-gap add-ons: simple spread/imbalance gates produced no lift.
- PEBBLES quadratic fair value and aggressive M/XS/L variants: degraded hard; current linear PEBBLES FV is better.
- Broad 10,000 anchors: degraded hard; 10,000 anchor appears narrow, not universal.

## Current 150k Read

The missing `~28k-40k` mechanism has not been found in the tested oracle families. The evidence now says `150k` is not reachable by stacking the known small add-ons or by simply trading more categories.

The next real path would need a new mechanism not captured by these probes, likely:

- a more exact official-portal fill/execution model than the current passive proxies,
- a product-specific formula/relationship not represented by linear/quadratic category curves,
- a state-dependent strategy learned from detailed product-level official logs,
- or a separate official-window exploit branch accepted as fragile rather than robust.

Candidate construction should therefore keep two branches separate:

- robust branch: preserve `111.9k / 379k` and add only proven non-toxic components,
- portal branch: preserve `120.3k` or the `121.6k` robot-fragile variant for official-window testing.

Do not claim a `150k` blueprint is proven yet.
