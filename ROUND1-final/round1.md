# Round 1 Final Report

## 1. Executive Summary

Round 1 finished with a combined total of **177,302 XIRECS** for team **ALCARAZGOAT2026**, placing the team at **overall position 1694** on the leaderboard screenshot. The score came from two almost equally important components: the algorithmic submission produced approximately **+89,307 XIRECS**, while the manual trading submission produced **+87,995.10 XIRECS**. The manual side was especially strong: the results screenshot shows a **manual round ranking of 1st**, while the algorithmic side ranked **2683rd** for the round.

The final Round 1 package is stored in `ROUND1-final`. The algorithmic submission is the `final-algo` package under `ROUND1-final/algo_submission`, containing the Python strategy file, the JSON result export, the log export, and the zip archive. The manual trading submission is represented by the final two manual orders visible in the result screenshots: a buy in **DRYLAND_FLAX** and a buy in **EMBER_MUSHROOM**. Together, those manual trades contributed almost half of the total Round 1 PnL and were the decisive reason the final round score was so strong.

At a high level, the algorithm combined two different approaches. For **INTARIAN_PEPPER_ROOT**, it used a long-only structural carry strategy that tried to accumulate close to the maximum allowed long position and profit from the persistent upward drift in fair value. For **ASH_COATED_OSMIUM**, it used a more active market-making and mean-reversion specialist centered around a stable fair value near 10,000. The result logs show that Pepper was the dominant algorithmic profit source, while Osmium added a smaller but still meaningful secondary contribution. The main algorithmic weakness was not the final PnL, which was solid, but risk posture: Osmium ended close to the long position limit despite being intended as a two-sided market-making component.

## 2. Final Results

### 2.1 Overall Leaderboard Result

The detailed results screenshot shows the team name as **ALCARAZGOAT2026** and the overall Round 1 leaderboard position as **1694**. The previous total before Round 1 was **0**, and the full Round 1 total was **177,302 XIRECS**, which also became the new total PnL. The mission progress panel showed **89%** progress toward a stated team goal of **200,000**, and the result page also showed **13 badges unlocked**.

The important interpretation is that Round 1 was a balanced result between automated trading and manual trading. The algorithmic system generated slightly more raw PnL than the manual trades, but the manual submission had a much stronger relative ranking. This means the manual component was unusually efficient compared with the field, while the algorithmic component was profitable but not as competitively differentiated.

Summary of final visible results:

- Team: **ALCARAZGOAT2026**
- Overall position: **1694**
- Previous total: **0**
- Round 1 total: **177,302 XIRECS**
- New total PnL: **177,302 XIRECS**
- Algorithmic trading result: **+89,307 XIRECS**
- Algorithmic round ranking: **2683rd**
- Manual trading result: **+87,995.10 XIRECS**
- Manual round ranking: **1st**

### 2.2 Algorithmic Trading Result

The screenshot rounds the algorithmic trading result to **+89,307 XIRECS**. The exact value in `272192.json` is **89,306.8125**, which explains the rounded display value. The algorithmic PnL chart in the screenshot is a mostly smooth upward-sloping line from near zero to roughly 90,000. It does not show the kind of large repeated drawdowns that would indicate an unstable or highly path-dependent strategy. Instead, the curve is dominated by a steady positive drift, which matches the log analysis: Pepper accumulated a long position early and then earned from the rising underlying value for the rest of the round.

The final JSON export reports these end positions:

- `INTARIAN_PEPPER_ROOT`: **+80**
- `ASH_COATED_OSMIUM`: **+78**
- `XIRECS`: **-1,810,163**

The two product positions are both close to the positive position limit of 80. This is an important detail. The final algo was not a flat end-of-round strategy. It ended heavily long both tradeable products, especially Pepper where the design was explicitly long-only. For Pepper this was intentional because the strategy expected the carry/uptrend to dominate. For Osmium, ending at +78 is more of a risk-management concern because the Osmium strategy was supposed to be an active market-making specialist rather than a pure long-carry position.

### 2.3 Manual Trading Result

The manual trading screenshot shows two final trades:

- **DRYLAND_FLAX**: Buy **9,999** units at price **+30**, producing **+9,999** PnL.
- **EMBER_MUSHROOM**: Buy **19,999** units at price **+17**, producing **+77,996.10** PnL.

The total manual trading PnL displayed is **87,995.10 XIRECS**. This total exactly matches the sum of the two displayed trade contributions: **9,999 + 77,996.10 = 87,995.10**. The manual ranking screenshot reports this as **round ranking 1st**, so the manual solution was not merely good in absolute terms; it was at the very top of the field for Round 1.

The manual result mattered nearly as much as the algorithmic result in raw score terms. Algorithmic trading contributed about 89.3k, while manual trading contributed about 88.0k. In percentage terms, manual trading contributed just under half of the total Round 1 score, despite being only two submitted orders. This is why the manual result deserves as much attention in the final Round 1 summary as the algorithmic system.

## 3. Files Submitted

### 3.1 Algo Submission Package

The final algorithmic package is located at:

`ROUND1-final/algo_submission/final-algo`

It contains:

- `272192.py`: the final Python strategy submitted for Round 1.
- `272192.json`: the final result export with exact profit, activities log, graph log, and final positions.
- `272192.log`: the execution log export, including activities log, per-timestamp logs, and trade history.
- `final-algo.zip`: the archived final algo package.

The JSON and log files are both large single-line JSON payloads. The `.json` file contains the exact official result summary, including `round`, `status`, `profit`, `activitiesLog`, `graphLog`, and final `positions`. The `.log` file contains the submission ID, the same activities log, a timestamped logs array, and the full trade history. The timestamped log entries are empty, which means the strategy was not printing internal debugging output and the official artifact contains no platform warning messages.

### 3.2 Hand Trade Submission

The final hand trade submission is represented by the two manual orders shown on the result page. No separate structured manual submission file was present in `ROUND1-final/hand_trade_submission` at the time this report was written. The final manual answer should be recorded as:

- Buy **9,999** units of **DRYLAND_FLAX** at **+30**.
- Buy **19,999** units of **EMBER_MUSHROOM** at **+17**.

The displayed manual result confirms that these two orders produced **+87,995.10 XIRECS** and ranked **1st** for the manual portion of Round 1.

## 4. Algorithm Design: What the Code Actually Does

### 4.1 Products Traded

The final algo trades exactly two products:

- `ASH_COATED_OSMIUM`
- `INTARIAN_PEPPER_ROOT`

Both products have a hard position limit of **80** units in the code. The strategy initializes an output order list for both products on every call and then conditionally fills those lists if the corresponding order book is available in the `TradingState`.

The code architecture is intentionally split into two specialized strategies. Osmium is handled by `trade_osmium`, which is a market-making / mean-reversion style strategy. Pepper is handled by `trade_pepper_accumulator`, which is a long-only accumulation strategy built around a structural upward trend assumption. This split is important because the two products were not treated symmetrically. Pepper was the primary directional/carry bet, while Osmium was the secondary active trading engine.

### 4.2 Shared Infrastructure

The strategy starts each call by loading `traderData` as JSON. This creates a persistent cache across timestamps. The cache stores rolling histories for wall mid prices, imbalances, and Pepper mid prices. These histories are capped at `HISTORY_LIMIT = 40`, so the model only carries a short rolling memory of recent market structure.

For each product, the strategy builds a normalized order book snapshot. The snapshot includes sorted buy orders, sorted sell orders, best bid, best ask, midpoint, wall midpoint, top-of-book imbalance, and a boolean indicating whether both sides of the book exist. These derived fields are used by both product strategies.

The main book features are:

- **mid**: the average of best bid and best ask when both sides exist. If only one side exists, it falls back to that side's best price.
- **wall_mid**: the average of the largest visible bid wall price and largest visible ask wall price. This is meant to capture where size is concentrated, not just where the top quote is.
- **top imbalance**: `(top_bid_volume - top_ask_volume) / (top_bid_volume + top_ask_volume)`. Positive imbalance means the top bid has more visible volume than the top ask.
- **trend_signal**: the difference between a short-window average and a long-window average for a cached history series.

The strategy has two separate limit-enforcement helpers. `ensure_within_limits` allows both long and short positions within the product limit, and it is used for Osmium. `enforce_long_only_limit` requires positions to stay between 0 and the positive limit, and it is used for Pepper. That means Pepper can never intentionally go short and will reject any generated order sequence that would move it below zero.

### 4.3 ASH_COATED_OSMIUM Strategy

The Osmium strategy is centered around a stable base fair value of **10,000**. It computes an alpha signal and adds that alpha to the base fair value. The alpha is clipped between **-4.0** and **+4.0**, so the strategy never allows its signal to move the fair value by more than four units away from the base.

The Osmium alpha uses several components:

- Wall-mid deviation: `(wall_mid - mid) * 1.10`
- Top-of-book imbalance: `imbalance * 2.40`
- Wall-mid trend: `trend * 0.20`
- Imbalance trend: `imbalance_trend * 0.40`

This combination says that Osmium is not just trading around the displayed midpoint. It is trying to read pressure in the book. If the large liquidity walls imply a fairer price above the midpoint, or if the bid side is stronger than the ask side, the strategy shifts fair upward. If the opposite is true, it shifts fair downward.

After computing fair value, the strategy computes a reservation price by subtracting an inventory skew: `reservation = fair - position * 0.10`. This makes the strategy less willing to buy when already long and less willing to sell when already short. It also computes a target position as `round(alpha * 5)` clipped between -20 and +20. This target is not the hard final target; it mainly influences whether the strategy should keep taking trades when edge is only marginal.

Osmium has two execution modes. First, it may aggressively take visible orders from the book. It sweeps up to two or three levels depending on signal strength. If alpha is strong enough, it checks more book levels. It buys asks when `fair - ask_price` is attractive and sells bids when `bid_price - fair` is attractive. The take size starts at 20 and increases modestly when edge is larger. It is reduced when inventory is already large or when the timestamp is in the endgame region.

Second, Osmium places passive quotes. It improves the best bid or best ask by one tick where possible and also adjusts the quote based on reservation price and alpha. Passive size starts around 20 but is reduced when inventory is already over 50% or 70% of the limit. This is the market-making component: the strategy tries to earn spread and mean-reversion edge while keeping inventory from becoming too extreme.

There is also a flattening rule. If Osmium position is above `OSMIUM_FLATTEN_TRIGGER = 40`, the strategy places an additional sell order to reduce inventory. If position is below -40, it places an additional buy order. This is meant to stop the market-making engine from drifting into a one-sided inventory problem.

### 4.4 INTARIAN_PEPPER_ROOT Strategy

The Pepper strategy is fundamentally different from the Osmium strategy. It is an accumulator, not a symmetric market maker. It is explicitly long-only and tries to build a large positive inventory because the code assumes Pepper has a structural upward drift over time.

The model defines a timestamp trend of `0.001` per timestamp unit and a default anchor around **13,000**. When both sides of the book exist, it estimates an observed anchor as `mid - timestamp * 0.001`. This anchor is smoothed with `PEPPER_ANCHOR_SMOOTHING = 0.10`, meaning each new observation updates the anchor gradually rather than fully resetting it.

The base fair value is then reconstructed as:

`base_fair = anchor + timestamp * 0.001`

The strategy adds a forward premium of **8.5** plus an alpha signal. That forward premium is a critical design choice. It makes the strategy willing to buy at prices that may look expensive relative to the current book midpoint, because the model expects future value to be higher.

Pepper alpha uses these components:

- Wall-mid deviation weighted by `1.10`
- Top-of-book imbalance weighted by `2.80`
- Wall-mid trend weighted by `0.40`
- Imbalance trend weighted by `0.35`
- Mid-price trend weighted by `0.15`

The alpha is clipped between **-4.0** and **+4.0**. The target position starts from `PEPPER_BASE_TARGET = 78`, can receive a positive imbalance bonus, and is clipped between **64** and **80**. Because `PEPPER_TARGET_SLOPE = 0`, the alpha itself does not move the base target up or down. In practice, this means the strategy almost always wants to be very long Pepper. The target is not a neutral prediction of fair position; it is a deliberate instruction to hold near the maximum long inventory.

Execution is aggressive. The strategy only sweeps the first ask level (`PEPPER_SWEEP_LEVELS = 1`), but it will buy even when the immediate edge is slightly negative if it is still far from target. If the gap to target is large, it allows a catch-up edge as low as **-1.00**. If the gap is smaller, it allows a less aggressive catch-up edge of **-0.35**. This is why the strategy can accumulate early even if mark-to-market temporarily looks bad.

Passive quoting for Pepper is effectively disabled. The passive trigger is set to `999`, which is unreachable given an 80-unit limit, and the passive max size is `0`. The code comments explicitly state the design: Pepper should rely on visible aggressive accumulation rather than inside-spread rests. This sacrifices potential maker edge but improves certainty of reaching the desired long position.

## 5. Algorithm Performance Analysis From JSON and Logs

### 5.1 Overall Equity Curve

The exact JSON result reports **89,306.8125** total profit. The graph log contains **500 sampled points**, starting at **0.0** and ending at **89,141.875**. The small difference between the graph's last sampled value and the exact final JSON profit is expected because the graph is sampled every 2,000 timestamp units and does not include the exact final timestamp value in the same way as the final result field.

The sampled graph shows a very strong and mostly monotonic upward curve. The largest sampled drawdown was **1,077.5625**, from timestamp **0** to timestamp **2,000**. After that initial loss, the curve recovered quickly and became consistently upward sloping. This is consistent with the strategy's design: it paid early spread/mark-to-market costs to build positions, especially Pepper, and then profited as the round progressed.

The worst sampled graph moves were:

- Timestamp **0 -> 2,000**: **-1,077.5625**
- Timestamp **708,000 -> 710,000**: **-228.359375**
- Timestamp **968,000 -> 970,000**: **-217.015625**
- Timestamp **486,000 -> 488,000**: **-120.671875**
- Timestamp **766,000 -> 768,000**: **-87.4609375**

The best sampled graph moves were:

- Timestamp **190,000 -> 192,000**: **+480.9375**
- Timestamp **706,000 -> 708,000**: **+426.390625**
- Timestamp **648,000 -> 650,000**: **+422.625**
- Timestamp **10,000 -> 12,000**: **+404.75**
- Timestamp **84,000 -> 86,000**: **+404.1875**

The important conclusion is that the algorithm did not win through a few isolated jumps. It won through persistent incremental accumulation of PnL. The largest losses were small relative to final profit, and the equity curve's shape suggests the core assumptions held throughout the round.

### 5.2 Product-Level PnL Breakdown

The activities log has **20,000 rows**, with **10,000 rows** for each product. The final product-level PnLs are highly uneven:

- `INTARIAN_PEPPER_ROOT`: **79,383.0** final PnL
- `ASH_COATED_OSMIUM`: **9,923.8125** final PnL

This means Pepper generated roughly **88.9%** of the final exact algorithmic PnL, while Osmium generated roughly **11.1%**. The algorithm was therefore mostly a Pepper strategy with an Osmium add-on, even though the Osmium code is more complex and more active.

Pepper's product-level PnL path was extremely clean after the initial accumulation period. It started at **0.0**, fell to a minimum of **-489.0** at timestamp **1,500**, and then finished at its maximum value of **79,383.0** at timestamp **999,900**. Its bucket-end PnL by 100,000 timestamp windows was almost perfectly linear:

- 0-99,999: **7,383.0**
- 100,000-199,999: **15,383.0**
- 200,000-299,999: **23,383.0**
- 300,000-399,999: **31,383.0**
- 400,000-499,999: **39,383.0**
- 500,000-599,999: **47,383.0**
- 600,000-699,999: **55,383.0**
- 700,000-799,999: **63,383.0**
- 800,000-899,999: **71,383.0**
- 900,000-999,999: **79,383.0**

That pattern is the clearest evidence that Pepper was capturing a structural drift/carry component. Once the strategy reached the long position, the PnL increased at a steady rate.

Osmium's path was profitable but less smooth. It started at **0.0**, reached a minimum of **-665.8125** at timestamp **2,300**, reached a maximum of **10,329.734375** at timestamp **964,700**, and finished at **9,923.8125**. The bucket-end Osmium PnL was:

- 0-99,999: **1,163.375**
- 100,000-199,999: **1,885.125**
- 200,000-299,999: **2,821.8515625**
- 300,000-399,999: **4,103.625**
- 400,000-499,999: **5,627.0**
- 500,000-599,999: **6,832.375**
- 600,000-699,999: **7,451.375**
- 700,000-799,999: **7,924.9375**
- 800,000-899,999: **9,562.1875**
- 900,000-999,999: **9,923.8125**

Osmium added value, but it was more volatile and less mechanically predictable than Pepper. Its contribution was still useful because it added nearly 10k PnL without destroying the Pepper edge, but it also carried the main inventory-control concern.

### 5.3 Pepper: Where It Did Well

Pepper did exactly what the final strategy wanted it to do. The trade history shows only **8 submission fills** in Pepper, all buys, and all in the first 100,000 timestamp bucket. Those fills totaled **80 units bought**, which matches the final position of **+80**. In other words, the strategy accumulated the maximum long Pepper position early and then held it.

That was the correct high-level behavior for the observed Round 1 environment. Once the long position was established, Pepper PnL rose steadily until the end. The product ended at its maximum PnL, with no meaningful late reversal. The algorithm's largest single source of profit was therefore not high-frequency trading or subtle quote placement; it was correctly identifying and exploiting the persistent upward value trend in Pepper.

The design choice to avoid passive Pepper quoting also appears justified by the result. Passive quoting might have improved average entry price in theory, but it could also have failed to fill enough size. The final strategy prioritized position certainty. Since the round rewarded holding the long Pepper exposure, getting filled early mattered more than optimizing every tick of entry.

### 5.4 Pepper: Weaknesses and Tradeoffs

Pepper's main weakness is that the strategy was structurally committed. It was not designed to adapt to a failed trend. The target stayed near maximum long inventory because `PEPPER_BASE_TARGET` was 78, the target slope was 0, and the clipped target range was 64 to 80. This means that even if short-term alpha weakened, the strategy would still generally want to remain heavily long.

The early PnL confirms the cost of this commitment. Pepper reached a minimum of **-489.0** at timestamp **1,500** while it was accumulating. That drawdown was small compared with the final profit, but it shows that the strategy was willing to absorb negative mark-to-market in order to build the desired position.

This was the correct tradeoff for this specific Round 1 result, but it would be risky in a different environment. If Pepper had mean-reverted, flattened, or reversed after early accumulation, the long-only design would have had limited protection. The code does not contain a true exit framework for Pepper. It is designed to accumulate and hold, not to dynamically unwind when the long thesis breaks.

### 5.5 Osmium: Where It Did Well

Osmium added **9,923.8125** final PnL, which is meaningful even though it was much smaller than Pepper's contribution. Unlike Pepper, Osmium traded actively across the entire round. The trade history shows **858 submission fills** in Osmium, with **2,429 units bought** and **2,351 units sold**. That is a very different profile from Pepper's 8 fills and confirms that Osmium was functioning as the active market-making / mean-reversion component.

Osmium recovered from an early drawdown and ended strongly positive. It reached its worst product-level PnL of **-665.8125** at timestamp **2,300**, but by the end of the first 100,000 timestamp bucket it had recovered to **+1,163.375**. It continued to build PnL over time and reached a maximum of **10,329.734375** near timestamp **964,700**.

The reason this worked is likely that the Osmium model used multiple book-pressure features rather than a naive static fair alone. It combined wall-mid deviation, top-book imbalance, wall-mid trend, and imbalance trend. That gave it a way to lean with short-term pressure while still anchoring to the stable 10,000 fair value. The inventory skew and flattening logic also helped prevent the strategy from becoming purely directional for most of the round.

### 5.6 Osmium: Weaknesses and Issues

The official `.log` artifact contains **10,000** timestamped log entries and **0** non-empty platform messages. There were no recorded runtime errors, sandbox warnings, lambda logs, or position-limit warning messages.

The main Osmium issue is therefore not platform cleanliness; it is inventory posture. Osmium ended at **+78**, very close to the maximum long limit. For a strategy that is supposed to be a two-sided specialist, this is a warning sign. It suggests that near the end of the round, the strategy was still carrying large directional exposure rather than flattening or reducing risk. That exposure was profitable here, but it made the final state less controlled than ideal.

### 5.7 Trade History Diagnostics

The final log's `tradeHistory` contains **1,322** rows. Of those, **370** are Pepper trades and **952** are Osmium trades. The submission participated in only a small number of Pepper trades but in most of the Osmium activity.

Pepper trade history summary:

- Total Pepper trade history rows: **370**
- Submission Pepper fills: **8**
- Submission Pepper buy quantity: **80**
- Submission Pepper sell quantity: **0**
- Final Pepper position: **+80**

This confirms the intended accumulator behavior. Pepper was not being traded actively after the initial build. The strategy bought to the limit and held.

Osmium trade history summary:

- Total Osmium trade history rows: **952**
- Submission Osmium fills: **858**
- Submission Osmium buy quantity: **2,429**
- Submission Osmium sell quantity: **2,351**
- Net submission fill quantity: **+78**
- Final Osmium position: **+78**

Osmium was the high-turnover component. Across the full round, the strategy bought and sold thousands of units while ending with a net long of 78. The high number of fills indicates that the strategy was consistently interacting with the market, not simply placing occasional directional trades.

Submission Osmium activity by 100,000 timestamp bucket:

- 0-99,999: **98 fills**, buy 251, sell 320
- 100,000-199,999: **50 fills**, buy 120, sell 131
- 200,000-299,999: **74 fills**, buy 259, sell 171
- 300,000-399,999: **104 fills**, buy 227, sell 309
- 400,000-499,999: **93 fills**, buy 340, sell 189
- 500,000-599,999: **85 fills**, buy 204, sell 228
- 600,000-699,999: **93 fills**, buy 250, sell 245
- 700,000-799,999: **108 fills**, buy 339, sell 333
- 800,000-899,999: **74 fills**, buy 187, sell 174
- 900,000-999,999: **79 fills**, buy 252, sell 251

The bucket data shows that Osmium stayed active for the whole round. It was not a short-lived opening strategy. It also shows that net positioning changed meaningfully across buckets, especially where buys exceeded sells or sells exceeded buys. This supports the interpretation that Osmium was both market-making and leaning directionally based on its alpha signal.

### 5.8 Best and Worst Time Windows

The worst time window was the opening move from timestamp **0** to **2,000**, where the sampled graph fell by **1,077.5625**. Product-level logs show that both products had early drawdowns: Pepper reached its minimum around timestamp 1,500, and Osmium reached its minimum around timestamp 2,300. This makes sense because the strategy was paying spread and absorbing mark-to-market while establishing inventory.

The best windows occurred later, after the initial positions and models were already active. The best sampled move was **+480.9375** from timestamp **190,000** to **192,000**. Other strong windows occurred around **706,000 -> 708,000** and **648,000 -> 650,000**. These gains were not isolated enough to define the whole round, but they show that Osmium and mark-to-market movements occasionally added bursts on top of Pepper's steady carry.

The main path-level lesson is that early drawdown was acceptable because the structural Pepper thesis was strong. However, if this strategy were being improved, the opening phase would be a natural place to inspect. The early loss was the largest sampled drawdown of the whole run. Cleaner staging of accumulation, or slightly better entry timing, might have improved the risk-adjusted curve without sacrificing the final carry capture.

## 6. Manual Trading Analysis

### 6.1 Final Manual Trades

The manual trading submission consisted of two buy orders. The first was **DRYLAND_FLAX**, bought for **9,999** volume at price **+30**. The displayed PnL for that trade was **+9,999**. The second was **EMBER_MUSHROOM**, bought for **19,999** volume at price **+17**. The displayed PnL for that trade was **+77,996.10**.

The combined manual PnL was therefore:

`9,999 + 77,996.10 = 87,995.10`

This matched the manual trading PnL displayed on the detailed results page.

### 6.2 Why This Manual Submission Worked

The manual screenshots show payoff curves for the selected goods. DRYLAND_FLAX produced a clean positive contribution with the submitted order. Its result was smaller than Ember Mushroom's, but it was still nearly 10,000 XIRECS. The selected bid volume of 9,999 appears to sit near the upper end of the useful volume range for that trade, producing close to the visible cap around 10,000.

EMBER_MUSHROOM was the dominant manual trade. It produced **+77,996.10**, which accounted for about **88.6%** of total manual PnL. The Ember payoff chart shows a much larger vertical PnL scale than Dryland Flax, with the selected trade landing near a very high payoff level. The selected volume of 19,999 and price of +17 were therefore the main reason the manual result achieved rank 1.

The key difference between manual and algo performance is concentration. The algo needed thousands of market observations and many Osmium fills to reach +89k. The manual submission reached +88k with only two decisions. This is why the manual rank was so strong: the final answer identified the high-value manual opportunity and sized it effectively.

### 6.3 Manual Trading Outcome

Manual trading was the most rank-efficient part of Round 1. The algorithm produced slightly more raw PnL, but the manual result ranked **1st**, while the algorithm ranked **2683rd**. This suggests that many teams found profitable algorithmic strategies, but very few matched the final manual trade combination.

From a final-round perspective, the manual result should be treated as a core part of the solution, not as an add-on. Without manual trading, the Round 1 total would have been about 89.3k. With manual trading, it became 177.3k. The manual side effectively doubled the team's Round 1 score.

## 7. Final Interpretation

### 7.1 What Went Right

The biggest thing that went right was identifying and exploiting the structural Pepper edge. The algorithm correctly prioritized early long accumulation in `INTARIAN_PEPPER_ROOT`, reached the maximum long position, and held it through a highly favorable upward path. This one decision generated the majority of algorithmic PnL.

The second thing that went right was adding Osmium as a secondary alpha stream. Osmium was not the main driver, but it added almost 10k extra PnL. Since the Pepper strategy was largely passive after initial accumulation, Osmium gave the algorithm another way to earn while waiting for the Pepper carry to accrue.

The third major success was the manual trade. The manual submission was exceptional. It produced nearly as much PnL as the entire algorithm and ranked 1st for the round. The final team result depended heavily on this.

### 7.2 What Did Not Go Perfectly

The algorithmic rank was much weaker than the manual rank. A +89k algo result was profitable, but **2683rd** indicates that the field had many stronger or comparable algorithmic submissions. The algorithm was good enough to contribute strongly to the total score, but it was not elite relative to the competition.

The Osmium ending inventory was the clearest technical issue. The strategy completed successfully and the official log was clean, but ending at **+78** on a nominally two-sided market-making product is not clean risk management. This should be improved in any future version by making the flattening logic more decisive late in the round.

The algorithm also ended with large long inventory in both products. Pepper ending at +80 was intentional and correct for this round. Osmium ending at +78 is less ideal because Osmium was supposed to be a market-making specialist. A more polished version might include stronger late-round inventory control or a stricter flattening policy.

Finally, the Pepper strategy was highly thesis-dependent. It worked because the structural upward trend existed and persisted. If that assumption had been wrong, the long-only design could have performed poorly. The strategy did not have a robust mechanism for detecting that the Pepper thesis had failed and exiting the position.

### 7.3 Lessons for Future Rounds

The first lesson is to separate primary edge from secondary edge. In Round 1, Pepper was the primary edge and Osmium was the secondary edge. The final report should make that clear because code complexity alone can be misleading. Osmium had more moving parts, but Pepper made most of the money.

The second lesson is that fill certainty can matter more than theoretical price improvement. Pepper avoided passive quoting and aggressively accumulated. That was the right choice because missing the long position would have been much more expensive than paying a few ticks of spread.

The third lesson is that execution validation and inventory validation should be stricter. Even profitable strategies should be checked for worst-case fills, final inventory, and whether a nominally market-making product is quietly becoming a directional bet.

The fourth lesson is that manual trading can dominate final scoring. The manual result nearly matched the algo result and ranked first. Future rounds should continue treating manual analysis as a first-class workstream, not a quick final step.

## 8. Final Round 1 Takeaway

Round 1 was a strong overall result built from one excellent manual submission and one profitable algorithmic submission. The manual side was the standout, earning **+87,995.10** and ranking **1st**. The algorithmic side earned **+89,306.8125** exactly, mostly by accumulating and holding `INTARIAN_PEPPER_ROOT`, with `ASH_COATED_OSMIUM` adding a smaller active-trading contribution.

The final algorithm was directionally right and profitable, but not perfect. Pepper was excellent because it captured the structural drift cleanly. Osmium was useful but messier from an inventory perspective, with a final position close to the cap. The combined Round 1 result was still very strong: **177,302 XIRECS**, overall position **1694**, and a balanced split between algorithmic and manual profit.
