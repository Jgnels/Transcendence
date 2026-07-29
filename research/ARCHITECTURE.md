# Architecture

## Working layers

1. Game data, campaign, battle and UI adapters.
2. Immutable observation snapshots.
3. Strategic director.
4. Operational army director.
5. Tactical commander where control is proven.
6. Validation, fairness and execution gates.
7. Telemetry and outcome evaluation.
8. Offline synthetic labs and surrogate models.

## First vertical slice after Gate 0

Army Objective Assignment in shadow mode:

- observe;
- infer threats/opportunities;
- generate candidate roles and targets;
- score and assign;
- log reasons;
- do not mutate game state;
- compare proposals with outcomes.

This slice is provisional until the capability gate confirms the required observations.
