# Candidate 31-34 State Repair Notes

## State Repair Result

Candidates 31-34 use compact deterministic state serialization and stay safely below the official portal `traderData` cap on portal-window replay.

| Strategy | Base | Portal Kevin | Portal Xeeshan | Portal Kevin 50k Cap | Portal Xeeshan 50k Cap | Max State | Safe |
|---|---|---:|---:|---:|---:|---:|---|
| `round5_candidate_31.py` | `568114.py` | 87,593 | 87,633 | 87,593 | 87,633 | 13,951 | yes |
| `round5_candidate_32.py` | `round5_candidate_30.py` | 70,713 | 70,713 | 70,713 | 70,713 | 15,535 | yes |
| `round5_candidate_33.py` | `round5_candidate_29.py` | 85,930 | 85,930 | 85,930 | 85,930 | 23,777 | yes |
| `round5_candidate_34.py` | `568593.py` | 105,940 | 105,940 | 105,940 | 105,940 | 19,364 | yes |

## 568593 Diagnosis

- Raw official submission max state: `73,832`.
- Raw uncapped local portal replay: `105,940`.
- Raw forced-50k local portal replay: `41,486`.
- Official portal score: `41,485.68`.
- Verdict: raw `568593.py` failed because the portal truncated `traderData`; `round5_candidate_34.py` fixes that state bug.

## Full-History Correction

The state repair is valid, but portal-window score is not the same as hidden-final robustness.

Full repaired scores:

| Strategy | Full Kevin | Full Xeeshan | Robustness Read |
|---|---:|---:|---|
| `round5_candidate_31.py` | 95,145 | 95,404 | positive but day2/day3 fragile |
| `round5_candidate_32.py` | 250,247 | 250,263 | best robust base |
| `round5_candidate_33.py` | 244,734 | 244,750 | best portal/full blend |
| `round5_candidate_34.py` | -49,854 | -49,708 | portal exploit, full-history fragile |

Submit priority for immediate portal-window score can still start with `round5_candidate_34.py`.

Development priority should start with `round5_candidate_32.py` and `round5_candidate_33.py`.
