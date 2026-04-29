# Round 5 Missing Edge Research Plan

This document is a new source-of-truth plan for the next Round 5 research phase.

The previous learning pass, candidate pass, official-submission analysis, and aggressive candidate pass were useful, but they did not find the real high-ceiling edge. The leaderboard evidence changes the problem. This is no longer a question of small parameter tuning or making candidates slightly more aggressive.

The task is now to explain the gap between our strategies and the top official portal scores, then find the missing structural edge.

## Core Evidence

Our first five official portal scores were roughly:

- `round5_candidate_1.py`: `1,864.24`
- `round5_candidate_2.py`: `-37,335.31`
- `round5_candidate_3.py`: `-890.34`
- `round5_candidate_4.py`: `2,821.48`
- `round5_candidate_5.py`: `899.14`

Our second aggressive candidate batch improved the local official-window proxy but still remained far below the leaderboard:

- `round5_candidate_6.py`: portal-window replay about `3,382`
- `round5_candidate_7.py`: portal-window replay about `5,574`
- `round5_candidate_8.py`: portal-window replay about `3,535`
- `round5_candidate_9.py`: portal-window replay about `8,267-8,302`
- `round5_candidate_10.py`: portal-window replay about `-393 to -438`

The public leaderboard shows many official portal entries above `100,000`, with the top entries above `400,000`.

This gap is too large to explain by conservatism alone. It strongly suggests we are missing one or more of:

- The primary intended product/category structure.
- A deterministic or semi-deterministic relation embedded in the 50 products.
- A high-ceiling oracle-like trend/mean-reversion pattern.
- A product representation/puzzle clue.
- A fill/execution exploit.
- A basket/factor identity.
- A product subset with much larger executable edge than our screens detected.
- A time/window effect that is legitimate and online-detectable, not hardcoded.

## New Objective

Find the missing high-ceiling edge that can plausibly produce `100k+` official portal PnL.

Do not optimize for tiny improvements from `3k` to `8k`. That is not enough. A valid result of this phase must either:

- identify a plausible path to `100k+` style official-window PnL, or
- prove with strong evidence why the available data/tooling cannot reveal it.

## Required Mindset Shift

The previous approach was too generic:

1. Broad quant research.
2. Product screens.
3. Conservative candidate translation.
4. Local/portal-window backtests.
5. Small candidate iteration.

That is not sufficient.

This phase must be more like puzzle-solving plus quantitative reverse engineering:

- First estimate where `100k+` PnL is even possible.
- Then identify which products/categories can support that ceiling.
- Then determine what signal or structure unlocks it.
- Then design aggressive executable strategies around that structure.

Do not start by tweaking existing candidates. Start by proving what kind of edge can produce leaderboard-scale PnL.

## All-50 Scanner Mandate

The previous candidates became too narrow. The correction is not to blindly trade all 50 products, but it is also not acceptable to only think in terms of one or two products.

Use all 50 products as the modeling universe. Every category and every product should be considered as a possible source of:

- fair-value structure,
- basket/factor identity,
- product-name formula,
- lead-lag signal,
- mean-reversion/reversal,
- breakout/trend,
- market-making edge,
- passive fill edge,
- execution anomaly,
- cross-category relationship.

The final strategy may trade many products if many products have real current edge. It may trade fewer products if the edge is concentrated. But this must be an evidence-driven decision. Do not skip products just because prior broad baskets failed. Candidate 2 proved that broad inclusion without edge is toxic; it did not prove that broad edge-gated scanning is bad.

The desired architecture for future candidates is an all-50 opportunistic edge scanner:

- For every product, compute the best available product/category fair value.
- For every product, compute current executable edge after spread and adverse-selection cost.
- For every product, determine whether the edge is strong enough to trade.
- Use product-specific logic where needed.
- Use category-specific logic where needed.
- Allow different strategies for different products in the same submitted file.
- Trade a majority of products if many products clear the edge threshold.
- Trade only a minority if only a minority has edge.
- Do not force diversification, but do not under-trade from conservatism.

This is the main strategic shift: model everything, then trade aggressively where the model says the edge is real.

## Files To Use

Use all Round 5 materials and outputs, including:

- `ROUND5/round5.md`
- `ROUND5/prices_round_5_day_2.csv`
- `ROUND5/prices_round_5_day_3.csv`
- `ROUND5/prices_round_5_day_4.csv`
- `ROUND5/trades_round_5_day_2.csv`
- `ROUND5/trades_round_5_day_3.csv`
- `ROUND5/trades_round_5_day_4.csv`
- `ROUND5/research/outputs/round5_learning_outputs.md`
- `ROUND5/research/outputs/research_exhaustion_checklist.md`
- `ROUND5/research/outputs/candidate_score_table.md`
- `ROUND5/research/outputs/official_candidate_score_table.md`
- `ROUND5/research/outputs/official_submission_analysis.md`
- `ROUND5/research/outputs/official_candidate_failure_matrix.csv`
- `ROUND5/research/outputs/official_candidate_promotion_notes.md`
- `ROUND5/research/outputs/candidate_6_10_score_table.md`
- `ROUND5/research/outputs/candidate_6_10_raw_backtests.json`
- all candidate strategy files under `ROUND5/strategies/`
- all official submission bundles/logs/jsons under `ROUND5/official_submissions/`

Create new outputs under:

- `ROUND5/research/outputs/missing_edge/`

## Phase A: Leaderboard Gap Interpretation

Analyze the leaderboard numbers as market evidence.

Questions:

- What does `100k-450k` official portal PnL imply about trade count, average edge, and position utilization?
- Given position limit `10` per product, how many repeated profitable fills are required?
- Does the average fill statistic from top teams imply frequent small edges or fewer large directional captures?
- Are top entries likely market making, directional, basket arbitrage, deterministic formula, or trend-following?
- What max drawdown/recovery factor patterns imply about the edge quality?
- Do duplicate/similar leaderboard scores indicate common public strategy families or deterministic exploitable structure?

Produce:

- `missing_edge/leaderboard_gap_notes.md`
- `missing_edge/leaderboard_required_edge_estimates.csv`

## Phase B: Hindsight Ceiling / Oracle PnL

Before looking for signals, estimate the maximum plausible PnL by product and category.

Build multiple oracle approximations:

- Perfect one-step direction oracle.
- Perfect short-horizon direction oracle.
- Perfect trend-following oracle.
- Perfect mean-reversion oracle.
- Perfect end-of-window liquidation oracle.
- Best possible position path with limit `10` using future mid prices.
- Best taker-only oracle constrained by top-of-book spreads.
- Best passive/spread-capture approximation if possible.
- Category basket residual oracle.
- Pair spread oracle.
- Factor residual oracle.

Questions:

- Which products/categories can theoretically generate `100k+`?
- Which products have high ceiling but our candidates ignored?
- Which products have high ceiling but bad naive screens?
- Which categories have hidden basket/factor ceiling?
- Which products are impossible to use for high scores because ceiling is too low?

This phase is mandatory. Do not continue without it.

Produce:

- `missing_edge/oracle_ceiling_by_product.csv`
- `missing_edge/oracle_ceiling_by_category.csv`
- `missing_edge/oracle_path_examples.md`
- plots of top oracle paths.

## Phase C: Product Representation / Puzzle Search

Round 5 has 10 named categories of 5 products. Product names are likely meaningful. Search for hidden structure in names, orderings, dimensions, sizes, colors, shapes, flavors, tasks, and category stories.

For each category, test all plausible representations:

- Ordinal ordering.
- Numeric encoding from names.
- Physical relations:
  - panel areas: `1x2`, `2x2`, `1x4`, `2x4`, `4x4`
  - pebble sizes: `XS`, `S`, `M`, `L`, `XL`
  - visor color spectrum ordering
  - microchip shape geometry
  - sleep pod material quality/order
  - oxygen flavor/usage groupings
  - snack flavor groupings
  - robot task relationships
  - translator color/shade ordering
  - galaxy phenomena relationships
- Basket identities.
- Linear formulas.
- Ratio formulas.
- Difference formulas.
- Rank constraints.
- Mean/median/category-index relationships.
- Synthetic fair values from other products in the same category.
- Cross-category analogies.

Do not assume prior factor tests were enough. Redo this as a puzzle search with explicit name-driven hypotheses.

Produce:

- `missing_edge/product_name_structure_tests.csv`
- `missing_edge/category_formula_candidates.md`
- `missing_edge/category_structure_rankings.csv`

## Phase D: Official Window Reverse Engineering

Use official portal windows from candidates 1-5 and any candidates 6-10 official submissions if available.

For each official window:

- Identify which products moved enough to support large PnL.
- Identify products where our strategies traded but should not have.
- Identify products where our strategies did not trade but oracle says they should have.
- Compare oracle paths vs actual candidate trades.
- Determine whether candidates failed by:
  - missing the right product,
  - wrong sign,
  - weak size,
  - poor execution,
  - late entry,
  - early exit,
  - holding too long,
  - trading too many products,
  - trading wrong regime,
  - missing deterministic basket/factor relation.

Produce:

- `missing_edge/official_window_oracle_vs_candidates.csv`
- `missing_edge/official_window_missed_products.md`
- `missing_edge/official_window_failure_modes.md`

## Phase E: Signal Search Targeting High-Ceiling Products

After Phase B identifies high-ceiling products/categories, search for signals only where the ceiling justifies attention.

For each high-ceiling product/category:

- Test lagged returns.
- Test order book imbalance.
- Test microprice.
- Test spread/depth states.
- Test trade flow.
- Test category residuals.
- Test cross-product lags.
- Test regime state.
- Test volatility bursts.
- Test change-point states.
- Test rolling z-scores.
- Test breakout/trend continuation.
- Test reversal after jumps.
- Test all plausible holding periods.
- Test all plausible entry/exit styles.

But focus on executable signal:

- Does it make money after spread?
- Does it survive top-of-book constraints?
- Does it survive position limit `10`?
- Does it survive day splits?
- Does it survive official-window replay?

Produce:

- `missing_edge/high_ceiling_signal_search.csv`
- `missing_edge/high_ceiling_signal_notes.md`

## Phase F: Strategy Implications

Convert the missing-edge research into concrete strategy directions.

Each direction must specify:

- Products traded.
- Products scanned but not traded.
- Signal formula.
- Entry rule.
- Exit rule.
- Position sizing.
- Aggression level.
- Edge threshold logic.
- Whether the direction is single-product, category-level, multi-category, or all-50 scanner.
- Expected official-window PnL range.
- Full-history risk.
- Hidden-data risk.
- Why it can plausibly reach leaderboard-scale PnL.

Do not accept a direction if it cannot plausibly beat `10k`. The target is `100k+` style edge, or at least a credible step toward it.

At least one next strategy direction must be a broad all-50 or multi-category scanner. This scanner should not blindly trade all 50 products. It should model all 50, compute product-specific executable edge, and trade only products whose current edge clears the threshold. This is the way to test the user's hypothesis that top teams may be monetizing many products without repeating Candidate 2's broad-basket failure.

Produce:

- `missing_edge/high_ceiling_strategy_directions.md`
- `missing_edge/next_candidate_plan.md`

## Anti-Patterns To Avoid

Do not:

- Keep tuning candidates that score below `10k` unless the tuning is based on a new high-ceiling diagnosis.
- Treat broad positive research screens as sufficient.
- Promote “safe” tiny-PnL strategies.
- Over-diversify across weak products without edge.
- Under-trade the universe from conservatism after modeling only one or two products.
- Confuse "broad basket" with "broad edge-gated scanner"; the first can be toxic, the second may be necessary.
- Hide behind robustness when the score ceiling is too low.
- Use raw full-data score as the only validation.
- Use portal-window score as the only validation.
- Confuse statistical predictability with executable PnL.
- Assume PEBBLES is the answer just because it looked clean.
- Assume a product is bad because the first candidate traded it badly.
- Ignore product names and category semantics.

## Stop Condition

Do not stop when you have another `5k-10k` candidate idea.

Stop only when:

- The plausible `100k+` edge sources have been identified, or
- All high-ceiling products/categories have been ruled out with evidence, and
- Oracle ceilings, product/category structures, official-window failures, and signal searches are documented.

If the result is “we still do not know the missing edge,” say that explicitly and show which high-ceiling avenues were eliminated.
