# Shadow Army Objective Assignment — Acceptance Specification v1

## Objective

Given an immutable observer-safe campaign snapshot, assign exactly one legal strategic objective to every controlled army without mutating game state.

## Required observations

- controlled army identity, position, movement, estimated strength, replenishment, and prior objective;
- visible enemy army identity, position, faction, and estimated strength;
- region identity, owner, position, strategic value proxy, threat proxy, siege state, and garrison estimate;
- current wars;
- turn number and environment profile.

Replicated baseline observation provides controlled army identity/position/subtype/unit count, local region identity/position, visible foreign character identity/position/faction/unit count, visible region identity/owner, turn number, and local faction.

Turns 4–7 observed controlled force strength, movement, average unit soldier percentage, stance, settlement structure/siege state, explicit wars, and visible entities. v0.1J additionally requires explicit field-army eligibility and armed-citizenry garrison identity in the corrected broad run.

Prior objectives are project-owned adapter history. Foreign army strength and foreign garrisons initially use disclosed proxies rather than privileged exact values.

## Invariants

1. Hidden armies cannot influence a decision.
2. One controlled army receives one objective.
3. Every objective type is from the allowed contract.
4. Targeted objectives reference an observed legal target.
5. Repeated identical inputs produce an identical result digest.
6. Target capacity limits prevent all armies from selecting one target without an explicit concentration policy.
7. Existing objectives receive a bounded continuity bonus rather than unconditional lock-in.
8. Every decision records rationale, component scores, and at least the best available alternatives.
9. `HOLD` remains a legal deterministic fallback.
10. No order is issued in shadow mode.
11. Nonfield character forces receive no army objective.
12. Own and foreign feasibility values use a common disclosed scale.
13. A field army occupying a settlement is not counted as settlement garrison strength.

## Initial synthetic metrics

- objective churn rate;
- hold rate;
- target overconcentration;
- legal-target violations;
- hidden-information violations;
- relief response for besieged high-value regions;
- recovery selection for depleted armies;
- travel efficiency;
- capture and battle outcomes in Tier 2;
- variation across Tier 3 seeds.

## Failure fixtures

- hidden enemy army located beside a controlled army;
- duplicate army identifiers;
- malformed war relationship;
- depleted army far from friendly territory;
- two threatened fronts with limited armies;
- high-value siege versus tempting weak offensive target;
- no legal targets;
- stale prior objective;
- changed profile hash;
- identical inputs rerun twice.

## Promotion rule

Passing this specification promotes only the offline decision contract. It does not prove WH3 observation availability, superior campaign performance, or order authority.

## Runtime timing rule

Only `LOCAL_FACTION_TURN_START` snapshots may enter the planner. `FIRST_TICK` snapshots are diagnostic because the first live run showed visibility expansion between those phases.


## Initial foreign-information policy

- foreign armies: identity, position, faction, subtype, and visible unit count only;
- foreign exact `military_force:strength()`: not consumed;
- foreign unit-health internals: not consumed;
- foreign garrison composition/strength: not consumed;
- foreign region garrison estimate: settlement-level/wall proxy;
- every proxy is recorded in field provenance.

This policy may be revised only after a specific fairness and UI-visibility review.


## Consolidated runtime acceptance

The corrected live vertical slice uses turn starts 1–5 from one fresh campaign and at least two manually fought ordinary campaign battles in the same prepared append-log session. The offline pipeline must:

- produce one proposal set per turn;
- retain exact scenario and decision digests;
- carry previous proposals only as bounded continuity inputs;
- report objective changes only for armies observable in adjacent turns;
- preserve every capability failure and proxy-policy violation;
- reject incomplete, duplicate, out-of-order, or nonconsecutive snapshots;
- stay in `SHADOW_NO_ORDERS` mode;
- create one upload ZIP.

Churn, HOLD rate, and state changes are descriptive in this gate. They do not establish gameplay quality.

The battle component is observational only. It must not create unitcontrollers or issue orders, and its presence does not promote campaign or battle action authority.
