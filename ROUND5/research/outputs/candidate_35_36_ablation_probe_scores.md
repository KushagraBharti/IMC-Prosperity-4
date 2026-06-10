# Candidate 35-36 Ablation Probe Scores

| Probe | Portal Kevin | Max State | Note |
|---|---:|---:|---|
| `base33` | 85930.0 | 23777 | benchmark |
| `base34` | 105940.0 | 19364 | benchmark |
| `probe_33_robot_uv` | 84772.0 | 26053 | 33 + robot/UV amber |
| `probe_33_trans_sleep` | 91912.0 | 25535 | 33 + 34 signal branch |
| `probe_33_panel_micro` | 86974.0 | 24945 | 33 + panel2x4/micro triangle |
| `probe_33_all_targeted` | 91347.0 | 28978 | 33 + all targeted 34/31 additions |
| `probe_34_no_snack_uvmag` | 105546.0 | 17918 | 34 remove snack/uvmagenta extras |
| `probe_34_keep_lineage` | 103434.0 | 19364 | 34 keep only 31-lineage momentum extras |
| `probe_34_remove_toxic` | 85275.0 | 13951 | 34 remove likely full-toxic extras |
| `probe_34_no_anchor` | 101756.0 | 19364 | 34 without anchor engine |
