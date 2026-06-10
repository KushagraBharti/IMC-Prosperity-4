# Candidate 37-44 Design Notes

Created eight candidates from the strongest validated Round 5 branches. No new research dependencies, no local file reads, and portal cap checks stayed below 50k for all files.

## round5_candidate_37.py
Max portal handwritten integration: fresh breadth + robot extras + MICROCHIP_SQUARE anchor overlay.
Portal Kevin/Xeeshan: 123425 / 123435; Full Kevin/Xeeshan: 158838 / 158515; max state 32325.

## round5_candidate_38.py
Ablation of 37 without MICROCHIP_SQUARE anchor overlay; tests whether anchor is real.
Portal Kevin/Xeeshan: 122897 / 122907; Full Kevin/Xeeshan: 108699 / 108376; max state 32325.

## round5_candidate_39.py
Balanced broad fresh-category branch without robot pair/anchor overlay; stronger full than 37.
Portal Kevin/Xeeshan: 121436 / 121446; Full Kevin/Xeeshan: 254379 / 254543; max state 31170.

## round5_candidate_40.py
Robot-pair portal branch; tests aggressive ROBOT_DISHES/MOPPING contribution.
Portal Kevin/Xeeshan: 121620 / 121630; Full Kevin/Xeeshan: 114755 / 114557; max state 31108.

## round5_candidate_41.py
Robust-full baseline: candidate-35 conservative anchor/micro/UV branch.
Portal Kevin/Xeeshan: 111868 / 111868; Full Kevin/Xeeshan: 379278 / 379319; max state 29953.

## round5_candidate_42.py
Robust-full plus panel/micro-anchor branch; best full-history candidate in this batch.
Portal Kevin/Xeeshan: 113412 / 113412; Full Kevin/Xeeshan: 421524 / 421564; max state 29953.

## round5_candidate_43.py
Conservative snackpack/micro/UV branch; robust-full alternative.
Portal Kevin/Xeeshan: 111490 / 111500; Full Kevin/Xeeshan: 379776 / 379726; max state 29953.

## round5_candidate_44.py
Very-tight robot portal branch; safer robot-heavy ablation than 40.
Portal Kevin/Xeeshan: 121466 / 121476; Full Kevin/Xeeshan: 120960 / 120694; max state 30523.
