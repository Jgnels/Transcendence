# Guarded Tactical Action Packet Specification v0.1V

## Purpose

Convert one canonical tactical feasibility envelope into a strictly bounded shadow-review packet set without creating order authority.

## Contracts

- `TACTICAL_GUARDED_ACTION_PACKET_V1`
- `TACTICAL_GUARDED_ACTION_PACKET_SET_V1`
- `TACTICAL_GUARDED_ACTION_TRAJECTORY_V1`

## Source requirements

A packet set is valid only when:

- tactical state, temporal schedule, and feasibility-envelope digests verify;
- source slice and time match exactly;
- the complete canonical plan identity set matches a feasibility envelope rebuilt from the state and schedule;
- plan identities are unique and cardinalities reconcile;
- candidate identities, ranks, strategies, points, displacements, derivations, and clipping flags match canonical geometry;
- authority remains `NO_ORDERS`.

## Readiness classes

- `READY_POINT_SUPPORTED_SHADOW_ONLY`
- `DEFERRED_POINT_UNOBSERVED`
- `DEFERRED_QUERY_UNAVAILABLE`
- `BLOCKED_POINT_QUERY_FALSE`
- `BLOCKED_ACTOR_PRECONDITION`
- `BLOCKED_GEOMETRY_UNAVAILABLE`
- `BLOCKED_MIXED_NO_SUPPORTED_POINT`

Only exact candidates carrying bound `QUERY_TRUE` evidence may enter the eligible-candidate list. The lowest canonical rank becomes the provisional packet selection. That selection is not executable and is passed only to simultaneous conflict review.

## Authority and interpretation

Every packet fixes:

- `application_status = PROHIBITED_NO_ORDER_AUTHORITY`;
- `project_issue_status = NOT_ATTEMPTED`;
- `direct_acknowledgement_status = UNAVAILABLE_NOT_OBSERVED`;
- `execution_status = NOT_ISSUED`;
- route, formation, collision, command legality, and outcome as `UNVERIFIED`.

`QUERY_FALSE` blocks one exact point only. It does not establish that the tactical objective is infeasible.
