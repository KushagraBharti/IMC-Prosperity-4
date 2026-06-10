# Candidate 31-34 State Repair Notes

## Repair Method
- Trading logic is preserved: product lists, thresholds, formulas, ranking, sizing, and execution rules are copied from the base files.
- Only `traderData` serialization/deserialization is changed.
- Histories are still exposed to the trading code as normal float lists after load.
- Returned state uses short product/prefix aliases, delta-encoded integer arrays, and deterministic trimming to the longest window actually read by the formulas.
- Mid-price histories are stored at half-tick precision (`scale=2`), which is exact for top-of-book mids in this data.
- PEBBLES residual histories use `scale=1000`; category residual histories use `scale=100`.

## round5_candidate_31.py
- Base: `C:/Users/kushagra/OneDrive/Documents/CS Projects/IMC Trading Comp/ROUND5/official_submissions/568114/568114.py`.
- Behavior change: intended none beyond sub-cent residual quantization needed for compact state.
- Official safety target: returned `traderData` below 45,000 characters; never relies on portal truncation.

## round5_candidate_32.py
- Base: `C:/Users/kushagra/OneDrive/Documents/CS Projects/IMC Trading Comp/ROUND5/strategies/round5_candidate_30.py`.
- Behavior change: intended none beyond sub-cent residual quantization needed for compact state.
- Official safety target: returned `traderData` below 45,000 characters; never relies on portal truncation.

## round5_candidate_33.py
- Base: `C:/Users/kushagra/OneDrive/Documents/CS Projects/IMC Trading Comp/ROUND5/strategies/round5_candidate_29.py`.
- Behavior change: intended none beyond sub-cent residual quantization needed for compact state.
- Official safety target: returned `traderData` below 45,000 characters; never relies on portal truncation.

## round5_candidate_34.py
- Base: `C:/Users/kushagra/OneDrive/Documents/CS Projects/IMC Trading Comp/ROUND5/official_submissions/568593/568593.py`.
- Behavior change: intended none beyond sub-cent residual quantization needed for compact state.
- Official safety target: returned `traderData` below 45,000 characters; never relies on portal truncation.
