# Round 5 Iterative Learning Loop

This file defines the Round 5 improvement loop after the initial quant learning pass and five scratch candidates have been created.

It is a source-of-truth operating manual for agents working on Round 5 iterative strategy improvement. The expected workflow is disciplined, research-driven, and persistent. Do not stop after shallow tweaks. Continue until additional changes are not improving robust performance, are simulator-specific, or are clearly overfit.

## Relationship to the Learning Plan

Before this loop begins, complete `ROUND5/research/round5_learning_plan.md`.

Required preconditions:

- The Round 5 data has been inspected and validated.
- Product and category behavior is understood at a deep level.
- Phase 6.5 open-ended research has been used to investigate discoveries that were not covered by the predefined checklist.
- `ROUND5/research/outputs/round5_learning_outputs.md` exists and summarizes the research frontier, extra tools used, extra experiments run, accepted discoveries, and rejected discoveries.
- Five neutral scratch candidates exist:
  - `ROUND5/strategies/round5_candidate_1.py`
  - `ROUND5/strategies/round5_candidate_2.py`
  - `ROUND5/strategies/round5_candidate_3.py`
  - `ROUND5/strategies/round5_candidate_4.py`
  - `ROUND5/strategies/round5_candidate_5.py`
- Kevin and Xeeshan backtests have been run on all five candidates.
- Candidate diagnostics exist for product PnL, category PnL, day PnL, timestamp-block PnL, inventory, fills, and simulator disagreement.
- The two best candidates have been selected for robustness, not just one-window PnL.

Only then create:

- `ROUND5/strategies/round5_iterative_1.py`
- `ROUND5/strategies/round5_iterative_2.py`

These two files are the only files where active strategy logic should be improved during this loop.

## Objective

Improve `round5_iterative_1.py` and `round5_iterative_2.py` until no further robust improvements are available.

The objective is hidden final-round PnL robustness. Public full backtests, portal-window tests, and official submission logs are measurement tools. They are not the true target.

Round 4 underperformed partly because portal-window optimization can diverge from hidden final robustness. Round 5 must avoid that failure mode.

## Core Rules

- No hardcoding.
- No hard overfitting.
- No future leakage.
- No timestamp memorization.
- No portal-window-specific logic.
- No exact event scripts.
- No behavior changes to backtesters, only instrumentation.
- No strategy-family assumptions not supported by research.
- Do not accept changes that only improve one simulator.
- Do not accept changes that only improve one small window unless there is a strong structural reason.
- Do not chase small PnL improvements if they increase hidden-test fragility.
- Larger systemic strategy changes are allowed and encouraged when justified by diagnostics.

## Allowed Work Outside the Two Strategy Files

Actual strategy logic changes belong only in:

- `ROUND5/strategies/round5_iterative_1.py`
- `ROUND5/strategies/round5_iterative_2.py`

Other work is allowed for diagnostics and tooling:

- Research scripts.
- Plot generation.
- CSV summaries.
- Backtest aggregation.
- Fill attribution.
- Backtester instrumentation.
- Package installation.
- Temporary experiments.
- Candidate comparison reports.
- Official submission log extraction when available.

Instrumentation changes to Kevin, Xeeshan, and Rust are explicitly allowed and expected if needed, but only for logging and analysis.

Instrumentation may expose:

- Fills.
- Rejected orders.
- Positions.
- Product-level PnL.
- Markouts.
- Order aggressiveness.
- Fill price vs fair value.
- Timestamp-block attribution.
- Inventory paths.
- Backtester matching differences.

Instrumentation must not alter:

- Matching behavior.
- Fill behavior.
- Scoring.
- Position limits.
- Liquidation.
- Order validation.
- Strategy state.
- Any simulation dynamics.

## Standard Validation Commands

Use Kevin and Xeeshan for normal iteration:

```powershell
.\scripts\bt-kevin.ps1 round5 -Strategy .\ROUND5\strategies\round5_iterative_1.py
.\scripts\bt-xeeshan.ps1 round5 -Strategy .\ROUND5\strategies\round5_iterative_1.py

.\scripts\bt-kevin.ps1 round5 -Strategy .\ROUND5\strategies\round5_iterative_2.py
.\scripts\bt-xeeshan.ps1 round5 -Strategy .\ROUND5\strategies\round5_iterative_2.py
```

Use Rust only for final validation or when a candidate is close to submission:

```powershell
.\scripts\bt-rust.ps1 round5 -Strategy .\ROUND5\strategies\round5_iterative_1.py
.\scripts\bt-rust.ps1 round5 -Strategy .\ROUND5\strategies\round5_iterative_2.py
```

If a portal-window helper exists and official submission logs are available, use it. If no official submission exists yet, portal-window analysis begins only after the first portal submission/log is available.

## Result Tracking

Every meaningful iteration must be logged.

Maintain a table under:

- `ROUND5/research/outputs/iteration_log.csv`

Minimum columns:

- `iteration_id`
- `timestamp`
- `strategy_file`
- `change_summary`
- `hypothesis`
- `products_changed`
- `categories_changed`
- `kevin_full_pnl`
- `xeeshan_full_pnl`
- `rust_full_pnl`
- `portal_window_kevin_pnl`
- `portal_window_xeeshan_pnl`
- `official_portal_score`
- `product_pnl_notes`
- `inventory_notes`
- `fill_quality_notes`
- `risk_notes`
- `accepted`
- `rejection_reason`

If Rust or portal scores are not run, leave those fields blank and explain why.

Also maintain:

- `ROUND5/research/outputs/current_best_table.csv`
- `ROUND5/research/outputs/iteration_notes.md`
- `ROUND5/research/outputs/rejected_ideas.md`

Rejected ideas matter. Record failed experiments so future agents do not repeat them.

## Iteration Cycle

Each improvement cycle should follow this sequence.

### Step 1: Diagnose Before Changing

Before editing, identify the weakest part of the current strategy.

Ask:

- Which products make money?
- Which products lose money?
- Which categories make money?
- Which categories lose money?
- Are losses concentrated by day?
- Are losses concentrated by timestamp block?
- Are losses from bad alpha or bad execution?
- Are losses from inventory pressure?
- Are losses from adverse selection?
- Are losses from too much passivity?
- Are losses from too much aggression?
- Are positions stuck at limits?
- Does Kevin disagree with Xeeshan?
- Does a product only work in one backtester?
- Does a product only work in one day?
- Is a high PnL driven by one isolated event?
- Does the strategy miss obvious opportunities?

Do not change constants blindly. Every change needs a hypothesis.

### Step 2: Build or Refresh Diagnostics

Use or create diagnostics as needed:

Before inventing new diagnostics, reopen `ROUND5/research/round5_learning_plan.md` and specifically review Phases 1 through 6.5. The iterative loop should reuse the full research stack, not only the short menu below. If a strategy failure points back to product statistics, stationarity, category structure, microstructure, execution, regimes, or the open-ended Phase 6.5 research frontier, go back and run the deeper analysis.

Also check `ROUND5/research/outputs/round5_learning_outputs.md` for discoveries, warnings, rejected ideas, and unresolved questions. If the current strategy behavior contradicts that file, investigate the contradiction before changing strategy code.

- Per-product PnL attribution.
- Per-category PnL attribution.
- Timestamp-block PnL attribution.
- Day-level PnL attribution.
- Fill attribution by product, category, side, edge, and order type.
- Passive fill quality.
- Taker trade quality.
- Adverse selection after fills.
- Inventory paths.
- Limit-pressure analysis.
- Rejected order analysis.
- Markouts after fills.
- Fair-value residual analysis.
- Cross-product residual analysis.
- Microstructure signal quality.
- Regime-conditioned performance.
- Kevin-vs-Xeeshan disagreement.
- Official-window vs full-data drift when available.

If a diagnostic is missing, write the script, install the research package, create the visualization, build the feature table, or instrument the backtester. Do not avoid a useful diagnostic because it requires new tooling. Research can be heavy; submitted strategy files must remain lightweight and platform-safe.

### Step 3: Form a Large Enough Hypothesis

Small constant tweaks are not enough unless diagnostics show they matter.

Allowed hypothesis types:

- Add/remove an entire product or category.
- Replace a fair-value model.
- Add a category factor model.
- Add an online residual model.
- Add a regime detector.
- Switch execution from taker to passive or mixed.
- Change inventory skewing.
- Change product selection logic.
- Add cross-product hedging or correlation-aware throttling.
- Add signal confidence buckets.
- Add dynamic thresholds based on spread, volatility, or liquidity.
- Add time-series forecast features.
- Remove a fragile but profitable-looking leg.
- Split strategy behavior by robust, online-detectable regime.
- Change portfolio allocation across products.

Small tuning is allowed after larger structure is right, but do not spend the loop only nudging thresholds.

### Step 4: Edit One Strategy Branch

Make the change in one of:

- `round5_iterative_1.py`
- `round5_iterative_2.py`

Keep branches distinct unless there is a clear reason to transfer a proven idea from one to the other.

Do not let both files collapse into identical strategies too early. Diversity is valuable because hidden final data is unknown.

### Step 5: Backtest

Run Kevin and Xeeshan first.

Capture:

- Total PnL.
- Product PnL.
- Category PnL.
- Day PnL.
- Timestamp-block PnL.
- Inventory summary.
- Fill summary.
- Rejected orders.
- Runtime/platform errors.

If the change looks strong, run additional diagnostics and eventually Rust.

### Step 6: Accept or Reject

Accept a change only if:

- It improves or preserves full-data robustness.
- It does not rely on one tiny window.
- It does not create obvious hidden-test fragility.
- It behaves reasonably in both Kevin and Xeeshan.
- Product-level attribution supports the change.
- Inventory behavior remains controlled.
- Execution quality does not degrade without compensation.
- The economic explanation makes sense.

Reject a change if:

- It improves total PnL by exploiting one public-data artifact.
- It improves one backtester while degrading another materially.
- It increases drawdown or tail risk without enough reward.
- It depends on exact timestamps or known public events.
- It causes unstable inventory limit behavior.
- It makes code too brittle for platform execution.

Record the decision.

## Deep Diagnostic Menu

Use this menu repeatedly. Do not treat it as a one-time checklist.

This menu is a minimum. If it does not explain the current failure mode or opportunity, return to the learning plan, especially Phase 6.5, and design deeper research. Keep drilling down until the behavior is explained well enough to produce an economically justified strategy change or a clear rejection.

### Product and Category Attribution

- PnL by product.
- PnL by category.
- PnL by day.
- PnL by timestamp block.
- PnL by signal bucket.
- PnL by spread bucket.
- PnL by volatility bucket.
- PnL by inventory bucket.
- Fill count by product and side.
- Average edge at entry.
- Average edge at exit.
- Average holding time.
- Limit saturation frequency.

### Inventory and Risk

- Position path by product.
- Maximum long and short inventory.
- Time spent at position limits.
- Time spent near position limits.
- Inventory vs future returns.
- Inventory vs strategy signal.
- Inventory drawdown contribution.
- End-of-window liquidation impact.
- Correlated inventory across categories.
- Worst product/category drawdown.

### Execution

- Passive quote fill rate.
- Passive quote markout.
- Passive quote adverse selection.
- Taker fill count.
- Taker markout.
- Taker edge vs fair value.
- Spread paid vs spread captured.
- Missed fills after signal.
- Overtrading during noisy periods.
- Undertrading during strong signal periods.

### Alpha and Fair Value

- Rolling mean-reversion model.
- Momentum model.
- Microprice model.
- Imbalance model.
- Category factor model.
- Residual z-score model.
- Cointegration spread model.
- PCA/SVD residual model.
- Volatility-adjusted threshold model.
- Liquidity-adjusted threshold model.
- Regime-conditioned model.
- Online Kalman/state-space estimate if useful.

### Statistical and ML Checks

- Train/test by day.
- Walk-forward splits.
- Leave-one-day-out.
- Leave-one-product-out.
- Leave-one-category-out.
- Feature importance stability.
- Regularized regression coefficients.
- Tree-based feature importance.
- Calibration curves.
- Residual diagnostics.
- Error distribution.
- Regime transition stability.
- Sensitivity to thresholds.
- Sensitivity to product inclusion.

### Robustness and Hidden-Test Defense

- Does this edge have a structural reason?
- Does it survive at least two visible days?
- Does it survive block splits?
- Does it survive both major backtesters?
- Does it survive worse execution assumptions?
- Does it require exact public data behavior?
- Is it too concentrated in one product?
- Is it too concentrated in one category?
- Is it too concentrated in one timestamp range?
- Is the strategy still profitable after removing its best product?
- Is the strategy still acceptable after removing its best day?

## Official Portal and Window Handling

At the start of Round 5, no official submission logs exist.

When official submissions become available:

- Save the official zip/json/log under `ROUND5/official_submissions/`.
- Extract the official activities window if possible.
- Compare official portal score with Kevin and Xeeshan replay on that same window.
- Determine whether portal-window proxy aligns with official score.
- Do not assume the portal window equals hidden final distribution.
- Use portal-window analysis to catch platform incompatibility and short-window failure modes.
- Do not optimize only for portal-window ranking.

Create:

- `ROUND5/research/outputs/official_window_summary.csv`
- `ROUND5/research/outputs/official_vs_local_alignment.md`

## Candidate Transfer Between Iterative 1 and Iterative 2

The two iterative branches should remain distinct unless evidence supports merging an idea.

Transfer an idea only when:

- It is structurally justified.
- It improves both branches or clearly complements one branch.
- It survives Kevin and Xeeshan.
- It does not make both strategies fail in the same way.

Do not blindly combine all profitable legs. Some legs interact badly through inventory, order budget, timing, or hidden-test risk.

## Final Selection Criteria

When choosing the final file to submit, rank by:

1. Hidden-test robustness estimate.
2. Full-data Kevin/Xeeshan performance.
3. Cross-backtester agreement.
4. Product/category attribution quality.
5. Day and timestamp-block stability.
6. Execution quality.
7. Inventory control.
8. Portal-window behavior if available.
9. Rust validation if time permits.
10. Code simplicity and platform safety.

The best official-window score is not automatically the best submission if it looks overfit. The best full-data score is not automatically best if it depends on one artifact. Choose the strategy with the strongest total evidence.

## Final Pre-Submission Checklist

Before recommending a submission:

- Strategy imports only platform-safe modules.
- No local file reads.
- No research dependencies inside submitted code unless platform-safe.
- No debug prints that could exceed platform limits.
- No dependency on unavailable packages.
- No previous-round products.
- All 50 products either handled safely or ignored intentionally.
- All position limits are respected.
- Code runs in Kevin.
- Code runs in Xeeshan.
- Code runs in Rust if final validation is requested.
- Product-level PnL is understood.
- Major losses are understood.
- Major wins are understood.
- No obvious hardcoding.
- No obvious overfit.
- Candidate notes and iteration log are updated.

## Stop Condition

Do not stop because one improvement worked.

Stop only when:

- Multiple substantial ideas have been tested.
- Both iterative branches have been improved or deliberately preserved.
- Remaining ideas are either not improving, too fragile, too simulator-specific, or too overfit.
- Product-level and category-level failure modes are understood.
- The final recommendation is defensible under hidden-data uncertainty.

If there is still a credible experiment that could improve robust hidden performance, keep going.
