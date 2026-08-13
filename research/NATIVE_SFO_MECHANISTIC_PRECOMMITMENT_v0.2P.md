# Native/SFO Mechanistic Precommitment — v0.2P

Status: **FROZEN BEFORE FRESH SFO OWNER DATA**

## Purpose

v0.2P hardens the already-preregistered v0.2O matched SFO benchmark before any SFO behavior trace exists. It does not change the in-game diagnostic probe, campaign protocol, v0.2N recovery thresholds, v0.2N temporal thresholds, or application authority.

The goal is to prevent three predictable attribution errors:

1. treating overlapping army windows as independent samples;
2. saying “SFO differed, therefore copy SFO rows” regardless of direction;
3. attributing an SFO recovery difference to allocator rows that SFO did not actually override in the decoded owner pack.

## Hash-frozen vanilla cluster sensitivity

The v0.2N owner vanilla bundle is retained by SHA-256 provenance and reprocessed only to derive descriptive faction-cluster sensitivity for the already-prospective territorial definition.

Territorial cohort:

- 48 eligible stable-context/battle-free windows;
- 13 single reversal candidates;
- candidate rate 0.270833;
- 26 factions with at least one eligible territorial window;
- 8 factions with at least one reversal candidate;
- zero territorial forces satisfying the v0.2N repeated non-overlapping signal rule.

Leave-one-faction-out candidate-rate range:

- minimum: **0.222222**;
- maximum: **0.317073**.

This range is a **descriptive cluster-sensitivity envelope only**. It is not a confidence interval, standard error, p-value, or causal estimate.

## Captured SFO CAI row footprint

From `NATIVE_CAI_ROW_DIFFS_2026-08-02.json`:

- decoded SFO CAI rows occur in `cai_task_management_system_task_generator_groups_generators_junctions_tables`;
- SFO carries 93 rows there;
- 88 differ from current vanilla;
- all 88 changed priorities are increases;
- zero are decreases;
- 30 generator groups are represented among changed rows;
- 13 distinct generators are represented;
- no decoded SFO rows are present in `cai_task_management_system_variables_tables`, so **no direct SFO allocator-variable override is observed** in the captured targeted corpus.

Therefore a future SFO recovery difference cannot be directly attributed to SFO changing allocator release/return/distance variables from this captured DB footprint. Other SFO systems and indirect interactions remain unresolved confounders.

## Precommitted temporal interpretation

Primary population remains territorial, using the exact v0.2O rule and unchanged v0.2N stable-context/battle exclusions.

1. `<20` eligible territorial windows -> `INSUFFICIENT_EXPOSURE`; extend/reacquire only.
2. `>=20` eligible and `repeated_reversal_force_count > 0` -> possible worsening/special-policy signal; causal review + replication; **do not copy SFO priority increases**.
3. repeated count `0` and candidate rate `<0.222222` -> descriptive improvement nomination; replicate matched profile before any row ablation; SFO task-priority increases become replication-eligible only.
4. repeated count `0` and candidate rate between `0.222222` and `0.317073` inclusive -> within vanilla faction-cluster sensitivity; **no temporal mechanistic nomination**.
5. repeated count `0` and candidate rate `>0.317073` -> descriptive worsening nomination; replication + causal review; **do not copy SFO priority increases**.

The repeated-force endpoint remains primary over the descriptive single-window rate.

## Precommitted recovery interpretation

The v0.2N threshold remains unchanged:

- recovery exposure = start-of-own-turn average unit health <65%;
- minimum 10 exposures;
- positive signal requires >=2 attacker-side reentries and >=20% attacker-side rate.

Branches:

1. `<10` exposures -> extend only;
2. positive SFO signal -> possible worsening relative to the vanilla negative cohort; replicate + causal review; task priorities may be indirectly relevant, but direct SFO allocator attribution is ineligible because no SFO allocator override was observed;
3. sufficient exposure without positive signal -> no recovery intervention earned.

## Dormant ablation candidates

A small generic/default task-priority candidate registry is prepared only so later work cannot cherry-pick rows after seeing SFO. Every candidate is `DORMANT_REPLICATION_ONLY_NOT_EARNED` before fresh SFO data.

No row is authorized for installation or application. Wholesale SFO row copying is prohibited.

## Statistics boundary

- Do not compute a p-value treating overlapping windows as independent observations.
- Report faction-cluster counts, candidate concentration, and leave-one-faction-out sensitivity.
- One vanilla campaign versus one SFO campaign is a matched benchmark, not randomized causal identification.
- A directionally interesting result earns replication, not a causal claim.

## Authority

- `authority = NO_ORDERS`
- `application_authority = PROHIBITED`
- privileged diagnostic telemetry remains `application_eligible=false`
- v0.2G/v0.2I remain outside the application path.
