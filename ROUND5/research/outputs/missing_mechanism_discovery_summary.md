# Missing Mechanism Discovery Summary

This sprint searched for mechanisms rather than another candidate-35/36 product tweak.

## Best Mechanism Proxies

### Identity / Basket
| target           | category   | kind          | peers                                       | coefs   |   full_resid_std |   portal_resid_std |   full_reversion_proxy |   portal_reversion_proxy |   signal_count |   portal_signal_count |   day2_proxy |   day3_proxy |   day4_proxy |   stability_min_day |
|:-----------------|:-----------|:--------------|:--------------------------------------------|:--------|-----------------:|-------------------:|-----------------------:|-------------------------:|---------------:|----------------------:|-------------:|-------------:|-------------:|--------------------:|
| PEBBLES_XL       | PEBBLES    | small_int_dev | PEBBLES_M|MICROCHIP_CIRCLE                  | 3|-2    |          2730.6  |            2866.92 |                 712214 |                   453228 |           4145 |                  1714 |      44618.5 |     214368   |       453228 |             44618.5 |
| MICROCHIP_SQUARE | MICROCHIP  | small_int_dev | PEBBLES_XL|PEBBLES_M                        | 3|-2    |          4415.65 |            4727.02 |                 786482 |                   449352 |           3170 |                  2556 |     226740   |     110390   |       449352 |            110390   |
| PEBBLES_XL       | PEBBLES    | small_int_dev | PEBBLES_L|PEBBLES_M                         | 3|2     |          3138.77 |            3430.68 |                 697844 |                   444722 |           3326 |                  1292 |      86772   |     166350   |       444722 |             86772   |
| MICROCHIP_SQUARE | MICROCHIP  | small_int_dev | MICROCHIP_TRIANGLE|PEBBLES_XL               | 3|2     |          2636.73 |            2362.53 |                 612596 |                   424458 |           3480 |                  1550 |      20637   |     167500   |       424458 |             20637   |
| PEBBLES_XL       | PEBBLES    | small_int_dev | MICROCHIP_SQUARE|GALAXY_SOUNDS_SOLAR_FLAMES | 2|-3    |          3384.79 |            2966.23 |                 552772 |                   422842 |           4603 |                  2218 |      35933.5 |      93996   |       422842 |             35933.5 |
| MICROCHIP_SQUARE | MICROCHIP  | small_int_dev | MICROCHIP_OVAL|PEBBLES_XL                   | 3|2     |          4260.41 |            1874.26 |                 534032 |                   414209 |           3967 |                  1979 |      98107.5 |      21715   |       414209 |             21715   |
| PEBBLES_S        | PEBBLES    | small_int_dev | PEBBLES_XL|UV_VISOR_AMBER                   | -3|-3   |          3067.62 |            3775.18 |                 708834 |                   408949 |           3752 |                  2969 |     202128   |      97758   |       408949 |             97758   |
| MICROCHIP_SQUARE | MICROCHIP  | small_int_dev | MICROCHIP_TRIANGLE|PEBBLES_XL               | 2|3     |          3709.62 |            4066.14 |                 709254 |                   404426 |           4224 |                  2432 |     312904   |      -8076.5 |       404426 |             -8076.5 |
| PEBBLES_S        | PEBBLES    | small_int_dev | PEBBLES_L|ROBOT_MOPPING                     | -3|-2   |          2631.04 |            2966.77 |                 418883 |                   394413 |           4533 |                  2977 |       8577   |      15893   |       394413 |              8577   |
| MICROCHIP_OVAL   | MICROCHIP  | small_int_dev | MICROCHIP_TRIANGLE|PEBBLES_L                | 2|-3    |          1782.17 |            2039.79 |                 591527 |                   393086 |           4697 |                  3042 |     105768   |      92672.5 |       393086 |             92672.5 |

### Anchor
| product          | category   | anchor_type   |   anchor | side      |   horizon |   full_proxy |   portal_proxy |   avg_pnl |   hit_rate |   count |   portal_count |
|:-----------------|:-----------|:--------------|---------:|:----------|----------:|-------------:|---------------:|----------:|-----------:|--------:|---------------:|
| MICROCHIP_SQUARE | MICROCHIP  | round_250     |    14250 | sell_high |       100 |       325332 |         260965 |   35.6022 |     0.5491 |    9138 |           4630 |
| MICROCHIP_SQUARE | MICROCHIP  | round_250     |    14250 | two_sided |       100 |       709756 |         260226 |   33.716  |     0.5579 |   21051 |           4689 |
| MICROCHIP_SQUARE | MICROCHIP  | round_1000    |    14000 | two_sided |       100 |       562221 |         254448 |   23.8149 |     0.5401 |   23608 |           6333 |
| MICROCHIP_SQUARE | MICROCHIP  | round_1000    |    14000 | sell_high |       100 |       205478 |         254448 |   16.9691 |     0.5168 |   12109 |           6333 |
| MICROCHIP_SQUARE | MICROCHIP  | median        |    14291 | sell_high |       100 |       322073 |         252560 |   36.7705 |     0.5497 |    8759 |           4407 |
| MICROCHIP_SQUARE | MICROCHIP  | round_1       |    14291 | sell_high |       100 |       322073 |         252560 |   36.7705 |     0.5497 |    8759 |           4407 |
| MICROCHIP_SQUARE | MICROCHIP  | round_5       |    14290 | sell_high |       100 |       321946 |         252068 |   36.7225 |     0.5496 |    8767 |           4413 |
| MICROCHIP_SQUARE | MICROCHIP  | round_10      |    14290 | sell_high |       100 |       321946 |         252068 |   36.7225 |     0.5496 |    8767 |           4413 |
| MICROCHIP_SQUARE | MICROCHIP  | round_25      |    14300 | sell_high |       100 |       320001 |         249712 |   36.7648 |     0.5496 |    8704 |           4373 |
| MICROCHIP_SQUARE | MICROCHIP  | round_50      |    14300 | sell_high |       100 |       320001 |         249712 |   36.7648 |     0.5496 |    8704 |           4373 |

### Passive Fill
| product             | category     | style   | side   | gate        |   horizon |   avg_markout |   portal_avg_markout |   hit_rate |   portal_hit_rate |   count |   portal_count |   full_proxy |   portal_proxy |   avg_fill_target |
|:--------------------|:-------------|:--------|:-------|:------------|----------:|--------------:|---------------------:|-----------:|------------------:|--------:|---------------:|-------------:|---------------:|------------------:|
| PEBBLES_XL          | PEBBLES      | join    | bid    | all         |       100 |       28.9936 |              46.1331 |     0.5473 |            0.587  |   29700 |           9900 |       861108 |         456718 |             12.41 |
| PEBBLES_XL          | PEBBLES      | join    | bid    | imb_buy     |       100 |       28.9936 |              46.1331 |     0.5473 |            0.587  |   29700 |           9900 |       861108 |         456718 |             12.41 |
| PEBBLES_XL          | PEBBLES      | improve | bid    | all         |       100 |       27.9936 |              45.1331 |     0.546  |            0.5856 |   29700 |           9900 |       831408 |         446818 |             12.41 |
| PEBBLES_XL          | PEBBLES      | improve | bid    | imb_buy     |       100 |       27.9936 |              45.1331 |     0.546  |            0.5856 |   29700 |           9900 |       831408 |         446818 |             12.41 |
| MICROCHIP_SQUARE    | MICROCHIP    | join    | ask    | all         |       100 |       -5.1669 |              30.8761 |     0.4754 |            0.5182 |   29700 |           9900 |      -153456 |         305673 |             -5.96 |
| MICROCHIP_SQUARE    | MICROCHIP    | join    | ask    | spread_high |       100 |        7.4365 |              31.2483 |     0.4933 |            0.5181 |   18113 |           9626 |       134696 |         300796 |             -5.99 |
| MICROCHIP_SQUARE    | MICROCHIP    | improve | ask    | all         |       100 |       -6.1669 |              29.8761 |     0.4733 |            0.5162 |   29700 |           9900 |      -183156 |         295773 |             -5.96 |
| MICROCHIP_SQUARE    | MICROCHIP    | improve | ask    | spread_high |       100 |        6.4365 |              30.2483 |     0.4914 |            0.516  |   18113 |           9626 |       116584 |         291170 |             -5.99 |
| OXYGEN_SHAKE_GARLIC | OXYGEN_SHAKE | join    | bid    | all         |       100 |       20.5979 |              28.4881 |     0.5557 |            0.5791 |   29700 |           9900 |       611756 |         282032 |             18.25 |
| OXYGEN_SHAKE_GARLIC | OXYGEN_SHAKE | join    | bid    | imb_buy     |       100 |       20.5979 |              28.4881 |     0.5557 |            0.5791 |   29700 |           9900 |       611756 |         282032 |             18.25 |

### Lead-Lag
| lead                | lag              | lead_category   | lag_category   | same_category   |   lookback |   horizon |      ic |   abs_ic |   full_proxy |   portal_proxy |   count |   portal_count |
|:--------------------|:-----------------|:----------------|:---------------|:----------------|-----------:|----------:|--------:|---------:|-------------:|---------------:|--------:|---------------:|
| PEBBLES_M           | PEBBLES_XL       | PEBBLES         | PEBBLES        | True            |        100 |        50 | 0.07348 |  0.07348 |     391100   |         251782 |   29550 |           9850 |
| PEBBLES_L           | PEBBLES_XL       | PEBBLES         | PEBBLES        | True            |        100 |        50 | 0.03826 |  0.03826 |     364236   |         248919 |   29550 |           9850 |
| UV_VISOR_ORANGE     | PEBBLES_XL       | UV_VISOR        | PEBBLES        | False           |         50 |        50 | 0.0144  |  0.0144  |     164352   |         247165 |   29700 |           9900 |
| PEBBLES_L           | PEBBLES_XL       | PEBBLES         | PEBBLES        | True            |         50 |        50 | 0.01677 |  0.01677 |     141792   |         228309 |   29700 |           9900 |
| PEBBLES_M           | PEBBLES_XL       | PEBBLES         | PEBBLES        | True            |         50 |        50 | 0.06037 |  0.06037 |     222314   |         206339 |   29700 |           9900 |
| PEBBLES_XL          | PEBBLES_M        | PEBBLES         | PEBBLES        | True            |        200 |        50 | 0.10722 |  0.10722 |     344622   |         199384 |   29250 |           9750 |
| MICROCHIP_CIRCLE    | PEBBLES_XL       | MICROCHIP       | PEBBLES        | False           |         50 |        50 | 0.01627 |  0.01627 |      66630.5 |         189685 |   29700 |           9900 |
| UV_VISOR_AMBER      | MICROCHIP_SQUARE | UV_VISOR        | MICROCHIP      | False           |         50 |        50 | 0.0255  |  0.0255  |      72901   |         187002 |   29700 |           9900 |
| MICROCHIP_SQUARE    | PEBBLES_XL       | MICROCHIP       | PEBBLES        | False           |        100 |        50 | 0.06376 |  0.06376 |     409164   |         183838 |   29550 |           9850 |
| SNACKPACK_RASPBERRY | MICROCHIP_SQUARE | SNACKPACK       | MICROCHIP      | False           |        200 |        50 | 0.03042 |  0.03042 |     151220   |         182186 |   29250 |           9750 |

## Read

- These tables are oracle/proxy diagnostics, not submitted strategy scores.
- A mechanism is candidate-worthy only if portal proxy is strong, full proxy is not obviously toxic, counts are high, and the rule is online-computable.
- The next step is to convert the strongest rows into executable probes only if they plausibly add at least `10k` to the active branches.