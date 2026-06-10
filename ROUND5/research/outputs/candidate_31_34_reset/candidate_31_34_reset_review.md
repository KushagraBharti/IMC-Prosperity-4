# Candidate 31-34 Reset Review

## Executive Read

Candidates 31-34 are state-safe under the official 50k `traderData` cap on the portal window. The repair fixed the prior official mismatch.

The reset materially changes the ranking:

| Strategy | Portal Kevin | Portal Xeeshan | Full Kevin | Full Xeeshan | Portal Max State | Verdict |
|---|---:|---:|---:|---:|---:|---|
| `round5_candidate_31.py` | 87,593 | 87,633 | 95,145 | 95,404 | 13,951 | Portal-strong control; full positive but day2/day3 fragile. |
| `round5_candidate_32.py` | 70,713 | 70,713 | 250,247 | 250,263 | 15,535 | Best robust full-history base. |
| `round5_candidate_33.py` | 85,930 | 85,930 | 244,734 | 244,750 | 23,777 | Best portal/full blend; higher official upside than 32, more noise. |
| `round5_candidate_34.py` | 105,940 | 105,940 | -49,854 | -49,708 | 19,364 | Best portal-window exploit, but not robust long-term. |

## Runtime Finding

The full-backtest slowdown was not only log size.

Observed issues:

- The first long run accidentally had duplicate Xeeshan backtester children writing the same candidate 31 log.
- Parallel full runs across multiple broad strategies made progress invisible and slow because each backtester spawns a CPU-heavy child process.
- Redirected `--no-progress` output remains empty until completion, so it can look frozen while CPU is active.
- Giant `--out` logs are still expensive: candidate 31 full logs were about 130 MB each.

Correct operating mode:

- Run full validation one strategy/backtester at a time.
- Use `--no-out` for score-only full runs.
- Use full JSON logs only for finalist attribution.
- Monitor CPU/processes instead of relying on redirected stdout.

## Strategy Breakdown

### `round5_candidate_31.py`

Base: repaired `568114.py`.

Mechanics:

- PEBBLES synthetic fair-value engine on selected PEBBLES.
- 10,000-anchor engine for a small anchor set.
- Product-specific signal engines.
- Extra category-relative engines.
- Momentum extras.
- Compact state serialization.

Full result:

- Day 2: -13,044 Kevin / -12,936 Xeeshan.
- Day 3: -27,974 Kevin / -27,948 Xeeshan.
- Day 4: 136,163 Kevin / 136,287 Xeeshan.
- Total: 95,145 Kevin / 95,404 Xeeshan.

Read:

- Good official-window candidate.
- Full-history profit depends heavily on day 4.
- Day 2/day 3 negative drift means this is not the cleanest hidden-final base.

### `round5_candidate_32.py`

Base: repaired `round5_candidate_30.py`.

Mechanics:

- PEBBLES fair-value core.
- Selective signal config across validated and cleaner non-PEBBLES engines.
- Fewer fragile extras than 33/34.
- Compact state serialization.

Full result:

- Day 2: 78,174 Kevin / 78,212 Xeeshan.
- Day 3: 44,874 Kevin / 44,874 Xeeshan.
- Day 4: 127,200 Kevin / 127,178 Xeeshan.
- Total: 250,247 Kevin / 250,263 Xeeshan.

Read:

- Best long-term candidate among 31-34.
- All visible full-history days are positive.
- Portal-window is lower than 33/34, but this is the strongest hidden-final robustness anchor.

### `round5_candidate_33.py`

Base: repaired `round5_candidate_29.py`.

Mechanics:

- Same PEBBLES core family as 32.
- Broader product-specific signal universe than 32.
- More GALAXY, OXYGEN, PANEL, UV, SLEEP, and MICROCHIP exposure.
- Compact state serialization.

Full result:

- Day 2: 35,566 Kevin / 35,604 Xeeshan.
- Day 3: 81,224 Kevin / 81,224 Xeeshan.
- Day 4: 127,944 Kevin / 127,922 Xeeshan.
- Total: 244,734 Kevin / 244,750 Xeeshan.

Read:

- Very strong blended candidate.
- Better portal score than 32 while nearly matching full-history strength.
- Wider product universe creates more toxic-leg risk, but visible-day stability is good.

### `round5_candidate_34.py`

Base: repaired `568593.py`.

Mechanics:

- PEBBLES/anchor/signal/relative/momentum architecture similar to 31, but with more aggressive momentum extras.
- Compact state serialization fixed the official cap issue.

Full result:

- Day 2: -107,065 Kevin / -107,002 Xeeshan.
- Day 3: -71,634 Kevin / -71,568 Xeeshan.
- Day 4: 128,846 Kevin / 128,863 Xeeshan.
- Total: -49,854 Kevin / -49,708 Xeeshan.

Read:

- Highest portal-window candidate.
- Not robust across full visible data.
- Should be treated as portal-window exploit / information submission, not as hidden-final default.

## Hardcoding And Platform Review

Static scan:

- No local file reads.
- No unsupported heavy imports.
- No `pandas`, `numpy`, `sklearn`, `statsmodels`, or research-only libraries.
- No `random`.
- No `eval` / `exec`.
- No official submission IDs embedded in strategy code.
- No timestamp-specific trading logic found.
- Only imports are `json`, `math`, `dataclasses`, and `typing`.

Hardcoding risk assessment:

- Product lists and thresholds are hand-selected from research and portal-window discovery. That is not forbidden hardcoding, but it is the main overfit vector.
- `ANCHOR = 10_000` in candidates 31/34 is a structural assumption. It is acceptable if the round’s fair-value anchor remains stable, but it is brittle if hidden final shifts.
- No evidence of future leakage or exact timestamp memorization.

State safety:

- Portal-window max state is well under 40k for all four.
- Cap and uncapped portal replays match for all four.
- The original official mismatch root cause is repaired.

## Product/Engine Risk Notes

Strong / useful:

- PEBBLES remains the core engine.
- Candidate 32/33 multi-engine branches validate non-PEBBLES breadth in full history.
- MICROCHIP_OVAL, ROBOT_IRONING, OXYGEN_SHAKE_GARLIC, UV_VISOR_ORANGE, TRANSLATOR_SPACE_GRAY, and selected PANEL/GALAXY legs are additive in at least one robust candidate.

Fragile/toxic:

- Candidate 34 has severe day 2/day 3 losses across PEBBLES_XS, ROBOT_LAUNDRY, MICROCHIP_RECTANGLE/TRIANGLE/SQUARE, OXYGEN_GARLIC, PANEL, UV, SNACKPACK, and several translator/galaxy legs.
- Candidate 31 is less extreme than 34 but still day 2/day 3 negative.
- Broad low-confidence extras can improve portal but destroy full-history robustness.

## Current Ranking

For official portal probing:

1. `round5_candidate_34.py`: highest portal-window replay, but fragile.
2. `round5_candidate_33.py`: strong portal and strong full.
3. `round5_candidate_31.py`: good portal control.
4. `round5_candidate_32.py`: lower portal but best robustness.

For hidden-final robustness:

1. `round5_candidate_32.py`.
2. `round5_candidate_33.py`.
3. `round5_candidate_31.py`.
4. `round5_candidate_34.py`.

For next development base:

1. Use `round5_candidate_32.py` as the robust base.
2. Use `round5_candidate_33.py` as the aggressive-but-still-robust base.
3. Mine `round5_candidate_34.py` only for portal-positive ideas, not as the default hidden-final base.

## Next Work

- Do not discard 34; submit/test it if portal score is the immediate objective.
- Do not use 34 as the main long-term branch without removing the day 2/day 3 toxic legs.
- Next candidate family should start from 32/33, then selectively import only 34 components that are proven additive outside the portal window.
- Full attribution logs should be generated only for 32 and 33 first, because those are now the actual robust bases.
