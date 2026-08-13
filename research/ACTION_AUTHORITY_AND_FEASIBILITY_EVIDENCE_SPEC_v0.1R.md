# Action Authority and Feasibility Evidence Specification — v0.1R

## Purpose

Freeze a public-safe, deterministic, read-only packet for one future ordinary single-player battle. The packet exists to discover what WH3 exposes around normal owner-issued commands without allowing Transcendence to issue orders.

## Authority

- `authority`: `NO_ORDERS`
- `project_issue_status`: `NOT_ATTEMPTED`
- `direct_acknowledgement_status`: `UNAVAILABLE_NOT_OBSERVED`
- `acknowledgement_claim`: `NOT_ACKNOWLEDGED`
- `outcome_attribution`: `UNVERIFIED_NOT_ATTRIBUTED`

## Contracts

### `TACTICAL_ACTION_AUTHORITY_EVIDENCE_PACKET_V1`

A deterministic offline packet for one command observation or no-command proposal. It records command-event presence, unresolved/fixture-declared origin, selection binding, target/position, point-in-time reachability, state matches, interruption, and interpretation limits.

### `TRANS_ACTION` runtime schema 1

A strict append-only battle log with:

- pack/runtime/battle lifecycle;
- local-unit static identities;
- local-unit selection changes;
- game command events;
- five-second read-only action windows sampled every 250 real milliseconds;
- controllability and player/AI/script control state;
- movement, idle, leaving, routing, and shattering;
- ordered-position and current-target matches;
- point-in-time positional reachability;
- explicit close reasons.

The log forbids foreign local-unit records, hidden target identities, project issue attempts, direct acknowledgements, mutation, unitcontrollers, and multiplayer capture.

### `ACTION_AUTHORITY_CAPTURE_VERIFICATION_V1`

The verifier binds one complete parsed session to the exact staged and installed pack hash and prepared-session manifest. It requires zero project issue attempts and zero direct acknowledgements.

## Evidence classifications

- Offline packet and matrix behavior: `CONTROL_OFFLINE` / `CONTROL_SYNTHETIC`.
- Battle 4 boundary report: `CONTROL_OFFLINE_DERIVED_FROM_OBSERVED_INPUT`.
- Future ordinary-battle capture after successful owner run: `OBSERVED_READ_ONLY_ACTION_AUTHORITY`.
- Project issue, direct acknowledgement, causal execution, and outcome: `UNVERIFIED`.

## Capture workflow

1. `prepare_action_authority_capture.ps1` builds the deterministic pack, stages and explicitly installs it, archives/clears the append log, and records exact hashes. It does not enable the mod or modify saves.
2. The owner enables only the action-authority pack and fights one ordinary single-player battle using normal player input.
3. `collect_action_authority_capture.ps1` parses and verifies the exact prepared session.
4. The public ZIP contains only summary, verification, and public manifest. Raw logs and personal paths remain under `local_inputs`.

## Fail-closed rules

Reject:

- malformed booleans, identities, times, events, fields, or ordering;
- nonlocal unit selection or samples;
- hidden target identities;
- multiplayer sessions;
- mismatched staged/installed/expected pack hashes;
- stale logs predating preparation;
- multiple or incomplete sessions;
- any project issue attempt, unitcontroller, direct acknowledgement, or open action window at completion;
- any claim that a state match establishes acceptance or causality.

## Limits

This gate does not establish command legality, live planner control, path safety, formation/collision feasibility, interruption semantics for every WH3 command, SFO compatibility, casualty reduction, or tactical superiority.
