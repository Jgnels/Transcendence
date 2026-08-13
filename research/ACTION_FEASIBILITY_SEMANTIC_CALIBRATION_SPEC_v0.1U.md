# Action Feasibility Semantic Calibration Specification — v0.1U

## Purpose

Correctly distinguish explicit point-query evidence from raw engine queries performed against command callbacks whose position field is absent, opaque, or represented by a zero-vector sentinel.

The calibration preserves every raw v0.1S/v0.1T observation but prevents semantically inapplicable query results from becoming tactical-feasibility claims.

## Contracts

- `OBSERVED_COMMAND_POINT_SEMANTIC_CALIBRATION_V1`
- `TACTICAL_FEASIBILITY_SEMANTIC_CAPABILITY_PROFILE_V2`

Historical contracts remain frozen:

- `ACTION_FEASIBILITY_WINDOW_EXPORT_V1`
- `TACTICAL_FEASIBILITY_CAPABILITY_PROFILE_V1`

## Source identity

The calibration accepts only the exact public-safe detailed re-export:

- ZIP SHA-256 `83b7c3d851605f290c6a50045be920cdddc7224c8f9e7e63deefba5323e2ff7d`;
- window document SHA-256 `e56e2e32fc5037bf104ea7da05184c7e591bec2394920b482174f808de7fa18f`;
- raw-log identity `b4f8c4ca9c285018772d50a4eda92f34572f742dd97967bca8229b0a6b3ce951`;
- probe-pack identity `3acf60520b60f87f8c18e13532512324cb7a539626996ce19897fad94cf2d25d`.

Raw log lines, machine paths, usernames, game paths, and private artifacts remain excluded.

## Command modalities

### Explicit point evidence

Only a `Move` callback with:

- no unit target;
- a finite target position;
- a nonzero target position;

is classified as `EXPLICIT_POINT_MOVE` in this captured command vocabulary.

Its raw `can_reach_position` result may be qualified as exact-point evidence for that actor, point, and observation instant.

### Visible unit-target evidence

`Attack Unit` with a visible target is classified as `VISIBLE_UNIT_TARGET_ATTACK`.

Current-target matching is state evidence. The zero-vector position field is not an attack-point query and its raw reachability result is semantically `NOT_APPLICABLE`.

### Opaque or non-point evidence

These captured callbacks do not supply trustworthy explicit point semantics:

- `Move Orientation Width`;
- `Double Click`;
- `Special Ability`.

Any raw reachability call made against their zero-vector callback position is preserved as historical telemetry but excluded from qualified point evidence.

## Corrected limiting result

The v0.1R probe queried every non-nil callback position. In the detailed capture, non-point and opaque callbacks exposed `(0, 0, 0)` as a sentinel-like value.

All 38 raw `QUERY_FALSE` samples came from two actors in window `w5`, a `Move Orientation Width` command. Neither actor moved or matched an ordered point during that window. Those results do not establish an unreachable explicit destination.

The qualified live evidence is therefore:

- 16 explicit Move windows;
- 16 actor-windows;
- 191 qualified samples;
- 191 `QUERY_TRUE`;
- zero qualified `QUERY_FALSE`;
- zero unavailable;
- 16/16 actors matching ordered position in the initial sample;
- 12/16 actors with movement observed during the window.

A valid false result for a semantically qualified explicit point remains `UNVERIFIED_NONE_OBSERVED`.

## State evidence boundary

For visible `Attack Unit` callbacks:

- 37 windows;
- 49 actor-windows;
- 48 actor-windows matched the visible target in the initial sample;
- 30 actor-windows later showed movement.

Ordered-position and current-target matches remain `OBSERVED_NOT_ACKNOWLEDGED`. They do not prove command origin, acceptance, causal execution, arrival, or tactical outcome.

## Planner use

The semantic capability profile may establish only that:

- explicit nonzero Move callback points were queryable in one ordinary vanilla battle;
- true results were observed for those points;
- the current capture provides no valid false-point calibration;
- the capability remains separate from all Transcendence-generated Battle 4 candidates.

The profile may not populate or infer any `TACTICAL_POINT_QUERY_EVIDENCE_V1` candidate result.

## Authority

`NO_ORDERS`.
