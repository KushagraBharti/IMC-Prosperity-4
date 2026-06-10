# Candidate 26-30 Official Mismatch Diagnosis

## Verdict

The mismatch is caused by the official portal's `traderData` 50,000-character cap. Candidates 28-30 store long per-product history arrays in JSON. Kevin/Xeeshan local portal replay did not enforce the cap, so it scored strategies using state that the official portal truncates.

When local replay is rerun with `traderData[:50000]` enforced, the scores match the official portal almost exactly.

| Strategy | Original Local Portal | Official Portal | Local With 50k `traderData` Cap |
|---|---:|---:|---:|
| `round5_candidate_28.py` | 45,395 | 40,362.72 | 40,372 |
| `round5_candidate_29.py` | 85,930 | 32,916.06 | 32,921 |
| `round5_candidate_30.py` | 70,713 | 48,950.08 | 48,960 |

## Evidence

- Submitted code matches local strategy files after whitespace normalization.
- Official market data values match local portal-window data by `(day, timestamp, product)`.
- Replaying against the official submission row order still gives the inflated local scores, so row order is not the cause.
- The official `.json` files do not contain `tradeHistory`, but the official `.log` files do. Official fill counts confirm fewer fills than local when the cap is ignored.
- Enforcing a 50k local `traderData` cap reproduces official PnL.

## State Size

| Strategy | First Timestamp Above 50k | Max Local `traderData` Length | Result |
|---|---:|---:|---|
| `round5_candidate_28.py` | 57,800 | 53,234 | Mild official mismatch |
| `round5_candidate_29.py` | 20,600 | 130,164 | Severe official mismatch |
| `round5_candidate_30.py` | 30,600 | 90,766 | Moderate official mismatch |

The broad candidates cache hundreds of float mid-price values per product. Candidate 29 tracks 24 signal products plus PEBBLES residuals, which makes the returned JSON state far above the official limit.

## Mechanism

The candidate code returns:

```python
return result, 0, json.dumps(cache, separators=(",", ":"))
```

The official container cuts this string to 50,000 characters. That usually creates invalid JSON. The strategy then does:

```python
try:
    return json.loads(raw) if raw else {}
except Exception:
    return {}
```

So once the cap is crossed, the cache resets. Long-horizon signals lose their history and stop firing correctly. Local Kevin/Xeeshan replay preserved the oversized JSON, so it credited many signals/fills that the portal could not reproduce.

## Fill Evidence

| Strategy | Local Submission Trades | Official Submission Trades | Interpretation |
|---|---:|---:|---|
| `round5_candidate_28.py` | 91 | 81 | Slight loss of late/stateful signal behavior |
| `round5_candidate_29.py` | 164 | 45 | Most broad non-PEBBLES engines stop firing after state truncation |
| `round5_candidate_30.py` | 120 | 96 | Some broad engines survive, but several lose fills |

Candidate 29 official final PnL has many local-positive products at exactly zero because their histories were reset before their long-horizon signals matured.

## Not The Cause

- Not wrong file upload.
- Not different market window.
- Not product row ordering.
- Not Kevin vs Xeeshan disagreement.
- Not an official runtime exception.
- Not Rust/full-backtest relevance.

## Required Fix

Future candidates must be designed under an explicit state budget. Target less than 40,000 characters, not just less than 50,000.

Repair options:

- Replace raw history arrays with compact rolling stats where possible.
- Store integer deltas or quantized values instead of full float mid prices.
- Store only the exact lookbacks needed, with tighter per-product caps.
- Use short cache keys.
- Add a deterministic cache eviction/compression step before returning `traderData`.
- Add a local scoring mode that enforces `traderData[:50000]` before every next call.
- Treat uncapped portal-window results as invalid for broad multi-engine candidates.

## Next Step

Build repaired candidates from 29/30 architecture with compact state, then rerun portal-window replay with the 50k cap enforced. Candidate 30 is the better repair base than candidate 29 because it still scored about 48.95k officially despite truncation.
