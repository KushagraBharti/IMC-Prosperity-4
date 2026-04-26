# Repo

This repo is the working research and execution workspace for `IMC Prosperity 4`.

## Structure

- `TUTORIAL_ROUND/`
  Tutorial data, official bundles, round-local research, and the active tutorial strategy.
- `ROUND1/`
  Round 1 data, official bundles, round-local research, and the active Round 1 strategy.
- `ROUND2/`
  Round 2 data, official bundles, round-local research, and the active Round 2 strategy.
- `ROUND3/`
  Round 3 data, official bundles, round-local research, and the active Round 3 strategy.
- `config/`
  Local paths, round metadata, defaults, and tool wiring.
- `scripts/`
  Thin wrappers around OSS backtesters, visualizers, packaging, comparison, and official-gap investigation.
- `outputs/`
  Generated runs, investigations, packaged submissions, and visualizer handoff files.
- `prosperity.md`
  Competition reference and meta-model.
- `strategies.md`
  Running strategy registry by round.
- `workflow.md`
  Practical development workflow, including how to treat portal-vs-local gaps.
- `main.py`
  One-command local runner.

## Where To Edit

- Active tutorial strategy:
  `TUTORIAL_ROUND/strategies/current_trader.py`
- Active Round 1 strategy:
  `ROUND1/strategies/current_trader.py`
- Active Round 2 strategy:
  `ROUND2/strategies/current_trader.py`
- Active Round 3 strategy:
  `ROUND3/strategies/current_trader.py`

Use round-local folders for everything else:

- `ROUND*/research/` for notebooks, analysis code, and investigation notes
- `ROUND*/official_submissions/` for downloaded portal bundles
- `ROUND*/strategies/archive/` for frozen candidates

Do not treat `official_submissions` as editable code. Treat them as ground-truth artifacts.

## Integrated Tools

External OSS repos live under:

- `C:\Users\kushagra\OneDrive\Documents\CS Projects\prosperity-tools`

Integrated tools:

- `xeeshan-backtester`
- `kevin-backtester`
- `rust-backtester`
- `gsgill7-visualizer`
- `kevin-visualizer`
- `chris-monte-carlo`

Roles:

- `Rust` is the best current local replay baseline.
- `Kevin` and `Xeeshan` are cross-check replay engines.
- `gsgill7` is the default visual inspection tool.
- `Kevin` visualizer is a secondary viewer.
- `Chris` is for tutorial-only robustness testing, not portal matching.

## Core Commands

Bootstrap environments:

```powershell
.\scripts\bootstrap-tools.ps1
```

Run all local tools for a round:

```powershell
python main.py --round round1 --strategy ROUND1\strategies\current_trader.py
```

```powershell
python main.py --round round2 --strategy ROUND2\strategies\current_trader.py
```

```powershell
python main.py --round round3 --strategy ROUND3\strategies\current_trader.py
```

Run replay engines individually:

```powershell
.\scripts\bt-xeeshan.ps1 round1
.\scripts\bt-kevin.ps1 round1
.\scripts\bt-rust.ps1 round1
```

```powershell
.\scripts\bt-xeeshan.ps1 round2
.\scripts\bt-kevin.ps1 round2
.\scripts\bt-rust.ps1 round2
```

```powershell
.\scripts\bt-xeeshan.ps1 round3
.\scripts\bt-kevin.ps1 round3
.\scripts\bt-rust.ps1 round3
```

Open visualizers:

```powershell
.\scripts\viz-gsgill.ps1
.\scripts\viz-kevin.ps1
```

Compare runs:

```powershell
.\scripts\compare-runs.ps1 ROUND1\official_submissions\184591 outputs\backtests\...
```

Package a candidate:

```powershell
.\scripts\package-submission.ps1 round1 -Label candidate
```

```powershell
.\scripts\package-submission.ps1 round2 -Label candidate
```

```powershell
.\scripts\package-submission.ps1 round3 -Label candidate
```

Investigate official-vs-local gaps:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\investigate-official.ps1 -OfficialArtifact ROUND1\official_submissions\184591\184591.log -Round round1 -Strategy ROUND1\strategies\current_trader.py
```

## What Is Reliable

Reliable:

- official portal bundles
- official product split and final portal PnL
- relative behavior seen repeatedly across multiple local replay engines
- trade-count, inventory-path, and fill-pattern debugging

Not reliable:

- any single OSS backtester as a portal-equivalent scorer
- absolute local PnL for fill-sensitive strategies
- tiny quote-placement optimizations chosen only from replay totals

## Main Gap Between Portal And OSS Backtesters

The repo investigation so far found three important causes of mismatch:

1. `Official evaluation windows may differ from the public round CSVs.`
   Official bundles include an `activitiesLog` that can imply a book path different from the public `prices_*.csv` files for the same nominal round/day.

2. `The portal uses a different within-tick matching model.`
   Public replay engines begin filling some passive inside-spread quotes earlier or more often than the portal does, especially in `INTARIAN_PEPPER_ROOT`.

3. `Many strategies are highly sensitive to passive inside-spread fills.`
   If the strategy depends on those fills for edge, local and official PnL can diverge hard even when the code is identical.

This means:

- a local replay can be directionally useful while still being numerically wrong
- portal mismatch is not automatically a wrapper bug
- “all / worse / none” trade-match settings help characterize the gap but do not eliminate it

## What We Fixed

We did not make OSS backtesters match the portal perfectly.

We did make the problem measurable:

- extract official portal windows into replayable local datasets
- rerun Kevin, Xeeshan, and Rust on that exact official window
- classify own fills relative to the displayed spread
- identify the first timestamp where local and official fills diverge

Relevant scripts:

- `scripts/extract_official_window.py`
- `scripts/analyze_fill_patterns.py`
- `scripts/compare_fill_sequences.py`
- `scripts/investigate-official.ps1`

Investigation outputs live under:

- `outputs/investigation/`

## How To Use The Toolchain Correctly

Use local tools to:

- eliminate obviously bad ideas
- inspect inventory and overtrading
- compare product-level PnL
- see whether an idea only works in one simulator
- understand where fills come from

Use the portal to:

- rank serious candidates
- validate any fill-sensitive strategy
- decide what is actually submission-worthy

Design preference:

- prefer strategies that are decent across `Rust`, `Kevin`, `Xeeshan`, and the portal
- distrust strategies that only work because one replay engine is generous on passive fills

The full operating rules for that process are in `workflow.md`.
