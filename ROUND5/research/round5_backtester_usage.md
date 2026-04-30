# Round 5 Backtester Harness

Canonical runner:

```powershell
python ROUND5/research/round5_backtester.py <strategies...> [options]
```

This replaces the one-off candidate scoring scripts for normal Round 5 validation.

## Fast Portal Validation

```powershell
python ROUND5/research/round5_backtester.py round5_candidate_35.py round5_candidate_36.py --tools kevin xeeshan --suites portal --cap-check --jobs 6 --name c35_36_portal
```

Outputs:

- `summary.md`
- `summary.csv`
- `summary.json`
- `state_size.csv`
- `product_pnl.csv`
- `category_pnl.csv`
- `block_pnl.csv`
- portal JSON logs and stdout files

## Fast Full Scores

```powershell
python ROUND5/research/round5_backtester.py round5_candidate_35.py round5_candidate_36.py --tools kevin xeeshan --suites full --jobs 4 --state none --name c35_36_full_scores
```

Full runs use `--no-out` by default, so they do not write 100MB+ JSON logs. This is the preferred path for score-only validation.

## Portal + Full In One Run

```powershell
python ROUND5/research/round5_backtester.py round5_candidate_35.py round5_candidate_36.py --tools kevin xeeshan --suites portal full --cap-check --jobs 6 --name c35_36_all
```

Portal runs save JSON logs for attribution. Full runs stay score-only unless `--full-logs` is passed.

## Full JSON Logs For Finalist Attribution

```powershell
python ROUND5/research/round5_backtester.py round5_candidate_35.py --tools kevin --suites full --full-logs --jobs 1 --name c35_full_attribution
```

Use this only when product-level full-history attribution is needed. Full JSON logs are large and slower.

## CPU Guidance

- Start with `--jobs 4` for full runs.
- Use `--jobs 6` to `--jobs 8` for portal-heavy batches.
- Higher jobs can be tested on the i7-13700, but watch CPU temperature and UI responsiveness.
- Avoid writing full JSON logs in parallel unless absolutely needed.

## Useful Options

- `--cap-check`: also runs forced-50k `traderData` variants.
- `--cap-suites portal full`: cap-check full too, if needed.
- `--state portal`: measure max `traderData` on the official portal window.
- `--state full`: measure max `traderData` across all local full-history price files; slower.
- `--reuse`: reuse outputs in the same run directory.
- `--dry-run`: print planned tasks without running backtests.
- `--no-portal-logs`: skip portal JSON logs if only score is needed.
- `--full-logs`: write full JSON logs; expensive.
