# Round 5 Current Checkpoint: Candidates 31-34

This is the active reset point for Round 5.

## Canonical Strategies

- `ROUND5/strategies/round5_candidate_31.py`: repaired 568114 official-lineage branch.
- `ROUND5/strategies/round5_candidate_32.py`: repaired candidate 30; strongest robust full-history base.
- `ROUND5/strategies/round5_candidate_33.py`: repaired candidate 29; best portal/full blend.
- `ROUND5/strategies/round5_candidate_34.py`: repaired 568593; highest portal-window score but full-history fragile.

## Canonical Scores

| Strategy | Portal Kevin | Portal Xeeshan | Full Kevin | Full Xeeshan | Max Portal State | Checkpoint Role |
|---|---:|---:|---:|---:|---:|---|
| `round5_candidate_31.py` | 87,593 | 87,633 | 95,145 | 95,404 | 13,951 | portal control / official-lineage benchmark |
| `round5_candidate_32.py` | 70,713 | 70,713 | 250,247 | 250,263 | 15,535 | robust base |
| `round5_candidate_33.py` | 85,930 | 85,930 | 244,734 | 244,750 | 23,777 | aggressive robust base |
| `round5_candidate_34.py` | 105,940 | 105,940 | -49,854 | -49,708 | 19,364 | portal exploit / idea mine |

## Current Decision

For official portal score only:

- Submit or test `round5_candidate_34.py` first.
- Then `round5_candidate_33.py`.
- Then `round5_candidate_31.py`.

For hidden-final robustness and next development:

- Start from `round5_candidate_32.py` and `round5_candidate_33.py`.
- Do not start from `round5_candidate_34.py` unless the candidate is explicitly portal-window/exploit-focused.

## Canonical Outputs

- `ROUND5/research/outputs/candidate_31_34_reset_review.md`
- `ROUND5/research/outputs/candidate_31_34_code_safety_review.md`
- `ROUND5/research/outputs/candidate_31_34_current_checkpoint.md`
- `ROUND5/research/outputs/candidate_31_34_portal_product_pnl.csv`
- `ROUND5/research/outputs/candidate_31_34_portal_category_pnl.csv`
- `ROUND5/research/outputs/candidate_31_34_reset/candidate_31_34_full_score_table.csv`

## Do Not Forget

- Uncapped broad-strategy replay is invalid unless capped replay matches.
- State repair fixed candidates 31-34 under the official 50k cap.
- Candidate 34 is the best portal-window strategy, but full-history negative.
- Candidate 32 and 33 are the real forward bases.
- Do not physically delete old logs or markdown; older files preserve the research trail.
