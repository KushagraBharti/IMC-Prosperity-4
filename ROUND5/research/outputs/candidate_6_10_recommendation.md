# Candidate 6-10 Recommendation

Score priority is split between hidden robustness and official-window upside:

1. Submit `round5_candidate_9.py` if the goal is maximum near-term upside. It has the best portal-window replay: Kevin 8302, Xeeshan 8267. Risk: full-history loss of about -70.9k.
2. Submit `round5_candidate_6.py` as the cleanest robust aggressive branch. It is positive full-history and positive portal-window, while still using full-limit `PEBBLES_XL` risk.
3. Submit `round5_candidate_7.py` if willing to test the `PEBBLES_L` overlay. It has strong portal replay but weaker robustness.
4. Submit `round5_candidate_10.py` as a stricter `PEBBLES_XL` alternative to Candidate 6.
5. Submit `round5_candidate_8.py` only if we want a structurally distinct ROBOT-only official-window test.

Across Candidates 1-10, the best next portal tests are `round5_candidate_9.py`, `round5_candidate_6.py`, `round5_candidate_7.py`, `round5_candidate_10.py`, and `round5_candidate_8.py`. If limiting submissions, prioritize 9, 6, and 7.

Do not promote yet. Wait for official portal results, then compare score plus product-level execution behavior before selecting iterative branches.
