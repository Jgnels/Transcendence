# Native CAI Diagnostic Telemetry Boundary — v0.2M

**Status:** `PRIVILEGED_RESEARCH_PLANE_PREPARED`  
**Authority:** `NO_ORDERS`  
**Application authority:** `PROHIBITED`

## Trigger

The owner v0.2L vanilla capture was technically sound for instrument evaluation but yielded zero primary-eligible player-visible churn windows. Exact derived evidence is frozen in:

`research/runtime_evidence/NATIVE_CHURN_VANILLA_OWNER_CAPTURE_REPROCESS_v0.2M.json`

Observed bottleneck:

- 14 consecutive Reikland snapshots;
- 187 four-frame actor windows;
- 149 excluded by player-visibility censoring;
- 38 excluded because the continuously visible army was non-directional/stationary;
- 0 eligible stable-context region windows.

Therefore D109 fires: no SFO v0.2L run is requested.

## Two-plane observation policy

### Application plane

`PLAYER_VISIBLE_ONLY`

This remains the fairness boundary for anything that could eventually affect gameplay. Hidden enemy forces, tasks, economy, and other omniscient state are not application inputs.

### Development diagnostic plane

`PRIVILEGED_OMNISCIENT_DIAGNOSTIC / APPLICATION_INELIGIBLE`

A separate read-only probe may inspect complete AI faction forces solely to measure and debug native behavior offline. Diagnostic artifacts may influence research questions and native row-tuning experiments, but their raw hidden state is forbidden as a runtime application dependency.

This separation avoids conflating *development observability* with *shipping AI information advantage*.

## Documented scripting surface

WH3's scripting documentation states that `FactionTurnStart` and `FactionTurnEnd` contexts expose a faction interface, and `FACTION_SCRIPT_INTERFACE:military_force_list()` returns all military forces in that faction. v0.2M uses that surface only in the privileged research probe.

## v0.2M purpose

v0.2M is **not** a churn-hypothesis rerun. It qualifies whether this research channel yields enough paired AI-turn and movement exposure to support a new preregistration.

Frozen minimum exposure:

- `paired_faction_turn_count >= 20`
- `matched_force_turn_pairs >= 50`
- `moved_force_turn_pairs >= 10`
- `trajectory_exposure_pairs >= 5`

No threshold may be changed after seeing the first owner diagnostic capture for the purpose of declaring that same capture qualified.

## Data captured

At each non-human faction turn start/end, the research probe attempts to record:

- complete field-army list;
- stable force/general CQIs;
- map position and region;
- unit count;
- force strength;
- mean unit health;
- remaining action-point percentage;
- stance;
- owned regions and siege state;
- current wars.

Human faction events emit round markers only.

## Interpretation limits

- Hidden-state telemetry does not become an application input.
- A force absent at one endpoint is not automatically labeled destroyed, disbanded, merged, recruited, or reassigned.
- A heading reversal is descriptive exposure only at v0.2M; it is not the v0.2L endpoint and is not evidence of task churn.
- Native task identity, assignment memory, and engine-internal hysteresis remain unobserved.
- No diagnostic result can directly authorize a project-owned planner.
