# Native Behavior Study Causal Review — v0.2O

Date: 2026-08-03

Status: **v0.2N confirmatory result ingested; no native-row ablation earned yet.**

## Source integrity

Owner bundle: `Transcendence_NativeBehaviorStudy_VANILLA_20260803T072222Z.zip`

SHA-256: `9416e0b73765570e6ffda1c1855a0430133b447e14cd63d307c966312987429d`

The ZIP passes integrity validation. All five payload files match the hashes and sizes in `export_manifest.json`. Re-running the sealed v0.2N evaluator against the raw trace reproduces the included result exactly at the semantic JSON level.

v0.2N result digest: `ebe747ca69a8b7da86586a7ea6759d65e2f81f5128cf45917fd9c41c495a8542`

Frozen threshold digest: `4499a497bfc7dd6a33a6c0a50da4e1e52b1705d1f2f20f1a917cdfebeb5486ac`

## Confirmatory integrity

- Reikland turn-start markers: 1 through 12.
- Required minimum: 11.
- Paired AI faction turns: 2,649.
- Complete pending-battle sequences: 615.
- Incomplete battle sequences: 0.
- Incomplete normal AI faction turns: 0.
- Capability failures: 0.
- Profile/hash binding unchanged: yes.
- `battle_participant_telemetry=true`: yes.
- `NO_ORDERS`, application authority `PROHIBITED`, privileged diagnostic data application-ineligible.

The cohort is confirmatory-eligible under the frozen v0.2N protocol.

## Recovery endpoint

Frozen result: **NO_PREREGISTERED_RECOVERY_SIGNAL_IN_COHORT**.

- damaged army-turn exposures below 65% average unit health: 38;
- attacker-side re-entry army-turns: 6;
- attacker-side re-entry rate: 15.7895%;
- frozen signal threshold: at least 10 exposures, at least 2 attacker-side reentries, and rate >=20%;
- attacker-side pending-battle sequences associated with the six candidate army-turns: 10.

Exposure is sufficient. The observed rate is below the frozen threshold. This is a cohort-limited negative result, not proof that native recovery policy is generally adequate.

## Temporal endpoint

Frozen v0.2N result: **REPEATED_BATTLE_FREE_REVERSAL_SIGNAL_OBSERVED**.

- eligible battle-free stable-context directional windows: 106;
- single-window heading-reversal candidates: 18;
- repeated non-overlapping reversal forces: 1;
- exact region A-B-A-B-A signals: 0.

The only force satisfying the frozen repeated non-overlap rule was:

- faction `wh2_dlc11_cst_rogue_grey_point_scuttlers`;
- force CQI `922`;
- selected windows turns 2-4 and 8-10;
- no owned regions;
- no wars;
- full-strength 18-unit army with unchanged health, strength, stance and composition through the observed track;
- campaign-map region field remained `none` throughout.

Observed positions for force 922 at turn-end:

| Turn | X | Y |
| ---: | ---: | ---: |
| 1 | 388 | 523 |
| 2 | 375 | 547 |
| 3 | 379 | 573 |
| 4 | 371 | 549 |
| 5 | 345 | 536 |
| 6 | 328 | 524 |
| 7 | 348 | 508 |
| 8 | 350 | 478 |
| 9 | 350 | 461 |
| 10 | 367 | 484 |
| 11 | 395 | 498 |

The two selected reversal angles are approximately 170.3° and 143.5°.

## Causal adjudication

The repeated trigger is **not representative evidence of ordinary territorial CAI task thrashing**.

Verified owner-trace facts:

- faction key is explicitly a `cst_rogue` faction;
- it owns no regions in the relevant windows;
- it has no wars in the relevant windows;
- its army remains at full health and constant strength/composition;
- it moves at sea and does not enter a campaign region.

External corroboration is lower-grade community evidence, not an official CA statement:

- Total War: WARHAMMER community documentation classifies Grey Point Scuttlers as a Rogue Pirate faction and describes it as remaining at sea while patrolling a specific route: https://totalwarwarhammer.fandom.com/wiki/Grey_Point_Scuttlers
- the broader Rogue Armies documentation groups Grey Point Scuttlers with Rogue Pirates/patrol armies: https://totalwarwarhammer.fandom.com/wiki/Rogue_Armies

Evidence classification for the fixed-route explanation: **MODDER_COMMUNITY_CLAIM + strong consistency with VERIFIED owner telemetry**.

Therefore the v0.2N endpoint correctly detected repeated heading reversal, but a fixed patrol-route geometry is a plausible intended-behavior explanation. The signal does **not** establish missing native assignment memory/hysteresis and does **not** earn a native-row intervention by itself.

## Retrospective population stratification

For causal review only, the 106 eligible windows were split by an objective observable rule:

- **territorial:** stable owned-region set is non-empty throughout the window;
- **non-territorial:** stable owned-region set is empty throughout the window.

Results:

| Population | Eligible | Reversal candidates | Candidate rate | Repeated forces |
| --- | ---: | ---: | ---: | ---: |
| Territorial | 48 | 13 | 27.0833% | 0 |
| Non-territorial | 58 | 5 | 8.6207% | 1 |

This split was chosen **after** seeing the vanilla result. It is not a fresh confirmatory subgroup analysis. It is frozen only as the reference definition for the next prospective SFO benchmark.

The territorial cohort contains multiple single/overlapping A-B-A observations, but none met the frozen v0.2N requirement for two non-overlapping reversal episodes and no exact A-B-A-B-A signal occurred. Those observations remain candidates for future study, not a defect verdict.

## Architecture decision

`NATIVE_PRIMARY_DECISION_STRENGTHENED — NO APPLICATION AUTHORITY CHANGE`

- Recovery: sufficient exposure, no preregistered signal.
- Temporal: formal signal observed, but causal review identifies a special patrol-policy explanation for the sole repeated trigger.
- No ordinary territorial repeated signal was established.
- No native-row ablation is authorized from v0.2N alone.
- v0.2G/v0.2I remain outside the default application path.

## Next gate

Run a prospective matched **SFO** cohort using the same read-only diagnostic probe and the same v0.2N recovery/temporal thresholds. The primary strategic temporal population is prospectively frozen as **territorial faction windows**; non-territorial windows remain a separately reported secondary population.

The vanilla stratified values above are a hash-frozen reference, not a randomized causal baseline. Any SFO difference is a benchmark signal requiring mechanistic follow-up, not proof that a specific SFO row caused it.
