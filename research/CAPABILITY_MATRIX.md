## v0.2N native diagnostic behavior-study capability update

| Surface | Classification | Exact boundary |
|---|---|---|
| Complete AI faction start/end field-army state | `OBSERVE_RESEARCH_ONLY` | privileged development plane; application-ineligible |
| `ScriptEventPendingBattle` occurrence | `DOCUMENTED_QUERY_EVENT / OWNER_RUNTIME_PENDING` | new v0.2N listener; no mutation |
| Pending battle attacker/defender military-force CQI + faction | `DOCUMENTED_QUERY_SURFACE / OWNER_RUNTIME_PENDING` | cache participant identity only |
| Recovering (<65%) army-turn exposure | `OBSERVE_PREREGISTERED` | project engineering threshold, not CA constant |
| Recovering attacker-side pending-battle re-entry | `OBSERVE_PREREGISTERED_CANDIDATE` | intent/causality not proven |
| Defender-side recovery participation | `OBSERVE_CONTEXT_ONLY` | explicitly excluded from offensive numerator |
| Stable-context >=120-degree realized heading reversal | `OBSERVE_PREREGISTERED_CANDIDATE` | battle participation excluded; native task identity unavailable |
| Two non-overlapping reversal windows for same force | `OBSERVE_PREREGISTERED_PRIMARY_SIGNAL` | requires >=20 eligible cohort windows |
| Exact region A→B→A→B→A under all exclusions | `OBSERVE_PREREGISTERED_HIGH_SPECIFICITY_SIGNAL` | still causal-review only |
| Old v0.2M-r1 log as confirmatory battle-free evidence | `PROHIBITED_BY_CONTRACT` | no declared battle telemetry |
| Native task ID / assignment memory / engine hysteresis | `UNAVAILABLE_ENGINE_INTERNAL` | unchanged |
| Project campaign order/application authority | `PROHIBITED` | unchanged |
| Privileged state as application input | `PROHIBITED` | fairness boundary |
| Matched SFO behavior cohort | `OWNER_RUN_CONDITIONAL` | only after vanilla eligibility + sufficient endpoint exposure |

## v0.2M diagnostic visibility additions

| Surface | Capability | Scope / prohibition |
|---|---|---|
| Player-filtered foreign armies/regions | OBSERVE | normal evaluator/application-safe evidence |
| Complete AI faction force list at AI turn start/end | OBSERVE_RESEARCH_ONLY | privileged diagnostic plane only; `application_eligible=false` |
| AI force position/strength/unit health/stance from complete faction list | OBSERVE_RESEARCH_ONLY | development telemetry only |
| AI owned regions and current wars in diagnostic stream | OBSERVE_RESEARCH_ONLY | development telemetry only |
| Feed privileged diagnostic rows to application controller | PROHIBITED | fairness boundary |
| Native task identity / assignment memory / engine hysteresis | UNAVAILABLE | not exposed merely by complete force telemetry |
| Campaign order execution | PROHIBITED | unchanged |

## 2026-08-02 v0.2L preregistered visible-direction churn capability

| Capability | Classification | Boundary |
|---|---|---|
| Continuously visible foreign-force trajectory | `OBSERVE` | WH3 player-filtered visibility only |
| Unique visible-region approach direction | `OBSERVE_PROXY` | direction, not native task identity |
| Four-frame region A→B→A oscillation with >=120° heading reversals | `OBSERVE_PREREGISTERED_CANDIDATE` | exact observed non-target context must remain stable |
| Repeated non-overlapping same-actor/same-region-pair oscillation cluster | `OBSERVE_PREREGISTERED_PRIMARY_SIGNAL` | still requires causal review because hidden context remains unknown |
| Stable hidden context | `UNAVAILABLE` | fog-of-war / engine state not observable |
| Native task identity | `UNAVAILABLE` | no task telemetry |
| Native assignment memory | `UNAVAILABLE` | engine internal |
| Native hysteresis | `UNAVAILABLE_ENGINE_INTERNAL` | trajectory proxy cannot prove mechanism |
| Project strategic application authority | `PROHIBITED` | no positive v0.2L result can directly promote v0.2G/v0.2I |
| Prelaunch VANILLA profile binding | `CONTROL` | exact WH3 executable + shadow probe + no non-probe active mod; runtime marker still required |
| Prelaunch SFO profile binding | `CONTROL` | exact WH3 executable + shadow probe + exactly one Workshop 2792731173 pack hash |
| Deferred local probe launcher materialization | `CONTROL_FAIL_CLOSED` | only probe appearance may differ; non-probe entries must remain identical and runtime probe hash/marker must verify |
| Passive owner protocol | `OWNER_ATTESTED_CONTROL` | not engine telemetry; non-attestation makes capture nonconfirmatory |
| Public-safe capture export | `CONTROL` | excludes private paths, private used_mods copy and raw Workshop pack bytes |

## 2026-08-02 v0.2K player-visible native behavior acquisition

| Capability | Classification | Exact scope |
|---|---|---|
| Foreign AI position continuity while player-visible | OBSERVE | stable force CQI across consecutive local-faction snapshots |
| Position stability | OBSERVE_PROXY | position stable only; no idle/stuck intent claim |
| Unique approach toward player-visible anchor | OBSERVE_PROXY | direction only; no native task identity |
| Visible-anchor direction change | OBSERVE_REVIEW_CANDIDATE | never promoted to task churn/hysteresis failure |
| Foreign visibility gain/loss | OBSERVE_CENSORED_TRANSITION | entry/exit from visible set; not lifecycle proof |
| Full foreign-faction front coverage | UNAVAILABLE_INCOMPLETE_FOREIGN_FACTION_VISIBILITY | hidden forces/regions may exist |
| Full response latency | UNAVAILABLE_INCOMPLETE_FOREIGN_FACTION_VISIBILITY | full denominator unavailable |
| Recovery misuse | UNAVAILABLE_NO_SAFE_FOREIGN_REPLENISHMENT_AT_ENGAGEMENT | current safe foreign records lack required engagement-time replenishment |
| Strategic reserve adequacy | UNAVAILABLE_INCOMPLETE_FOREIGN_FACTION_VISIBILITY | hidden healthy forces may exist |
| Native task identity | UNAVAILABLE | no task telemetry |
| Assignment exclusivity | UNAVAILABLE_FROM_TRAJECTORY_ONLY | cannot infer internal allocation slots from movement |
| Native assignment memory / hysteresis | UNAVAILABLE | engine internal |
| Campaign application/order authority | PROHIBITED | no order adapter added |

## 2026-08-02 native-CAI reconciliation capability override

Current official/source evidence establishes native WH3 responsibility for threat/strength evaluation, task generation, task batching, distance-sensitive priority, task/army pairing, recruitment-aware resourcing, personalities, and execution at a responsibility level. Exact internal semantics remain partially opaque. Do **not** infer that native lacks recovery protection, reserves, assignment exclusivity, memory, hysteresis or temporal commitment; classify those as `UNVERIFIED`/`UNKNOWN_ENGINE_INTERNAL` until decoded or observed. Patch 8.1 turn-dependent prioritisation exists officially; its exact DB/script exposure remains `UNVERIFIED`.

The active capability-discovery gate is `GATE_0_NATIVE_CAI_RECONCILIATION`; assignment-derived v0.2I is not the discovery prerequisite.

## v0.2I-r3 live-feasibility transport status

| Surface | Status | Evidence | Boundary |
|---|---|---|---|
| real/UI polling callback | OBSERVE | owner runtime `FEASIBILITY_POLL_TICK` | read-only |
| shared parser for feasibility diagnostics | CONTROL_OFFLINE | r2 regressions | local tooling only |
| runtime-created relative request-file inbound handoff | UNAVAILABLE | repeated owner `request_seen=false` | exact cause unverified |
| prelaunch embedded bounded request | CONTROL_OFFLINE / READY_FOR_OBSERVATION | r3 deterministic builder + environment binding | generated local PFH5, no orders |
| WH3 feasibility query results | UNVERIFIED | next embedded owner retry | query only |
| campaign application/order authority | PROHIBITED | project invariant | no controller |

## v0.2I-r2 live-feasibility transport status

| Surface | Status | Evidence |
|---|---|---|
| Idle real/UI feasibility polling | OBSERVED | second owner-runtime attempt emitted `FEASIBILITY_POLL_TICK` |
| Local parser acceptance of r1 diagnostics | CONTROL / OFFLINE VERIFIED | r2 parser allowlist + synthetic summary regressions |
| Request file consumed by WH3 | UNVERIFIED | `FEASIBILITY_REQUEST_SEEN` not yet observed |
| Query results | UNVERIFIED | no result packet yet |
| Campaign order/application authority | UNAVAILABLE / PROHIBITED | unchanged hard boundary |

# Capability Matrix

## v0.2I-r1 live-feasibility transport status

- first-tick campaign snapshot: `OBSERVED` on owner runtime;
- v0.2E→v0.2H current plan derivation: `OBSERVED` on owner runtime;
- request generation: `OBSERVED` on owner runtime;
- old model-time request polling: `INVALIDATED_FOR_IDLE_WORKLOAD`;
- real UI-timer request polling: `CONTROL_OFFLINE`, owner-runtime confirmation pending;
- live campaign query results: `UNVERIFIED`;
- campaign order/application authority: `PROHIBITED`.

## v0.2I campaign-feasibility live-observation preparation

| Capability | Classification | Exact scope |
|---|---|---|
| First-tick observer-safe campaign snapshot capture | CONTROL_OFFLINE / OWNER_RUNTIME_UNVERIFIED | dedicated campaign-only Lua prepared; no turn advance required by design |
| Canonical current-state v0.2E→v0.2H reconstruction | CONTROL_OFFLINE | Python sidecar uses project-owned deterministic functions |
| Exact bounded live query request | CONTROL_OFFLINE | maximum 16 plan-bound IDs; atomic local file transport |
| In-game query whitelist | CONTROL_OFFLINE / OWNER_RUNTIME_UNVERIFIED | fixed read-only surface set; no arbitrary query dispatch |
| Independent live-packet reconstruction and adjudication | CONTROL_OFFLINE | raw snapshot must reproduce exact saved plan before results are accepted |
| Exact owner WH3+SFO query execution | UNVERIFIED | next live gate |
| Route/ZOC/interception/action legality | UNVERIFIED | not implied by reachability booleans |
| Campaign order application | PROHIBITED | no movement/attack/stance/garrison/AP/pathfinding/save mutation adapter |
| Query→acknowledgement/execution/outcome causality | UNVERIFIED / NOT_INFERRED | explicitly outside v0.2I |

## v0.2H campaign strategic feasibility/action-authority envelope

| Capability | Classification | Exact scope |
|---|---|---|
| Deterministic campaign feasibility query-plan construction | CONTROL_OFFLINE | exact v0.2G shadow assignment + exact observer-safe scenario |
| Actor CQI binding contract | CONTROL_OFFLINE over documented query surface | character/force CQIs required; owner-runtime lookup not yet observed |
| Point reachability query representation | DOCUMENTED / UNOBSERVED_OWNER_BUILD | this-turn, stance-specific, and long-horizon query forms; no route geometry |
| Settlement reachability query representation | DOCUMENTED / UNOBSERVED_OWNER_BUILD | exact REGION→settlement interface only; no attack-target promotion |
| Current active stance query representation | DOCUMENTED / UNOBSERVED_OWNER_BUILD | current state only |
| Stance activation eligibility | DOCUMENTED / UNOBSERVED_OWNER_BUILD | separate from target reachability and not automatically planned |
| Garrison siege context | DOCUMENTED / UNOBSERVED_OWNER_BUILD | `is_under_siege` context only |
| Garrison `can_assault` as actor-target legality | REJECTED_FOR_V0_2H | documented wording is context-ambiguous; never promoted |
| Historical Reikland turn-7 feasibility results | UNOBSERVED | eight query records frozen as `UNOBSERVED_QUERY_NOT_RUN` |
| Campaign route/path details, ZOC, interception | UNVERIFIED | no route observer or path result exists |
| Campaign order application | UNVERIFIED / PROHIBITED | mutation surfaces inventoried but never called |
| Query→acknowledgement/execution/outcome causality | UNVERIFIED | explicitly not inferred |

## v0.2G campaign theater force assignment and commitment

| Capability | Classification | Exact scope |
|---|---|---|
| Deterministic theater-to-army shadow assignment | CONTROL_OFFLINE | exact v0.2E/v0.2F recomputation, planner-eligible controlled armies only |
| Actor exclusivity | CONTROL_OFFLINE | one abstract `ARMY_STRATEGIC_COMMITMENT_SLOT` per controlled actor; zero double booking in gate fixtures |
| Critical-overflow expansion | CONTROL_OFFLINE | exact omitted critical source priorities restored before resource allocation |
| Recovery protection / explicit critical override | CONTROL_OFFLINE | noncritical assignments blocked below 0.65 replenishment; critical emergency use labeled explicitly |
| Strategic reserve capacity reservation | CONTROL_OFFLINE | one healthy unclaimed actor preserved when possible; no destination/stance/order implied |
| Resource-conflict and shortage disclosure | CONTROL_OFFLINE | unfilled obligations retained instead of fabricated capacity |
| Temporal anti-thrashing lifecycle | CONTROL_OFFLINE | deterministic start/continue/review-reassign/supersede/cancel/retire/reset over consecutive snapshots |
| Observed turn-7 Reikland assignment | SUPPORTED_OFFLINE | one `CONTAIN_COHERENT_VISIBLE_RIVAL` shadow assignment to `force:65`; no execution claim |
| Campaign route/path feasibility | UNVERIFIED | geometry is reference-only; no WH3 path, stance, ZOC, interception, or reachability proof |
| Campaign order application | UNVERIFIED / PROHIBITED | no runtime command or mutation adapter |
| Optimal assignment/timing policy | UNPROVEN | greedy solver and 2/4-turn + 0.15 thresholds are engineering hypotheses |
## v0.2F campaign strategic/theater priority portfolio

| Capability | Classification | Exact scope |
|---|---|---|
| Observer-safe strategic priority portfolio | CONTROL | deterministic project-owned derivation from exact v0.2E benchmark evidence |
| Critical-source overflow preservation | CONTROL | 7-front adversarial fixture retains 1.0 critical source coverage under six-record budget |
| Fragmented-pressure aggregation | CONTROL | multiple hostile wars create one aggregate pressure priority rather than one commitment per war |
| Crisis / total-recovery aggression veto | CONTROL | `selected_aggressive_priorities` empty while veto is active |
| Strategic reserve representation | CONTROL | medium project-owned priority when multiple controlled field armies exist; no assignment |
| Player-label invariance | CONTROL | player→NPC metamorphic result is semantically identical |
| Army-to-theater assignment | UNVERIFIED / NOT_PERFORMED | next gate |
| Strategic route feasibility | UNVERIFIED | no campaign movement/path adapter in v0.2F |
| Campaign order application | UNVERIFIED / PROHIBITED | no runtime order path added |
| Optimal six-record / one-aggressive-channel policy | UNPROVEN | engineering constraints only |

## v0.2E campaign strategic challenge benchmark

| Capability | Classification | Exact scope |
|---|---|---|
| Observer-safe campaign challenge evaluation | CONTROL | project-owned deterministic evaluator over campaign scenario snapshots |
| Hidden hostile army exclusion | CONTROL | hidden-army injection leaves semantic benchmark output unchanged |
| Player-label invariance | CONTROL | `player_empire` → `npc_empire` rename leaves semantic output unchanged |
| Visible rival concentration/front diagnostics | CONTROL | snapshot benchmark only; project-owned thresholds |
| Turn-7 Marienburg coherent visible-rival candidate | SUPPORTED_OFFLINE | derived from owner-observed v0.1J turn-7 snapshot; not durable-coordination proof |
| Anti-player bias | UNAVAILABLE_FROM_SNAPSHOT | needs targeting history and nonplayer counterfactuals |
| Diplomatic bloc intent | UNAVAILABLE_FROM_WAR_EDGES | needs richer diplomacy state/history |
| Durable recovery capacity | UNAVAILABLE_FROM_SNAPSHOT | needs economy/recruitment/replenishment history |
| Campaign order application | UNVERIFIED / PROHIBITED | no runtime adapter or order path added |
| Late-game campaign quality | UNPROVEN | synthetic reference + early observed snapshots do not establish owner experience |

## v0.2C Chaos replay divergence calibration

| Capability | Classification | Exact scope |
|---|---|---|
| Exact SFO replay environment | OBSERVED | exact SFO + read-only replay probe, two-mod load order |
| Dense nonterminal unit-state trace | OBSERVED | 338.5s, 115 detail samples, 637 aggregates, 23 units |
| Natural battle completion | LIMITING_RESULT | `BATTLE_COMPLETE` absent; completed battle count 0 |
| Original live defeat | OWNER_ATTESTED | recording consistent; normal result card absent |
| Exact defeat grade / victorious alliance | UNVERIFIED | replay cannot supply terminal result |
| Elite cavalry, artillery, infantry, commander crisis | SUPPORTED | lower-bound nonterminal findings only |
| Reserve state | SUPPORTED_REFINEMENT | delayed/uneven commitment, not proven absence |
| Terminal-outcome learning from replay exhaustion | INVALIDATED | prohibited by lifecycle guard |
| Command acknowledgement / causal execution | UNOBSERVED | command traffic and inference only |
| Anti-Chaos tactical superiority | UNPROVEN | one divergent replay, no controlled intervention |

## v0.2B Chaos defeat preparation (historical)

| Capability | Classification | Exact scope |
|---|---|---|
| Exact Chaos replay identity | OBSERVED | 86,067-byte replay SHA-256 `28d780d0…f838cb5` |
| Visual battle title/factions | OBSERVED | `An Ogre's Folly`, Reikland vs Warhost of the Apocalypse |
| Visual defeat trajectory | SUPPORTED | deployment → local overload → unsupported engagement → fragmentation → cascading failure → terminal defeat |
| Exact defeat grade | UNVERIFIED | normal result card absent |
| Dense health/morale/ammunition/routing chronology | UNOBSERVED | one exact read-only replay capture pending |
| Formation/reserve/commitment/firing-lane/reset diagnoses | HYPOTHESIS/SUPPORTED | bounded visual preparation only |
| Exact dedicated replay observer | CONTROL_PREPARED | frozen pack hash |
| Exact script-equivalent shadow observer | CONTROL_PREPARED | accepted only under frozen shadow-pack and shared battle-script hashes |
| Command acknowledgement/execution causality | UNOBSERVED | no project-issued order; observation only |
| Defeat preventability or tactical superiority | UNPROVEN | no counterfactual execution evidence |


## v0.2A exact dual-replay visual calibration

| Capability | Classification | Exact scope |
|---|---|---|
| Exact Ubersreik/Marienburg replay identity | OBSERVED | SHA-bound private replay cohort |
| Dense replay tactical time series | OBSERVED | 521 detail samples, 2,958 aggregate records, 63 canonical units, 511 command events across two replays |
| Visual replay title and outcome | OBSERVED | Ubersreik Decisive Victory; Marienburg Pyrrhic Victory |
| Reinforcement-aware force completeness | SUPPORTED | 3→16 local units at Ubersreik; 1→20 at Marienburg |
| Victory-grade versus tactical-cost separation | SUPPORTED | Marienburg 2.100861× duration and 2.341317× local casualty lower bound |
| Local crisis while enemy collapse is underway | SUPPORTED | Marienburg phase alignment and route timing |
| Terminal high-commitment abstention | SUPPORTED | bounded advisory rule only |
| Replay/runtime/display identity separation | OBSERVED | runtime `Battle of Eilhart` retained separately from visual titles |
| Exact outer Transcendence pack container | UNVERIFIED | launcher attestation named shadow pack; battle script bytes were identical |
| Command acknowledgement/execution causality | UNOBSERVED | no supported acknowledgement signal; no project-issued order |
| Tactical superiority or broad SFO generalization | UNPROVEN | two Reikland land battles only |

## v0.1Z exact SFO observed baseline

| Capability | Classification | Exact scope |
|---|---|---|
| SFO environment identity | OBSERVED | frozen WH3 executable, SFO pack, probe, load order, settings, and Reikland faction |
| SFO campaign observation | OBSERVED | six consecutive local turns |
| SFO ordinary land-battle observation | OBSERVED | three completed campaign battles |
| Campaign → battle → campaign append continuity | OBSERVED | three independent cycles and 130 valid prefixes |
| Dense schema-2 battle time series | OBSERVED | 698 detail samples, 4,000 aggregates, 80 canonical units |
| Selection-event observation | OBSERVED | 1,025 events |
| Command-event observation | OBSERVED_NOT_ACKNOWLEDGED | 683 events; origin/acceptance/causality unresolved |
| Siege, ambush, reinforcement coverage | UNOBSERVED | no such battle in the cohort |
| Order acknowledgement and execution causality | UNOBSERVED | no supported acknowledgement signal or project-issued order |
| Tactical superiority | UNPROVEN | no controlled policy comparison |
| Broad factions and full mod stack | UNOBSERVED | exact SFO-only Reikland profile only |


## Offline/project capabilities

| Area | Capability | Status | Evidence |
|---|---|---:|---|
| SyntheticLab | validate campaign contracts and reject prohibited private fields | CONTROL | automated tests |
| SyntheticLab | filter hidden enemy armies from planner input | CONTROL | automated tests |
| SyntheticLab | deterministic Army Objective Assignment | CONTROL | repeated identical result digests |
| SyntheticLab | abstract seeded campaign rollout | CONTROL | Tier 2 implementation; uncalibrated |
| SyntheticLab | seeded ensemble aggregation | CONTROL | Tier 3 implementation; uncalibrated |
| SyntheticLab | tactical contract surrogate | CONTROL | Tier 4 implementation; uncalibrated |
| Audit tooling | enumerate uncompressed zero-dependency PFH5 pack entries and hashes | CONTROL | DeepWar/Hecleas audits + tests |
| Audit tooling | ingest extracted SFO DB/script/text ZIP | CONTROL | SFO audit report + tests |
| Audit tooling | identify shared table families and potential conflict surface | CONTROL | three-way comparison |
| Probe tooling | build deterministic uncompressed zero-dependency PFH5 Mod packs | CONTROL | repeated byte-identical builds + parser round trip |
| Probe tooling | statically enforce read-only campaign and battle shadow-source boundaries | CONTROL | mutation/order/controller-token regression tests |
| Probe tooling | parse bounded structured campaign and battle records | CONTROL | valid and adversarial fixture tests |
| Probe tooling | reject private, malformed, duplicate-field, out-of-order, incomplete-sample, and hidden-enemy-leak records | CONTROL | automated tests |
| Probe tooling | stage, collect, hash, and rollback probe artifacts | CONTROL | observer/persistence installation and collection completed; live rollback pending |
| Probe tooling | capture installed probe hash, staged agreement, loaded probe kind, battle-loader evidence, and prepared combined-session identity | CONTROL | evidence-manifest schema v4 + combined-session manifest |
| Probe tooling | verify isolated two-phase saved-value persistence chains | CONTROL | live replicated chain + adversarial tests |
| Campaign shadow | convert every canonical local-turn snapshot to an observer-safe scenario | CONTROL | deterministic five-turn fixture pipeline + real turns 4–7 reprocessing |
| Campaign shadow | carry bounded prior-proposal continuity and generate orderless assignments | CONTROL | multi-turn regression tests |
| Campaign shadow | compute churn, HOLD rate, state change, proxy, volume, and processing metrics | CONTROL | consolidated verifier tests |
| Campaign shadow | exclude nonfield character forces from army assignment | CONTROL | explicit eligibility schema + legacy-log regression fixture |
| Campaign shadow | align own/foreign feasibility proxies and keep exact own strength telemetry-only | CONTROL | proxy-alignment regression fixture + real-input reprocessing |
| Campaign shadow | exclude stationed field armies from settlement garrison estimates | CONTROL | armed-citizenry guard + regression fixture |
| Battle telemetry | parse ordinary-battle sessions, phases, samples, units, commands, and completion | CONTROL | deterministic fixture and adversarial tests |
| Battle telemetry | enforce visible-only foreign unit records | CONTROL | source audit + hidden-enemy-leak rejection test |
| Battle telemetry | derive descriptive unit/alliance/battle metrics without issuing orders | CONTROL | `BATTLE_OBSERVATION_NO_ORDERS` report tests |
| Combined gate | require five campaign turns and one completed battle under one exact read-only pack | CONTROL | combined verifier fixture tests |
| Combined gate | return a partial result rather than fabricate battle evidence when no battle occurred | CONTROL | no-battle regression test |
| Combined logging | preserve campaign and battle records across separate WH3 Lua runtimes | CONTROL_OFFLINE | append-only source, prepared-session script, strict collector tests; live continuity pending |
| Evidence adjudication | separate current-session live logs from historical logs, fixtures, and recovery re-exports | CONTROL | timestamp-scoped recovery adjudicator regression test |

## WH3 runtime capabilities

| Area | Required behavior | Status | Evidence | Next probe |
|---|---|---:|---|---|
| Campaign | load a script-only PFH5 Mod pack | OBSERVE | exact observer replication and persistence run | combined shadow pack |
| Campaign | enumerate local armies and regions | OBSERVE | replicated observer snapshots | expanded fields in combined run |
| Campaign | receive game-filtered visible foreign characters and regions | OBSERVE | replicated observer snapshots | combined run |
| Campaign | persist one namespaced project integer through save/reload | CONTROL | replicated `WRITE 0→1` / `RELOAD 1→2` | migration design later |
| Campaign | observe expanded strength, movement, health, siege, garrison, structure, and wars | OBSERVE | four live snapshots, turns 4–7; corrected derived report | fresh prepared turns 1–5 run |
| Campaign | issue or influence army objectives | UNVERIFIED | source audit only | later intervention sandbox |
| Campaign | influence recruitment/economy priorities | UNVERIFIED | native DB tuning surface | isolated DB experiment |
| Battle | load a project-authored ordinary-battle script from the combined pack | UNVERIFIED | documented loader path; first live run lost/failed to preserve battle records | corrected append-log run |
| Battle | observe battle metadata and phase callbacks | UNVERIFIED | primary documentation + fixture | combined run |
| Battle | observe local unit state across synchronized samples | UNVERIFIED | primary documentation + fixture | combined run |
| Battle | observe only visible foreign unit state | UNVERIFIED | primary visibility query + static guard | combined run |
| Battle | observe player command-handler traffic | UNVERIFIED | primary documentation + fixture | combined run |
| Battle | command units in ordinary battles | UNVERIFIED | no unitcontroller or order path in current pack | later isolated authority probe |
| Battle | command units in generated/scripted battles | UNVERIFIED | documentation suggests controller path | later generated-battle probe |
| UI | expose settings and Why inspector | UNVERIFIED | source patterns only | minimal UI component |
| Tooling | build structurally valid combined campaign/battle pack | CONTROL | deterministic two-entry PFH5 build |
| Tooling | load the combined pack in WH3 campaign context | OBSERVE | exact pack loaded; turns 4–7 preserved | corrected combined run |
| Tooling | load the combined pack in WH3 battle context | UNVERIFIED | no live `TRANS_BATTLE` record survived; fixture records excluded | corrected combined run |
| Tooling | build a valid optional SFO profile pack | UNVERIFIED | no certified profile | after vanilla combined slice |
| Logging | write structured campaign output through `ModLog` | OBSERVE | replicated observer/persistence and turns 4–7 evidence | append-log continuity run |
| Logging | append campaign and battle records to one project-owned cross-runtime file | UNVERIFIED | static source and collector tests; live run pending | corrected combined run |
| Logging | write structured ordinary-battle output | OBSERVE | exact replay produced a complete 11.8 MB dense structured log | later ordinary live campaign battle |
| Rollback | remove/restore installed probe packs safely | UNVERIFIED | offline hash guards only | controlled live rollback test |
| Multiplayer | deterministic/desync-safe execution | OUT_OF_SCOPE_INITIAL | personal single-player target | revisit only if requested |


## v0.1K Battle 4 capability update

| Capability | Classification | Evidence |
|---|---|---|
| Load exact preserved ordinary-battle replay with project battle script | OBSERVE — OBSERVED | complete 739.6-second replay session |
| Query local unit static/dynamic fields | OBSERVE — OBSERVED | 17 canonical local units |
| Query player-visible enemy unit fields | OBSERVE — OBSERVED | 17 canonical visible-enemy units; hidden units withheld |
| Observe battle phases, outcome, winner, and command traffic | OBSERVE — OBSERVED | deployment/deployed/victory/complete plus 397 commands |
| Reliable continuous three-second replay sampling | OBSERVE — UNVERIFIED | original sampler invalidated; v0.1K dual-clock probe prepared |
| Stable unit continuity using unique UI identity | CONTROL (offline adapter) — REPLICATED | identity-churn fixture and Battle 4 reconciliation |
| Direct command-to-selected-unit attribution | OBSERVE — UNVERIFIED | corrected per-unit callbacks prepared |
| Bounded command attribution from dense state deltas | INFLUENCE (offline inference only) — CONTROLLED OFFLINE | deterministic, labeled `INFERRED_NOT_ACKNOWLEDGED`; live dense input pending |
| Issue or verify ordinary-battle commands | CONTROL — UNVERIFIED | no unitcontroller/order/acknowledgement path |
| Tactical-AI quality improvement | UNVERIFIED | no control trial or benchmark comparison |


## v0.1L Battle 4 dense-trace capability update

| Capability | Classification | Evidence |
|---|---|---|
| Run dual model/real replay callbacks with heartbeat monitoring | OBSERVE — OBSERVED | 739 model ticks, 1,206 real ticks, 120 heartbeats |
| Capture dense unit-state samples throughout the exact replay | OBSERVE — OBSERVED | 249 detail samples, 247 expected, 100.8097% coverage, 3.4 s maximum gap |
| Capture one-second alliance aggregates throughout the exact replay | OBSERVE — OBSERVED | 1,477 aggregate records |
| Maintain stable unit identity through the dense replay | CONTROL (offline identity contract) — REPLICATED | 37 canonical units, zero aliases/conflicts |
| Observe local and visibility-filtered foreign unit state | OBSERVE — OBSERVED | 17 local and 20 visible-enemy canonical units; hidden enemy identities omitted |
| Observe direct selected-unit callbacks during replay playback | OBSERVE — LIMITING_RESULT | zero selection events despite corrected per-unit registration |
| Infer bounded command candidates from state deltas | CONTROL (offline inference) — OBSERVED INPUT / HYPOTHESIS OUTPUT | 302 inferred commands, 121 high-confidence; always `INFERRED_NOT_ACKNOWLEDGED` |
| Build visibility-safe reality slices from the dense trace | CONTROL | eight deterministic Tier 4R slices; no raw log/replay committed |
| Run deterministic tactical shadow assessment over observed slices | CONTROL_OFFLINE — HYPOTHESIS | no-order evaluator with bounded priorities and explicit hidden-information guard |
| Issue, accept, or verify ordinary-battle orders | UNVERIFIED | no order/controller/acknowledgement path exercised |

## v0.1M tactical-state and decision-opportunity update

| Capability | Classification | Evidence |
|---|---|---|
| Normalize visibility-safe observed slices into a canonical tactical-state trajectory | CONTROL_OFFLINE | eight deterministic states, state result digest `cec345739fc6d4231b88f2cfb6814082ab0be970530da704f3b36d881f63cbb5` |
| Derive role-specific asset, danger, recoverability, collapse-risk, support, and engagement proxies | CONTROL_OFFLINE — HYPOTHESIS METRICS | disclosed deterministic formulas and regression tests; weights uncalibrated beyond Battle 4 |
| Distinguish temporary pressure, local crisis, recovery, visible rout cascade, and terminal state | CONTROL_OFFLINE — HYPOTHESIS CLASSIFICATION | expected eight-slice state sequence and adversarial tests |
| Extract bounded tactical decision opportunities without issuing commands | CONTROL_OFFLINE — HYPOTHESIS OUTPUT | 37 candidates, 25 selected, six-per-slice cap, all alternatives `PROPOSED_NOT_EXECUTED` |
| Apply role-specific preservation policies | CONTROL_OFFLINE — HYPOTHESIS | commander, artillery, ranged, cavalry, frontline, and unknown policies are separate and tested |
| Identify pursuit-termination windows | CONTROL_OFFLINE — HYPOTHESIS | absent at first contact; selected at majority rout and victory countdown |
| Diagnose severe degradation as plausibly preventable versus insufficient evidence | CONTROL_OFFLINE — HYPOTHESIS | 4 plausible and 7 insufficient-evidence cases; all counterfactuals remain `UNVERIFIED` |
| Compare advisory priority churn with owner command traffic | CONTROL_OFFLINE — REFERENCE_ONLY_NOT_CAUSAL | 50 transitions / 397 command events = `0.125945` |
| Prove a proposed alternative reduces casualties or improves the battle | UNVERIFIED | requires accepted/executed intervention telemetry, path feasibility, and matched cohorts |
| Issue, accept, or verify battle commands | UNVERIFIED | v0.1M authority remains `NO_ORDERS` |

## v0.1N tactical-contract hardening update

| Capability | Classification | Evidence |
|---|---|---|
| Reject malformed tactical observations before state construction | CONTROL_OFFLINE — REPLICATED | 18/18 preserved invalid mutations fail closed under `BATTLE_TRACE_TACTICAL_INPUT_V2` |
| Preserve tactical semantics under safe transformations | CONTROL_OFFLINE — REPLICATED | 6/6 metamorphic cases pass; seed `20260730` |
| Separate local force condition from combined tactical phase | CONTROL_OFFLINE — HYPOTHESIS CLASSIFICATION | simultaneous-collapse regression and corrected Battle 4 majority-rout state |
| Track continuing decision opportunities across slices | CONTROL_OFFLINE — REPLICATED | stable `opportunity_key`; 28 transitions and 11 continuations instead of 50 slice-ID artifacts |
| Rebuild v0.1N state, decisions, and adversarial evidence deterministically | CONTROL_OFFLINE — REPLICATED | three artifacts reproduced byte-identically twice |
| Generalize the contracts to other battle types, factions, unit scales, or SFO | UNVERIFIED | requires heterogeneous public-safe corpora and later runtime cohorts |
| Prove tactical improvement or issue/acknowledge orders | UNVERIFIED | authority remains `NO_ORDERS`; outcomes remain counterfactual-uncertain |

## v0.1O tactical portfolio capability update

| Capability | Classification | Evidence |
|---|---|---|
| Expose all tactical candidates before legacy budget selection | CONTROL_OFFLINE | deterministic public seam; frozen v0.1N outputs unchanged |
| Group equivalent unit-level concerns into bounded portfolio records | CONTROL_OFFLINE | Battle 4 and saturation regressions |
| Preserve critical source awareness when distinct groups exceed capacity | CONTROL_OFFLINE | explicit overflow fixture, 100% critical-source coverage |
| Compare deterministic policy baselines across strict synthetic fixtures | CONTROL_SYNTHETIC | 16 scenarios, six policies, deterministic report |
| Establish tactical superiority or causal outcome improvement | UNVERIFIED | no action execution, transition model, pathfinding, or matched outcomes |


## v0.1P tactical assignment capability update

| Capability | Classification | Evidence |
|---|---|---|
| Convert canonical portfolio sources into explicit tactical objectives | CONTROL_OFFLINE | Battle 4 trajectory and 12-scenario matrix |
| Assign one eligible local actor to at most one abstract unit-action slot per slice | CONTROL_OFFLINE | deterministic maximum-weight assignment; zero double-booking |
| Preserve uncontrollable, unassignable, and resource-conflict obligations | CONTROL_OFFLINE | distinct unfilled reasons and frozen stress fixtures |
| Reject stale, forged, authority-altered, or source-substituted portfolio inputs | CONTROL_OFFLINE | digest, contract, authority, count, and canonical-source-set guards |
| Preserve assignment semantics under unit order, portfolio order, and coordinate translation | CONTROL_SYNTHETIC | 3/3 metamorphic checks |
| Establish terrain-aware feasibility, command acceptance, or outcome improvement | UNVERIFIED | no paths, command channel, acknowledgement, or transition outcomes |

## v0.1Q tactical temporal scheduling capability update

| Capability | Classification | Evidence |
|---|---|---|
| Retain, review, supersede, cancel, or retire canonical abstract plans across trusted observations | CONTROL_OFFLINE | deterministic Battle 4 trajectory and lifecycle implementation |
| Block noncritical same-action thrashing while disclosing critical override | CONTROL_OFFLINE | frozen cooldown scenarios |
| Fail closed on stale/forged assignments, altered authority, and nonmonotonic time | CONTROL_OFFLINE | strict scheduler-input regressions |
| Preserve semantics under input order and coordinate translation | CONTROL_SYNTHETIC | 3/3 temporal metamorphic checks |
| Infer continuity across gaps greater than 30 seconds | UNAVAILABLE_BY_POLICY | explicit continuity reset |
| Establish measured timing, command legality, execution, or outcome improvement | UNVERIFIED | no live authority or acknowledgement packet |

## v0.1R action-authority preparation capability update

| Capability | Classification | Evidence |
|---|---|---|
| Separate command event, issue attempt, acknowledgement, state match, interruption, and outcome | CONTROL_OFFLINE | strict packet and 12/12 matrix |
| Build deterministic read-only action-authority PFH5 pack | CONTROL_OFFLINE | exact pack SHA-256 `3acf60520b60f87f8c18e13532512324cb7a539626996ce19897fad94cf2d25d` |
| Parse local selection, command events, reachability, and five-second state windows | CONTROL_OFFLINE | strict fixtures and parser regressions |
| Verify one prepared exact-pack capture | CONTROL_OFFLINE | `ACTION_AUTHORITY_CAPTURE_VERIFICATION_V1` fixture |
| Observe ordinary-live selection binding and reachability availability | UNVERIFIED | prepared batched owner run pending |
| Identify command origin as player versus script | UNAVAILABLE_IN_CURRENT_CALLBACK | source audit exposes unresolved origin |
| Observe direct command acknowledgement | UNVERIFIED / NO SOURCE FOUND | state matches are not acknowledgement |
| Issue or execute Transcendence battle orders | UNVERIFIED | no unitcontroller and authority remains `NO_ORDERS` |
| Attribute outcome improvement to a proposal | UNVERIFIED | no issue, acknowledgement, execution, or matched outcome |


## v0.1S live action-authority calibration update

| Capability | Classification | Evidence |
|---|---|---|
| Observe ordinary-battle local selection callbacks | OBSERVED | 130 selection events in one complete exact-pack session |
| Bind command-state windows to contemporaneously selected local units | OBSERVED_WITH_ORIGIN_UNRESOLVED | 89/89 bound windows; binding is not command-origin attribution |
| Sample local action state after command events | OBSERVED | 1,287 read-only samples |
| Query callback position reachability, raw | OBSERVED_RAW_WITH_SEMANTIC_LIMIT | 1,249 true, 38 false, 0 unavailable; non-point zero-vector callbacks were included |
| Observe ordered-position and current-target state matches | OBSERVED_NOT_ACKNOWLEDGED | 189 ordered-position and 443 target matches |
| Observe movement, routing, control loss, and window interruption | OBSERVED | 739 movement, 1 routing, 1 control-loss; 45 subsequent-command, 43 timeout, 1 routed close |
| Observe leaving-battle or shattered state in this capture | UNVERIFIED | zero samples for both states |
| Independently replay raw-event parsing from public artifacts | UNAVAILABLE_BY_PRIVACY_POLICY | raw log retained locally and excluded from repository |
| Independently replay schema-1 preparation checks from the public packet | LIMITING_RESULT | prepared manifest omitted; owner-run verification and digest preserved |
| Identify command origin, direct acknowledgement, route completion, or causal outcome | UNVERIFIED / UNAVAILABLE_IN_CURRENT_CALLBACK | no trusted source and zero project orders |

## v0.1T bounded feasibility capability update

| Capability | Classification | Evidence |
|---|---|---|
| Generate bounded role-aware candidate points from canonical active plans | CONTROL_OFFLINE | 34 Battle 4 envelopes, 102 candidates, max 3 per plan |
| Bind exact candidate points to point-query evidence | CONTROL_OFFLINE | strict actor/time/state/schedule/candidate digest guards |
| Use `QUERY_FALSE` as an exact-point veto | CONTROL_OFFLINE | deterministic matrix regressions |
| Use `QUERY_TRUE` as point support only | CONTROL_OFFLINE | route, formation, legality, acknowledgement, execution, and outcome remain explicitly absent |
| Preserve v0.1S raw reachability as frozen historical telemetry | OBSERVED_RAW_AGGREGATE_WITH_SEMANTIC_LIMIT | 1,249 true, 38 false; v0.1U qualifies only explicit point commands |
| Re-export detailed windows from the preserved private log without replay | OBSERVED_OWNER_RUN | exact 89-window, 1,287-sample public-safe export received and verified |
| Establish terrain-aware route or executable action feasibility | UNVERIFIED | point queries are not routes or legal orders |


## v0.1U semantic point-evidence update

| Capability | Classification | Evidence |
|---|---|---|
| Distinguish explicit point commands from unit-target and opaque callbacks | CONTROL_OFFLINE | strict five-modality adjudicator and exact source identities |
| Observe true point-query results for explicit nonzero Move points | OBSERVED, SCOPED | 16 windows, 16 actors, 191/191 qualified `QUERY_TRUE` samples |
| Observe false point-query result for an explicit nonzero point | UNVERIFIED_NONE_OBSERVED | all 38 raw false samples came from zero-vector formation callback window `w5` |
| Treat non-point callback queries as tactical point evidence | REJECTED | 1,096 samples reclassified semantically `NOT_APPLICABLE` |
| Observe initial ordered-position match for explicit Move callbacks | OBSERVED_NOT_ACKNOWLEDGED | 16/16 actor-windows |
| Observe initial visible current-target match for Attack Unit callbacks | OBSERVED_NOT_ACKNOWLEDGED | 48/49 actor-windows |
| Apply live semantic calibration to generated Battle 4 candidates | UNVERIFIED / PROHIBITED_INFERENCE | separate battle and separate points; 34 envelopes remain unqueried |

## v0.1V guarded action-packet capability update

| Capability | Classification | Evidence |
|---|---|---|
| Convert exact-point feasibility evidence into authority-prohibited shadow packets | CONTROL_OFFLINE | 15/15 guarded scenarios and frozen Battle 4 trajectory |
| Abstain when point evidence is absent, unavailable, false, mixed, or actor-invalid | CONTROL_OFFLINE | explicit readiness classes and 34/34 Battle 4 deferrals |
| Reject duplicate, stale, forged, identity-substituted, actor-duplicated, or authority-altered packet sources | CONTROL_OFFLINE | canonical packet/source binding, unique plan and actor identities, cardinality, and source-shape guards |
| Treat guarded readiness as command legality or execution | UNAVAILABLE_BY_POLICY | packets fix application authority to `PROHIBITED` |

## v0.1W endpoint-reservation capability update

| Capability | Classification | Evidence |
|---|---|---|
| Reserve nonoverlapping candidate endpoints across ready shadow packets | CONTROL_OFFLINE | 14/14 matrix scenarios; 12 m endpoint-separation contract |
| Preserve criticality and utility under bounded simultaneous conflict | CONTROL_SYNTHETIC | exact branch-and-bound within 16 ready packets |
| Disclose deterministic fallback and unverified optimality above the exact bound | CONTROL_OFFLINE | 20-packet matrix case and 24–160 packet scale cases |
| Prove route, formation, terrain, collision, or arrival feasibility | UNVERIFIED | endpoint-only contract explicitly excludes these claims |

## v0.1X full-pipeline audit capability update

| Capability | Classification | Evidence |
|---|---|---|
| Fuzz the complete offline tactical pipeline deterministically | CONTROL_SYNTHETIC | 256/256 cases, seed `20260730` |
| Preserve semantic output under unit-order and uniform-translation changes | CONTROL_SYNTHETIC | all randomized representation checks pass |
| Reject duplicate-plan, forged-packet, duplicate-actor, and authority-escalation attacks | CONTROL_OFFLINE | preserved defect and sampled attack regressions |
| Scale endpoint reservation structurally to 160 ready packets | CONTROL_SYNTHETIC | 12/12 scale cases; explicit exact/fallback modes |
| Establish live WH3 performance or tactical superiority | UNVERIFIED | no runtime orders, route simulation, or matched outcomes |

## v0.1Y SFO combined-session preparation capability update

| Capability | Classification | Evidence |
|---|---|---|
| Capture exact WH3 executable, SFO full-pack, probe-pack, load-order, and owner-settings identity | CONTROL_OFFLINE_PREPARED | strict parsers, hashing, and exact-two-pack tests |
| Reject additional active mods from the SFO certification cohort | CONTROL_OFFLINE | explicit extra-mod regression |
| Checkpoint the append-only combined log and verify byte-prefix continuity | CONTROL_OFFLINE | deterministic six-checkpoint artifact and tamper tests |
| Recognize current `battle_replay_shadow` runtime marker | CONTROL_OFFLINE | source/collector compatibility regression |
| Export path-free SFO combined evidence while preserving raw/checkpoints locally | CONTROL_OFFLINE_PREPARED | workflow privacy regression |
| Prove campaign → battle → campaign continuity under SFO | UNVERIFIED_OWNER_RUN_REQUIRED | one uninterrupted live session pending |
| Certify SFO compatibility beyond one exact pack/settings/load-order profile | UNVERIFIED | requires version-bound broader cohorts |

## v0.1Y-r5 watcher startup calibration

| Capability | Status | Scope |
|---|---|---|
| Exact owner-machine SFO environment preflight | OWNER_MACHINE_PREFLIGHT | one WH3 executable, one SFO pack hash, one shadow-probe hash, exact two-pack order |
| Handshake-token watcher readiness | CONTROL_OFFLINE | schema-2 private watcher status/manifest |
| Owner-machine watcher startup after token repair | UNVERIFIED | rerun required |
| SFO campaign → battle → campaign continuity | UNVERIFIED | live five-turn/two-battle session required |

## v0.2D policy-layer capability note

No WH3 interaction capability is promoted by v0.2D. Cross-corpus policy construction and evaluation are `CONTROL_OFFLINE`; runtime command issue, acceptance, acknowledgement, execution, route completion, formation feasibility, causal outcome attribution, and tactical superiority remain `UNVERIFIED` or `UNAVAILABLE` exactly as before.

## v0.2O native/SFO behavior benchmark preparation

| Capability | Classification | Evidence |
|---|---|---|
| Reproduce v0.2N owner behavior result from raw diagnostic trace | OBSERVED + CONTROL_OFFLINE | raw owner trace recomputes exact result digest `ebe747ca...` |
| Separate territorial vs non-territorial temporal windows without changing v0.2N thresholds | CONTROL_OFFLINE | deterministic population stratifier + regressions |
| Bind SFO benchmark to exact Workshop pack, WH3 executable, probe and exact two-pack launcher profile | CONTROL_OFFLINE_PREPARED | SFO profile binder; hash/extra-mod rejection tests |
| Attribute a SFO/vanilla behavioral difference to a specific SFO DB row | UNVERIFIED | SFO changes many systems; later narrow ablation required |
| Use privileged diagnostic state at application time | UNAVAILABLE_BY_POLICY | `application_eligible=false`, application `PROHIBITED` |
