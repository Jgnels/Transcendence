## v0.2P pre-SFO mechanistic interpretation layer

v0.2P adds an **offline evidence-routing layer only**:

`fresh SFO diagnostic trace -> unchanged v0.2N endpoints -> territorial/non-territorial stratification -> faction-cluster descriptive diagnostics -> frozen direction-aware decision table -> replication nomination only -> separately preregistered minimal native-row ablation if later earned`

It does not alter the diagnostic probe or the application architecture. SFO row deltas are candidate mechanisms, not controllers. The captured SFO CAI footprint has no decoded allocator-variable override, so recovery differences cannot be directly assigned to those allocator rows. All prepared task-priority candidates are dormant and application-ineligible.

## v0.2N confirmatory diagnostic-study layer

v0.2N sits entirely on the **development diagnostic plane**. It does not change the application planner/executor or the player-visible information contract.

`native WH3 CAI execution -> privileged read-only faction-turn + pending-battle telemetry -> preregistered recovery/temporal evaluator -> causal review -> narrow native-row ablation if earned`

The pending-battle listener records only side/faction/character-CQI/military-force-CQI identity from the documented cache. It issues no campaign or battle commands. Confirmatory evaluation requires the probe to declare that battle telemetry surface, so older no-battle-channel logs cannot masquerade as battle-free evidence.

The recovery endpoint studies damaged-army attacker-side re-entry; defender-side battles are separated. The temporal endpoint studies repeated realized movement reversals under stable observed own context and excludes any force with recorded battle participation across the candidate window. Neither endpoint reveals native task identity, assignment memory or internal hysteresis.

A positive result changes only the **research queue**: causal review, then a mechanistically narrow current-native DB ablation. It does not promote project-owned planning. Privileged state is never an application input.

## v0.2M research/application telemetry separation

Transcendence now distinguishes **development observability** from **application information authority**.

`APPLICATION PLANE`: WH3 native CAI execution -> player-visible observation -> evaluator/tuner -> bounded correction if earned. Hidden foreign state is not an application input.

`RESEARCH DIAGNOSTIC PLANE`: read-only privileged WH3 telemetry -> offline evaluator -> preregistration design / native-row experiment design only. Every artifact is `PRIVILEGED_OMNISCIENT_DIAGNOSTIC`, `application_eligible=false`, `NO_ORDERS`, `PROHIBITED`.

The diagnostic plane may never be imported as a runtime decision source. Its existence does not weaken D104 for normal observation or application.

## 2026-08-02 authoritative post-review architecture

**This section supersedes older v0.2E-I application-path descriptions below; those sections remain preserved as historical implementation documentation.**

Default application architecture:

`Native WH3 CAI planner/executor → observer-safe Transcendence telemetry → independent evaluator/diagnosis → bounded native DB tuning → narrowly bounded script correction after measured failure → project-owned strategic control only after native+tuning falsification`

- v0.2E: evaluator/oracle.
- v0.2F: portfolio metrics/evaluator; not the default application controller.
- v0.2G assignment: evaluator; remove from default application path.
- v0.2G temporal commitment: churn/hysteresis hypothesis only; `2–4` turns and `0.15` are uncalibrated.
- v0.2H: preserve query catalog/capability labels/authority firewall/observation packets; generalize away from hypothetical project assignments.
- v0.2I: paused; preserve limiting-result evidence and do not continue assignment-derived transport.

See `research/NATIVE_CAI_RECONCILIATION_DECISION_2026-08-02.md` and `gates/GATE_0_NATIVE_CAI_RECONCILIATION.md`.

**Historical-boundary rule:** any later section that describes v0.2F/v0.2G/v0.2H/v0.2I as a controller, allocator, “current chain,” or next application step is implementation history only. It cannot be used as active application authority without a newer explicit evidence-backed decision that falsifies the native-first path.

## Historical v0.2I-r2 live feasibility parser contract (paused)

The live feasibility transport now treats the append-log event vocabulary as an explicit interface between the game-side probe and local sidecar. Every statically emitted `TRANS_PROBE` event in the dedicated feasibility Lua must be present in the shared parser allowlist. The generic session validator must also understand `campaign_feasibility` as a snapshot-bearing read-only probe kind. This prevents observability instrumentation itself from breaking the control pipeline. The r1 game-side real/UI timer remains unchanged.

# Architecture

## Historical v0.2I-r1 live feasibility transport correction (paused)

The campaign-feasibility bridge is asynchronous: the game emits a first-tick observer snapshot, an external sidecar derives one exact v0.2H plan, then the game reads the generated request. Because the owner workload deliberately leaves the campaign model idle, transport polling is now scheduled by `repeat_real_callback` (UI updates) rather than `repeat_callback` (campaign-model time). One immediate poll minimizes races, and one-shot poll/request-seen markers make transport progress observable. This is lifecycle plumbing only; it does not change strategic policy, query semantics, or order authority.

## Historical v0.2I live campaign-feasibility observation boundary (paused)

The current campaign evidence path is:

`first-tick observer-safe snapshot → local deterministic v0.2E→v0.2H reconstruction → exact bounded request → hard-coded in-game read-query whitelist → append-only result packet → independent offline reconstruction/adjudication`

The dedicated campaign-feasibility probe deliberately separates **query selection** from **query execution**. The Lua runtime does not invent a strategic target or choose a query family: a local sidecar derives one current v0.2G assignment using canonical project code, builds the exact v0.2H plan, and writes at most 16 plan-bound query IDs. The Lua executor accepts only a fixed read-only whitelist and rejects stale turns or unknown query keys.

The first-tick snapshot avoids requiring a turn advance, movement, battle, or save merely to obtain current evidence. If that current state produces no v0.2G assignment, no request is written and no feasibility query is executed. This is a valid limiting observation rather than permission to manufacture an objective.

The collector independently reconstructs the selected plan from the raw observer snapshot before accepting query results. `QUERY_TRUE`, `QUERY_FALSE`, and unavailable/error observations remain point-in-time query evidence only. Authority remains `NO_ORDERS`; application remains `PROHIBITED`; route geometry, zones of control, interception, action legality, acknowledgement, execution, and outcome remain outside this layer.

## Historical v0.2H campaign feasibility/action-authority boundary

The historical campaign reasoning chain was:

`observer-safe campaign snapshot → v0.2E challenge envelope → v0.2F theater portfolio → v0.2G exclusive army assignment/commitment → v0.2H read-only feasibility query plan → later live query observation → only then a separately authorized application sandbox`

v0.2H is deliberately a **query-contract layer**, not a route planner or controller. It binds a shadow assignment to stable actor CQIs and generates only the query shapes appropriate to the source target. REGION targets can resolve to their settlement interfaces for reachability questions; FACTION targets retain only their observer-safe reference centroid and cannot silently become a concrete attack target.

Documentation-derived model-hierarchy queries are kept structurally separate from episodic/campaign-manager mutation surfaces. An observed true reachability boolean would still establish neither route geometry nor command legality, acknowledgement, execution, or success. Every application surface remains outside the architecture at this gate.

## Historical v0.2G campaign force-allocation and temporal-commitment layer (evaluator only)

The historical campaign reasoning chain was:

`observer-safe campaign snapshot → v0.2E challenge envelope → v0.2F strategic/theater portfolio → v0.2G exclusive army assignment → v0.2G temporal commitment lifecycle → later campaign feasibility/action-authority envelope`

v0.2G is an allocation layer, not a movement controller. It expands bounded critical overflow before assignment, protects recovery and reserve capacity, ranks controlled actors against observer-safe reference anchors, exposes force shortages, and then retains valid actor/priority commitments across consecutive turns. Actor exclusivity is represented by one abstract `ARMY_STRATEGIC_COMMITMENT_SLOT` per planner-eligible field army.

The assignment solver is deterministic severity-first greedy arbitration. Straight-line distance divided by movement is a geometric comparison feature only; it is not a campaign route or reachability model. The temporal layer prevents geometry-driven oscillation through a project-owned 2-turn minimum commitment, 4-turn review window, and 0.15 material score margin. These values are hypotheses until longitudinal WH3 calibration exists.

No runtime campaign adapter is imported. Assignment remains `SHADOW_PROPOSED_NOT_EXECUTED`, route state remains `NOT_EVALUATED_GEOMETRIC_REFERENCE_ONLY`, authority remains `NO_ORDERS`, and application remains `PROHIBITED`.

## v0.2F strategic/theater portfolio layer

`observer-safe campaign snapshot → v0.2E challenge envelope → bounded strategic priority candidates → severity/value arbitration → explicit critical overflow → aggression veto → later theater-to-army assignment`

The v0.2F layer intentionally stops before force assignment. It represents front stabilization, siege-relief coverage, field-force recovery, coherent-rival containment, fragmented-pressure management, strategic reserve, and low-pressure consolidation as project-owned priorities. A six-record budget bounds strategic workload; when critical fronts exceed that budget, five are represented directly and the sixth record carries every omitted critical source ID. This prevents awareness loss without inventing an executable plan.

A front crisis or a state in which every controlled field army is below the frozen recovery threshold disables new aggressive commitment. Rival-awareness priorities may remain visible for planning continuity, but `selected_aggressive_priorities` is empty while the veto is active. War count never creates one commitment per enemy, and visible faction IDs identify observer-safe rival records without using human/player identity as a utility feature.

## v0.2E strategic challenge benchmark layer

`observer-safe campaign snapshot → visible rival/front diagnostics → strategic challenge envelope → adversarial/metamorphic benchmark → later strategic/theater portfolio`

This layer sits above raw campaign observation and below any strategic director that could eventually propose objectives. It deliberately contains no game adapter. Hidden hostile armies are filtered by the existing campaign contract before evaluation; human/player identity is not a quality feature; war count is descriptive rather than rewarded; same-faction co-location is recorded without inferring command coordination. The layer defines what a later director must preserve—coherent rival candidates, meaningful fronts, fairness, and recovery review—before adding theater assignment, diplomacy, HTN/search, or learned ranking.

The v0.2E thresholds are benchmark definitions only. Durable rival power requires longitudinal economy, recruitment, diplomacy, targeting, and outcome evidence. Campaign application remains a separate authority boundary.

## v0.2C replay-lifecycle authority guard

`exact private capture → public-safe capture/unit fixtures → strict nonterminal validation → lifecycle adjudication → bounded crisis/loss calibration`

A replay trace may enter terminal-outcome logic only after an observed `BATTLE_COMPLETE` or a separately bound live result artifact. Process exit, stable log bytes, replay-overlay exhaustion, and replay-exit summary screens are transport/lifecycle facts—not outcome evidence. Incomplete reports emit `UNVERIFIED_INCOMPLETE_SESSION`. This guard precedes utility scoring and prevents a simulator/replay artifact from becoming canonical outcome truth.

## v0.2B exact defeat-preparation layer (historical)

`private replay hash + private visual descriptor → strict public-safe visual contract → deterministic defeat-capture readiness → exact read-only schema-2 capture → later telemetry/visual adjudication`

The visual stage may identify ordered phases and bounded hypotheses but cannot supply canonical unit state, command acknowledgement, execution causality, or optimal policy. The runtime capture accepts either the dedicated replay pack or the exact frozen shadow container only when the outer pack hash and byte-identical battle-script hash are both bound. It does not grant either container order authority.


## Product layers

1. Vanilla WH3 data/campaign/battle/UI adapters.
2. Optional environment profiles: SFO first, then personal-stack profiles.
3. Immutable observer-safe snapshots.
4. Strategic director.
5. Operational army director.
6. Tactical commander only where control is proven.
7. Validation, fairness, and execution gates.
8. Telemetry and outcome evaluation.
9. Offline SyntheticLab tiers and Reality Gate R0.

## Dependency rule

Core reasoning consumes semantic concepts such as army strength, unit role, settlement value, threat, movement, replenishment, diplomatic state, formation state, pressure, target suitability, ammunition, morale, and reserve status. It does not depend directly on SFO keys or values. Environment profiles map game/mod data into those concepts.

## Synthetic tiers

- Tier 0: contracts, privacy, visibility, deterministic digests.
- Tier 1: one-frame Army Objective Assignment.
- Tier 2: operational campaign surrogate.
- Tier 3: seeded ensemble robustness.
- Tier 4: uncalibrated tactical contracts.
- R0: real WH3 shadow observation.

## Reality Gate R0 boundary

R0 uses three isolated script-only packs:

1. **Observer:** frozen replicated baseline campaign observation with no saved-value or campaign mutation.
2. **Persistence:** frozen replicated proof that one disclosed project-owned integer survives a disposable save/reload.
3. **Combined shadow:** experimental read-only campaign input acquisition plus ordinary-battle telemetry. It has no campaign application packet, creates no battle unitcontrollers, and emits `SHADOW_NO_ORDERS` and `BATTLE_OBSERVATION_NO_ORDERS` artifacts.

The combined shadow pack contains two scripts under the appropriate WH3 loader paths:

- `script/campaign/mod/transcendence_shadow_probe.lua`;
- `script/battle/mod/transcendence_battle_probe.lua`.

The offline parsers are the sole components that promote log evidence into capability labels. A loaded script does not grant planner or order authority.

Evidence uses two digest concepts where useful:

- transport-sensitive digests preserve source paths/positions for traceability;
- semantic digests exclude transport metadata for behavioral comparison.

Strict replication still requires matching installed pack SHA-256 values. Semantic equivalence across different pack revisions is not exact replication.

## Pack and evidence path

```text
project-authored campaign + battle Lua
  → deterministic PFH5 builder
  → ignored dist/runtime_probe output
  → explicit owner-confirmed copy into WH3 data
  → manual launcher enablement
  → WH3 lua_mod_log.txt
  → private evidence copy + SHA-256
  → strict campaign and battle parsers
  → orderless campaign proposals + descriptive battle report
  → combined gate verifier
```

## Campaign vertical slice

Army Objective Assignment in shadow mode:

- observe at local-faction turn start;
- filter hidden information;
- infer threats and opportunities;
- generate candidate roles and targets;
- score and assign;
- log reasons and alternatives;
- do not mutate game state;
- compare proposals with later observed outcomes.

The offline contract, replicated baseline observer, replicated persistence path, and deterministic multi-turn adapter are implemented. Expanded fields remain unverified until the owner-machine run.

## Ordinary-battle telemetry slice

The battle slice is observational, not a tactical commander. It is designed to establish what an ordinary campaign battle exposes before any control architecture is chosen.

It records, where available:

- battle origin/type, unit scale, local alliance, time, phase, and result;
- alliance/army/unit hierarchy and static unit classifications;
- position, ordered position, bearing, movement, idle, melee, missile pressure, morale/routing, flank threats, health, men, kills, ammunition, target, and visibility;
- one-second alliance aggregates and three-second unit samples;
- selection and command-handler traffic;
- completion and winner/outcome fields.

Foreign unit records are emitted only while WH3 reports them visible to the local alliance. Hidden units receive no identity or state record. The script never creates a unitcontroller, sends an order, changes battle speed, writes a save value, changes visibility, or alters damage.

Command events are evidence that WH3 exposed command traffic. They are not acknowledgements, not proof of execution, and not proof that Transcendence can control units.

## Runtime lifecycle

Campaign evidence has two distinct phases:

1. `FIRST_TICK`: initialization diagnostics and capability discovery.
2. `LOCAL_FACTION_TURN_START`: canonical planner snapshot.

The battle script uses battle-manager phase callbacks and battle-model-synchronized repeating callbacks where the live runtime supports them. Every unsupported field must produce explicit capability evidence or a conservative fallback; it may not silently fabricate data.

## Data and authority

The runtime pack owns no canonical objective or tactical state and cannot issue orders. Offline adapters own only derived artifacts.

Campaign foreign entities originate from WH3 player-filtered lists. The first campaign policy avoids exact foreign force strength and foreign garrison composition.

Battle foreign units are visible-only. The current battle report may use engine strategic-value fields only as disclosed telemetry proxies, never as hidden authoritative valuation or a published recruitment-cost equivalent.

Prior campaign proposals are project-owned history supplied to the adapter. They are not inferred from attempted WH3 orders and are not persisted in this gate.

Region identity is canonicalized before the scenario reaches SyntheticLab. A controlled region may legitimately appear in both the owned-region and player-visible-region interfaces; those records are coalesced by stable region key, the owned record wins, cross-view overlap is counted, and owner conflicts or same-source duplicates fail closed.

## Consolidated live-test policy

Live tests are batched by authority boundary:

1. one combined read-only vanilla campaign-and-battle session;
2. one later combined read-only SFO compatibility session;
3. one separate campaign order-authority sandbox;
4. one separate battle order-authority sandbox, with generated and ordinary battle paths distinguished.

Campaign observation and ordinary-battle observation may share a session because both are read-only. Save mutation and game orders remain separate because they cross materially different safety and evidence boundaries.

## v0.1J cross-runtime evidence boundary

WH3 campaign and ordinary-battle scripts run in separate Lua environments. The shared mod loader's `ModLog` implementation opens `lua_mod_log.txt` with write/truncate mode on the first call in each runtime, then appends only within that runtime. A campaign → battle → campaign session therefore cannot rely on `lua_mod_log.txt` as one durable transcript.

The combined pack now uses two sinks:

1. `transcendence_runtime_log.txt` — project-owned append-only structured evidence shared across campaign and battle runtimes;
2. `lua_mod_log.txt` — secondary engine/mod-loader diagnostic output only.

A pre-session step archives and removes the previous append log, verifies staged/installed pack identity, and writes a prepared-session manifest. Live combined collection requires that manifest and refuses legacy-log fallback. Each runtime emits `PACK_LOADED` followed by `RUNTIME_BEGIN`, allowing the parsers to preserve runtime boundaries without merging sessions accidentally.

## v0.1J semantic force and garrison contracts

Army Objective Assignment consumes only planner-eligible field armies:

- `military_force:is_army() = true`;
- general `character_type_key = general`;
- at least one unit.

Embedded agents and other character forces are recorded as `SHADOW_FILTERED_FORCE` telemetry but receive no army objective. A one-general field army remains valid when the live explicit fields identify it as an army; the unit-count heuristic is used only to conservatively reprocess legacy logs that lack those fields.

Cross-faction feasibility must compare like-scaled values. The planner uses a disclosed unit-count-and-health proxy for controlled armies and visible unit count for foreign armies. Exact controlled-force strength remains in the observation envelope for telemetry and later calibration but cannot enter foreign-relative scoring.

Settlement garrison estimates accept unit evidence only from an armed-citizenry force. A normal field army occupying a settlement is not a garrison and cannot be counted twice. Otherwise, owned and foreign settlements use a disclosed structure proxy based on settlement level and walls.


## v0.1K observed-trace calibration layer

SyntheticLab now has a separate Tier **4R** path for reality regressions derived from real WH3 evidence. Tier 4R is not a simulator tier and does not use the owner trace as an optimal action label. It stores only public-safe derived facts and source digests.

```text
private replay + private TRANS_BATTLE log
  → strict parser and identity reconciliation
  → conservative outcome/lower-bound report
  → public-safe Tier 4R corpus
  → deterministic stress-case derivation
  → regression constraints for future tactical planners/simulators
```

The dense replay probe is a separate battle-only pack. Its scheduler uses a model-time callback and a UI/real-time callback, deduplicated by battle model time. Heartbeats prove callback continuity. Detailed samples occur every three seconds of model time and alliance aggregates every second. Metrics are fail-closed: path, engagement, routing, target-switch, fatigue, reserve, flank, and command-inference analysis is withheld unless coverage and maximum-gap criteria pass.

Unit identity uses `alliance_index + unique_ui_id`; current army and unit indexes are hierarchy observations. Direct selection callbacks provide observed command context. A bounded state-delta attribution layer may produce `INFERRED_NOT_ACKNOWLEDGED` candidates only when dense sampling is valid.


## v0.1L dense reality-slice and offline shadow-evaluator layer

The corrected Battle of Eilhart replay closes the dense telemetry calibration segment. SyntheticLab now consumes two public-safe observed artifacts:

1. the full dense Tier 4R corpus, containing aggregate curves, per-unit derived metrics, command traffic, and bounded inference labels;
2. eight compact state slices at deployment, contact, melee commitment, local crisis, enemy break, majority rout, victory countdown, and completion.

```text
private dense TRANS_BATTLE log
  → strict schema-2 parser
  → public-safe dense corpus
  → visibility-safe state slices
  → deterministic tactical stress benchmarks
  → no-order offline shadow evaluator
```

The shadow evaluator is deliberately below tactical command authority. It emits only bounded priority classes such as character preservation, frontline stabilization, ranged protection, cavalry disengagement, artillery extraction, visible-target comparison, and pursuit termination. It consumes no hidden enemy identity and issues no game order.

Direct selection callbacks were not replayed. Command attribution therefore has two explicit grades:

- direct callback attribution: absent in this replay;
- bounded state-change inference: `INFERRED_NOT_ACKNOWLEDGED`.

Observed owner commands are workload and situation evidence, not a gold policy. The evaluator is constrained to fewer priority changes than the raw human command stream and must remain deterministic and explainable.

## v0.1M tactical-state and decision-opportunity layer

The first planner-facing tactical representation is now explicit and versioned. It consumes only validated Tier 4R slices and produces immutable state plus advisory decision windows.

```text
visibility-safe observed slice
  → canonical observed unit record
  → deterministic support/pressure geometry
  → role-specific value, danger, recoverability, and engagement proxies
  → local-stability and visible-enemy-collapse state machines
  → bounded decision-opportunity candidates
  → six-per-slice advisory budget
  → counterfactual-safe diagnosis and quality metrics
```

The state contract is `TACTICAL_STATE_VISIBILITY_SAFE_V1`; the trajectory contract is `TACTICAL_STATE_TRAJECTORY_V1`. Hidden enemies remain a count only. Straight-line x/z distance is disclosed as a geometric proxy and cannot be promoted to pathfinding feasibility.

Responsibility remains layered:

- constraints enforce visibility, authority, privacy, legality, and counterfactual uncertainty;
- utility scores asset value, danger, recoverability, marginal engagement value, and visible target threat;
- state machines classify local stability, visible enemy collapse, and pursuit termination;
- assignment identifies reserve, screening, and safe-pursuit candidates;
- behavior trees wait for proven execution primitives and acknowledgement;
- HTN/search waits for a calibrated transition model;
- learning waits for heterogeneous observed cohorts and deterministic baselines.

A decision opportunity is not a selected order. Its alternatives are `PROPOSED_NOT_EXECUTED`, its counterfactual status is `UNVERIFIED`, and its authority is `ADVISORY_ONLY`. The full framework remains `NO_ORDERS`.

## v0.1N tactical contract hardening layer

v0.1N inserts a strict validation and lifecycle boundary ahead of future planner growth:

```text
untrusted/public-safe tactical slice
  → BATTLE_TRACE_TACTICAL_INPUT_V2 fail-closed validation
  → TACTICAL_STATE_VISIBILITY_SAFE_V2
  → local condition + independent tactical phase
  → candidate opportunities with stable opportunity_key
  → bounded per-slice selection
  → lifecycle-aware command-budget metrics
  → adversarial metamorphic verification
```

Validation owns raw type, range, consistency, identity, timing, and visibility-scope rules. Derived utility functions may clamp their own scores but may not repair malformed observations. This prevents permissive Python truthiness or numeric conversion from manufacturing tactical facts.

The state machine now separates:

- `local_stability_state`: condition of the local force;
- `visible_enemy_collapse_state`: condition of the observed enemy force;
- `tactical_phase_state`: the combined policy phase.

Enemy rout therefore cannot imply local recovery. The majority-rout Battle 4 slice remains `LOCAL_CRISIS` while the phase becomes `RECOVERY_REQUIRED`.

Per-slice opportunity instances retain unique IDs for auditability. Persistent concerns use a stable key composed from opportunity type, subject, and objective. Churn and command-budget accounting use the stable key, so an unchanged warning does not become a fictitious new command every sample.

The adversarial runner is a project-owned deterministic test harness. It has no authority over canonical state outside validated outputs and no path to WH3 runtime actions.

## v0.1O tactical priority portfolio and baseline matrix

```text
validated tactical state
  → all advisory opportunity candidates
  → group equivalent unit concerns by opportunity type
  → preserve source IDs, subjects, severity, utility, confidence, and limits
  → apply six-priority bound
  → explicit critical-overflow record when distinct groups exceed capacity
  → deterministic heterogeneous baseline comparison
```

The portfolio is an arbitration representation, not an assignment or sequence. Grouping prevents repeated same-type unit emergencies from consuming the entire advisory budget, while the overflow record prevents critical concerns from disappearing silently.

Synthetic fixtures share the strict unit/scope validator but retain `CONTROL_SYNTHETIC` evidence status. Observed and synthetic evidence are never merged. Baseline scores measure contract alignment and disagreement only; they do not establish tactical superiority.


## v0.1P tactical objective assignment and conflict-resolution layer

```text
validated tactical state + canonical bounded portfolio
  → verify digests, contracts, authority, counts, and exact source set
  → expand source opportunities into self-directed and support objectives
  → reject uncontrollable, protected, role-incompatible, or over-endangered actors
  → score legal actor/objective pairs
  → solve one UNIT_ACTION_SLOT per actor with deterministic tie-breaks
  → preserve assigned, unassignable, and resource-conflict results
  → NO_ORDERS advisory artifact
```

Self-directed objectives bind the subject as the only actor. Support objectives use role and source-pool constraints. The optimizer never invents a responder and never interprets straight-line distance as a valid terrain route. Assignment count is not command count, and the output is not an execution sequence.

## v0.1Q tactical temporal scheduling and abstract-transition layer

```text
canonical tactical state + canonical per-slice assignment
  → authenticity and monotonic-time validation
  → abstract plan lifecycle keyed by actor, objective, and action
  → minimum commitment + periodic review + maximum commitment
  → cancellation, supersession, cooldown, or observational retirement
  → continuity reset across observation gaps
  → NO_ORDERS temporal evidence
```

The scheduler is a state machine above assignment and below execution. Project-owned timing windows prevent synthetic thrashing but are not WH3 movement-time estimates. A later observation can retire a concern, but the scheduler never attributes that change to its unexecuted proposal. Qualitative transition envelopes define what future evidence should inspect without predicting paths, coordinates, casualties, or success.

Observation gaps greater than 30 seconds break continuity. Prior plans become unknown history rather than silently completed commands. Behavior trees, HTN/GOAP, and forward search remain deferred until legal action primitives, acknowledgements, and calibrated transition evidence exist.

## v0.1R read-only action-authority evidence layer

```text
ordinary single-player game command event
  → unresolved origin + contemporaneous local selection binding
  → exact local-unit state window
  → point-in-time reachability and ordered-position/current-target evidence
  → explicit interruption/close reason
  → strict verification against prepared exact-pack manifest
  → NO_ORDERS public-safe evidence packet
```

This layer is an observer, not an execution adapter. `battle_manager:register_command_handler_callback` supplies game command events, while battle-unit queries supply state. Unitcontroller creation and order calls remain absent. A state match is evidence that WH3 exposed a compatible state after a command event; it is not direct acknowledgement and receives no causal credit.

The future execution boundary remains physically and contractually separate. No behavior tree, HTN/GOAP, search, learned ranker, or LLM proposal may cross into order authority until an explicitly authorized sandbox proves legality, issue, acknowledgement, interruption, and rollback.


## v0.1S observed action-authority calibration layer

```text
public-safe schema-1 capture documents
  → exact member/hash/contract validation
  → cross-document count and authority reconciliation
  → capability-by-capability evidence adjudication
  → OBSERVED query/state promotions with explicit claim boundaries
  → NO_ORDERS live calibration artifact
```

The adjudicator treats selection binding as a useful ordinary-battle observation boundary, not as proof that the player rather than a script originated a command. Ordered-position, target, movement, routing, and control-loss matches remain state observations. Point reachability remains a point-in-time query. None of these become issue, acknowledgement, execution, route completion, or outcome attribution.

The v0.1S collector hardening adds a schema-2 public export containing a sanitized preparation attestation. It carries the exact staged/installed pack hashes and nonmutation flags while omitting runtime-log paths, installation paths, backups, usernames, and other private fields. Schema-1 evidence remains valid but its private prepared manifest cannot be independently replayed from the public packet.

## v0.1T bounded tactical feasibility layer

```text
canonical tactical state + canonical active abstract schedule
  → bounded role-aware candidate-point generator
  → optional exact point-query evidence binding
  → point-supported / exact-point-rejected / unavailable / unobserved envelope
  → NO_ORDERS planner-development evidence
```

The envelope sits below temporal scheduling and above any future execution adapter. Aggregate query availability is calibration metadata, not per-plan evidence. No candidate may become a route, formation, legal command, acknowledgement, execution, or outcome without a separate authoritative contract.

A separate no-replay re-export path reads the owner-preserved private v0.1S log, verifies exact source identities, and emits only public-safe detailed windows. This path does not launch WH3 or install a pack.

## v0.1U semantic command-point calibration layer

```text
verified detailed action windows
  → command-modality classification
  → explicit point / visible unit target / opaque callback separation
  → raw reachability preserved
  → semantically qualified point reachability
  → corrected capability profile
  → Battle 4 candidates remain unqueried
```

The calibration sits between runtime evidence ingestion and the tactical feasibility capability profile. It does not change historical v0.1S/v0.1T artifacts. Instead, it separates what the engine returned from what the callback semantically represented.

Only an explicit finite nonzero `Move` callback destination qualifies as point evidence in the captured vocabulary. `Attack Unit` contributes visible-target state matching, while `Move Orientation Width`, `Double Click`, and `Special Ability` remain opaque or non-point callbacks. Raw queries against their zero-vector fields are retained as telemetry but cannot support point feasibility.

This layer deliberately does not infer a false-point rate. The current capture contains 191 qualified true samples and zero qualified false samples. Any planner component that requires observed false-point calibration must remain synthetic or unverified.

## v0.1V guarded readiness layer

The feasibility envelope now feeds a guarded packet layer rather than any command adapter. This layer authenticates the complete state/schedule/geometry source, classifies readiness, and fixes application authority to `PROHIBITED`. Exact-point support is necessary for readiness but never sufficient for route, legality, acknowledgement, or execution.

## v0.1W simultaneous endpoint layer

Ready packets feed an endpoint reservation layer. Its only spatial guarantee is minimum horizontal distance between selected endpoint coordinates. It has no route graph, formation footprint, collision mesh, terrain model, or controller. Exact optimization is bounded; deterministic fallback is explicit rather than hidden behind an optimality claim.

## v0.1X robustness boundary

The complete offline tactical chain is now exercised by a deterministic fuzz and structural-scaling harness. Representation order and global coordinate origin are nonsemantic. Stable optimization tie-breaks therefore use project identities and canonical ranks, never coordinate-derived hashes. All learned or future planning components must enter above the same source-authentication and authority barriers.

## v0.1Y SFO-bound evidence architecture

The SFO combined-session layer sits outside the planner and remains read-only:

`launcher-owned load order → environment attestation → append-only campaign/battle probe → private prefix checkpoints → strict combined verifier → path-free public export`

The environment attestation binds one exact SFO pack and WH3 executable. The checkpoint watcher observes only the project log and never controls WH3. A passing result promotes scoped observation compatibility and transport continuity only; no planner state, order authority, acknowledgement, or outcome claim flows backward from this layer.

## v0.2A replay-visible calibration layer

```text
exact private replay/video hashes + public-safe dense telemetry
  → strict visual-alignment contract
  → replay/runtime/display identity separation
  → ordered nonoverlapping phase alignment
  → role, force-discovery, crisis, outcome, and terminal contrast
  → deterministic bounded calibration rules
  → NO_ORDERS SyntheticLab artifact
```

This layer is an evidence adapter above observed telemetry and below tactical policy development. It carries no video bytes, image frames, replay bytes, paths, or game assets. Visual evidence may add display identity, broad geometry, phase context, and visible outcome. It may not rewrite runtime identity or promote movement to acknowledgement or causal execution.

The derived rules are constraints on later candidate scoring and state machines, not learned policy labels. In particular, force discovery must stabilize before full-army assumptions, local crisis remains independent from visible enemy collapse, and terminal states prohibit new high-commitment objectives. Any future learned ranker or LLM receives only validated project-owned outputs and remains advisory.

## v0.2D cross-corpus tactical policy layer

A pure offline policy layer now sits above frozen observed-battle/calibration artifacts and below any future tactical proposal/application interface. It has two project-owned components:

1. `tactical_policy.py` validates exact provenance, derives cross-corpus summaries/rules, and evaluates bounded observation snapshots;
2. `tactical_policy_matrix.py` adversarially tests those contracts, including representation invariants and fail-closed inputs.

The layer has no runtime imports, no game API adapter, and no order-authority surface. Its output is review/abstention metadata only. A future executor, if ever authorized, must remain a separate adapter behind legality, capability, fairness, acknowledgement, and outcome contracts.


## v0.2J native-first behavior observation layer

```text
current native CAI remains planner/executor
  → observer-safe longitudinal campaign snapshots
  → optional observed engagement events with engagement-time replenishment
  → threatened-front coverage/latency + home-zone buffer proxy
  → movement-only target/retarget proxies
  → explicit unavailable native task-memory/exclusivity/hysteresis fields
  → evidence for native/tuning falsification, never order authority
```

This layer replaces the old assumption that a project-owned assignment must exist before native strategic quality can be evaluated. It reuses v0.2E's observer-safe front representation but does not call v0.2G to decide what native armies *should* be doing. A trajectory may falsify a native behavior hypothesis; it may not prove undocumented engine internals from silence.

The v0.2J detector intentionally has no runtime import or collection adapter. Observation acquisition is a separate gate so visibility/completeness, provenance, and authority can be validated before real data enters the evaluator.

## v0.2K player-visible native behavior acquisition boundary

v0.2K separates the ideal full-information behavior metrics defined in v0.2J from what the normal owner-safe observer can actually know about foreign AI factions. The application architecture remains native-first. The normal observer may use only WH3 player-filtered foreign characters/regions; it does not enumerate arbitrary AI faction force lists simply because the scripting hierarchy can expose them.

The new path is:

`WH3 native CAI -> WH3 player-visible foreign state -> partial trajectory adapter -> native behavior review candidates`

It is not:

`WH3 native CAI -> hidden foreign state -> project assignment reconstruction`.

Under partial visibility, position stability, movement direction, visible-anchor direction changes, and visibility transitions are measurable proxies. Full front coverage, reserve adequacy, recovery misuse, native task identity, assignment exclusivity, native memory, and hysteresis remain unavailable unless a later evidence contract closes those gaps without violating authority/visibility rules.

## v0.2L preregistered native directional-churn falsification layer

v0.2L adds a conservative confirmatory layer above v0.2K player-visible traces and below any native-row modification. It does not infer WH3 task IDs or compare native movement to v0.2G's preferred assignments.

Pipeline:

`native CAI execution -> WH3 player-filtered visible trace -> v0.2K movement/direction proxies -> v0.2L repeated stable-context region oscillation endpoint -> evidence adjudication -> bounded native-row ablation if mechanistically earned`

The primary endpoint requires two non-overlapping A→B→A region-direction episodes for the same actor/region pair, with >=120-degree heading reversals and exact stability of every observed non-target anchor. This deliberately trades sensitivity for specificity.

Architecture invariants:

- `NO_ORDERS`;
- application `PROHIBITED`;
- no hidden full-faction enumeration;
- no import from strategic assignment/commitment application modules;
- one oscillation episode is candidate-only;
- no-signal results do not prove native memory/hysteresis;
- positive signal may at most earn a bounded native-tuning experiment, not project strategic ownership.

## v0.2O behavior-adjudication refinement

Native-first application ownership remains unchanged. Diagnostic evaluation now distinguishes `TERRITORIAL_FACTION_WINDOWS` from `NON_TERRITORIAL` roaming/patrol windows for strategic temporal interpretation. This is an evaluator population boundary, not an application input or planner feature.

A formal behavior signal must survive causal review before it can nominate tuning. The v0.2N repeated reversal endpoint fired, but its sole repeated trigger is plausibly explained by special Rogue Pirate patrol behavior, so no ordinary CAI row is changed. The next layer is a hash-bound SFO benchmark using the same read-only probe; differences can nominate a narrow ablation only after mechanism review.


## v0.2Q benchmark-adjudication architecture boundary

The first SFO behavior benchmark does not change application architecture. Native WH3 CAI remains the strategic planner/executor. SFO profile differences are research evidence only. The frozen descriptive worsening branch blocks copying SFO priority increases; the subsequent composition review blocks causal row attribution. Replication is staged before any mechanism-selection experiment. Privileged diagnostic telemetry remains outside the application plane; v0.2G/v0.2I remain evaluator/history only.
