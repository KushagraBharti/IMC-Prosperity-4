# Strategy Registry Conventions

When adding a new strategy to Round 1:

- give it a stable name
- record its file path
- explain the strategy in extreme depth
- describe the fair-value model
- describe the execution model
- describe the main risk
- note whether it is a scratch idea, active candidate, archived winner, or official artifact

# Round 1

## Research Baseline

Stable name:

- `round1_research_baseline`

Paths:

- `ROUND1/research/analyze_round1.py`
- `ROUND1/research/outputs/`

Status:

- research and diagnostics only
- not a trader

What it actually does:

- loads every `prices_round_1_day_*.csv` and `trades_round_1_day_*.csv`
- enriches the price tape with `spread`, `top_imbalance`, `wall_bid_price`, `wall_ask_price`, `wall_mid`, `wall_deviation`, `next_valid_mid_change`, and `pepper_detrended`
- defines the wall price as the single highest-volume displayed level on each side, which is a useful research heuristic even though it is not the same thing as the simulator's fill logic
- computes per-product summary statistics including mean mid, mid volatility, mean spread, correlation of top-of-book imbalance with next mid move, and correlation of wall deviation with next mid move
- fits and plots the linear drift in `INTARIAN_PEPPER_ROOT` by subtracting `0.001 * timestamp`
- generates five concrete artifacts:
- `mid_paths.png`
- `pepper_detrended.png`
- `spread_boxplot.png`
- `imbalance_signal.png`
- `trade_overlay.png`
- writes `summary.md` with the main numeric takeaways

Why it matters:

- it is the source of the repo's core Round 1 priors
- it explicitly supports the claim that `ASH_COATED_OSMIUM` is the stable market-making product around `10000`
- it explicitly supports the claim that `INTARIAN_PEPPER_ROOT` has a strong positive linear drift close to `0.001` per timestamp plus usable microstructure residuals
- it makes imbalance and wall-mid deviation measurable instead of anecdotal

Main limitations:

- it does not simulate queueing, matching, passive fills, or inventory path dependence
- it uses a heuristic wall-price construction rather than a simulator-calibrated execution model
- it is for signal discovery, not PnL truth

## Round 1 Strategy Families

The Round 1 artifacts in this repo fall into five clear families:

- `167536`: older symmetric two-product market maker with conservative local `50`-lot limits and no explicit pepper target inventory
- `current_trader`, `scratch_alpha_01`, and `184591`: the main two-product microstructure market-maker family with `80`-lot limits and an explicit long-biased pepper target position
- `214011` and `218688`: pepper-only long-biased trend-accumulation family
- `218869`: osmium-only market-making extraction
- `219274`: explicit combination of the `218869` osmium module and the `218688` pepper module

That family structure is not a guess. It is directly visible in the code and in the portal outputs:

- `ROUND1/strategies/current_trader.py` and `ROUND1/research/scratch_alpha_01/trader.py` are byte-identical
- `184591.py` is functionally identical to those two files and differs only by one trailing newline at EOF
- `214011.py` and `218688.py` are the same pepper-only strategy except that `218688.py` raises the configured product limits from `50` to `80`
- `219274.py` combines the osmium logic used in `218869.py` with the pepper logic used in `218688.py`
- the official portal profit of `219274` is exactly `218869 + 218688`, which strongly suggests that the combined file is just the additive merger of those independent single-product legs on the recorded evaluation window

## Current Trader

Stable name:

- `round1_current_micro_mm`

Path:

- `ROUND1/strategies/current_trader.py`

Status:

- active editable Round 1 strategy
- primary file used by the local wrappers when no explicit strategy path is supplied

Relationship to other files:

- byte-identical to `ROUND1/research/scratch_alpha_01/trader.py`
- functionally identical to `ROUND1/official_submissions/184591/184591.py`
- `184591.py` differs only by one trailing newline, not by logic

Products traded:

- `ASH_COATED_OSMIUM`
- `INTARIAN_PEPPER_ROOT`

Fair-value model for osmium:

- starts from a fixed base fair of `10000.0`
- computes a microstructure alpha from:
- `0.85 * (wall_mid - mid)`
- `2.8 * top_of_book_imbalance`
- `0.35 * trend_signal(history_of_wall_mid, short=4, long=14)`
- clips the resulting alpha to `[-3.2, 3.2]`
- sets `fair = 10000 + alpha`
- sets reservation price to `fair - position * 0.12`
- keeps osmium target inventory at exactly `0`

Fair-value model for pepper:

- maintains a persistent anchor in `traderData`
- updates that anchor using `observed_anchor = current_mid - 0.001 * timestamp`
- smooths anchor updates with `PEPPER_ANCHOR_SMOOTHING = 0.18`
- reconstructs the structural trend fair as `anchor + 0.001 * timestamp`
- computes a microstructure alpha from:
- `1.20 * (wall_mid - mid)`
- `3.10 * top_of_book_imbalance`
- `0.50 * trend_signal(history_of_wall_mid, short=4, long=16)`
- `0.35` of constant carry bias
- clips the total alpha to `[-4.5, 4.5]`
- sets `fair = drift_fair + alpha`

Target inventory model:

- unlike osmium, pepper is intentionally not centered on flat inventory
- computes a long-biased target position as:
- `14 + 10 * imbalance + 4 * clipped_trend`
- clips that target to `[-6, 32]`
- shifts reservation price by `(position - target_position) * 0.10`
- this means the strategy is structurally willing to carry a meaningful long pepper inventory when microstructure agrees with the upward drift

Execution model:

- snapshots the book into sorted bid and ask ladders
- computes best bid, best ask, midpoint, top imbalance, and a volume-weighted wall mid using the top three displayed levels on each side
- sweeps displayed liquidity before quoting passively
- osmium sweeps up to `2` price levels
- pepper sweeps up to `3` price levels
- takes asks when `fair - ask >= take_threshold`
- takes bids when `bid - fair >= take_threshold`
- sizes taker orders with `take_size`, which increases order size when:
- the local edge is larger
- the current position is far from the desired target inventory
- places one passive bid and one passive ask inside the spread whenever capacity remains
- passive quotes are built from reservation price and then clipped back inside the current spread
- passive size is asymmetric and depends on how far current inventory is from target inventory

Risk controls:

- hard product limits are `80` on both products
- soft limits are `66` for osmium and `74` for pepper
- once a soft limit is crossed, quoting on the risk-increasing side is shut off
- `trim_orders` sequentially clips aggregate orders so the final basket cannot exceed the hard limit

What kind of strategy this really is:

- osmium is a classic inventory-aware market maker around a stable anchor
- pepper is not pure market making and not pure trend following
- it is a hybrid: drift-aware, microstructure-timed, long-biased market making

Strengths:

- modular and mechanically simple
- uses persistent state only for histories and the pepper anchor
- puts most of the complexity into fair-value and inventory control instead of special-case execution hacks
- uses official-style `80` limits rather than the older conservative `50` assumption

Main risks:

- pepper performance depends heavily on passive fills near the inside spread
- the strategy is intentionally willing to carry long pepper, so a simulator mismatch on fill order or mark-to-market timing can move results a lot
- this is exactly the family that already shows large portal-versus-local disagreement

Observed official portal result via bundle `184591`:

- total profit: `6286.5625`
- final osmium PnL from activity log: `2631.0625`
- final pepper PnL from activity log: `3655.5`
- terminal positions: short `18` osmium, long `35` pepper
- practical conclusion: this family is the current main portal-validated two-product baseline even though public replayers disagree materially with it

## scratch_alpha_01

Stable name:

- `scratch_alpha_01`

Path:

- `ROUND1/research/scratch_alpha_01/trader.py`

Status:

- active scratch copy
- research-side staging file for the current main strategy family

Relationship to other files:

- byte-identical to `ROUND1/strategies/current_trader.py`
- functionally identical to `ROUND1/official_submissions/184591/184591.py`
- not a separate strategy family

Why it exists separately:

- it gives the repo a research-local copy that can be compared against official artifacts without changing the main editable path immediately
- it is the most natural file to use when investigating why the portal liked `184591` while local public replayers disliked it

Fair-value model:

- identical to `Current Trader`

Execution model:

- identical to `Current Trader`

Main risk:

- because it is the same strategy as `Current Trader`, it inherits the same main risk: pepper sensitivity to fill semantics and inside-spread matching assumptions

Observed significance:

- treat this file as the working research alias for the `184591` family, not as an independent idea

## Official Submission 167536

Stable name:

- `official_167536_two_product_mm_v1`

Paths:

- `ROUND1/official_submissions/167536/167536.py`
- `ROUND1/official_submissions/167536/167536.log`
- `ROUND1/official_submissions/167536/167536.json`

Status:

- historical official artifact
- earlier two-product baseline

Products traded:

- `ASH_COATED_OSMIUM`
- `INTARIAN_PEPPER_ROOT`

Fair-value model for osmium:

- fixed anchor at `10000.0`
- alpha terms:
- `0.95 * (wall_mid - mid)`
- `2.0 * top_imbalance`
- `0.30 * short_vs_long_wall_mid_trend`
- alpha clipped to `[-3.0, 3.0]`
- reservation price `fair - position * 0.12`

Fair-value model for pepper:

- uses structural drift model `anchor + 0.001 * timestamp`
- starts from `PEPPER_INITIAL_ANCHOR = 13000.0`
- updates anchor with smoothing `0.12`
- alpha terms:
- `1.10 * (wall_mid - mid)`
- `2.30 * top_imbalance`
- `0.45 * short_vs_long_wall_mid_trend`
- alpha clipped to `[-4.0, 4.0]`
- reservation price `fair - position * 0.16`
- no explicit long target inventory; it stays centered on current inventory rather than pushing toward a separate desired pepper position

Execution model:

- one generic `generate_orders` function handles both products
- configured with conservative local hard limits of `50` for both products
- that means the code was clearly written under a safer local assumption than the later `80`-limit family
- sweeps cheap asks and rich bids first
- osmium uses `take_edge = 2.0`
- pepper uses `take_edge = 1.0`
- pepper sweep depth expands from `2` to `3` levels when the absolute alpha is at least `1.5`
- uses inventory-pressure multipliers to scale passive bid and ask size separately
- shrinks quoting after a configured endgame timestamp
- explicitly adds flattening orders once inventory crosses a flatten trigger
- improves passive quotes aggressively:
- osmium quote improve is `6` ticks
- pepper quote improve is `5` ticks
- also nudges quotes by one extra tick when the signal is strong

What kind of strategy this is:

- symmetric two-product market making with trend-aware fair values
- more conservative in hard limits than the later family
- more aggressive in quote-improvement constants than the later family
- still fundamentally inventory-aware, but less structurally opinionated about pepper than the `184591` family

Strengths:

- clear and portable code
- explicit flattening logic
- works as a useful reference for a less target-driven pepper model

Main risks:

- conservative `50`-lot assumptions do not match the stronger later `80`-limit files
- large quote-improve settings make passive fill assumptions more important
- pepper logic has no explicit desired inventory target, so it can under-express the structural drift relative to later variants

Observed official portal result:

- total profit: `2974.2734375`
- final osmium PnL from activity log: `1116.875`
- final pepper PnL from activity log: `1857.3984375`
- terminal positions: short `28` osmium, short `4` pepper

How to use it:

- this is the right historical checkpoint when you want to compare the earlier symmetric MM design against the later target-inventory pepper family

## Official Submission 184591

Stable name:

- `official_184591_current_family`

Paths:

- `ROUND1/official_submissions/184591/184591.py`
- `ROUND1/official_submissions/184591/184591.log`
- `ROUND1/official_submissions/184591/184591.json`

Status:

- critical official artifact
- best portal-validated representative of the current active strategy family

Code relationship:

- same logic as `ROUND1/strategies/current_trader.py`
- same logic as `ROUND1/research/scratch_alpha_01/trader.py`
- differs only by a trailing newline at EOF

Fair-value model:

- identical to `Current Trader`

Execution model:

- identical to `Current Trader`

Why it matters:

- it is the exact official bundle that anchors the repo's simulator-mismatch investigation
- this is the artifact to use when you need a portal-truth reference for the current family

Observed official portal result:

- total profit: `6286.5625`
- final osmium PnL from activity log: `2631.0625`
- final pepper PnL from activity log: `3655.5`
- terminal positions: short `18` osmium, long `35` pepper

Main risk:

- if local replayers disagree with this file, trust the portal bundle and treat the replayer as the approximation, not the other way around

## Official Submission 214011

Stable name:

- `official_214011_pepper_only_limit50`

Paths:

- `ROUND1/official_submissions/214011/214011.py`
- `ROUND1/official_submissions/214011/214011.log`
- `ROUND1/official_submissions/214011/214011.json`
- `ROUND1/official_submissions/214011.zip`

Status:

- official artifact
- first pepper-only trend-accumulation variant in the repo

Products traded:

- `INTARIAN_PEPPER_ROOT` only
- explicitly returns no osmium orders

Fair-value model:

- uses only pepper
- reconstructs structural fair as `anchor + 0.001 * timestamp`
- updates the anchor with smoothing `0.10`
- computes alpha from:
- `1.30 * (wall_mid - mid)`
- `3.10 * top_imbalance`
- `0.55 * short_vs_long_wall_mid_trend`
- `0.50 * short_vs_long_imbalance_trend`
- clips alpha to `[-4.5, 4.5]`
- splits fair into two distinct concepts:
- `forward_fair = base_fair + 6.0 + alpha`
- `unwind_fair = base_fair + alpha`
- this is important: the strategy intentionally values buying inventory using a richer forward view than the level it uses to unwind inventory

Target inventory model:

- explicitly long-only
- raw target position is `42 + 8 * clipped_alpha`
- clipped into `[0, limit]`
- limit is set to `50` in this file
- once the session reaches `timestamp >= 940000`, the target is capped down to `10`

Execution model:

- buy up to the first `3` ask levels
- buy if either:
- `forward_fair - ask >= 1.0`
- or current inventory is still below target and the ask is at least non-negative edge
- sell only to trim existing longs
- sell up to the first `2` bid levels
- sell if either:
- `bid - unwind_fair >= 2.0`
- or inventory is above target and the bid is at least non-negative edge
- keeps a strong passive bid working at roughly `best_bid + 6`, bounded by `forward_fair - 1`
- only posts an ask when already long enough or in endgame
- enforces a strict long-only invariant with `0 <= next_position <= limit`

What kind of strategy this is:

- not market making in the symmetric sense
- it is an inventory-seeking pepper accumulator with opportunistic trimming
- it assumes pepper's upward drift is strong enough that holding inventory is a feature, not a bug

Strengths:

- matches the Round 1 structural story for pepper directly
- easy to reason about because it separates entry fair from exit fair

Main risks:

- one-sided exposure
- no diversification from osmium
- profit depends on being allowed to carry a long pepper book
- configured limit is only `50`, so it leaves headroom unused if the real environment allows `80`

Observed official portal result:

- total profit: `4237.0`
- final osmium PnL from activity log: `0.0`
- final pepper PnL from activity log: `4237.0`
- terminal positions: long `50` pepper

## Official Submission 218688

Stable name:

- `official_218688_pepper_only_limit80`

Paths:

- `ROUND1/official_submissions/218688/218688.py`
- `ROUND1/official_submissions/218688/218688.log`
- `ROUND1/official_submissions/218688/218688.json`
- `ROUND1/official_submissions/218688.zip`

Status:

- official artifact
- direct descendant of `214011`

Code relationship:

- same pepper-only logic as `214011`
- main material difference is that configured product limits are raised from `50` to `80`

Products traded:

- `INTARIAN_PEPPER_ROOT` only

Fair-value model:

- identical to `214011`

Execution model:

- identical to `214011`

Why it matters:

- this file isolates the effect of using the same pepper-only logic under a less restrictive inventory cap
- that makes it one of the cleanest A/B comparisons in the whole repo

Observed official portal result:

- total profit: `4726.25`
- final osmium PnL from activity log: `0.0`
- final pepper PnL from activity log: `4726.25`
- terminal positions: long `58` pepper

Practical interpretation:

- compared with `214011`, this file shows that the same pepper thesis benefits from the larger allowable inventory range

Main risks:

- still one-sided pepper exposure
- still no osmium leg
- still vulnerable if the upward-drift assumption weakens or if the simulator punishes inventory carry more harshly than expected

## Official Submission 218869

Stable name:

- `official_218869_osmium_only`

Paths:

- `ROUND1/official_submissions/218869/218869.py`
- `ROUND1/official_submissions/218869/218869.log`
- `ROUND1/official_submissions/218869/218869.json`
- `ROUND1/official_submissions/218869.zip`

Status:

- official artifact
- osmium-only extraction

Products traded:

- `ASH_COATED_OSMIUM` only
- explicitly returns no pepper orders

Fair-value model:

- fixed osmium anchor at `10000.0`
- alpha terms:
- `1.10 * (wall_mid - mid)`
- `2.40 * top_imbalance`
- `0.20 * wall_mid_trend`
- `0.40 * imbalance_trend`
- alpha clipped to `[-4.0, 4.0]`
- reservation price `fair - position * 0.10`
- desired inventory is not flat all the time; it computes `target_position = clip(round(alpha * 5), -20, 20)`

Execution model:

- sweeps `2` levels normally and `3` levels when the alpha magnitude is at least `1.4`
- buys asks when edge is positive enough or when current inventory is below target and the ask is at least not above fair
- sells bids symmetrically when edge is positive enough or when current inventory is above target and the bid is at least not below fair
- adds explicit flattening orders when inventory breaches `34`
- places one passive bid and one passive ask inside the spread
- quote improvement is only `1` tick, so this is much less aggressively quote-improving than `167536`
- passive size shrinks materially when inventory gets large or the session is near the end

What kind of strategy this is:

- pure osmium market making with a light alpha tilt
- it is the cleanest standalone osmium implementation in the repo

Strengths:

- focused
- uses official-style `80` limits
- easier to reason about than the combined files because it isolates one product

Main risks:

- omits the entire pepper opportunity
- total edge ceiling is lower than the best two-product combinations simply because one product is unused

Observed official portal result:

- total profit: `2249.625`
- final osmium PnL from activity log: `2249.625`
- final pepper PnL from activity log: `0.0`
- terminal positions: short `20` osmium

## Official Submission 219274

Stable name:

- `official_219274_combined_single_product_winners`

Paths:

- `ROUND1/official_submissions/219274/219274.py`
- `ROUND1/official_submissions/219274/219274.log`
- `ROUND1/official_submissions/219274/219274.json`
- `ROUND1/official_submissions/219274.zip`

Status:

- official artifact
- strongest recorded Round 1 bundle currently present in the repo

Code relationship:

- contains the osmium-only logic from `218869`
- contains the pepper-only logic from `218688`
- merges them into one two-product submission without materially changing the per-product logic

Products traded:

- `ASH_COATED_OSMIUM`
- `INTARIAN_PEPPER_ROOT`

Fair-value model for osmium:

- same as `218869`

Fair-value model for pepper:

- same as `218688`

Execution model:

- same osmium execution module as `218869`
- same pepper execution module as `218688`
- no visible shared cross-product coupling beyond both modules living in the same class and reading the same `TradingState`

Observed official portal result:

- total profit: `6975.875`
- final osmium PnL from activity log: `2249.625`
- final pepper PnL from activity log: `4726.25`
- terminal positions: short `20` osmium, long `58` pepper

Important structural note:

- the total official profit of `219274` is exactly:
- `2249.625 + 4726.25 = 6975.875`
- that is the exact sum of `218869` and `218688`
- the terminal positions also combine cleanly
- the cleanest interpretation is that `219274` is the direct additive merge of those single-product strategies on the official evaluation window

Why it matters:

- this is the clearest proof in the repo that product-specific specialists can be merged without obvious degradation, at least on the portal window captured by these bundles

Main risks:

- additive success in one portal window does not guarantee additivity in all future windows
- if simulator behavior changes, the two modules could interact through inventory timing, order submission budget, or fill sequencing in ways this snapshot does not expose

# Round 2

## No Strategies Registered Yet

Round 2 strategy work has not been documented in this file yet.

# Round 3

## No Strategies Registered Yet

Round 3 strategy work has not been documented in this file yet.

# Round 4

## No Strategies Registered Yet

Round 4 strategy work has not been documented in this file yet.

# Round 5

## No Strategies Registered Yet

Round 5 strategy work has not been documented in this file yet.
