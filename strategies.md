# Strategy Registry

This file records the actual Round 1 strategies in the repo, not just their names. Each section is self-contained, uses the file that implements the strategy, and reports results from an official submission artifact when one exists. If a repo strategy is byte-identical to an official bundle, the section says so and uses that bundle's `.json` / `.log` result. If no official bundle exists, the section uses the latest local `.log`.

# Round 1

Round 1 splits cleanly into two market personalities. `ASH_COATED_OSMIUM` behaves like a stationary book around `10000`, so the useful strategies are inventory-aware market makers that lean on short-horizon order-book alpha but still make most of their money from spread capture and disciplined rebalancing. `INTARIAN_PEPPER_ROOT` behaves like an upward-drifting product with usable microstructure timing, so the useful strategies are long-biased carry traders that buy dips, maintain inventory, and sell only when the unwind is unusually attractive or the session is late. Most later files are either stricter specializations of one of those ideas or direct merges of the best osmium and pepper modules.

The repo history is also unusually clean in one respect: many of the named strategies are not vague cousins but exact copies or near-exact constant retunes. That matters because the right way to document them is not to invent fake differences. `current_trader`, `scratch_alpha_01`, and `184591` are the same family in the strict sense that matters. `official_221414_plus` is the repo copy of `224169`. `round1_portal_pepper_hold` and `round1_portal_pepper_swing` are the repo copies of `233714` and `233545`. `aggressive_hybrid_v2` is the repo copy of `222545`. The sections below preserve those relationships explicitly so the document remains accurate to the code rather than just neat on the page.

## Round 1 Result Ladder

For quick orientation, the main official Round 1 totals documented in this file are:

- `233545`: `9950.5`
- `233714`: `9870.5`
- `224169`: `9440.5`
- `221414`: `9270.625`
- `222545`: `8837.75`
- `219274`: `6975.875`
- `184591`: `6286.5625`
- `218688`: `4726.25`
- `214011`: `4237.0`
- `167536`: `2974.2734375`
- `218869`: `2249.625`

That ranking already captures most of the Round 1 evolution. The middle phase of the repo is about discovering that pepper should be carried harder. The late phase is about discovering that, on the recorded portal window, hardcoded early pepper accumulation and small scheduled pepper swings beat the cleaner dynamic pepper specialist. Osmium improves more slowly and mostly through inventory-envelope tuning rather than through a sequence of big conceptual rewrites.

## Documentation Conventions

Each section uses the same headings on purpose. "Overview" explains the strategic idea in plain language. "Pepper strategy" and "Osmium strategy" describe the actual trading logic for each product rather than vague intent. "Additional details" is reserved for things that would otherwise be easy to miss, such as identical-file relationships, retune-only changes, portal warnings, or simulator caveats.

The file is also intentionally asymmetric across strategies. A research script does not need fake PnL, an official artifact does not need speculative commentary about whether it "probably" matched a repo file if the identity is exact, and a local-only experimental file should not be presented with the same authority as a portal-validated submission. The goal is consistency of structure, not artificial sameness of content.

## How To Read Results

This registry mixes three kinds of result sources, and they should not be treated as interchangeable.

- Official bundle result: this is the strongest evidence, because it comes from the actual submitted `.json` and `.log` artifact in `ROUND1/official_submissions/...`.
- Identical-file official result: this is also strong evidence, because the repo file is byte-identical to an official bundle, so citing the official artifact is the right thing to do.
- Local backtest result: this is useful diagnostic evidence, but not portal truth. It is appropriate for research-only files such as `aggressive_hybrid_v1`, where no official artifact exists.

The result formatting in each section is deliberately minimal:

- `total` means final aggregate PnL for the run.
- `pepper only` means final PnL attributed to `INTARIAN_PEPPER_ROOT`.
- `osmium only` means final PnL attributed to `ASH_COATED_OSMIUM`.

Those three numbers are enough for most comparisons because the codebase is strongly modular. When a family retune improves only pepper or only osmium, that usually tells the real story much more clearly than the total alone.

Two interpretation rules are worth keeping in mind:

- If two files are identical, use the official artifact once and treat the repo copy as the same strategy, not as a distinct strategy with a duplicate result.
- If local and official results disagree, the official result dominates. A large part of this repo's Round 1 documentation exists precisely because public replayers and portal outcomes do not always agree.

## Round 1 Evolution

The Round 1 strategy tree is easier to understand if it is read as a sequence of discoveries instead of as a flat list of files. The first discovery is structural: osmium and pepper should not be traded with the same philosophy. Osmium behaves like a mean-reverting inventory game around a stable center, so edge comes from quoting well, skewing inventory intelligently, and monetizing short book-pressure signals. Pepper behaves like a drifted asset, so edge comes from accepting that long inventory is usually desirable and then using microstructure only to improve entry timing and occasional exits.

The second discovery is that better pepper performance did not come from increasingly complicated signal stacks alone. The large improvement from `184591` through `221414`, `224169`, `233714`, and `233545` is mostly a change in posture: the code becomes progressively more comfortable holding meaningful long pepper inventory, buying earlier in the session, and selling less often. In other words, later pepper strategies win because they express the carry thesis more directly, not because they found some magical extra alpha term.

The third discovery is that the best late portal scores are partly path-specific. `233714` and `233545` are excellent Round 1 files, but they are excellent because they exploit the observed early-session portal window very hard with explicit accumulation rules and, in the swing version, a scheduled trim-and-rebuy plan. That makes them strong references for what actually won Round 1 in this repo, but weaker references for what should be generalized blindly to a different environment.

## Research Baseline

Location: `ROUND1/research/analyze_round1.py`

Overview: This is not a trading strategy. It is the research script that establishes the repo's Round 1 priors by loading all Round 1 price and trade CSVs, building enriched book features, and writing diagnostic plots plus `ROUND1/research/outputs/summary.md`.

Pepper strategy: The script shows that pepper has a strong linear drift close to `0.001 * timestamp`, then studies the residual microstructure around that drift by tracking spread, top-of-book imbalance, wall prices, wall-mid deviation, and detrended price paths. That is the analytical basis for every later long-biased pepper strategy in the repo.

Osmium strategy: The script shows that osmium is much closer to a stationary product around `10000`, with smaller directional structure and more value in short-horizon order-book pressure. That is the analytical basis for the repo's osmium market-making family.

Additional details: "Wall price" here is a research heuristic defined as the highest-volume displayed level on each side. It is useful for signal discovery, but it is not a simulator-calibrated fill model. The script discovers signals; it does not simulate queue position, matching, or realistic PnL.

Implementation details:
- The script enriches each tape with `spread`, `top_imbalance`, `wall_bid_price`, `wall_ask_price`, `wall_mid`, `wall_deviation`, `next_valid_mid_change`, and `pepper_detrended`.
- It computes per-product summaries such as mean mid, mid volatility, mean spread, and correlations between microstructure features and future mid moves.
- It plots both raw and detrended pepper, which is why later strategy files explicitly separate structural carry from microstructure timing.
- It writes concrete research artifacts rather than strategy outputs, including `mid_paths.png`, `pepper_detrended.png`, `spread_boxplot.png`, `imbalance_signal.png`, and `trade_overlay.png`.

Why it matters: This file is the reason the rest of the Round 1 strategy tree is coherent at all. It provides the empirical basis for "osmium is a stationary MM product" and "pepper is a drifting carry product with exploitable residual timing."

Results: none. This file produces research artifacts, not trading PnL.

## Current Trader

Location: `ROUND1/strategies/current_trader.py`

Overview: This is the main balanced two-product market maker in the repo's "184591 family." It keeps osmium centered on a stationary fair near `10000`, while pepper is intentionally long-biased around a drifting anchor. The design goal is not maximum carry; it is a controlled two-product trader that still lets pepper run long when the book agrees with the trend.

Pepper strategy: Pepper fair is `anchor + 0.001 * timestamp + alpha`, where the anchor is updated from observed mid minus drift. Alpha comes from wall-mid deviation, top-of-book imbalance, and a short wall-mid trend. The strategy does not target flat inventory; it targets a persistent long book using `PEPPER_TARGET_LONG = 14`, then shifts that target with imbalance and trend, clipped to `[-6, 32]`. It sweeps up to three ask levels when asks are cheap versus fair, and it keeps passive bids inside the spread so long as inventory is still below the target.

Osmium strategy: Osmium fair is `10000 + alpha`, with alpha driven by wall-mid deviation, top-of-book imbalance, and a short wall-mid trend. Target inventory is always `0`, so the reservation price is purely an inventory-skewed version of fair. The strategy sweeps only when the displayed edge is strong enough, then posts inside-spread quotes whose sizes shrink or grow with inventory bias.

Additional details: This file is byte-identical to `ROUND1/research/scratch_alpha_01/trader.py` and to official bundle `184591.py`. It is the repo's canonical example of a two-product trader that is still a market maker in osmium but already a carry trader in pepper.

Execution and risk notes:
- Osmium sweeps first, then quotes passively around reservation value, with target inventory fixed at `0`.
- Pepper also sweeps first, but its passive quoting is intentionally inventory-seeking because it wants to live long rather than flat.
- The file uses persistent state only for short histories and the pepper anchor. There is no path-specific hardcoded trade schedule.
- Soft limits shut off quoting on the risk-increasing side once inventory gets too large, but the strategy is still structurally willing to stay meaningfully long pepper.

Why it matters: This is the cleanest balanced family in the repo and the one most people should read first if they want to understand how the codebase moved from generic market making into product-specific logic.

Practical takeaway: If someone wants one file that still looks like a disciplined general trading strategy rather than a portal-path execution schedule, this is the best first file to read.

Main risk: Pepper performance in this family depends heavily on passive fills near the inside spread. That is exactly why this family later became central to the portal-vs-local mismatch investigation.

Results: total `6286.5625`, pepper `3655.5`, osmium `2631.0625`, from identical official bundle `ROUND1/official_submissions/184591/184591.json` and `184591.log`.

## scratch_alpha_01

Location: `ROUND1/research/scratch_alpha_01/trader.py`

Overview: This is a research-staging copy of the current-trader logic, not a distinct strategy family. It exists as a sandboxed research file, but the implemented behavior is the same balanced two-product trader that later became official bundle `184591`.

Pepper strategy: Pepper uses a drifting anchor, then adds wall-mid deviation, imbalance, and short trend to build a long-biased fair. Inventory is deliberately centered above zero, so the file carries pepper rather than recycling it back to flat.

Osmium strategy: Osmium remains a stationary-fair market maker around `10000` with short-horizon alpha and zero target inventory. It monetizes microstructure by taking obvious edges and then leaning its passive quotes with inventory.

Additional details: This file is byte-identical to `ROUND1/strategies/current_trader.py` and to `ROUND1/official_submissions/184591/184591.py`, so the correct interpretation is "research copy of the same strategy," not "variant."

Execution and usage notes:
- Use this file when you want to analyze the `184591` family from the research side without touching the main editable strategy path.
- The fair-value model, reservation logic, and inventory behavior are all the same as `current_trader`.
- Because the code is identical, any difference in observed performance must come from environment, tooling, or replay conditions rather than from strategy logic.

Why it matters: This file is useful precisely because it is not different. It gives the repo a safe alias for studying the same family from a research path.

Results: total `6286.5625`, pepper `3655.5`, osmium `2631.0625`, using the identical official `184591` artifact.

## Official Submission 167536

Location: `ROUND1/official_submissions/167536/167536.py`

Overview: This is the older, more symmetric two-product market maker. It already recognizes pepper drift, but it still treats both products more like skewed market-making problems than like fully specialized product-specific strategies. Relative to later files, it is less opinionated, smaller, and more conservative.

Pepper strategy: Pepper fair is still anchor-plus-drift-plus-alpha, but inventory stays centered on the live position rather than on an explicit long target. It buys and sells symmetrically around reservation value, uses `50`-lot local limits, and only expands sweep depth from two levels to three when alpha is strong. That makes it a drift-aware pepper market maker, not a true carry accumulator.

Osmium strategy: Osmium is already a stationary-fair market maker around `10000`, with deviation, imbalance, and short trend feeding alpha. It uses conservative sizes, explicit flattening triggers, and passive quote improvement of `6` ticks, so it is relatively careful about inventory.

Additional details: This file is the right baseline for comparing the earlier symmetric style against the later target-inventory pepper family. Its main limitation is that it under-expresses the structural pepper drift because it never says "I want to stay long."

Execution and style notes:
- One generic order generator handles both products, which is a useful marker of how early this design is.
- Osmium and pepper both rely on reservation-price quoting, flatten triggers, and inventory-pressure scaling of passive order size.
- The file is conservative in limits but relatively aggressive in quote-improvement constants, which means it can look cleaner conceptually than it really is under strict passive-fill assumptions.

Why it matters: This is the correct historical checkpoint for "before the repo really specialized pepper."

Results: total `2974.2734375`, pepper `1857.3984375`, osmium `1116.875`, from `ROUND1/official_submissions/167536/167536.json` and `167536.log`.

## Official Submission 184591

Location: `ROUND1/official_submissions/184591/184591.py`

Overview: This is the official artifact for the repo's main balanced market-maker family. It is the same logic as `current_trader.py`: osmium is traded as a stationary market around `10000`, while pepper is traded as a drift-aware long-biased market maker with an explicit positive target inventory.

Pepper strategy: Pepper fair is `anchor + 0.001 * timestamp + alpha`, with alpha built from wall-mid deviation, imbalance, and short trend. The target inventory is positive by design and can climb to `32`, so the strategy keeps working bids and accumulates long pepper whenever the tape looks even modestly favorable.

Osmium strategy: Osmium fair is `10000 + alpha`, with `alpha` clipped to `[-3.2, 3.2]`. The file always wants osmium inventory back at `0`, so the market-making logic is a cleaner spread-capture engine than the pepper side.

Additional details: This bundle is the exact same code as `ROUND1/strategies/current_trader.py` and `ROUND1/research/scratch_alpha_01/trader.py`. The result therefore validates that family, not just the submission folder copy.

Why it matters:
- This is one of the core portal-truth anchors in the repo.
- When local replayers disagree with this family, this artifact should dominate the interpretation.
- It is the official reference point for the balanced two-product design before the repo moved into more aggressive specialist and portal-targeted branches.

Results: total `6286.5625`, pepper `3655.5`, osmium `2631.0625`, from `ROUND1/official_submissions/184591/184591.json` and `184591.log`.

## Official Submission 214011

Location: `ROUND1/official_submissions/214011/214011.py`

Overview: This is the first pure pepper specialist in the repo. It abandons osmium completely and expresses the simplest clean version of the repo's pepper thesis: estimate the drift anchor, add microstructure alpha, build a long target, buy into that target, and only trim when the unwind is favorable.

Pepper strategy: Pepper fair is split into a forward-looking entry fair and a lower unwind fair, which makes the strategy more willing to buy than to sell. Target inventory starts from `PEPPER_BASE_TARGET = 42`, then moves with clipped alpha. It buys up to three ask levels, keeps an aggressive passive bid when below target, and enforces long-only behavior so the book never flips short.

Osmium strategy: None. The file explicitly returns no osmium orders.

Additional details: This file is the template for the later pepper-only and merged specialist family. Its weakness is concentration: all edge comes from one product and one thesis, namely that carrying long pepper is desirable.

Execution and structure notes:
- Pepper is the only active product. Osmium orders are explicitly omitted.
- The file separates entry economics from exit economics by using a higher forward fair than unwind fair.
- It buys multiple ask levels, keeps a strong passive bid while behind target, and only sells to trim a long when the unwind looks unusually favorable.

Why it matters: This is the first file where the pepper thesis appears in its cleanest specialist form rather than as a biased extension of a general MM engine.

Practical takeaway: Once this file exists, most later pepper-family changes are about how hard to carry and how hard to bid, not about whether pepper should be treated as its own specialist product.

Results: total `4237.0`, pepper `4237.0`, osmium `0.0`, from `ROUND1/official_submissions/214011/214011.json` and `214011.log`.

## Official Submission 218688

Location: `ROUND1/official_submissions/218688/218688.py`

Overview: This is the same pepper-only specialist as `214011`, but with the inventory ceiling raised from `50` to `80`. Nothing material changes in the logic; the file simply allows the same thesis to hold and recycle a larger long position.

Pepper strategy: Pepper still uses the anchor-plus-drift fair, the same forward-vs-unwind separation, the same target-inventory construction, and the same long-only enforcement. The practical change is that the target has more room to matter because the hard position ceiling is no longer binding as early.

Osmium strategy: None. The file still returns no osmium orders.

Additional details: The correct reading of this file is "same idea, larger balance sheet." Because the logic is unchanged apart from limits, the result isolates the value of allowing the strategy to stay longer pepper for longer.

Why it matters:
- This is one of the cleanest A/B comparisons in the repo.
- It shows that the pepper specialist did not saturate at `50`; it benefited from being allowed to hold more inventory.
- That lesson directly feeds into the later specialist-combination files that keep pushing pepper target inventory upward.

Results: total `4726.25`, pepper `4726.25`, osmium `0.0`, from `ROUND1/official_submissions/218688/218688.json` and `218688.log`.

## Official Submission 218869

Location: `ROUND1/official_submissions/218869/218869.py`

Overview: This is the clean standalone osmium specialist. It treats osmium as a stationary product around `10000`, adds short-horizon alpha from wall-mid deviation, imbalance, and trend, and turns that into a small target inventory plus tight inside-spread market making.

Pepper strategy: None. The file explicitly returns no pepper orders.

Osmium strategy: Osmium fair is `10000 + alpha`, with alpha clipped to `[-4, 4]`. Unlike the earlier balanced files, this strategy allows a bounded directional target using `round(alpha * 5)` clipped to `[-20, 20]`, so it can lean into short-lived book pressure instead of always snapping back to flat. It sweeps two or three levels depending on alpha magnitude, then posts best-price passive quotes with additional flattening when inventory gets too large.

Additional details: This is the osmium module later reused unchanged inside `219274`, `221414`, and `224169` except for explicit constant retunes. It is the repo's cleanest proof that osmium can be traded as a specialist market-making product on its own.

Execution and style notes:
- The file uses a bounded non-zero target inventory rather than forcing osmium back to flat immediately.
- It takes more levels when alpha magnitude is larger, which makes the leg more responsive to very strong book pressure than the balanced `184591` family.
- Quote improvement is only one tick, so the edge is less dependent on generous passive matching semantics than some earlier files.

Why it matters: This is the clean standalone osmium reference that the later specialist-combination family builds on almost unchanged.

Practical takeaway: If someone wants to understand the osmium specialist line without pepper noise, this is the correct file to study.

Results: total `2249.625`, pepper `0.0`, osmium `2249.625`, from `ROUND1/official_submissions/218869/218869.json` and `218869.log`.

## Official Submission 219274

Location: `ROUND1/official_submissions/219274/219274.py`

Overview: This is the first direct merge of the repo's best single-product specialists. It takes the osmium module from `218869` and the pepper module from `218688`, places them in one file, and otherwise changes almost nothing.

Pepper strategy: Pepper is the same long-biased `218688` carry specialist: anchor-plus-drift fair, forward-vs-unwind pricing, positive target inventory, aggressive bidding below target, and long-only enforcement.

Osmium strategy: Osmium is the same `218869` specialist: stationary fair near `10000`, bounded directional target, multi-level taker logic, explicit flattening, and passive best-price quoting.

Additional details: This file is important because it proves the two product modules coexist cleanly. The result is exactly additive: the official total equals `218869 + 218688`, which is strong evidence that the merged file really is just the sum of two independent specialist legs on that window.

Relationship notes:
- Osmium logic is the `218869` specialist with no material architectural change.
- Pepper logic is the `218688` specialist with no material architectural change.
- There is no evidence in the official result that the two legs cannibalized each other on the recorded window.

Why it matters: This is the file that proves a merged specialist architecture is viable before the later constant retunes start pushing pepper much harder.

Results: total `6975.875`, pepper `4726.25`, osmium `2249.625`, from `ROUND1/official_submissions/219274/219274.json` and `219274.log`.

## Official Submission 221414

Location: `ROUND1/official_submissions/221414 (9200)/221414.py`

Overview: This file is a two-module specialist strategy. `ASH_COATED_OSMIUM` is traded as a short-horizon stationary market around `10000`, while `INTARIAN_PEPPER_ROOT` is traded as a directional carry product that should usually sit long. The key idea is to stop forcing one shared market-making style across both products. Instead, osmium monetizes spread plus inventory-aware alpha, while pepper uses a higher entry fair than exit fair so the code naturally prefers buying and holding over frequent round-tripping.

Pepper strategy: Pepper starts from a drifting base fair, `anchor + 0.001 * timestamp`, where the anchor is updated from realized mids. It then adds microstructure alpha from wall-mid deviation, top-of-book imbalance, short wall-mid trend, and short imbalance trend. That alpha feeds two prices: `forward_fair = base_fair + 6 + alpha` for entries and `unwind_fair = base_fair + alpha` for exits. Because the entry fair is permanently higher than the unwind fair, buying is structurally easier than selling. Inventory is also explicitly long-biased: `PEPPER_BASE_TARGET = 66`, then a clipped alpha term pushes the target up or down, with a hard soft-limit of `78` and a late-session target cap after `940000`. Execution follows that bias. The strategy sweeps up to three ask levels when the entry edge is good, or even when the displayed edge is only non-negative but inventory is still below target. It sweeps only the top two bid levels on the sell side, and it sells mainly when bids are rich versus `unwind_fair` or when the book is above target. Passive quoting reinforces the same posture: the bid is improved aggressively with `PEPPER_BID_IMPROVE = 7`, while the ask uses `PEPPER_ASK_IMPROVE = 0`, meaning the strategy competes harder to buy than to sell.

Osmium strategy: Osmium is a stationary specialist built around `fair = 10000 + alpha`, with alpha from wall-mid deviation, imbalance, and short trend. Unlike the older balanced family, this file allows a bounded non-zero osmium target so the reservation price can lean with short-lived book pressure instead of always snapping directly to flat. It sweeps two levels normally and three when alpha is large, buys asks when they are cheap versus fair or when inventory needs to move back toward target, and symmetrically hits bids on the sell side. After the taker pass, it adds explicit flattening clips once inventory moves beyond `OSMIUM_FLATTEN_TRIGGER = 34`, then posts passive bid and ask quotes one tick inside the spread with inventory-aware sizing. `OSMIUM_BASE_SIZE = 20` makes the whole osmium leg materially larger than in the earlier merged specialist file.

Additional details: This is the first bundle where the merged specialist architecture is not just combined cleanly but materially retuned. The gain over `219274` comes almost entirely from pushing the pepper carry thesis much harder while also enlarging the osmium order sizes. In lineage terms, the pepper module is the `214011` / `218688` specialist with more aggressive inventory targets and less eager offering, and the osmium module is the `218869` specialist with a larger clip size.

Exact retune relative to `219274`:
- `OSMIUM_BASE_SIZE = 20` instead of `14`
- `PEPPER_BASE_TARGET = 66` instead of `42`
- `PEPPER_BID_IMPROVE = 7` instead of `6`
- `PEPPER_ASK_IMPROVE = 0` instead of `1`
- `PEPPER_SOFT_LIMIT = 78` instead of `50`

Why it matters: This bundle is the strongest proof in the repo that most of the middle-period improvement came from letting pepper carry much harder, not from inventing a new cross-product framework.

Practical takeaway: The story of `221414` is simple but important: the same merged specialist architecture became much better once pepper was allowed to live much closer to the hard limit.

Results: total `9270.625`, pepper `7021.0`, osmium `2249.625`, from `ROUND1/official_submissions/221414 (9200)/221414.json` and `221414.log`.

## official_221414_plus

Location: `ROUND1/strategies/official_221414_plus.py`

Overview: This file is a self-contained two-product specialist trader and the editable repo copy of official bundle `224169`. It runs a large-size osmium market-making engine next to a long-biased pepper carry engine. The file is still fully model-based rather than hardcoded to one opening path: osmium uses live fair-value and reservation-price logic, and pepper uses a live anchor, live alpha, and explicit entry-versus-exit pricing rather than a fixed script.

Pepper strategy: Pepper computes `base_fair = anchor + 0.001 * timestamp`, where the anchor is persistent state updated from observed mids after removing the expected drift. It then forms alpha from wall-mid deviation, top-of-book imbalance, short wall-mid trend, and short imbalance trend, clipped to a bounded range so the signal moves the trader without destabilizing it. That alpha feeds `forward_fair = base_fair + 6 + alpha` and `unwind_fair = base_fair + alpha`. The gap between those two prices is the core of the algorithm: the trader is willing to pay up to establish the long, but it requires meaningfully richer conditions to exit. Inventory policy is also explicit. The target starts at `68`, moves with clipped alpha through `PEPPER_TARGET_SLOPE = 8`, is capped by the `80`-lot hard limit, and only gets cut back late in the day after `PEPPER_ENDGAME = 950000`, with the final cap relaxed to `12` instead of `10`. Execution is built around that target. The file sweeps up to three ask levels when `forward_fair` says they are attractive, or when it is still below target and the edge is at least non-negative. On the sell side it only checks the top two bid levels and mainly trims when bids are clearly rich versus `unwind_fair` or when inventory is above target. Passive quotes keep the same bias: the bid is improved aggressively by `7`, while the ask is not improved at all, so the maker behavior also tries harder to accumulate than to liquidate.

Osmium strategy: Osmium is a specialist market maker around `10000` with short-horizon directional lean. The file computes `fair = 10000 + alpha`, where alpha comes from wall-mid deviation, imbalance, and recent wall-mid trend, then converts that into a bounded directional target and an inventory-skewed reservation price. The taker pass examines up to two levels, or three when the signal is strong, buying asks that are sufficiently cheap and selling bids that are sufficiently rich. If the current inventory is already on the wrong side of the target, the file is willing to take zero-or-better rebalancing trades even without a full edge. After the taker pass it runs explicit flattening logic only once inventory exceeds `OSMIUM_FLATTEN_TRIGGER = 40`, and it does not fully shut down risk-increasing activity until `OSMIUM_SOFT_LIMIT = 80`. Finally it posts passive quotes one tick inside the spread, with size reduced only when inventory is already large. The result is an osmium leg that is still disciplined, but much less eager to choke off inventory than `221414`.

Additional details: This section is intentionally standalone because the file should be readable without first reading `221414`. The concise lineage is that it keeps the same architecture as `221414` but retunes the inventory envelope. Specifically, it raises `OSMIUM_SOFT_LIMIT` from `58` to `80`, raises `OSMIUM_FLATTEN_TRIGGER` from `34` to `40`, raises `PEPPER_BASE_TARGET` from `66` to `68`, raises `PEPPER_SOFT_LIMIT` from `78` to `80`, delays the pepper endgame from `940000` to `950000`, and raises the final pepper cap from `10` to `12`. The important point is not the family tree; it is the effect. This file lets osmium hold and unwind inventory more freely and lets pepper maintain the long book slightly longer before late-session de-risking starts.

Exact retune relative to `221414`:
- `OSMIUM_SOFT_LIMIT = 80` instead of `58`
- `OSMIUM_FLATTEN_TRIGGER = 40` instead of `34`
- `PEPPER_BASE_TARGET = 68` instead of `66`
- `PEPPER_SOFT_LIMIT = 80` instead of `78`
- `PEPPER_ENDGAME = 950000` instead of `940000`
- Endgame pepper target cap `12` instead of `10`

Why it matters: This file is the editable repo version of the specialist-family peak before the portal-targeted pepper descendants replaced dynamic pepper logic with hardcoded opening behavior.

Practical takeaway: `official_221414_plus` is the right repo file to use when you want the strongest clean specialist-combination logic without crossing into portal-window-specific pepper hardcoding.

Results: total `9440.5`, pepper `7013.0`, osmium `2427.5`, using the identical official `224169` artifact.

## Official Submission 224169

Location: `ROUND1/official_submissions/224169 (9400)/224169.py`

Overview: This is the official portal artifact for the strongest fully dynamic specialist-combination strategy in the repo before the later hardcoded pepper-window files. It trades osmium as a live fair-value market maker and pepper as a live carry trader with explicit asymmetric entry and exit economics. There is no fixed timestamp script on pepper here; all decisions still come from the model state, book state, and current inventory.

Pepper strategy: Pepper maintains a persistent anchor for the drifted product, then computes `base_fair = anchor + 0.001 * timestamp`. It layers on live alpha from wall-mid deviation, top-of-book imbalance, short wall-mid trend, and short imbalance trend. That alpha drives two different fair values: `forward_fair = base_fair + 6 + alpha` for entries and `unwind_fair = base_fair + alpha` for exits. Because the entry price is permanently premiumed over the exit price, the strategy is structurally a long-carry trader rather than a symmetric maker. Inventory target starts at `68`, moves with clipped alpha through a slope of `8`, is bounded by the `80`-lot limit, and only gets cut back late in the session after `950000`, at which point it still allows a residual target of `12`. The taker layer sweeps up to three ask levels when entry economics are good or when the strategy still needs inventory, and it sells only the top two bid levels when unwind economics are strong or when position is above target. The maker layer then reinforces the same idea: aggressively improved bids, effectively unimproved asks, and no interest in short inventory.

Osmium strategy: Osmium is built around a stationary center near `10000`. The file computes a live alpha from deviation, imbalance, and recent trend, converts that into `fair = 10000 + alpha`, then skews reservation pricing toward a bounded directional target so the strategy can lean with book pressure without turning into a large directional bet. It sweeps up to three levels when alpha is large, accepts zero-or-better trades if those trades move inventory back toward target, flattens more assertively only after inventory breaches `40`, and does not choke risk until `80`. Passive bid and ask quotes are then posted one tick inside the spread with size adjusted for inventory and signal strength. In practice, this is a relatively large and tolerant osmium MM, not a hyper-conservative rebalancer.

Additional details: The file is byte-identical to `ROUND1/strategies/official_221414_plus.py`, so the repo strategy file and the official artifact are the same strategy. Relative to `221414`, the conceptual change is small but the operational effect is real: the file gives osmium more room to hold inventory and slightly delays pepper de-risking. The gain over `221414` is `+169.875`, and almost all of that comes from osmium rather than pepper, which is why this bundle is best read as "same pepper thesis, better osmium envelope."

Interpretation notes:
- Total change versus `221414`: `+169.875`
- Osmium change versus `221414`: `+177.875`
- Pepper change versus `221414`: `-8.0`
- The strategy still depends heavily on full-limit pepper carry, but the actual incremental win on this window came from a looser osmium inventory envelope.

Why it matters: This file is the best simple specialist-family bundle before the repo starts path-targeting the portal opening with explicit pepper rules.

Practical takeaway: `224169` is the peak of the clean specialist-combination line. After this file, later gains come mostly from increasingly path-specific pepper logic rather than from cleaner general strategy design.

Results: total `9440.5`, pepper `7013.0`, osmium `2427.5`, from `ROUND1/official_submissions/224169 (9400)/224169.json` and `224169.log`.

## round1_portal_pepper_hold

Location: `ROUND1/strategies/round1_portal_pepper_hold.py`

Overview: This file is a mixed design: osmium remains a normal live specialist market maker, but pepper is no longer model-based. Instead of estimating fair value continuously, the pepper leg becomes a deterministic opening accumulator that tries to fill the full long book as early as possible and then does nothing else. It is the repo copy of official submission `233714`.

Pepper strategy: Pepper here is intentionally simple. The algorithm looks only at the best ask and the first ask volume. If the timestamp is at or before `1000`, it buys the entire displayed best-ask size whenever `best_ask <= 12007`. If the timestamp is after `1000` but at or before `2000`, it uses a looser catch-up band and buys whenever `best_ask <= 12008`. It keeps doing that until the `80`-lot hard limit is reached. There is no pepper anchor, no alpha model, no target function, no unwind fair, no passive quote layer, and no late-session recycling. Once the opening accumulation either fills the book or the price filter stops accepting trades, pepper becomes a pure held carry position. That is the whole strategy, and that simplicity is deliberate: the file is testing whether the dynamic pepper specialist was overtrading relative to what the portal opening actually rewarded.

Osmium strategy: Osmium is still a full live specialist, not a placeholder. It computes `fair = 10000 + alpha` from wall-mid deviation, imbalance, and trend, converts that into a bounded target and reservation price, sweeps favorable asks and bids across up to three levels when alpha is strong, runs explicit flattening once inventory breaches `40`, and posts passive quotes one tick inside the spread with inventory-aware sizing. In other words, only pepper is hardcoded; osmium remains the same large, tolerant `224169` market maker.

Additional details: The key nuance is that this file is not "more detailed pepper logic"; it is less logic in exchange for stronger path fit. By removing the forward-fair / unwind-fair machinery, the file also removes all later pepper churn. The bet is that Round 1 portal data rewarded getting long very early and then simply keeping that exposure. That makes the strategy powerful on the recorded path and fragile off it.

Execution notes:
- Osmium remains byte-for-byte the `224169` specialist.
- Pepper buys only at the best ask.
- Pepper stops completely once inventory reaches `80`.
- There is no attempt to recycle pepper later, so the post-opening pepper path is almost pure carry exposure.

Why it matters: This is the first clear repo file that says a hand-tuned opening pepper policy can outperform a cleaner dynamic pepper model on the portal.

Results: total `9870.5`, pepper `7443.0`, osmium `2427.5`, using the identical official `233714` artifact.

## Official Submission 233714

Location: `ROUND1/official_submissions/233714 (9870)/233714.py`

Overview: This is the official portal proof that the simple opening-accumulator idea worked. The bundle keeps the full `224169` osmium specialist untouched and swaps only the pepper module for a deterministic early buy-and-hold rule. Because the osmium code is unchanged, this artifact is a very clean A/B test of dynamic pepper trading versus scripted early accumulation.

Pepper strategy: Pepper looks only at the best ask, the top ask size, the current timestamp, and current position. If `timestamp <= 1000`, it buys ask-one whenever `best_ask <= 12007`. If `1000 < timestamp <= 2000`, it switches to `best_ask <= 12008` as a catch-up rule. Every accepted trade buys as much of ask-one as possible until the `80`-lot limit is reached. After that, the pepper leg is finished: there are no sells, no passive bids, no fair-value calculations, and no second phase. The strategy is therefore not "a simpler fair model"; it is an execution rule whose entire purpose is to convert the early portal window into an immediate long carry position.

Osmium strategy: Osmium remains the same model-driven specialist as in `224169`: live fair around `10000`, bounded directional lean, multi-level taker logic, flattening beyond `40`, soft-risk gating at `80`, and one-tick inside-spread passive quotes. That identity matters because it isolates the pepper change cleanly.

Additional details: The bundle beats `224169` by `+430.0`, entirely from pepper, and the portal log is clean. That combination makes the interpretation unusually strong: on the portal path that produced this result, the dynamic pepper specialist was not adding value relative to simply buying early and sitting on the long.

Interpretation notes:
- Improvement versus `224169`: `+430.0`
- Osmium contribution to improvement: `0.0`
- Pepper contribution to improvement: `+430.0`
- Clean portal log means the result is not muddied by warning messages or rejected intent.

Why it matters: This bundle turns a design intuition into an official result: on this window, early deterministic accumulation outperformed the more elegant dynamic pepper specialist.

Practical takeaway: This is the clearest official evidence that a simpler pepper rule can beat a more elegant pepper model when the portal heavily rewards early accumulation and later carry.

Results: total `9870.5`, pepper `7443.0`, osmium `2427.5`, from `ROUND1/official_submissions/233714 (9870)/233714.json` and `233714.log`.

## round1_portal_pepper_swing

Location: `ROUND1/strategies/round1_portal_pepper_swing.py`

Overview: This file keeps the same live osmium specialist as `224169` and the same deterministic early pepper accumulator as `233714`, but adds a second pepper phase: a pre-authored guarded swing schedule. It is the repo copy of official submission `233545`. Conceptually, the file says: build the long book early exactly as before, then rotate a small portion of that book around known favorable timestamps and price zones without ever abandoning the overall long carry thesis.

Pepper strategy: Phase one is identical to `233714`: buy ask-one up to the `80`-lot limit whenever `best_ask <= 12007` through `1000` or `best_ask <= 12008` through `2000`. Phase two is driven by `PEPPER_PLAN`, an ordered list of `11` timestamped steps. Each step specifies a side, quantity, and guard price. The file keeps an index in cache and executes steps strictly in order. For a buy step, once the scheduled timestamp has passed, the trade fires only if the current best ask is at or below the guard and there is displayed ask-one volume. For a sell step, it fires only if the current best bid is at or above the guard and there is displayed bid-one volume. Because the quantities are small and the steps alternate between trims and reloads, the plan behaves like a controlled swing overlay on top of the core long book. It is still not a live model; it is a timestamp-and-price script with stateful progression through a predetermined sequence.

Osmium strategy: Osmium is unchanged from `224169` and `233714`: live alpha around `10000`, bounded target inventory, multi-level taker logic, flattening clips beyond `40`, and passive one-tick-improved quotes. As in the hold strategy, only the pepper side is path-authored.

Additional details: The actual plan sells `6`, buys back `5` then `1`, sells `5`, buys `5`, sells `6`, buys `6`, sells `4`, buys `4`, sells `3`, and buys `3` at guarded timestamps. That detail matters because it clarifies what the file is really doing: not broad regime detection, but a handful of small rotations around a long inventory core. The edge gain is only `+80.0` versus `233714`, but it is cleanly attributable to those added pepper swings.

Execution notes:
- Phase 1 is the same deterministic opening accumulator as `233714`.
- Phase 2 is the guarded `PEPPER_PLAN`, which contains `11` timestamp-and-price-conditioned swing steps.
- The strategy stays structurally long; the swing plan trims and reloads around the long book rather than trying to flip directional conviction.

Why it matters: This file shows the repo's most path-specific but still successful pepper refinement: not just hold the carry, but opportunistically realize small scheduled rotations around it.

Results: total `9950.5`, pepper `7523.0`, osmium `2427.5`, using the identical official `233545` artifact.

## Official Submission 233545

Location: `ROUND1/official_submissions/233545 (9951)/233545.py`

Overview: This is the highest-scoring official Round 1 artifact in the registry and the endpoint of the portal-specific pepper branch. The bundle uses the same live osmium specialist as `224169`, the same early pepper accumulation as `233714`, and then overlays a hardcoded pepper swing schedule that trims into strong bids and reloads into lower asks while keeping the book structurally long. It is best understood as a successful execution script for one realized path, not as the cleanest reusable model.

Pepper strategy: Pepper is explicitly two-stage. Stage one is deterministic front-loading: buy the entire best ask when the early or catch-up price filter passes, until the `80`-lot long is established. Stage two advances through `PEPPER_PLAN`, which contains `11` sequential guarded steps. Those steps are not fuzzy signals; each one has a fixed timestamp threshold, side, quantity, and guard price. The state machine executes one step at a time in order, only advancing when the scheduled trade is actually filled. On buy steps, the guard requires the current best ask to be cheap enough; on sell steps, it requires the current best bid to be rich enough. The resulting behavior is a long-carry core position with small scripted rotations around it. The algorithm understands nuance only through those authored guards, not through a live fair-value model.

Osmium strategy: Osmium is identical to `224169` and `233714`, so the osmium leg remains a large but disciplined live market maker around `10000`: signal-driven fair value, bounded target inventory, multi-level sweeps, flattening beyond `40`, soft-risk gating at `80`, and passive quotes inside the spread. That unchanged osmium leg is why the result difference across these three files can be interpreted purely as a pepper statement.

Additional details: The file beats `233714` by `+80.0` and `224169` by `+510.0`, both entirely from pepper, and the portal log is clean. The right reading is therefore narrow but strong: for this portal window, the extra scripted swing layer added value on top of simple accumulation. The wrong reading would be to treat this as a generally robust algorithm. It is deliberately path-authored, and its strength comes from that specificity.

Interpretation notes:
- Improvement versus `233714`: `+80.0`, entirely pepper.
- Improvement versus `224169`: `+510.0`, entirely pepper.
- Osmium is unchanged across `224169`, `233714`, and `233545`, so the whole ranking difference is one pepper-story continuum.

Why it matters: This is the highest-scoring portal artifact in the registry and the clearest example of a strategy that is excellent on one realized path but too hand-authored to treat as a robust general template.

Practical takeaway: Use this file to understand what the recorded portal path rewarded, not as the default template for a reusable Round 1 strategy.

Results: total `9950.5`, pepper `7523.0`, osmium `2427.5`, from `ROUND1/official_submissions/233545 (9951)/233545.json` and `233545.log`.

## Aggressive Hybrid V1

Location: `ROUND1/strategies/aggressive_hybrid_v1.py`

Overview: This is a research-only attempt to merge the stronger observed osmium microstructure extraction from the `184591` family with the stronger pepper carry thesis from the `218688` / `219274` family. Unlike the official specialist files, it is intentionally aggressive on both products and is optimized for upside rather than cleanliness or portal safety.

Pepper strategy: Pepper fair is split into `forward_fair = base_fair + 8.0 + alpha` and `unwind_fair = base_fair + alpha`, with alpha built from wall-mid deviation, imbalance, wall-mid trend, imbalance trend, short mid trend, and a constant carry bias. The target is explicitly long-seeking: `58 + clipped_alpha * 10 + max(0, imbalance) * 6`, clipped to `[28, 78]`, then late-capped to `48`. The execution side is aggressive: it will buy several ask levels, tolerate slightly negative displayed edge while catching up to target, and only sells to trim a long or harvest a strong unwind edge.

Osmium strategy: Osmium fair is `10000 + alpha`, where alpha uses wall-mid deviation, imbalance, wall-mid trend, imbalance trend, and short mid trend. Unlike `current_trader`, osmium also has a directional target using `round(alpha * 7)` clipped to `[-30, 30]`, so the reservation price is skewed toward that target rather than toward flat. The strategy sweeps deeper when alpha is large, then posts layered inside-spread quotes with target-aware size.

Additional details: This file has no official portal bundle. It is a local research candidate whose main risk is that some of its extra pepper edge may depend on public-simulator-friendly passive fills. It is still important because it is the clearest pure expression of the repo's "strong osmium leg plus strong pepper carry leg" hybrid thesis.

Execution and result notes:
- Osmium is an alpha-tilted MM with a non-zero target inventory rather than a flat-target specialist.
- Pepper is an aggressive long-carry accumulator with late target caps and reluctant selling.
- Kevin local cross-check: total `170807`, pepper `150335`, osmium `20472`.
- The corresponding Rust cross-check was slightly lower total but told the same broad story: very strong pepper plus still-positive osmium.

Why it matters: Even though it is not portal-validated, this is one of the best research windows into what a deliberately aggressive two-leg hybrid can look like in this repo.

Results: total `170807`, pepper `150335`, osmium `20472`, from `outputs/backtests/2026-04-16_154457_kevin_round1/kevin.log`.

## Aggressive Hybrid V2

Location: `ROUND1/strategies/aggressive_hybrid_v2.py`

Overview: This is the second aggressive hybrid pass and the exact code later submitted officially as `222545`. It keeps the V1 idea of combining a strong osmium leg with a stronger-than-official pepper carry leg, but shifts the aggression away from passive inside-spread optimism and toward explicit target pressure and taker behavior.

Pepper strategy: Relative to V1, pepper pushes harder. `PEPPER_FORWARD_PREMIUM` rises to `8.5`, the base target rises to `62`, the target slope rises to `10.5`, the minimum target rises to `36`, and the late cap rises to `56`. The buy logic is also more forceful: when it is far below target, it will still buy at mildly negative displayed edge, and it can sweep up to five ask levels in large catch-up states.

Osmium strategy: Osmium keeps the same broad V1 architecture but with cleaner layering. It still uses multi-component alpha, a bounded directional target, aggressive taker logic, and two layers of passive quotes, but the quote construction is more controlled than the rougher first-pass hybrid.

Additional details: This file is byte-identical to official submission `222545`, so the official portal result is the decisive result for the strategy. The main caveat is that the official portal log contains limit-exceeded osmium warnings, which means the result was achieved despite some order baskets being too large under real portal enforcement.

Relationship and interpretation notes:
- This is not just similar in spirit to `222545`; it is the same logic.
- Local replayers gave mixed signals on whether V2 was really better than V1.
- The official portal result therefore matters more than local ranking when judging this file.

Why it matters: This is the clearest example in the repo of why design direction can be right even when the most available public replay tools are not ranking the candidates correctly.

Results: total `8837.75`, pepper `6983.0`, osmium `1854.75`, using the identical official `222545` artifact.

## Official Submission 222545

Location: `ROUND1/official_submissions/222545 (8800)/222545.py`

Overview: This is the official portal artifact for `aggressive_hybrid_v2`. It keeps the same philosophy: osmium is an aggressive alpha-tilted market maker with a non-zero target inventory, and pepper is a long-only carry trader that is willing to force inventory catch-up more aggressively than the simpler official specialist family.

Pepper strategy: Pepper uses a high forward premium, a high positive target, strong carry bias, wide sweep depth when it is behind target, and relatively reluctant selling. The result is a pepper leg that looks much closer to deliberate carry accumulation than to classic market making.

Osmium strategy: Osmium uses a multi-term alpha, target-aware reservation pricing, deep sweeps when alpha is large, and two passive quote layers on both sides. It is more aggressive and more inventory-tolerant than the earlier specialist files.

Additional details: The important implementation detail is in the portal log: `sandboxLog` includes non-empty warnings that osmium order baskets exceeded the hard limit of `80`. So this bundle validates the family on the portal, but it also documents a correctness issue in the official order construction.

Interpretation notes:
- The strategy validated strongly on the official portal even though it was not the cleanest local winner.
- The pepper result is close to the top specialist-family pepper outcomes, but osmium ends in a very different posture from `221414` / `224169`.
- The warnings matter: the result was achieved despite some rejected or adjusted osmium intent, not because the implementation was fully clean under portal enforcement.

Why it matters: `222545` is simultaneously a success case and a warning case. It proves the aggressive hybrid family can work on the portal, and it proves that correctness and cleanliness still matter even when a bundle scores well.

Practical takeaway: `222545` is the right reference when the question is "can the aggressive hybrid philosophy work on real portal data?" It is not the right reference when the question is "which Round 1 file is the cleanest to generalize from?"

Results: total `8837.75`, pepper `6983.0`, osmium `1854.75`, from `ROUND1/official_submissions/222545 (8800)/222545.json` and `222545.log`.

# Round 2

No strategies registered yet.

# Round 3

No strategies registered yet.

# Round 4

No strategies registered yet.

# Round 5

No strategies registered yet.
