## v0.2P SFO benchmark hardening

The v0.2O campaign protocol and v0.2N endpoint thresholds remain unchanged. v0.2P additionally requires: faction-cluster descriptive diagnostics; leave-one-faction-out sensitivity; no p-value treating overlapping windows as independent; application of the frozen post-SFO decision table digest `6493a5df13c4703bf9e16febf825c6ad0764c7127fae308e1b0856a3e355de74`; and mechanistic attribution constrained by the captured SFO row footprint. The v0.2P benchmark spec digest is `8efd88f7a07272d6eb45f4a298f2b8519e10435323bc3ca56e0b2374c70f0db7`.

## v0.2I-r2 parser-contract benchmark

A valid release must prove: (1) all static event names emitted by `transcendence_campaign_feasibility_probe.lua` are accepted by `parse_probe_log.py`; (2) a synthetic `campaign_feasibility` session containing first-tick snapshot, `FEASIBILITY_POLL_TICK`, and `FEASIBILITY_REQUEST_SEEN` parses and summarizes successfully; (3) the dedicated probe pack remains byte-identical to r1; and (4) authority remains `NO_ORDERS` / application `PROHIBITED`.

# Benchmark Specification — v0.1J

## v0.2I-r1 live transport benchmark

A valid live-feasibility preparation now additionally requires: (1) no model-time polling dependency for the asynchronous request, (2) one immediate poll, (3) UI-synchronized real polling while idle, (4) a one-shot poll marker, (5) a one-shot request-seen marker when a valid request is parsed, and (6) callback removal after packet completion or explicit rejection. A session that reaches plan/request generation but produces no poll/request/result/rejection evidence is a limiting transport result, not evidence that WH3 lacks the requested query surfaces.

## v0.2I campaign-feasibility live-observation preparation benchmark

Offline preparation passes only if:

- the dedicated PFH5 pack is campaign-only, save-nonmutating, gameplay-nonmutating, and deterministic;
- one first-tick observer-safe snapshot can be captured without a turn advance or owner order;
- query selection is derived from the exact current snapshot through canonical v0.2E→v0.2H code rather than hand-authored live targets;
- no current v0.2G assignment produces no request rather than a fabricated objective;
- the request is atomically written, bound to exact turn/assignment/plan/query IDs, and capped at 16 queries;
- the in-game executor contains a fixed read-query whitelist and no movement, attack, stance-mutation, garrison-transfer, action-point, pathfinding-mutation, save-value, or generic arbitrary-call adapter;
- stale turn and unknown query keys fail closed;
- the collector independently reconstructs the plan from raw snapshot evidence and rejects duplicate, foreign, stale, cardinality-drifted, pack-mismatched, environment-mismatched, or authority-promoted packets;
- the public export excludes raw logs and personal paths;
- observed booleans cannot promote route/action legality, application authority, acknowledgement, execution, or causal outcome.

Closing this benchmark does **not** prove any WH3 query works on the owner's current runtime. The live gate closes only with one exact owner SFO packet whose environment, probe hash, snapshot, request, and results all verify.

## v0.2H campaign feasibility/action-authority benchmark

The gate passes only if:

- every plan consumes a digest-valid v0.2G `SHADOW_PROPOSED_NOT_EXECUTED` assignment with `NO_ORDERS` / `PROHIBITED` authority;
- stable actor character/force CQIs are required before a query plan exists;
- REGION targets may expose exact settlement reachability queries without becoming attack orders;
- FACTION targets expose point-reachability only and never create a concrete character/settlement target;
- missing stance information suppresses stance-specific reachability queries;
- capacity/posture records with no destination do not acquire one;
- all preserved owner results remain unobserved until a live read-only packet exists;
- stale, foreign, duplicate/cardinality-drifted, malformed, or authority-promoted observation packets fail closed;
- synthetic observed booleans cannot promote application, acknowledgement, execution, or causal outcome;
- hidden enemy state, human/player labeling, input order, coordinate translation, and uniform strength scaling do not alter feasibility semantics;
- mutation APIs are explicit prohibited surfaces and no runtime/mutation adapter is imported.

## v0.2G campaign force-allocation benchmark

A passing campaign force-allocation implementation must:

- recompute and verify exact v0.2E/v0.2F source evidence rather than trusting supplied portfolio records;
- expand critical overflow to its exact source obligations before force allocation;
- assign each planner-eligible controlled army to at most one active commitment/protection slot;
- protect recovering armies from noncritical work and label any critical override explicitly;
- preserve a healthy strategic reserve when possible without turning reserve into a destination/order;
- propagate the v0.2F aggressive-commitment veto;
- expose unfilled priorities and force shortages instead of inventing capacity;
- keep path/stance/action feasibility explicitly unverified;
- prevent small geometric changes from causing actor churn;
- permit reviewed reassignment only after the project-owned review window and material score margin;
- retire disappeared priorities without causal-success attribution and reset continuity across missing turns;
- remain semantically invariant under hidden-enemy injection, player-label change, safe input ordering, coordinate translation, and uniform strength scaling;
- emit no campaign orders and retain application authority `PROHIBITED`.

The benchmark does not reward raw aggression, war count, player targeting, or synthetic completion. Greedy assignment quality and temporal constants are engineering hypotheses, not claims of optimal WH3 strategy.
## v0.2F campaign strategic/theater portfolio gate

A strategic portfolio passes only if it is deterministic, `NO_ORDERS`, observer-safe, bounded to at most six top-level priorities, and preserves every critical source through direct representation or explicit overflow. It must:

- prioritize sieged/exposed fronts ahead of opportunistic rival pressure;
- protect recovering field-force capacity;
- aggregate fragmented hostile pressure rather than reward war count;
- preserve a strategic-reserve priority when multiple field armies exist;
- allow at most one aggressive-priority channel and veto that channel during local crisis or total-force recovery;
- distinguish coherent visible-rival containment from proof of coordination or durable power;
- remain invariant to hidden hostile injection, player/NPC relabeling, input ordering, coordinate translation, uniform strength scaling, and empty war edges;
- reject forged/stale v0.2E challenge evidence;
- expose unassigned critical overflow rather than silently dropping it.

The six-record budget and one-aggressive-priority cap are engineering constraints, not measured WH3 optima. Passing this gate does not prove army assignment quality, route feasibility, order authority, campaign outcomes, or owner enjoyment.

## v0.2E strategic challenge benchmark acceptance

A campaign strategic benchmark passes offline only when it preserves observer-safe visibility, does not use human/player identity as a quality or target feature, keeps war count separate from rival coherence, keeps co-location separate from proven coordination, and withholds anti-player bias/diplomacy/recovery/campaign-quality claims that require longitudinal evidence.

The frozen v0.2E matrix requires 8/8 adversarial cases and 5/5 metamorphic checks. Semantic output must be invariant to army/region/war ordering, coordinate translation, uniform strength scaling, insertion of an arbitrarily strong hidden enemy army, and relabeling an otherwise identical enemy from `player_empire` to `npc_empire`. Private/path-bearing input fails closed.

`COHERENT_VISIBLE_RIVAL_CANDIDATE` is a benchmark label, not a gameplay-quality promotion. The 2.0-turn front horizon, 0.65 recovery threshold, 0.50 coherence share, and 0.65 fragmentation ceiling remain project-owned engineering definitions until later longitudinal calibration.

## v0.2C nonterminal replay acceptance

A divergent replay may pass as a **limiting-result evidence fixture** when exact source/environment binding, dense sampling, privacy, and authority checks pass even though natural completion does not. It must be excluded from win/loss, grade, terminal casualty, defeat-irreversibility, and tactical-superiority metrics. Valid uses are phase recognition, crisis timing, lower-bound loss diagnosis, reserve-state refinement, and lifecycle robustness. Repeated playback of the same exhausted stream is not a benchmark improvement.

## v0.2B defeat-calibration acceptance (historical)

A defeat case is not scored as useful merely because the player lost. Before it may affect tactical policy, the project must separate: exact replay identity, visible phase interpretation, exact unit-state telemetry, outcome evidence, and bounded counterfactual hypotheses. The benchmark must reward earlier crisis recognition, mutual support, reserve preservation, firing-lane protection, regroup/fallback eligibility, and asset extraction without assuming that victory was possible or that the owner's commands are correct labels.

The preparation gate passes offline only when replay/video hashes, privacy, phase order, authority, and capture requirements are deterministic. The defeat-calibration gate remains open until a complete schema-2 capture is independently adjudicated.


## Environment cohorts

1. pure vanilla WH3 at the owner's exact settings;
2. vanilla + Transcendence shadow mode;
3. DeepWar reference environment;
4. Hecleas reference environment;
5. SFO alone;
6. SFO + optional Transcendence profile;
7. owner's eventual full mod stack.

Reference mods are never combined blindly. Shared table families require an explicit merged profile.

## Campaign cohorts

- Karl Franz early survival and consolidation;
- Karl Franz midgame multi-front defense;
- Karl Franz late-game dominant empire;
- at least one non-human order faction;
- at least one destruction/chaos faction;
- at least one geographically isolated faction;
- weak, equal, and dominant player positions.

## Primary campaign metrics

- coherent rival powers;
- credible offensive capacity;
- coordinated-army operations;
- exposed-front pressure;
- target quality;
- siege completion and reinforcement;
- recovery after losses;
- diplomacy/war churn;
- objective churn and target thrashing;
- idle armies and wasted travel;
- anti-player bias indicators;
- resource or stat advantages separated from decision quality;
- turn time and script cost;
- owner-rated tension, fairness, variety, and tedium.

## Battle metrics

Long-term battle evaluation includes:

- value-adjusted casualties;
- idle unit time;
- target suitability;
- formation and flank integrity;
- reserve timing;
- ranged, artillery, spell, and ammunition value;
- capture and pursuit behavior;
- command latency and command churn;
- morale collapse and routing propagation;
- direct stat bonuses reported separately;
- owner-rated challenge, fairness, spectacle, responsiveness, and tactical variety.

The v0.1J observation slice does not claim to measure every long-term metric. It records the raw or proxy fields currently expected to support casualties, idle time, engagement timing, flank pressure, reserve timing, ammunition use, command traffic, target transitions, routing, and outcome analysis.

## Promotion rule

No benchmark is canonical until setup, inputs, versions, pack hashes, seeds, and result collection are reproducible. Synthetic results remain hypotheses until calibrated through Reality Gate R0.

## Reality Gate R0 observer acceptance

A campaign-observer run is accepted only when:

- the installed observer pack SHA-256 is recorded directly in each evidence manifest and matches the staged deterministic build;
- lifecycle records appear in order;
- the local faction matches the scenario;
- local army and region records are present or an explicit zero count is justified;
- foreign records originate from game-filtered interfaces;
- no capability-error record invalidates a promoted field;
- exact-pack replication is performed for foundational runtime mechanisms;
- raw logs, private paths, and hashes remain outside Git.

A persistence result requires two isolated exact-pack sessions: fresh `WRITE 0→1`, manual save, then same-environment non-new-game `RELOAD 1→2`. This is replicated for one namespaced integer.

## Consolidated campaign-and-battle acceptance

One live run batches the expanded campaign inputs, orderless planning, and ordinary-battle observation. It is accepted only when:

### Campaign

- only the `shadow` Transcendence pack is loaded;
- the installed shadow pack matches the staged deterministic build;
- at least five complete, consecutive `LOCAL_FACTION_TURN_START` snapshots exist;
- controlled-army strength, movement, unit-health proxy, position, stance, owned-region siege/garrison/structure fields, explicit wars, and visible foreign entities either succeed or preserve explicit capability failures;
- visible foreign entities originate only from WH3 player-filtered lists;
- exact foreign force strength and foreign garrison composition are absent;
- the adapter produces one deterministic proposal set per observed turn;
- previous proposals enter only as bounded project-owned continuity history;
- duplicate, out-of-order, incomplete, or nonconsecutive snapshots fail the gate;
- objective churn, HOLD rate, scenario changes, proxy-policy violations, log volume, and processing time are reported;
- output mode is `SHADOW_NO_ORDERS`.

### Ordinary battle

- the battle script in the same exact pack logs `BATTLE_START` and a completed battle session;
- at least two manually fought ordinary campaign battles complete;
- at least one should be an ordinary field battle; a settlement/siege battle is preferred as the second when naturally available;
- battle metadata includes campaign origin, battle type, local alliance, and unit-scale factor where supported;
- local units and at least one visible enemy unit are observed;
- multiple samples are captured;
- hidden enemy units do not produce identifying or state records;
- capability failures are explicit;
- phases, unit/static counts, sample count, command traffic, casualties, kills, health, ammunition, idle/melee/missile/flank/routing ratios, and result are reported where available;
- output mode is `BATTLE_OBSERVATION_NO_ORDERS`;
- no unitcontroller, battle order, speed modification, save write, visibility modification, or damage modification occurs.

### Combined evidence

- one prepared-session manifest and exact-pack manifest bind the campaign and battle evidence;
- campaign and battle records survive in one append-only project log across runtime transitions;
- nonfield character forces receive no army objective;
- own and foreign feasibility values use compatible disclosed proxy scales;
- a stationed field army is not counted as settlement garrison strength;
- total raw log size is no larger than 30 MB;
- offline processing completes within 60 seconds on the owner machine;
- repeated processing produces the same result digests;
- observed command traffic is never mislabeled as accepted or successful commands;
- one battle promotes interface feasibility only, not tactical-AI quality, SFO compatibility, or battle-control authority.

The corrected session target is campaign turn starts 1–5 and two manually fought ordinary campaign battles in one fresh vanilla Karl Franz run. At least one must be a field battle. A settlement or siege battle is preferred as the second when naturally available, but the owner should not manufacture a battle solely to satisfy type diversity.

## Lost-evidence rule

Owner testimony may establish that a battle or important campaign event occurred, but it is not telemetry. Historical logs, parser fixtures, packaged sample logs, and recovery re-exports may not be substituted for missing current-session evidence. A recovery result that finds no current-session record is preserved as `LIMITING_RESULT`, and the instrumentation defect must be corrected before one broad rerun.


## Battle replay telemetry calibration acceptance

For the preserved Battle of Eilhart replay, the dense telemetry pass is accepted only when:

- the exact replay SHA-256 and exact dedicated battle-only pack SHA-256 are verified;
- `replay=true`, one complete battle, and the victorious alliance are observed;
- schema 2 stable IDs produce no duplicate canonical identity and no identity conflict;
- at least 50% of the expected three-second interval samples are present and maximum detail gap is no more than nine seconds, excluding declared paused/deployment exceptions if later added;
- sampler registration and heartbeat records are present;
- local and visible-enemy units are observed and hidden enemy identity is never emitted;
- aggregate sampling provides a usable men/kills/ammunition/routing/idle/moving curve;
- terminal coverage, exact-vs-lower-bound casualty semantics, and visibility incompleteness are reported;
- selection attribution ratio is reported; zero attribution is a limiting result, not a reason to fabricate ownership;
- bounded inferred attribution is enabled only when dense coverage passes and is labeled `INFERRED_NOT_ACKNOWLEDGED`;
- no unitcontroller, order, battle-speed change, save write, damage/healing, ammunition mutation, visibility change, or randomness occurs;
- raw log remains below 100 MB and offline processing remains below 60 seconds on the owner machine.

The pass calibrates telemetry and SyntheticLab. It does not prove command acceptance, causal effectiveness, tactical-AI quality, live campaign-battle equivalence, or SFO compatibility.


## Battle 4 dense reality-benchmark result

The exact replay calibration condition is now satisfied:

- 249 detail samples against 247 expected;
- 100.8097% coverage;
- 3.4-second maximum detail gap;
- 1,477 alliance aggregates;
- 120 heartbeats;
- 37 stable units and zero aliases;
- local and visible-enemy state;
- read-only authority;
- complete 739.6-second result.

Direct selection attribution is a limiting result: zero callback selection events. Bounded state-delta inference is permitted only under the label `INFERRED_NOT_ACKNOWLEDGED`.

## Tier 4R trace-slice benchmark

A tactical evaluator passes the Battle 4 trace-slice contract only when:

- all eight slice digests and the dense-corpus digest match;
- no hidden enemy identity or state enters an evaluator input;
- outputs are deterministic;
- preservation and target priorities include explanations;
- output authority remains `NO_ORDERS`;
- owner commands are not treated as gold labels;
- local crisis produces stabilization priorities;
- enemy majority rout produces a preservation-aware termination posture;
- direct and inferred command attribution remain distinct;
- no exact casualty claim is made while terminal coverage is incomplete.

Passing this benchmark establishes only offline consistency against one observed vanilla land battle.

## v0.1M tactical-state and decision-opportunity benchmark

The v0.1M framework passes only when:

- the eight trace-slice and dense-corpus source digests match the frozen Battle 4 artifacts;
- tactical-state outputs are deterministic and digest-stable;
- all foreign unit detail remains `VISIBLE_TO_LOCAL_ALLIANCE`;
- hidden enemies contribute only an incompleteness count;
- commander, artillery, ranged, cavalry, and frontline policies use distinct thresholds;
- straight-line distances and withdrawal recoverability disclose that they are not terrain/pathfinding proof;
- local crisis is distinguished from irreversible collapse;
- visible enemy break is distinguished from majority rout and terminal countdown;
- pursuit termination is absent before the rout cascade and present when marginal cleanup value falls below preservation value;
- no actionable opportunity is emitted after battle completion;
- every alternative is `PROPOSED_NOT_EXECUTED` and every counterfactual diagnosis is `UNVERIFIED`;
- no output contains an order, acknowledgement, success, or causal-improvement claim;
- selected advisory opportunities never exceed six per slice;
- critical-opportunity coverage is reported;
- owner command-event comparison is labeled `REFERENCE_ONLY_NOT_CAUSAL`;
- causal casualty reduction, pathfinding success, ordinary-live equivalence, and SFO generalization remain explicitly unmeasured.

Passing this benchmark establishes a deterministic planner-development interface over one observed vanilla battle. It does not establish tactical quality or battle authority.

## v0.1N tactical-contract adversarial benchmark

The v0.1N gate passes only when:

- all frozen source and suite digests match;
- 18 malformed-input cases fail closed;
- 6 metamorphic invariants pass under seed `20260730`;
- string booleans cannot cross alliance, routing, movement, or visibility contracts;
- health, model, ammunition, timing, geometry, identity, role, fatigue, target, and visibility inconsistencies are rejected;
- unit ordering and global x/z translation do not change semantic evaluation;
- worsening a commander cannot improve its danger/recoverability assessment;
- simultaneous local and enemy collapse retains a local-collapse response;
- hidden enemies remain counts and cannot create terminal certainty;
- opportunity lifecycle uses stable keys rather than slice-instance IDs;
- v0.1M artifacts remain frozen;
- v0.1N state, decision, and adversarial artifacts reproduce byte-identically twice;
- all SyntheticLab and Runtime Probe tests pass;
- output remains `NO_ORDERS`, `PROPOSED_NOT_EXECUTED`, and `UNVERIFIED` where applicable.

Observed result: 24/24 adversarial cases pass. Corrected Battle 4 lifecycle metrics are 44 candidates, 25 selected, 28 transitions, and 11 continued priorities. The owner-command comparison remains noncausal.

Passing establishes input and lifecycle contract integrity for one observed vanilla land-battle corpus. It does not establish planner quality, live order feasibility, pathfinding, causal improvement, SFO compatibility, or heterogeneous-battle generalization.

## v0.1O tactical priority portfolio and heterogeneous baseline benchmark

The gate passes only when:

- all 16 project-owned synthetic state contracts pass;
- `ROLE_AWARE_PORTFOLIO_V1` passes all 16 intent/subject contracts;
- required-intent recall and forbidden-intent safety are both 1.0;
- the paired full-scale and half-scale ranged-flank fixtures are semantically equivalent;
- six-group and seven-group saturation fixtures preserve 100% critical source coverage;
- no selected portfolio exceeds six records;
- overflow is explicit and retains all suppressed critical source identities;
- the frozen legacy selector remains reproducible as before-state evidence;
- Battle 4 portfolios and the matrix rebuild byte-identically twice;
- all outputs remain `NO_ORDERS`;
- no synthetic result is described as causal tactical improvement.

Passing establishes deterministic offline portfolio arbitration and heterogeneous contract coverage. It does not establish assignment feasibility, command sequencing, pathfinding, tactical superiority, live authority, or SFO/general battle generalization.


## v0.1P tactical objective assignment and conflict-resolution benchmark

The gate passes only when:

- all 12 assignment scenarios satisfy exact objective, actor, and unfilled-reason contracts;
- all 3 metamorphic checks preserve exact or semantic assignment results;
- each actor occupies at most one abstract action slot per slice;
- routing, shattered, leaving, and rampaging units are never treated as controllable responders;
- stale, forged, authority-altered, and source-substituted portfolios fail closed;
- critical-overflow sources expand into explicit objectives;
- unassignable and resource-conflict objectives remain in the output;
- terminal states produce no objectives or assignments;
- Battle 4 and matrix artifacts rebuild byte-identically twice;
- all outputs remain `NO_ORDERS` and `PROPOSED_NOT_EXECUTED`;
- no result is described as pathfinding, command acceptance, causal improvement, or tactical superiority.

Passing establishes deterministic offline objective assignment and conflict disclosure. It does not establish route feasibility, temporal sequencing, live controllability, command issue/acceptance/acknowledgement/execution, outcome improvement, or SFO/general battle validity.

## v0.1Q tactical temporal scheduling benchmark

The temporal layer passes only when:

- state and assignment digests, contracts, authority, time, and semantic membership validate;
- non-increasing observations and forged assignments fail closed;
- each actor has at most one active abstract plan;
- unchanged canonical assignments continue inside the continuity horizon;
- minor responder changes cannot bypass minimum commitment;
- reviewed reassignment and self-preservation supersession are explicit;
- failed control preconditions and terminal observations cancel explicitly;
- objective disappearance is observational retirement with no causal credit;
- same-action cooldown blocks noncritical thrashing and critical override is disclosed;
- gaps over 30 seconds reset continuity instead of fabricating completion;
- maximum commitment creates a fresh review/replan boundary;
- reversed units, reversed assignment records, and translated coordinates preserve semantic output;
- desired transitions contain no numeric outcome, route, command, or execution prediction;
- all outputs remain `NO_ORDERS` and `ABSTRACT_SCHEDULED_NOT_ISSUED`.

Passing establishes deterministic offline lifecycle semantics only. It does not establish WH3 timing, command legality, reachability, execution, or outcome quality.

## v0.1R action-authority and feasibility preparation benchmark

The offline gate passes only when:

- all 12 action-authority scenarios pass deterministic packet contracts;
- project issue attempts, fabricated direct acknowledgements, hidden targets, malformed booleans, and invalid binding fail closed;
- Battle 4 preserves 397 observed command events, zero direct selection attribution, 302 inferred candidates, and zero issue/acknowledgement/reachability claims;
- the runtime probe contains no unitcontroller or order primitive;
- the strict parser accepts one complete valid fixture and rejects issue, acknowledgement, hidden-target, ordering, and count defects;
- the verifier binds one complete session to exact staged/installed/expected pack hashes;
- the deterministic pack and evidence artifacts rebuild byte-identically twice;
- the one-command prepare/collect workflow keeps raw logs and personal paths local;
- full SyntheticLab and Runtime Probe suites pass twice;
- all outputs retain `NO_ORDERS`, `NOT_ACKNOWLEDGED`, and `UNVERIFIED_NOT_ATTRIBUTED`.

Passing closes preparation only. It does not establish live selection callbacks, query availability, command origin, project issue, direct acknowledgement, route completion, causal execution, outcome improvement, or SFO compatibility.


## v0.1S live action-authority observation benchmark

The live gate passes only when:

- the public export contains exactly the expected schema-1 members and no raw log;
- manifest hashes bind the summary and verification files;
- the exact pinned action-authority pack is preserved;
- one complete session passes every v0.1R verification check;
- command windows, bound/unbound counts, reachability counts, close reasons, and state-match counts reconcile across documents;
- project issue attempts and direct acknowledgements remain zero;
- observed capabilities are promoted individually rather than through a blanket execution claim;
- absent leaving-battle and shattered samples remain `UNVERIFIED`;
- command origin, acknowledgement, route completion, execution, and outcome claims remain rejected or unverified;
- tampered public members fail closed;
- future collector exports include a sanitized, hash-bound preparation attestation without personal paths;
- the complete repository test suite passes repeatedly and the canonical evidence artifact rebuilds identically.

Passing closes the ordinary-battle read-only action-authority observation gate. It does not authorize orders or establish tactical superiority.

## v0.1T bounded tactical feasibility benchmark

The offline gate passes only when:

- all 15 feasibility scenarios and all three metamorphic checks pass;
- each active plan produces at most three candidates and no candidate exceeds 120 m abstract displacement;
- stale state/schedule inputs and forged query evidence fail closed;
- `QUERY_FALSE` vetoes only an exact candidate point;
- `QUERY_TRUE` never promotes route, formation, legality, acknowledgement, execution, or outcome;
- aggregate live reachability is not mapped to Battle 4 candidates;
- Battle 4 remains query-ready but unobserved at candidate level;
- the detailed no-replay export fixture verifies and tampered members fail closed;
- all artifacts rebuild identically and complete repository validation passes twice;
- all outputs retain `NO_ORDERS`.

Passing establishes a bounded evidence envelope only. It does not establish executable feasibility or tactical quality.

## v0.1U observed command-point semantic calibration benchmark

The gate passes only when:

- the exact owner-provided detailed re-export ZIP, window document, manifest, raw-log identity, and pack identity reconcile;
- all 89 windows, 106 actor-windows, and 1,287 samples validate;
- command origin remains unresolved and issue/acknowledgement counts remain zero;
- only explicit finite nonzero `Move` callbacks qualify as point evidence;
- all non-point and opaque callback queries become semantically `NOT_APPLICABLE` without deleting raw telemetry;
- all 38 raw false samples are preserved and traced to their exact window and actors;
- the qualified point profile reports 191 true, zero false, and zero unavailable samples;
- valid false-point evidence remains explicitly unobserved;
- the semantic capability profile cannot promote any of the 102 Battle 4 candidate points;
- ordered-position and current-target matches remain `OBSERVED_NOT_ACKNOWLEDGED`;
- deterministic artifacts and full repository validation pass repeatedly;
- output remains `NO_ORDERS`.

Passing corrects evidence semantics for one ordinary vanilla battle. It does not establish route completion, formation feasibility, command legality, acknowledgement, execution, outcome improvement, SFO compatibility, or broader command-vocabulary coverage.

## v0.1V guarded tactical action packet benchmark

The gate passes only when:

- all 15 guarded scenarios and three metamorphic checks pass;
- only bound exact-point `QUERY_TRUE` candidates enter eligible lists;
- false, unavailable, unobserved, mixed, actor-invalid, and geometry-invalid cases remain explicit;
- source state, schedule, feasibility, plan identities, packet identities, actor identities, cardinalities, selected candidate fields, and candidate geometry validate exactly;
- duplicate plans, duplicate actors, and forged packet identities fail closed;
- all packets retain `NO_ORDERS`, `PROHIBITED`, `NOT_ATTEMPTED`, and `NOT_ISSUED` states;
- Battle 4 remains 34 deferred packets and zero ready packets.

Passing establishes guarded evidence adjudication only. It does not establish command legality, route, formation, acknowledgement, execution, or outcome.

## v0.1W tactical endpoint reservation benchmark

The gate passes only when:

- all 14 reservation scenarios and three metamorphic checks pass;
- every selected endpoint satisfies the 12 m development separation contract;
- criticality and utility dominate lower-priority conflicting packets;
- alternate candidates may resolve endpoint conflicts without changing authority;
- exact and fallback solver modes are explicit and deterministic;
- malformed authority, duplicate plan identity, and nonfinite endpoints fail closed;
- Battle 4 produces zero reservations without candidate-level query evidence;
- outputs remain shadow-only and `NO_ORDERS`.

Passing establishes endpoint-only simultaneous arbitration. It does not establish route crossing, formation footprint, collision simulation, command legality, execution, or tactical benefit.

## v0.1X tactical pipeline adversarial and scaling benchmark

The gate passes only when:

- all 256 deterministic full-pipeline cases pass twice with identical artifacts;
- all authority, issue, acknowledgement, execution, candidate-bound, actor-exclusivity, and endpoint-separation invariants hold;
- semantic outputs survive reversed unit order and uniform battlefield translation;
- duplicate feasibility-plan, forged guarded-packet, duplicate-actor, and authority-escalation attacks fail closed;
- the preserved coordinate-hash tie fixture changes under the legacy tie-break and remains stable after correction;
- all 12 scale cases through 160 ready packets pass with solver mode and optimality status disclosed;
- no structural scale result is described as live WH3 frame-time or tactical outcome evidence.

Passing establishes deterministic offline robustness and bounded structural scaling. It does not establish runtime performance, command authority, route/formation feasibility, casualty reduction, tactical superiority, or SFO generalization.

## v0.1Y SFO combined-session acceptance cohort

One initial SFO continuity cohort requires:

- exact owner-machine `Warhammer3.exe` SHA-256;
- exact Workshop item `2792731173` pack SHA-256 and metadata;
- exactly SFO plus `transcendence_shadow_probe.pack` active, with ordered hashes;
- recorded campaign/battle difficulty, ironman, battle-realism/battlefield-limitation setting, and Karl Franz/Reikland identity;
- one WH3 process;
- at least five local-faction turn-start snapshots;
- at least two manually fought campaign battles;
- campaign return after every battle;
- a valid append-prefix checkpoint chain with no truncation;
- path-free public export and private raw-log retention.

Passing establishes one exact profile's observation compatibility and campaign/battle log continuity. It is not a tactical-quality benchmark and does not generalize to later SFO updates or the full mod stack.

## v0.2A dual-replay tactical-calibration acceptance

The exact Ubersreik/Marienburg cohort passes only when:

- replay, dense-log, dense-corpus, and private visual hashes match the frozen contracts;
- no private path, video/frame/replay bytes, raw log, game asset, or generated pack enters canonical files;
- Ubersreik and Marienburg visual display identities remain separate from the runtime battlefield identity;
- visual outcome and telemetry winner agree without treating victory grade as tactical-quality score;
- reinforcement discovery is represented explicitly before force-complete state;
- telemetry phase windows are ordered and nonoverlapping;
- local crisis may overlap visible enemy collapse;
- terminal/victory evidence permits only bounded pursuit, disengagement, or reformation hypotheses;
- owner command traffic remains reference-only and not acknowledgement, execution, or optimal policy;
- the calibration rebuilds deterministically and matches the frozen result digest;
- all SyntheticLab, Runtime Probe, and repository validations pass twice.

Passing this benchmark closes two-replay calibration only. It does not establish siege/ambush/flying/multi-army behavior, broad SFO compatibility, command authority, or tactical superiority.

## v0.2D cross-corpus tactical-policy acceptance

The gate passes only when:

- all four frozen dense-corpus result digests and both frozen calibration digests match exactly;
- runtime battlefield identity and display/replay identity remain separate when source layers disagree;
- the nonterminal Chaos replay cannot acquire a terminal outcome, winner, or grade;
- multi-corpus safeguards and single-corpus hypotheses have distinct evidence labels;
- high-value severe-loss review uses a ratio threshold and survives model-count scale transformation;
- simultaneous terminal evidence and local crisis preserves local preservation priority while blocking new high commitment;
- hidden-enemy fields, stale observations, foreign provenance, and authority promotion fail closed or abstain as specified;
- all 17 adversarial scenarios and all three metamorphic checks pass deterministically;
- a 500-asset structural evaluation is deterministic;
- no runtime/order adapter, private path, raw artifact, acknowledgement, execution, causality, or tactical-superiority claim is introduced.

Passing establishes a deterministic offline policy envelope over the exact four-battle cohort. It does not establish live command quality, route/formation feasibility, casualty reduction, win-probability improvement, siege/ambush behavior, cross-faction generalization, or broad SFO compatibility.


## v0.2J native behavior observation benchmark

The next native-first benchmark consumes longitudinal observations rather than Transcendence-issued or Transcendence-proposed assignments. Required metrics are: threatened-front coverage, observed front-response latency, recovering-army offensive-engagement rate where replenishment is measured at engagement, healthy unengaged home-zone buffer proxy, stationary-position transition rate proxy, and unexplained directional reversal proxy count.

No product pass threshold is established by the synthetic matrix. The previously discussed 90% front coverage, 5% damaged-army misuse, 2/4-turn commitment window, and 0.15 reassignment margin remain preregistration candidates/project hypotheses—not current-WH3 facts or validated product constants. Real thresholds are frozen only after the observation acquisition contract and matched cohort design are complete.

## v0.2K partial-observation benchmark rule

Never apply a full-faction v0.2J denominator to `PLAYER_VISIBLE_PARTIAL_FOREIGN_AI` evidence. Missing foreign armies or regions are censored/unobserved, not negative examples.

Allowed v0.2K benchmark quantities are observation-process quantities: comparable visible-force intervals, position-stable intervals, movement intervals, uniquely directional visible-anchor proxies, ambiguous approaches, visible-anchor direction-change review candidates, and visibility gains/losses.

`position_idle_rate` is an observation statistic, **not a campaign-AI quality score**. No threshold on that statistic is currently calibrated as a failure criterion.

## v0.2L preregistered player-visible directional-churn benchmark

Primary endpoint: `REPEATED_STABLE_CONTEXT_REGION_OSCILLATION_CLUSTER`.

A candidate window contains exactly four consecutive local-player turn frames and requires:

- continuous visibility of the same foreign force;
- three `VISIBLE_ANCHOR_DIRECTION_PROXY` movement intervals;
- region anchors only;
- anchor sequence A→B→A with A != B;
- movement-heading cosine <= -0.5 at both transitions (>=120 degrees);
- exact equality of all non-target player-visible anchor identities, owners/factions and coordinates across the four frames.

A primary signal requires at least two non-overlapping candidates for the same actor and same unordered region pair. Candidate windows may share their boundary frame but not a movement interval.

Report at minimum: total actor four-frame windows, every exclusion category, eligible stable-context region windows, single oscillation candidates, repeated clusters, and candidate rate per eligible window. Never suppress a zero denominator.

Zero eligible windows = `INSUFFICIENT_ELIGIBLE_EXPOSURE`. Zero clusters with nonzero exposure = `NO_REPEATED_SIGNAL_OBSERVED_NOT_PROOF_OF_NATIVE_HYSTERESIS`.

Vanilla/SFO initial comparison is descriptive only. A detected difference may nominate a bounded native-row treatment; it cannot by itself establish causality or justify a project-owned planner.

## v0.2N fresh privileged diagnostic benchmark

v0.2N confirmatory behavior benchmarking uses only a fresh post-preregistration vanilla cohort and rejects older traces without an explicit battle-participant telemetry declaration.

Recovery endpoint:
- recovering exposure = average unit health at faction turn start <65%;
- denominator >=10 recovering army-turns;
- candidate = same force appears attacker-side in pending-battle cache during its own start→end interval;
- defender-side participation excluded from offensive numerator;
- primary signal requires >=2 candidate army-turns and candidate rate >=20%.

Temporal endpoint:
- three consecutive TURN_END observations for same force;
- exact stable war set, owned-region set and stance;
- health range <=5 points, strength ratio <=1.10, unit-count range <=1;
- both moves >=5 campaign-coordinate units;
- no recorded battle participation between first/last endpoints;
- reversal cosine <=-0.5 (>=120 degrees);
- cohort denominator >=20 eligible windows;
- primary repeated signal requires >=2 **non-overlapping** windows for the same force, or an exact stable/battle-free A→B→A→B→A region pattern.

Negative results never prove native recovery protection or hysteresis generally. Positive results are causal-review candidates and can at most earn a narrow native-row ablation. Threshold digest: `4499a497bfc7dd6a33a6c0a50da4e1e52b1705d1f2f20f1a917cdfebeb5486ac`.

## v0.2O matched SFO behavior benchmark

The sealed v0.2N behavior thresholds remain unchanged. v0.2O prospectively adds a population boundary for strategic temporal interpretation:

- `TERRITORIAL_FACTION_WINDOWS`: stable owned-region set is non-empty; primary strategic cohort;
- `NON_TERRITORIAL`: stable owned-region set empty; secondary patrol/roaming cohort.

At least 20 eligible territorial windows are required for the SFO primary temporal interpretation. Report the same reversal-candidate and repeated-force metrics for both populations, plus the unchanged v0.2N recovery endpoint.

SFO identity is pinned to Workshop `2792731173`, `sfo_grimhammer_3_main.pack`, SHA-256 `ae20a0a08037aa3ebcbe7461d2589fc28dc15a5fe5d9ca4c0a9d0ff0a26da603`. The active launcher profile must contain exactly SFO main plus the diagnostic probe.

Vanilla territorial/non-territorial subgroup values were defined during post-hoc causal review and are reference-only. SFO-minus-vanilla differences are descriptive benchmark signals, not randomized causal effects or proof of a particular DB row.

v0.2O benchmark spec digest: `d9478530440b4bbcd2a5b4453d8bfddc11accbcb0d10d6e310fdbba16f96fb35`.


## v0.2Q staged SFO replication benchmark

Stage A repeats the exact v0.2P SFO profile/instrument on a fresh campaign. Keep every v0.2N/v0.2P movement, battle, stability, population and recovery rule unchanged. Primary territorial interpretation requires >=20 eligible windows.

- repeated territorial force >0: causal/special-policy review; no row copying;
- repeated=0 and rate >0.317073: SFO elevation replicated; request fresh vanilla Stage B;
- repeated=0 and rate <=0.317073: elevation not independently replicated; stop row-ablation path;
- <20 eligible: extend/repeat SFO only.

Stage B is conditional. Profile-level separation requires `min(SFO1,SFO2) > max(VANILLA1,VANILLA2)`. A pooled shared-faction composition guard additionally requires >=20 pooled shared eligible windows per profile and SFO shared-faction rate > vanilla shared-faction rate. Failure or insufficient composition exposure blocks mechanism nomination. Passing both gates earns mechanism-selection review only, never direct application or SFO-row copying.
