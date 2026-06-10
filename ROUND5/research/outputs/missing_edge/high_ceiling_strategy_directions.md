# High Ceiling Strategy Directions

The missing edge is not another small z-score candidate. Day-4 oracle capacity is enormous: `PEBBLES` alone has 4.83M taker-oracle capacity, `MICROCHIP` 3.69M, `SLEEP_POD` 2.86M, and `ROBOT` 2.75M. Our candidates captured only basis points of that opportunity.

## Direction 1: ROBOT_DISHES 10-tick reversal liquidity strategy

Evidence: `ROBOT_DISHES` day-4 10-tick reversal has the strongest high-ceiling signal found. A full-fill target-position simulation reaches about 235k on day 4, and the gross directional proxy is 302k. This is the first discovered signal in the right leaderboard order of magnitude.

Important caveat: visible top-1/top-3 taker-depth simulation does not preserve the edge. That means the plausible implementation is not naive crossing. It likely needs passive 10-lot liquidity provision after a 10-tick move, or careful price-through execution where the portal fills differently from the visible public-trade approximation.

Candidate implication: build a research candidate that quotes aggressively but mostly passively on `ROBOT_DISHES` after 10-tick moves, with immediate inventory flip/flatten when the reversal starts. Use `ROBOT_IRONING/MOPPING/VACUUMING` only as confirmers, not as broad basket trades.

Expected official-window range if the fill model transfers: 50k-200k. Full-history risk is high because this appears day/regime-specific.

## Direction 2: Exact PEBBLES basket/fair-value arbitrage

Evidence: leave-one-product linear formulas inside `PEBBLES` have day-4 residual std near 2.82 for every product. That is far tighter than the raw product volatility and much more structural than our previous anchor-normalized residual. The `PEBBLES` category also has the highest day-4 oracle capacity.

Why our candidates missed it: Candidate 1 used weak online normalized anchors and traded sparsely. Candidates 6/7/9 used single-product rolling z-scores, not the exact cross-product synthetic fair value.

Candidate implication: fit no static hardcoded coefficients in the submitted file, but compute online category fair values from the current five-product cross-section or rolling leave-one regressions. Quote full size around synthetic fair value and trade all five PEBBLES, not just XL/L.

Expected official-window range: 20k-100k if passive fills are frequent; higher only if basket residuals can be harvested repeatedly with size.

## Direction 3: MICROCHIP structure and MICROCHIP_SQUARE

Evidence: `MICROCHIP_SQUARE` has the second-highest day-4 product oracle capacity at 1.29M, and the entire `MICROCHIP` category ranks second. We barely traded it. Simple directional signals did not produce a trustworthy executable edge, but the ceiling is too large to ignore.

Candidate implication: search for shape-based fair-value structure and pair/basket residuals, especially `SQUARE/RECTANGLE/TRIANGLE` versus `CIRCLE/OVAL`. A naive time-series signal is not enough; the next attempt should be a category formula or market-making strategy.

Expected official-window range: unknown; current evidence proves ceiling, not signal. This is a high-priority research target before candidate construction.

## Direction 4: Name-structured curve strategies

Evidence: product-name representations are meaningful in several categories: `SLEEP_POD` ordinal/material representation has day-4 cross-sectional R2 around 0.945; `PEBBLES` size ordering has R2 around 0.88; `PANEL` physical dimensions are meaningful on earlier days though weaker on day 4.

Candidate implication: build fair-value curves from semantic features, then trade deviations rather than raw momentum/reversion. This is more likely to match top-team puzzle-solving than generic ML screens.

Expected official-window range: 10k-75k initially; can become 100k+ if combined across categories with passive full-size execution.

## Direction 5: Fair-value filtered market making

Evidence: leaderboard avg fill values around 6-11 and low drawdowns suggest repeated full-size fills with high hit rate. That profile is more consistent with market making around a strong fair value than with sporadic taker entries.

Candidate implication: quote 10-lot passive orders only when synthetic fair value says the quote is favorable, cancel/flip aggressively when residual changes sign, and avoid broad products without a fair-value anchor.

Expected official-window range: this is the most plausible path to leaderboard-scale recovery factor if the fair-value model is right.
