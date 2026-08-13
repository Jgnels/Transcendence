# Native Diagnostic Vanilla Owner Qualification — v0.2M-r1

Date: 2026-08-03

## Status

**Telemetry qualification: PASS. Behavioral confirmation: NOT ATTEMPTED.**

The owner capture `Transcendence_NativeDiagnostic_VANILLA_20260803T060701Z.zip` (SHA-256 `99c7ad0b1d08441307e65815801e29c0ee38d4067fb8aa864b88fcc6c98a0c02`) is a profile-bound vanilla diagnostic cohort produced by probe SHA-256 `347605a1c00efc2478cc3f43bd699db6ec8f4af96b7a3cd3cc189861ad1a5d37`. The campaign reached Reikland turn-start markers `[1, 2, 3, 4, 5, 6, 7]` with zero capability failures and zero incomplete normal AI faction turns.

## Frozen qualification facts

- 1,588 paired AI faction-turn start/end observations.
- 292 distinct AI factions.
- 2,353 matched army-turn pairs.
- 967 moving army-turn pairs.
- 426 consecutive trajectory-exposure pairs.
- 116 descriptive >=120-degree heading-reversal candidates from the pre-existing v0.2M exposure metric.
- 12 explicit `rebels` pseudo-faction skip events; the r1 crash fix survived all completed cycles.
- `NO_ORDERS`, application authority `PROHIBITED`, privileged diagnostic data permanently application-ineligible.

## Exploratory observations only

These observations were produced after looking at the cohort and **must not be treated as confirmatory evidence**. They exist only to choose the next preregistered study.

A stricter post-hoc filter requiring stable subject war set, owned-region set, stance, health range <=5 percentage points, strength ratio <=1.10, unit-count range <=1, two moves >=5 coordinate units, and a >=120-degree reversal retained **7** candidates. Examples included:

- `wh_main_emp_averland` force `233`, turns [4, 5, 6]: wh3_main_combi_region_wurtbad -> wh3_main_combi_region_niedling -> wh3_main_combi_region_wurtbad; cosine -0.924223; at_peace=true.
- `wh3_main_grn_tusked_sunz` force `302`, turns [4, 5, 6]: wh3_main_combi_region_the_challenge_stone -> wh3_main_combi_region_icespewer -> wh3_main_combi_region_the_challenge_stone; cosine -1.0; at_peace=false.
- `wh_main_grn_necksnappers` force `274`, turns [4, 5, 6]: wh3_main_combi_region_crooked_fang_fort -> wh3_main_combi_region_valayas_sorrow -> wh3_main_combi_region_crooked_fang_fort; cosine -0.930312; at_peace=false.

The same cohort also contains damaged armies that moved, but movement alone cannot establish offensive re-entry or recovery misuse. The v0.2M-r1 probe had **no battle-participant channel**, so the old data cannot certify that any reversal was battle-free or that any damaged army initiated a battle.

## Decision

The diagnostic acquisition channel is qualified. The next confirmatory cohort must be **fresh** and produced by a new probe that explicitly declares and records pending-battle participants. Thresholds and exclusion rules are frozen before that fresh cohort is collected. The old v0.2M-r1 capture is structurally ineligible for the confirmatory evaluator.
