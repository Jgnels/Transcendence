# Tactical Pipeline Adversarial and Scaling Specification v0.1X

## Purpose

Exercise the complete offline tactical path:

`tactical state → assignment → temporal schedule → feasibility envelope → guarded packet → endpoint reservation`

under deterministic representation changes, query evidence modes, forged inputs, and bounded scale.

## Deterministic fuzz corpus

- seed `20260730`;
- 256 full-pipeline cases;
- 12 heterogeneous source scenarios;
- five query modes: none, all true, all false, all unavailable, and cyclic mixed;
- reversed unit order and translated coordinates checked semantically;
- repeated execution must reproduce exact digests.

## Structural invariants

- all authority remains `NO_ORDERS` and application authority `PROHIBITED`;
- no issue, acknowledgement, execution, arrival, or outcome claim appears;
- each plan has at most three candidates and no candidate exceeds 120 metres abstract displacement;
- reservations never exceed ready packets;
- no actor is reserved twice;
- selected endpoints satisfy the 12-metre development separation contract;
- forged duplicate plans and authority escalation fail closed.

## Scaling matrix

Packet counts: 8, 16, 24, 40, 80, and 160, each in separated-line and clustered-grid layouts. Results preserve solver mode, search nodes, reservation counts, and explicit optimality status. These are structural work-unit tests, not live WH3 frame-time measurements.
