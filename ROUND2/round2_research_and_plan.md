# Round 2 Research and Plan

## Executive decision

Primary algorithm candidate: `round2_strategy_primary_bid3001.py`.

Primary manual allocation candidate: **Research 15%, Scale 44%, Speed 41%**.

Primary Market Access Fee: **3001 XIRECs**.

Aggressive alternate MAF file: `round2_strategy_aggressive_bid5001.py`.

The algorithm recommendation deliberately does not change the core trading logic much before the first Round 2 portal bundle. The new problem variable is the Market Access Fee and randomized 80% quote visibility, not a new product. The Round 2 public data says the same structural trade still dominates: long Intarian Pepper Root carry plus stable Ash-Coated Osmium extraction.

---

## What changed in Round 2

Round 2 still trades:

- `ASH_COATED_OSMIUM`, limit 80
- `INTARIAN_PEPPER_ROOT`, limit 80

New mechanism:

- `Trader.bid()` can bid a one-time Market Access Fee.
- Accepted bids are the top 50% of all participant bids.
- Accepted teams pay their own bid and receive 25% more order-book quotes.
- Rejected teams do not pay and trade the default 80% quote set.
- Portal testing ignores the bid and uses an 80% randomized quote subset.

Practical interpretation:

- Bidding is not a trading signal.
- It is an option on more market data/liquidity.
- The bid should not exceed the expected incremental value of extra access.
- Because the position limits are still 80, extra access is helpful but probably not worth a huge fee for the current carry-heavy strategy.

---

## Round 2 data findings

The uploaded Round 2 files contain three 10,000-timestamp days:

- day -1
- day 0
- day 1

Each file has the same two products and timestamps from 0 to 999900 in 100-step increments.

### Ash-Coated Osmium

Osmium remains anchored around 10,000.

| day | start mid | end mid | change | mean spread | mid std after removing zero mids |
|---:|---:|---:|---:|---:|---:|
| -1 | 9991.0 | 10002.0 | +11.0 | 16.22 | 4.47 |
| 0 | 10003.0 | 10008.0 | +5.0 | 16.25 | 5.66 |
| 1 | 10008.0 | 9993.0 | -15.0 | 16.23 | 5.02 |

Conclusion: keep treating osmium as fixed-fair / mean-reverting around 10,000. There is no evidence for a structural drift model like pepper.

### Intarian Pepper Root

Pepper remains an almost perfect linear trend product.

| day | start mid | end mid | change | fitted slope | linear R² | mean spread |
|---:|---:|---:|---:|---:|---:|---:|
| -1 | 11001.5 | 11999.5 | +998.0 | ~0.001 | ~0.99994 | 13.07 |
| 0 | 11998.5 | 13000.0 | +1001.5 | ~0.001 | ~0.99993 | 14.12 |
| 1 | 13000.0 | 13999.5 | +999.5 | ~0.001 | ~0.99992 | 15.18 |

Conclusion: the carry thesis is still real. Most of the robust algorithmic score should still come from getting long pepper early and staying long.

---

## Pepper policy experiments

I ran deterministic active-fill experiments on the public Round 2 book. These are not official portal predictions; they are a directional way to compare pepper policies.

Representative results:

| policy proxy | volume multiplier | day -1 | day 0 | day 1 | average |
|---|---:|---:|---:|---:|---:|
| current C-style, generated file settings | 1.00 | 79362 | 79439 | 79364 | 79388 |
| uploaded 238191-style | 1.00 | 79334 | 79382 | 79364 | 79360 |
| too-fast premium 12 | 1.00 | 79291 | 79293 | 79223 | 79269 |
| adaptive trim test | 1.00 | 79294 | 79313 | 79306 | 79304 |

Main result:

- Buying faster is not always better.
- The best robust pepper behavior is still early accumulation, but not reckless sweeping through every level.
- Residual trimming still does not justify the lost carry except in rare cases, and the tested adaptive trim underperformed the simple accumulator.

This is why the primary Round 2 code keeps a disciplined accumulator rather than becoming a churny sell/rebuy strategy.

---

## Extra market access value

I tested a crude proxy by scaling visible volumes:

| policy proxy | 80% volume average | 100% volume average | 125% volume average |
|---|---:|---:|---:|
| generated C-style pepper | 79383 | 79388 | 79397 |
| uploaded 238191-style pepper | 79344 | 79360 | 79382 |

This proxy probably understates the value of extra access because the official extra quotes can appear as intermediate price levels, not merely more volume at existing levels. Still, it shows an important bound:

- for a strategy that reaches +80 pepper quickly, additional volume has low marginal value after inventory is full;
- extra access is more valuable for osmium spread capture and for strategies that actively recycle inventory;
- it is probably not worth paying a huge MAF unless portal evidence later proves the extra quotes are much more valuable than the public data suggests.

Recommended MAF posture:

- **3001** is the primary bid: it beats many low/focal bids while not risking a large negative fee if accepted.
- **5001** is the aggressive alternate: use only if you think the field median bid will be around 5000 or if the first portal tests suggest extra access is materially valuable.
- I would avoid bids above roughly 8000 without stronger evidence that full access is worth that much.

---

## Manual challenge analysis

Manual formula:

`PnL = Research(x) * Scale(y) * SpeedMultiplier(z) - BudgetUsed`

with integer percentages and total allocation <= 100.

For any fixed speed investment and fixed speed multiplier, the optimal Research/Scale split is heavily weighted toward Scale because Research is logarithmic and Scale is linear.

If speed multiplier were known and speed did not affect rank, the best allocation would be roughly:

- Research 23
- Scale 77
- Speed 0

But speed is rank-based, so speed cannot be ignored.

I modeled speed as a competitive percentile problem. If your speed investment beats fraction `q` of other teams, your approximate multiplier is:

`0.1 + 0.8q`

The robust focal allocation is:

- **Research 15%**
- **Scale 44%**
- **Speed 41%**

Why:

- It beats common equal-split / one-third speed answers.
- It beats the likely optimizer crowd around 36-40 speed.
- It does not overpay as badly as 50+ speed if the field median is lower.
- It remains strong if speed 41 lands in the 60th-75th percentile of submissions.

Approximate outcome for Research 15 / Scale 44 / Speed 41:

| speed percentile beaten | speed multiplier | approximate manual PnL |
|---:|---:|---:|
| 50% | 0.50 | ~135k |
| 60% | 0.58 | ~164k |
| 70% | 0.66 | ~194k |
| 75% | 0.70 | ~209k |
| 80% | 0.74 | ~224k |
| 90% | 0.82 | ~254k |

Aggressive alternate if you think the crowd will over-invest in speed:

- Research 13
- Scale 37
- Speed 50

I prefer 15 / 44 / 41 as the first submission because the cost of chasing speed too high is real.

---

## Recommended next actions

1. Submit `round2_strategy_primary_bid3001.py` first.
2. Use manual allocation `15 / 44 / 41` unless you have strong evidence the field median speed is above 45.
3. If a first portal bundle comes back materially lower than expected, inspect whether the randomized 80% access is starving pepper entry or osmium fills.
4. If the portal suggests full access is crucial or if leaderboard chatter strongly implies high MAF median, consider `round2_strategy_aggressive_bid5001.py`.
5. Do not bid above 8000 yet without evidence.

