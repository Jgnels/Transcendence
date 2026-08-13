# Campaign Strategic Feasibility and Action-Authority Specification v0.2H

## Purpose

v0.2H sits between the v0.2G shadow army commitment and any future campaign order adapter. Its job is to describe the smallest read-only questions that WH3 can plausibly answer about a shadow assignment while preventing documentation, geometric references, query results, or ambiguous interfaces from becoming order authority by accident.

## Authority boundary

- project authority: `NO_ORDERS`;
- application authority: `PROHIBITED`;
- source assignments: `SHADOW_PROPOSED_NOT_EXECUTED`;
- v0.2G geometry: `NOT_EVALUATED_GEOMETRIC_REFERENCE_ONLY`;
- v0.2H query results over the preserved owner evidence: `UNOBSERVED_QUERY_NOT_RUN`.

No campaign movement, stance change, attack, garrison entry/exit, action-point mutation, pathfinding-restriction change, acknowledgement, execution, or outcome interface is invoked by this release.

## Documented query classes

The documentation audit establishes a query vocabulary, not owner-runtime proof:

1. stable actor binding by character and military-force CQI;
2. current active stance;
3. same-turn point reachability;
4. same-turn point reachability in an exact stance;
5. long-horizon point reachability;
6. exact region-to-settlement interface resolution;
7. same-turn settlement reachability;
8. same-turn settlement reachability in an exact stance;
9. long-horizon settlement reachability;
10. current garrison siege-state context;
11. stance activation eligibility as a separate future query, never a target-reachability proof.

`GARRISON_RESIDENCE_SCRIPT_INTERFACE.can_assault` is documented but context-ambiguous for this project and is not accepted as actor-target attack legality. `can_be_occupied_by_faction` is also not an actor movement/attack legality signal.

## Target semantics

A v0.2G `REGION` target may be resolved to that exact region's settlement interface for reachability queries. This is not promotion to an attack order or proof that assault/occupation is legal.

A v0.2G `FACTION` target remains a faction/theater objective. Its observer-safe visible-asset centroid may be queried only as a reference point. The centroid may not silently become a character target, settlement target, or attack target.

A capacity/posture assignment with no destination does not gain a destination merely because movement APIs exist.

## Query-result semantics

A true same-turn reachability result means only that the documented query returned true for the exact actor, exact target representation, exact stance if supplied, and observation instant. It does not reveal route geometry, zone-of-control behavior, interception outcome, command legality, command acceptance, execution, or success.

A false same-turn result does not imply permanent unreachability. A true `can_ever_reach_*` result is long-horizon/topological evidence only; it is not an ETA, route quality, safety, or eventual-success guarantee.

## Observation packet

Any later live packet must bind:

- exact current scenario and turn;
- source feasibility-plan digest;
- current planner-eligible controlled actor CQIs;
- exact generated query IDs;
- every observed boolean/string result;
- `orders_emitted = false`;
- `save_values_written = false`.

Stale turns, foreign query IDs, duplicate query IDs, changed authority, malformed values, or cardinality drift fail closed.

## Mutation surfaces kept prohibited

The v0.2H boundary explicitly inventories movement, attack, garrison, stance-force, action-point, movement-enable/disable, and pathfinding-restriction mutation surfaces. The catalog is evidence of what must *not* be called by a read-only probe; listing a name is not an implementation of it.

## Generalization limits

The preserved Reikland campaign sequence contains only one v0.2G force assignment, on turn 7, and that assignment targets a faction centroid. Therefore v0.2H can freeze the query contract and historical query plan but cannot promote any campaign reachability query to owner-runtime `OBSERVED` without a distinct live read-only gate. The historical turn-7 state does not need to be recreated.
