# Gate 0 Consolidated Campaign-Shadow Preparation Report — v0.1H

## Result

The offline preparation segment for one batched, read-only, multi-turn WH3 campaign run is **closed**.

Gate 0 overall remains open because the consolidated pack has not yet produced live WH3 evidence.

## Why this segment changed

The initial shadow plan requested one fresh campaign for a single turn and would have encouraged further one-field-at-a-time runs. Observer loading, structured logging, exact-pack identity, parser strictness, and persistence are already proven. Additional read-only campaign fields can therefore be tested together without crossing a new authority boundary.

## Implemented

- multi-snapshot shadow-log extraction;
- one deterministic Army Objective Assignment proposal per local-faction turn start;
- bounded continuity from the prior proposal for the same observed army;
- objective-change and comparable-army accounting;
- objective churn and HOLD-rate telemetry;
- scenario-state-change telemetry;
- foreign-strength and foreign-garrison proxy-policy enforcement;
- exact installed/staged shadow-pack verification;
- isolated loaded-probe verification;
- minimum five-turn and consecutive-turn acceptance;
- duplicate, capability-failure, log-volume, and processing guardrails;
- one-command collection and one upload ZIP;
- documentation that inferred campaign-state changes are not direct battle observation.

## Authority boundary

The shadow pack remains byte-identical to v0.1G:

`2cb66df8850d1953f42686a52d6338b62addc2a9e347d4844aba32e74dd343ae`

It contains no save-value write, campaign order, diplomacy mutation, resource mutation, foreign complete-world enumeration, or randomness path.

Every generated result remains `SHADOW_NO_ORDERS`.

## Offline fixture result

The five-turn fixture produced:

- turns: `1, 2, 3, 4, 5`;
- 10 total army assignments;
- 8 comparable adjacent-turn assignment pairs;
- 2 objective changes;
- objective churn rate: `0.25`;
- HOLD rate: `0.60`;
- 4 scenario-state changes;
- zero capability failures;
- zero foreign-proxy violations;
- deterministic result digest: `7adeac641b0ad95dbd039530f731e08e1301fcac8b1b3804bbc37e41a79ad45a`.

These values validate the pipeline only. They are not gameplay-quality targets.

## Adversarial coverage

The suite now verifies:

- fewer than five turns fail acceptance;
- exact pack identity is required;
- loaded and expected probe kinds must both be shadow-only;
- foreign source-policy violations are reported;
- duplicate snapshot records remain defects;
- nonconsecutive turn sequences fail;
- orders and save writes are absent;
- identical five-turn inputs reproduce identical output.

## Remaining live condition

One fresh pure-vanilla Karl Franz campaign must run through at least five consecutive local-faction turn starts with only the shadow probe enabled. The one-command collector must then return `OBSERVED` and create the upload ZIP.

No separate live run is required for each expanded field.


## Validation summary

- 18 SyntheticLab tests;
- 30 runtime-probe tests;
- 48 tests per complete validation;
- 112 repository files hash-verified;
- two complete validations passed;
- two probe builds were byte-identical;
- probe-build result digest: `1de93c89eddbd5ca566f37f02ed9c5f914b72569a9b9127baeaf1c9f6c55d804`;
- build-manifest file SHA-256: `1ad861908b6849c1868bb428cbfa865cc7514ceb3670f8ed8fdc1c5ab55ebec5`.
