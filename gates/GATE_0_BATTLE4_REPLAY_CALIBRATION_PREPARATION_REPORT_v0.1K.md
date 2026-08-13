# Gate 0 Battle 4 observed-trace calibration and dense replay preparation — v0.1K

## Result

The **offline Battle 4 calibration and dense replay-preparation segment is closed**.

The replay-observation feasibility segment was already `OBSERVED`. v0.1K converts that evidence into a reusable public-safe SyntheticLab Tier 4R corpus, corrects identity and interpretation defects in the offline analysis, and prepares one dedicated read-only replay pass capable of proving or limiting dense telemetry.

The live dense replay condition remains open. The owner does not manually refight the battle.

## Frozen owner evidence

- Battle: Battle of Eilhart — Reikland versus Empire Secessionists
- replay SHA-256: `76b8807f5cc2d223d454028f54fc18b791a254c3ce543aa587ad4286658e302b`
- captured `TRANS_BATTLE` log SHA-256: `61191615c008a48791397486fa7e841c383656fb313660ee48d44af3cece8860`
- exact capture-verification digest: `fcfec312c281dc92f53d49a5698332479bba5f2d19059dd071dcfd6638292607`
- completed duration: 739.6 seconds
- observed command events: 397
- authority: read-only; no orders, unitcontrollers, speed changes, save writes, or visibility mutation

## Defects found and corrected

### Stable unit identity

The first report treated hierarchy indexes as part of canonical identity and produced 50 apparent units. The replay actually contains 34 canonical observed units and 16 hierarchy aliases.

Correction: schema 2 uses `alliance_index + unique_ui_id` as identity. Alliance/army/unit indexes are retained only as mutable hierarchy observations.

### Sparse sample interpretation

The source declared a three-second detail interval but produced five phase-triggered samples instead of roughly 247. The largest gap was 601.9 seconds.

Correction: time-series metrics are withheld unless explicit density and maximum-gap checks pass. Terminal outcomes, lower bounds, phases, deployment changes, and command traffic remain usable.

### Selection attribution

The original callback was not registered per unit and captured zero selection events.

Correction: the source-supported callback is now registered once per local player-controlled unit. Command attribution remains direct only when callback state is present; state-change matching is separately labeled `INFERRED_NOT_ACKNOWLEDGED`.

### Outcome exactness

Some units disappeared from observation before the terminal phase because visibility and hierarchy membership changed.

Correction: casualties and ammunition are lower bounds unless the unit has a terminal observation. Exact total-casualty claims are withheld unless local and visible-enemy terminal coverage are both complete.

## Battle 4 as SyntheticLab Tier 4R

The public corpus contains source digests and derived state only. It does not contain the replay, raw log, personal paths, or Creative Assembly assets.

It deterministically tests:

- stable identity and hierarchy churn;
- hidden-enemy boundaries;
- sample-density sufficiency;
- exact-versus-lower-bound outcomes;
- explicit command-attribution labels;
- commander danger;
- frontline collapse;
- high-output ranged/specialist preservation;
- routed visible enemies;
- missing terminal observations.

All ten Tier 4R checks pass.

Frozen digests:

- reconciled report: `1f151473c0530a43f768ea2c3c01ae2df1faa397d79de5e1d6a001daef8352cb`
- Tier 4R corpus: `24af79128738bc648504094784eaced4d872ca05bf680c0e5f16061eac47da8d`
- Tier 4R regression: `0d93daf622e65e1bdf498c9a8526c2d34a79c93bbd29099a0d2c31c6ce149e02`
- public analysis: `ff77f7792b005bb4b2e7ad242618e4fe578fec3c24555c951ee062bda67f4bff`

## Dense replay instrumentation

The dedicated battle-only pack adds:

- schema-2 stable identities and hierarchy-change events;
- army/faction/subculture context;
- dual model-time and real-time callbacks;
- 500 ms real callback, one-second alliance aggregates, three-second detailed unit samples;
- sampler start and heartbeat records;
- callback-failure disclosure and maximum-gap verification;
- current, ordered, and officer positions;
- path length and ordered-path change;
- deployment and control state;
- target identity, target distance/range, and target switches;
- flank threat identity and direction;
- movement, melee, missile pressure, morale, routing, shattering, fatigue, ammunition, and strategic-value proxy;
- ability ownership and ability-command timeline;
- per-unit selection callbacks and selected-unit command attribution;
- bounded inference when direct selection is unavailable;
- one-command capture, report, corpus generation, verification, and export.

## Authority boundary

The dedicated replay pack is battle-only and query-only. It contains no:

- unitcontroller creation;
- movement, attack, formation, or ability order;
- battle-speed change;
- damage, healing, resurrection, or ammunition mutation;
- save write;
- visibility mutation;
- randomness.

## Deterministic build

- observer pack: `0c1dd8940a697a2d840876f08092ba02f988170e90c5f77b6f934ac15c79f173`
- persistence pack: `71bf96e4fca54d16e323f5eef9766a6098c6ea4b9416b33aa012317d5f682bd2`
- combined shadow pack: `782f7e69c97059c9f66eb6dad5736236c3af9c54bee8b62b6a40a4d9fbf99da8`
- dedicated replay pack: `185baaa832beb458797e47766a3ad121530cdcf811097e8eb90d787df50c8443`
- build result digest: `bb06bff155cfd1e69182c82080e1ae865b8ef1a19008f80990c0a716e2b9710c`
- build-manifest SHA-256: `d88b383cccc9c26e9f5b4193130ba52ff25c18ebf7699d9f15c8cb735b940644`

Two independent builds were byte-identical. Two complete repository validations passed, each running 76 tests and verifying 150 canonical files. Validation times were 2.04 and 1.86 seconds, with maximum resident memory of 114,828 KB and 111,668 KB.

## Capability claims

Promoted:

- Battle 4 observed replay can serve as a Tier 4R calibration corpus — `OBSERVED`.
- Stable reconciliation of schema-1 hierarchy aliases — `CONTROL` offline.
- Sparse-sampling sufficiency rejection — `CONTROL` offline.
- Exact/lower-bound outcome labeling — `CONTROL` offline.
- Dense schema-2 parser, reporter, verifier, and fixture pipeline — `CONTROL` offline.

Still unverified live:

- dual-clock callback continuity in the preserved replay;
- dense three-second per-unit coverage;
- one-second aggregate continuity;
- direct selection callbacks during replay playback;
- bounded attribution quality;
- ordinary live campaign-battle equivalence;
- SFO compatibility;
- order acceptance or tactical-AI quality.

## Smallest remaining live condition

1. apply and validate v0.1K;
2. install the dedicated replay pack;
3. enable only that pack;
4. arm the dense capture watcher;
5. play the existing `Auto-save.replay` through its result screen without issuing commands;
6. upload the one exported ZIP.

The verifier closes as `OBSERVED_DENSE` when direct selection attribution is present. It preserves `OBSERVED_DENSE_SELECTION_LIMITING_RESULT` when telemetry is dense but replay playback does not emit selection callbacks. Either result is informative and requires no manual refight.
