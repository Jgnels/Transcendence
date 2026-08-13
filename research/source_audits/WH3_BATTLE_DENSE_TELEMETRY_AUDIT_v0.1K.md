# WH3 dense battle telemetry source audit — v0.1K

## Scope

This audit supports the narrow Battle of Eilhart dense replay-calibration gate. It does not establish battle-order authority.

## Pinned inspected sources

### Battle-manager callback implementation

- repository: `Shazbot/WH3-Dump`
- revision: `61d4e117f669ea93d6da1077d1524c332d5e74c9`
- file: `script/_lib/lib_battle_manager.lua`

Observed mechanism:

- `register_unit_selection_callback(unit, callback)` is registered once per subject unit;
- the internal handler invokes `callback(unit, selected)`;
- therefore one global registration without a unit argument cannot provide selected-unit attribution.

The same library distinguishes model-time callbacks from real/UI-time callbacks. v0.1K uses both and emits explicit sampler heartbeats rather than assuming one timer works during replay playback.

### Generated battle-unit query interface

- repository: `chadvandy/tw_autogen`
- revision: `a4f87829cd7197ecdbcd7701373ca6281f53314b`
- file: `output/wh3/battle/battle_unit.lua`

Observed query contracts used by v0.1K include:

- `unique_ui_id`, alliance and army indexes;
- type, class, commander and role-category queries;
- current, ordered, and officer position;
- bearing, ordered bearing, and ordered width;
- player/AI/script control state;
- movement, idle, deployment, valid-target, hidden, and visibility queries;
- men, health, kills, ammunition, strategic-value proxy;
- melee, missile pressure, morale, routing, shattering, rampage, fatigue;
- current target, target distance/range, and flank-threat queries;
- passive and non-passive ability ownership.

`unique_ui_id` is documented as the stable unit-card identity. v0.1K therefore treats hierarchy indexes as mutable observations rather than canonical identity.

## Authority classification

All methods used by the probe are query or callback registration methods. The source deliberately excludes:

- unitcontroller creation;
- movement, attack, formation, or ability orders;
- speed changes;
- unit damage, healing, resurrection, ammunition changes, or respawn;
- visibility mutation;
- saved values and campaign mutation;
- randomness.

Capability classification: `OBSERVE — PREPARED_OFFLINE`; live dense callback continuity remains `UNVERIFIED` until the replay pass.

## Defensive interpretation

- command-handler events are not acknowledgements;
- selected-unit attribution is direct only when selection callbacks are observed;
- state-change matching is labeled `INFERRED_NOT_ACKNOWLEDGED`;
- visible enemy telemetry is intentionally incomplete while units are hidden;
- strategic value is an engine proxy, not published recruitment cost;
- dense time-series metrics are withheld unless callback coverage and maximum-gap checks pass.
