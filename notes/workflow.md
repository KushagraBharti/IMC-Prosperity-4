# Daily Workflow

Default loop:

```powershell
.\scripts\bt-xeeshan.ps1 round1 0
.\scripts\bt-kevin.ps1 round1 0
.\scripts\viz-gsgill.ps1
```

Typical research loop:

1. Edit the active strategy for the target round.
   - Round 1 implementation: `ROUND1\strategies\current_trader.py`
   - Tutorial implementation: `TUTORIAL_ROUND\strategies\current_trader.py`
2. Run Xeeshan first for the fast official-output-like replay.
3. Run Kevin as the architecture cross-check.
4. Compare the two replay outputs or compare against official bundles.
5. Open the latest log in a visualizer.
6. When a tutorial strategy looks stable, run Monte Carlo:

```powershell
.\scripts\stress-chris.ps1 tutorial
```

Submission packaging:

```powershell
.\scripts\package-submission.ps1 round1 -Label baseline
```

Useful notes:

- Wrappers mirror the flat CSV files into tool-specific data directories automatically. The original round folders stay untouched.
- The latest replay log is always copied to `outputs\visualizer-inbox\latest.log`.
- The latest run metadata is written to `outputs\visualizer-inbox\latest-run.json`.
