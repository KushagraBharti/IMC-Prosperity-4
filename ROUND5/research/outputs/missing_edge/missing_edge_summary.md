# Missing Edge Summary

The leaderboard gap is real and cannot be explained by conservative sizing. Top-100 median official PnL is about 134k; our best official score is 2.8k and our best official-window replay is 8.3k.

Highest day-4 theoretical capacity:

- `PEBBLES`: 4.83M category taker oracle; top product `PEBBLES_XL` 1.71M.
- `MICROCHIP`: 3.69M category taker oracle; top product `MICROCHIP_SQUARE` 1.29M.
- `SLEEP_POD`: 2.86M category taker oracle.
- `ROBOT`: 2.75M category taker oracle; `ROBOT_DISHES` 764k.

Most important discovered signal:

- `ROBOT_DISHES` 10-tick reversal on official day 4. Full-fill target-position simulation reaches about 235k, with gross directional proxy around 302k. Visible-depth taker simulation fails, so the likely implementation is passive/liquidity-providing reversal, not naive crossing.

Most important discovered structure:

- `PEBBLES` has extremely tight leave-one-product formulas: day-4 residual std about 2.82 for every product. Our PEBBLES strategies did not use this exact synthetic fair value; they used weak rolling/anchor proxies.

Most important missed products:

- `MICROCHIP_SQUARE`, `PEBBLES_S`, `MICROCHIP_TRIANGLE`, `MICROCHIP_RECTANGLE`, `SLEEP_POD_POLYESTER`, `SLEEP_POD_COTTON`, `ROBOT_MOPPING`, `PANEL_2X4`.

Why previous candidates missed:

- They traded low-ceiling or weakly modeled subsets.
- They used generic time-series signals instead of exact category fair values.
- Candidate 4 found some ROBOT official-window behavior but used the wrong signal family; the high-ceiling result is 10-tick reversal on `ROBOT_DISHES`.
- Candidate 1 used PEBBLES but not the exact cross-product relation.
- Candidate 2 proved that broad product inclusion without a structural edge loses quickly.

Conclusion: the next work should be high-ceiling candidate construction around `ROBOT_DISHES` reversal-liquidity and exact PEBBLES basket fair value. We have not fully solved the top-team edge, but we now have two plausible paths that explain how 100k+ could be possible.
