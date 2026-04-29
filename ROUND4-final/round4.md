# Round 4 Final Report

## 1. Executive Summary

Round 4 finished with a new total score of **208,622 XIRECS** for team **ALCARAZGOAT2026**, with overall position **694** on the detailed results screenshot. The previous total was **154,829**, Round 4 added **53,793**, and the new total became **208,622**. The displayed arithmetic reconciles: **154,829 + 53,793 = 208,622**.

This was a disappointing round relative to the previous final-round reports. The algorithmic submission produced **+50,966 XIRECS**, while the manual submission produced only **+2,826 XIRECS**. The algo still contributed most of the Round 4 score, but it **severely underperformed** relative to expectations and relative to stronger earlier Round 4 official submissions already present in the repo. The final algo package scored **50,966.40673828125**, while the Round 4 official feedback files show prior official submissions around **75,988**, **86,962**, and **87,114**. In other words, the final algo was not just modest; it appears to have been materially worse than known earlier candidates.

The final algorithmic package is stored under `ROUND4-final/algo_submission/final-algo`. It contains `544490.py`, `544490.json`, and `544490.log`. The algorithm continued the Round 3 style of trading **HYDROGEL_PACK**, **VELVETFRUIT_EXTRACT**, and VEV vouchers, but it added more Round 4-specific mechanics: Mark counterparty flow signals, timed exits/re-entries, Hydrogel PnL locks, and broader voucher participation. The strategy was operationally clean, with **0 non-empty sandbox or lambda messages**, but its trading outcome was poor.

The most important product-level issue was that several components lost money or gave back expected edge. `HYDROGEL_PACK` lost **-6,513.0**, `VEV_5200` lost **-2,653.0**, and `VEV_5300` lost **-1,766.0**. The profitable products were not enough to offset those leaks and the large opportunity cost relative to stronger candidates. The algo also had a very large sampled drawdown of about **78,994** from timestamp **408,000** to **628,000**, showing that the path was unstable even though the final score remained positive.

The manual result was also weak. The manual trades produced only **+2,826.16**, displayed as **+2,826**, with manual round ranking **888th**. Manual trading was not a meaningful rescue this round.

## 2. Final Results

### 2.1 Overall Leaderboard Result

The detailed Round 4 result screenshot shows:

- Team: **ALCARAZGOAT2026**
- Position: **694**
- Total XIREC: **208,622**
- Previous Total: **154,829**
- Round 4 Total: **53,793**
- New Total PnL: **208,622**
- Algorithmic Trading Result: **+50,966**
- Algorithmic Round Ranking: **832nd**
- Manual Trading Result: **+2,826**
- Manual Round Ranking: **888th**
- Crew honors: **14 badges unlocked**

The position indicator in the screenshot points downward, so despite adding positive PnL, the team lost relative standing. This matches the weak Round 4 total. A **53,793** round contribution was not enough to keep pace with the field.

### 2.2 Algorithmic Trading Result

The screenshot displays algorithmic trading PnL as **+50,966 XIRECS**. The exact value in `544490.json` is **50,966.40673828125**.

The final JSON positions were:

- `HYDROGEL_PACK`: **0**
- `VELVETFRUIT_EXTRACT`: **+200**
- `VEV_4000`: **+300**
- `VEV_4500`: **+300**
- `VEV_5000`: **+300**
- `VEV_5100`: **+300**
- `VEV_5200`: **0**
- `VEV_5300`: **0**
- `VEV_5400`: **+300**
- `XIRECS`: **-1,685,237**

The final inventory shows that the strategy ended flat in Hydrogel and in the weak exited vouchers `VEV_5200` and `VEV_5300`, but it remained max long VFE and several vouchers. The final long book was not enough to generate a competitive result.

The algorithmic PnL chart was very volatile. It reached high levels around the 400k region, then suffered a major drawdown into the 600k region, recovered later, and finished around 50k. The final score was positive, but the path and final rank confirm that the algo underperformed.

### 2.3 Manual Trading Result

The manual screenshot shows five option-style manual trades:

- `AC_50_P_2`: Buy **50** at price **-282.40**, PnL **-14,119.75**
- `AC_50_C_2`: Buy **50** at price **-468.84**, PnL **-23,442.21**
- `AC_50_C0`: Sell **50** at price **+1,087.08**, PnL **+54,354.22**
- `AC_40_BP`: Sell **50** at price **+300.00**, PnL **+15,000.00**
- `AC_45_K0`: Buy **500** at price **-57.93**, PnL **-28,966.10**

The total manual PnL was:

`-14,119.75 - 23,442.21 + 54,354.22 + 15,000.00 - 28,966.10 = 2,826.16`

The UI displays manual trading PnL as **2,826**. This was a very small contribution compared with previous rounds. The manual round ranking was **888th**, so manual trading also underperformed.

## 3. Files Submitted

### 3.1 Algo Submission Package

The final algorithmic package is located at:

`ROUND4-final/algo_submission/final-algo`

It contains:

- `544490.py`: the final Round 4 submitted strategy code.
- `544490.json`: the official result export with exact profit, activities log, graph log, and final positions.
- `544490.log`: the execution log with submission ID, timestamped logs, and trade history.
- `final-algo.zip`: the archived final package, stored in `ROUND4-final/algo_submission`.

The submission ID in `544490.log` is:

`c16cb940-c2b7-41ae-a412-16a5d9beeb4d`

The JSON result reports:

- Round: **4**
- Status: **FINISHED**
- Exact profit: **50,966.40673828125**
- Displayed rounded profit: **50,966**

The final-folder layout has also been standardized:

- `ROUND4-final/algo_submission`
- `ROUND4-final/algo_submission/final-algo`
- `ROUND4-final/hand_trade_submission`
- `ROUND4-final/round4.md`

### 3.2 Hand Trade Submission

The final hand trade submission is documented from the screenshots. There is no separate structured manual submission file currently stored in `ROUND4-final/hand_trade_submission`.

The final manual result was:

- Manual PnL: **2,826.16**
- Displayed manual PnL: **2,826**
- Manual round ranking: **888th**

The manual result was positive but weak. It contributed only about **5.3%** of the Round 4 total.

## 4. Algorithm Design: What the Code Actually Does

### 4.1 Products Traded

The Round 4 strategy trades the same broad instrument universe as Round 3:

- `HYDROGEL_PACK`
- `VELVETFRUIT_EXTRACT`
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

The limits are:

- Hydrogel: **200**
- Velvetfruit: **200**
- Each voucher: **300**

Unlike the Round 3 final strategy, the Round 4 code activates **all vouchers** in `ACTIVE_VOUCHERS`. It does not restrict itself to only the middle strikes. That broader participation was risky. Some of the broader voucher decisions worked, especially `VEV_4500`, `VEV_5000`, and `VEV_5100`, but others either lost money or added little.

### 4.2 Shared Infrastructure

The strategy uses the same general helper structure as prior rounds:

- `book_snapshot` normalizes each order book.
- `compute_mid` computes midpoint.
- `top_imbalance` computes top-of-book volume imbalance.
- `load_cache`, `push_history`, and `update_anchor` maintain `traderData` state.
- `ensure_within_hard_limit` sorts and trims orders so planned orders stay within product limits.

The code was operationally clean. The final `.log` file had **10,000** timestamped log entries and **0** non-empty sandbox/lambda messages. This means the underperformance was not caused by runtime errors or platform warnings. It was caused by strategy design, product selection, timing, and market exposure.

### 4.3 Mark Flow Signals

Round 4 introduced Mark counterparty mechanics, and the code attempts to use them. The strategy defines Mark weights for Hydrogel and VFE:

Hydrogel Mark weights:

- `Mark 14`: **+1.0**
- `Mark 38`: **-1.0**
- `Mark 22`: **-2.0**

Velvet Mark weights:

- `Mark 01`: **0.0**
- `Mark 14`: **-0.7**
- `Mark 67`: **+1.0**
- `Mark 55`: **+1.0**
- `Mark 49`: **-1.0**
- `Mark 22`: **-0.5**

The function `mark_flow_signal` reads `market_trades`, looks at buyer and seller identities, scales by square root of trade size, and updates a smoothed signal in `traderData`. The signal is clipped between **-4.0** and **+4.0**.

This was a reasonable attempt to use the new Round 4 mechanic, but the final result suggests it did not produce enough edge. The code had Mark-aware Hydrogel and VFE adjustments, but Hydrogel lost money and VFE was profitable but not enough to rescue the round.

### 4.4 HYDROGEL_PACK Strategy

Hydrogel was one of the biggest failures of the final algo. The code includes a complex Hydrogel engine:

- Dynamic fair around `HYDRO_DEFAULT_FAIR = 9991.0`
- Imbalance, deviation, and trend adjustments
- Mark-flow fair adjustment
- Active taking
- Passive Mark-based quoting
- Market making
- PnL lock logic
- Timed exit logic at **60,000**

The intended design was to avoid the Round 3 problem of carrying Hydrogel through bad regimes. The code tries to lock Hydrogel PnL after a threshold and flatten position after a short early window.

The final result was still poor:

- Hydrogel final PnL: **-6,513.0**
- Hydrogel max PnL: **347.2734375** at timestamp **25,400**
- Hydrogel min/final PnL: **-6,513.0** at timestamp **60,400**
- Final Hydrogel position: **0**

Hydrogel lost money early and then stayed flat at that loss for the rest of the round. The strategy exited/locked the loss rather than recovering. This was a major source of underperformance. The research notes had already flagged Hydrogel as a critical problem area, and the final official result confirms it remained broken.

### 4.5 VELVETFRUIT_EXTRACT Strategy

VFE was profitable and was one of the better parts of the final algorithm. The code computes both a linear fair and an implied fair from deep vouchers, then blends them:

`velvet_fair = 0.35 * velvet_linear_fair + 0.65 * velvet_implied_fair + mark_adjustment`

The code also includes timed exit/re-entry:

- `VELVET_EXIT_TIMESTAMP = 71,900`
- `VELVET_REENTRY_TIMESTAMP = 85,000`

VFE final stats:

- Final PnL: **11,847.5625**
- Minimum PnL: **-1,160.1875** at timestamp **2,600**
- Maximum PnL: **20,982.75** at timestamp **408,200**
- Final position: **+200**

VFE worked, but it gave back a lot from its peak. At timestamp 408,200, VFE was above 20k, but it finished below 12k. That drawdown mirrors the broader algo path: the strategy had strong early/mid profits but failed to retain them.

### 4.6 Voucher Strategy

The voucher engine uses Black-Scholes fair values with strike-specific implied volatility. It also includes:

- Strike-specific edge thresholds
- Strike-specific sizing for 5000 and 5100
- Timed exit/re-entry for `VEV_5000`
- Weak-option exit set for `VEV_5200` and `VEV_5300`
- Zero-price bids for far OTM vouchers when allowed

The active voucher set includes all vouchers from 4000 through 6500. The final PnL attribution shows this broad approach had mixed results.

Profitable voucher final PnL:

- `VEV_4500`: **16,531.359375**
- `VEV_5000`: **14,875.5**
- `VEV_5100`: **14,178.5234375**
- `VEV_5400`: **3,064.08642578125**
- `VEV_4000`: **1,401.375**

Losing or zero voucher final PnL:

- `VEV_5200`: **-2,653.0**
- `VEV_5300`: **-1,766.0**
- `VEV_5500`: **0.0**
- `VEV_6000`: **0.0**
- `VEV_6500`: **0.0**

The best voucher products were 4500, 5000, and 5100. The weak-option exit set did not prevent 5200 and 5300 from ending negative. `VEV_4000` was also far weaker than prior official submissions.

## 5. Algorithm Performance Analysis From JSON and Logs

### 5.1 Overall Equity Curve

The official JSON result reports exact algorithmic profit of **50,966.40673828125**. The graph log contains **500 sampled points**. It starts at **0.0**, ends at **52,016.47607421875**, reaches a maximum of **98,318.3525390625**, and reaches a minimum of **-16,395.7158203125**.

The final graph sample is close to, but not exactly the same as, the exact final JSON profit. The official `profit` field is authoritative.

The maximum sampled drawdown was extremely large:

- Max sampled drawdown: **78,994.08129882812**
- Drawdown start: timestamp **408,000**
- Drawdown end: timestamp **628,000**

This is the clearest path-level evidence of underperformance. The algo had the ability to reach nearly **98k**, but it gave back most of that and ended near **51k**. A strategy that peaks at 98k and finishes at 51k did not manage risk or regime transition well.

Worst sampled graph moves:

- Timestamp **38,000 -> 40,000**: **-14,822.270874023438**
- Timestamp **730,000 -> 732,000**: **-14,163.536865234375**
- Timestamp **878,000 -> 880,000**: **-12,136.291015625**
- Timestamp **960,000 -> 962,000**: **-12,019.80029296875**
- Timestamp **768,000 -> 770,000**: **-11,862.89453125**

Best sampled graph moves:

- Timestamp **924,000 -> 926,000**: **+23,215.689208984375**
- Timestamp **754,000 -> 756,000**: **+16,772.683837890625**
- Timestamp **866,000 -> 868,000**: **+14,782.591064453125**
- Timestamp **386,000 -> 388,000**: **+12,735.720947265625**
- Timestamp **8,000 -> 10,000**: **+12,254.501708984375**

The path was extremely noisy. There were large wins and large losses, but the final score was not competitive with the stronger known Round 4 submissions.

### 5.2 Product-Level PnL Breakdown

The activities log contains **120,000 rows**, with **10,000 rows** per product. Final product PnL was:

- `VEV_4500`: **16,531.359375**
- `VEV_5000`: **14,875.5**
- `VEV_5100`: **14,178.5234375**
- `VELVETFRUIT_EXTRACT`: **11,847.5625**
- `VEV_5400`: **3,064.08642578125**
- `VEV_4000`: **1,401.375**
- `VEV_5500`: **0.0**
- `VEV_6000`: **0.0**
- `VEV_6500`: **0.0**
- `VEV_5300`: **-1,766.0**
- `VEV_5200`: **-2,653.0**
- `HYDROGEL_PACK`: **-6,513.0**

The final product PnLs sum exactly to the official result:

`50,966.40673828125`

The biggest problem was not that every product failed. Several products were profitable. The problem was that the final strategy carried meaningful losing legs and failed to preserve the high mid-run gains in the profitable legs.

### 5.3 Comparison Against Prior Known Round 4 Submissions

The repo contains official feedback for earlier Round 4 submissions:

- `522830 (rohan)`: **75,988.85998535156**
- `524123 (kush)`: **75,988.85998535156**
- `524290 (kush)`: **75,728.53283691406**
- `524413 (kush)`: **75,728.53283691406**
- `530880`: **87,114.39221191406**
- `534133`: **86,962.39221191406**

The final `544490` package scored **50,966.40673828125**. This is much worse than the stronger prior official submissions:

- About **36,148** below `530880`.
- About **35,996** below `534133`.
- About **25,022** below the 75,988 baseline submissions.

This is why the algo should be described as severely underperforming. The underperformance is not just relative to hopes; it is visible against concrete prior official results in the project.

The prior feedback also explains what went wrong. For example, `530880` had much stronger positive Hydrogel and VFE, while `544490` had Hydrogel at **-6,513**. Prior submissions also had `VEV_5200` and `VEV_5300` positive, while final `544490` had both negative.

### 5.4 Hydrogel: Major Failure

Hydrogel was the worst product:

- Final PnL: **-6,513.0**
- Minimum PnL: **-6,513.0**
- Maximum PnL: **347.2734375**
- Final position: **0**

The bucket-end PnL shows the issue clearly:

- 0-99,999: **-6,513.0**
- 100,000-199,999: **-6,513.0**
- 200,000-299,999: **-6,513.0**
- 300,000-399,999: **-6,513.0**
- 400,000-499,999: **-6,513.0**
- 500,000-599,999: **-6,513.0**
- 600,000-699,999: **-6,513.0**
- 700,000-799,999: **-6,513.0**
- 800,000-899,999: **-6,513.0**
- 900,000-999,999: **-6,513.0**

Hydrogel lost early and then stayed locked at that loss. The strategy did not recover, did not continue harvesting, and did not cut the product before the damage. This was one of the clearest failures in the final algo.

### 5.5 VFE: Good But Gave Back Too Much

VFE was profitable:

- Final PnL: **11,847.5625**
- Minimum PnL: **-1,160.1875**
- Maximum PnL: **20,982.75**
- Final position: **+200**

The issue is that VFE gave back nearly **9,135** from its peak. It reached its maximum at timestamp **408,200**, the same region where the overall graph reached its maximum. It then declined and finished much lower.

VFE did not fail outright, but it did not preserve gains. The final strategy was unable to lock in the best VFE state or adapt when the regime changed.

### 5.6 Vouchers: Mixed And Worse Than Needed

The strongest voucher was `VEV_4500` at **16,531.359375**. `VEV_5000` and `VEV_5100` were also strong at **14,875.5** and **14,178.5234375**. These were the core profitable legs.

However, several voucher results were weak:

- `VEV_4000`: only **1,401.375**, much lower than prior official submissions around **9,382**.
- `VEV_5200`: **-2,653.0**
- `VEV_5300`: **-1,766.0**
- `VEV_5500`, `VEV_6000`, `VEV_6500`: **0.0**

The final strategy broadened the active voucher universe but did not turn that breadth into a better result. It also appears to have weakened previously useful low-strike behavior. The research notes explicitly warned that `VEV_4000` sizing was important; final `544490` ended with only **1,401.375** in `VEV_4000`, which was a major opportunity miss.

### 5.7 Trade History Diagnostics

The final log contains **2,657** trade history rows.

Submission trade summary:

- `HYDROGEL_PACK`
  - Submission fills: **42**
  - Submission buy quantity: **190**
  - Submission sell quantity: **190**
  - Net final quantity: **0**
  - Final PnL: **-6,513.0**

- `VELVETFRUIT_EXTRACT`
  - Submission fills: **70**
  - Submission buy quantity: **846**
  - Submission sell quantity: **646**
  - Net final quantity: **+200**
  - Final PnL: **11,847.5625**

- `VEV_4000`
  - Submission fills: **40**
  - Submission buy quantity: **300**
  - Submission sell quantity: **0**
  - Net final quantity: **+300**
  - Final PnL: **1,401.375**

- `VEV_4500`
  - Submission fills: **143**
  - Submission buy quantity: **900**
  - Submission sell quantity: **600**
  - Net final quantity: **+300**
  - Final PnL: **16,531.359375**

- `VEV_5000`
  - Submission fills: **265**
  - Submission buy quantity: **1,396**
  - Submission sell quantity: **1,096**
  - Net final quantity: **+300**
  - Final PnL: **14,875.5**

- `VEV_5100`
  - Submission fills: **330**
  - Submission buy quantity: **1,676**
  - Submission sell quantity: **1,376**
  - Net final quantity: **+300**
  - Final PnL: **14,178.5234375**

- `VEV_5200`
  - Submission fills: **48**
  - Submission buy quantity: **300**
  - Submission sell quantity: **300**
  - Net final quantity: **0**
  - Final PnL: **-2,653.0**

- `VEV_5300`
  - Submission fills: **59**
  - Submission buy quantity: **300**
  - Submission sell quantity: **300**
  - Net final quantity: **0**
  - Final PnL: **-1,766.0**

- `VEV_5400`
  - Submission fills: **151**
  - Submission buy quantity: **900**
  - Submission sell quantity: **600**
  - Net final quantity: **+300**
  - Final PnL: **3,064.08642578125**

The trade history confirms that the strategy did not simply fail due to inactivity. It traded actively in several products. The issue was trade quality and product selection, especially Hydrogel and the weak voucher exits.

### 5.8 Log Health

The final log was operationally clean:

- Timestamped logs: **10,000**
- Non-empty sandbox/lambda messages: **0**
- Runtime errors: **0 reported**
- Position-limit warnings: **0 reported**

This matters because the poor result cannot be blamed on a platform error. The strategy ran successfully. It just did not make enough money.

### 5.9 Where The Algo Did Well

The algo did well in:

- `VEV_4500`: **16,531.359375**
- `VEV_5000`: **14,875.5**
- `VEV_5100`: **14,178.5234375**
- `VELVETFRUIT_EXTRACT`: **11,847.5625**

These products kept the final result positive. Without them, Round 4 would have been disastrous. The middle voucher complex still had real edge.

The code also did well operationally. It respected limits and produced no warnings. This is important given the number of products traded.

### 5.10 Where The Algo Did Badly

The algo did badly in three main ways.

First, Hydrogel lost **-6,513.0** and never recovered. This was a major known risk from the research notes, and the final strategy did not solve it.

Second, `VEV_5200` and `VEV_5300` both finished negative despite being actively traded and explicitly included in weak-option exit logic. The exit logic did not create positive realized edge.

Third, the strategy gave back a huge amount of PnL after the 408k peak. The graph peaked at **98,318.3525390625** and later fell into a much lower regime. This was exactly the kind of post-peak/post-regime problem the research notes warned about.

The final result was therefore not competitive, especially compared with earlier official submissions in the repo.

## 6. Manual Trading Analysis

### 6.1 Final Manual Trades

The manual submission consisted of five trades:

- Buy 50 of `AC_50_P_2`, losing **14,119.75**
- Buy 50 of `AC_50_C_2`, losing **23,442.21**
- Sell 50 of `AC_50_C0`, gaining **54,354.22**
- Sell 50 of `AC_40_BP`, gaining **15,000.00**
- Buy 500 of `AC_45_K0`, losing **28,966.10**

The total was:

`2,826.16`

The displayed rounded manual result was **+2,826**.

### 6.2 Why Manual Was Weak

The manual submission had two strong positive trades, but three losing trades consumed almost all of the gains.

Positive manual legs:

- `AC_50_C0`: **+54,354.22**
- `AC_40_BP`: **+15,000.00**

Negative manual legs:

- `AC_50_P_2`: **-14,119.75**
- `AC_50_C_2`: **-23,442.21**
- `AC_45_K0`: **-28,966.10**

The positive legs summed to **69,354.22**, but the negative legs summed to **-66,528.06**. That left only **2,826.16** net. This was not a strong manual portfolio. It had correct ideas in some legs but too much offsetting loss.

### 6.3 Manual Trading Outcome

Manual trading ranked **888th**. It contributed only **2,826** to a Round 4 total of **53,793**. That is about **5.3%** of the round score.

Compared with previous rounds, manual trading was not a meaningful driver. Round 1 manual was rank 1st, Round 2 manual was rank 236th, Round 3 manual was rank 52nd, but Round 4 manual was rank 888th. This was a large drop.

## 7. Final Interpretation

### 7.1 What Went Right

The algo was still positive, and the strongest voucher legs worked. `VEV_4500`, `VEV_5000`, `VEV_5100`, and VFE generated meaningful PnL. The code also ran cleanly with no platform warnings.

The manual result was positive, even if small. The `AC_50_C0` and `AC_40_BP` legs were good trades.

### 7.2 What Went Wrong

The final algo severely underperformed. It scored **50,966**, while earlier known Round 4 official submissions scored up to about **87,114**. The final package was materially worse than prior candidates.

Hydrogel was the clearest product failure, losing **-6,513**. `VEV_5200` and `VEV_5300` also lost money. `VEV_4000` was much weaker than prior candidates. The strategy also had a massive drawdown after a strong peak, meaning it failed to preserve gains.

Manual trading also underperformed. Three losing manual legs almost fully offset the two profitable legs, leaving only **2,826** net.

### 7.3 Lessons For Future Rounds

The first lesson is that final selection must compare against known official candidates before packaging. The repo already had official feedback showing much stronger Round 4 candidates. A final algo scoring 50,966 should not have displaced candidates in the 75k-87k range unless there was a specific hidden-test reason.

The second lesson is that product-level attribution has to be mandatory before final submission. The final result's losses in Hydrogel, `VEV_5200`, and `VEV_5300` were not hidden in the aggregate once parsed. They directly explain the underperformance.

The third lesson is that clean logs are not enough. This strategy executed cleanly but still underperformed. Engineering correctness and trading profitability are separate.

The fourth lesson is that manual portfolios need net-risk checking. The positive manual trades were strong, but the losing trades nearly eliminated the gains. A manual solution should be evaluated as a combined portfolio, not as a list of individually plausible trades.

## 8. Final Round 4 Takeaway

Round 4 was a weak round. The team added **53,793 XIRECS**, bringing the total to **208,622**, but the overall position fell to **694**. The algo produced **50,966** and ranked **832nd**; the manual produced only **2,826** and ranked **888th**.

The final algo underperformed badly relative to stronger known Round 4 candidates. Its main profitable legs were `VEV_4500`, `VEV_5000`, `VEV_5100`, and VFE, but Hydrogel lost **-6,513**, `VEV_5200` and `VEV_5300` were negative, and the strategy gave back a huge amount of PnL after peaking near 98k. The logs were clean, so the problem was not execution failure; it was strategy quality and final candidate selection.

The manual result was also weak. Two profitable trades were nearly offset by three losing trades, leaving only **2,826.16** net. Round 4 should be treated as a clear underperformance round and a reminder that final packaging must be based on parsed product attribution and comparison against prior official candidates.
