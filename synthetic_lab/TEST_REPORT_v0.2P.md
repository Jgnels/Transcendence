# SyntheticLab Test Report — v0.2P

Date: 2026-08-04

Command:

`PYTHONPATH=synthetic_lab python -m transcendence_lab.cli test`

Result: **187/187 PASS**.

v0.2P-specific coverage includes:

- deterministic vanilla territorial faction-cluster reference and 0.222222–0.317073 leave-one-faction-out sensitivity envelope;
- captured SFO task-priority footprint: 93 carried rows, 88 changed, 88 increases / 0 decreases, 30 changed generator groups;
- fail-closed direct SFO allocator attribution when no decoded SFO allocator-variable override exists;
- direction-aware precommitted temporal branches for insufficient, lower-than-envelope, within-envelope, higher-than-envelope, and repeated-force outcomes;
- recovery branch separation and allocator-attribution guard;
- deterministic rebuild equality for mechanistic registry, ablation candidate registry, and post-SFO decision table;
- preservation of `NO_ORDERS`, `application_eligible=false`, and application `PROHIBITED`.
