# Battle 4 — Battle of Eilhart calibration analysis (v0.1K)

## Evidence result

The preserved replay is now a high-value **Tier 4R observed-trace calibration corpus**. It is not treated as an optimal-policy demonstration. The source proves a completed 739.6-second Reikland victory with 397 observed command events. Reconciliation reduces 50 raw static identities to 34 canonical units and preserves 16 hierarchy aliases as a regression fixture.

Reliable outcome anchors are deliberately conservative:

- Reikland casualties: at least **489**;
- visible-enemy casualties: at least **1096**;
- local observed kills max-sum: **1141**;
- local terminal coverage: **64.7%**;
- visible-enemy terminal coverage: **88.2%**.

Exact casualty totals are withheld because terminal coverage was incomplete.

## Sparse-sampling defect preserved

The source declared a 3-second detail interval and would have produced roughly 247 samples. It emitted only 5 phase-bound samples, with a largest gap of 601.9 seconds. Therefore engagement timing, routing timing, idle ratios, fatigue progression, reserve commitment, path length, target switching, and flank timing are `INVALIDATED_BY_SPARSE_SAMPLING`. Terminal outcomes, commands, phases, deployment changes, and lower bounds remain usable.

## Command trace

- Attack Unit: 150
- Move: 127
- Double Click: 86
- Move Orientation Width: 19
- Special Ability: 15
- Median command interval: 300 ms
- 90th-percentile interval: 5000 ms
- Direct selection attribution: 0.0%

The zero direct-attribution result is a known instrumentation defect. v0.1K registers the documented callback once per local player-controlled unit and preserves a separately labeled bounded inference fallback.

## Representative local outcomes

| Unit | Role | Kills | Casualty lower bound | Ammo lower bound | Last HP | Terminal |
|---|---|---:|---:|---:|---:|---|
| `wh3_dlc25_emp_cha_master_engineer` | commander | 212 | 0 | 15 | 79.9% | no |
| `wh_main_emp_inf_handgunners` | ranged | 141 | 23 | 1309 | 57.3% | yes |
| `wh3_dlc25_emp_cha_master_engineer` | commander | 102 | 0 | 14 | 80.9% | no |
| `wh_main_emp_inf_handgunners` | ranged | 98 | 13 | 959 | 56.4% | yes |
| `wh2_dlc13_emp_inf_archers_0` | ranged | 94 | 61 | 1406 | 13.3% | yes |
| `wh_main_emp_cha_wizard_fire_0` | commander | 86 | 0 | 0 | 13.1% | yes |
| `wh_main_emp_inf_swordsmen` | frontline | 81 | 92 | 0 | 18.3% | yes |
| `wh_main_emp_cha_karl_franz_0` | commander | 74 | 0 | 0 | 16.0% | yes |
| `wh_main_emp_inf_halberdiers` | frontline | 65 | 105 | 0 | 4.6% | yes |
| `wh2_dlc13_emp_inf_archers_0` | ranged | 61 | 47 | 1263 | 26.7% | yes |

## SyntheticLab Tier 4R framework

The public corpus contains source digests and derived state only—no replay binary, raw log, personal path, or Creative Assembly asset. It now drives deterministic reality regressions for:

- stable identity and hierarchy churn;
- hidden-enemy boundaries;
- sampling sufficiency;
- exact-versus-lower-bound casualty semantics;
- selection and inference labeling;
- endangered commanders: `1:u1001`;
- collapsed frontline: `1:u1003`, `1:u1004`, `1:u1005`;
- high-output ranged/specialists;
- routed visible enemies;
- units missing a terminal observation.

All ten Tier 4R regression checks pass deterministically.

## Additional data prepared for the dense replay pass

The dedicated replay probe adds far more than the first capture:

- one-second alliance battle curves for men, kills, ammunition, strategic value, melee, routing, wavering, idle, movement, missile pressure, and flank exposure;
- three-second per-unit trajectories, ordered trajectories, state durations, fatigue durations, target switches, target distance/range, and threat-source identity;
- army/faction/subculture context and reinforcement counts;
- unique-UI stable identity plus hierarchy-change records;
- per-unit selection callbacks and selected-unit command attribution;
- command burst, target concentration, ability timeline, and bounded state-change attribution;
- sampler start, dual-clock ticks, heartbeats, callback failures, maximum gap, and coverage sufficiency;
- terminal-state coverage and exact/lower-bound outcome labeling.

The source remains read-only: no unitcontroller, order, speed, save, damage, healing, ammunition, visibility, or randomness authority exists.

## Frozen digests

- Reconciled report: `1f151473c0530a43f768ea2c3c01ae2df1faa397d79de5e1d6a001daef8352cb`
- Tier 4R corpus: `24af79128738bc648504094784eaced4d872ca05bf680c0e5f16061eac47da8d`
- Tier 4R regression: `0d93daf622e65e1bdf498c9a8526c2d34a79c93bbd29099a0d2c31c6ce149e02`
- Analysis: `ff77f7792b005bb4b2e7ad242618e4fe578fec3c24555c951ee062bda67f4bff`

## Remaining live condition

Play the same preserved replay once with the v0.1K dedicated battle-only pack. The dense verifier must observe schema 2, callback heartbeats, bounded sample gaps, stable identities without aliases, local and visible-enemy units, a complete result, and read-only authority. Direct selection attribution may close as `OBSERVED_DENSE` or be preserved honestly as `OBSERVED_DENSE_SELECTION_LIMITING_RESULT`. No manual refight is required.
