# Candidate 21-25 Integration Analysis

## Baselines

- Candidate 16 benchmark: Kevin full `118231`, Xeeshan full `117875`, portal-window `19935`.
- Long-horizon non-PEBBLES probe benchmark: full about `62k`, portal-window `17304`.
- Unresolved mixed probe benchmark: full about `33.8k`, portal-window `10227`.

## Results

| Candidate | Role | Kevin Full | Xeeshan Full | Portal Kevin | Portal Xeeshan |
|---|---|---:|---:|---:|---:|
| `round5_candidate_21.py` | formal long-horizon non-PEBBLES standalone | 65570 | 65972 | 17304 | 17304 |
| `round5_candidate_22.py` | cleaned unresolved-products standalone | 18578 | 18578 | 20426 | 20426 |
| `round5_candidate_23.py` | candidate 16 + long-horizon breadth | 183801 | 183847 | 37240 | 37240 |
| `round5_candidate_24.py` | candidate 16 + cleaned unresolved breadth | 131105 | 130749 | 41760 | 41760 |
| `round5_candidate_25.py` | candidate 16 + selected best additive legs | 156771 | 156415 | 38946 | 38946 |

## Required Questions

1. Did standalone non-PEBBLES breadth remain profitable as a formal candidate?

Yes. Candidate 21 preserved the probe: portal-window `17304`, full `65.6k/66.0k`. Candidate 22 was even better on portal-window (`20426`) but weaker on full (`18.6k`), so it is more window-sensitive.

2. Did candidate 16 + non-PEBBLES improve over candidate 16 alone?

Yes, all three integrations beat candidate 16's `19935` portal-window. Candidate 23 also strongly improves full-history (`183.8k` vs `118.2k`). Candidate 24 is best portal (`41760`) but weaker full (`131.1k`). Candidate 25 is balanced (`38.9k` portal, `156.8k` full).

3. Which non-PEBBLES products helped?

Strongest evidence:

- Long-horizon breadth: `MICROCHIP_SQUARE`, `GALAXY_SOUNDS_PLANETARY_RINGS`, `ROBOT_LAUNDRY`, `OXYGEN_SHAKE_EVENING_BREATH`, `MICROCHIP_TRIANGLE`, `ROBOT_IRONING`, `UV_VISOR_AMBER`, with smaller support from `MICROCHIP_OVAL` and `SLEEP_POD_SUEDE`.
- Cleaned unresolved set: `UV_VISOR_ORANGE`, `SLEEP_POD_COTTON`, `TRANSLATOR_GRAPHITE_MIST`, `SLEEP_POD_POLYESTER`, `PANEL_2X4`, `ROBOT_MOPPING`, `TRANSLATOR_VOID_BLUE`.

4. Which products hurt?

Earlier individual probes showed standalone negatives for `GALAXY_SOUNDS_SOLAR_WINDS`, `TRANSLATOR_SPACE_GRAY`, and `GALAXY_SOUNDS_DARK_MATTER`; those were excluded from the cleaned candidate 22/24. The MICRO/ROBOT/PANEL group was full-history toxic as a separate basket, so candidate 25 narrowed it rather than using the whole group.

5. Did integration reduce PEBBLES PnL?

No direct product overlap exists, and candidate 16's PEBBLES logic was preserved byte-for-byte in structure. Candidate 23's near-additive full and portal totals are the strongest evidence that PEBBLES was not damaged. Candidate 24/25 differences are attributable to non-PEBBLES selection/gating rather than PEBBLES inventory conflict.

6. Did integration create inventory conflicts or stale-signal issues?

No cross-product inventory conflict is visible because every product has its own limit and the added products are distinct from PEBBLES. Stale-signal risk is still present in the 50/100-tick non-PEBBLES signals; candidate 24's portal/full divergence is the clearest warning that some unresolved legs are window-sensitive.

7. Did any candidate beat candidate 16's portal-window benchmark?

Yes. Candidate 24 `41760`, candidate 25 `38946`, candidate 23 `37240`, candidate 22 `20426`, and candidate 21 `17304` as standalone. All integrated candidates beat candidate 16's `19935`.

8. Did any candidate preserve or improve candidate 16's full-history benchmark?

Yes. Candidate 23 `183.8k`, candidate 25 `156.8k`, and candidate 24 `131.1k` all beat candidate 16 full-history. Candidate 23 is the strongest full-history integration.

9. Which candidate should be submitted to official portal first?

Submit `round5_candidate_24.py` first if the priority is official-window upside. It has the best local portal-window replay at `41760`.

Submit `round5_candidate_23.py` first if the priority is the best blend of full-history robustness and portal improvement. It is the strongest full-history candidate at `183.8k` and still scores `37240` portal-window.

10. Which candidate should become the base for the later iterative loop?

Candidate 23 is the best base branch because it has the strongest full-history robustness and clean additive behavior. Candidate 24 should be kept as an official-window probe branch, not the main robustness base yet.

11. What missing-edge research should happen after this batch?

Only targeted attribution, not broad research:

- Product-level attribution for candidate 24 to identify which unresolved legs create its large portal boost and which reduce full-history robustness.
- Compare candidate 23 vs 25 to determine whether the omitted long-horizon products are necessary or whether selected additive legs can reach similar full PnL with lower fragility.
- Official log analysis after submitting 23/24 to verify whether portal fills match local replay.

## Bottom Line

Integration worked. The best robust branch is `round5_candidate_23.py`; the best portal-window branch is `round5_candidate_24.py`; the best compromise branch is `round5_candidate_25.py`.
