# Round 3 Iterative Loop Plan

## Goal

Create and improve exactly two Round 3 strategy branches:

| New strategy | Starting point | Purpose |
|---|---|---|
| `Iterative 1` | `official_443820_rohan.py` | Start from best known official/portal-window performer |
| `Iterative 2` | `round3_combined_aggressive.py` | Start from strongest full-local performer, then adapt toward portal-window robustness |

Strategy files:

- `ROUND3/strategies/round3_iterative_1.py`
- `ROUND3/strategies/round3_iterative_2.py`

## Core Rule

All actual strategy edits stay in those two files. Any other files are only for diagnostics, logs, analysis scripts, plots, or output tables.

## Workflow

1. Copy the two starting strategies into `Iterative 1` and `Iterative 2`.
2. Run baseline Kevin + Xeeshan on full Round 3 data.
3. Run Kevin + Xeeshan on the official-like portal window.
4. Compare against official scores, especially `443820`, `442527`, `441171`, and `440633`.
5. Break down product-level PnL for Hydrogel, Velvetfruit, and each voucher.
6. Inspect inventory paths, fills, order aggressiveness, passive-vs-taker behavior, and failure timestamps.
7. Build fair-value and alpha diagnostics outside the submitted algorithms.
8. Change one idea at a time inside `Iterative 1` and `Iterative 2`.
9. Keep changes only if they improve portal-window proxy, survive both Kevin and Xeeshan, and make economic sense.
10. Avoid hardcoding and avoid optimizing purely to one extracted window.
11. Stop only when marginal gains flatten or changes become simulator-specific or fragile.

## Diagnostics To Build

- Per-product PnL attribution.
- Timestamp-block PnL attribution.
- Fill attribution by order type, side, edge, and product.
- Inventory path and limit-pressure analysis.
- Option fair-value residual analysis.
- Black-Scholes model checks.
- Implied volatility inversion.
- IV surface and IV time-decay analysis.
- Delta, gamma, and theta exposure estimates.
- Underlying-voucher hedge diagnostics.
- Strike-relative value diagnostics.
- Microstructure imbalance predictive tests.
- Regime clustering and segmentation.
- Markov/regime transition checks where useful.
- Adverse selection after fills.
- Passive quote fill quality.
- Taker trade edge quality.
- Kevin-vs-Xeeshan disagreement analysis.
- Official-window vs full-data drift analysis.
- Strategy diff and result tracking across iterations.

## Guardrails

- No hardcoded timestamp scripts unless there is a defensible market-structure reason, and flag it if used.
- No overfitting to the `0..99900` portal window alone.
- No Rust by default.
- No Monte Carlo by default.
- Debug/logging should be local-only or disabled by default before serious submission.
- Portal-window score gets priority over full public-data score, but not blindly.
- No submission limits.
- No time constraints.
- Diagnostics should be thorough, not just first-pass regressions.

## Backtester Instrumentation Rules

Kevin/Xeeshan backtester changes are allowed only for instrumentation.

Do not change:

- Matching behavior.
- Fill logic.
- Scoring logic.
- Position/risk logic.
- Any behavior that can alter PnL.

Allowed:

- Local logs.
- Execution traces.
- Fills.
- Rejections.
- Positions.
- Per-product execution details.
- Markouts.
- Diagnostic summaries.

## Stop Condition

Persist until both iterative strategies reach convergence. Stop only when further changes:

- Do not improve portal-window proxy.
- Are too fragile or simulator-specific.
- Violate no-hardcoding/no-overfitting.
- Have clearly diminishing marginal returns.

Final state must include:

- Best discovered `Iterative 1`.
- Best discovered `Iterative 2`.
- Evidence table.
- Notes on what improved, what failed, and why.
