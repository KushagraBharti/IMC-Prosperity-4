# Round 5 Learning Outputs

Objective correction applied: portal logs are compatibility and portal-window alignment evidence only. The research target is hidden final-round robustness.

## Executed Phases

- Phase 0 data integrity/product health: complete.
- Phase 1 baseline market statistics: complete.
- Phase 2 stationarity/mean-reversion/momentum: complete.
- Phase 3 category/cross-sectional structure: complete.
- Phase 4 microstructure alpha: complete using linear, tree, bucket, and split diagnostics.
- Phase 5 execution/fill quality: complete as market-trade/quote-state proxies; no strategy backtests were run because candidate files are intentionally not created yet.
- Phase 6 regimes/clustering/state models: complete with KMeans, optional HMM, change-point, and product clustering diagnostics.
- Phase 6.5 open-ended expansion: complete with graph communities, factor-residual screens, nonlinear threshold maps, hidden-robustness edge screens, and optional GARCH diagnostics.
- Phase 7 portfolio/risk: complete with edge rankings, correlation, drawdown, and risk summaries.

## Key Output Tables

- `tables/data_inventory.csv`, `product_health.csv`, `basic_stats_by_product.csv`, `basic_stats_by_category.csv`
- `tables/return_horizon_stats.csv`, `spread_depth_stats.csv`, `trade_activity_stats.csv`
- `tables/stationarity_tests.csv`, `autocorrelation_by_product.csv`, `mean_reversion_half_life.csv`, `momentum_reversal_tests.csv`
- `tables/category_correlation_matrices.csv`, `category_pca_summary.csv`, `category_pair_spreads.csv`, `category_residual_stationarity.csv`, `category_lead_lag_tests.csv`
- `tables/microstructure_predictive_scores.csv`, `microstructure_feature_importance.csv`, `microstructure_signal_stability.csv`
- `tables/fill_quality_by_product.csv`, `execution_markouts.csv`, `passive_quote_quality.csv`, `taker_trade_quality.csv`, `inventory_pressure_summary.csv`
- `tables/regime_signal_performance.csv`, `product_cluster_summary.csv`, `change_point_summary.csv`
- `tables/phase65_*`, `product_edge_ranking.csv`, `category_edge_ranking.csv`, `portfolio_correlation.csv`, `strategy_risk_summary.csv`

## Robust Edge Screens

| product                     | category     | signal       |   edge_mean |   positive_days |   positive_blocks |   robust_score |
|:----------------------------|:-------------|:-------------|------------:|----------------:|------------------:|---------------:|
| PEBBLES_XL                  | PEBBLES      | z50_revert   |    1.8491   |               3 |                 7 |        3.8831  |
| ROBOT_DISHES                | ROBOT        | z50_revert   |    2.74945  |               2 |                 9 |        3.69041 |
| PEBBLES_XS                  | PEBBLES      | z50_revert   |    1.78195  |               3 |                 6 |        3.20751 |
| OXYGEN_SHAKE_EVENING_BREATH | OXYGEN_SHAKE | z50_revert   |    1.21846  |               3 |                 8 |        2.92429 |
| ROBOT_DISHES                | ROBOT        | past5_revert |    1.67748  |               2 |                 9 |        2.90395 |
| OXYGEN_SHAKE_MORNING_BREATH | OXYGEN_SHAKE | z50_revert   |    0.990899 |               3 |                 8 |        2.37816 |
| OXYGEN_SHAKE_MORNING_BREATH | OXYGEN_SHAKE | past5_revert |    0.849942 |               3 |                 9 |        2.29484 |
| SNACKPACK_STRAWBERRY        | SNACKPACK    | z50_revert   |    0.938049 |               3 |                 8 |        2.25132 |
| SNACKPACK_RASPBERRY         | SNACKPACK    | z50_revert   |    0.825368 |               3 |                 8 |        1.98088 |
| PEBBLES_L                   | PEBBLES      | past5_revert |    0.919446 |               3 |                 6 |        1.655   |
| OXYGEN_SHAKE_EVENING_BREATH | OXYGEN_SHAKE | past5_revert |    0.759022 |               3 |                 7 |        1.59395 |
| TRANSLATOR_VOID_BLUE        | TRANSLATOR   | z50_revert   |    0.854089 |               3 |                 6 |        1.53736 |

## Factor/Residual Follow-Ups

| category     | product                     |   contrarian_future10_edge_all |   day_edge_mean |   stable_positive_days |
|:-------------|:----------------------------|-------------------------------:|----------------:|-----------------------:|
| OXYGEN_SHAKE | OXYGEN_SHAKE_EVENING_BREATH |                       1.28585  |        1.28765  |                      3 |
| PEBBLES      | PEBBLES_XS                  |                       1.20071  |        1.20129  |                      3 |
| PANEL        | PANEL_2X2                   |                       0.496157 |        0.495452 |                      3 |
| PEBBLES      | PEBBLES_XL                  |                       4.55334  |        4.54401  |                      2 |
| ROBOT        | ROBOT_LAUNDRY               |                       0.66465  |        0.667663 |                      2 |
| PEBBLES      | PEBBLES_M                   |                       0.668009 |        0.665487 |                      2 |
| TRANSLATOR   | TRANSLATOR_VOID_BLUE        |                       0.513051 |        0.514477 |                      2 |
| PEBBLES      | PEBBLES_S                   |                       0.494552 |        0.491044 |                      2 |
| TRANSLATOR   | TRANSLATOR_GRAPHITE_MIST    |                       0.468417 |        0.468655 |                      2 |
| OXYGEN_SHAKE | OXYGEN_SHAKE_CHOCOLATE      |                       0.458641 |        0.457261 |                      2 |
| MICROCHIP    | MICROCHIP_RECTANGLE         |                       0.401775 |        0.404534 |                      2 |
| PEBBLES      | PEBBLES_L                   |                       0.404866 |        0.401979 |                      2 |

## Pair/Cointegration Follow-Ups

| category     | product_a              | product_b            |   price_corr |   return_corr |   spread_adf_p |   cointegration_p |
|:-------------|:-----------------------|:---------------------|-------------:|--------------:|---------------:|------------------:|
| MICROCHIP    | MICROCHIP_SQUARE       | MICROCHIP_RECTANGLE  |    -0.882298 |    0.00611692 |     0.307814   |         0.0274192 |
| SNACKPACK    | SNACKPACK_PISTACHIO    | SNACKPACK_STRAWBERRY |    -0.441237 |    0.913295   |     0.101959   |         0.031346  |
| SNACKPACK    | SNACKPACK_CHOCOLATE    | SNACKPACK_STRAWBERRY |    -0.541036 |    0.0168037  |     0.257322   |         0.0356068 |
| SNACKPACK    | SNACKPACK_CHOCOLATE    | SNACKPACK_PISTACHIO  |     0.470438 |    0.0248877  |     0.00420899 |         0.0452653 |
| SNACKPACK    | SNACKPACK_VANILLA      | SNACKPACK_PISTACHIO  |    -0.313141 |    0.0396869  |     0.145253   |         0.0540195 |
| MICROCHIP    | MICROCHIP_OVAL         | MICROCHIP_TRIANGLE   |     0.870459 |    0.00193169 |     0.30619    |         0.0610404 |
| ROBOT        | ROBOT_VACUUMING        | ROBOT_LAUNDRY        |     0.787417 |   -0.00194848 |     0.0185052  |         0.0701374 |
| SLEEP_POD    | SLEEP_POD_LAMB_WOOL    | SLEEP_POD_NYLON      |     0.493173 |    0.00315638 |     0.044789   |         0.0752795 |
| UV_VISOR     | UV_VISOR_AMBER         | UV_VISOR_MAGENTA     |    -0.867276 |    0.00616499 |     0.308445   |         0.0776371 |
| SNACKPACK    | SNACKPACK_VANILLA      | SNACKPACK_STRAWBERRY |     0.284329 |    0.0311008  |     0.0570348  |         0.0782944 |
| ROBOT        | ROBOT_VACUUMING        | ROBOT_DISHES         |    -0.686489 |    0.005338   |     0.90072    |         0.0977215 |
| OXYGEN_SHAKE | OXYGEN_SHAKE_CHOCOLATE | OXYGEN_SHAKE_GARLIC  |     0.645802 |    0.00676993 |     0.0256871  |         0.0978475 |

## Microstructure Predictive Evidence

| product                  | category     |   horizon | split     | model   |          r2 |   direction_accuracy |   prediction_actual_corr |
|:-------------------------|:-------------|----------:|:----------|:--------|------------:|---------------------:|-------------------------:|
| ROBOT_DISHES             | ROBOT        |         1 | d23_to_d4 | ridge   |  0.00773103 |             0.594966 |                0.266628  |
| ROBOT_DISHES             | ROBOT        |         1 | d2_to_d4  | ridge   |  0.00987551 |             0.581236 |                0.387922  |
| SNACKPACK_VANILLA        | SNACKPACK    |        50 | d2_to_d3  | ridge   |  0.0296906  |             0.566095 |                0.173135  |
| SNACKPACK_RASPBERRY      | SNACKPACK    |        50 | d2_to_d3  | ridge   |  0.00599203 |             0.56143  |                0.156067  |
| SNACKPACK_CHOCOLATE      | SNACKPACK    |        50 | d2_to_d3  | ridge   |  0.00758551 |             0.558432 |                0.170202  |
| ROBOT_IRONING            | ROBOT        |         1 | d23_to_d4 | ridge   |  0.0170662  |             0.558127 |                0.149101  |
| SNACKPACK_CHOCOLATE      | SNACKPACK    |        25 | d2_to_d3  | ridge   |  0.0151033  |             0.558122 |                0.158612  |
| TRANSLATOR_GRAPHITE_MIST | TRANSLATOR   |        50 | d2_to_d4  | ridge   | -0.0297428  |             0.557178 |                0.0432765 |
| MICROCHIP_TRIANGLE       | MICROCHIP    |        50 | d2_to_d3  | ridge   | -0.0294388  |             0.550912 |                0.0997719 |
| SLEEP_POD_NYLON          | SLEEP_POD    |        50 | d2_to_d3  | ridge   | -0.0116744  |             0.548484 |                0.0755464 |
| SNACKPACK_VANILLA        | SNACKPACK    |        25 | d2_to_d3  | ridge   |  0.0195768  |             0.548087 |                0.144338  |
| OXYGEN_SHAKE_CHOCOLATE   | OXYGEN_SHAKE |        50 | d2_to_d3  | ridge   |  0.012325   |             0.547905 |                0.157635  |

## Health And Coverage

- Products with zero market trades across visible days: none.
- Locked/crossed/duplicated timestamp health flags: 0 product-day rows.

## Rejected Or Fragile Ideas

| product                   | category      | signal           |   edge_mean |   positive_days |   positive_blocks |   min_day_edge |
|:--------------------------|:--------------|:-----------------|------------:|----------------:|------------------:|---------------:|
| OXYGEN_SHAKE_CHOCOLATE    | OXYGEN_SHAKE  | z50_revert       |   0.461136  |               2 |                 4 |   -1.0415      |
| MICROCHIP_OVAL            | MICROCHIP     | past5_revert     |   0.364213  |               1 |                 4 |   -0.891487    |
| PEBBLES_XS                | PEBBLES       | past5_revert     |   0.237273  |               1 |                 4 |   -0.507661    |
| OXYGEN_SHAKE_GARLIC       | OXYGEN_SHAKE  | z50_revert       |   0.22805   |               1 |                 6 |   -0.0783489   |
| GALAXY_SOUNDS_SOLAR_WINDS | GALAXY_SOUNDS | z50_revert       |   0.120429  |               1 |                 5 |   -0.125639    |
| SLEEP_POD_SUEDE           | SLEEP_POD     | z50_revert       |   0.119577  |               1 |                 5 |   -0.622733    |
| PEBBLES_M                 | PEBBLES       | z50_revert       |   0.11208   |               1 |                 5 |   -0.423204    |
| PANEL_2X4                 | PANEL         | z50_revert       |   0.100224  |               1 |                 6 |   -0.411482    |
| SLEEP_POD_SUEDE           | SLEEP_POD     | past5_revert     |   0.0649474 |               1 |                 5 |   -0.425638    |
| MICROCHIP_TRIANGLE        | MICROCHIP     | past5_momentum   |   0.0566183 |               1 |                 4 |   -0.597046    |
| SLEEP_POD_NYLON           | SLEEP_POD     | z50_revert       |   0.0533514 |               2 |                 4 |   -0.398457    |
| TRANSLATOR_ASTRO_BLACK    | TRANSLATOR    | imbalance_follow |   0.0522856 |               2 |                 4 |   -0.000900901 |

## Candidate-Worthy Directions

- Direction A: product-specific microstructure signals only where day/block stability is positive and feature signs agree across splits.
- Direction B: category factor/residual trading for categories with stationary residuals and stable contrarian residual edge.
- Direction C: product subset/cherry-picking using robust edge ranking, with explicit exclusion of weak/noisy products rather than trading all 50.
- Direction D: regime-conditioned throttling when regime diagnostics show a signal works in detectable high-spread/high-volatility/liquidity states and fails elsewhere.
- Direction E: execution-first passive/taker mix based on spread-to-volatility, trade markouts, and adverse-selection proxies.

## Additional Review Findings

- Strongest broad mean-reversion screens are in `PEBBLES`, `OXYGEN_SHAKE`, `ROBOT`, and selected `SNACKPACK`/`TRANSLATOR` products. These are not uniformly category-wide; product selection matters.
- `PEBBLES` is structurally exceptional: all five products are almost perfectly explained by the other four, residuals are stationary, and the Phase 6.5 graph puts all five in one community. This is the cleanest category-factor/residual system.
- `SNACKPACK` has the strongest return PCA factor, but it splits into two correlation communities: `PISTACHIO/RASPBERRY/STRAWBERRY` and `CHOCOLATE/VANILLA`. Treating all five as one basket is probably too crude.
- Lead-lag correlations are weak. The top absolute lead-lag result is about 0.05, so lead-lag should be secondary unless a candidate backtest proves execution timing value.
- Several nonlinear threshold maps are stable across all three days, especially `roll_z_50` / `past_mid_diff_5` thresholds in `SLEEP_POD_LAMB_WOOL`, `SLEEP_POD_COTTON`, `GALAXY_SOUNDS_BLACK_HOLES`, `GALAXY_SOUNDS_PLANETARY_RINGS`, and `MICROCHIP_TRIANGLE`. These need caution because they did not all rank highly in the simpler hidden-robustness screen.
- Weakest best-product screens include `PANEL_1X4`, `PEBBLES_M`, `MICROCHIP_SQUARE`, `TRANSLATOR_ASTRO_BLACK`, and `PANEL_4X4`. These are avoid-first unless needed as hedges or residual legs.
- `MICROCHIP_SQUARE` has high volatility and some pair/cointegration hints, but edge screens are weak/fragile. It is a risk candidate, not a primary edge candidate yet.
- Market-trade markouts show large product/day effects, especially in `PEBBLES` and `MICROCHIP`, but many are day-specific. Use as execution-risk evidence, not direct alpha proof.

## Unresolved Questions

- Exact fill behavior remains unknown until candidate strategies are backtested; Phase 5 used market-trade and quote-state proxies only.
- Portal-window compatibility cannot be assessed because no Round 5 official submission logs are present beyond the placeholder README.
- Any deployable constants must be rechecked during candidate backtests for sensitivity and hidden-robustness risk.
- The strongest Phase 6.5 screens are candidate directions, not final strategy decisions.

## Extension Pass Findings

Additional research was run because the first pass still had useful unresolved questions around residual stability, cost-stressed signal robustness, and model stability.

New tables:

- `extension_pebbles_leave_day_residuals.csv`
- `extension_pebbles_leave_day_coefficients.csv`
- `extension_pebbles_pair_spread_stability.csv`
- `extension_signal_parameter_sensitivity.csv`
- `extension_cost_stressed_robust_signals.csv`
- `extension_leave_one_day_ml_scores.csv`
- `extension_leave_one_day_feature_importance.csv`
- `extension_ridge_feature_sign_stability.csv`
- `extension_category_exclusion_risk.csv`

Top cost-stressed robust signal screens:

| product    | category   | signal   | feature    |   horizon |   threshold |   cost_mult |   active_rate |   net_edge_mean |   positive_days |   positive_blocks |   robust_score |
|:-----------|:-----------|:---------|:-----------|----------:|------------:|------------:|--------------:|----------------:|----------------:|------------------:|---------------:|
| PEBBLES_XL | PEBBLES    | z_revert | roll_z_500 |       100 |        2    |         0.5 |      0.134    |         73.9471 |               3 |                18 |        66.5524 |
| PEBBLES_XL | PEBBLES    | z_revert | roll_z_500 |       100 |        2    |         1   |      0.134    |         69.7678 |               3 |                18 |        62.791  |
| PEBBLES_XL | PEBBLES    | z_revert | roll_z_500 |       100 |        1.5  |         0.5 |      0.294732 |         58.031  |               3 |                17 |        49.3264 |
| PEBBLES_XL | PEBBLES    | z_revert | roll_z_500 |       100 |        1.5  |         1   |      0.294732 |         53.8637 |               3 |                17 |        45.7841 |
| PEBBLES_XL | PEBBLES    | z_revert | roll_z_500 |       100 |        1    |         0.5 |      0.541986 |         41.695  |               3 |                17 |        35.4407 |
| PEBBLES_XL | PEBBLES    | z_revert | roll_z_500 |        50 |        2    |         0.5 |      0.133726 |         40.4794 |               3 |                16 |        32.3836 |
| PEBBLES_XL | PEBBLES    | z_revert | roll_z_500 |       100 |        1    |         1   |      0.541986 |         37.5299 |               3 |                17 |        31.9004 |
| PEBBLES_XL | PEBBLES    | z_revert | roll_z_500 |       100 |        0.75 |         0.5 |      0.660511 |         35.9096 |               3 |                16 |        28.7276 |
| PEBBLES_XL | PEBBLES    | z_revert | roll_z_50  |       100 |        2    |         0.5 |      0.130118 |         36.6668 |               3 |                15 |        27.5001 |
| PEBBLES_XL | PEBBLES    | z_revert | roll_z_500 |        50 |        2    |         1   |      0.133726 |         36.2976 |               3 |                15 |        27.2232 |
| PEBBLES_XL | PEBBLES    | z_revert | roll_z_500 |        50 |        1.5  |         0.5 |      0.295165 |         33.857  |               3 |                16 |        27.0856 |
| PEBBLES_XL | PEBBLES    | z_revert | roll_z_500 |       100 |        0.75 |         1   |      0.660511 |         31.7373 |               3 |                16 |        25.3898 |

`PEBBLES` leave-one-day residual validation:

| target     |   test_day |       r2 |   resid_std |   resid_adf_p |   future10_contrarian_edge |
|:-----------|-----------:|---------:|------------:|--------------:|---------------------------:|
| PEBBLES_XL |          4 | 0.999996 |     2.82227 |             0 |                  0.919319  |
| PEBBLES_XL |          2 | 0.999996 |     2.81544 |             0 |                  1.18919   |
| PEBBLES_M  |          3 | 0.999986 |     2.75922 |             0 |                 -1.01922   |
| PEBBLES_L  |          4 | 0.999985 |     2.82189 |             0 |                 -0.284735  |
| PEBBLES_XS |          3 | 0.999984 |     2.75871 |             0 |                  0.916066  |
| PEBBLES_XL |          3 | 0.99998  |     2.75892 |             0 |                  0.374374  |
| PEBBLES_XS |          2 | 0.999979 |     2.81565 |             0 |                 -0.68964   |
| PEBBLES_L  |          2 | 0.999969 |     2.81541 |             0 |                  0.199299  |
| PEBBLES_S  |          4 | 0.999968 |     2.82144 |             0 |                  0.0851852 |
| PEBBLES_XS |          4 | 0.999967 |     2.8225  |             0 |                  0.0033033 |

Best leave-one-day ML diagnostics:

| product                  | category   |   test_day | model          |           r2 |   pred_actual_corr |   direction_accuracy |
|:-------------------------|:-----------|-----------:|:---------------|-------------:|-------------------:|---------------------:|
| PEBBLES_XS               | PEBBLES    |          3 | ridge_lodo     |  0.00165008  |          0.0494966 |             0.530881 |
| SLEEP_POD_COTTON         | SLEEP_POD  |          2 | ridge_lodo     |  0.000531254 |          0.0419611 |             0.522442 |
| PEBBLES_L                | PEBBLES    |          3 | ridge_lodo     | -0.001646    |          0.0307467 |             0.521093 |
| MICROCHIP_OVAL           | MICROCHIP  |          2 | rf_depth4_lodo | -0.00878946  |         -0.0518528 |             0.520792 |
| SLEEP_POD_COTTON         | SLEEP_POD  |          4 | ridge_lodo     |  0.000983936 |          0.0445624 |             0.519455 |
| MICROCHIP_OVAL           | MICROCHIP  |          2 | ridge_lodo     | -0.00857372  |         -0.0194322 |             0.519142 |
| SLEEP_POD_NYLON          | SLEEP_POD  |          3 | rf_depth4_lodo |  0.000726737 |          0.0515389 |             0.519069 |
| TRANSLATOR_GRAPHITE_MIST | TRANSLATOR |          4 | ridge_lodo     |  0.00104264  |          0.049474  |             0.517792 |
| UV_VISOR_YELLOW          | UV_VISOR   |          3 | ridge_lodo     |  0.00164212  |          0.0488815 |             0.517381 |
| UV_VISOR_MAGENTA         | UV_VISOR   |          3 | ridge_lodo     |  0.00543861  |          0.0749081 |             0.517044 |

Category exclusion risk from top stressed screens:

| excluded_category   |   remaining_products |   remaining_score_sum |   remaining_edge_mean |   lost_score |
|:--------------------|---------------------:|----------------------:|----------------------:|-------------:|
| PEBBLES             |                   27 |               181.552 |               9.68005 |     82.7775  |
| ROBOT               |                   24 |               214.704 |              12.3825  |     49.6257  |
| TRANSLATOR          |                   25 |               230.017 |              12.4577  |     34.3121  |
| PANEL               |                   25 |               239.194 |              12.9309  |     25.1354  |
| UV_VISOR            |                   26 |               243.026 |              12.6398  |     21.3032  |
| MICROCHIP           |                   26 |               244.511 |              12.71    |     19.8182  |
| OXYGEN_SHAKE        |                   26 |               252.915 |              13.1304  |     11.4143  |
| SLEEP_POD           |                   27 |               253.716 |              12.71    |     10.6135  |
| SNACKPACK           |                   27 |               259.111 |              13.0212  |      5.21802 |
| GALAXY_SOUNDS       |                   28 |               260.218 |              12.6409  |      4.11118 |

Updated interpretation:

- `PEBBLES` residual structure survives leave-one-day fitting with extremely high R2 and stationary residuals. This is now the best-evidenced category-structure direction.
- Cost-stressed screens still favor selective mean reversion, but the exact signal/window/horizon matters. This argues for candidate diversity and sensitivity-aware thresholds, not one fixed global rule.
- ML remains diagnostic, not a direct deployment plan. Leave-one-day models show pockets of directionality, but not enough broad accuracy to justify a heavy model-family assumption.
- Category exclusion risk confirms concentration: removing `PEBBLES`, `OXYGEN_SHAKE`, or selected `ROBOT`/`SNACKPACK` structures costs most of the robust-screen score; many other categories are optional unless used for diversification.
- Remaining unresolved item is exact simulator fill behavior, which cannot be settled until neutral candidate strategies are written and backtested. The research evidence base is otherwise materially stronger than the initial pass.

## Nested Validation Addendum

A further nested validation pass was run after the extension exposed a possible parameter-selection artifact. For each product and held-out day, signal/window/horizon/threshold/cost settings were selected only on the other two days, then evaluated on the held-out day.

New tables:

- `extension_nested_signal_selection.csv`
- `extension_nested_signal_product_summary.csv`
- `extension_nested_top_train_combos.csv`

Best product summaries by held-out-day performance:

| product                  | category     |   mean_test_edge |   min_test_edge |   positive_test_days |   mean_train_edge |   overfit_ratio | selected_signals                          |
|:-------------------------|:-------------|-----------------:|----------------:|---------------------:|------------------:|----------------:|:------------------------------------------|
| ROBOT_LAUNDRY            | ROBOT        |         24.5514  |       2.74777   |                    3 |          24.4672  |        1.00344  | past_revert|past_revert|past_revert       |
| TRANSLATOR_GRAPHITE_MIST | TRANSLATOR   |         21.3209  |       3.07721   |                    3 |          20.2245  |        1.05421  | past_revert|past_revert|past_revert       |
| PEBBLES_L                | PEBBLES      |         18.0301  |       0.848943  |                    3 |          18.5866  |        0.970057 | past_momentum|past_momentum|past_momentum |
| TRANSLATOR_ASTRO_BLACK   | TRANSLATOR   |         16.6823  |       3.51099   |                    3 |          16.4595  |        1.01353  | z_revert|z_revert|z_revert                |
| ROBOT_IRONING            | ROBOT        |          8.77883 |       7.46308   |                    3 |          16.8072  |        0.522326 | past_momentum|past_momentum|past_momentum |
| SLEEP_POD_SUEDE          | SLEEP_POD    |          6.36297 |       3.36057   |                    3 |           6.71363 |        0.947768 | z_revert|past_revert|z_revert             |
| MICROCHIP_OVAL           | MICROCHIP    |          5.88814 |       2.0322    |                    3 |          13.2262  |        0.445189 | past_revert|past_revert|past_revert       |
| UV_VISOR_ORANGE          | UV_VISOR     |          3.97321 |       2.66821   |                    3 |          17.7271  |        0.224132 | past_revert|past_revert|past_revert       |
| PEBBLES_XL               | PEBBLES      |         54.3185  |     -19.1047    |                    2 |          84.7454  |        0.640961 | z_revert|z_revert|z_revert                |
| OXYGEN_SHAKE_CHOCOLATE   | OXYGEN_SHAKE |         18.6442  |     -10.1878    |                    2 |          20.9135  |        0.891492 | past_revert|past_revert|z_revert          |
| PEBBLES_M                | PEBBLES      |          9.52662 |     -15.2822    |                    2 |          27.0098  |        0.35271  | past_revert|z_revert|z_revert             |
| PANEL_1X4                | PANEL        |          6.77634 |      -5.27377   |                    2 |          21.9952  |        0.308083 | past_momentum|past_momentum|past_momentum |
| PANEL_1X2                | PANEL        |          5.96998 |      -0.0159369 |                    2 |           5.86614 |        1.0177   | z_revert|z_revert|z_revert                |
| SNACKPACK_STRAWBERRY     | SNACKPACK    |          5.65263 |      -1.33772   |                    2 |           7.66595 |        0.737368 | z_revert|z_revert|z_revert                |
| ROBOT_DISHES             | ROBOT        |          5.3979  |      -1.13127   |                    2 |          19.9956  |        0.269955 | past_revert|past_revert|past_revert       |

Worst product summaries by held-out-day performance:

| product                       | category      |   mean_test_edge |   min_test_edge |   positive_test_days |   mean_train_edge |   overfit_ratio | selected_signals                        |
|:------------------------------|:--------------|-----------------:|----------------:|---------------------:|------------------:|----------------:|:----------------------------------------|
| PEBBLES_S                     | PEBBLES       |        -25.7902  |       -51.0402  |                    0 |          22.0283  |       -1.17078  | z_revert|past_momentum|z_revert         |
| SLEEP_POD_LAMB_WOOL           | SLEEP_POD     |        -22.362   |       -40.1936  |                    0 |          13.249   |       -1.68783  | past_revert|past_momentum|past_momentum |
| TRANSLATOR_SPACE_GRAY         | TRANSLATOR    |        -20.111   |       -27.2448  |                    0 |          11.7846  |       -1.70655  | past_momentum|past_momentum|z_revert    |
| GALAXY_SOUNDS_SOLAR_FLAMES    | GALAXY_SOUNDS |        -16.751   |       -23.288   |                    0 |          11.6911  |       -1.43281  | z_revert|past_revert|past_momentum      |
| MICROCHIP_TRIANGLE            | MICROCHIP     |        -15.3721  |       -29.4079  |                    0 |          15.2283  |       -1.00944  | past_momentum|past_revert|past_momentum |
| SNACKPACK_VANILLA             | SNACKPACK     |        -15.2834  |       -24.9711  |                    0 |           4.62111 |       -3.30729  | past_momentum|past_revert|past_momentum |
| SLEEP_POD_POLYESTER           | SLEEP_POD     |        -14.1203  |       -16.9224  |                    0 |          12.2579  |       -1.15193  | z_revert|past_revert|past_momentum      |
| SNACKPACK_CHOCOLATE           | SNACKPACK     |        -13.7006  |       -22.6698  |                    0 |           8.81385 |       -1.55444  | past_momentum|past_revert|z_revert      |
| PANEL_2X4                     | PANEL         |        -13.6763  |       -24.7455  |                    0 |          16.6903  |       -0.819418 | z_revert|past_momentum|z_revert         |
| GALAXY_SOUNDS_PLANETARY_RINGS | GALAXY_SOUNDS |        -11.8002  |       -20.2541  |                    0 |          13.3086  |       -0.886662 | past_revert|past_momentum|z_revert      |
| OXYGEN_SHAKE_EVENING_BREATH   | OXYGEN_SHAKE  |         -8.26057 |       -13.6552  |                    0 |           7.3821  |       -1.119    | past_momentum|z_revert|past_revert      |
| GALAXY_SOUNDS_DARK_MATTER     | GALAXY_SOUNDS |         -7.08603 |       -10.5312  |                    0 |          10.4183  |       -0.68015  | past_momentum|past_revert|z_revert      |
| MICROCHIP_SQUARE              | MICROCHIP     |         -6.70582 |       -10.7722  |                    0 |          16.2719  |       -0.412109 | z_revert|past_momentum|past_momentum    |
| UV_VISOR_YELLOW               | UV_VISOR      |         -6.19574 |        -8.60132 |                    0 |           6.00466 |       -1.03182  | past_momentum|z_revert|past_revert      |
| OXYGEN_SHAKE_GARLIC           | OXYGEN_SHAKE  |         -6.13229 |       -12.6478  |                    0 |          11.4547  |       -0.535351 | past_momentum|past_momentum|past_revert |

Best individual held-out selections:

| product                  | category     |   test_day | signal        | feature           |   horizon |   threshold |   cost_mult |   train_edge |   test_edge |   test_positive_blocks |
|:-------------------------|:-------------|-----------:|:--------------|:------------------|----------:|------------:|------------:|-------------:|------------:|-----------------------:|
| PEBBLES_XL               | PEBBLES      |          3 | z_revert      | roll_z_500        |       100 |           2 |         0.5 |      59.4992 |    104.076  |                     15 |
| PEBBLES_XL               | PEBBLES      |          4 | z_revert      | roll_z_500        |       100 |           2 |         0.5 |      71.8663 |     77.9843 |                     16 |
| PEBBLES_L                | PEBBLES      |          3 | past_momentum | past_mid_diff_100 |       100 |         237 |         0.5 |      11.7884 |     40.2338 |                      8 |
| ROBOT_LAUNDRY            | ROBOT        |          3 | past_revert   | past_mid_diff_100 |       100 |         161 |         0.5 |      16.025  |     37.26   |                     13 |
| OXYGEN_SHAKE_CHOCOLATE   | OXYGEN_SHAKE |          2 | past_revert   | past_mid_diff_100 |       100 |         156 |         0.5 |      13.0643 |     36.9897 |                     12 |
| ROBOT_LAUNDRY            | ROBOT        |          2 | past_revert   | past_mid_diff_100 |       100 |         161 |         0.5 |      21.5159 |     33.6465 |                     16 |
| PEBBLES_M                | PEBBLES      |          3 | z_revert      | roll_z_500        |       100 |           2 |         0.5 |      20.9159 |     33.5834 |                     13 |
| TRANSLATOR_GRAPHITE_MIST | TRANSLATOR   |          2 | past_revert   | past_mid_diff_100 |       100 |         164 |         0.5 |      16.3338 |     32.444  |                     16 |
| OXYGEN_SHAKE_CHOCOLATE   | OXYGEN_SHAKE |          3 | past_revert   | past_mid_diff_100 |       100 |         156 |         0.5 |      19.3376 |     29.1306 |                     12 |
| TRANSLATOR_GRAPHITE_MIST | TRANSLATOR   |          3 | past_revert   | past_mid_diff_100 |       100 |         164 |         0.5 |      14.4353 |     28.4416 |                     12 |
| TRANSLATOR_ASTRO_BLACK   | TRANSLATOR   |          3 | z_revert      | roll_z_500        |       100 |           2 |         0.5 |      10.6156 |     27.8128 |                     14 |
| TRANSLATOR_ASTRO_BLACK   | TRANSLATOR   |          2 | z_revert      | roll_z_500        |       100 |           2 |         0.5 |      15.3222 |     18.723  |                     15 |

Nested-validation interpretation:

- The large in-sample/cost-stressed `PEBBLES_XL` rolling-z signal remains useful but is materially less clean under train-days-to-held-out-day selection than the raw grid implied.
- Products with all three held-out days positive deserve more trust than products with a spectacular average driven by one held-out day.
- This reduces confidence in blindly deploying the most extreme long-horizon parameter screen and increases confidence in diversified candidate directions with explicit product selection and conservative thresholds.

## Evidence-Backed Candidate Direction Matrix

Created `tables/candidate_direction_evidence_matrix.csv` to map neutral candidate-worthy directions to supporting evidence, fragility, and required next validation. No strategy candidate files were created.

Key implications:

- The strongest structurally grounded direction is still `PEBBLES` factor/residual trading, but it should be implemented conservatively because short-horizon residual edge is mixed by product/day.
- The strongest nested-validation product subset is `ROBOT_LAUNDRY`, `TRANSLATOR_GRAPHITE_MIST`, `PEBBLES_L`, `TRANSLATOR_ASTRO_BLACK`, `ROBOT_IRONING`, `SLEEP_POD_SUEDE`, `MICROCHIP_OVAL`, and `UV_VISOR_ORANGE`.
- The broad cost-stressed scan is useful for candidate design, but the nested pass is the stricter guardrail against parameter overfit.
- Heavy ML is not justified for direct deployment; ML should only inform simple hand-coded signals.
- Broad all-product trading is not supported by the evidence.

## Exhaustion Boundary

Created `research_exhaustion_checklist.md`.

The remaining unknowns are not pre-candidate research questions anymore. They require the next learning-plan phase: writing five neutral candidates and running Kevin/Xeeshan candidate diagnostics. Exact fill behavior, realized product PnL, inventory paths, rejected orders, simulator disagreement, and portal-window alignment cannot be resolved further without candidate strategy code or official logs.
## Completion Status

The learning pass, including mandatory Phase 6.5 open-ended expansion and supplementary nested robustness validation, has been executed deeply. The next step is candidate design, but no candidate files were created in this pass.
