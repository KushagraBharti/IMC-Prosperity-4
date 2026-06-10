# Candidate 31-34 Canonical Reset Review

This is the active Round 5 checkpoint for candidates 31-34.

It supersedes earlier candidate 31-34 notes that only used portal-window replay. Those notes were directionally useful, but incomplete because they did not include the repaired full-history backtests.

## Executive Read

The state-size bug is fixed for all four strategies. Capped and uncapped portal-window replay match, and all four stay far below the official 50,000-character `traderData` cap.

The full-history runs materially change the practical ranking:

| Strategy | Base | Est. Products Traded | Portal Kevin | Portal Xeeshan | Full Kevin | Full Xeeshan | Max Portal State | Current Role |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `round5_candidate_31.py` | repaired `568114.py` | ~27 | 87,593 | 87,633 | 95,145 | 95,404 | 13,951 | official-lineage portal control |
| `round5_candidate_32.py` | repaired `round5_candidate_30.py` | ~22 | 70,713 | 70,713 | 250,247 | 250,263 | 15,535 | best robust full-history base |
| `round5_candidate_33.py` | repaired `round5_candidate_29.py` | ~30 | 85,930 | 85,930 | 244,734 | 244,750 | 23,777 | best portal/full blend |
| `round5_candidate_34.py` | repaired `568593.py` | ~33 | 105,940 | 105,940 | -49,854 | -49,708 | 19,364 | highest portal exploit, not robust |

## Correct Ranking

Portal-window upside:

1. `round5_candidate_34.py`: best portal replay, 105.9k.
2. `round5_candidate_31.py`: official-lineage branch, 87.6k.
3. `round5_candidate_33.py`: broad repaired candidate 29, 85.9k.
4. `round5_candidate_32.py`: lower portal score, 70.7k.

Hidden-final / full-history robustness:

1. `round5_candidate_32.py`: 250.2k full, positive on every visible full-history day.
2. `round5_candidate_33.py`: 244.7k full, positive on every visible full-history day, more aggressive/noisy than 32.
3. `round5_candidate_31.py`: 95.2k full, but day 2/day 3 are negative.
4. `round5_candidate_34.py`: -49.8k full despite huge day 4/portal strength.

Development base:

1. Use `round5_candidate_32.py` as the robust base.
2. Use `round5_candidate_33.py` as the aggressive robust base.
3. Mine `round5_candidate_34.py` for portal-positive ideas only after attribution; do not use it as the default hidden-final base.
4. Keep `round5_candidate_31.py` as the repaired official-lineage benchmark.

## Strategy Differences

### `round5_candidate_31.py`

Identity: repaired official submission `568114.py`.

Architecture:

- Fixed `ANCHOR = 10000` engine.
- PEBBLES synthetic fair-value engine on selected PEBBLES, not all five.
- Product-specific signal engine.
- Category-relative residual engine.
- Momentum extras.
- Compact state serialization.

Strengths:

- Actual official lineage: raw 568114 already worked officially.
- Strong portal replay after repair.
- Broad enough to capture multiple non-PEBBLES groups without being the widest branch.

Weaknesses:

- Full PnL depends heavily on day 4.
- Day 2 and day 3 are negative in full replay.
- Uses the fixed 10,000 anchor assumption.

Full profile:

- Day 2: -13,044 Kevin / -12,936 Xeeshan.
- Day 3: -27,974 Kevin / -27,948 Xeeshan.
- Day 4: 136,163 Kevin / 136,287 Xeeshan.

Use:

- Good official/portal benchmark.
- Not the cleanest robust base.

### `round5_candidate_32.py`

Identity: repaired candidate 30.

Architecture:

- All-five PEBBLES synthetic fair-value engine.
- Curated product-specific signal table.
- No fixed-anchor engine.
- No separate category-relative/momentum-extra subsystem like 31/34.
- Compact state serialization.

Strengths:

- Best full-history score of the four.
- Positive on every visible full-history day.
- Cleaner than 33/34: fewer products, fewer weird extras, less hand-shaped breadth.
- Best hidden-final base.

Weaknesses:

- Lowest portal-window score among the four.
- Still uses hand-selected products/lookbacks/thresholds.
- May leave portal-window upside unused.

Full profile:

- Day 2: 78,174 Kevin / 78,212 Xeeshan.
- Day 3: 44,874 Kevin / 44,874 Xeeshan.
- Day 4: 127,200 Kevin / 127,178 Xeeshan.

Use:

- Primary robust branch.
- Best foundation for the next serious integrated candidate.

### `round5_candidate_33.py`

Identity: repaired candidate 29.

Architecture:

- All-five PEBBLES synthetic fair-value engine.
- Broader product-specific signal table than 32.
- More GALAXY, OXYGEN, PANEL, UV, SLEEP, and MICROCHIP exposure.
- No fixed-anchor engine.
- Compact state serialization.

Strengths:

- Nearly matches 32 on full history.
- Much higher portal score than 32.
- Positive on every visible full-history day.
- Best blend of portal upside and full-history evidence.

Weaknesses:

- More product-specific configs than 32.
- More broad-signal fragility.
- Wider product universe creates more hidden-window decay risk.

Full profile:

- Day 2: 35,566 Kevin / 35,604 Xeeshan.
- Day 3: 81,224 Kevin / 81,224 Xeeshan.
- Day 4: 127,944 Kevin / 127,922 Xeeshan.

Use:

- Best aggressive-but-defensible branch.
- Strong candidate for official submission and for next-candidate development.

### `round5_candidate_34.py`

Identity: repaired `568593.py`.

Architecture:

- Fixed `ANCHOR = 10000` engine.
- PEBBLES synthetic fair-value engine on selected PEBBLES.
- Product-specific signal engine.
- Category-relative residual engine.
- Large momentum-extra set.
- Broadest of the four.
- Compact state serialization.

Strengths:

- Highest portal-window replay by far: 105.9k.
- State repair is successful: portal capped and uncapped match.
- Useful source of portal-positive legs and ideas.

Weaknesses:

- Full-history result is negative.
- Massive day 2/day 3 drawdown in full replay.
- Broadest and most hand-shaped branch.
- Highest overfit risk.

Full profile:

- Day 2: -107,065 Kevin / -107,002 Xeeshan.
- Day 3: -71,634 Kevin / -71,568 Xeeshan.
- Day 4: 128,846 Kevin / 128,863 Xeeshan.

Use:

- Submit/test if the objective is immediate official portal upside.
- Do not promote as the robust hidden-final base without removing toxic day 2/day 3 legs.

## Safety / Hardcoding / Overfit Matrix

| Strategy | Illegal Hardcoding Risk | Competition Hardcoding Level | Overfit Risk | Reason |
|---|---|---|---|---|
| `round5_candidate_31.py` | low | medium | medium | fixed anchor and selected engines, but official lineage and narrower than 34 |
| `round5_candidate_32.py` | low | low-medium | medium-low | no anchor engine, fewer products, best full-history stability |
| `round5_candidate_33.py` | low | medium | medium-high | many product-specific configs, but strong full-history support |
| `round5_candidate_34.py` | low | medium-high | high | best portal result but negative full history and broadest hand-shaped extras |

Static safety findings:

- All four compile.
- No local file reads.
- No subprocess/network usage.
- No heavy research imports.
- No `pandas`, `numpy`, `sklearn`, `statsmodels`, or similar.
- No `eval` / `exec`.
- No runtime randomness.
- No timestamp-based trading branch found.
- Only platform-safe imports: `json`, `math`, `dataclasses`, `typing`, and `datamodel`/fallback classes.

Important distinction:

- None of the four appears illegally hardcoded.
- The real risk is overfitting through product lists, lookbacks, thresholds, weights, signal caps, and the `ANCHOR = 10000` assumption in 31/34.

## Runtime / Backtest Process Lesson

The full-run slowdown was not just log file size.

Confirmed issues:

- One earlier run had duplicate child processes writing to the same output log.
- Running several full broad-strategy replays in parallel makes progress look frozen and competes heavily for CPU.
- Redirected `--no-progress` output can stay empty until process exit.
- `--out` full JSON logs are huge; candidate 31 full logs were about 130 MB each.

Correct procedure:

- Run full validation one strategy/backtester at a time.
- Use `--no-out` for score-only validation.
- Use full JSON logs only for finalist attribution.
- Monitor process CPU if a no-progress run looks silent.

## Active Source Of Truth

Use these current files:

- `ROUND5/research/outputs/candidate_31_34_reset_review.md`
- `ROUND5/research/outputs/candidate_31_34_code_safety_review.md`
- `ROUND5/research/outputs/candidate_31_34_current_checkpoint.md`
- `ROUND5/research/outputs/candidate_31_34_portal_product_pnl.csv`
- `ROUND5/research/outputs/candidate_31_34_portal_category_pnl.csv`
- `ROUND5/research/outputs/candidate_31_34_reset/candidate_31_34_full_score_table.csv`

Older outputs remain useful as historical evidence, but any earlier recommendation that treats candidate 34 as the best overall branch is stale unless the objective is portal-window-only score.

## Next Work

1. If submitting immediately, test `round5_candidate_34.py` for max portal upside and `round5_candidate_33.py` for a safer high-upside branch.
2. If building the next candidate set, start from 32/33, not 34.
3. Attribute candidate 34 versus 32/33 to isolate which portal-positive legs are killing day 2/day 3.
4. Build the next integrated branch by importing only 34 components that remain additive beyond the portal window.
