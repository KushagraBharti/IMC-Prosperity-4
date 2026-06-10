# Official Submission Analysis

Scope: diagnosis only. No strategy edits and no iterative files were created.

## Mapping
- `round5_candidate_1.py` -> official submission `559965`; code matched submitted `.py` exactly.
- `round5_candidate_2.py` -> official submission `560036`; code matched submitted `.py` exactly.
- `round5_candidate_3.py` -> official submission `560076`; code matched submitted `.py` exactly.
- `round5_candidate_4.py` -> official submission `560128`; code matched submitted `.py` exactly.
- `round5_candidate_5.py` -> official submission `560155`; code matched submitted `.py` exactly.

## Score Table

| Strategy | Kevin Full | Xeeshan Full | Portal Window Kevin | Portal Window Xeeshan | Rust Full | Official Portal Score |
|---|---:|---:|---:|---:|---:|---:|
| round5_candidate_1.py | 4238 | 4238 | 1865.00 | 1865.00 |  | 1864.24 |
| round5_candidate_2.py | -1007708 | -1007817 | -38530.00 | -38568.00 |  | -37335.31 |
| round5_candidate_3.py | 19338 | 19331 | -894.00 | -894.00 |  | -890.34 |
| round5_candidate_4.py | -105458 | -105462 | 2828.00 | 2828.00 |  | 2821.48 |
| round5_candidate_5.py | -54298 | -54318 | 902.00 | 894.00 |  | 899.14 |

## Consistency Check
- Official activities window: day 4, timestamps 0..99900. Full activity hashes: 5 unique because `profit_and_loss` differs by submission; market-book hashes: 1 unique.
- Kevin and Xeeshan full scores were nearly identical to each other, so the full-history local tools are internally consistent.
- Portal-window Kevin/Xeeshan replay on extracted official market data matches the official portal scores within rounding for all five submissions.
- The major disagreement is full-history research/backtests versus the official day-4 window: Candidate 3 was positive full-history but negative official; Candidates 4 and 5 were poor full-history but positive official.
- Main isolation: the strategy edge is dominated by day/window regime and actual fill path. Directional research translated only when the specific filled products had favorable realized PnL under the official window.
- No strategy emitted sandbox/lambda errors in official logs; mismatches are execution/fill/path issues, not platform crashes.

## Candidate Diagnostics
### round5_candidate_1.py / submission 559965
- Edge attempted: PEBBLES category factor/residual mean reversion.
- Official score 1864.24; reconstructed own-fill marked PnL 1865.00; own trades 9; nonempty portal error logs 0.
- Portal-window replay: Kevin 1865.00, Xeeshan 1865.00.
- Made money: PEBBLES_XL 1410, PEBBLES_L 644.
- Lost money: PEBBLES_M -104, PEBBLES_XS -85.
- Final inventory: {'PEBBLES_XL': 2, 'PEBBLES_M': 0, 'PEBBLES_L': 2, 'PEBBLES_XS': 2}. Max abs position: {'PEBBLES_M': 2, 'PEBBLES_L': 4, 'PEBBLES_XL': 2, 'PEBBLES_XS': 2}.
- Worst graph deltas: 73400:-203, 55200:-156, 63200:-151, 59800:-140, 61400:-129.
- Avg 1000-tick markout: PEBBLES_M -21.2, PEBBLES_XS 6.5, PEBBLES_L 7.0, PEBBLES_XL 131.0.
- Diagnosis: PEBBLES relation did not fail wholesale, but fills were too sparse to support the full factor thesis. XL and L were right; M/XS were adverse, so breadth mattered more than the category-level signal.
- Repair first: keep PEBBLES but reduce breadth, require stronger residual confirmation, and favor XL/L while making stale inventory exits less eager.
### round5_candidate_2.py / submission 560036
- Edge attempted: Nested-validation survivor product time-series signals.
- Official score -37335.31; reconstructed own-fill marked PnL -37341.50; own trades 7146; nonempty portal error logs 0.
- Portal-window replay: Kevin -38530.00, Xeeshan -38568.00.
- Made money: SLEEP_POD_SUEDE 152.
- Lost money: ROBOT_LAUNDRY -8782, MICROCHIP_OVAL -8732, TRANSLATOR_GRAPHITE_MIST -8191, TRANSLATOR_ASTRO_BLACK -4756.
- Final inventory: {'TRANSLATOR_ASTRO_BLACK': -9, 'TRANSLATOR_GRAPHITE_MIST': -9, 'ROBOT_LAUNDRY': -9, 'SLEEP_POD_SUEDE': 3, 'ROBOT_IRONING': 9, 'MICROCHIP_OVAL': 9, 'PEBBLES_L': -3, 'UV_VISOR_ORANGE': -5}. Max abs position: {'MICROCHIP_OVAL': 10, 'ROBOT_IRONING': 10, 'TRANSLATOR_ASTRO_BLACK': 10, 'TRANSLATOR_GRAPHITE_MIST': 10, 'SLEEP_POD_SUEDE': 10, 'PEBBLES_L': 9, 'ROBOT_LAUNDRY': 10, 'UV_VISOR_ORANGE': 10}.
- Worst graph deltas: 33600:-890, 41400:-871, 67400:-856, 84600:-830, 42600:-764.
- Avg 1000-tick markout: TRANSLATOR_GRAPHITE_MIST -5.2, TRANSLATOR_ASTRO_BLACK -3.7, ROBOT_LAUNDRY -3.6, SLEEP_POD_SUEDE -3.6, MICROCHIP_OVAL -3.4, ROBOT_IRONING -2.8, PEBBLES_L -1.3, UV_VISOR_ORANGE -1.0.
- Diagnosis: broad survivor basket overtraded. The largest filled products all lost money and several sat near limits. Nested-validation inclusion did not translate into executable day-4 PnL.
- Repair first: reject the broad basket form; salvage only products with favorable official markout or use it as a negative-control branch.
### round5_candidate_3.py / submission 560076
- Edge attempted: Cost-stressed concentrated subset signals.
- Official score -890.34; reconstructed own-fill marked PnL -894.00; own trades 585; nonempty portal error logs 0.
- Portal-window replay: Kevin -894.00, Xeeshan -894.00.
- Made money: PEBBLES_XL 3273, PANEL_1X4 2022, PEBBLES_L 2007.
- Lost money: ROBOT_LAUNDRY -4982, OXYGEN_SHAKE_CHOCOLATE -3214.
- Final inventory: {'ROBOT_LAUNDRY': -10, 'OXYGEN_SHAKE_CHOCOLATE': -10, 'PEBBLES_XL': -10, 'PANEL_1X4': -10, 'PEBBLES_L': -6}. Max abs position: {'OXYGEN_SHAKE_CHOCOLATE': 10, 'PEBBLES_XL': 10, 'PEBBLES_L': 10, 'PANEL_1X4': 10, 'ROBOT_LAUNDRY': 10}.
- Worst graph deltas: 86200:-1349, 19200:-1057, 25800:-1052, 67400:-949, 44400:-948.
- Avg 1000-tick markout: ROBOT_LAUNDRY -6.4, PEBBLES_L -3.6, OXYGEN_SHAKE_CHOCOLATE -2.5, PANEL_1X4 -0.8, PEBBLES_XL 12.6.
- Diagnosis: concentrated stressed subset was mixed rather than structurally broken. PEBBLES_XL, PANEL_1X4, and PEBBLES_L worked; ROBOT_LAUNDRY and OXYGEN_SHAKE_CHOCOLATE overwhelmed them.
- Repair first: prune losing legs, lower limit residence, and retest whether PANEL/PEBBLES gains survive with less short bias concentration.
### round5_candidate_4.py / submission 560128
- Edge attempted: ROBOT/SNACKPACK short-horizon microstructure and relative factor.
- Official score 2821.48; reconstructed own-fill marked PnL 2828.00; own trades 216; nonempty portal error logs 0.
- Portal-window replay: Kevin 2828.00, Xeeshan 2828.00.
- Made money: ROBOT_IRONING 3106, ROBOT_DISHES 1201, SNACKPACK_CHOCOLATE 901.
- Lost money: SNACKPACK_VANILLA -1340, SNACKPACK_RASPBERRY -1040.
- Final inventory: {'SNACKPACK_RASPBERRY': 8, 'ROBOT_IRONING': 10, 'SNACKPACK_CHOCOLATE': 8, 'ROBOT_DISHES': -10, 'SNACKPACK_VANILLA': 8}. Max abs position: {'ROBOT_DISHES': 10, 'ROBOT_IRONING': 10, 'SNACKPACK_RASPBERRY': 10, 'SNACKPACK_CHOCOLATE': 10, 'SNACKPACK_VANILLA': 10}.
- Worst graph deltas: 76400:-520, 92400:-483, 89200:-449, 45000:-449, 69400:-438.
- Avg 1000-tick markout: ROBOT_IRONING -2.8, ROBOT_DISHES -2.3, SNACKPACK_CHOCOLATE -1.9, SNACKPACK_VANILLA 3.0, SNACKPACK_RASPBERRY 3.8.
- Diagnosis: official portal supported the ROBOT microstructure idea. ROBOT_IRONING and ROBOT_DISHES carried the candidate; SNACKPACK_VANILLA/RASPBERRY damaged it.
- Repair first: promote ROBOT-focused version, cut or heavily gate Snackpack relative trades, and reduce end-window inventory.
### round5_candidate_5.py / submission 560155
- Edge attempted: Diversified regime-throttled blend of survivor and residual directions.
- Official score 899.14; reconstructed own-fill marked PnL 894.50; own trades 836; nonempty portal error logs 0.
- Portal-window replay: Kevin 902.00, Xeeshan 894.00.
- Made money: PEBBLES_XL 3740, SLEEP_POD_SUEDE 2662, OXYGEN_SHAKE_EVENING_BREATH 1749, TRANSLATOR_GRAPHITE_MIST 1193.
- Lost money: MICROCHIP_OVAL -3482, TRANSLATOR_ASTRO_BLACK -1951, ROBOT_LAUNDRY -1574, PEBBLES_L -1111.
- Final inventory: {'PEBBLES_L': 7, 'ROBOT_LAUNDRY': -9, 'SNACKPACK_STRAWBERRY': 5, 'OXYGEN_SHAKE_EVENING_BREATH': 5, 'SLEEP_POD_SUEDE': 6, 'PEBBLES_XL': -1, 'ROBOT_IRONING': 10, 'MICROCHIP_OVAL': 10, 'TRANSLATOR_GRAPHITE_MIST': -5, 'TRANSLATOR_ASTRO_BLACK': -7, 'UV_VISOR_ORANGE': -5}. Max abs position: {'MICROCHIP_OVAL': 10, 'TRANSLATOR_ASTRO_BLACK': 10, 'ROBOT_LAUNDRY': 10, 'ROBOT_IRONING': 10, 'SLEEP_POD_SUEDE': 10, 'PEBBLES_XL': 10, 'PEBBLES_L': 9, 'OXYGEN_SHAKE_EVENING_BREATH': 10, 'UV_VISOR_ORANGE': 10, 'TRANSLATOR_GRAPHITE_MIST': 10, 'SNACKPACK_STRAWBERRY': 8}.
- Worst graph deltas: 33000:-1495, 93200:-1285, 21800:-1276, 97800:-1235, 89400:-1208.
- Avg 1000-tick markout: OXYGEN_SHAKE_EVENING_BREATH -3.2, MICROCHIP_OVAL -3.0, SLEEP_POD_SUEDE -2.6, TRANSLATOR_ASTRO_BLACK -2.0, UV_VISOR_ORANGE 0.1, ROBOT_LAUNDRY 0.4, PEBBLES_XL 2.3, TRANSLATOR_GRAPHITE_MIST 2.4.
- Diagnosis: diversified blend was repairable but noisy. Strong wins in PEBBLES_XL, SLEEP_POD_SUEDE, and OXYGEN_SHAKE_EVENING_BREATH were diluted by MICROCHIP_OVAL, TRANSLATOR_ASTRO_BLACK, ROBOT_LAUNDRY, and ROBOT_IRONING.
- Repair first: convert to a pruned ensemble with hard product allowlist from official product PnL and markout, not the original broad survivor set.

## Cross-Candidate Diagnosis
- Common failure: research-level directional/proxy signals were much easier to make look good than to monetize after actual portal fills. Passive fill quality and limit residence dominate.
- Products that helped officially: `PEBBLES_XL`, `PEBBLES_L`, `ROBOT_IRONING` in Candidate 4, `ROBOT_DISHES`, `SLEEP_POD_SUEDE`, `OXYGEN_SHAKE_EVENING_BREATH`, and `PANEL_1X4`.
- Products that hurt repeatedly: `ROBOT_LAUNDRY`, `MICROCHIP_OVAL`, `TRANSLATOR_ASTRO_BLACK`, `TRANSLATOR_GRAPHITE_MIST`; Snackpack was mixed and should not be broadly trusted.
- Research that transferred: PEBBLES structural relation exists but needs product/selectivity; ROBOT short-horizon microstructure transferred better in Candidate 4 than broad nested survivor baskets.
- Research that did not transfer: broad nested-validation survivor selection and cost-stressed product inclusion without fill-quality gating.
- Permanent reject: Candidate 2 as a broad basket. It can only contribute pruned/product-level lessons.
- Promotion candidates by combined evidence, not raw score: Candidate 4, Candidate 5, Candidate 1. Candidate 3 is first alternate because its profitable legs are clear but its official total was negative.
