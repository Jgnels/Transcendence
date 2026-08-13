# Campaign Turns 4–7 Reprocessing — v0.1J

**Evidence label:** `LIMITING_RESULT` for the original live gate; `SUPPORTED_OFFLINE` for the corrected adapter behavior.

## Frozen inputs

- Owner combined-session campaign log SHA-256: `b5a2dd1db21eaff3cd3d02d457ee34f69a89deab28a362461135d52bef323e51`
- Original v0.1I-r2 campaign report SHA-256: `35e71ad612e13374b052233c80794ae7d3bb46887f2e0dedfc35c9bad701775d`
- Corrected v0.1J report file SHA-256: `8189081fb1b4ad57fb09592f5c9594480b42cf3f575d76eed94014cec7dc37a5`
- Corrected v0.1J result digest: `953e35299dd0ef9e06de9d5347df01cabbd79cce68727e8b7a12175a058bc03b`
- Profile: `vanilla_wh3_8_1_1_build_48122_4194776`
- Random seed: none.

The private raw log is not committed. This file and the adjacent JSON are derived, public-safe evidence.

## Defects exposed by the live input

1. Two one-unit Master Engineer character forces were treated as field armies and received objectives.
2. Controlled forces used WH3 exact force-strength values in the millions while visible foreign forces used `unit_count × 10`, creating meaningless ratios such as `14537.34`.
3. A field army occupying a settlement was treated as the settlement garrison, causing the field army's exact strength to be double counted.
4. The previous collector relied on `lua_mod_log.txt`, which WH3's mod logger opens with truncation semantics at the beginning of each Lua runtime. Campaign-to-battle-to-campaign transitions therefore did not produce one durable combined transcript.

## Narrow corrections

- New live records explicitly distinguish real armies from embedded character forces using `military_force:is_army()` plus `character:character_type_key()`.
- Legacy logs use a conservative one-unit nonfield heuristic only for reprocessing; new live evidence carries explicit eligibility.
- Own and foreign feasibility now use the same unit-count scale. Exact own strength remains telemetry and is excluded from cross-faction scoring.
- Only armed-citizenry forces may contribute a garrison-unit proxy. A field army in a residence is excluded and the settlement-structure proxy is used.
- Campaign and battle scripts append structured records to `transcendence_runtime_log.txt`, while `ModLog` remains a secondary diagnostic sink.

## Before and after

| Metric | Original v0.1I-r2 | Corrected v0.1J |
|---|---:|---:|
| Controlled objective recipients per turn | 3 | 1 |
| Total assignments, turns 4–7 | 12 | 4 |
| Master Engineer character forces assigned | 2 per turn | 0 |
| Maximum reported attack ratio | 14537.34 | 1.65 |
| Field-army strength used as garrison | yes | no |
| Objective changes | 3 | 1 |
| HOLD assignments | 9 | 3 |

The corrected turn-7 proposal targets a visible Marienburg army with estimated ratio `1.65`, rather than a five-digit ratio. This is still an uncalibrated shadow hypothesis and no order was attempted.

## Remaining limitation

The available owner evidence contains canonical campaign snapshots only for turns 4–7 and no live `TRANS_BATTLE` records. The owner's report that turns 1–3 and multiple manually fought battles contained the most valuable experience is accepted as owner testimony, not telemetry. Those segments must not be reconstructed from fixtures or historical observer logs.
