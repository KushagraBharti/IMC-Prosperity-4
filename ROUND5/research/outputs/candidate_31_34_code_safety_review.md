# Candidate 31-34 Code Safety And Overfit Review

Scope: static review plus current score evidence. This file focuses on platform safety, illegal-hardcoding risk, and overfit risk.

## Static Safety Table

| Strategy | Compiles | Imports | Local Reads | Eval/Exec | Network/Subprocess | Randomness | Timestamp Trading | State Safe | Verdict |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| `round5_candidate_31.py` | yes | safe | false | false | false | false | false | yes | platform-safe |
| `round5_candidate_32.py` | yes | safe | false | false | false | false | false | yes | platform-safe |
| `round5_candidate_33.py` | yes | safe | false | false | false | false | false | yes | platform-safe |
| `round5_candidate_34.py` | yes | safe | false | false | false | false | false | yes | platform-safe |

Safe imports observed:

- `json`
- `math`
- `dataclasses`
- `typing`
- `datamodel` or fallback local dataclasses

No evidence found of:

- local file reads,
- official log parsing,
- external subprocess/network calls,
- `pandas`, `numpy`, `sklearn`, `statsmodels`, or heavy research dependencies,
- `eval` / `exec`,
- runtime randomness,
- exact timestamp branching,
- future data access.

## Hardcoding / Overfit Matrix

| Strategy | Illegal Hardcoding Risk | Competition Hardcoding Level | Overfit Risk | Evidence |
|---|---|---|---|---|
| `round5_candidate_31.py` | low | medium | medium | fixed product lists, fixed `ANCHOR = 10000`, official lineage, full positive but day2/day3 negative |
| `round5_candidate_32.py` | low | low-medium | medium-low | no anchor engine, cleaner product table, best full-history score and positive all visible days |
| `round5_candidate_33.py` | low | medium | medium-high | broad signal table, strong portal and full, positive all visible days but more moving parts |
| `round5_candidate_34.py` | low | medium-high | high | highest portal score, broadest extras, fixed anchor, negative full history |

## Important Distinction

These strategies do not appear illegally hardcoded.

The risk is competition overfit:

- product-specific inclusion lists,
- product-specific lookbacks,
- thresholds and weights,
- active signal caps,
- fixed `ANCHOR = 10000` in 31/34,
- portal-window-positive but full-history-toxic branches.

## State Safety

The state repair is successful for portal-window replay:

| Strategy | Portal Max State | Official 50k Cap Margin |
|---|---:|---:|
| `round5_candidate_31.py` | 13,951 | strong |
| `round5_candidate_32.py` | 15,535 | strong |
| `round5_candidate_33.py` | 23,777 | strong |
| `round5_candidate_34.py` | 19,364 | strong |

The old official mismatch was caused by `traderData` truncation. Candidates 31-34 avoid that failure mode.

## Safety Conclusion

Platform safety is not the blocker.

The blocker is choosing the right risk profile:

- `round5_candidate_34.py` is a high-upside portal-window branch with high overfit risk.
- `round5_candidate_32.py` is the safest robust base.
- `round5_candidate_33.py` is the best compromise between official upside and full-history robustness.
- `round5_candidate_31.py` is a useful official-lineage control, but not the strongest base.
