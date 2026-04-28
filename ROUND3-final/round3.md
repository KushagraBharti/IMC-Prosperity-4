# Round 3 Final Report

## 1. Executive Summary

Round 3 finished with a total score of **154,829 XIRECS** for team **ALCARAZGOAT2026**, placing the team at **position 382** on the detailed results screenshot. The score came from two strong and relatively balanced components: the algorithmic submission produced **+76,114 XIRECS**, and the manual trading submission produced **+78,715 XIRECS**. The manual result ranked **52nd**, while the algorithmic result ranked **407th**.

The Round 3 result page shows **Previous Total = 0**, **Round 3 Total = 154,829**, and **New Total PnL = 154,829**. This means the screenshot is a standalone Round 3 result context rather than a cumulative continuation of the earlier Round 1 and Round 2 screenshots. The displayed score reconciles exactly: **76,114 + 78,715 = 154,829**.

The final algorithmic package is stored under `ROUND3-final/algo_submission/final-algo`. It contains `486387.py`, `486387.json`, and `486387.log`. This algorithm is materially different from the Round 1 and Round 2 strategies. Instead of trading only two products, it trades a full Round 3 market with **HYDROGEL_PACK**, **VELVETFRUIT_EXTRACT**, and multiple **VEV voucher** products. The code combines stable/dynamic fair-value trading for delta-one products with Black-Scholes relative-value trading for vouchers.

The official JSON result reports exact algorithmic profit of **76,114.025390625**, which rounds to the displayed **76,114**. Product-level attribution shows that the largest contributors were **VEV_5000**, **VELVETFRUIT_EXTRACT**, **VEV_5100**, **VEV_5200**, **HYDROGEL_PACK**, and **VEV_5300**. Several vouchers were present in the market data but not traded by the submission, producing zero PnL. The log was clean: **0 non-empty sandbox or lambda messages**, so there were no platform warnings, errors, fee deductions, or limit warnings.

The manual trading result was also excellent. The final manual submission used two bid prices, **765** and **860**, generating total buy price **614,045**, total sell price **692,760**, and final manual PnL **78,715**. The manual result ranked **52nd**, making it the stronger ranking component of the round.

## 2. Final Results

### 2.1 Overall Leaderboard Result

The detailed Round 3 results screenshot shows:

- Team: **ALCARAZGOAT2026**
- Position: **382**
- Total XIREC: **154,829**
- Previous Total: **0**
- Round 3 Total: **154,829**
- New Total PnL: **154,829**
- Algorithmic Trading Result: **+76,114**
- Algorithmic Round Ranking: **407th**
- Manual Trading Result: **+78,715**
- Manual Round Ranking: **52nd**
- Crew honors: **14 badges unlocked**

This was a strong round across both components. Unlike Round 2, where manual trading dominated the total, Round 3 was nearly balanced between manual and algorithmic PnL. Manual contributed slightly more raw PnL and had the better rank, but the algorithm also ranked well and contributed almost half of the total score.

In percentage terms:

- Algorithmic contribution: about **49.2%** of total Round 3 PnL.
- Manual contribution: about **50.8%** of total Round 3 PnL.

The important takeaway is that Round 3 was not carried by only one side. Both the algo and manual submissions were competitive.

### 2.2 Algorithmic Trading Result

The screenshot displays algorithmic trading PnL as **+76,114 XIRECS**. The exact value in `486387.json` is **76,114.025390625**, which explains the rounded display.

The algorithmic result ranked **407th**, which is significantly stronger than the algorithmic ranks from Rounds 1 and 2. The PnL chart in the screenshot is much more volatile than the Round 1 and Round 2 charts. It does not show a smooth monotonic carry curve. Instead, it shows a fast early jump, a long volatile middle section, a deep mid-round drawdown, and a strong late recovery into the final result.

The final JSON positions were:

- `HYDROGEL_PACK`: **+108**
- `VELVETFRUIT_EXTRACT`: **+200**
- `VEV_5000`: **+300**
- `VEV_5100`: **+300**
- `VEV_5200`: **+300**
- `VEV_5300`: **+300**
- `XIRECS`: **-2,191,854**

The final inventory is very important. The strategy ended long the underlying-style products and max long several active vouchers. `VELVETFRUIT_EXTRACT` finished at its +200 limit. The active vouchers `VEV_5000`, `VEV_5100`, `VEV_5200`, and `VEV_5300` all finished at their +300 limits. This means the final score was not produced by flat arbitrage alone; it was produced by a relative-value strategy that carried large long exposure into the end of the round.

### 2.3 Manual Trading Result

The manual screenshot shows two bid rows:

- Bid price **765**
  - Accepted: **353**
  - Rejected: **647**
  - Buy price: **270,045**
  - Sell price: **324,760**
  - PnL: **54,715**

- Bid price **860**
  - Accepted: **400**
  - Rejected: **600**
  - Buy price: **344,000**
  - Sell price: **368,000**
  - PnL: **24,000**

The manual totals shown at the bottom were:

- Total buy price: **614,045**
- Total sell price: **692,760**
- Manual PnL: **78,715**

These reconcile exactly:

`692,760 - 614,045 = 78,715`

The manual chart also shows bid distribution information. The average first bid was **768**, the lowest first bid was **765**, the average second bid was **859**, and the highest second bid was **860**. The team's submitted bids were therefore positioned at important distribution boundaries: the first bid was exactly the displayed lowest bid, and the second bid was exactly the displayed highest bid. The result was strong enough to rank **52nd** for manual trading.

## 3. Files Submitted

### 3.1 Algo Submission Package

The final algorithmic package is located at:

`ROUND3-final/algo_submission/final-algo`

It contains:

- `486387.py`: the final Round 3 strategy code.
- `486387.json`: the official result export with exact profit, activities log, graph log, and final positions.
- `486387.log`: the official execution log with submission ID, activities log, timestamped logs, and trade history.
- `final-algo.zip`: the archived final package, stored in `ROUND3-final/algo_submission`.

The submission ID in `486387.log` is:

`a3558e94-f71d-4c99-bfbc-4ec05ebf4f92`

The JSON result reports:

- Round: **3**
- Status: **FINISHED**
- Exact profit: **76,114.025390625**
- Displayed rounded profit: **76,114**
- Final long positions in Hydrogel, VFE, and four active vouchers.

The `.json` file contains a very large `activitiesLog` and a sampled `graphLog`. The `.log` file contains the same activities log plus timestamped logs and `tradeHistory`. The timestamped logs were fully clean: there were **10,000** log entries and **0** non-empty sandbox/lambda messages.

### 3.2 Hand Trade Submission

The final manual result is recorded from the screenshots as:

- First bid: **765**
- Second bid: **860**
- Total accepted across both rows: **753**
- Total rejected across both rows: **1,247**
- Total buy price: **614,045**
- Total sell price: **692,760**
- Final manual PnL: **78,715**
- Manual round ranking: **52nd**

There is no separate structured manual submission file currently stored in `ROUND3-final/hand_trade_submission`; the final manual answer is therefore documented directly in this report from the result screenshots.

## 4. Algorithm Design: What the Code Actually Does

### 4.1 Products Traded

The final Round 3 algorithm covers three families of instruments:

- **HYDROGEL_PACK**
- **VELVETFRUIT_EXTRACT**
- **VEV vouchers**

The voucher universe in the code is:

- `VEV_4000`
- `VEV_4500`
- `VEV_5000`
- `VEV_5100`
- `VEV_5200`
- `VEV_5300`
- `VEV_5400`
- `VEV_5500`
- `VEV_6000`
- `VEV_6500`

However, not all vouchers are actively traded. The code defines the active voucher subset as:

- `VEV_5000`
- `VEV_5100`
- `VEV_5200`
- `VEV_5300`
- `VEV_5500`

In the official result, the strategy actually generated PnL only in `VEV_5000`, `VEV_5100`, `VEV_5200`, and `VEV_5300`. `VEV_5500` was in the active list, but the official result shows zero final PnL and zero submission fills for it. The deep in-the-money vouchers `VEV_4000` and `VEV_4500`, and the far out-of-the-money vouchers `VEV_6000` and `VEV_6500`, were not traded by the submission.

Position limits are:

- `HYDROGEL_PACK`: **200**
- `VELVETFRUIT_EXTRACT`: **200**
- Every VEV voucher: **300**

The final positions show that the strategy used those limits aggressively. It ended at +200 VFE and +300 in four vouchers.

### 4.2 Shared Infrastructure

The code uses a compact set of helper functions to normalize order books:

- `get_bids` returns sorted buy orders from highest bid to lowest bid.
- `get_asks` converts negative sell volumes into positive available quantities and sorts asks from lowest to highest.
- `best_bid` and `best_ask` extract top-of-book prices.
- `mid_price` computes the midpoint when both sides exist, falling back to one side when necessary.
- `wall_mid_and_imbalance` computes a wall-based midpoint and top-of-book imbalance.

The strategy also defines an `OrderBuilder` class. This is an important improvement in execution hygiene. The builder tracks current position, product limit, planned buys, and planned sells. When adding a buy, it caps quantity by remaining buy capacity. When adding a sell, it caps quantity by remaining sell capacity. This prevents generated orders from exceeding limits under the strategy's own order plan.

The clean official log confirms that this order-building layer worked operationally. There were no position-limit warnings, no lambda errors, and no sandbox warnings.

### 4.3 HYDROGEL_PACK Strategy

Hydrogel is traded as a dynamic fair-value product. The code comments say that Hydrogel is path-dependent enough that a static active-fill model overtrades downturns, so the strategy uses a dynamic fair and signal gate.

The key Hydrogel parameters are:

- Default fair: **9991.0**
- Anchor smoothing: **0.05**
- Imbalance weight: **10.5**
- Deviation weight: **0.04**
- Trend weight: **0.03**
- Signal threshold: **1.1**
- Take edge: **10.0**
- Maker edge: **4.0**
- Quote size: **72**
- Take size: **80**
- Soft limit: **200**
- Flatten trigger: **130**

The Hydrogel fair value is computed by `compute_linear_fair`. The algorithm updates a smoothed anchor from observed mid prices, stores a rolling history, compares short and long moving averages, and adjusts fair value using imbalance, deviation, and trend. This means Hydrogel is not treated as a static 10,000 product. The model adapts to path changes and uses signal gating before placing quotes.

Execution has three components. First, it aggressively takes asks or bids only when edge is at least **10.0**, so aggressive fills require a large margin. Second, if inventory exceeds the flatten trigger, it places flattening orders around fair. Third, if signal is strong enough but not in flattening mode, it places passive quotes with maker edge protection.

This design was profitable overall but volatile. Hydrogel finished at **+7,903.5** PnL, but it also had a minimum of **-2,319.75** and a maximum of **11,421.625**. That means Hydrogel contributed positively, but it was not stable throughout the round.

### 4.4 VELVETFRUIT_EXTRACT Strategy

VELVETFRUIT_EXTRACT, or VFE, is treated as the underlying for the voucher complex. The strategy estimates VFE fair value from a fixed anchor and from deep-voucher-implied values.

The key VFE parameters are:

- Base anchor: **5260.0**
- Anchor weight: **0.55**
- Take edge: **5.0**
- Inventory skew: **0.0025**
- Take size: **70**
- Passive size: **24**

The VFE fair function starts with the base anchor of **5260.0**. It then looks at `VEV_4000` and `VEV_4500`. Since those vouchers are deep in-the-money, their mid prices can imply the underlying value by adding back the strike. If `VEV_4000` is available, the code uses `mid_4000 + 4000`; if `VEV_4500` is available, it uses `mid_4500 + 4500`. These implied values are combined with weights and blended with the fixed anchor.

This is a smart structural idea: the deep vouchers are not actively traded as alpha products, but they are used as information about the underlying. The strategy uses them to estimate VFE fair value, then trades VFE directly when market prices are far enough away from that fair.

VFE execution is active and passive. It aggressively buys asks when `fair_adj - ask >= 5.0`, sells bids when `bid - fair_adj >= 5.0`, and places light passive quotes around fair with a two-point buffer. The code also applies a small inventory skew so that the fair adjustment becomes less aggressive as position grows.

In the official result, VFE was the second-largest contributor after `VEV_5000`. It finished at **+16,083.75** PnL. It had a rough middle section, reaching **-2,482.375** at timestamp **534,800**, but recovered strongly and reached a maximum of **19,551.375** near timestamp **977,600**.

### 4.5 VEV Voucher Strategy

The voucher strategy uses Black-Scholes call pricing. The code defines `norm_cdf`, `bs_call_price`, and `bs_delta`. It treats VFE as the underlying spot and prices each voucher as a call option with strike-specific implied volatility.

The strike map is:

- `VEV_4000`: strike **4000**
- `VEV_4500`: strike **4500**
- `VEV_5000`: strike **5000**
- `VEV_5100`: strike **5100**
- `VEV_5200`: strike **5200**
- `VEV_5300`: strike **5300**
- `VEV_5400`: strike **5400**
- `VEV_5500`: strike **5500**
- `VEV_6000`: strike **6000**
- `VEV_6500`: strike **6500**

The volatility table is fitted by strike. For example, the model uses volatility **0.25** for strike 5000, **0.2475** for strike 5100, **0.24215** for strike 5200, **0.24455** for strike 5300, and **0.24845** for strike 5500. The comments say these were fitted from historical days using decaying time to expiry and a 365-day convention.

The code assumes Round 3 starts at **5 days** to expiry and decays through the simulation:

`tte_days = max(0.05, 5.0 - timestamp / 1_000_000.0)`

Then:

`t = tte_days / 365.0`

For each active voucher, the strategy computes Black-Scholes fair value and delta, compares fair value to the best ask or bid, and trades only when edge clears a strike-specific threshold. The active edge thresholds are:

- Strike 5000: **1.60**
- Strike 5100: **1.20**
- Strike 5200: **8.00**
- Strike 5300: **1.25**
- Strike 5500: **2.00**

The size table is:

- Strike 5000: **7**
- Strike 5100: **12**
- Strike 5200: **10**
- Strike 5300: **2**
- Strike 5500: **8**

If edge is more than two points above threshold, the strategy doubles the base size. There is no active delta hedge penalty in the final code. The comment says the hedge penalty was removed because it muted the highest-quality 5000/5100 rotations. This means the final voucher strategy is mostly relative-value taker logic rather than a tightly delta-hedged options book.

The official result validates most of the voucher selection. `VEV_5000`, `VEV_5100`, `VEV_5200`, and `VEV_5300` all made money. `VEV_5500` did not trade in the official result despite being in the active list, and all other vouchers remained at zero PnL.

## 5. Algorithm Performance Analysis From JSON and Logs

### 5.1 Overall Equity Curve

The official JSON result reports exact algorithmic profit of **76,114.025390625**. The graph log contains **500 sampled points**, starts at **0.0**, ends at **79,984.111328125**, reaches a maximum of **92,410.0546875**, and reaches a minimum of **-6,476.189453125**.

The graph log ending value is not identical to the official final profit because the graph is sampled every 2,000 timestamp units and does not necessarily represent the exact final accounting value. The official profit field is the authoritative value.

The largest sampled drawdown was extremely large relative to the final score:

- Max sampled drawdown: **59,949.70458984375**
- Drawdown start: timestamp **400,000**
- Drawdown end: timestamp **534,000**

This confirms what the screenshot visually shows: Round 3 algorithmic PnL was much more volatile than Rounds 1 and 2. The strategy experienced large mid-round swings but recovered strongly into the close.

The worst sampled graph moves were:

- Timestamp **404,000 -> 406,000**: **-14,543.5234375**
- Timestamp **628,000 -> 630,000**: **-11,299.89453125**
- Timestamp **858,000 -> 860,000**: **-11,215.0087890625**
- Timestamp **32,000 -> 34,000**: **-10,740.826171875**
- Timestamp **932,000 -> 934,000**: **-9,997.8037109375**

The best sampled graph moves were:

- Timestamp **804,000 -> 806,000**: **+11,800.744140625**
- Timestamp **896,000 -> 898,000**: **+11,159.380859375**
- Timestamp **624,000 -> 626,000**: **+10,509.03955078125**
- Timestamp **40,000 -> 42,000**: **+10,237.5732421875**
- Timestamp **588,000 -> 590,000**: **+10,187.435546875**

The key interpretation is that Round 3 was an options/relative-value round with large mark-to-market swings. The algo was not a smooth carry engine. It won by being directionally/relatively correct across VFE and vouchers by the end, while tolerating substantial interim drawdowns.

### 5.2 Product-Level PnL Breakdown

The activities log contains **120,000 rows**, with **10,000 rows** for each of 12 products. Final product-level PnL was:

- `VEV_5000`: **19,178.546875**
- `VELVETFRUIT_EXTRACT`: **16,083.75**
- `VEV_5100`: **15,280.05078125**
- `VEV_5200`: **10,144.890625**
- `HYDROGEL_PACK`: **7,903.5**
- `VEV_5300`: **7,523.287109375**
- `VEV_4000`: **0.0**
- `VEV_4500`: **0.0**
- `VEV_5400`: **0.0**
- `VEV_5500`: **0.0**
- `VEV_6000`: **0.0**
- `VEV_6500`: **0.0**

The final product PnLs sum exactly to the official profit:

`76,114.025390625`

The largest single contributor was `VEV_5000`, followed by VFE and `VEV_5100`. This means the best part of the algorithm was the underlying-voucher complex, especially the lower active strikes. Hydrogel was positive but not dominant.

### 5.3 Hydrogel Performance

Hydrogel finished with **+7,903.5** PnL. It was a useful contributor, but it was volatile and suffered a major late-round dip.

Hydrogel stats:

- Final PnL: **7,903.5**
- Minimum PnL: **-2,319.75** at timestamp **922,000**
- Maximum PnL: **11,421.625** at timestamp **849,200**
- Final position: **+108**

Hydrogel bucket-end PnL by 100,000 timestamp blocks:

- 0-99,999: **170.0**
- 100,000-199,999: **1,251.59375**
- 200,000-299,999: **3,682.3125**
- 300,000-399,999: **4,946.375**
- 400,000-499,999: **7,560.8125**
- 500,000-599,999: **6,509.75**
- 600,000-699,999: **2,702.9375**
- 700,000-799,999: **2,975.0**
- 800,000-899,999: **1,987.75**
- 900,000-999,999: **7,903.5**

Hydrogel did well in the first half, weakened materially around the 600k-900k region, then recovered late. This matches the research notes that Hydrogel was regime-sensitive and that static fair models could fail badly on official-style windows. The final dynamic Hydrogel engine was profitable, but it was not the cleanest source of PnL.

### 5.4 VFE Performance

VFE finished with **+16,083.75** PnL, making it the second-largest contributor. It was also volatile, with a deep mid-round drawdown and a strong late recovery.

VFE stats:

- Final PnL: **16,083.75**
- Minimum PnL: **-2,482.375** at timestamp **534,800**
- Maximum PnL: **19,551.375** at timestamp **977,600**
- Final position: **+200**

VFE bucket-end PnL:

- 0-99,999: **10,005.5**
- 100,000-199,999: **7,182.5**
- 200,000-299,999: **3,943.3125**
- 300,000-399,999: **10,025.5**
- 400,000-499,999: **-855.5**
- 500,000-599,999: **3,304.5625**
- 600,000-699,999: **8,495.875**
- 700,000-799,999: **8,542.375**
- 800,000-899,999: **10,123.5**
- 900,000-999,999: **16,083.75**

VFE was strong early, broke down in the middle, and then recovered sharply. The final long +200 position was profitable, but the path shows that the underlying signal was not stable all day. The VFE edge worked, but it required tolerating significant adverse movement.

### 5.5 Voucher Performance

The voucher strategy was the largest source of total algorithmic PnL. The active and profitable strikes were `VEV_5000`, `VEV_5100`, `VEV_5200`, and `VEV_5300`.

`VEV_5000` was the best product:

- Final PnL: **19,178.546875**
- Minimum PnL: **-5,574.87109375** at timestamp **534,800**
- Maximum PnL: **24,422.234375** at timestamp **974,800**
- Final position: **+300**

`VEV_5100` was the third-largest contributor:

- Final PnL: **15,280.05078125**
- Minimum PnL: **-4,173.1875** at timestamp **534,800**
- Maximum PnL: **21,177.86328125** at timestamp **973,700**
- Final position: **+300**

`VEV_5200` was strong but more complicated:

- Final PnL: **10,144.890625**
- Minimum PnL: **-1,365.11328125** at timestamp **9,100**
- Maximum PnL: **20,066.279296875** at timestamp **949,400**
- Final position: **+300**

`VEV_5300` added a smaller but meaningful profit:

- Final PnL: **7,523.287109375**
- Minimum PnL: **-991.568359375** at timestamp **9,100**
- Maximum PnL: **8,719.3330078125** at timestamp **979,000**
- Final position: **+300**

The voucher book had a major shared drawdown around timestamp **534,800**, especially in `VEV_5000` and `VEV_5100`. This is the same timestamp where VFE reached its minimum. That shows the strategy had concentrated exposure to the VFE/voucher complex. When that complex moved against the model, multiple products drew down together.

The deep and far vouchers did not contribute:

- `VEV_4000`: **0.0**
- `VEV_4500`: **0.0**
- `VEV_5400`: **0.0**
- `VEV_5500`: **0.0**
- `VEV_6000`: **0.0**
- `VEV_6500`: **0.0**

This was mostly intentional. The code comments say 4000/4500 were deep ITM, 6000/6500 were near-dead, and active trading focused on the middle strikes. The research notes also say 5500 looked attractive in some residual analysis but lost in replay, while 5400 was small/noisy. The final official result supports that selectivity: the money came from the 5000-5300 region.

### 5.6 Trade History Diagnostics

The final log contains **2,891** trade history rows. Submission participation was concentrated in the products that produced PnL.

Submission trade summary:

- `HYDROGEL_PACK`
  - Total market rows: **393**
  - Submission fills: **228**
  - Submission buy quantity: **588**
  - Submission sell quantity: **480**
  - Net submission quantity: **+108**

- `VELVETFRUIT_EXTRACT`
  - Total market rows: **510**
  - Submission fills: **70**
  - Submission buy quantity: **829**
  - Submission sell quantity: **629**
  - Net submission quantity: **+200**

- `VEV_5000`
  - Total market rows: **271**
  - Submission fills: **269**
  - Submission buy quantity: **1,220**
  - Submission sell quantity: **920**
  - Net submission quantity: **+300**

- `VEV_5100`
  - Total market rows: **181**
  - Submission fills: **179**
  - Submission buy quantity: **1,211**
  - Submission sell quantity: **911**
  - Net submission quantity: **+300**

- `VEV_5200`
  - Total market rows: **122**
  - Submission fills: **90**
  - Submission buy quantity: **600**
  - Submission sell quantity: **300**
  - Net submission quantity: **+300**

- `VEV_5300`
  - Total market rows: **779**
  - Submission fills: **699**
  - Submission buy quantity: **1,004**
  - Submission sell quantity: **704**
  - Net submission quantity: **+300**

The trade history confirms that the strategy was very active in `VEV_5000`, `VEV_5100`, and especially `VEV_5300`. It was also meaningfully active in Hydrogel. VFE had fewer fills than the voucher products, but each fill was larger and the final PnL contribution was high.

The final net positions line up exactly with the net submission quantities. This is a useful consistency check: the strategy's final inventory was not accidental or hidden. It came directly from buying more than it sold in the products where it had conviction.

### 5.7 Log Health

The Round 3 log health was excellent. The `.log` file contains **10,000** timestamped log records and **0** non-empty sandbox or lambda messages.

This means:

- No reported runtime errors.
- No sandbox warnings.
- No position-limit warning messages.
- No market access fee deduction messages.
- No unexpected platform-side issue surfaced in logs.

This is operationally clean in the same artifact-level sense as the earlier final logs: there were no non-empty platform messages. Round 3's risk was not platform cleanliness; the risk was market and model volatility.

### 5.8 Where the Algo Did Well

The algo did well by correctly identifying that the most profitable area was the VFE/voucher complex. The top four PnL contributors were `VEV_5000`, VFE, `VEV_5100`, and `VEV_5200`. The strategy also made money in `VEV_5300` and Hydrogel, so it was not purely a one-product result.

It also did well by being selective. It did not waste capacity trading every voucher just because the products existed. The final zero-PnL vouchers show that the strategy avoided deep ITM and near-dead strikes. The research notes specifically warned that some strikes looked attractive in raw Black-Scholes residuals but failed in replay. The final strategy mostly respected that lesson.

The code also did well operationally. The `OrderBuilder` kept planned orders inside product limits, and the log had no warnings. That is important because this strategy traded many more products than the prior rounds and had many more opportunities to create messy order sets.

Finally, the late recovery was strong. The graph reached its maximum near the end and finished high despite a severe mid-round drawdown. The final result shows that the strategy's large long positions in VFE and vouchers were ultimately profitable.

### 5.9 Where the Algo Did Not Do Well

The biggest weakness was volatility. The graph drawdown from timestamp **400,000** to **534,000** was about **59,949.7**, which is enormous relative to final PnL of **76,114.0**. This means the strategy had a large path risk. It could look excellent early, suffer a major loss, and then recover later.

The second weakness was concentrated exposure. VFE, `VEV_5000`, and `VEV_5100` all hit their minimum PnLs at timestamp **534,800**. That synchronized drawdown shows that the products were not independent. The strategy was exposed to a common underlying factor. When the VFE/voucher complex moved against the model, multiple positions lost together.

The third weakness was ending at maximum long inventory in multiple vouchers. Ending at +300 in `VEV_5000`, `VEV_5100`, `VEV_5200`, and `VEV_5300` was profitable here, but it was not low-risk. A more hedged options strategy might have had lower drawdowns, but the code comments say the hedge penalty was removed because it muted profitable rotations. That tradeoff improved upside but increased exposure.

Hydrogel was also not fully stable. It made **7,903.5**, but its path included a drop to **-2,319.75** late in the run. The dynamic fair model helped avoid worse static-fair failures, but Hydrogel was still a regime-sensitive contributor.

## 6. Manual Trading Analysis

### 6.1 Final Manual Bids

The final manual submission used two bid prices: **765** and **860**.

For the first bid:

- Bid price: **765**
- Accepted: **353**
- Rejected: **647**
- Buy price: **270,045**
- Sell price: **324,760**
- PnL: **54,715**

For the second bid:

- Bid price: **860**
- Accepted: **400**
- Rejected: **600**
- Buy price: **344,000**
- Sell price: **368,000**
- PnL: **24,000**

Combined:

- Total buy price: **614,045**
- Total sell price: **692,760**
- Final PnL: **78,715**

The final manual result ranked **52nd**, which was the best ranking component of Round 3.

### 6.2 Why This Manual Submission Worked

The manual chart shows the distribution of first and second bids across teams. The team's first bid of **765** matched the displayed lowest bid, while the average first bid was **768**. The team's second bid of **860** matched the displayed highest bid, while the average second bid was **859**.

That positioning mattered. The first bid generated the larger PnL component: **54,715**. The second bid added **24,000**. Together they produced **78,715**, only slightly more than the algorithmic result. The accepted/rejected counts show that the bids were not simply all accepted; each row had a mixture of accepted and rejected outcomes. The first row accepted **353** and rejected **647**; the second accepted **400** and rejected **600**.

The manual result was strong because the bid choices landed near important distribution thresholds. The first bid sat at the bottom edge of first-bid distribution, and the second bid sat at the top edge of second-bid distribution. That produced a favorable buy/sell spread across the accepted quantities.

### 6.3 Manual Trading Outcome

Manual trading contributed **78,715** out of **154,829** total Round 3 XIRECS. That is slightly more than half the total. It also ranked **52nd**, which was stronger than the algo rank of **407th**.

This means the manual result was not just a nice addition. It was one of the main reasons Round 3 reached position **382** overall. Without manual trading, the round would have been a solid 76k algo result. With manual trading, the total doubled to 154,829.

## 7. Final Interpretation

### 7.1 What Went Right

The biggest thing that went right was the voucher selection. `VEV_5000`, `VEV_5100`, `VEV_5200`, and `VEV_5300` all made money, while the avoided vouchers did not create losses. The final code focused on the strikes that had realized edge rather than blindly trading every Black-Scholes residual.

The second major success was VFE. VFE was not only the underlying input for voucher fair values; it was also directly profitable, adding **16,083.75**. The deep-voucher-implied fair method was useful enough to make VFE the second-largest product contributor.

The third success was clean execution. The final algorithm traded many products and generated thousands of fills, but the log had no warnings or errors. That is a meaningful engineering result.

The fourth success was the manual bid selection. The two-bid manual result ranked **52nd** and produced slightly more PnL than the algorithm.

### 7.2 What Did Not Go Perfectly

The main imperfection was path volatility. The algorithm finished strong, but the graph had a nearly **60k** sampled drawdown from peak to trough. That is not a small issue. It means the strategy was exposed to significant adverse movement and required a late recovery to finish at 76k.

The second imperfection was concentration. The final position was max long in four vouchers and max long VFE. This was profitable, but it was not balanced or hedged in a conservative sense. The code explicitly removed the hedge penalty, which likely improved final PnL but increased shared exposure.

The third imperfection was Hydrogel inconsistency. Hydrogel added profit, but it went negative late and had large swings. It was not the main edge, and its behavior remained regime-sensitive.

The fourth imperfection is that some active-list logic did not translate into fills. `VEV_5500` was in the active voucher list but did not contribute. This is not necessarily bad, because avoiding bad fills is acceptable, but it shows that active-list inclusion alone did not mean the product became part of the final realized strategy.

### 7.3 Lessons for Future Rounds

The first lesson is that product selection matters as much as model complexity. The Black-Scholes framework was useful, but the final result depended on choosing which strikes to actually trade. The avoided strikes were as important as the traded strikes.

The second lesson is that replay/realized behavior beats raw theoretical richness. The research notes explicitly warned that 5500 and 5400 could look attractive on surface tables but underperform in replay. The final result supports that view.

The third lesson is that clean order construction scales. Round 3 traded far more instruments than Rounds 1 and 2, but the `OrderBuilder` kept execution clean. This pattern should be reused.

The fourth lesson is that high PnL can hide high drawdown. The final score was strong, but the algorithmic path was risky. Any future options strategy should report both final PnL and drawdown, because final PnL alone does not describe the strategy's risk.

## 8. Final Round 3 Takeaway

Round 3 was a strong and balanced result. The team finished with **154,829 XIRECS**, position **382**, algorithmic PnL **76,114**, and manual PnL **78,715**. Manual trading ranked **52nd** and algorithmic trading ranked **407th**.

The algorithm's strongest edge was the VFE/voucher complex. `VEV_5000`, `VELVETFRUIT_EXTRACT`, `VEV_5100`, `VEV_5200`, `HYDROGEL_PACK`, and `VEV_5300` all contributed positive PnL. The log was perfectly clean, with no sandbox or lambda warnings. The main weakness was not execution quality; it was risk and volatility. The strategy had a large mid-round drawdown and ended with heavy long exposure in several options.

The manual result was excellent. The two bids, **765** and **860**, produced **78,715** PnL and ranked **52nd**. Combined with the algorithm, this made Round 3 one of the strongest overall results so far.
