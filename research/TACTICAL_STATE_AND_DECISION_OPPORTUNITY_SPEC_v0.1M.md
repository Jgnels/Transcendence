# Tactical State and Decision Opportunity Specification — v0.1M

## Purpose

This specification defines the first canonical planner-facing tactical state and decision-opportunity contracts for Transcendence.

The implementation consumes the frozen, public-safe Battle 4 Tier 4R trace slices. It does not read the replay or raw owner log, does not create a unitcontroller, and does not issue or validate a game order.

Classification:

- input state: `OBSERVED` public-safe trace slices;
- derived state: `DERIVED_FROM_OBSERVED_INPUT`;
- decision opportunities: `HYPOTHESIS`;
- authority: `NO_ORDERS`;
- counterfactual alternatives: `UNVERIFIED`.

## Planner-facing state contract

The canonical state contract is `TACTICAL_STATE_VISIBILITY_SAFE_V1`. A trajectory of states uses `TACTICAL_STATE_TRAJECTORY_V1`.

Each state contains:

1. exact source slice identity and time;
2. the local-unit count, visible-enemy-unit count, and hidden-enemy count;
3. explicit capability limits for terrain-aware pathfinding, line-of-sight geometry, and enemy reserve completeness;
4. one normalized record per observed unit;
5. role-specific policy thresholds;
6. deterministic derived risk, value, support, recoverability, and engagement proxies;
7. local-stability, visible-enemy-collapse, and outcome states;
8. evidence and authority labels;
9. a deterministic result digest.

### Observed unit fields

The state preserves only fields already present in the visibility-safe slice:

- stable unit identity;
- type, class, role, and alliance;
- visibility source;
- position, ordered position, bearing, ordered bearing, and ordered width;
- hitpoint and model fractions;
- ammunition and starting ammunition;
- fatigue;
- idle, movement, melee, routing, shattered, wavering, leaving, and rampaging flags;
- missile and flank pressure flags;
- current visible target fields;
- missile range, commander status, special-ability count, and disclosed strategic-value proxies.

Foreign unit detail is accepted only when the source is `VISIBLE_TO_LOCAL_ALLIANCE`. Hidden units contribute only an integer incompleteness count.

### Derived unit fields

Derived fields are deterministic and intentionally bounded:

- model fraction;
- ammunition fraction where starting ammunition is nonzero;
- normalized fatigue severity;
- straight-line nearest-friendly and nearest-visible-enemy distances;
- friendly support and visible-enemy pressure counts within 90 meters;
- support balance;
- asset-value score;
- danger score;
- withdrawal-recoverability proxy;
- collapse-risk score;
- marginal-engagement-value proxy;
- change since the previous milestone.

These are not engine facts. In particular, straight-line distance is not a terrain path, and withdrawal recoverability does not prove WH3 can execute the movement.

## Role-specific preservation policies

The evaluator does not use one universal health threshold.

### Commander

- highest survival priority;
- preservation begins before terminal health;
- continued engagement requires unusually high visible marginal value;
- campaign and leadership value justify early extraction consideration.

### Artillery

- high productive value and poor recovery after contact;
- model preservation threshold is stricter than frontline infantry;
- screening and evacuation are evaluated before prolonged melee exposure.

### Ranged

- value depends on retained models, ammunition, firing opportunity, and freedom from melee or flank pressure;
- repositioning can dominate continued firing when exposure becomes persistent.

### Cavalry

- fatigue, isolation, and model loss are treated as overextension indicators;
- disengagement and reformation are evaluated before repeated low-value pursuit.

### Frontline

- accepts more bounded attrition than high-value specialist roles;
- relief is triggered by formation or morale-collapse risk, not simply by any damage;
- holding for delay remains a valid alternative only when it protects greater value.

## Battle-level state machines

### Local stability

The local force transitions among:

- `STABLE`;
- `PRESSURED`;
- `LOCAL_CRISIS`;
- `RECOVERABLE_COLLAPSE`;
- `IRREVERSIBLE_COLLAPSE`;
- `RECOVERY_REQUIRED` after visible enemy rout dominance;
- `TERMINAL` after battle completion.

The classification combines weighted integrity, routing, wavering, melee commitment, flank pressure, missile pressure, and high-value asset risk. One routing unit does not automatically imply army collapse.

`IRREVERSIBLE_COLLAPSE` requires a deliberately severe combination of low integrity and broad morale failure. Battle 4 never enters that state.

### Visible-enemy collapse

The visible enemy transitions among:

- `CONTESTED`;
- `PRESSURED`;
- `BREAKING`;
- `ROUT_CASCADE`;
- `TERMINAL_COUNTDOWN` when the visible result is effectively irreversible and no hidden units remain;
- `TERMINAL`.

This state is limited to the observed visible scope.

## Decision-opportunity contract

A decision opportunity is not an order. It records:

- a stable opportunity ID;
- opportunity type and scope;
- subject units;
- severity and utility score;
- observed triggering state;
- disclosed derived metrics;
- tactical diagnosis;
- multiple proposed alternatives and tradeoffs;
- confidence and limitations;
- expiry conditions;
- `UNVERIFIED` counterfactual status;
- `ADVISORY_ONLY` authority.

Implemented opportunity types are:

- `COMMANDER_EXTRACTION_WINDOW`;
- `ARTILLERY_EVACUATION_WINDOW`;
- `RANGED_REPOSITION_WINDOW`;
- `CAVALRY_DISENGAGEMENT_WINDOW`;
- `FRONTLINE_RELIEF_WINDOW`;
- `LOCAL_ROUT_CONTAINMENT_WINDOW`;
- `RESERVE_COMMITMENT_WINDOW`;
- `SELECTIVE_PURSUIT_WINDOW`;
- `PURSUIT_TERMINATION_WINDOW`;
- `REFORM_AND_PRESERVE_WINDOW`.

A proposed alternative is always labeled `PROPOSED_NOT_EXECUTED`. The framework never claims that the alternative would have caused a better outcome.

## Pursuit policy

General pursuit should stop when visible enemy resistance has entered a rout cascade and endangered or exhausted local units have more preservation value than marginal cleanup value.

The evaluator may still propose bounded specialist pursuit when:

- the pursuer is coherent and sufficiently fresh;
- the visible target remains tactically meaningful;
- danger and distance remain bounded;
- no stronger preservation need dominates.

The current contract cannot model campaign capture consequences, terrain traps, hidden reserves, or pathfinding execution.

## Command-budget contract

Each slice may select at most six advisory opportunities. Candidates are ranked by severity, utility, and stable identity. The evaluator reports:

- candidate and selected opportunity counts;
- suppressed opportunity count;
- critical-opportunity coverage;
- new and retired selected priorities;
- total advisory priority transitions across the trace;
- an optional comparison with observed owner command-event count.

The comparison is `REFERENCE_ONLY_NOT_CAUSAL`. Fewer advisory transitions do not prove that fewer commands would win or save more units.

## Outcome-independent tactical-quality dimensions

Future planners should be measured using dimensions that do not collapse into win/loss:

- high-value asset preservation;
- avoidable high-danger exposure duration;
- frontline and morale stability;
- reserve timing;
- ranged output and ammunition preservation;
- pursuit termination discipline;
- high-severity opportunity coverage;
- command or priority churn;
- legality, visibility, and fairness compliance.

Causal casualty reduction, accepted-command latency, pathfinding success, and SFO or ordinary-live-battle generalization are not yet measurable.

## Architecture allocation

v0.1M assigns responsibility as follows:

- **constraints:** visibility, privacy, authority, legality, and counterfactual uncertainty;
- **utility:** asset value, danger, recoverability, marginal engagement value, and visible-target threat;
- **state machines:** local stability, visible-enemy collapse, and pursuit termination;
- **assignment:** reserve suitability, screening candidates, and safe pursuit candidates;
- **behavior trees:** deferred until execution primitives and acknowledgement exist;
- **HTN/search:** deferred until a calibrated transition model can compare multi-step alternatives;
- **learning:** deferred until heterogeneous battle cohorts and deterministic baselines exist.

## Promotion boundary

Passing this specification establishes deterministic offline consistency over one observed vanilla land battle. It does not establish:

- command authority;
- command acceptance or success;
- causal loss prevention;
- pathfinding feasibility;
- tactical superiority;
- ordinary live campaign-battle equivalence;
- SFO compatibility;
- cross-faction or cross-battle generalization.
