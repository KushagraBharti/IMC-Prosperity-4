# Candidate 39/42 Fill-Capacity Sprint Summary

Focus: candidate 42 as primary base; candidate 39 used only as parameter reference. No final candidates were created.

## Main Findings

- The qty10 probes matched candidate 42 baseline, proving candidate 42 is fillability/turnover limited, not requested-quantity limited.
- Pure candidate 42 robust upgrade: skip `PEBBLES_XS`. Portal improves from `113,412` to `115,356`; full improves from `421.5k` to `424.6k`.
- Candidate 42 can exceed 120k portal by selectively importing MICRO/UV loosened settings and skipping `PEBBLES_XS`: `123,434` portal, `310.7k/310.9k` full. This is the best balanced 42-derived upgrade.
- Panel hybrid/crossing raises portal but costs full robustness. Pure 42 panel+skipXS gets `118,106` portal / `314.7k` full; MICRO/UV+panel reaches `126,184` portal but only `200.8k/201.3k` full.
- Passive weak-signal exits slightly helped some portal variants but generally hurt pure 42. Taker exits were destructive (`~80k` portal on the tested branch).
- Candidate 42 did not reach 130k portal while preserving >300k full in this sprint. The best >300k full branch is `probe_c42_transplant_micro_uv_from39_skipxs.py` at `123,434` portal.

## Best Portal Probes

| Probe | Portal K | Portal X | Full K | Full X | Max State | Trades | Avg Fill |
|---|---:|---:|---:|---:|---:|---:|---:|
| `probe_c42_c39_panel_galaxy_skipxs_exit_robot.py` | 128420.0 | 128420.0 | -163588.0 | -163672.0 | 31745 | 1850 | 3.587 |
| `probe_c42_c39_panel_galaxy_skipxs_exit_passive.py` | 126959.0 | 126959.0 | -17214.0 | -16818.0 | 30589 | 1757 | 3.483 |
| `probe_c42_c39_panel_galaxy_skip_pebxs.py` | 126476.0 | 126476.0 | -19142.0 | -18746.0 | 30589 | 1752 | 3.484 |
| `probe_c42_microuv_skipxs_panelhybrid.py` | 126184.0 | 126184.0 | 200838.0 | 201272.0 | 29372 | 1622 | 3.105 |
| `probe_c37_hybrid_panel.py` | 126174.0 | 126184.0 | 49000.0 | 48934.0 | 32325 | 1717 | 3.244 |
| `probe_c42_c39_hybrid_panel_skipxs.py` | 126073.0 | 126073.0 | 192614.0 | 193048.0 | 30589 |  |  |
| `probe_c42_microuv_skipxs_panelhybrid_exit.py` | 125956.0 | 125956.0 |  |  | 29372 |  |  |
| `probe_c42_c39_hybrid_panel_skipxs_exit.py` | 125846.0 | 125846.0 | 191338.0 | 191772.0 | 30589 |  |  |
| `probe_c42_c39_panel_galaxy_exit_passive.py` | 125014.0 | 125014.0 | -20244.0 | -19870.0 | 31170 | 1758 | 3.486 |
| `probe_c42_c39_hybrid_panel_galaxy.py` | 124530.0 | 124530.0 | -22172.0 | -21798.0 | 31170 | 1753 | 3.488 |
| `probe_c39_hybrid_panel.py` | 124186.0 | 124196.0 | 144540.0 | 144962.0 | 31170 | 1622 | 3.109 |
| `probe_c42_c39_panel_galaxy_skipxs_exit_pruned_low.py` | 124150.0 | 124150.0 |  |  | 24318 |  |  |

## Robust Candidates From This Sprint

| Probe | Portal K | Full K | Full X | Read |
|---|---:|---:|---:|---|
| `probe_c42_transplant_micro_uv_from39_skipxs.py` | 123434.0 | 310677.0 | 310853.0 | viable 42-derived candidate input |

## Capacity Diagnosis

- Fill size stayed low because passive orders were not being fully hit at posted prices. Increasing requested size alone did not change realized fills.
- Category-specific hybrid/crossing works only selectively. Panel crossing adds portal PnL but is full-history fragile; micro/UV crossing is harmful; broad crossing is toxic.
- Inventory turnover fixes must be gentle. Passive exits can help a portal-specific branch; taker exits destroy PnL.
- `PEBBLES_XS` is a clear negative/toxic traded leg in portal and removing it is robust-positive on full history.
