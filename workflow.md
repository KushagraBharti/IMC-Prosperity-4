# Workflow

This is the operating workflow for building Prosperity strategies in this repo.

The short version:

- local replay is for research
- the portal is for truth
- robust strategies beat simulator-specific strategies

## Default Loop

1. Edit the active round strategy.
2. Run local replay engines.
3. Inspect product split, trade count, fill style, and inventory path.
4. Submit serious candidates to the portal.
5. Compare portal bundles against local replays when results disagree.
6. Archive good candidates before the next major change.

## Active Files

- Tutorial:
  `TUTORIAL_ROUND/strategies/current_trader.py`
- Round 1:
  `ROUND1/strategies/current_trader.py`
- Round 2:
  `ROUND2/strategies/current_trader.py`
- Round 3:
  `ROUND3/strategies/current_trader.py`

Keep candidate variants in round-local folders, not in the active file.

## Local Tool Order

Use the tools in this order:

1. `Rust`
   Best current local replay baseline.
2. `Kevin`
   Cross-check replay engine.
3. `Xeeshan`
   Cross-check replay engine with slightly different assumptions.
4. `gsgill7` visualizer
   Primary visual inspection layer.
5. `Kevin` visualizer
   Secondary visual inspection layer.
6. `Chris`
   Tutorial-only robustness testing, not a Round 1 truth proxy.

Typical commands:

```powershell
.\scripts\bt-rust.ps1 round1
.\scripts\bt-kevin.ps1 round1
.\scripts\bt-xeeshan.ps1 round1
.\scripts\viz-gsgill.ps1
```

Use the same commands with `round2` when working in Round 2:

```powershell
.\scripts\bt-rust.ps1 round2
.\scripts\bt-kevin.ps1 round2
.\scripts\bt-xeeshan.ps1 round2
.\scripts\viz-gsgill.ps1
```

Use the same commands with `round3` when working in Round 3:

```powershell
.\scripts\bt-rust.ps1 round3
.\scripts\bt-kevin.ps1 round3
.\scripts\bt-xeeshan.ps1 round3
.\scripts\viz-gsgill.ps1
```

Integrated run:

```powershell
python main.py --round round1 --strategy ROUND1\strategies\current_trader.py
```

```powershell
python main.py --round round2 --strategy ROUND2\strategies\current_trader.py
```

```powershell
python main.py --round round3 --strategy ROUND3\strategies\current_trader.py
```

## What Local Replay Is Good For

Use local replay to answer:

- Is the strategy overtrading?
- Is one product carrying or killing the run?
- Is inventory management improving?
- Are fills mostly passive, aggressive, or weird?
- Does the idea survive across multiple replay engines?
- Is the change structurally better, or only better in one simulator?

Local replay is good for:

- debugging
- behavior inspection
- relative comparisons between robust candidates
- fast iteration before portal submission

## What Local Replay Is Bad For

Do not trust local replay for:

- exact portal PnL prediction
- choosing between near-identical candidates using tiny PnL differences
- validating strategies that depend heavily on favorable passive inside-spread fills
- assuming a single replay engine is “the official scorer”

If a strategy only works because one simulator gives generous passive fills, treat it as fragile.

## Known Portal Gap

Current repo investigation shows that official-vs-local discrepancies come from two main sources.

### 1. Dataset gap

Official bundles can imply a different evaluated book path than the public round CSVs.

Concretely:

- the portal bundle’s `activitiesLog` is the closest visible record of the book the portal actually used
- that book can differ materially from `ROUND*/prices_*.csv`
- replaying only the public CSVs can therefore compare against the wrong market path

### 2. Matching gap

Even on the exact extracted official window, the public replayers still do not perfectly match the portal.

What we see repeatedly:

- local replayers start filling some passive inside-spread quotes earlier than the portal
- this happens especially in quote-sensitive products like `INTARIAN_PEPPER_ROOT`
- small fill-semantics differences create large PnL gaps when the strategy depends on passive edge

### Practical meaning

This does not make OSS backtesters useless.

It means:

- use them as instruments, not as oracles
- measure robustness across engines
- submit serious candidates to the portal earlier than you otherwise would

## Strategy Design Rules

When building a new strategy, prefer:

- fair-value logic that still works with fewer passive fills
- inventory control that does not rely on ideal exits
- quoting logic that remains acceptable under pessimistic fill assumptions
- simple execution rules that survive across `Rust`, `Kevin`, and `Xeeshan`

Be careful with:

- one-tick inside-spread farming
- ultra-tight passive quoting with no fallback
- strategies whose edge disappears if passive fills are delayed
- tuning thresholds only to maximize one replay engine’s total PnL

If you suspect simulator sensitivity, ask:

- does the strategy still work if passive fills are rarer?
- does it still work if pepper fills are delayed?
- does the edge come from signal quality, or from replay-specific fill generosity?

## How To Handle Portal Disagreement

When portal and local results disagree:

1. Do not immediately trust the local PnL.
2. Download the official bundle.
3. Compare the submitted `.py` against the local strategy to confirm they are the same.
4. Extract the official window and rerun local replayers on that exact window.
5. Compare fill patterns and first divergence timestamps.
6. Decide whether the idea is still robust enough to keep.

Use:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\investigate-official.ps1 -OfficialArtifact ROUND1\official_submissions\184591\184591.log -Round round1 -Strategy ROUND1\strategies\current_trader.py
```

That investigation produces:

- extracted official-window CSVs
- local reruns on that exact window
- fill-bucket summaries
- first-difference reports

Look under:

- `outputs/investigation/`

## How To Evaluate A Candidate

Before submitting, check these:

- total PnL across `Rust`, `Kevin`, and `Xeeshan`
- per-product PnL split
- own trade count
- whether gains come from one fragile fill pattern
- inventory path and end-of-window inventory
- whether `all / worse / none` mode changes are catastrophic

After submitting, check these:

- official total PnL
- official per-product split
- whether the official bundle shows a very different fill mix
- whether the portal win is structural or only from a fragile corner case

## Decision Rules

Good candidate:

- behaves sensibly across multiple local replayers
- does not rely on magical passive fills
- has understandable product-level economics
- survives portal validation

Bad candidate:

- wins in only one simulator
- loses control of inventory
- needs very optimistic inside-spread fills
- cannot explain where its PnL comes from

## Archive Discipline

Before replacing a candidate that looks promising:

```powershell
.\scripts\package-submission.ps1 round1 -Label candidate
```

Use the active round key when archiving later rounds:

```powershell
.\scripts\package-submission.ps1 round3 -Label candidate
```

Also copy or move stable variants into:

- `ROUND*/strategies/archive/`

and record them in:

- `strategies.md`

The goal is simple:

- keep the active file clean
- keep strong candidates recoverable
- keep official-vs-local evidence attached to the right strategy version
