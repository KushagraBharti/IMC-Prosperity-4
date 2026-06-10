# Round 5 Research Exhaustion Checklist

Status: complete within the current instruction boundary.

Completed:

- Data integrity and health checks across all 50 products and all visible days.
- Baseline statistics, spread/depth/trade activity, return horizons, volatility, and category summaries.
- Stationarity, autocorrelation, half-life, momentum/reversal, day stability, and block stability diagnostics.
- Category/cross-sectional work: PCA, residual models, pair spreads, cointegration checks, lead-lag, graph communities, and ordinal checks.
- Microstructure diagnostics: split ridge models, tree feature importance, bucketed signal stability, microprice/imbalance summaries.
- Execution proxies: trade-vs-mid, markouts, passive/taker quality proxies, inventory pressure, and spread/volatility stress.
- Regime work: KMeans states, sampled HMM states, transition tables, product clustering, and change-point summaries.
- Mandatory Phase 6.5 expansion: factor residuals, nonlinear threshold maps, graph structure, GARCH summaries, hidden-robustness screens.
- Additional extension pass: Pebbles leave-one-day residual validation, cost-stressed signal grid, leave-one-day ML stability, category exclusion risk.
- Nested validation pass: train on two days, select signal/window/horizon/threshold/cost settings, test on held-out day for every product.
- Candidate-direction evidence matrix without creating strategy candidate files.

Remaining items that cannot be resolved without entering the next phase:

- Exact strategy fill behavior in Kevin/Xeeshan/Rust requires actual candidate strategy files.
- Product-level realized PnL, inventory paths, rejected orders, and simulator disagreement require candidate backtests.
- Portal-window compatibility requires an official Round 5 submission log, which is not present.

Do not do more pre-candidate research unless new data, official logs, or a specific anomaly from candidate backtests appears. The next meaningful step is to design the five neutral candidates required by the learning plan.
