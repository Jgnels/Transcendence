# Gate 0 Consolidated Campaign-and-Battle Preparation Report — v0.1I

## Result

The offline preparation segment for one batched, read-only WH3 campaign-and-ordinary-battle session is **closed**.

Gate 0 overall remains open because the combined pack has not yet produced live battle evidence or expanded live campaign evidence.

## Why v0.1H was superseded

v0.1H treated battles as allowed but did not inspect them directly. That was misaligned with the product: real-time battles are a central part of why the owner values Total War. Requiring a later independent battle-observation session would also add avoidable owner tedium.

Campaign observation and ordinary-battle observation share the same read-only authority boundary, so v0.1I combines them safely while preserving separate parsers, contracts, and evidence labels.

## Implemented

### Combined exact pack

`transcendence_shadow_probe.pack` now contains:

- `script/campaign/mod/transcendence_shadow_probe.lua`;
- `script/battle/mod/transcendence_battle_probe.lua`.

Final pack SHA-256:

`c23b8187dde9e0f162b1564b47910714501b9d088b756cb95dfe16cad470b551`

### Campaign pipeline

- at least five consecutive local-turn snapshots;
- one deterministic orderless objective proposal per turn;
- bounded prior-proposal continuity;
- churn, HOLD, state-change, proxy-policy, volume, and processing telemetry;
- strict expanded-field and hidden-information handling.

### Ordinary-battle telemetry

- battle origin/type/local alliance/unit-scale metadata;
- deployment, deployed, victory-countdown, and completion phase callbacks;
- alliance → army → unit hierarchy traversal;
- visible-only foreign unit records;
- static type/class/control metadata;
- dynamic position, ordered position, bearing, movement, idle, melee, missile pressure, morale/routing, flank, health, men, kills, ammunition, target, and strategic-value proxy fields where available;
- one-second alliance aggregates;
- three-second detailed samples plus phase samples;
- selection and command-handler traffic;
- completion, result, winner, and duration;
- descriptive per-unit and battle metrics.

### Combined verifier and export

- exact installed/staged pack identity;
- shadow-only loaded-probe isolation;
- five-turn campaign minimum;
- one completed battle minimum;
- local and visible enemy unit minimums;
- multiple battle samples;
- hidden-enemy leak rejection;
- explicit capability failures;
- read-only authority assertions;
- 30 MB log bound;
- one upload ZIP.

## Authority boundary

The battle script contains no unitcontroller creation, order call, battle-speed modification, saved-value write, visibility mutation, damage/heal mutation, or random choice.

Campaign output is `SHADOW_NO_ORDERS`.

Battle output is `BATTLE_OBSERVATION_NO_ORDERS`.

Observed command traffic is not an acknowledgement and is not proof of execution or tactical effectiveness.

## Deterministic fixture result

The combined five-turn/one-battle fixture produced:

- campaign turns: `1, 2, 3, 4, 5`;
- 10 campaign assignments;
- campaign objective churn: `0.25`;
- one completed ordinary land battle;
- four detailed battle samples;
- three observed unit identities: two local and one visible enemy;
- one command event;
- local casualties observed: 10;
- visible-enemy casualties observed: 80;
- local kills observed: 53;
- zero capability failures;
- no order authority.

Deterministic digests:

- campaign result: `7adeac641b0ad95dbd039530f731e08e1301fcac8b1b3804bbc37e41a79ad45a`;
- battle result: `e4793e9e43e3663b568c1438b66a4331aab398bd272ec443d29346ec1df3e266`;
- combined verifier result: `91b8809710d90d251f8924ef6c8dd72ef42cfabc6934b9669a8163fd19270f2b`.

These values validate the pipeline only. They are not tactical-quality or balance targets.

## Adversarial coverage

The suite rejects or reports:

- hidden foreign unit records;
- detailed samples without matching end records;
- malformed/private/out-of-order fields;
- campaign turn gaps;
- too few campaign turns;
- wrong exact pack identity;
- foreign campaign strength-policy violations;
- missing battle sessions as `PARTIAL_NO_BATTLE` rather than fabricated success;
- capability failures;
- any static indication of unitcontroller or order authority.

## Remaining live condition

One fresh pure-vanilla Karl Franz campaign must:

1. use only the exact combined shadow pack;
2. reach at least five consecutive local-faction turn starts;
3. manually fight and complete at least one ordinary campaign battle, preferably a field battle;
4. return one combined evidence ZIP whose verifier status is `OBSERVED`.

No additional one-turn or one-field probe is required first.

## Validation summary

- 18 SyntheticLab tests;
- 38 runtime-probe tests;
- 56 total tests per complete validation;
- 122 repository files hash-verified;
- two complete validations passed in 1.72 and 1.67 seconds;
- maximum resident memory 111,496 KB and 111,200 KB;
- two final pack builds were byte-identical;
- pack-build result digest `2b18a01f5b9c75100de50dda59774ae5d265352f29594b29941dce4534da4550`;
- build-manifest SHA-256 `64d736885bff93fccd9207c33663eb987f610301ad12556b6894a3b605b64b65`.
