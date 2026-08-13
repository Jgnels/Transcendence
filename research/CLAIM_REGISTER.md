## v0.2N native diagnostic behavior-study claims — AUTHORITATIVE

| ID | Claim | Status | Evidence / boundary |
|---|---|---|---|
| C-V02N-01 | v0.2M-r1 telemetry qualification passed on the successful owner vanilla run | OBSERVED_DERIVED_OWNER_EVIDENCE | exact uploaded bundle SHA-256 `99c7ad0b1d08441307e65815801e29c0ee38d4067fb8aa864b88fcc6c98a0c02`; 1,588 paired faction-turns / 2,353 matched army-turns / 967 moved / 426 trajectories |
| C-V02N-02 | The completed v0.2M-r1 cohort confirms native recovery failure or temporal churn | REJECTED | endpoints refined post-hoc and old probe had no battle-participant telemetry |
| C-V02N-03 | WH3 campaign-manager scripting exposes a populated pending-battle cache and attacker/defender military-force CQIs to `ScriptEventPendingBattle` listeners | VERIFIED_SCRIPT_SOURCE_DOCUMENTATION | generated WH3 campaign-manager docs / `lib_campaign_manager.lua` surface |
| C-V02N-04 | v0.2N can certify an old no-battle-channel log as battle-free | REJECTED_BY_CONTRACT | confirmatory evaluator requires `battle_participant_telemetry=true` |
| C-V02N-05 | A recovering army appearing attacker-side during its own faction turn proves voluntary bad strategic intent | NOT_SUPPORTED | stronger offensive-use proxy only; ambush/interception/special mechanics require causal review |
| C-V02N-06 | Repeated battle-free stable-context heading reversals reveal native task IDs, assignment memory or engine hysteresis | NOT_SUPPORTED | observable realized-trajectory pathology only; engine internals remain unavailable |
| C-V02N-07 | A positive v0.2N endpoint directly authorizes project strategic control | REJECTED | positive result can earn causal review then narrow native-row ablation only |
| C-V02N-08 | Privileged diagnostic state may feed application decisions because it improved research quality | REJECTED_ARCHITECTURE_POLICY | `application_eligible=false`; player-visible/native-first application boundary unchanged |

## v0.2M diagnostic-telemetry claims

| ID | Claim | Evidence label | Boundary |
|---|---|---|---|
| C-V02M-01 | The owner v0.2L vanilla capture produced 0 eligible primary windows across 187 four-frame actor windows | OBSERVED_DERIVED_OWNER_EVIDENCE | 149 visibility-censored + 38 non-directional |
| C-V02M-02 | Zero v0.2L eligible windows is an instrument-exposure failure, not evidence of good native hysteresis | SUPPORTED_LIMITING_RESULT | frozen D107/D109 interpretation |
| C-V02M-03 | WH3 scripting documents `FactionTurnStart`/`FactionTurnEnd` faction contexts and `FACTION_SCRIPT_INTERFACE:military_force_list()` | DOCUMENTED_SCRIPT_SURFACE | does not by itself prove live owner probe behavior |
| C-V02M-04 | The deterministic v0.2M diagnostic pack is read-only and application-ineligible by construction | CONTROL_OFFLINE | manifest/source/static tests |
| C-V02M-05 | Privileged diagnostic telemetry is permitted for development but forbidden as an application-time information source | ARCHITECTURE_POLICY | two-plane boundary |
| C-V02M-06 | The v0.2M-r1 live diagnostic channel yields sufficient movement exposure under owner WH3 | OBSERVED_DERIVED_OWNER_EVIDENCE | 1,588 paired faction-turns; 2,353 matched force-turns; 967 moved; 426 trajectory pairs; zero capability/incomplete-normal-faction failures |
| C-V02M-07 | Any diagnostic heading reversal proves native task churn or missing hysteresis | REJECTED | descriptive exposure only until separately preregistered |

## 2026-08-02 v0.2L directional-churn preregistration claims — AUTHORITATIVE

- `VERIFIED_REPO_FACT`: v0.2L freezes a confirmatory endpoint before new owner data: repeated non-overlapping same-actor/same-region-pair A→B→A visible-region direction episodes under exact observed non-target context stability.
- `VERIFIED_REPO_FACT`: each candidate requires two >=120-degree movement-heading reversals; one A→B→A episode cannot trigger the primary signal.
- `VERIFIED_REPO_FACT`: v0.2L rejects privileged foreign visibility and remains `NO_ORDERS / PROHIBITED` with no strategic-assignment application import.
- `SUPPORTED_DERIVED_OWNER_EVIDENCE_LIMITING_RESULT`: preserved turns 4–7 yield zero eligible v0.2L primary windows; therefore they do not test native hysteresis.
- `NOT_CLAIMED`: a positive v0.2L cluster is not proof of native task thrashing or missing engine-internal hysteresis because hidden context remains unavailable.
- `NOT_CLAIMED`: zero observed clusters is not proof of adequate native assignment memory/hysteresis.
- `INFERENCE`: a reproducible positive cluster can justify testing the smallest mechanistically related native-row treatment before any project-owned strategic planner.
- `VERIFIED_REPO_FACT`: the v0.2L owner harness fail-closed binds VANILLA/SFO launcher profile, executable/probe/SFO hashes, consecutive-turn protocol and public-safe export; deferred local-probe materialization is the only modeled launcher exception and still requires the exact runtime-loaded shadow probe hash.
- `VERIFIED_REPO_FACT`: D109 freezes sequential acquisition before owner data: VANILLA first; SFO is requested only if vanilla yields at least one eligible primary window. This changes acquisition burden, not the endpoint.

## 2026-08-02 v0.2K acquisition claims — AUTHORITATIVE

- `VERIFIED_REPO_FACT`: the normal shadow probe obtains foreign characters/regions through WH3 player-filtered foreign visibility lists and labels that provenance.
- `VERIFIED_REPO_FACT`: v0.2K has a separate partial-trace evaluator/runtime adapter with `NO_ORDERS` and application `PROHIBITED`; it does not import the v0.2F/v0.2G assignment pipeline.
- `SUPPORTED_DERIVED_OWNER_EVIDENCE`: preserved owner turns 4–7 expose seven foreign factions across enough frames for partial longitudinal reprocessing; 37 comparable visible-force intervals contain 36 position-stable intervals and one ambiguous movement interval.
- `NOT_CLAIMED`: 36/37 position stability does not establish native CAI idleness, clumping, passivity, or failure.
- `UNAVAILABLE`: full foreign-faction front coverage, full response latency, recovery misuse, reserve adequacy, native task identity, assignment exclusivity, assignment memory, and hysteresis are not established by the player-visible partial trace.
- `INFERENCE`: richer player-visible longitudinal evidence may reveal review candidates for native behavior, but a future owner run must be tied to a preregistered question rather than generic data collection.

## 2026-08-02 post-review claim corrections — AUTHORITATIVE

- **SUPPORTED:** Current WH3 has native task generation and an allocation phase in which tasks and armies are paired; an additional batching pass combines same-type/same-target tasks. Source: CA Hotfix 6.3.4.
- **SUPPORTED:** Native task evaluation uses distinct threat and battle-strength concepts; owned forces are evaluated against target strength and insufficient force strength can trigger recruitment. Source: CA Campaign AI Beta #2.
- **SUPPORTED:** Native distance scaling is measured in turns and considers movement extents, applicable stances, and recruitment distance/time. Source: CA Campaign AI Beta #2.
- **SUPPORTED:** Patch 8.1 introduced campaign-turn-dependent priority control and used it to lower late-game defensive-task priority and slightly increase enemy-force task priority.
- **UNVERIFIED:** exact Patch 8.1 table/column/variable/script exposure.
- **INVALIDATED as confident claim:** current WH3 uses MCTS.
- **UNVERIFIED/UNKNOWN_ENGINE_INTERNAL:** native explicit reserve policy, recovery protection, assignment exclusivity, temporal commitment, reassignment hysteresis.
- **UNCALIBRATED_HYPOTHESIS:** project 2–4 turn commitment and 0.15 reassignment margin.
- **INVALIDATED as next-step claim:** assignment-derived v0.2I transport is the highest-value engineering task before row/schema reconciliation.

## v0.2I-r3 claims

- **OBSERVED / LIMITING_RESULT:** owner WH3 executes the real/UI feasibility poll while the runtime-created request remains unseen (`request_seen=false`).
- **SUPPORTED_OFFLINE:** an exact prior `NO_ORDERS` / `PROHIBITED` plan can be semantically validated, embedded into a deterministic session-local PFH5, and hash-bound to the preflight environment.
- **SUPPORTED_OFFLINE:** the public adjudicator rejects a retry unless the new observer-safe snapshot reproduces the exact saved plan and exact query/result cardinality.
- **UNVERIFIED:** the precise engine/OS reason `io.open(..., "r")` cannot see the request.
- No claim of order issue, acknowledgement, execution, route safety, action legality, or causal outcome is promoted.

## v0.2I-r2 claims

- **OBSERVED:** the exact owner WH3 + SFO runtime executed the r1 real/UI polling callback.
- **SUPPORTED:** the second limiting result was caused by the local parser rejecting a newly emitted diagnostic event before request generation.
- **CONTROL/OFFLINE VERIFIED:** r2 statically requires every dedicated feasibility-probe event to be parser-allowlisted and accepts/summarizes a campaign-feasibility diagnostic session.
- **NOT CLAIMED:** request consumption, query success, route legality, order issue, acknowledgement, execution, or causal outcome.

# Claim Register

## v0.2I-r1 claims

- **C-V02I-R1-01 — OBSERVED:** the owner runtime loaded the exact dedicated feasibility probe with SFO, emitted a first-tick snapshot, and the local deterministic stack produced a five-query turn-6 request for `force:928`.
- **C-V02I-R1-02 — LIMITING_RESULT:** the v0.2I session emitted `FEASIBILITY_EXECUTOR_READY` but zero query results, explicit request rejections, or packet-end markers. This does not establish query unavailability.
- **C-V02I-R1-03 — SUPPORTED:** model-time polling is unsuitable for an intentionally idle campaign-map request bridge; the active hotfix uses UI-synchronized real polling.
- **C-V02I-R1-04 — CONTROL_OFFLINE:** the r1 timer correction changes only transport scheduling and diagnostics; policy remains `NO_ORDERS` and application remains `PROHIBITED`.

## v0.2I claims

| ID | Claim | Evidence label | Boundary |
|---|---|---|---|
| C-V02I-01 | A dedicated campaign-only pack can deterministically encode the bounded live-feasibility observer/executor | CONTROL_OFFLINE | pack build + static/runtime regression |
| C-V02I-02 | Current-state query selection is reproducibly derived through canonical v0.2E→v0.2H code and capped at 16 exact queries | CONTROL_OFFLINE | sidecar integration + tests |
| C-V02I-03 | A no-assignment current snapshot emits no live request | CONTROL_OFFLINE | fail-closed sidecar contract |
| C-V02I-04 | The collector can independently reconstruct the saved plan and reject foreign/stale/cardinality-drifted results | CONTROL_OFFLINE | artifact-builder tests |
| C-V02I-05 | The owner WH3+SFO runtime actually loads the new pack and returns the requested campaign query results | UNVERIFIED | requires one live owner packet |
| C-V02I-06 | A returned true reachability result proves a safe route, legal campaign action, acknowledgement, execution, or success | REJECTED | query evidence is narrower |
| C-V02I-07 | v0.2I grants campaign order authority | REJECTED / PROHIBITED | no mutation/order adapter |

## v0.2H claims

| ID | Claim | Evidence label | Boundary |
|---|---|---|---|
| C-V02H-01 | v0.2G assignments can be deterministically converted into bounded read-only feasibility query plans | CONTROL_OFFLINE | frozen envelope + matrix |
| C-V02H-02 | WH3 documentation exposes character/force CQI lookup and point/settlement reachability query surfaces | DOCUMENTED | source audit; not owner-runtime observation |
| C-V02H-03 | Preserved Reikland turn 7 maps to one eight-query historical plan for `force:65`/character `120`/force `65` | CONTROL_OFFLINE over observed source | all results unobserved |
| C-V02H-04 | A faction-centroid assignment remains point-only and never becomes an attack target | CONTROL_OFFLINE | matrix + exact turn-7 plan |
| C-V02H-05 | REGION targets can expose settlement-interface reachability questions without granting action authority | CONTROL_OFFLINE over documented surface | no attack/order call |
| C-V02H-06 | Supplied read-only query observations can be adjudicated without granting application/execution/outcome authority | CONTROL_SYNTHETIC | synthetic observation matrix |
| C-V02H-07 | The owner build has actually returned the v0.2H campaign reachability results | UNVERIFIED | no live v0.2H packet yet |
| C-V02H-08 | A true reachability query proves a safe/legal route or successful campaign order | REJECTED | query scope is narrower |
| C-V02H-09 | v0.2H can issue campaign orders | REJECTED / PROHIBITED | no runtime mutation adapter |

## v0.2G claims

| ID | Claim | Status | Evidence |
|---|---|---|---|
| C-V02G-01 | Exact v0.2F priorities can be deterministically mapped onto unique controlled-army shadow slots | CONTROL_OFFLINE | frozen v0.2G force-allocation artifact and matrix |
| C-V02G-02 | Critical overflow can be expanded without losing source obligations | REPLICATED_SYNTHETIC | adversarial shortage fixture |
| C-V02G-03 | Recovery/reserve constraints and actor exclusivity are enforced | REPLICATED_SYNTHETIC | deterministic assignment matrix |
| C-V02G-04 | Small geometric changes can be prevented from causing immediate actor churn | REPLICATED_SYNTHETIC | temporal adversarial fixtures; timing constants uncalibrated live |
| C-V02G-05 | Observed Reikland turn 7 yields one coherent-rival shadow assignment | SUPPORTED_OFFLINE | one-army early-campaign evidence only |
| C-V02G-06 | Straight-line geometric ETA establishes campaign route feasibility | INVALIDATED_AS_CLAIM | reference-only by contract |
| C-V02G-07 | A disappeared priority proves the shadow plan succeeded | INVALIDATED_AS_CLAIM | retirement is `NO_CAUSAL_CREDIT` |
| C-V02G-08 | v0.2G can issue, acknowledge, execute, or evaluate outcomes of campaign orders | UNVERIFIED / PROHIBITED | no runtime order adapter exists |
## v0.2F strategic/theater portfolio claims

| ID | Claim | Status | Evidence |
|---|---|---|---|
| C-V02F-01 | A deterministic six-record strategic portfolio can be built from observer-safe v0.2E challenge evidence without orders | CONTROL | frozen v0.2F cross-evidence artifact |
| C-V02F-02 | Critical strategic sources can remain fully represented when more than six obligations exist | CONTROL | seven-critical-front overflow fixture, 1.0 source coverage |
| C-V02F-03 | War count need not create one aggression commitment per hostile faction | CONTROL | fragmented-pressure case + empty-war-edge metamorphic check |
| C-V02F-04 | A front crisis or total-force recovery can veto new aggressive commitment while retaining rival awareness | CONTROL | crisis/coherent-rival and all-recovering fixtures |
| C-V02F-05 | Player/human identity is required to select strategic pressure priorities | INVALIDATED_FOR_TESTED_CASES | player→NPC semantic invariance |
| C-V02F-06 | v0.2F assigns armies, proves routes, or issues campaign orders | REJECTED | force assignment `NOT_PERFORMED`, application `PROHIBITED` |
| C-V02F-07 | Six priorities / one aggressive channel is a WH3-optimal policy | UNVERIFIED | engineering constraint only |

## v0.2E campaign strategic challenge claims

| ID | Claim | Status | Evidence |
|---|---|---|---|
| C-V02E-01 | Observer-safe campaign snapshots can be deterministically classified for visible rival structure and front pressure without game orders | CONTROL | v0.2E envelope + 8-case matrix |
| C-V02E-02 | Hidden hostile armies do not affect v0.2E strategic benchmark semantics | CONTROL | hidden-enemy metamorphic injection |
| C-V02E-03 | Human/player identity is not required by v0.2E strategic quality semantics | CONTROL | `player_empire`→`npc_empire` metamorphic invariance |
| C-V02E-04 | Turn-7 Marienburg is a coherent visible-rival candidate in the v0.1J observed snapshot | SUPPORTED_OFFLINE | two visible Marienburg armies, one observed region, 100% visible hostile army share |
| C-V02E-05 | Turn-7 Marienburg was durably coordinated or strategically intelligent | UNVERIFIED | snapshot cannot establish intent, economy, diplomacy, or longitudinal behavior |
| C-V02E-06 | v0.2E measures anti-player bias | INVALIDATED | explicitly unavailable without targeting history/counterfactuals |
| C-V02E-07 | v0.2E proves improved late-game WH3/SFO campaign quality | UNPROVEN | early observed inputs + synthetic late-game reference only |

| ID | Claim | Status | Evidence |
|---|---|---|---|
| C001 | The captured settings baseline is pure vanilla WH3 v8.1.1 build 48122.4194776 | OBSERVED | owner screenshots and explicit owner confirmation |
| C002 | SFO materially alters campaign and battle environment | OBSERVED | 612 DB files across 338 table families in the extracted audit |
| C003 | SFO is one unified replacement strategic AI | INVALIDATED | source surface combines DB environment changes, native CAI edits, mechanic/UI scripts, and bounded state interventions |
| C004 | DeepWar is concentrated on native CAI and difficulty tables | OBSERVED | PFH5 index: 15 DB files, 14 direct native-CAI families |
| C005 | Hecleas reaches strategic CAI, diplomacy, campaign behavior, and autoresolve | OBSERVED | PFH5 index: 28 DB files including those families |
| C006 | DeepWar and Hecleas can be enabled together without conflict | UNVERIFIED | 10 shared table families create material row/load-order conflict risk |
| C007 | SFO directly applies some AI accommodations and scripted interventions | SUPPORTED | supplied Lua includes AI vow progression, direct bonuses, force/region/resource mutations, and scripted recovery paths |
| C008 | SyntheticLab v0.1B is deterministic for identical inputs and seeds | REPLICATED | automated tests and repeated smoke runs in the build environment |
| C009 | SyntheticLab predicts WH3 campaign or battle outcomes | INVALIDATED | all Tier 2–4 outputs are explicitly uncalibrated |
| C010 | Ordinary WH3 battle AI can be directly replaced by a normal mod | UNVERIFIED | requires capability probe |
| C011 | Army Objective Assignment required observations are available in campaign scripts | LIMITING_RESULT | turns 4–7 observed strength, movement, health, stance, position, region structure/siege, wars, and visible entities; early-turn coverage, outcome calibration, acknowledgements, and additional faction/SFO cases remain |
| C012 | The probe builder produces byte-identical script-only PFH5 Mod packs for identical inputs | REPLICATED | two independent builds; pack hashes and aggregate digest match |
| C013 | The observer probe contains no campaign or save mutation calls | SUPPORTED | static prohibited-call regression test; live runtime behavior remains unverified |
| C014 | WH3 loads `script/campaign/mod` probe scripts and writes their `ModLog` records | OBSERVED | pure-vanilla owner-machine run; raw log SHA-256 `ddf462130e6551c034ddd5e79dfc916fba0a133cfa0cf6ef715e6df7afd1f9f7` |
| C015 | WH3 can return player-visibility-filtered foreign characters and regions to the probe | OBSERVED | both `get_foreign_visible_*_for_player` calls returned bounded records in the pure-vanilla run |
| C016 | One namespaced project integer survives save/reload in the tested disposable pure-vanilla campaign | REPLICATED | exact persistence pack; isolated `WRITE 0→1` and same-save `RELOAD 1→2`; verifier semantic digest `b996cc93f07275bc8d36fa428baa5e055ee03ba19bebc113175beedf048198bb` |


| C017 | `FIRST_TICK` is a stable canonical planner snapshot | INVALIDATED | local-turn-start exposed 3 more visible characters and 2 more visible regions in the same turn |
| C018 | Two independent observer sessions produced semantically identical structured observations | REPLICATED | exact corrected pack, distinct collection evidence, byte-identical raw logs, shared semantic digest `947d9aa1815485a7ba844d79b20e680ea8e36ed5eeb108a8fc5692e7e2bfb6f7` |
| C019 | The v0.1D filename-matched observer loader entrypoint executes successfully in WH3 | OBSERVED | second raw log contains invocation and successful completion |
| C020 | Reality Gate observer acceptance has two clean sessions using the exact same corrected pack hash | REPLICATED | two independent collections used observer SHA-256 `0c1dd8940a697a2d840876f08092ba02f988170e90c5f77b6f934ac15c79f173`; verifier digest `4bd1ad7bf39e086fa26d1dad3265da1a487db437b4d51b2d5715a4a2203326f` |
| C021 | A transport-sensitive summary digest is sufficient for cross-run semantic comparison | INVALIDATED | filename and unrelated non-probe line offsets changed the digest without changing structured observation semantics |
| C022 | Byte-identical observer logs imply the sessions were not independent | INVALIDATED | collection independence is established by distinct manifest hashes/timestamps; deterministic output may be byte-identical |
| C023 | The persistence pack's environment-aware two-phase verifier is sufficient by itself as WH3 evidence | INVALIDATED | live evidence was still required; the verifier now confirms the supplied real write/reload sessions rather than replacing them |

| C024 | Transport-sensitive persistence verifier digests are stable across renamed uploads | INVALIDATED | re-verification changed the result digest when uploaded filenames changed |
| C025 | The v0.1G persistence semantic digest is stable across renamed logs/manifests | SUPPORTED | regression test removes filenames but retains evidence hashes, collection IDs, timestamps, states, and pack identity |
| C026 | The shadow-input pack can observe all planned expanded campaign fields in WH3 | OBSERVED_PARTIAL | four live snapshots, turns 4–7, contain the planned campaign fields; explicit v0.1J eligibility and armed-citizenry fields require a corrected run |
| C027 | The shadow pipeline issues no campaign orders | SUPPORTED | source contains no order/application path; output mode is `SHADOW_NO_ORDERS`; static tests |
| C028 | Foreign strength and garrison estimates in the initial shadow slice avoid privileged exact values | SUPPORTED | foreign armies use visible unit-count proxy; foreign regions use settlement-structure proxy |

| C029 | The consolidated offline shadow pipeline deterministically processes five consecutive turn snapshots and emits no game orders | REPLICATED | two identical five-turn fixture runs; result digest `7adeac641b0ad95dbd039530f731e08e1301fcac8b1b3804bbc37e41a79ad45a` |
| C030 | One prepared live multi-turn run can prove expanded campaign and ordinary-battle observation | UNVERIFIED | first run lost early/battle runtime segments; v0.1J append-only transport requires live proof |
| C031 | The combined shadow pack is deterministically built with separate campaign and battle scripts | SUPPORTED | two-entry PFH5 manifest, byte-identical v0.1J builds, static tests |
| C032 | The project can parse and report detailed ordinary-battle telemetry without issuing orders | SUPPORTED_OFFLINE | deterministic valid fixture plus malformed, hidden-leak, and incomplete-sample rejection tests |
| C033 | The v0.1I battle source cannot issue battle orders or create unitcontrollers | SUPPORTED | static source guard and explicit authority report; live runtime still unverified |
| C034 | WH3 ordinary battles will load the v0.1I battle script and expose all requested fields | UNVERIFIED | primary interface documentation only; one live manually fought battle required |
| C035 | Observed command-handler events prove command acceptance or tactical effectiveness | INVALIDATED | event observation lacks acknowledgement, execution, and causal outcome evidence |
| C036 | One combined five-turn campaign and one-battle session is sufficient to establish tactical-AI quality | INVALIDATED | it establishes interface feasibility and descriptive telemetry only; quality needs broader cohorts |
| C037 | WH3 may return the same controlled region through both owned-region and player-visible-region interfaces in one canonical snapshot | OBSERVED | first consolidated owner log: four turn snapshots parsed before `duplicate region id: wh3_main_combi_region_altdorf`; v0.1I-r2 preserves one owned-precedence entity and rejects owner conflicts |
| C038 | The first consolidated owner run already satisfies the full five-turn campaign-and-battle gate | INVALIDATED | preserved summary contains only four canonical turn-start snapshots, turns 4–7; battle evidence was not reached because the campaign adapter failed first |
| C039 | The recovery scan recovered the owner's early turns and battles | INVALIDATED | timestamp-scoped adjudication recovered only current-session turns 4–7 and zero live battle records; 72 apparent battle records and two completions were project fixtures |
| C040 | `lua_mod_log.txt` is a durable campaign-plus-battle transcript | INVALIDATED | primary mod-loader implementation opens it with `io.open(..., "w")` on the first `ModLog` call in each Lua runtime |
| C041 | An append-only project log can preserve separate campaign and battle runtime records | SUPPORTED_OFFLINE | campaign/battle source writes `transcendence_runtime_log.txt` in append mode; prepared-session and strict-collector regression tests; live proof pending |
| C042 | Every one-unit character force is a planner army | INVALIDATED | live turns 4–7 included two Master Engineer character forces that were incorrectly assigned; v0.1J explicit eligibility excludes nonfield forces |
| C043 | Exact own force strength can be compared directly with foreign visible-unit-count proxies | INVALIDATED | live reprocessing exposed ratios up to 14537.34; common-scale v0.1J proxy reduces the observed maximum to 1.65 |
| C044 | A field army occupying a settlement is settlement-garrison strength | INVALIDATED | live Eilhart/Fort Bergbres records double-counted Karl's field army; v0.1J accepts unit garrison evidence only from armed citizenry |
| C045 | Corrected v0.1J reprocessing produces a calibrated campaign policy | UNVERIFIED | assignments are internally coherent shadow hypotheses only; no order, acknowledgement, outcome, or owner-quality calibration exists |

| C-B401 | The exact Battle of Eilhart replay loads the battle probe and exposes a complete read-only ordinary-battle query session | OBSERVED | replay SHA `76b880…`, log SHA `611916…`, verification digest `fcfec3…` |
| C-B402 | The original replay record provides reliable continuous tactical timing | INVALIDATED | five phase samples over 739.6 seconds; expected about 247; 601.9-second maximum gap |
| C-B403 | Raw hierarchy-index unit IDs are stable across the replay | INVALIDATED | 50 static IDs reconcile to 34 canonical unique-UI identities with 16 aliases |
| C-B404 | Battle 4 establishes command acceptance or tactical-AI quality | REJECTED | command traffic is observation only; no acknowledgement/control path |
| C-B405 | Battle 4 can serve as a SyntheticLab calibration artifact | OBSERVED | Tier 4R corpus and deterministic stress-case derivation; no raw replay/log committed |
| C-B406 | Dual-clock dense sampling works in the owner replay | OBSERVED | 249 detail samples, 1,477 aggregates, 120 heartbeats, 3.4-second maximum gap, verification digest `a8f9e724d0c86cbff82af0a48842eb4e257356186a895b67f2660e6ddaba59d8` |


| C-B407 | Direct per-unit selection callbacks replay selected-unit context | LIMITING_RESULT | zero selection events while 397 commands replayed; ordinary live-battle behavior remains unverified |
| C-B408 | Dense state deltas can provide bounded command-candidate attribution | OBSERVED_INPUT_HYPOTHESIS_OUTPUT | 302 inferred command records, 121 high-confidence; labeled `INFERRED_NOT_ACKNOWLEDGED` |
| C-B409 | Battle 4 supports visibility-safe milestone scenarios for SyntheticLab | OBSERVED | eight Tier 4R state slices derived from the dense trace; foreign units require `VISIBLE_TO_LOCAL_ALLIANCE` |
| C-B410 | The Battle 4 dense trace provides exact total casualties | INVALIDATED | local terminal coverage 64.7059% and visible-enemy coverage 75%; totals remain lower bounds |
| C-B411 | A deterministic no-order tactical evaluator can run over real WH3 state slices without hidden-state leakage | REPLICATED_OFFLINE | eight-slice evaluator passes deterministic, privacy, visibility, and no-order tests; tactical quality remains a hypothesis |
| C-B412 | A deterministic canonical tactical-state trajectory can be derived from Battle 4 slices without hidden-enemy detail or order authority | REPLICATED_OFFLINE | eight states; result digest `cec345739fc6d4231b88f2cfb6814082ab0be970530da704f3b36d881f63cbb5`; visibility and determinism tests |
| C-B413 | v0.1M can extract bounded role-specific decision opportunities and pursuit-termination windows | REPLICATED_OFFLINE_IMPLEMENTATION / HYPOTHESIS_POLICY | 37 candidates, 25 selected, all critical covered, result digest `5af29dc6a23af6e82c8288ab321f1a06d1bb9583c8ddfea39b2c6f501d80670b` |
| C-B414 | Four Battle 4 severe-loss cases were definitely preventable | REJECTED | v0.1M labels four only `PLAUSIBLY_PREVENTABLE_SEVERITY`; all alternatives are unexecuted and causal effect is unverified |
| C-B415 | v0.1M proves that 50 advisory transitions are superior to 397 owner commands | REJECTED | ratio `0.125945` is workload/selectivity context only and is labeled `REFERENCE_ONLY_NOT_CAUSAL` |
| C-B419 | Repository validation is independent of checkout ancestor names | REPLICATED_CONTROL_OFFLINE | regression loads the validator beneath a `tmp` ancestor, tracks ordinary files, and excludes only repository-relative `dist/` content |
| C-B420 | The v0.1M validator safely handled checkouts beneath ignored-name ancestors | INVALIDATED | absolute path filtering could exclude every file before v0.1N correction |
| C-B421 | A six-instance advisory cap always preserves every critical tactical concern | INVALIDATED | v0.1O saturation fixtures reduce legacy critical-source coverage to 66.6667% and 60% |
| C-B422 | Grouping equivalent opportunity types can preserve bounded top-level workload without silently discarding critical sources | REPLICATED_CONTROL_OFFLINE | six-group and overflow fixtures retain 100% critical source coverage with at most six portfolio records |
| C-B423 | The v0.1O role-aware portfolio satisfies the current heterogeneous synthetic contract matrix | REPLICATED_CONTROL_SYNTHETIC | 16/16 scenario passes, 1.0 required-intent recall, 1.0 forbidden-intent safety, one scale-equivalence pass |
| C-B424 | v0.1O baseline alignment proves tactical superiority or casualty reduction | REJECTED | matrix is project-owned synthetic contract evidence with no executed commands, transition model, or outcomes |
| C-B425 | A critical overflow record is an executable assignment or command sequence | REJECTED | overflow preserves source awareness only; assignment, ordering, pathfinding, acknowledgement, and outcomes remain unverified |


| C-B426 | The v0.1P assignment layer can deterministically avoid double-booking local units | REPLICATED_CONTROL_OFFLINE | Battle 4 and 12-scenario matrix produce zero double-booked actors |
| C-B427 | Every critical advisory objective can always receive a legal actor | INVALIDATED | observed and synthetic routing/shattered subjects and single-responder conflicts remain explicitly unfilled |
| C-B428 | v0.1P can distinguish uncontrollable subjects, absent legal responders, and resource conflicts | REPLICATED_CONTROL_OFFLINE | three frozen unfilled-reason contracts |
| C-B429 | Reordering units or portfolio records changes assignment semantics | INVALIDATED_FOR_TESTED_CASES | 3/3 metamorphic checks preserve exact or semantic output |
| C-B430 | A v0.1P assignment proves a feasible WH3 order or improved outcome | REJECTED | straight-line proxy, no command channel, no acknowledgement, no execution, no causal outcome |

| C-B431 | v0.1Q can deterministically preserve or change abstract assignments through explicit lifecycle events | REPLICATED_CONTROL_OFFLINE | Battle 4 trajectory plus 12-scenario matrix; all outputs `NO_ORDERS` |
| C-B432 | Project-owned commitment and cooldown windows are measured WH3 action durations | REJECTED | windows are bounded anti-thrashing contracts only; no runtime timing calibration |
| C-B433 | Objective disappearance proves that the proposed action succeeded | REJECTED | lifecycle uses `PLAN_RESOLVED_BY_OBSERVATION_NOT_ATTRIBUTED` |
| C-B434 | Sparse Battle 4 milestone slices support continuous plan-history inference | INVALIDATED_FOR_THIS_CORPUS | 18 continuity-reset events and zero plan continuations |
| C-B435 | v0.1Q remains semantically stable under unit order, assignment-record order, and uniform coordinate translation | REPLICATED_CONTROL_SYNTHETIC | 3/3 metamorphic checks under seed `20260730` |
| C-B436 | A v0.1Q abstract schedule is an executable command sequence or proof of improved outcome | REJECTED | no command adapter, legality, acknowledgement, execution, route, or causal outcome evidence |

## v0.1R claims

| Claim | Status | Evidence / limit |
|---|---|---|
| Transcendence can deterministically separate command observation from issue, acknowledgement, state match, and outcome | CONTROL_OFFLINE | 12/12 matrix and strict packet |
| Battle 4 contains direct acknowledged commands | REJECTED | 397 callbacks, 0 direct selection attribution, 302 inferred only |
| A matching ordered position/current target proves acknowledgement | REJECTED | source audit and packet invariant |
| The v0.1R probe can issue orders | REJECTED | no unitcontroller/order primitive; static tests |
| The v0.1R pack is deterministic and read-only | CONTROL_OFFLINE | two identical builds; exact SHA-256 recorded |
| Ordinary live battle exposes useful selection/reachability/interruption evidence | UNVERIFIED | batched owner capture pending |
| v0.1R improves tactical outcomes | UNVERIFIED | no project issue or causal outcome evidence |


## v0.1S claims

| Claim | Status | Evidence / limit |
|---|---|---|
| Ordinary single-player battle selection events are observable | OBSERVED | 130 events in exact-pack complete session |
| Every observed command window in this capture was bound to selected local units | OBSERVED_FOR_THIS_CAPTURE | 89 bound, 0 unbound |
| Selection binding identifies command origin | REJECTED | callback origin remains unresolved |
| Raw callback-position reachability returned true and false | OBSERVED_RAW_WITH_LIMIT | 1,249 true / 38 false, but all false samples were zero-vector non-point callbacks |
| Ordered position and current target can match inside command-state windows | OBSERVED_NOT_ACKNOWLEDGED | 189 and 443 matches |
| Movement, routing, control loss, and interruption are visible | OBSERVED | 739 movement; one routing; one control loss; three observed close classes |
| Leaving-battle and shattered state are observed in the capture | UNVERIFIED | zero evidence counts |
| Reachability proves safe path completion or formation feasibility | REJECTED | point-in-time query only |
| The public packet proves project issue, acknowledgement, execution, or outcome | REJECTED | all issue/ack counts zero; causal attribution explicitly withheld |
| A second identical gameplay capture is required to close v0.1S | REJECTED | current gate criterion is capability observation, not cross-session replication |

## v0.1T claims

| Claim | Status | Evidence / boundary |
|---|---|---|
| The project deterministically generates bounded feasibility candidates from canonical schedules | SUPPORTED — CONTROL_OFFLINE | 15/15 matrix scenarios; Battle 4 34 envelopes / 102 points |
| Raw callback-position reachability returned both values in one ordinary battle | OBSERVED_RAW_WITH_LIMIT | v0.1U shows only 191 explicit-point true samples and zero valid explicit-point false samples |
| A true point query proves a complete route or safe arrival | REJECTED | contract explicitly limits support to the exact point and instant |
| Battle 4 candidate points are reachable | UNVERIFIED | all 34 envelopes are `QUERY_READY_NOT_OBSERVED` |
| The preserved private log can be transformed into a detailed public-safe packet without replay | SUPPORTED_OFFLINE / OWNER RUN PENDING | fixture-verifiable read-only re-export workflow |
| v0.1T issues or acknowledges orders | REJECTED | authority remains `NO_ORDERS`; counts fixed at zero |


## v0.1U claims

| Claim | Status | Evidence / boundary |
|---|---|---|
| Explicit nonzero Move callback points returned true reachability in the captured battle | OBSERVED, scoped | 16 windows / 16 actors / 191 qualified true samples |
| A valid false result was observed for an explicit command point | REJECTED_FOR_CURRENT_CAPTURE | all 38 raw false samples were zero-vector formation-callback telemetry |
| Non-point and opaque command callbacks may be used as exact-point feasibility evidence | REJECTED | 1,096 samples semantically not applicable |
| Ordered-position and visible-target state match at the first sample | OBSERVED_NOT_ACKNOWLEDGED | 16/16 Move actors and 48/49 Attack Unit actors |
| The live calibration proves any Battle 4 generated candidate is reachable | REJECTED | no candidate-level query exists for the 102 generated points |

## v0.1V–v0.1X claims

| Claim | Status | Evidence / limitation |
|---|---|---|
| Guarded packets authenticate complete plan identity and candidate geometry | CONTROL_OFFLINE | duplicate-plan regression and 15/15 matrix |
| Battle 4 has 34 ready tactical action packets | INVALIDATED | 34 packets exist; all 34 are deferred and 0 are ready |
| Endpoint reservation prevents selected endpoints from violating the 12 m development bound | CONTROL_SYNTHETIC | 14/14 matrix plus 12 scale cases |
| Endpoint reservation proves collision-free movement | REJECTED | no route, footprint, terrain, or collision simulation |
| The complete offline pipeline is deterministic under tested representation changes | CONTROL_SYNTHETIC | 256/256 cases, seed `20260730` |
| Structural scaling to 160 packets proves live performance | REJECTED | no WH3 runtime measurement |
| The new layers improve casualties or win probability | UNVERIFIED | no issued/acknowledged/executed intervention or matched outcomes |

## v0.1Y SFO combined-session claims

| Claim | Evidence label | Status |
|---|---|---|
| Exact SFO/WH3/probe/load-order identity can be captured without modifying the active list | CONTROL_OFFLINE_PREPARED | strict parser/hash tests |
| Append-log prefix continuity can be verified from private full-file checkpoints | CONTROL_OFFLINE | deterministic chain and tamper tests |
| Current `battle_replay_shadow` records are recognized by combined collection | CONTROL_OFFLINE | regression-locked correction |
| Public SFO combined exports exclude raw logs and private paths | CONTROL_OFFLINE_PREPARED | static workflow tests |
| Campaign → battle → campaign continuity works under the owner's exact SFO profile | UNVERIFIED | live session required |
| One passing SFO run proves broad SFO compatibility or tactical improvement | REJECTED | scope exceeds available evidence |

| C-SFO-YR5-01 | Exact owner-machine SFO preflight completed before watcher startup | OWNER_MACHINE_PREFLIGHT | v0.1Y-r4 owner output; exact SFO/probe/WH3 hashes and two-pack order | Does not prove either pack loaded in runtime |
| C-SFO-YR5-02 | Watcher readiness can be safely bound to a per-session token without PID equality | CONTROL_OFFLINE | v0.1Y-r5 watcher regression and static workflow audit | Windows owner-machine rerun still required |

## v0.1Z SFO observed claims

| ID | Claim | Status | Evidence |
|---|---|---|---|
| C046 | The exact SFO/Reikland owner session preserved six consecutive campaign turns and three completed ordinary land battles | OBSERVED | frozen path-free fixture bound to exact raw-log/checkpoint identities |
| C047 | Each of the three completed battles was followed by its own campaign-runtime return | OBSERVED | corrected schema-2 transition analysis and 130-prefix chain |
| C048 | The exact shadow probe produced dense schema-2 battle telemetry under SFO without project order authority | OBSERVED | 698 detail samples, 4,000 aggregates, 683 commands, 1,025 selections, 80 units; zero authority violations |
| C049 | Observed command events prove acknowledgement or causal execution | REJECTED | no project-issued order and no supported acknowledgement signal |
| C050 | Three Reikland land battles establish broad SFO tactical superiority or compatibility | REJECTED | no policy comparison; sieges, ambushes, reinforcements, factions, updates, and normal mod stack unobserved |
| C051 | The two preserved replays can be used as exact read-only tactical-alignment cohorts | QUERY_READY | exact replay/save hashes and shared campaign session are frozen; deep-dive playback pending |

## v0.2A SFO dual-replay claims

| ID | Claim | Status | Evidence / limit |
|---|---|---|---|
| C052 | The exact Ubersreik replay is visually identified and ends in Reikland Decisive Victory | OBSERVED | hash-bound full recording and exact replay identity |
| C053 | The exact Marienburg replay is visually identified and ends in Reikland Pyrrhic Victory | OBSERVED | two hash-bound overlapping recording segments and exact replay identity |
| C054 | The initial local hierarchy can be incomplete during reinforcement discovery | SUPPORTED_FOR_EXACT_COHORT | 3→16 and 1→20 observed local-unit discovery patterns |
| C055 | Victory grade alone is sufficient tactical-quality evidence | INVALIDATED_FOR_THIS_COHORT | both victories; duration and casualty cost differ materially |
| C056 | Local crisis may persist while visible enemy units are routing | SUPPORTED_FOR_EXACT_COHORT | Marienburg local routes overlap enemy collapse |
| C057 | Runtime battlefield identity and replay display title are interchangeable | INVALIDATED | both runtime corpora report Eilhart while visuals prove Ubersreik/Marienburg |
| C058 | Visible movement after an observed command proves acknowledgement or causal execution | REJECTED | no supported acknowledgement channel or project-issued order |
| C059 | The two replay traces are optimal policy demonstrations | REJECTED | owner behavior is reference-only and outcomes are not counterfactual comparisons |
| C060 | Two Reikland land battles prove broad SFO tactical superiority | REJECTED | no policy intervention, matched comparator, or battle/faction diversity |
## v0.2B Chaos defeat preparation claims

| Claim | Status | Boundary |
|---|---|---|
| The uploaded replay is the recorded `An Ogre's Folly` battle | OBSERVED | exact SHA-256/size plus matching embedded labels and visual identity |
| The recording is consistent with a Reikland defeat | OWNER_ATTESTED + SUPPORTED | normal result card absent; exact grade unverified |
| The visible battle follows an ordered deterioration sequence | SUPPORTED | broad visual phase interpretation only |
| Formation, reserve, piecemeal commitment, firing-lane, and failed-reset issues caused the defeat | UNVERIFIED | preserved only as bounded hypotheses pending dense telemetry |
| The exact replay is ready for read-only dense capture | CONTROL_OFFLINE | exact contract, scripts, tests, hashes; live playback still required |
| The shadow container is equivalent for battle observation | SUPPORTED/CONTROL_PREPARED | exact outer hash plus byte-identical battle-script hash only |
## v0.2C Chaos replay divergence claims

| Claim | Status | Boundary |
|---|---|---|
| Exact Chaos replay telemetry was captured under the exact SFO/probe environment | OBSERVED | 338.5-second nonterminal stream |
| The replay naturally completed | REJECTED | `BATTLE_COMPLETE` absent |
| The replay reproduced the original defeat | INVALIDATED | final snapshot nonterminal; zero terminal coverage |
| Original live battle was a defeat | OWNER_ATTESTED | exact grade not shown |
| Extreme elite cavalry and Tattersouls losses occurred before stream end | SUPPORTED | lower bounds, not terminal totals |
| Reserve was absent | REFINED | later Halberd commitment shows reserve-like capacity |
| Commands were acknowledged or causally effective | UNVERIFIED | inference only |
| Trace proves anti-Chaos superiority or a winning policy | REJECTED | no controlled intervention |

## v0.2D cross-corpus policy claims

| ID | Claim | Status | Evidence / limit |
|---|---|---|---|
| C061 | The exact four battle corpora can be reconciled into one deterministic read-only policy envelope | CONTROL_OFFLINE | exact dense/calibration digest binding; 17/17 matrix |
| C062 | Ubersreik, Marienburg, and Chaos display identities may differ from the repeated Eilhart runtime battlefield identity | OBSERVED_MULTI_SOURCE | v0.2A/v0.2C explicit identity layers; silent rewrite prohibited |
| C063 | Replay exhaustion is sufficient terminal-outcome evidence | REJECTED | Chaos remains `UNVERIFIED_NONTERMINAL` |
| C064 | Victory grade alone is sufficient tactical-quality scoring | INVALIDATED_FOR_CURRENT_COHORT | Ubersreik/Marienburg cost divergence |
| C065 | Severe high-value-asset review can be expressed with a model-count-scale-invariant loss ratio | CONTROL_OFFLINE / SUPPORTED_MULTI_CORPUS | 0.5 ratio trigger plus metamorphic scale test; causal benefit unverified |
| C066 | Target concentration proves tactical fixation or error | HYPOTHESIS_SINGLE_CORPUS | Chaos only; selection attribution absent |
| C067 | The v0.2D policy issues or executes WH3 orders | REJECTED | `NO_ORDERS`, application `PROHIBITED`, static AST regression |
| C068 | v0.2D proves tactical superiority, casualty reduction, or win-probability gain | UNVERIFIED | no issued/acknowledged/executed intervention or matched outcome cohort |


| C069 | Current vanilla WH3 exposes allocator policy variables for distance scaling, fresh-army recruitment, force release/return, and recruiting/non-recruiting horizons | OBSERVED_PACK_ROW | owner-exported current vanilla `cai_task_management_system_variables_tables`; full binary layout consumed exactly |
| C070 | Current vanilla WH3 exposes timed/endgame task-priority data including `wh3_combi_tms_generator_group_endgame_overrides` and elapsed-round/timed-priority variable groups | OBSERVED_PACK_ROW | owner-exported current vanilla task-generator junction and variable-group rows |
| C071 | Current vanilla WH3 contains explicit player-specific threat/strength multipliers | OBSERVED_PACK_ROW | owner-exported `cai_personality_variable_set_junctions_tables`: `ai_threat_score_personality_multiplier_player` and `coordinator_player_strength_multiplier` |
| C072 | DeepWar broadly changes `cai_personalities_tables` because it carries a ~175 KB copy | INVALIDATED | decoded payload is byte-identical to owner current vanilla after DB header |
| C073 | Native reserve preservation, recovering-army protection, assignment exclusivity, temporal commitment and reassignment hysteresis are proven absent | NOT_SUPPORTED | no decoded row or official evidence establishes absence; remain `UNKNOWN_ENGINE_INTERNAL` / behavioral measurement questions |
| C074 | v0.2I assignment-feasibility transport is required before native CAI capability discovery can proceed | INVALIDATED | current owner DB rows resolved high-value allocator/priority/fairness surfaces offline while v0.2I remained paused |

| C075 | The fresh v0.2N vanilla behavior cohort is confirmatory-eligible and independently reproducible from its raw trace | OBSERVED_OWNER_RUNTIME | source bundle SHA `9416e0...`, 12 consecutive Reikland markers, 2,649 paired faction turns, 615 complete battles, zero capability/incomplete-sequence failures; recomputed result digest `ebe747ca...` |
| C076 | The v0.2N recovery endpoint had sufficient exposure but did not cross its preregistered signal threshold | OBSERVED_OWNER_RUNTIME | 38 damaged army-turns; 6 attacker-side reentry army-turns; rate 0.157895 vs frozen 0.20 threshold |
| C077 | The v0.2N temporal endpoint formally observed a repeated battle-free reversal signal | OBSERVED_OWNER_RUNTIME | 106 eligible windows, 18 reversal candidates, one force with two non-overlapping candidate intervals |
| C078 | The only repeated v0.2N trigger is representative proof that ordinary territorial CAI lacks hysteresis | NOT_SUPPORTED | trigger is `wh2_dlc11_cst_rogue_grey_point_scuttlers`, with no owned regions/wars and a plausible fixed patrol-route explanation |
| C079 | Retrospective territorial stratification of vanilla found 48 eligible windows, 13 single reversal candidates and zero repeated territorial forces | POST_HOC_CAUSAL_REVIEW | hash-frozen v0.2N raw trace; definition selected after vanilla result and not promoted to fresh confirmation |
| C080 | Grey Point Scuttlers are intended to remain at sea and patrol a specific route | MODDER_COMMUNITY_CLAIM | Total War: WARHAMMER community documentation; consistent with owner telemetry but not an official CA implementation statement |
| C081 | v0.2O can compare a fresh SFO cohort against the frozen vanilla behavior reference without copying the SFO binary | CONTROL_OFFLINE_PREPARED | exact SFO/profile binder, benchmark stratifier, owner-kit builder and focused regressions; owner SFO run pending |

### C082 — Vanilla territorial cluster sensitivity
**Claim:** The hash-frozen vanilla v0.2N territorial reprocess contains 48 eligible windows, 13 single reversal candidates, and a leave-one-faction-out candidate-rate range of 0.222222–0.317073.
**Class:** `SUPPORTED_DERIVED_OWNER_EVIDENCE`
**Limit:** Descriptive sensitivity only; not randomized, not a CI, not a p-value.

### C083 — Captured SFO task-priority directionality
**Claim:** In the decoded targeted owner row corpus, SFO carries 93 task-generator junction rows; 88 differ from vanilla and all 88 priority changes are increases across 30 groups / 13 generators.
**Class:** `VERIFIED_MOD_SOURCE_OR_PACK_FACT`

### C084 — No captured SFO allocator-variable override
**Claim:** The decoded targeted owner row corpus contains no SFO rows in `cai_task_management_system_variables_tables`.
**Class:** `VERIFIED_MOD_SOURCE_OR_PACK_FACT`
**Limit:** Does not prove SFO cannot affect allocation/recovery indirectly through other tables, scripts, mechanics, or engine interactions.

### C085 — SFO row difference is not causal attribution
**Claim:** A matched SFO-vs-vanilla behavior difference can nominate a mechanism for replication but cannot establish that an SFO row caused the difference.
**Class:** `METHODOLOGICAL_CONSTRAINT`


### C086 — Fresh SFO benchmark formally exceeds the frozen vanilla territorial cluster envelope
**Claim:** SFO has 39 eligible territorial windows, 18 reversal candidates, rate 0.461538, zero repeated territorial forces; frozen v0.2P branch is descriptive worsening.
**Class:** `SUPPORTED_DERIVED_OWNER_EVIDENCE`

### C087 — Fresh SFO recovery does not meet the preregistered positive threshold
**Claim:** 56 damaged-army exposures, 8 attacker-side reentries, rate 0.142857.
**Class:** `OBSERVED_OWNER_RUNTIME`

### C088 — SFO aggregate elevation survives every single-faction deletion
**Claim:** SFO leave-one-faction-out territorial candidate-rate range is 0.382353–0.486486; all values remain above vanilla ceiling 0.317073.
**Class:** `SUPPORTED_DERIVED_OWNER_EVIDENCE`

### C089 — One-vs-one campaign composition is unstable enough to block causal row attribution
**Claim:** Only 6 of 47 union eligible territorial factions are shared; shared-faction rates are SFO 0.111111 vs vanilla 0.210526, reversing aggregate direction.
**Class:** `POST_HOC_CAUSAL_REVIEW`
**Limit:** Does not invalidate the frozen aggregate branch; it blocks causal interpretation and motivates replication.

### C090 — No native-row ablation is earned by v0.2P/v0.2Q evidence yet
**Class:** `GOVERNANCE_DECISION_SUPPORTED_BY_CURRENT_EVIDENCE`
