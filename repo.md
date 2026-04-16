# Repo

This repo is the working research and execution workspace for `IMC Prosperity 4`.

## Top-Level Layout

- `TUTORIAL_ROUND/`
  Tutorial round data, official submission bundles, and the current tutorial strategy.
- `ROUND1/`
  Round 1 data, official submission bundles, research scripts, scratch strategies, and the current Round 1 strategy.
- `config/`
  Local config for paths, rounds, defaults, and tool integration.
- `scripts/`
  Thin wrappers around the external backtesters, visualizers, packaging flow, and comparison tools.
- `outputs/`
  Generated backtests, stress runs, investigation artifacts, submission-ready files, and visualizer handoff files.
- `notes/`
  Internal setup and workflow notes.
- `main.py`
  One-command runner for the integrated local workflow.

## Where To Work

- Edit the active tutorial strategy in `TUTORIAL_ROUND/strategies/current_trader.py`.
- Edit the active Round 1 strategy in `ROUND1/strategies/current_trader.py`.
- Keep experiments in round-local scratch folders like `ROUND1/scratch_alpha_01/`.
- Keep round-specific research code in `ROUND1/research/` and future `ROUND*/research/` folders.

## Official Submission Artifacts

Each official portal result is stored as a bundle containing:

- the submitted `.py`
- the portal `.log`
- the portal `.json`

Current examples:

- `ROUND1/official_submissions/167536/`
- `ROUND1/official_submissions/184591/`
- `ROUND1/official_submissions/214011/`

These are important because they are the closest thing to ground truth for what the portal actually evaluated.

## Tooling

External OSS tools live outside this repo under:

- `C:\Users\kushagra\OneDrive\Documents\CS Projects\prosperity-tools`

Current integrated tools:

- `xeeshan-backtester`
- `kevin-backtester`
- `rust-backtester`
- `kevin-visualizer`
- `gsgill7-visualizer`
- `chris-monte-carlo`

## Core Commands

Bootstrap local environments:

```powershell
.\scripts\bootstrap-tools.ps1
```

Run the integrated local flow:

```powershell
python main.py --round round1 --strategy ROUND1\scratch_alpha_01\trader.py
```

Run the replay engines individually:

```powershell
.\scripts\bt-xeeshan.ps1 round1
.\scripts\bt-kevin.ps1 round1
.\scripts\bt-rust.ps1 round1
```

Open the visualizers:

```powershell
.\scripts\viz-gsgill.ps1
.\scripts\viz-kevin.ps1
```

Package a candidate for submission:

```powershell
.\scripts\package-submission.ps1 round1 -Label candidate
```

Compare two runs or an official bundle versus a local run:

```powershell
.\scripts\compare-runs.ps1 ROUND1\official_submissions\184591 outputs\backtests\...
```

## Navigation Rules

- Treat `ROUND*/official_submissions/` as reference artifacts, not active code.
- Treat `ROUND*/strategies/current_trader.py` as the active editable strategy for that round.
- Treat `outputs/` as generated files. Read from it freely, but do not hand-edit generated artifacts.
- Use `strategies.md` as the running registry of what each strategy is trying to do.
- Use `prosperity.md` as the competition reference, not Discord memory.

## Practical Workflow

1. Start from the active round strategy.
2. Make a small change.
3. Run Xeeshan, Kevin, and Rust locally.
4. Compare the runs, especially product split, trade count, and inventory behavior.
5. Use the portal as the real judge for serious candidates.
6. Archive the winning strategy before the next major change.
