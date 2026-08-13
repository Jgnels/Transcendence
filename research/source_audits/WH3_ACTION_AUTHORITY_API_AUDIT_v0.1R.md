# WH3 Action-Authority API Audit — v0.1R

**Inspected:** 2026-07-30  
**Purpose:** freeze the narrowest honest ordinary-battle action-observation boundary before any live capture or command-authority experiment.

## Primary sources inspected

- WH3 Battle Manager documentation: `register_command_handler_callback`, `register_unit_selection_callback`, real-time callbacks, and phase callbacks.
- WH3 Battle code-interface documentation: command-handler events may originate from player or script and do not expose a trustworthy origin field.
- WH3 Battle Unit documentation: local unit query interfaces including controllability, player/AI/script control, movement, idle/leaving/routing/shattered state, ordered position, current target, visibility, and `can_reach_position`.
- Battle Unitcontroller documentation: order issue requires a controller that takes control and exposes move/attack/withdraw/halt operations.

Canonical URLs are recorded in `research/SOURCE_LEDGER.md`. No third-party code was copied.

## Findings

1. A command callback proves only that the game emitted a command event matching the registered command name.
2. The callback does not prove player origin, script origin, acceptance, direct acknowledgement, execution, or outcome.
3. Selection callbacks can provide a contemporaneous local-unit binding in ordinary live battle, but Battle 4 replay produced zero direct selection events; absence must remain explicit.
4. Unit state can be queried after a command event. Ordered-position, current-target, movement, withdrawal, and control-state matches are observational evidence only.
5. `can_reach_position` is a point-in-time engine query for a position. It does not prove route safety, formation feasibility, arrival, or successful command execution.
6. Issuing orders belongs to the unitcontroller boundary. v0.1R creates no unitcontroller and contains no order call.

## Canonical claim separation

```text
candidate action
  ≠ game command event observed
  ≠ project issue attempt
  ≠ direct acknowledgement
  ≠ matching subsequent state
  ≠ execution caused by the project
  ≠ outcome caused by the project
```

## Design consequence

v0.1R may prepare a read-only ordinary-battle capture that observes command events and local-unit state. It may not promote command issue, acknowledgement, execution, or outcome. Any later authority experiment requires separate explicit owner authorization, an isolated sandbox, legality and fairness gates, rollback, and a new evidence contract.
