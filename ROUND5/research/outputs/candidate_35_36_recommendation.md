# Candidate 35-36 Recommendation

| Strategy | Portal Kevin | Full Kevin | Role | Recommendation |
|---|---:|---:|---|---|
| `round5_candidate_35.py` | 91912 | 287444 | robust alpha composite | submit first / next robust development base |
| `round5_candidate_36.py` | 105546 | 36673 | cleaned portal-upside strategy | submit as portal-upside probe, not robust base |

## Read
- `round5_candidate_35.py` is the best result of this phase: it beats candidate 33 portal (`91.9k` vs `85.9k`) and beats candidate 32/33 full history (`287.4k` vs `250.2k`/`244.7k`).
- `round5_candidate_36.py` nearly preserves candidate 34 portal (`105.5k` vs `105.9k`) and fixes the sign of full history (`36.7k` vs `-49.9k`), but it remains far weaker than 32/33/35 on full robustness.
- Best official submission order depends on objective: submit `36` first for raw portal upside; submit `35` first if we want the strongest score/robustness blend.
- Next development base should be `round5_candidate_35.py`, not 36. Candidate 36 is an idea mine and portal-upside branch.
- Neither candidate beats candidate 34 portal, but candidate 35 beats every current full-history score and is the best robust branch so far.
