# Round 5 Learning Plan

This file is a source-of-truth document for the Round 5 research agent. It must be treated as complete operational guidance, not as a loose suggestion.

Round 5 is not a normal continuation of prior rounds. The product universe is new, broad, and intentionally designed so that only some products or categories contain strong exploitable structure. Do not begin by assuming the edge. The first job is to discover the structure of the data at quant-research depth, then build strategies from evidence.

## Primary Objective

Maximize hidden final-round algorithmic PnL while minimizing overfit risk.

The final hidden run is the real target. Portal-window results and public backtests are useful diagnostics, but they are not the objective. Do not optimize to a small portal window if it damages full-data robustness or economic validity.

## Round 5 Source Material

Read these before doing strategy work:

- `ROUND5/round5.md`: Round 5 prompt and product list.
- `ROUND5/prices_round_5_day_2.csv`
- `ROUND5/prices_round_5_day_3.csv`
- `ROUND5/prices_round_5_day_4.csv`
- `ROUND5/trades_round_5_day_2.csv`
- `ROUND5/trades_round_5_day_3.csv`
- `ROUND5/trades_round_5_day_4.csv`
- `algo_guide.md`: Strategy submission format and implementation constraints.
- Existing backtester wrappers in `scripts/`, especially:
  - `scripts/bt-kevin.ps1`
  - `scripts/bt-xeeshan.ps1`
  - `scripts/bt-rust.ps1`
  - `scripts/sync-round-data.ps1`
  - `scripts/package-submission.ps1`

If any file is missing, locate the closest equivalent before proceeding. Do not guess API details when the repo contains a guide or examples.

## Round 5 Product Universe

Only these 50 algorithmic products are tradable. Do not trade previous-round products.

All products have position limit `10`.

### Galaxy Sounds Recorders

- `GALAXY_SOUNDS_DARK_MATTER`
- `GALAXY_SOUNDS_BLACK_HOLES`
- `GALAXY_SOUNDS_PLANETARY_RINGS`
- `GALAXY_SOUNDS_SOLAR_WINDS`
- `GALAXY_SOUNDS_SOLAR_FLAMES`

### Vertical Sleeping Pods

- `SLEEP_POD_SUEDE`
- `SLEEP_POD_LAMB_WOOL`
- `SLEEP_POD_POLYESTER`
- `SLEEP_POD_NYLON`
- `SLEEP_POD_COTTON`

### Organic Microchips

- `MICROCHIP_CIRCLE`
- `MICROCHIP_OVAL`
- `MICROCHIP_SQUARE`
- `MICROCHIP_RECTANGLE`
- `MICROCHIP_TRIANGLE`

### Purification Pebbles

- `PEBBLES_XS`
- `PEBBLES_S`
- `PEBBLES_M`
- `PEBBLES_L`
- `PEBBLES_XL`

### Domestic Robots

- `ROBOT_VACUUMING`
- `ROBOT_MOPPING`
- `ROBOT_DISHES`
- `ROBOT_LAUNDRY`
- `ROBOT_IRONING`

### UV-Visors

- `UV_VISOR_YELLOW`
- `UV_VISOR_AMBER`
- `UV_VISOR_ORANGE`
- `UV_VISOR_RED`
- `UV_VISOR_MAGENTA`

### Instant Translators

- `TRANSLATOR_SPACE_GRAY`
- `TRANSLATOR_ASTRO_BLACK`
- `TRANSLATOR_ECLIPSE_CHARCOAL`
- `TRANSLATOR_GRAPHITE_MIST`
- `TRANSLATOR_VOID_BLUE`

### Construction Panels

- `PANEL_1X2`
- `PANEL_2X2`
- `PANEL_1X4`
- `PANEL_2X4`
- `PANEL_4X4`

### Liquid Breath Oxygen Shakes

- `OXYGEN_SHAKE_MORNING_BREATH`
- `OXYGEN_SHAKE_EVENING_BREATH`
- `OXYGEN_SHAKE_MINT`
- `OXYGEN_SHAKE_CHOCOLATE`
- `OXYGEN_SHAKE_GARLIC`

### Protein Snack Packs

- `SNACKPACK_CHOCOLATE`
- `SNACKPACK_VANILLA`
- `SNACKPACK_PISTACHIO`
- `SNACKPACK_STRAWBERRY`
- `SNACKPACK_RASPBERRY`

Note: if the prompt text has a missing comma between `SNACKPACK_VANILLA` and `SNACKPACK_PISTACHIO`, treat them as two separate products.

## Explicit Non-Goals

- Do not work on the manual Ignith/Ashflow Alpha challenge in this plan.
- Do not start by assuming market making, microstructure alpha, relative value, regime alpha, or ensemble selection.
- Do not create five parameter variants of the same idea.
- Do not optimize purely to a portal-window score.
- Do not hardcode timestamps, day numbers, exact event indices, exact public-data windows, or product behavior that only exists in one visible slice.
- Do not carry over old Round 3 or Round 4 product assumptions.

## Research Philosophy

Think like a quant researcher, not like a contestant trying quick constants.

The correct order is:

1. Understand the raw data and mechanics.
2. Discover stable inefficiencies.
3. Separate alpha from execution.
4. Validate on multiple data partitions.
5. Build diverse strategy candidates from the discovered edges.
6. Backtest and attribute results.
7. Promote only robust candidates to iterative strategy work.

The goal is extreme understanding of product behavior, data-generating structure, microstructure, category relationships, and hidden-test robustness. Use every useful resource available. Use Python packages aggressively. Install additional packages if they materially improve diagnostics or modeling. Generate plots, CSVs, reports, feature tables, and intermediate notebooks/scripts as needed.

Do more than the obvious. If a diagnostic answers one question, ask the next deeper question. If a product looks profitable, identify why. If a product looks noisy, identify whether it is genuinely untradeable or just requires a different representation.

## Allowed Tools and Packages

Use the existing environment first:

- Python
- NumPy
- pandas
- SciPy
- scikit-learn
- statsmodels
- matplotlib
- seaborn if installed
- any already available repo tooling

Install more packages as needed for serious research. Do not use the current environment as a ceiling. If a package, model family, visualization tool, optimizer, statistical test, or data-processing library can plausibly reveal more structure, use it or explicitly record why it was not worth using. The research phase should use maximum effort, not only the packages already installed.

Examples that may be useful:

- `numba` for fast research loops.
- `ruptures` for change-point detection.
- `hmmlearn` or equivalent for hidden Markov models.
- `arch` for volatility modeling.
- `pmdarima` for ARIMA exploration.
- `lightgbm`, `xgboost`, or `catboost` for feature importance and nonlinear diagnostics.
- `polars` for faster table analysis.
- `pyarrow` for faster intermediate storage.
- `networkx` for graph relationships between products.
- `plotly` for interactive inspection if useful.
- `tsfresh` or similar for broad time-series feature extraction if useful.

Additional research-only package categories to consider:

- Bayesian modeling and probabilistic programming if useful.
- Change-point and structural-break libraries.
- Time-series feature extraction libraries.
- Causal/lead-lag discovery tools.
- Robust statistics packages.
- Convex optimization packages for portfolio/risk allocation.
- Signal-processing packages for filters, spectra, and denoising.
- Fast dataframe/query engines for large experiment grids.
- Interactive plotting and dashboard packages.
- Any other package that helps extract market structure from the data.

Heavy research dependencies are allowed. Full machine-learning pipelines are allowed. Large offline model searches are allowed. Expensive analysis scripts are allowed. The only restriction is that submitted strategy files must remain platform-compatible and must not depend on unavailable packages.

## File Discipline

Use these locations:

- Research scripts: `ROUND5/research/`
- Research outputs: `ROUND5/research/outputs/`
- Plots: `ROUND5/research/outputs/plots/`
- Tables: `ROUND5/research/outputs/tables/`
- Model diagnostics: `ROUND5/research/outputs/models/`
- Backtest summaries: `ROUND5/research/outputs/backtests/`
- Main running research notebook/notes file: `ROUND5/research/outputs/round5_learning_outputs.md`
- Candidate strategies: `ROUND5/strategies/round5_candidate_1.py` through `round5_candidate_5.py`
- Final iterative strategies after candidate selection:
  - `ROUND5/strategies/round5_iterative_1.py`
  - `ROUND5/strategies/round5_iterative_2.py`

Candidate filenames must stay neutral. Do not name candidates after assumed strategy families before research proves those families.

## Phase 0: Setup and Data Integrity

Before modeling, verify the dataset.

Checklist:

- Confirm all 50 products appear in price data.
- Confirm all 50 products are recognized by backtesters.
- Confirm position limit is `10` for all products in strategy code and any local config.
- Count rows per product per day.
- Count timestamps per day.
- Validate timestamp spacing and whether all products have rows at all timestamps.
- Check for missing best bid/ask levels.
- Check for crossed books, locked books, negative spreads, zero/invalid prices, missing volumes, duplicated rows.
- Compare price CSV schema with prior rounds.
- Compare trade CSV schema with prior rounds.
- Verify whether trades include market trades only or own-trade-like fields in local replay output.
- Identify products with no trade prints, sparse trade prints, or abnormal quote behavior.

Produce:

- `ROUND5/research/outputs/tables/data_inventory.csv`
- `ROUND5/research/outputs/tables/product_health.csv`
- `ROUND5/research/outputs/data_integrity_notes.md`

## Phase 1: Baseline Market Statistics

For every product and every day, compute:

- Mid-price path.
- Best bid and best ask path.
- Spread mean, median, percentiles, and max.
- Spread distribution by timestamp block.
- Book depth at each visible level.
- Total visible bid volume and ask volume.
- Top-of-book imbalance.
- Multi-level imbalance.
- Weighted mid-price.
- Microprice.
- Return distributions at multiple horizons.
- Realized volatility at multiple horizons.
- Rolling volatility.
- Rolling mean and trend.
- Tail events.
- Jump frequency.
- Quote update frequency.
- Trade count.
- Trade volume.
- Signed trade imbalance if inferable.
- Trade price vs prevailing mid.
- Trade clustering.
- Intraday/time-block seasonality.

Return horizons should include at least:

- 1 timestamp
- 2 timestamps
- 5 timestamps
- 10 timestamps
- 25 timestamps
- 50 timestamps
- 100 timestamps
- 250 timestamps
- 500 timestamps

Use more horizons if the data suggests it.

Produce per-product and category summary tables:

- `basic_stats_by_product.csv`
- `basic_stats_by_category.csv`
- `return_horizon_stats.csv`
- `spread_depth_stats.csv`
- `trade_activity_stats.csv`

Produce plots:

- Mid-price path by product.
- Spread path by product.
- Rolling volatility by product.
- Return histogram by product.
- Category overlays.
- Heatmaps by product and horizon.

## Phase 2: Stationarity, Mean Reversion, and Momentum

For every product:

- Run stationarity-style checks where useful:
  - ADF-style tests.
  - KPSS-style tests.
  - Rolling mean stability.
  - Rolling variance stability.
  - Difference-stationarity vs trend-stationarity checks.
- Compute ACF/PACF of returns.
- Compute ACF/PACF of mid-price deviations from rolling means.
- Estimate half-life of mean reversion where meaningful.
- Test lagged return predictability:
  - Continuation after positive return.
  - Reversal after positive return.
  - Volatility-conditioned continuation/reversal.
  - Spread-conditioned continuation/reversal.
  - Volume-conditioned continuation/reversal.
- Check whether signal direction changes by day.
- Check whether signal direction changes by timestamp block.
- Check whether apparent edges survive leave-one-day-out.

Important:

- A high in-sample Sharpe is not enough.
- The edge must survive multiple splits or have a defensible structural reason.
- If a product is only predictable on one day, flag it as fragile.

Produce:

- `stationarity_tests.csv`
- `autocorrelation_by_product.csv`
- `mean_reversion_half_life.csv`
- `momentum_reversal_tests.csv`
- `signal_stability_by_day.csv`
- `signal_stability_by_block.csv`

## Phase 3: Cross-Sectional and Category Structure

Round 5 has 10 categories of 5 products each. This is likely intentional. Treat categories as potential factor systems, relative-value baskets, ranking groups, or hidden transformations.

For each category:

- Plot all 5 mid-price paths together.
- Normalize each product by initial price, z-score, rolling z-score, and log price.
- Compute correlation matrix of returns.
- Compute correlation matrix of price levels after detrending.
- Compute lead-lag correlations across products.
- Compute pair spreads and basket residuals.
- Fit linear combinations that explain one product using the other four.
- Test if residuals are stationary.
- Test if residuals mean revert.
- Test if one product is a noisy representation of category factor plus idiosyncratic residual.
- Test if category products follow rank ordering.
- Test if product names imply an ordinal structure that appears in data:
  - Pebble sizes.
  - Panel dimensions.
  - Visor colors.
  - Shapes.
  - Materials.
  - Robot tasks.
  - Flavors.
  - Translator colors.
  - Galaxy phenomena.
- Test whether any category has a conservation or basket identity.
- Test if products are cointegrated.

Use linear algebra:

- PCA/SVD on returns.
- PCA/SVD on normalized price levels.
- Eigenvalue spectrum.
- First factor vs residual decomposition.
- Residual z-score analysis.
- Low-rank reconstruction error.
- Category factor loadings.
- Cross-category factor loadings.

Use statistics:

- Pairwise correlation with confidence intervals.
- Rolling correlation.
- Cointegration-style tests where meaningful.
- Residual normality and tail checks.
- Robust regression if outliers dominate.

Produce:

- `category_correlation_matrices.csv`
- `category_pca_summary.csv`
- `category_pair_spreads.csv`
- `category_residual_stationarity.csv`
- `category_lead_lag_tests.csv`
- `category_factor_notes.md`

Produce plots:

- Category price overlays.
- Category normalized overlays.
- Correlation heatmaps.
- PCA explained variance charts.
- Residual z-score paths.
- Pair spread plots.

## Phase 4: Microstructure Alpha

For every product, test whether current order book structure predicts future mid-price movement.

Features:

- Best bid price.
- Best ask price.
- Mid price.
- Spread.
- Best bid volume.
- Best ask volume.
- Top-of-book imbalance.
- Multi-level bid volume.
- Multi-level ask volume.
- Multi-level imbalance.
- Microprice.
- Weighted mid.
- Distance from rolling mean.
- Recent returns.
- Recent volatility.
- Recent trade count.
- Recent trade imbalance if inferable.
- Quote update intensity.
- Spread widening/narrowing.
- Depth replenishment patterns.
- Product/category residual z-score.

Targets:

- Future mid change at multiple horizons.
- Future best bid/ask movement.
- Probability of upward move.
- Probability of downward move.
- Future spread widening/narrowing.
- Future adverse selection after taking or making liquidity.

Models:

- Simple linear regression.
- Ridge/Lasso/ElasticNet.
- Logistic regression.
- Random forest.
- Gradient boosting.
- LightGBM/XGBoost/CatBoost if useful and available.
- Shallow decision trees for interpretable thresholds.
- Quantile regression if useful.
- Nonlinear calibration curves.

Validation:

- Train on day 2, test on day 3 and day 4.
- Train on day 2 and day 3, test on day 4.
- Leave-one-day-out.
- Walk-forward by timestamp blocks.
- Block bootstrap where useful.
- Compare model signs across days.
- Compare feature importance across days.

Do not directly deploy a complex ML model if it cannot be represented safely in the final submitted Python file. Use ML primarily to discover robust patterns and thresholds.

Produce:

- `microstructure_feature_importance.csv`
- `microstructure_predictive_scores.csv`
- `microstructure_signal_stability.csv`
- `imbalance_regression_summary.csv`
- `microprice_edge_summary.csv`

## Phase 5: Execution and Fill Quality Research

Separate alpha from execution. A correct fair value can still lose if execution is wrong.

For each product and candidate execution style:

- Compare taker orders vs passive quotes.
- Measure spread capture.
- Measure adverse selection after fills.
- Measure markout after fills at multiple horizons.
- Measure inventory holding cost.
- Measure limit-pressure frequency.
- Measure missed opportunities due to being too passive.
- Measure losses from crossing spread too aggressively.
- Measure realized edge against fair value at fill time.
- Measure PnL contribution from entry vs exit/liquidation.

Markout horizons:

- Immediate next timestamp.
- 5 timestamps.
- 10 timestamps.
- 25 timestamps.
- 50 timestamps.
- 100 timestamps.
- End of day/window.

Attribution dimensions:

- Product.
- Category.
- Side.
- Passive vs taker.
- Aggression level.
- Signal strength bucket.
- Spread bucket.
- Imbalance bucket.
- Inventory bucket.
- Timestamp block.
- Day.
- Backtester.

Produce:

- `fill_quality_by_product.csv`
- `adverse_selection_by_product.csv`
- `passive_quote_quality.csv`
- `taker_trade_quality.csv`
- `execution_markouts.csv`
- `inventory_pressure_summary.csv`

If the existing backtesters do not expose enough fill detail, instrument them. Instrumentation must not alter matching, scoring, position limits, or strategy behavior.

## Phase 6: Regime, Clustering, and State Models

Look for structure that changes by market state.

Regime candidates:

- High vs low volatility.
- Wide vs tight spread.
- High vs low imbalance.
- Trending vs mean-reverting periods.
- High vs low trade activity.
- Category dislocation vs category equilibrium.
- Time-of-day blocks.
- Day-specific market conditions.
- Product-specific liquidity regimes.
- Hidden shared factor regimes.

Methods:

- K-means or Gaussian mixtures on market-state features.
- Hierarchical clustering of products.
- HDBSCAN/DBSCAN if useful and installed.
- Change-point detection.
- Hidden Markov models if useful.
- Markov transition matrices for discrete regimes.
- Rolling PCA/factor regime analysis.
- State-conditional signal performance.

Questions:

- Does an edge only work in one regime?
- Can the regime be detected online without future leakage?
- Does regime switching improve robustness or just overfit?
- Are transitions stable across days?
- Are product categories moving together under specific states?

Produce:

- `regime_definitions.csv`
- `regime_signal_performance.csv`
- `regime_transition_matrices.csv`
- `product_cluster_summary.csv`
- `change_point_summary.csv`
- `regime_notes.md`

## Phase 6.5: Open-Ended Research Expansion

After Phases 1 through 6, stop following the checklist mechanically and synthesize what has been learned.

This phase exists because the strongest Round 5 edge may not fit any predefined diagnostic. The previous phases are minimum coverage, not a complete research frontier. Use the evidence gathered so far to decide what deserves deeper investigation, then pursue it aggressively.

This is the "do more research" phase.

Instructions:

- Review every anomaly, partial edge, unexplained residual, unstable product, category relationship, regime split, backtester disagreement, and suspiciously profitable/loss-making pattern found so far.
- Ask what the previous phases failed to explain.
- Build new diagnostics that were not listed earlier if they answer a real question.
- Install new packages if they help.
- Use heavy research dependencies if they help.
- Run full ML/statistical/time-series experiments if they help.
- Build visualizations that make structure easier to see.
- Generate intermediate datasets and feature stores if useful.
- Try alternate data representations.
- Try transformations that make hidden structure visible.
- Push deeper into any category that appears intentionally structured.
- Push deeper into any product that looks unusually predictable.
- Push deeper into any product that looks noisy but may be a transformed representation of another signal.
- Do not stop just because the predefined checklist is complete.

Examples of deeper follow-up work:

- If PCA shows one dominant category factor, investigate residual trading, factor timing, and factor-neutral portfolios.
- If residuals mean revert, estimate robust entry/exit bands and half-life stability.
- If residuals trend, test lag structure, continuation horizons, and execution timing.
- If one product leads another, test whether the lead-lag is stable by day and regime.
- If a signal works only during high spread, identify whether spread is a real state variable or an overfit proxy.
- If a product has strange jumps, test event clustering, reversion after jumps, and whether jumps are predictable from book state.
- If a category has ordinal names, test every plausible ordinal mapping and whether deviations from the mapping revert.
- If model performance is nonlinear, use tree/boosting models to identify thresholds and interactions.
- If ML feature importance is unstable, identify which features are robust enough to encode manually.
- If fill quality is poor despite good alpha, redesign execution rather than discarding the alpha.
- If Kevin and Xeeshan disagree, isolate exactly which fills, products, or timestamps create the disagreement.
- If all obvious alphas are weak, search for portfolio-level edges, product selection edges, or execution-only edges.

Advanced methods to consider:

- PCA/SVD and robust PCA.
- Sparse factor models.
- Cointegration and residual error-correction models.
- Kalman filtering and state-space estimates.
- Hidden Markov models and explicit regime transition models.
- Change-point detection.
- Spectral analysis and filtering.
- Wavelet or multi-scale decomposition if useful.
- Robust regression and quantile regression.
- Bayesian shrinkage where sample sizes are limited.
- Graph-based product relationship models.
- Community detection on product correlation/lead-lag networks.
- Mutual information and nonlinear dependence tests.
- Regularized supervised learning.
- Gradient boosting and random forests for feature discovery.
- Walk-forward model selection.
- Block bootstrap robustness checks.
- Stress tests with degraded execution assumptions.
- Sensitivity maps over model parameters.
- Portfolio optimization with shrinkage covariance.
- Online-learning approximations that can be implemented safely in final code.

Record this phase in:

- `ROUND5/research/outputs/round5_learning_outputs.md`

That file should summarize:

- What the earlier phases revealed.
- What extra questions were asked.
- What extra packages/tools were used or installed.
- What deeper experiments were run.
- What was discovered.
- Which discoveries are robust.
- Which discoveries are suspicious or overfit-prone.
- Which discoveries should become strategy candidates.
- Which discoveries should be rejected.

This phase should end with a clear, evidence-backed list of candidate edges. Only then proceed to portfolio/risk research and candidate strategy design.

## Phase 7: Portfolio and Risk Research

Position limit is small (`10`), but there are 50 products. Portfolio construction matters.

Analyze:

- Product-level expected edge.
- Product-level risk.
- Category-level risk.
- Correlation of PnL streams.
- Concentration risk.
- Simultaneous inventory pressure.
- Worst timestamp-block drawdowns.
- Tail loss events.
- Strategy behavior when many signals fire at once.
- Opportunity cost of allocating order bandwidth to weak products.
- Whether trading all products dilutes edge.
- Whether cherry-picking a subset improves hidden robustness.

Use:

- Covariance matrices.
- Shrinkage covariance if useful.
- PCA of strategy PnL.
- Risk-adjusted product ranking.
- Robust product selection.
- Leave-one-product-out and leave-one-category-out tests.
- Stress tests with worse fills, wider spreads, and delayed exits.

Produce:

- `product_edge_ranking.csv`
- `category_edge_ranking.csv`
- `portfolio_correlation.csv`
- `strategy_risk_summary.csv`
- `drawdown_by_product.csv`
- `selection_notes.md`

## Phase 8: Candidate Strategy Design

Only after the research pass should strategy candidates be designed.

Create exactly five initial candidate strategies:

- `ROUND5/strategies/round5_candidate_1.py`
- `ROUND5/strategies/round5_candidate_2.py`
- `ROUND5/strategies/round5_candidate_3.py`
- `ROUND5/strategies/round5_candidate_4.py`
- `ROUND5/strategies/round5_candidate_5.py`

The five candidates must be meaningfully different. They should not be five parameter variants of the same idea.

However, do not pre-label them by assumed style. Let the research determine what each candidate is. If the data reveals five versions of relative value are the only serious ideas, that is acceptable only if they are structurally different. If the data reveals one category dominates and others are noise, candidates can focus differently around that discovery. Evidence comes first.

For each candidate, create a short companion note:

- `ROUND5/research/outputs/candidate_1_notes.md`
- `ROUND5/research/outputs/candidate_2_notes.md`
- `ROUND5/research/outputs/candidate_3_notes.md`
- `ROUND5/research/outputs/candidate_4_notes.md`
- `ROUND5/research/outputs/candidate_5_notes.md`

Each note must answer:

- What edge does this strategy exploit?
- Which products/categories does it trade?
- Why should the edge persist on hidden data?
- What data supports the edge?
- What are the primary risks?
- What would make this strategy fail?
- What backtest result would invalidate it?
- What is the expected execution style?
- How does it control inventory?
- How does it avoid overfitting?

## Phase 9: Backtesting Protocol for Five Candidates

Run Kevin and Xeeshan first. Use Rust later for finalists.

Typical commands:

```powershell
.\scripts\bt-kevin.ps1 round5 -Strategy .\ROUND5\strategies\round5_candidate_1.py
.\scripts\bt-xeeshan.ps1 round5 -Strategy .\ROUND5\strategies\round5_candidate_1.py
```

Repeat for candidates 1 through 5.

Capture:

- Total PnL.
- Product-level PnL.
- Category-level PnL.
- Day-level PnL.
- Timestamp-block PnL.
- Inventory extrema.
- Fill count by product and side.
- Rejected order count if available.
- Position-limit pressure.
- Kevin vs Xeeshan disagreement.
- Runtime errors and platform compatibility issues.

Produce:

- `candidate_backtest_matrix.csv`
- `candidate_product_pnl.csv`
- `candidate_category_pnl.csv`
- `candidate_day_pnl.csv`
- `candidate_timestamp_block_pnl.csv`
- `candidate_inventory_summary.csv`
- `candidate_disagreement_notes.md`

## Phase 10: Promotion to Iterative Strategies

Pick the two best candidates using a robust blend:

- Strong full-data PnL.
- Strong Kevin/Xeeshan agreement.
- Product-level PnL that is not dependent on one tiny window.
- Day-level stability.
- Timestamp-block stability.
- Economic explanation.
- Low overfit risk.
- Sensible inventory behavior.
- No obvious hardcoding.
- No fragile dependence on exact public-data artifacts.

Then copy them to:

- `ROUND5/strategies/round5_iterative_1.py`
- `ROUND5/strategies/round5_iterative_2.py`

The detailed improvement loop after that is defined in `ROUND5/research/round5_iterative_learning_loop.md`.

## Anti-Overfit Rules

Reject or flag any idea that:

- Only works on one day without a structural explanation.
- Only works in one timestamp window.
- Requires exact timestamp thresholds copied from public data.
- Requires exact day-specific constants.
- Uses exact product constants that are not statistically stable.
- Is extremely sensitive to one parameter.
- Wins one backtester and fails another without explanation.
- Generates most PnL from one isolated event.
- Improves total PnL while worsening hidden-robustness indicators.
- Looks profitable only because of end-of-day liquidation quirks.

Allowed:

- Product-specific models.
- Category-specific models.
- Different thresholds by product if justified by stable volatility, spread, liquidity, or factor structure.
- Online regime detection using only current and past information.
- Precomputed constants learned from historical data if they represent stable structural parameters and are validated across days.

Not allowed:

- Future leakage.
- Data-window leakage.
- Portal-window memorization.
- Exact timestamp scripts.
- Submission-result chasing without an economic reason.

## Minimum Research Deliverables Before Candidate Strategies

Do not write the five candidates until these exist:

- Data inventory and health checks.
- Product/category statistics.
- Return horizon diagnostics.
- Spread/depth/liquidity diagnostics.
- Stationarity and autocorrelation diagnostics.
- Category relationship diagnostics.
- Microstructure predictive diagnostics.
- Execution/fill quality plan or instrumentation plan.
- Regime/clustering diagnostics.
- Product/category edge ranking.
- Clear notes on likely exploitable structures.

If time pressure exists, compress the research into fewer scripts, but do not skip the thinking.

## Final Instruction

This plan is intentionally broad. It is not the ceiling. If another diagnostic, package, model, plot, transformation, or statistical test can produce better understanding of the 50-product market, use it. Keep going deeper until the product structure is understood well enough that the five candidate strategies are evidence-driven rather than guessed.
