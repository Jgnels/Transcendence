## v0.2N confirmatory native-behavior study risks

- **Retrospective battle-free laundering:** old v0.2M-r1 logs had no battle channel. Mitigation: v0.2N evaluator requires explicit `battle_participant_telemetry=true`; old logs fail closed.
- **Attacker-side intent overclaim:** pending-battle attacker status may include ambush/interception/special mechanics. Mitigation: classify as `RECOVERING_ATTACKER_SIDE_BATTLE_REENTRY_CANDIDATE`, require causal review before any native-row treatment.
- **Overlapping reversal inflation:** consecutive A→B→A→B movement can create overlapping three-point reversals. Mitigation: the repeated-force primary signal requires at least two **non-overlapping** reversal windows; exact A→B→A→B→A is tracked separately.
- **Context-stability incompleteness:** unchanged wars/owned regions/stance/health/strength/units cannot prove unchanged native tasks or enemy context. Mitigation: temporal signal remains an observable pathology proxy, never engine-internal hysteresis proof.
- **Post-hoc threshold selection:** v0.2M-r1 exploratory observations informed v0.2N. Mitigation: all v0.2N thresholds/exclusions are frozen before a fresh cohort; old data is structurally nonconfirmatory.
- **Battle-listener perturbation or failure:** a new listener adds instrumentation overhead and may fail on owner runtime. Mitigation: read-only pcall-wrapped cache reads, explicit capability failures, incomplete battle-sequence rejection, and >=1 complete battle sequence required for confirmatory collection.
- **Privileged-state leakage:** full AI state remains a development-only information plane. Mitigation: no order imports, `application_eligible=false`, `NO_ORDERS / PROHIBITED`, normal player-visible observer remains separate.
- **Owner-burden drift:** matched SFO can double live work without useful denominator. Mitigation: SFO is conditional on confirmatory vanilla plus sufficient exposure in at least one endpoint.

## v0.2M diagnostic-telemetry risks

- **Hidden-state leakage into application:** highest new architecture risk. Mitigation: privileged artifacts are explicitly `application_eligible=false`; diagnostic tools have no order/application imports; normal shadow observer remains unchanged.
- **Research instrumentation perturbation:** a Lua listener may theoretically add runtime overhead. The first live v0.2M run is qualification-only and must inspect capability failures/log density before behavioral use.
- **Endpoint absence semantics:** a force missing from turn start/end is not automatically death/disband/merge/recruitment. v0.2M records endpoint absence without causal promotion.
- **Post-hoc endpoint drift:** v0.2L's A→B→A definition remains frozen and is not loosened. v0.2M qualifies a new data plane only; any behavior hypothesis requires a new preregistration after the first diagnostic capture.

## v0.2L native directional-churn preregistration risks

- **False causal attribution from visible oscillation:** even exact player-visible context stability cannot exclude hidden armies, diplomacy, recruitment state or native task changes. Mitigation: primary output remains a causal-review candidate, never `NATIVE_HYSTERESIS_FAILURE_PROVEN`.
- **Low eligible exposure:** the strict region-only/exact-context endpoint may produce few or zero windows. Mitigation: report the denominator; zero exposure is `INSUFFICIENT_ELIGIBLE_EXPOSURE`, not a clean bill of health.
- **Moving-target aliasing:** army anchors can create apparent direction changes as they move. Mitigation: confirmatory endpoint allows visible-region anchors only.
- **Single-retarget overinterpretation:** one legitimate emergency retarget can look like churn. Mitigation: one A→B→A window is insufficient; the primary signal requires two non-overlapping episodes for the same actor/region pair.
- **Observer perturbation:** human movement changes what AI can see/respond to and changes the player-visible anchor context. Mitigation: the sealed confirmatory capture uses `PASSIVE_NO_VOLUNTARY_CAMPAIGN_ORDERS` and profile binding.
- **Passive-cohort ecological validity:** a deliberately inactive Karl Franz campaign is not representative of ordinary play and may itself change AI incentives. Mitigation: v0.2L is an instrumentation/falsification cohort only; no general native-CAI quality claim is promoted from it.
- **Launcher materialization drift:** a local probe may be absent from prelaunch `used_mods.txt` and appear after launch. Mitigation: only that one probe materialization is permitted; non-probe entries, installed/staged hash, and runtime `PACK_LOADED` evidence remain exact.
- **Vanilla/SFO causal overclaim:** unmatched stochastic campaigns cannot establish treatment causality. Mitigation: initial profile comparison is descriptive and only nominates a bounded native-row ablation.

## v0.2K native behavior acquisition risks

| Risk | Status | Mitigation |
|---|---|---|
| Missing foreign armies are counted as absent coverage/reserve | CONTROLLED | full-faction metrics explicitly unavailable under partial visibility |
| Foreign army leaves fog-of-war and is labeled destroyed/reassigned | CONTROLLED | visibility loss is right-censored |
| Stationary map position is labeled idle/stuck AI | CONTROLLED | `POSITION_STABLE_NO_INTENT_INFERRED`; no quality threshold |
| Movement toward one of many nearby anchors invents a target | CONTROLLED | tied approach deltas become `AMBIGUOUS_VISIBLE_ANCHOR_APPROACH` |
| Direction change is labeled native task churn | CONTROLLED | only `VISIBLE_ANCHOR_DIRECTION_CHANGE_CANDIDATE_NOT_TASK_CHURN` |
| Research closes observability gap by reading hidden foreign force lists | PROHIBITED_NORMAL_OBSERVER | preserve `WH3_PLAYER_FILTERED_LISTS`; separate authorization required for any omniscient research mode |
| Existing turns 4–7 are overinterpreted as current global CAI quality | OPEN_AND_BOUNDED | historical owner-derived limiting result only; exact source/profile retained |

## 2026-08-02 post-review architecture risks — AUTHORITATIVE

### R-NATIVE-006 — File/table presence is mistaken for behavioral change

**Status:** OBSERVED FAILURE OF INFERENCE. DeepWar carries a large `cai_personalities_tables` file whose decoded payload is identical to vanilla. Mitigation: row-level diff before semantic attribution.

### R-NATIVE-007 — RPFM extraction format is trusted from the requested flag rather than inspected bytes

**Status:** MITIGATED. Owner extraction returned binary DB payloads despite `as_tsv=true`. Downstream tooling now detects text TSV vs binary DB and uses a narrow full-file decoder for supported layouts.

### R-NATIVE-008 — Native allocator tuning is bypassed by an explainable but less-informed project allocator

**Status:** OPEN / ARCHITECTURALLY GUARDED. Current vanilla exposes allocator distance/recruit/release-return policy rows. v0.2G remains evaluator-only unless native+tuning fails preregistered metrics.

### R-NATIVE-009 — Current player-specific threat/strength multipliers undermine fairness goals

**Status:** MEASURABLE/TUNABLE. Exact current vanilla rows exist. Treat as a fairness experiment surface; do not assume changing them alone improves strategic quality.

1. **Parallel-planner sunk-cost risk:** treating clean, tested v0.2F/G code as evidence that Transcendence should own responsibilities current WH3 already performs.
2. **Native-surface ignorance risk:** tuning project constants before exact 8.1 schema/rows and mature-mod deltas are decoded.
3. **Historical-value drift:** treating 2025 beta numeric values as current 8.1 values without row/runtime confirmation.
4. **Unknown-engine-internal fallacy:** converting lack of public documentation for native reserves/recovery/hysteresis into proof of absence.
5. **Transport optimization risk:** spending owner/runtime effort on assignment-derived v0.2I when its upstream application path may remain removed.
6. **Mod-success confounding:** calling budget, faction-potential, economy, autoresolve, recruitment or scripted-bypass pressure “better strategy.”
7. **Patch 8.1 exposure hallucination:** official existence of turn-dependent prioritisation does not prove a public DB/script control surface.
8. **Reviewer-staleness risk:** initial Grok/Kimi/Claude conclusions contain claims later retracted; future work must consult correction passes.

## v0.2I-r3 embedded-handoff risks

The runtime-created request-file path is no longer trusted for owner evidence. The embedded retry requires the same unchanged save/turn to reproduce the frozen plan; if it does not, adjudication fails closed even if read queries happened. Generated packs are session-local and must be bound by exact SHA-256 in the environment attestation, then replaced by the pre-retry probe after collection. The exact WH3 `io.open` read limitation is not generalized beyond this owner environment.

## v0.2I-r2 live feasibility transport risks

- **Event-vocabulary drift:** mitigated by extracting all static feasibility-probe emit names and requiring parser allowlisting in regression tests. Dynamic event construction remains prohibited by convention for this probe.
- **Future parser/session drift:** `campaign_feasibility` is now explicitly accepted as a snapshot-bearing probe kind.
- **Request/query uncertainty:** still open until the next owner-runtime attempt observes `FEASIBILITY_REQUEST_SEEN`, explicit rejection, or query results.
- **Authority creep:** unchanged; no runtime mutation/order surface is introduced.

# Known Risks

## v0.2I-r1 live feasibility transport risks

- **Idle-model timer starvation — corrected offline, owner confirmation pending.** v0.2I used a campaign-model timer for an asynchronous request while instructing the owner to leave the map idle. r1 switches to a UI real timer and immediate poll.
- **Relative request-file readability — still unverified.** The append log proves relative game-root writes work, but the first limiting run had no request-seen marker. r1 adds `FEASIBILITY_REQUEST_SEEN` so a second failure can distinguish file transport from query execution.
- **Exact query semantics — still unverified.** No live query result was observed in the limiting run; no route, legality, order, acknowledgement, execution or outcome claim is promoted.

## v0.2I live campaign-feasibility preparation risks

- **No current assignment:** the loaded campaign may legitimately yield no v0.2G force assignment. The probe then performs no feasibility query; this is a limiting observation, not a reason to invent a target.
- **Snapshot/request staleness:** campaign state can progress between first-tick capture and request execution. The request is turn-bound and stale-turn packets are rejected, but finer within-turn state drift remains observable only indirectly.
- **Read-query semantic overreach:** a true reachability result may be mistaken for route safety or action legality. The adjudicator explicitly prohibits that promotion.
- **Transport race:** the local sidecar and Lua runtime communicate through append log plus an atomic relative request file. Missing/partial packet termination fails closed and remains local for diagnosis.
- **Environment drift:** SFO, WH3 executable, launcher state, or probe hash changes invalidate the prepared cohort.
- **First-tick compatibility:** documentation recommends first-tick model access, but exact owner-runtime behavior of this new pack remains unverified until the live session.
- **File-I/O availability:** the request-file transport is project infrastructure, not a campaign-model capability; inability to read the request must fail as unavailable rather than trigger fallback mutation behavior.

## v0.2H campaign feasibility/action-authority risks

- **Documentation→runtime promotion:** a documented method may differ or fail in the owner's exact build/profile. Mitigation: all catalog entries remain `UNOBSERVED_OWNER_BUILD` until a bound live packet exists.
- **Centroid target laundering:** a faction centroid could be mistaken for a legal enemy target. Mitigation: point-only semantics and explicit no-attack-target flag.
- **Region→settlement overreach:** resolving a region's settlement could be mistaken for permission to attack/occupy it. Mitigation: reachability-only query scope; `concrete_attack_target_promoted = false`.
- **Boolean→route overclaim:** a reachability result contains no route geometry, ZOC/interception, safety, ETA quality, or execution guarantee. Mitigation: each query carries explicit scope and nonclaims.
- **Ambiguous `can_assault` misuse:** garrison context may not identify a specific source actor/action. Mitigation: catalogued but excluded from feasibility plans.
- **Stale CQI/query packet:** historical or destroyed interfaces could produce misleading results. Mitigation: exact turn/scenario/plan/query binding and fail-closed stale/foreign rejection.
- **Authority creep by helper API:** campaign-manager wrappers may enable movement or otherwise mutate state even when used for convenience. Mitigation: read-only probe must use query interfaces only; mutation-surface inventory is prohibited.
- **SFO semantic drift:** documented vanilla/core query shapes may behave differently under SFO or future WH3 builds. Mitigation: runtime evidence is profile/build-bound and unknown hashes revoke certification.

## v0.2G campaign force-allocation risks

- **Geometry/path conflation:** straight-line distance and movement can rank actors while being wrong about actual WH3 routes, stances, zones of control, interception, or access. Mitigation: route status is explicitly reference-only and the next gate must fail closed on unsupported feasibility claims.
- **One-army observed calibration:** frozen Reikland turns 4–7 cannot validate multi-army allocation, reserve size, overflow behavior, or temporal persistence. Mitigation: label those mechanisms synthetic/control evidence until a distinct longitudinal campaign gate exists.
- **Greedy assignment local optimum:** severity-first greedy selection may miss better global allocations. Mitigation: no optimality claim; retain ranked candidates/conflicts and move to optimization only if a preserved adversarial counterexample requires it.
- **Recovery override misuse:** critical obligations can consume recovering capacity. Mitigation: override is critical-only, explicit, and unexecuted; future live calibration must measure whether the policy is too permissive.
- **Temporal constants may over-hold or churn:** 2-turn minimum, 4-turn review, and 0.15 score margin are synthetic engineering values. Mitigation: keep them disclosed and centrally testable; do not call them observed WH3 timing.
- **Retirement outcome leakage:** disappearance of a priority could be caused by observation loss or third-party/native-AI action rather than project success. Mitigation: retirement always carries `NO_CAUSAL_CREDIT`.
- **Portfolio-to-allocation identity drift:** stale/forged upstream evidence could redirect actors. Mitigation: exact v0.2E/v0.2F recomputation is mandatory before allocation.
## v0.2F strategic/theater portfolio risks

- **Priority-budget overfit:** six records may be too small or too large for real late-game WH3. Mitigation: preserve all critical sources through overflow and keep the bound explicitly uncalibrated.
- **Awareness/commitment confusion:** a rival priority visible during crisis could be mistaken for authorization to attack. Mitigation: separate `selected_priorities` from `selected_aggressive_priorities` and make crisis/recovery veto explicit.
- **Reserve fetishization:** always valuing reserve could become passive play. Mitigation: reserve is one bounded medium priority, not a hard army assignment; future assignment/outcome calibration must test it.
- **Faction-ID bias:** observer-safe faction IDs could accidentally become human/player heuristics later. Mitigation: player/NPC relabel invariance and explicit no-human-identity contract.
- **Snapshot thrashing:** v0.2F has no temporal commitment lifecycle; priorities can still oscillate across turns as observations change. Mitigation: next gate must add portfolio-to-army assignment plus commitment/review/cooldown semantics before any application authority.
- **False containment:** coherent visible-rival classification can be mistaken for durable power or coordination. Mitigation: retain v0.2E limits on economy, diplomacy, recruitment, intent, and longitudinal quality.

## v0.2E strategic benchmark risks

- **R-STRAT-001 — War count masquerades as challenge.** Mitigated by v0.2E: wars are descriptive; rival structure depends on visible asset concentration/presence and front state.
- **R-STRAT-002 — Hidden armies leak into strategic threat scoring.** Mitigated by observer-safe filtering plus hidden-army metamorphic injection.
- **R-STRAT-003 — Anti-player design is smuggled in through a human/player feature.** Mitigated by no human/player evaluator input and player→NPC label invariance.
- **R-STRAT-004 — Army co-location is mislabeled coordination.** Mitigated by explicit `NOT_INFERRED_FROM_COLOCATION`.
- **R-STRAT-005 — Early Reikland snapshots are overgeneralized to late-game quality.** Open and bounded: observed turns 4–7 calibrate input semantics only; late-game reference remains synthetic.
- **R-STRAT-006 — Engineering thresholds become presumed tactical/strategic truth.** Controlled: all four v0.2E thresholds are labeled project-owned benchmark definitions.
- **R-STRAT-007 — Visible local balance is mistaken for world power rank.** Controlled: global dominance, economy, recruitment, diplomacy, and native intent remain unavailable dimensions.
- **R-STRAT-008 — Benchmark work silently acquires campaign authority.** Mitigated by `NO_ORDERS` / `PROHIBITED`, static runtime-boundary tests, and no adapter imports.

| Risk | Severity | Mitigation |
|---|---:|---|
| WH3 does not expose enough authority to replace ordinary battle AI | Critical | capability probes; separate control from influence; use data tuning or scripted contexts honestly |
| SFO or WH3 update invalidates an optional profile | Critical | exact hashes, capability/schema checks, shadow-only fallback, isolated compatibility layer |
| DeepWar/Hecleas/SFO write overlapping table families | High | never combine raw packs as a design baseline; require row-level merged profile and regression suite |
| Late-game challenge becomes anti-player bias | High | fairness metrics, rival-power coherence metrics, explicit player-proximity disclosure |
| Difficulty bonuses are mislabeled as intelligence | High | separate stats, resources, mechanic bypasses, scripted intervention, and planner quality |
| SyntheticLab optimizes simulator artifacts | Critical | tier labels, calibration against R0, holdout scenarios, delete policies that fail reality checks |
| Hidden information leaks into decisions | Critical | observer-safe contract, visibility filtering, dedicated regression fixtures |
| Personal-project scope drifts into a whole-game rewrite | High | active gate, vertical slices, benchmark-linked features, deletion criteria |
| Copyrighted or personal artifacts enter Git | Critical | ignored local inputs, derived manifests only, static repository scan |
| Save corruption or campaign incompatibility | Critical | shadow mode first, backups, migrations, rollback, soak tests |
| Overfitting to Karl Franz | Medium | Karl Franz first, then cross-faction validation before general claims |
| PFH5 audit parser is mistaken for a general pack editor | High | audit-only, uncompressed PFH5 and zero-dependency guardrails, RPFM remains authoritative |
| Project PFH5 writer is mistaken for a general pack editor | High | limit it to uncompressed zero-dependency script-only packs; parse every output; RPFM remains authoritative |
| Probe output leaks hidden or personal information | Critical | use game-filtered visibility interfaces; bounded fields; parser rejects path/user fields |
| `ModLog` is absent, stale, duplicated, or polluted by other mods | High | unique prefix/schema, session ordering, exact hashes, manual pure-vanilla first run |
| Persistence test alters a valued campaign save | High | separate pack, explicit confirmation, disposable save only, inert namespaced key |
| Rollback removes a file changed after installation | High | installed-hash check; refuse removal unless explicitly forced; restore pre-existing backup |


| Early lifecycle snapshot is incomplete or unstable | High | treat first tick as diagnostics; canonical planning begins at local-faction turn start; preserve phase deltas |
| Cross-snapshot re-observation is mislabeled as duplicate corruption | Medium | scope duplicate detection to one snapshot and report cross-snapshot repeats separately |
| Transport metadata is mistaken for semantic evidence change | High | preserve raw/result digest separately; compare only the normalized semantic digest |
| Semantically equivalent but different pack revisions are mislabeled exact replication | High | require matching installed pack SHA-256 in two evidence manifests before `REPLICATED` |
| Deterministic byte-identical logs are rejected as non-independent | High | use distinct evidence collection IDs/manifests; treat byte identity as compatible with replication |
| A stale or different save produces a misleading persistence increment | High | require fresh `WRITE 0→1`, same-environment `RELOAD 1→2`, exact pack hash, and isolated persistence-only sessions |
| A probe pack is present in the data folder but mistaken for active | Medium | record loaded probe kinds from `PACK_LOADED`; distinguish installed presence from runtime loading |


| Persistence result digest changes when evidence files are renamed | Medium | preserve transport digest; compare the filename-invariant semantic digest for behavior |
| Foreign exact force/garrison internals leak information beyond the player UI | Critical | do not query foreign exact force strength or garrison composition in the initial shadow slice; use disclosed visible-unit-count and settlement-structure proxies |
| Movement and map-distance units are incomparable | High | label movement scaling uncalibrated; use only for shadow ranking; calibrate against observed travel outcomes before promotion |
| A read-only shadow proposal is mistaken for an accepted or successful order | Critical | output `SHADOW_NO_ORDERS`; no application packet; maintain decision/order/acknowledgement/outcome separation |
| Settlement structure fields exposed by a visible-region interface exceed legitimate player knowledge | High | collect only in a bounded probe; review live output and UI correspondence before certifying the field |

| Excessively granular live testing creates owner tedium and delays meaningful validation | High | batch read-only checks into multi-turn campaign sessions; separate only authority boundaries or defect isolation |
| A short multi-turn run is mistaken for campaign-quality calibration | High | treat churn and HOLD metrics as descriptive; require later cohort and outcome calibration before gameplay claims |
| State changes between turn snapshots are mislabeled direct battle observation | Medium | report only campaign-state deltas; direct battle capability requires a separate battle probe |
| Battle telemetry silently exposes hidden enemy units | Critical | require `is_visible_to_alliance` before foreign static/dynamic records; parser rejects hidden-identifying records |
| Battle instrumentation creates turn/frame-time or log-volume problems | High | 1 s aggregates, 3 s detailed samples, 240-unit cap, 30 MB log cap, processing telemetry |
| Optional battle query methods fail on one unit class or battle type | High | guarded calls, explicit capability records, no fabricated defaults promoted |
| Command events are mislabeled as accepted or successful orders | Critical | keep observation/attempt/acknowledgement/outcome contracts separate; label report `BATTLE_OBSERVATION_NO_ORDERS` |
| One easy battle is overfit as tactical quality evidence | High | first run proves feasibility only; later field/siege/SFO cohorts and owner ratings required |
| Battle script works in generated battles but not ordinary campaign battles, or vice versa | Critical | require an ordinary manually fought campaign battle now; test generated controller path separately later |
| Owned and player-visible region interfaces emit the same stable region as separate records | High | coalesce by region key before scenario validation; owned record wins; record overlap count; reject same-source duplicates and owner conflicts |
| A campaign-pipeline defect prevents battle evidence from being parsed or exported | High | preserve the raw log before downstream processing; correct the narrow adapter defect; reprocess the same evidence before requiring any replay |

| `lua_mod_log.txt` is overwritten as WH3 changes Lua runtimes, losing early campaign or battle evidence | Critical | append project records to `transcendence_runtime_log.txt`; clear/archive before session; require prepared-session manifest; forbid fallback for combined collection |
| Recovery scanner promotes embedded test fixtures or historical logs as owner gameplay | Critical | classify by source kind/name/hash/time; apply current-session cutoff; preserve fixture exclusions and limiting result |
| Embedded agents or hero forces are assigned army objectives | High | record `is_army`, `character_type_key`, and explicit eligibility; emit filtered-force telemetry; legacy heuristic only for old logs |
| Own exact force strength and foreign proxy strength use incompatible scales | Critical | common disclosed unit-count-scale feasibility proxy; exact own strength telemetry-only; ratio regression fixtures |
| Field army in a settlement is double-counted as settlement garrison | High | accept unit-count garrison proxy only from armed citizenry; otherwise structure proxy; preserve exclusion count |
| Append-only runtime log is stale or contains multiple owner sessions | High | pre-session archive/delete step, timestamped session manifest, creation-time/staged-pack checks, strict collector |


## R-BATTLE-012 — Replay timer callbacks may differ from live battle callbacks

**Status:** Replay side mitigated; live equivalence open. The exact replay produced dense dual-clock coverage with bounded gaps, but ordinary live campaign-battle timing still requires separate evidence.

## R-BATTLE-013 — Selection callbacks may not replay selection state

**Status:** Observed limiting result. Replay playback emitted 397 command events and zero selection events despite corrected per-unit registration. The system fails closed and labels 302 bounded state-delta matches as `INFERRED_NOT_ACKNOWLEDGED`.

## R-BATTLE-014 — Telemetry volume may affect performance

**Status:** Mitigated for the replay. The dense pass produced an 11.8 MB log, 249 detail samples, 1,477 aggregates, and 120 heartbeats under the configured cap. Broader armies, reinforcements, sieges, SFO, and ordinary live battles may produce different load.

## R-BATTLE-015 — Observed owner play may be mistaken for optimal policy

**Status:** Guarded. Tier 4R stores reality constraints and stress cases, not an imitation target. The owner command stream can reveal workload and tactical situations but cannot automatically become the AI policy.


## R-BATTLE-016 — The dense owner trace is overfit into a narrow tactical policy

**Status:** Open and guarded. Battle 4 is one vanilla land battle. The evaluator uses it for invariant and stress-case regression, not as a gold action label. Siege, ambush, reinforcement-heavy, monster/flying, artillery-heavy, and SFO cohorts remain necessary.

## R-BATTLE-017 — State-delta command attribution is mistaken for acknowledgement

**Status:** Guarded. Inferred records remain separately labeled, are never counted as accepted orders, and cannot establish causal effectiveness.

## R-BATTLE-018 — Straight-line recoverability is mistaken for a feasible withdrawal

**Status:** Open and guarded. v0.1M uses x/z distance, observed support, visible pressure, fatigue, health, and morale to produce a withdrawal-recoverability proxy. Every state and opportunity discloses that terrain, collision, formation geometry, and WH3 pathfinding are unavailable. No extraction alternative may be labeled executable until a separate authority/path probe exists.

## R-BATTLE-019 — A plausible prevention window is mistaken for causal proof

**Status:** Open and guarded. v0.1M separates `PLAUSIBLY_PREVENTABLE_SEVERITY` from insufficient evidence, but every diagnosis remains `UNVERIFIED`. Promotion requires accepted and executed intervention telemetry, path feasibility, and matched or calibrated counterfactual cohorts.

## R-BATTLE-020 — Utility weights overfit Battle 4 roles and unit scales

**Status:** Open. Role policies and weights are deterministic baselines, not calibrated truth. Future siege, ambush, reinforcement, monster/flying, artillery-heavy, other-faction, unit-scale, and SFO cohorts must perturb or replace weights that fail generalization tests.

## R-BATTLE-021 — Permissive coercion manufactures tactical facts

**Status:** Mitigated for the v0.1N slice contract; open for future adapters. Strict V2 validation rejects preserved malformed types, non-finite/out-of-range values, consistency errors, duplicate identity, invalid timing, and visibility mismatches before scoring. Every future adapter must map into the same fail-closed boundary.

## R-BATTLE-022 — Enemy collapse masks local collapse

**Status:** Mitigated offline. Local condition and combined tactical phase are separate in V2, including a simultaneous-collapse regression. Threshold quality and live-battle generalization remain open.

## R-BATTLE-023 — Instance identity inflates command churn

**Status:** Mitigated offline. Lifecycle accounting now uses stable opportunity keys; per-slice IDs remain audit instances only. Future planner objectives and multi-unit assignments need the same stable-identity discipline.

## R-BATTLE-024 — Adversarial fixtures overfit known contract failures

**Status:** Open. The 24-case suite protects known boundaries but is not an exhaustive fuzzer or proof against every malformed runtime adapter. Add heterogeneous schemas and property-based generation only when deterministic minimization and preserved fixtures can be maintained.
## R-TOOL-001 — Repository validation depends on checkout parent names

**Status:** Mitigated and regression-covered. Ignore rules now inspect repository-relative components. Future validation tools must not apply repository ignore semantics to absolute machine paths.

## R-BATTLE-025 — Advisory workload caps starve critical concern classes

**Status:** Mitigated offline. v0.1O groups equivalent unit concerns and preserves excess critical groups through explicit overflow. Later assignment may still fail to resolve all groups feasibly.

## R-BATTLE-026 — Synthetic baseline oracles are mistaken for gameplay quality

**Status:** Open and guarded. Matrix outputs are `CONTROL_SYNTHETIC`, comparisons are noncausal, and no policy is promoted to tactical superiority. Broader observed cohorts and eventually controlled execution evidence remain required.

## R-BATTLE-027 — Grouped portfolios hide incompatible unit-level actions

**Status:** Partially mitigated offline. v0.1P separates objectives, excludes protected or incompatible responders, and enforces one action slot per unit. Path, formation, timing, multi-unit coordination, and runtime legality remain open.



## R-BATTLE-028 — Straight-line actor ranking is mistaken for route feasibility

**Status:** Open and explicitly guarded. Distance affects offline ranking only. Terrain, collision, formation width, disengagement, line-of-sight, and WH3 pathfinding are not modeled.

## R-BATTLE-029 — Per-slice assignments are mistaken for a temporal command plan

**Status:** Open. The single-slot model prevents simultaneous double-booking inside one slice but has no duration, cooldown, cancellation, precondition, or replan semantics.

## R-BATTLE-030 — Assignment optimization overfits the current objective and role vocabulary

**Status:** Open. The tested matrix uses Empire-like roles and project-authored fixtures. Siege, flying, monster, summoned, reinforcement, artillery-heavy, other-faction, and SFO cohorts may require different eligibility and utility contracts.

## v0.1R action-authority risks

- **Origin ambiguity:** game command callbacks may reflect player or script. Mitigation: fixed unresolved-origin label.
- **False acknowledgement:** ordered position, target, movement, or withdrawal may match without direct acceptance semantics. Mitigation: state evidence is never acknowledgement.
- **Selection race:** selection state may change before callback or may be absent. Mitigation: explicit unbound windows and no inferred origin.
- **Reachability overclaim:** `can_reach_position` may not represent path safety, formation width, obstruction, or arrival. Mitigation: point-in-time query wording only.
- **Logging volume:** 250 ms samples for multiple selected units can grow rapidly. Mitigation: five-second windows, command-bound scope, local units only, raw logs local-only.
- **Runtime API absence:** optional queries or callbacks may fail under a live build/mod stack. Mitigation: capability records, strict required/optional classification, no fallback claims.
- **Pack/mod interaction:** enabling multiple probe packs could duplicate callbacks or contaminate evidence. Mitigation: owner instructions require only the action-authority pack; exact prepared hash and one-session verifier.
- **Privacy:** raw logs and machine paths could enter public artifacts. Mitigation: collector exports only summary, verification, and public manifest.


## v0.1S live-calibration risks

- **One-battle overgeneralization:** 89 windows from one custom land battle do not establish SFO, siege, reinforcement, monster, flying, or faction-wide behavior. Mitigation: capability claims are scoped to observed availability, not rates or tactical quality.
- **Selection-binding overclaim:** 100% binding can be mistaken for trusted player origin. Mitigation: every capability and artifact retains `SELECTION_BOUND_NOT_COMMAND_ORIGIN_ATTRIBUTED`.
- **Reachability prevalence overfit:** 97.0474% true results may reflect the chosen map and commands. Mitigation: no threshold or policy is calibrated from that prevalence.
- **State-match acknowledgement drift:** high target/movement counts can tempt later code to infer acceptance. Mitigation: strict rejected claims and zero acknowledgement invariant.
- **Schema-1 preparation opacity:** prepared-session details are not public. Mitigation: retain as limiting result; future schema-2 collector exports a sanitized hash-bound attestation.
- **Raw-evidence reproducibility:** public artifacts cannot be reparsed from the private raw log. Mitigation: preserve raw hash/size and owner-run verifier output; do not claim replication.

- **Evidence-byte normalization:** rewriting BOM-bearing PowerShell JSON would break source hashes. Mitigation: parse with `utf-8-sig`, preserve bytes, and regression-test the validator.

## v0.1T bounded-feasibility risks

- **Point-to-route overclaim:** a true point query may be mistaken for route completion. Mitigation: exact-point-only classification and prohibited stronger fields.
- **Aggregate leakage:** one live battle's reachability prevalence may be projected onto unrelated candidates. Mitigation: separate capability-profile contract and no candidate mapping.
- **Candidate geometry overfit:** three points and 120 m are project-owned bounds, not measured optima. Mitigation: disclose as uncalibrated and preserve configuration.
- **False regional veto:** one false point may be treated as objective infeasibility. Mitigation: reject only the exact point.
- **Private-log exposure:** richer no-replay exports could leak paths or raw lines. Mitigation: strict allowlisted schema, recursive privacy scan, exact source hashes, and public verifier.
- **Stale evidence binding:** query evidence could be attached to a different actor/time/candidate. Mitigation: actor, time, candidate, state, schedule, and result digests must reconcile.


## v0.1U semantic feasibility risks

- **Callback position sentinel leakage:** non-point callbacks may expose a vector object whose coordinates do not represent a destination. Mitigation: command-modality qualification and nonzero explicit-point requirement.
- **False-rate fabrication:** raw false counts can overstate infeasibility if semantic applicability is ignored. Mitigation: raw and qualified counts remain separate.
- **Immediate state-match overinterpretation:** ordered position and current target often match in the first sample, but this is not a trusted acknowledgement signal. Mitigation: status remains `OBSERVED_NOT_ACKNOWLEDGED`.
- **One-battle vocabulary limit:** the semantic allowlist covers only the five command names observed in this ordinary vanilla battle. Unknown command modalities fail closed.
- **No valid false-point calibration:** current qualified evidence contains no explicit-point `QUERY_FALSE`; planner handling remains synthetic until observed.

## v0.1V–v0.1X risks

- **Guarded readiness overinterpretation:** `QUERY_TRUE` can still be mistaken for command or route readiness. Mitigation: application authority remains `PROHIBITED` and stronger fields remain unverified.
- **Guarded identity substitution:** a downstream caller could attempt to rewrite packet identity or double-book one actor across packets. Mitigation: canonical packet/source digest binding, unique actor validation, and deterministic sampled attacks.
- **Endpoint-only false confidence:** separated endpoints can have crossing routes or incompatible formations. Mitigation: contract names endpoint separation only.
- **Development-bound miscalibration:** 12 m may be inappropriate for some unit widths or SFO entities. Mitigation: label as project-owned and require live/profile calibration later.
- **Fallback suboptimality:** more than 16 ready packets uses deterministic greedy fallback. Mitigation: expose solver mode and optimality status; never claim global optimum.
- **Fuzz-corpus overfitting:** 256 cases reuse current heterogeneous fixtures. Mitigation: preserve seed, source scenarios, and generalization limits; add new corpora rather than treating count as coverage proof.

## v0.1Y SFO combined-session risks

| Risk | Status | Mitigation |
|---|---|---|
| SFO updates between preparation and play | OPEN | hash full active pack at preflight and bind export to that identity |
| Additional active mods contaminate the first certification cohort | CONTROLLED | exact-two-pack profile fails closed |
| Combined log truncates or diverges during runtime transitions | OPEN_LIVE / CONTROL_OFFLINE_PREPARED | independent prefix checkpoints and fail-closed verifier |
| Current battle marker is missed by historical collector logic | CORRECTED | accept `battle_replay_shadow` and historical alias; regression test |
| Public upload leaks raw logs or personal paths | CONTROLLED_IN_V0.1Y | path-free wrapper ZIP; raw/checkpoints remain local |
| One SFO run is overgeneralized to later versions, full stack, factions, or battle types | OPEN | exact-scope warnings and version-bound evidence labels |
| SFO or launcher filename/layout differs from expected Workshop structure | OPEN_OWNER_PREFLIGHT | discover active filename from `used_mods.txt` and fail closed on ambiguity |


## R-TOOL-002 — SwitchParameter serialized across child PowerShell boundary

**Status:** Mitigated in v0.1Y-r1 and regression-covered. Passing `-Confirm:$false` to a script launched through a second `powershell.exe -File` process can arrive as the string `False` under Windows PowerShell 5.1 and fail parameter binding. SFO preparation now invokes the probe installer in process with splatted parameters. Future wrappers must not serialize expression-valued common parameters across an external PowerShell process boundary.

## v0.1Y-r2 launcher-state risks

| Risk | Status | Mitigation |
|---|---|---|
| WH3 launcher stores `used_mods.txt` outside the legacy Steam AppData path | CORRECTED_CONTROL_OFFLINE | deterministic game-root/Steam/EOS/GDK discovery |
| stale launcher copies disagree about enabled mods or load order | FAIL_CLOSED_CONTROL_OFFLINE | parse every supported existing copy and reject semantic disagreement |
| selected mod-list source leaks a personal machine path publicly | CONTROL_OFFLINE | public source-kind only; exact path retained in private manifest |
| current launcher creates no supported `used_mods.txt` copy at all | OPEN_OWNER_PREFLIGHT | report every searched location and stop before log clearing or watcher startup |



## R-SFO-003 — Prelaunch launcher state omits or decorates local probe entries

**Status:** Mitigated by v0.1Y-r3. Exact and safely decorated aliases are hash-bound. A genuinely absent prelaunch local entry is labeled `DEFERRED_RUNTIME_MARKER` and cannot become certified until the exact prepared pack is observed through campaign and battle runtime markers. The actual owner launcher materialization mode remains unverified until the next preparation/run.


## R-SFO-004 — Current used_mods is a launch script with working-directory directives

**Status:** Mitigated by v0.1Y-r4 and regression-covered. The parser accepts only the observed `add_working_directory` and `mod` grammar. Working directories must be absolute Windows paths with no `.` or `..` traversal components; duplicate directories and unsupported directives fail closed. Active-mod certification still derives only from validated `.pack` entries resolved to exact local bytes.

## R-UX-001 — Case-sensitive READY prompt causes safe but unnecessary cancellation

**Status:** Mitigated by v0.1Y-r4. The confirmation is trimmed and case-insensitive. This changes no pack identity, authority, or runtime-evidence contract.

## R-SFO-09 — Watcher launcher PID differs from runtime interpreter PID

**Status:** Mitigated by v0.1Y-r5 and regression-covered. Readiness is bound to a random per-session handshake token published atomically by the watcher. Launcher and runtime PIDs are retained only for private diagnostics. Early nonzero exit and captured stderr/stdout are reported instead of a generic initialization timeout.

## R-SFO-10 — Orphan watcher after launcher-PID false negative

**Status:** Mitigated by v0.1Y-r5. Before preparing a new run, the workflow requests shutdown only for SFO session directories that have a live watcher status but never produced `session_manifest_private.json`. Canonical prepared sessions are not auto-stopped.

## R-SFO-11 — Redundant watcher status can be zero-filled

**Status:** Mitigated by v0.1Z. Atomic writes use unique temporary files, flush/`fsync`, replacement, and exact byte verification. Collection trusts the token-bound checkpoint manifest and treats status as diagnostic.

## R-SFO-12 — Current battle schema can be excluded by historical marker filters

**Status:** Mitigated by v0.1Z. Transition and checkpoint summaries accept current schema 2 plus preserved schema 1 fixtures. Three schema-2 campaign-return cycles are regression-covered.

## R-EXPORT-003 — PowerShell evidence ZIP may be zero-filled

**Status:** Mitigated by v0.1Z. SFO public export uses a deterministic Python builder and verifies every member and final archive. Empty, all-zero, private-path, malformed JSON, size mismatch, and hash mismatch fail closed.

## R-CAL-001 — Overfitting to one Reikland/SFO land-battle cohort

**Status:** Open and explicitly bounded. The observed baseline calibrates only the exact frozen environment and three ordinary land battles. Replay deep dives improve interpretation but do not expand battle-type, faction, version, or mod-stack coverage.

## R-REPLAY-001 — Visual replay interpretation can be mistaken for causal ground truth

**Status:** Controlled by v0.1Z protocol. Visual annotations are aligned to exact telemetry and remain evidence notes. They cannot promote owner commands to optimal labels or observed command events to acknowledgement/execution.


## v0.1Z-r1 cross-platform durability boundary

- `os.fsync` semantics differ across operating systems. Public evidence ZIP creation now requires a writable descriptor for the durability barrier and is regression-tested by attempting a zero-length write before the real `fsync`.
- Directory-entry durability after `os.replace` is not claimed on Windows. The artifact is instead reopened and fully verified by member bytes, CRC, path set, size, and SHA-256 before success is reported.

## v0.2A replay-visible calibration risks

- **Identity-layer collapse:** display title, runtime battlefield identity, and replay hash can be mistakenly merged. Mitigation: separate required fields and exact regression tests.
- **Visual causality overclaim:** movement following an event may be called acknowledgement or execution. Mitigation: explicit forbidden promotions and `NO_ORDERS` authority.
- **Demonstration overfitting:** two owner-played Reikland land battles may become a presumed optimal policy. Mitigation: reference-only labels, no imitation target, and targeted future battle-type cohorts.
- **Camera-observability limit:** high tactical camera does not continuously expose unit-card state, exact frontage, or formation depth. Mitigation: broad facts only; telemetry remains quantitative source.
- **Timeline misalignment:** recording time includes menus/loading and Marienburg spans overlapping files. Mitigation: artifact-specific ranges and ordered nonoverlapping telemetry windows.
- **Outer-pack ambiguity:** launcher state named the shadow pack in both captures. Mitigation: preserve outer container as `UNVERIFIED`; bind tactical use to byte-identical battle-script SHA only.
- **Outcome reward misspecification:** rewarding victory alone would favor expensive Pyrrhic outcomes. Mitigation: independent preservation, crisis, role-loss, and terminal metrics.
## v0.2B Chaos defeat risks

- **Outcome overpromotion:** the result card is absent; preserve owner-attested defeat and withhold exact grade.
- **Bad-play imitation:** owner commands are reference observations, never policy labels.
- **Visual causal overreach:** geometry may suggest a failure mode but cannot prove why health, morale, or routing changed.
- **Replay/container ambiguity:** accept only exact dedicated or exact script-equivalent shadow containers; duplicates and unknown hashes fail closed.
- **Replay determinism:** the playback may diverge after WH3/SFO updates even when the replay hash is exact; preserve environment hashes and report failure honestly.
- **Chaos overfitting:** one Archaon/Warriors of Chaos land battle cannot define all Chaos, monster, magic, or terror doctrine.
## v0.2C replay-divergence risks

- **Replay terminal-equivalence risk:** old or divergent replay streams may end without reproducing the original result. Mitigation: require `BATTLE_COMPLETE` or separately bound live result evidence.
- **Process-exit promotion risk:** collector termination may be mistaken for battle completion. Mitigation: explicit false promotion field and regression tests.
- **Late-log-flush risk:** final bytes may arrive after WH3 exits. Mitigation: bounded consecutive-read stabilization.
- **Nonterminal lower-bound overreach:** casualties and routing may be mistaken for terminal totals. Mitigation: zero terminal coverage remains explicit.
- **Single-Chaos-case overfit:** role-loss thresholds may caricature Chaos doctrine. Mitigation: advisory-only findings and independent cohorts before generalization.

## R-POLICY-001 — Cross-battle runtime identity alias misread as canonical battle identity

**Status:** Mitigated by v0.2D. Ubersreik, Marienburg, and Chaos retain their separate display identities while the repeated Eilhart runtime field is preserved as source provenance. Silent reconciliation is prohibited and regression-tested.

## R-POLICY-002 — Single-battle hypothesis promoted into general doctrine

**Status:** Mitigated by v0.2D evidence classes. Target concentration remains `HYPOTHESIS_SINGLE_CORPUS`; reserve refinement remains bounded. Multi-corpus labels require explicit supporting battle IDs.

## R-POLICY-003 — Absolute model-loss threshold distorts unit-scale comparisons

**Status:** Mitigated by ratio-based severe-asset review and a model-count scaling metamorphic test. The numeric threshold remains a project-owned advisory contract, not a learned causal threshold.

## R-POLICY-004 — Terminal state suppresses urgent local preservation

**Status:** Mitigated by explicit simultaneous-state ordering: local preservation remains first while new high commitment is prohibited. Tactical benefit remains live-unverified.

## R-POLICY-005 — Offline doctrine accidentally acquires runtime authority

**Status:** Mitigated by `NO_ORDERS` / `PROHIBITED` contracts and Runtime Probe AST/import/call regression. No runtime adapter is present.

### R-NATIVE-010 — Scripted or patrol factions are mistaken for general strategic thrashing

A roaming force can reverse heading because its intended route turns back, even with stable wars/army state. Mitigation: report non-territorial windows separately and require territorial evidence before ordinary native-CAI tuning.

### R-NATIVE-011 — Post-hoc subgrouping is mislabeled confirmatory

The territorial/non-territorial split was selected during causal review of the completed vanilla cohort. Mitigation: preserve vanilla subgroup values as `POST_HOC_CAUSAL_REVIEW` / reference-only and treat the definition as prospective only for fresh SFO data.

### R-SFO-013 — Workshop update silently breaks behavior/profile comparability

SFO may update independently of Transcendence. Mitigation: v0.2O pins Workshop `2792731173` pack SHA-256 before and after the run and fails closed on drift; raw SFO bytes are never copied into project artifacts.

### R-NATIVE-012 — Pseudoreplication from overlapping trajectory windows
**Risk:** Treating overlapping army windows as independent samples would overstate certainty.
**Mitigation:** Report faction clusters, candidate concentration, leave-one-faction-out sensitivity; prohibit window-level p-values.

### R-NATIVE-013 — Direction-blind SFO copying
**Risk:** Any SFO difference could be misread as evidence to copy SFO priority rows even when SFO performs worse.
**Mitigation:** Frozen direction-aware decision table; worse/repeated results explicitly block copying; favorable results nominate replication only.

### R-NATIVE-014 — False allocator attribution
**Risk:** A future recovery difference could be credited to SFO allocator thresholds even though the captured SFO DB footprint contains no allocator-variable override.
**Mitigation:** Machine-enforced mechanistic registry marks direct SFO allocator attribution ineligible.


### R-NATIVE-015 — Campaign-composition confounding across profile benchmarks
**Risk:** One vanilla and one SFO campaign expose different territorial faction/force cohorts, so aggregate reversal-rate differences may reflect composition rather than profile behavior.
**Mitigation:** v0.2Q staged replication, campaign-level ordinal profile separation, and pooled shared-faction composition guard before mechanism nomination.

### R-NATIVE-016 — Post-result shared-faction analysis overpromoted to confirmation
**Risk:** The shared-faction direction reversal was discovered during causal review after the SFO result.
**Mitigation:** Preserve it as post-hoc causal review only; use it to design prospective replication, never to rewrite the frozen v0.2P endpoint.

### R-NATIVE-017 — Owner burden from unnecessary paired replication
**Risk:** Requiring another vanilla run before knowing whether SFO elevation replicates wastes owner time.
**Mitigation:** Stage A fresh SFO first; Stage B vanilla is conditional.
