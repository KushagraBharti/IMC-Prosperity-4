# Round 2 Final Report

## 1. Executive Summary

Round 2 finished with a new total score of **422,674 XIRECS** for team **ALCARAZGOAT2026**, improving the overall leaderboard position to **1410**. The Round 2 contribution was **245,372 XIRECS**, made up of **+80,708 XIRECS** from algorithmic trading and **+164,664 XIRECS** from the manual trading challenge. The previous total from Round 1 was **177,302 XIRECS**, so the displayed totals reconcile as **177,302 + 245,372 = 422,674**.

The final Round 2 result was driven more by the manual challenge than by the algorithm. The manual result ranked **236th** for the round and contributed about two thirds of the Round 2 PnL. The algorithmic result ranked **2803rd** and contributed about one third of the Round 2 PnL. This was the opposite shape from a pure algo-led round: the final team result depended heavily on getting the manual allocation mostly right.

The final algorithmic package is stored in `ROUND2-final/algo_submission/final-algo`. It contains the final code file `360502.py`, the official result file `360502.json`, and the execution log `360502.log`. The code is a Round 2 adaptation of the Round 1 approach: it keeps the same two products, keeps the aggressive long-only Pepper accumulator, simplifies/reworks the Osmium market-making logic, and adds a Round 2 market access fee bid through `Trader.bid()`. The code bid **651 XIRECS** for market access. The raw execution result in the JSON was **81,359.0**, and the log explicitly states that the platform deducted the **651.00** bid, storing the displayed final algorithmic profit as **80,708.00**.

At a product level, the algorithm was again dominated by **INTARIAN_PEPPER_ROOT**. Pepper produced **79,361.0** product-level PnL, while **ASH_COATED_OSMIUM** produced only **1,998.0** product-level PnL. The algorithm did what it was designed to do on Pepper: it bought to the +80 limit early and held the structural carry for the rest of the round. Osmium was positive, but much weaker than Round 1 and much less important to the final score.

## 2. Final Results

### 2.1 Overall Leaderboard Result

The detailed results screenshot shows team **ALCARAZGOAT2026** with overall position **1410** and total **422,674 XIRECS** after Round 2. The page also shows an upward movement indicator next to the position, so Round 2 improved the team's standing relative to the previous total.

The result breakdown shown in the screenshot is:

- Previous total: **177,302**
- Round 2 total: **245,372**
- New total PnL: **422,674**
- Algorithmic trading result: **+80,708**
- Algorithmic round ranking: **2803rd**
- Manual trading result: **+164,664**
- Manual round ranking: **236th**
- Mission progress: **100%**
- Team goal shown: **422,674 of 200,000**
- Crew honors: **14 badges unlocked**

The important interpretation is that Round 2 was a strong total-score round despite the algorithmic rank being moderate. The manual component was the major differentiator. The algorithm still produced a meaningful positive result, but the manual allocation was what made the Round 2 total large.

### 2.2 Algorithmic Trading Result

The screenshot displays algorithmic trading PnL as **+80,708 XIRECS**. The exact result files explain how that number was produced. In `360502.json`, the raw execution `profit` is **81,359.0**. In `360502.log`, the only non-empty sandbox log message says:

`Deducting bid 651.00 from current execution 360502 profit 81359.0. Result will be stored as final profit of 80708.00`

So the algorithmic accounting is:

`81,359.0 raw trading profit - 651.0 market access fee = 80,708.0 displayed final algorithmic profit`

This distinction matters because the actual trading system made **81,359.0** before fees, but the competition result was **80,708.0** after paying the market access bid. The fee was not a normal trade loss; it was the Round 2 bid mechanism.

The final JSON export reports these ending positions:

- `INTARIAN_PEPPER_ROOT`: **+80**
- `ASH_COATED_OSMIUM`: **+80**
- `XIRECS`: **-1,918,514**

Both tradeable products ended exactly at the positive position limit of **+80**. For Pepper, this was fully consistent with the intended long-carry design. For Osmium, it is more mixed. The Osmium strategy was meant to recycle inventory around a stable fair value, so ending at the maximum long position shows that the final state was directional and inventory-heavy.

The algorithmic PnL chart in the screenshot is mostly upward sloping. It starts slightly below zero, climbs steadily through the full timestamp range, and finishes a little above 80,000 after the fee adjustment. The path was not perfectly smooth, but the drawdowns were small relative to final profit. This shape matches the logs: Pepper generated a near-linear carry stream, while Osmium added smaller and more uneven profit.

### 2.3 Manual Trading Result

The Round 2 manual trading screenshot shows a different type of manual challenge from Round 1. Instead of choosing buy/sell orders for goods, the team allocated budget across three levers:

- **Research**: **18% invested**
- **Scale**: **57% invested**
- **Speed**: **25% invested**

The displayed formula was:

`Research(x) * Scale(y) * Hit_Rate(Rank(z)) - Budget = PnL`

The visible output boxes show:

- Strategy XIRECS from research: **127,600**, logarithmic
- Scale multiplier: **x 4.0**, linear
- Hit rate: **0.42**, with rank **#2574**
- Total before budget: **214,664**
- Budget: **-50,000**
- Final manual trading PnL: **164,664**

The displayed values are rounded in the UI, so multiplying the rounded visible components does not exactly reproduce the displayed total. Conceptually, though, the logic is clear: research generated the base strategy value, scale multiplied that value, speed determined the hit rate through competitive rank, and the fixed/used budget was subtracted at the end.

The manual result ranked **236th**, which was much stronger than the algorithmic rank of **2803rd**. It also contributed **164,664 / 245,372**, or roughly **67%** of the full Round 2 score. This was the decisive part of Round 2.

## 3. Files Submitted

### 3.1 Algo Submission Package

The final algorithmic package is located at:

`ROUND2-final/algo_submission/final-algo`

It contains:

- `360502.py`: the final Round 2 Python strategy.
- `360502.json`: the official result export with raw profit, activities log, graph log, and final positions.
- `360502.log`: the execution log with submission ID, activities log, timestamped logs, and trade history.
- `final-algo.zip`: the archived final package, stored one level above the extracted folder.

The submission ID in `360502.log` is:

`2c68831d-52d4-4edf-ad1a-5aa9cffa77c8`

The JSON result reports:

- Round: **2**
- Status: **FINISHED**
- Raw profit before market access fee: **81,359.0**
- Final displayed profit after fee: **80,708.0**, based on the log deduction
- Final Pepper position: **+80**
- Final Osmium position: **+80**

The `.json` file contains the product-level activities log and sampled graph log. The `.log` file contains the same activities log plus the timestamped sandbox/lambda logs and the trade history. Unlike Round 1, the Round 2 log did not contain repeated position-limit warnings. It contained only one non-empty sandbox message, and that message was the expected market-access-fee deduction.

### 3.2 Hand Trade Submission

The final manual submission, based on the screenshot, was:

- Research: **18%**
- Scale: **57%**
- Speed: **25%**

This allocation produced:

- Total before budget: **214,664**
- Budget cost: **50,000**
- Final manual PnL: **164,664**
- Manual round ranking: **236th**

There is no separate structured manual submission file currently stored in `ROUND2-final/hand_trade_submission`. The final manual answer is therefore recorded from the screenshot values above.

## 4. Algorithm Design: What the Code Actually Does

### 4.1 Products Traded

The final Round 2 algo trades the same two products as Round 1:

- `ASH_COATED_OSMIUM`
- `INTARIAN_PEPPER_ROOT`

Both products have a hard position limit of **80** units. The code initializes empty order lists for both products on every call, reads each product's order book if available, updates rolling cache features, and delegates the actual order generation to a product-specific strategy.

The biggest Round 2 structural addition is the market access fee bid. The `Trader` class defines:

`MARKET_ACCESS_FEE_BID = 651`

and exposes it through:

`def bid(self): return self.MARKET_ACCESS_FEE_BID`

That means the strategy chose to bid **651 XIRECS** for the Round 2 market access mechanism. The final log confirms that the bid was charged, so the bid was accepted or otherwise applied by the official engine. The fee reduced the final displayed algorithmic score from **81,359.0** to **80,708.0**.

### 4.2 Shared Infrastructure

The strategy uses the same general infrastructure as the Round 1 final algo. It loads a JSON cache from `traderData`, stores rolling histories, computes book snapshots, and returns the updated cache as compact JSON. The cache is limited to **40** historical observations per feature.

For every product, the strategy computes:

- Sorted buy orders and sell orders.
- Best bid and best ask.
- Mid price.
- Wall mid price.
- Top-of-book imbalance.
- Whether the book has both sides.

The **mid price** is the average of best bid and best ask when both exist. If the book is one-sided, it falls back to the available side. The **wall mid** is the average of the price with the largest bid-side volume and the price with the largest ask-side volume. This is meant to capture where visible size is concentrated. The **top imbalance** compares best bid volume to best ask volume and produces a value between -1 and +1 when both sides exist.

The strategy also has two different limit filters:

- `ensure_within_limits` is used for Osmium and permits both long and short positions within the 80-unit limit.
- `enforce_long_only_limit` is used for Pepper and permits only positions from 0 to +80.

The Round 2 `ensure_within_limits` implementation is more careful than the sequential Round 1 version. It separates buy orders from sell orders, tracks remaining buy and sell capacity, and trims order quantities if needed. It also prioritizes better prices first: lower prices for buys and higher prices for sells. This is likely why the Round 2 log avoided the repeated Osmium limit warnings that appeared in Round 1.

### 4.3 ASH_COATED_OSMIUM Strategy

The Round 2 Osmium strategy is simpler and more explicitly fixed-fair than the Round 1 Osmium strategy. It sets:

`OSMIUM_FAIR = 10002.0`

The comment in the code explains the reason: Osmium remains mean-reverting, but the hidden replay is believed to be richer than a perfectly symmetric 10,000-fair view, so the strategy biases fair slightly upward. Unlike Round 1, the Round 2 Osmium logic does not compute a dynamic alpha from wall-mid deviation, imbalance, and trends. It mostly uses a stable fair value and inventory-based execution rules.

The strategy has three main execution components.

First, it aggressively takes visible favorable orders. It scans up to three ask levels and buys if the ask is below fair, or if inventory is too short and the edge is at least neutral. It scans up to three bid levels and sells if the bid is above fair, or if inventory is too long and the edge is at least neutral. The take size is **12** normally and **24** when edge is at least 2.

Second, it tries to flatten inventory when position becomes too large. If position is above `OSMIUM_FLATTEN_TRIGGER = 18`, it places a sell order around fair or better. If position is below -18, it places a buy order around fair or better. This is intended to recycle risk so the strategy can keep harvesting spread rather than getting stuck at an inventory extreme.

Third, it places passive quotes. The primary passive bid is usually one tick above best bid but capped around 10001/10000 depending on inventory. The primary passive ask is usually one tick below best ask but floored around 10003/10004 depending on inventory. It also layers a secondary passive order at the current top of book with size **4**. The code comment says this was intended to harvest more neutral flow without changing the core fair-value logic.

The final result shows that this Osmium design was safe but not very profitable. It ended positive, but only by **1,998.0** product-level PnL. It also ended at **+80**, meaning that despite the flattening logic, the strategy finished fully long.

### 4.4 INTARIAN_PEPPER_ROOT Strategy

The Pepper strategy is effectively the same structural idea as Round 1: aggressively accumulate the long carry. It assumes Pepper has a persistent upward trend of:

`PEPPER_TREND_PER_TIMESTAMP = 0.001`

It estimates an anchor from the observed midpoint:

`observed_anchor = mid - timestamp * 0.001`

and smooths that anchor with:

`PEPPER_ANCHOR_SMOOTHING = 0.10`

The forward fair value is then:

`base_fair + PEPPER_FORWARD_PREMIUM + alpha`

where `PEPPER_FORWARD_PREMIUM = 8.5`. The alpha includes wall-mid deviation, top-of-book imbalance, wall-mid trend, imbalance trend, and mid-price trend. The alpha is clipped between **-4.0** and **+4.0**.

The target position logic strongly prefers being long. The base target is **78**, the minimum target is **64**, and the maximum target is **80**. Because `PEPPER_TARGET_SLOPE = 0`, alpha does not materially reduce the target. Positive imbalance can add a small target bonus, but the strategy is already near the limit by default.

Pepper execution is aggressive but controlled. It only sweeps the first ask level. If the strategy is far from target, it can buy even when edge is slightly negative, using a catch-up threshold as low as **-1.00**. If it is closer to target, it uses a less permissive catch-up threshold of **-0.35**. This lets it build inventory early without recklessly sweeping every visible level.

Passive Pepper quoting is effectively disabled. The passive gap trigger is **999** and passive max size is **0**, so the strategy does not rely on resting bids. This is intentional. The strategy values fill certainty over maker-edge optimization because the main Pepper edge comes from holding the long position through the round.

## 5. Algorithm Performance Analysis From JSON and Logs

### 5.1 Overall Equity Curve

The raw JSON profit is **81,359.0**, and the final displayed algorithmic score after deducting the **651** market access fee is **80,708.0**. The graph log contains **500 sampled points**. It starts at **0.0**, reaches a minimum of **-1,195.875**, and ends at **81,061.625** on the sampled graph. The graph's last sampled value is close to, but not exactly equal to, the raw final profit because the graph is sampled every 2,000 timestamp units and does not represent the final accounting field exactly.

The largest sampled drawdown was **1,195.875**, from timestamp **0** to timestamp **2,000**. This was the same general pattern as Round 1: the algorithm took its largest mark-to-market hit early while building positions. After the initial drawdown, the equity curve recovered and trended upward for the rest of the round.

The worst sampled graph moves were:

- Timestamp **0 -> 2,000**: **-1,195.875**
- Timestamp **758,000 -> 760,000**: **-271.0625**
- Timestamp **44,000 -> 46,000**: **-131.875**
- Timestamp **876,000 -> 878,000**: **-124.625**
- Timestamp **150,000 -> 152,000**: **-109.3125**

The best sampled graph moves were:

- Timestamp **980,000 -> 982,000**: **+545.6875**
- Timestamp **848,000 -> 850,000**: **+501.5**
- Timestamp **112,000 -> 114,000**: **+470.4375**
- Timestamp **986,000 -> 988,000**: **+448.3125**
- Timestamp **412,000 -> 414,000**: **+435.375**

The graph is best understood as Pepper's steady carry plus a small, noisy Osmium overlay. The line rises persistently because Pepper is long and the product keeps trending upward. The smaller pullbacks and jumps are mostly the result of mark-to-market changes and the much less stable Osmium component.

### 5.2 Product-Level PnL Breakdown

The activities log contains **20,000 rows**, with **10,000 rows** for each product. The final product-level PnL split is:

- `INTARIAN_PEPPER_ROOT`: **79,361.0**
- `ASH_COATED_OSMIUM`: **1,998.0**

The two product PnLs sum to the raw JSON profit:

`79,361.0 + 1,998.0 = 81,359.0`

After the market access fee:

`81,359.0 - 651.0 = 80,708.0`

This means Pepper produced about **97.5%** of raw algorithmic trading PnL, while Osmium produced only about **2.5%**. The final algo was therefore overwhelmingly a Pepper carry strategy. Osmium was positive, but it was not a major contributor.

Pepper's product-level PnL path was extremely clean. It started at **0.0**, hit a minimum of **-559.0** at timestamp **900**, and finished at its maximum of **79,361.0** at timestamp **999,900**. Its bucket-end PnL by 100,000 timestamp windows was:

- 0-99,999: **7,361.0**
- 100,000-199,999: **15,361.0**
- 200,000-299,999: **23,361.0**
- 300,000-399,999: **31,361.0**
- 400,000-499,999: **39,361.0**
- 500,000-599,999: **47,361.0**
- 600,000-699,999: **55,361.0**
- 700,000-799,999: **63,361.0**
- 800,000-899,999: **71,361.0**
- 900,000-999,999: **79,361.0**

This is almost perfectly linear and confirms that the Pepper thesis remained valid in Round 2. The strategy bought early, held +80, and monetized the structural upward drift.

Osmium was much weaker. It started at **0.0**, reached a minimum of **-849.125** at timestamp **6,500**, reached a maximum of **2,009.9375** at timestamp **995,700**, and finished at **1,998.0**. Its bucket-end PnL was:

- 0-99,999: **-9.6875**
- 100,000-199,999: **-141.375**
- 200,000-299,999: **1,310.25**
- 300,000-399,999: **880.875**
- 400,000-499,999: **-149.125**
- 500,000-599,999: **245.75**
- 600,000-699,999: **664.6875**
- 700,000-799,999: **1,394.25**
- 800,000-899,999: **909.9375**
- 900,000-999,999: **1,998.0**

Unlike Pepper, Osmium did not produce a clean monotonic path. It moved between small profits and losses for much of the run and only became clearly positive late. This means the Round 2 Osmium logic was not a strong edge source. It helped, but only modestly.

### 5.3 Pepper: Where It Did Well

Pepper did exactly what it was supposed to do. The trade history shows **9 submission fills** in Pepper, all in the first 100,000 timestamp bucket. Those fills bought a total of **80 units**, and there were no submission sells. The final position was **+80**.

This confirms that the strategy reached maximum long exposure early and then held. That was the right behavior for the Round 2 market. Pepper's PnL rose from early drawdown to final maximum with near-mechanical consistency. The product's final PnL of **79,361.0** was almost the entire algorithmic result before fees.

The strength of Pepper also confirms the research premise from the Round 2 planning files: Pepper remained an almost linear trend product. The public research notes described Pepper as having an approximate fitted slope of **0.001** with very high linear fit, and the final official log behaved exactly like that assumption. The final strategy did not need complex Pepper trading. It needed early long exposure and patience.

### 5.4 Pepper: Weaknesses and Tradeoffs

The main Pepper weakness is the same as in Round 1: it is thesis-dependent. The strategy is not designed to be neutral. It assumes that long Pepper exposure is structurally profitable and therefore pushes toward a high target between **64** and **80**, with a base target of **78**. If the structural trend had failed, the algorithm would have had little protection.

The early product-level drawdown of **-559.0** at timestamp **900** shows the cost of accumulation. The strategy was willing to buy early even if immediate mark-to-market was negative. That was correct in this round, but it is still a risk. It works only when the later carry is large enough to overwhelm the entry cost.

Another limitation is that Pepper did not benefit much from active optimization after reaching +80. Once the position was full, the strategy mostly became a hold-to-end carry trade. That made the result robust and simple, but it also means the algorithmic ceiling was tied to the fixed position limit. After reaching +80, there was no way for Pepper to scale further.

### 5.5 Osmium: Where It Did Well

Osmium did at least finish positive. It contributed **1,998.0** raw PnL and reached a maximum of **2,009.9375** near timestamp **995,700**. It also avoided the repeated position-limit warnings that appeared in Round 1. The Round 2 log had only one non-empty sandbox entry, and that entry was the fee deduction, not an error or order-limit warning.

The improved order filtering is a real positive. The Round 2 `ensure_within_limits` function trims order quantities by remaining buy and sell capacity and prioritizes better prices first. This produced a cleaner execution log. Even though Osmium was less profitable than in Round 1, it was technically cleaner from a platform-compliance perspective.

Osmium also gave some diversification away from pure Pepper carry. If Pepper had remained profitable but slightly weaker, any positive Osmium contribution would still have helped. In the final result, however, the diversification value was small because the absolute contribution was only about 2.5% of raw algo profit.

### 5.6 Osmium: Weaknesses and Issues

The main Osmium issue is that it did not make much money. Round 1 Osmium added about **9,923.8125** product-level PnL. Round 2 Osmium added only **1,998.0**. That is a large drop in contribution. The Round 2 simplification to a mostly fixed fair of **10002.0** made the strategy cleaner, but it may also have removed useful dynamic alpha from the Round 1 version.

The Osmium path was also choppy. It was negative at the end of several 100,000-timestamp windows, including **-141.375** at the end of the 100,000-199,999 bucket and **-149.125** at the end of the 400,000-499,999 bucket. It did not establish a strong positive contribution until later.

The final position was **+80**, exactly at the long limit. That is not ideal for a mean-reversion / market-making product. It means the strategy ended fully exposed rather than flat or near neutral. The code had inventory flattening logic, but the actual final state shows that the logic did not prevent ending at the cap. This could have been harmless in the official replay, but it is not a clean risk posture.

The trade history also shows that Osmium was much less active than Round 1. Round 1 had **858** submission Osmium fills. Round 2 had only **63** submission Osmium fills. Round 2 Osmium bought **182** units and sold **102** units, netting to the final **+80** position. This is far less turnover and suggests the Round 2 Osmium implementation was more passive and less able to harvest spread repeatedly.

### 5.7 Trade History Diagnostics

The final log's `tradeHistory` contains **897** rows. Of these, **519** are Osmium trades and **378** are Pepper trades. Submission participation was concentrated in a small number of fills:

Pepper trade history summary:

- Total Pepper trade history rows: **378**
- Submission Pepper fills: **9**
- Submission Pepper buy quantity: **80**
- Submission Pepper sell quantity: **0**
- Final Pepper position: **+80**

Osmium trade history summary:

- Total Osmium trade history rows: **519**
- Submission Osmium fills: **63**
- Submission Osmium buy quantity: **182**
- Submission Osmium sell quantity: **102**
- Net submission fill quantity: **+80**
- Final Osmium position: **+80**

The Pepper behavior is simple and strong: buy to the limit and hold. The Osmium behavior is more ambiguous. It traded both sides, but not very often, and the net result was still a maximum long position.

Submission Osmium activity by 100,000 timestamp bucket:

- 0-99,999: **6 fills**, buy 80, sell 0
- 100,000-199,999: **2 fills**, buy 2, sell 2
- 200,000-299,999: **5 fills**, buy 5, sell 15
- 300,000-399,999: **23 fills**, buy 53, sell 43
- 400,000-499,999: **2 fills**, buy 2, sell 2
- 600,000-699,999: **4 fills**, buy 6, sell 6
- 700,000-799,999: **10 fills**, buy 15, sell 15
- 800,000-899,999: **4 fills**, buy 4, sell 4
- 900,000-999,999: **7 fills**, buy 15, sell 15

The most important bucket is the first one. Osmium bought **80** units in the opening 100,000 timestamp bucket and ended the round at **+80**, despite some later two-sided recycling. That means the strategy effectively became long Osmium early. Since Osmium only produced **1,998.0**, this long exposure did not hurt badly, but it also did not generate a large edge.

### 5.8 Log Health and Market Access Fee Diagnostics

Round 2 log health was much cleaner than Round 1. There were **10,000** timestamped log entries, but only **1** non-empty sandbox/lambda message. That message was not an error. It was the fee deduction:

`Deducting bid 651.00 from current execution 360502 profit 81359.0. Result will be stored as final profit of 80708.00`

There were no repeated warnings about exceeding product limits. This is a meaningful improvement from Round 1, where Osmium produced many position-limit warnings. The final Round 2 code was therefore cleaner operationally, even though its Osmium PnL was weaker.

The market access bid itself was small relative to the algorithmic result. A **651** fee reduced raw algorithmic profit by about **0.8%**. Since the final score still remained above 80k, the fee was not damaging. However, the logs alone do not prove that the extra access was worth more than 651. The fee was cheap enough that it did not need to create a large benefit to be acceptable.

## 6. Manual Trading Analysis

### 6.1 Final Manual Allocation

The final manual allocation shown in the screenshot was:

- Research: **18%**
- Scale: **57%**
- Speed: **25%**

The displayed manual formula was:

`Research(x) * Scale(y) * Hit_Rate(Rank(z)) - Budget = PnL`

The resulting displayed components were:

- Strategy XIRECS: **127,600**
- Scale multiplier: **x 4.0**
- Speed hit rate: **0.42**
- Speed rank: **#2574**
- Total: **214,664**
- Budget: **-50,000**
- Manual trading PnL: **164,664**

This was a strong result. The manual ranking was **236th**, which means the final allocation beat the overwhelming majority of teams even though the speed rank shown inside the formula was only **#2574**.

### 6.2 Why This Manual Submission Worked

The manual challenge required balancing three competing uses of budget. Research increased base strategy value, but the UI indicates it was logarithmic, so each additional research point had diminishing returns. Scale applied a linear multiplier, so it rewarded larger investment more directly. Speed determined a hit rate based on rank, so it was competitive: the value of speed depended not only on the team's allocation but also on what other teams chose.

The final allocation leaned heavily into **Scale** at **57%**. This made sense because scale was linear and directly multiplied the researched strategy value. The allocation still invested **18%** into Research, enough to create a large base strategy value of about **127,600** displayed XIRECS. It invested **25%** into Speed, which produced a displayed hit rate of **0.42**.

The result suggests that the team chose a relatively efficient middle ground. It did not overpay for speed, but it invested enough speed to avoid an extremely low hit rate. It put most of the remaining budget into scale, where the return was linear. That combination generated a large pre-budget total of **214,664**, and after the **50,000** budget cost, the final manual PnL was still **164,664**.

The internal planning file had earlier discussed a possible **15 / 44 / 41** allocation, emphasizing a higher speed investment. The final submitted allocation was different: **18 / 57 / 25**. In hindsight, the final lower-speed, higher-scale allocation performed well. The hit rate was only **0.42**, but the higher scale multiplier made the final PnL strong enough to rank **236th**.

### 6.3 Manual Trading Outcome

Manual trading was the dominant part of Round 2. It contributed **164,664** out of **245,372** Round 2 XIRECS. That is roughly **67%** of the round's score. The algorithm contributed **80,708**, or roughly **33%**.

The manual rank was also much better than the algorithmic rank. Manual ranked **236th**, while algo ranked **2803rd**. This means the final Round 2 score was not mainly a result of a top-tier algorithm. It was a result of a very strong manual allocation combined with a solid but not elite algorithmic submission.

The main manual tradeoff was speed. A higher speed allocation may have improved hit rate, but it would have reduced research or scale. The final result shows that the chosen allocation was strong enough: the hit rate did not need to be near the top of the field because the research and scale components generated a high gross total.

## 7. Final Interpretation

### 7.1 What Went Right

The biggest success in the algorithm was preserving the Pepper carry thesis. Pepper again behaved like the dominant structural edge. The strategy bought to **+80** early and held the position, producing **79,361.0** product-level PnL. Without Pepper, the algorithmic submission would have been weak.

The second success was operational cleanliness. The Round 2 algo avoided the repeated order-limit warnings that appeared in Round 1. The only non-empty log message was the expected **651** market access fee deduction. The code's revised limit filtering likely helped.

The third and most important Round 2 success was the manual allocation. The **18 / 57 / 25** allocation produced **164,664** PnL and ranked **236th**. It more than doubled the algorithmic contribution and was the main reason Round 2 added **245,372** total XIRECS.

### 7.2 What Did Not Go Perfectly

The algorithmic rank was only **2803rd**, so the algo was profitable but not highly competitive. Its final score was mostly a known Pepper carry capture rather than a diversified set of strong edges.

Osmium was the weakest part of the algorithm. It contributed only **1,998.0** product-level PnL and ended at the **+80** limit. Compared with Round 1's much stronger Osmium contribution, this was a major drop. The simplified fixed-fair strategy was cleaner but less profitable.

The market access fee was small, but the logs do not prove that it created meaningful incremental value. It cost only **651**, so it was not harmful, but the final report should not overstate it as a clear source of edge.

The manual result was strong but not perfect. The speed hit rate was **0.42**, with displayed rank **#2574**, so the speed component was not elite. The allocation won because research and scale compensated strongly. A better speed/rank prediction might have improved the manual result further.

### 7.3 Lessons for Future Rounds

The first lesson is that the best edge should remain the center of the strategy. In Round 2, that was still Pepper. The algorithm's success came from not overcomplicating the product that already had the clearest structural behavior.

The second lesson is that clean execution matters, but clean execution alone is not enough. Round 2 Osmium was operationally cleaner than Round 1 Osmium, but it made much less money. A future strategy should combine Round 2's safer order filtering with a stronger alpha model.

The third lesson is that fees must be analyzed separately from trading PnL. The raw algo made **81,359.0**, but the final displayed algo result was **80,708.0** after the market access bid. Any future round with fees or bids should report raw and net PnL separately.

The fourth lesson is that manual allocation can dominate the round. Round 2 manual PnL was more than twice the algorithmic net PnL. Manual challenges should be treated as a full optimization problem, not as a secondary task.

## 8. Final Round 2 Takeaway

Round 2 was a strong total-score round built around an excellent manual result and a solid Pepper-driven algorithm. The final Round 2 score was **245,372 XIRECS**, bringing the team's total to **422,674 XIRECS** and improving the overall position to **1410**.

The algorithm made **81,359.0** before fees and **80,708.0** after the **651** market access bid. Almost all of that came from `INTARIAN_PEPPER_ROOT`, which contributed **79,361.0**. `ASH_COATED_OSMIUM` was positive but weak at **1,998.0**. The algo was clean from a logging and limit-warning perspective, but it was not a top-ranked algorithmic submission.

The manual challenge was the standout. The final **18% Research / 57% Scale / 25% Speed** allocation produced **164,664 XIRECS** and ranked **236th**. That manual performance was the main reason Round 2 was successful overall.
