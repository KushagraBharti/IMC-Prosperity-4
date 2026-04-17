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

The Round 1 artifacts in this repo fall into six clear families:

- `167536`: older symmetric two-product market maker with conservative local `50`-lot limits and no explicit pepper target inventory
- `current_trader`, `scratch_alpha_01`, and `184591`: the main two-product microstructure market-maker family with `80`-lot limits and an explicit long-biased pepper target position
- `214011` and `218688`: pepper-only long-biased trend-accumulation family
- `218869`: osmium-only market-making extraction
- `219274`, `221414`, `official_221414_plus`, `224169`, `round1_portal_pepper_hold`, `233714`, `round1_portal_pepper_swing`, and `233545`: specialist-combination family that merges the `218869` osmium module with a pepper-only carry module, with `221414` as the first major tuned descendant, `224169` as the official validation of the `official_221414_plus` retune, and `233714` / `233545` as increasingly portal-window-targeted pepper descendants
- `aggressive_hybrid_v1`, `aggressive_hybrid_v2`, and `222545`: post-hoc aggressive hybrid family that tries to combine the strongest observed osmium and pepper ideas while accounting for the repo's portal-versus-local mismatch guidance, with `222545` as the official portal artifact for `aggressive_hybrid_v2`

That family structure is not a guess. It is directly visible in the code and in the portal outputs:

- `ROUND1/strategies/current_trader.py` and `ROUND1/research/scratch_alpha_01/trader.py` are byte-identical
- `184591.py` is functionally identical to those two files and differs only by one trailing newline at EOF
- `214011.py` and `218688.py` are the same pepper-only strategy except that `218688.py` raises the configured product limits from `50` to `80`
- `219274.py` combines the osmium logic used in `218869.py` with the pepper logic used in `218688.py`
- `221414.py` is a near-identical descendant of `219274.py` and differs by only five tuned constants:
- `OSMIUM_BASE_SIZE = 20` instead of `14`
- `PEPPER_BASE_TARGET = 66` instead of `42`
- `PEPPER_BID_IMPROVE = 7` instead of `6`
- `PEPPER_ASK_IMPROVE = 0` instead of `1`
- `PEPPER_SOFT_LIMIT = 78` instead of `50`
- `official_221414_plus.py` and `224169.py` are functionally identical and differ only by a trailing newline at EOF
- relative to `221414.py`, that retune changes six operational constants:
- `OSMIUM_SOFT_LIMIT = 80` instead of `58`
- `OSMIUM_FLATTEN_TRIGGER = 40` instead of `34`
- `PEPPER_BASE_TARGET = 68` instead of `66`
- `PEPPER_SOFT_LIMIT = 80` instead of `78`
- `PEPPER_ENDGAME = 950000` instead of `940000`
- endgame pepper target cap `12` instead of `10`
- `round1_portal_pepper_hold.py` and `233714.py` are functionally identical and differ only by leading / trailing newline formatting
- relative to `224169.py`, that portal-targeted descendant keeps osmium unchanged and replaces the pepper module with a deterministic front-loaded accumulator that only buys level-1 asks while `ask_1 <= 12007` through `ts = 1000` or `ask_1 <= 12008` through `ts = 2000`
- `round1_portal_pepper_swing.py` and `233545.py` are functionally identical and differ only by leading / trailing newline formatting
- relative to `233714.py`, `233545.py` keeps the same osmium and same front-loaded pepper acquisition, then adds an `11`-step guarded timestamped pepper swing plan
- the official portal result of `233714` beats `224169` by exactly `+430.0`, entirely from pepper
- the official portal result of `233545` beats `233714` by exactly `+80.0`, again entirely from pepper
- the official portal profit of `219274` is exactly `218869 + 218688`, which strongly suggests that the combined file is just the additive merger of those independent single-product legs on the recorded evaluation window
- `aggressive_hybrid_v1.py` is a new research-only composite that starts from the `184591` osmium family and the `218688` pepper carry thesis rather than matching any one official artifact
- `aggressive_hybrid_v2.py` is the second-pass refinement of that same research composite and is explicitly informed by `repo.md` and `workflow.md` guidance about avoiding overreliance on generous passive inside-spread fills
- `222545.py` is functionally identical to `ROUND1/strategies/aggressive_hybrid_v2.py` and differs only by a trailing newline at EOF

## Aggressive Hybrid V1

Stable name:

- `round1_aggressive_hybrid_v1`

Path:

- `ROUND1/strategies/aggressive_hybrid_v1.py`

Status:

- research candidate
- first aggressive merge attempt after analyzing the official `184591`, `218688`, `218869`, and `219274` artifacts in depth
- not promoted to `current_trader.py`

Design goal:

- keep the stronger observed osmium microstructure extraction from the `184591`-style two-product family
- keep the stronger observed pepper carry thesis from the `218688` / `219274` pepper-only family
- remove as much unnecessary pepper de-risking as possible
- optimize for maximum upside rather than for conservative simulator stability

Fair-value model for osmium:

- fixed base fair at `10000.0`
- alpha combines:
- `0.95 * (wall_mid - mid)`
- `2.85 * top_of_book_imbalance`
- `0.35 * wall_mid_trend`
- `0.45 * imbalance_trend`
- `0.20 * short_mid_trend`
- alpha clipped to `[-4.5, 4.5]`
- fair is `10000 + alpha`
- target inventory is no longer always flat; it becomes `clip(round(alpha * 7), -30, 30)`
- reservation price is `fair - (position - target_position) * 0.11`

Fair-value model for pepper:

- reconstructs structural drift as `anchor + 0.001 * timestamp`
- updates anchor with smoothing `0.12`
- separates entry and exit economics:
- `forward_fair = base_fair + 8.0 + alpha`
- `unwind_fair = base_fair + alpha`
- alpha combines:
- `1.15 * (wall_mid - mid)`
- `3.25 * top_of_book_imbalance`
- `0.60 * wall_mid_trend`
- `0.65 * imbalance_trend`
- `0.20 * short_mid_trend`
- `0.40` constant carry bias
- alpha clipped to `[-5.5, 5.5]`

Target inventory model:

- pepper is explicitly long-seeking rather than symmetric
- raw target is:
- `58 + round(clip(alpha, -3, 3) * 10) + round(max(0, imbalance) * 6)`
- clipped into `[28, 78]`
- after `timestamp >= 980000`, target is capped down to `48`
- strict long-only post-filter prevents the strategy from crossing below zero pepper inventory

Execution model:

- osmium:
- sweeps `2`, `3`, or `4` levels depending on alpha magnitude
- takes displayed liquidity when edge exceeds `1.0` or when inventory needs to move toward target at non-negative edge
- adds flattening clips once inventory breaches `76`
- posts layered passive bid and ask quotes inside the spread, with size tied to target-position gap and signal strength
- pepper:
- sweeps up to `4` ask levels when behind target or strongly bullish
- buys either on positive forward edge or when still below target at slightly negative edge
- sells only to trim an existing long when unwind edge is attractive or inventory is materially above target
- keeps a strong inside-spread passive bid working when below target
- only offers passively when already above target or in endgame

What kind of strategy this is:

- osmium is an alpha-tilted inventory-aware market maker
- pepper is an aggressive long-carry accumulator with opportunistic trimming
- the whole file is a deliberately aggressive two-product hybrid, not a conservative balanced market maker

Strengths:

- much more direct expression of the official pepper carry thesis than `184591`
- keeps an actively trading osmium leg instead of going pepper-only
- uses official-style `80` limits for both products

Main risks:

- still relies materially on passive pepper accumulation
- not portal-validated
- can overstate edge locally if a replay engine is overly generous on inside-spread pepper fills

Observed local cross-check result:

- Kevin total profit: `170807`
- Rust total profit: `170449`
- Kevin product split by day-level stdout sums: `150335` pepper and `20472` osmium
- Rust product split: `150335` pepper and `20114` osmium
- practical conclusion: this is the strongest local research candidate created so far, but the repo rules still require treating those totals as diagnostic rather than as portal truth

## Aggressive Hybrid V2

Stable name:

- `round1_aggressive_hybrid_v2`

Path:

- `ROUND1/strategies/aggressive_hybrid_v2.py`

Status:

- research candidate
- second aggressive pass
- functionally identical to official submission `222545`
- still not clearly superior to `aggressive_hybrid_v1` on the public cross-check replayers

Why it exists:

- this file was created after re-reading `repo.md` and `workflow.md`
- the explicit goal was to make the aggression more portal-aware by relying less on public-simulator-friendly passive inside-spread farming and more on stronger inventory-taking and carry expression
- the resulting logic was later submitted officially as bundle `222545`

How it differs from V1:

- keeps the same broad architecture and product split
- pulls osmium closer to the healthier `v1` layering and skew profile after the first second-pass attempt degraded both products
- raises pepper baseline carry ambition relative to the official files:
- `forward_fair` premium is `8.5`
- base target is `62`
- target slope is `10.5`
- target floor is raised to `36`
- late target cap is raised to `56`
- changes pepper catch-up logic so it will buy while below target at more negative displayed edge than `v1`, especially when the target gap is large
- reduces the most simulator-sensitive passive bid improvement from `7` to `5` so more of the extra aggression comes from deliberate taking and target pressure instead of assuming ideal passive fills

Execution model:

- osmium remains a layered alpha-tilted market maker with `1`-tick inside quoting, bounded target inventory, and explicit flattening near hard risk
- pepper remains long-only, but its buy logic is more willing to force inventory catch-up when below target
- pepper sell logic stays reluctant and mainly trims when significantly above target or in endgame

What was learned from it:

- the repo's portal-gap guidance was directionally useful
- the first naive second pass, which made the strategy more aggressive mostly by improving passive placement, was the wrong move
- the corrected `v2` shifts the extra aggression toward target inventory and taker behavior instead

Observed local cross-check result:

- Kevin total profit: `168234`
- Rust total profit: `168106`
- Kevin product split by day-level stdout:
- day `-2`: `54239` pepper, `7169` osmium
- day `-1`: `51892` pepper, `7203` osmium
- day `0`: `42685` pepper, `5046` osmium
- Rust product split:
- `148845` pepper
- `19261` osmium

Practical conclusion:

- `v2` is materially better than the first broken second-pass attempt
- but it still does not beat `v1` on either Kevin or Rust
- the correct takeaway is that the second pass produced useful design information but not a clear local successor candidate
- however, the exact same logic later appeared as official submission `222545`, so this file is not just a scratch branch; it is a portal-tested family representative

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
- strongest older specialist-combination bundle before `221414`

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

## Official Submission 221414

Stable name:

- `official_221414_specialist_combo_tuned`

Paths:

- `ROUND1/official_submissions/221414 (9200)/221414.py`
- `ROUND1/official_submissions/221414 (9200)/221414.log`
- `ROUND1/official_submissions/221414 (9200)/221414.json`
- `ROUND1/official_submissions/221414 (9200).zip`

Status:

- official artifact
- current strongest recorded Round 1 portal bundle present in the repo

Code relationship:

- direct tuned descendant of `219274`
- same broad architecture as `219274`: osmium specialist plus pepper specialist merged in one file
- differs from `219274` by only five constants:
- `OSMIUM_BASE_SIZE = 20` instead of `14`
- `PEPPER_BASE_TARGET = 66` instead of `42`
- `PEPPER_BID_IMPROVE = 7` instead of `6`
- `PEPPER_ASK_IMPROVE = 0` instead of `1`
- `PEPPER_SOFT_LIMIT = 78` instead of `50`

Products traded:

- `ASH_COATED_OSMIUM`
- `INTARIAN_PEPPER_ROOT`

Fair-value model for osmium:

- unchanged from the `218869` / `219274` osmium specialist family
- fixed fair at `10000.0`
- alpha terms:
- `1.10 * (wall_mid - mid)`
- `2.40 * top_imbalance`
- `0.20 * wall_mid_trend`
- `0.40 * imbalance_trend`
- alpha clipped to `[-4.0, 4.0]`
- target inventory `clip(round(alpha * 5), -20, 20)`
- reservation price `fair - position * 0.10`

Fair-value model for pepper:

- same anchor-plus-drift construction as `218688` / `219274`
- `forward_fair = base_fair + 6.0 + alpha`
- `unwind_fair = base_fair + alpha`
- alpha terms:
- `1.30 * (wall_mid - mid)`
- `3.10 * top_imbalance`
- `0.55 * wall_mid_trend`
- `0.50 * imbalance_trend`
- alpha clipped to `[-4.5, 4.5]`

Target inventory model:

- this is where the real change lives
- raw pepper target is `66 + 8 * clipped_alpha` instead of `42 + 8 * clipped_alpha`
- target is still long-only and still capped to the hard limit
- soft limit is raised from `50` to `78`
- practical effect: the strategy spends much more of the session trying to live near full-limit pepper carry

Execution model:

- osmium execution is effectively the same as `219274`, except taker and passive base size step up from `14` to `20`
- pepper execution is structurally the same as `219274`:
- buy up to three ask levels
- sell only to trim longs
- maintain an aggressive passive bid while below target
- only offer passively when materially above target or in endgame
- the retuned constants make that same execution model far more willing to accumulate and hold pepper:
- higher target means less trimming
- higher soft limit means less suppression of additional buys
- `PEPPER_ASK_IMPROVE = 0` makes passive asks less eager and therefore less likely to bleed inventory out early
- `PEPPER_BID_IMPROVE = 7` makes passive bids more aggressive

Observed official portal result:

- total profit: `9270.625`
- final osmium PnL from activity log: `2249.625`
- final pepper PnL from activity log: `7021.0`
- terminal positions: short `20` osmium, long `80` pepper

Observed trade-path characteristics from `tradeHistory`:

- osmium:
- `123` own trades
- `318` bought, `338` sold
- average absolute inventory during own-trade path about `20.28`
- final position `-20`
- pepper:
- `41` own trades
- `174` bought, `94` sold
- average absolute inventory during own-trade path about `70.73`
- final position `80`
- zero pepper sign changes

Why it matters:

- this bundle proves that the specialist-combination family had much more headroom than `219274`
- the full improvement over `219274` comes almost entirely from pepper:
- osmium PnL is unchanged at `2249.625`
- pepper PnL rises from `4726.25` to `7021.0`
- the cleanest interpretation is that a much more aggressive pepper target and softer buy suppression dominated the result

Main risks:

- it is even more dependent on carrying large pepper inventory than `219274`
- the improved result may be highly sensitive to whether future portal windows still reward full-limit pepper carry

## Official Submission 224169

Stable name:

- `official_224169_221414_plus`

Paths:

- `ROUND1/official_submissions/224169 (9400)/224169.py`
- `ROUND1/official_submissions/224169 (9400)/224169.log`
- `ROUND1/official_submissions/224169 (9400)/224169.json`
- `ROUND1/official_submissions/224169 (9400).zip`

Status:

- official artifact
- strongest simple specialist-family retune before the later portal-targeted pepper descendants
- official representative of `ROUND1/strategies/official_221414_plus.py`

Code relationship:

- functionally identical to `ROUND1/strategies/official_221414_plus.py`
- differs only by a trailing newline at EOF
- direct specialist-family retune of `221414.py`

Exact deltas relative to `221414.py`:

- `OSMIUM_SOFT_LIMIT = 80` instead of `58`
- `OSMIUM_FLATTEN_TRIGGER = 40` instead of `34`
- `PEPPER_BASE_TARGET = 68` instead of `66`
- `PEPPER_SOFT_LIMIT = 80` instead of `78`
- `PEPPER_ENDGAME = 950000` instead of `940000`
- endgame pepper target cap `12` instead of `10`

Products traded:

- `ASH_COATED_OSMIUM`
- `INTARIAN_PEPPER_ROOT`

Fair-value model:

- unchanged from `221414`
- fixed osmium specialist fair around `10000`
- same pepper anchor-plus-drift carry model with separate `forward_fair` and `unwind_fair`

Execution model:

- unchanged in structure from `221414`
- same simple specialist merge architecture
- same osmium specialist MM logic
- same pepper long-carry specialist logic
- the improvement comes from looser risk-envelope constants, not from a new execution algorithm

Observed official portal result:

- total profit: `9440.5`
- final osmium PnL from activity log: `2427.5`
- final pepper PnL from activity log: `7013.0`
- terminal positions: short `16` osmium, long `80` pepper

Observed improvement relative to `221414`:

- total PnL change: `+169.875`
- osmium PnL change: `+177.875`
- pepper PnL change: `-8.0`

Observed trade-path characteristics from `tradeHistory`:

- osmium:
- `123` own trades
- `64` buys and `59` sells, same trade count shape as `221414`
- `322` bought versus `318` in `221414`
- `338` sold, same as `221414`
- average absolute inventory during own-trade path about `19.37`
- final position `-16`
- `6` sign changes, down from `10` in `221414`
- pepper:
- `42` own trades
- `27` buys and `15` sells
- `174` bought and `94` sold
- average absolute inventory during own-trade path about `71.07`
- final position `80`
- zero sign changes

Drawdown and path observations from `activitiesLog`:

- osmium max drawdown improves slightly:
- `102.469` for `224169`
- `107.648` for `221414`
- pepper max drawdown is unchanged at `402`
- pepper path is almost identical, which is why the final pepper PnL is nearly unchanged
- the real gain is osmium monetization with slightly more permissive inventory handling

Why it matters:

- this bundle validates the exact experiment you asked for:
- keep `221414` simple
- raise the soft limits to the maximum
- make only small parameter changes
- the portal result says that worked
- but it also says the win came from osmium, not pepper

Practical interpretation:

- the additional osmium flexibility helped the strategy hold and unwind the specialist leg more efficiently
- the extra pepper aggression was basically neutral to slightly negative on this window
- so the useful lesson is not "push everything harder"
- it is "the `221414` architecture still had osmium headroom under looser inventory constraints"

Main risks:

- this variant still depends heavily on full-limit pepper carry
- the improvement is real, but it is modest rather than transformative
- because most of the gain came from osmium while pepper slipped slightly, future tuning should probably focus on preserving this osmium improvement without paying away any pepper edge

## Official Submission 233714

Stable name:

- `official_233714_portal_pepper_hold`

Paths:

- `ROUND1/official_submissions/233714 (9870)/233714.py`
- `ROUND1/official_submissions/233714 (9870)/233714.log`
- `ROUND1/official_submissions/233714 (9870)/233714.json`

Status:

- official artifact
- first portal-window-targeted descendant of `224169`
- official representative of `ROUND1/strategies/round1_portal_pepper_hold.py`

Code relationship:

- functionally identical to `ROUND1/strategies/round1_portal_pepper_hold.py`
- direct descendant of `224169.py`
- osmium module is unchanged from `224169.py`
- pepper module is completely replaced by a deterministic accumulator with no dynamic anchor, alpha, maker quotes, or unwind logic

Exact pepper execution change relative to `224169.py`:

- buy level-1 pepper asks only
- buy while `best_ask <= 12007` through `ts = 1000`
- if still short of the hard limit, continue buying while `best_ask <= 12008` through `ts = 2000`
- once `80` pepper is reached, stop trading pepper entirely

Products traded:

- `ASH_COATED_OSMIUM`
- `INTARIAN_PEPPER_ROOT`

Fair-value model:

- osmium unchanged from `224169`
- pepper effectively abandons the prior fair-value model in favor of fixed portal-window price acceptance bands

Execution model:

- osmium identical to `224169`
- pepper is an explicit front-load-and-hold implementation
- there is no pepper inventory recycling after the opening accumulation phase

Observed official portal result:

- total profit: `9870.5`
- final osmium PnL from activity log: `2427.5`
- final pepper PnL from activity log: `7443.0`
- terminal positions: short `16` osmium, long `80` pepper

Observed improvement relative to `224169`:

- total PnL change: `+430.0`
- osmium PnL change: `0.0`
- pepper PnL change: `+430.0`

Observed trade-path characteristics from `tradeHistory`:

- osmium is identical to `224169`:
- `123` own trades
- `64` buys and `59` sells
- `322` bought and `338` sold
- average absolute inventory during own-trade path about `19.37`
- final position `-16`
- `6` sign changes
- pepper:
- `8` own trades
- all `8` are buys and all occur during the opening accumulation window
- `80` bought and `0` sold
- fill timestamps are exactly `0`, `200`, `300`, `400`, `500`, `600`, `700`, and `900`
- fill prices are `12006` once and `12007` seven times
- average absolute inventory during own-trade path about `46.75`
- final position `80`
- zero sign changes

Drawdown and path observations from `activitiesLog` and `logs`:

- osmium path is identical to `224169`, including the same final PnL and same max drawdown of `102.469` at `ts = 56900`
- pepper max drawdown worsens to `469.0` at `ts = 1000`, versus `402.0` for `224169`
- after the opening fill sequence, the pepper PnL path becomes a near-pure carry line because the strategy never sells inventory back
- `233714.log` contains no non-empty portal warnings or lambda diagnostics; all `sandboxLog` and `lambdaLog` fields are empty strings throughout

Why it matters:

- this bundle proves that, on the official evaluation window, the dynamic pepper churn in `224169` was leaving money on the table
- simply buying to `80` quickly and refusing to recycle the position improved the portal result by `430.0`
- the entire gain came from pepper while leaving osmium untouched

Main risks:

- this is far more portal-window-specific than `224169`
- the pepper logic is almost entirely hardcoded to a specific early ask regime and a strong upward carry assumption
- if future windows do not offer the same early asks or the same persistent drift, the edge can disappear abruptly

## Official Submission 233545

Stable name:

- `official_233545_portal_pepper_swing`

Paths:

- `ROUND1/official_submissions/233545 (9951)/233545.py`
- `ROUND1/official_submissions/233545 (9951)/233545.log`
- `ROUND1/official_submissions/233545 (9951)/233545.json`

Status:

- official artifact
- current strongest recorded Round 1 portal bundle present in the repo
- official representative of `ROUND1/strategies/round1_portal_pepper_swing.py`

Code relationship:

- functionally identical to `ROUND1/strategies/round1_portal_pepper_swing.py`
- direct descendant of `233714.py`
- keeps the entire `224169` / `233714` osmium module unchanged
- keeps the same opening pepper accumulator as `233714`
- adds a fixed `PEPPER_PLAN` with `11` guarded timestamped pepper swing steps

Exact pepper swing plan layered on top of the `233714` accumulator:

- `14300`: sell `6` if `best_bid >= 12017`
- `19300`: buy `5` if `best_ask <= 12015`
- `20200`: buy `1` if `best_ask <= 12016`
- `32600`: sell `5` if `best_bid >= 12036`
- `38700`: buy `5` if `best_ask <= 12035`
- `64200`: sell `6` if `best_bid >= 12067`
- `65700`: buy `6` if `best_ask <= 12062`
- `74300`: sell `4` if `best_bid >= 12077`
- `74400`: buy `4` if `best_ask <= 12070`
- `77300`: sell `3` if `best_bid >= 12080`
- `82300`: buy `3` if `best_ask <= 12078`

Products traded:

- `ASH_COATED_OSMIUM`
- `INTARIAN_PEPPER_ROOT`

Fair-value model:

- osmium unchanged from `224169`
- pepper is even more explicitly path-dependent than `233714`, because it uses a hand-authored sequence of timestamp-and-guard instructions rather than a live fair-value estimate

Execution model:

- osmium identical to `224169` and `233714`
- pepper has two phases:
- phase 1: buy to the hard limit using the same deterministic ask thresholds as `233714`
- phase 2: execute the guarded `PEPPER_PLAN` one step at a time while preserving a long-only posture and returning to `80`

Observed official portal result:

- total profit: `9950.5`
- final osmium PnL from activity log: `2427.5`
- final pepper PnL from activity log: `7523.0`
- terminal positions: short `16` osmium, long `80` pepper

Observed improvement relative to `233714`:

- total PnL change: `+80.0`
- osmium PnL change: `0.0`
- pepper PnL change: `+80.0`

Observed improvement relative to `224169`:

- total PnL change: `+510.0`
- osmium PnL change: `0.0`
- pepper PnL change: `+510.0`

Observed trade-path characteristics from `tradeHistory`:

- osmium is identical to `224169` and `233714`:
- `123` own trades
- `64` buys and `59` sells
- `322` bought and `338` sold
- average absolute inventory during own-trade path about `19.37`
- final position `-16`
- `6` sign changes
- pepper:
- `19` own trades
- `14` buys and `5` sells
- `104` bought and `24` sold
- average absolute inventory during own-trade path about `64.68`
- final position `80`
- zero sign changes
- the `11` planned swing steps all appear in `tradeHistory` exactly once, which means the guarded schedule executed cleanly on the official window

Drawdown and path observations from `activitiesLog` and `logs`:

- osmium path is again identical to `224169` and `233714`
- pepper max drawdown remains `469.0` at `ts = 1000`, because the opening accumulation is the same as `233714`
- the additional `+80.0` comes from realized pepper swings after the position is already established, not from a better opening acquisition
- `233545.log` contains no non-empty portal warnings or lambda diagnostics; all `sandboxLog` and `lambdaLog` fields are empty strings throughout

Why it matters:

- this is the highest-scoring Round 1 portal artifact currently present in the repo
- it shows that the portal window rewarded not just full-limit pepper carry, but a very specific low-count sequence of opportunistic sell-high / buy-back-lower pepper rotations on top of that carry
- the entire improvement over `224169` and `233714` is pure pepper extraction with zero change to osmium

Main risks:

- this is the most portal-window-specific Round 1 artifact in the repo
- the pepper schedule is effectively hand-authored against one realized path, so it has high fragility outside that path
- it should be treated as a forensic reference for what the portal rewarded, not as a robust general-purpose strategy template

## Official Submission 222545

Stable name:

- `official_222545_aggressive_hybrid_v2`

Paths:

- `ROUND1/official_submissions/222545 (8800)/222545.py`
- `ROUND1/official_submissions/222545 (8800)/222545.log`
- `ROUND1/official_submissions/222545 (8800)/222545.json`
- `ROUND1/official_submissions/222545 (8800).zip`

Status:

- official artifact
- strong portal artifact for the aggressive hybrid family, but no longer one of the top specialist-family scores after `224169`, `233714`, and `233545`
- official representative of the `aggressive_hybrid_v2` family

Code relationship:

- functionally identical to `ROUND1/strategies/aggressive_hybrid_v2.py`
- differs only by a trailing newline at EOF
- not just similar in spirit; it is the same logic family in the exact operational sense that matters

Products traded:

- `ASH_COATED_OSMIUM`
- `INTARIAN_PEPPER_ROOT`

Fair-value model:

- identical to `Aggressive Hybrid V2`

Execution model:

- identical to `Aggressive Hybrid V2`

Observed official portal result:

- total profit: `8837.75`
- final osmium PnL from activity log: `1854.75`
- final pepper PnL from activity log: `6983.0`
- terminal positions: long `65` osmium, long `80` pepper

Observed trade-path characteristics from `tradeHistory`:

- osmium:
- `88` own trades
- `288` bought, `223` sold
- average absolute inventory during own-trade path about `26.47`
- final position `65`
- pepper:
- `34` own trades
- `170` bought, `90` sold
- average absolute inventory during own-trade path about `72.09`
- final position `80`
- zero pepper sign changes

Portal-specific operational note:

- unlike most other official bundles in this repo, `222545.log` contains non-empty `sandboxLog` messages
- there are `7` timestamps with:
- `Orders for product ASH_COATED_OSMIUM exceeded limit of 80 set`
- the bundle still finished successfully, but this is an important implementation detail:
- the official submission attempted some osmium order baskets whose aggregate exposure exceeded the hard limit and the portal flagged them
- that means the official result was achieved despite some rejected or adjusted osmium intent, not with a perfectly clean order stream

Why it matters:

- this bundle validates that the `aggressive_hybrid_v2` logic can score very well on the actual portal even though it was not the best local candidate among the public replayers
- it is one of the clearest examples in the repo of why portal truth must dominate local replay totals
- compared with `221414`, it reaches almost the same pepper outcome but with a very different osmium posture:
- `221414` finishes short `20` osmium and earns `2249.625` osmium PnL
- `222545` finishes long `65` osmium and earns `1854.75` osmium PnL
- so the main competition between these two bundles is not pepper philosophy but which osmium execution style converts microstructure into portal PnL more efficiently

Main risks:

- the official sandbox limit warnings indicate that the osmium order construction still has a correctness / cleanliness issue under real portal enforcement
- the strategy is structurally very aggressive in both products, so future windows can punish it harder than the more specialist-shaped `221414`

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
