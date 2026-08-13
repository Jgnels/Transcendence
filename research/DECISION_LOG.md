## 2026-08-01 — v0.2I-r3: replace runtime inbound file polling with a prelaunch embedded request

Decision: stop spending owner sessions on a request-file channel that repeatedly reached real polling but never `FEASIBILITY_REQUEST_SEEN`. Preserve the result as a limiting observation, keep the canonical game-side policy read-only, and move the exact already-derived query packet into a generated PFH5 before WH3 starts. Acceptance remains post-hoc and fail-closed: the new live snapshot must independently reproduce the frozen strategic-feasibility plan.

## 2026-08-01 — v0.2I-r2: make probe event vocabulary an explicit parser contract

**Decision:** retain the v0.2I-r1 game-side real/UI timer unchanged and repair the local shared parser instead. Add `FEASIBILITY_POLL_TICK` and `FEASIBILITY_REQUEST_SEEN` to the parser event vocabulary, recognize `campaign_feasibility` sessions/snapshots, add a static emitted-event→allowlist regression.

**Reason:** the second owner-runtime attempt observed `FEASIBILITY_POLL_TICK`, so the r1 timer fix worked. The sidecar then failed because its own parser rejected that newly added event before it could derive/write the request. Changing WH3 behavior again would be treating a local parser defect as a runtime uncertainty.

**Authority:** unchanged `NO_ORDERS`; application `PROHIBITED`.

# Decision Log

## 2026-08-01 — v0.2I-r1: replace idle campaign request polling with a real UI timer

**Decision:** preserve the first live v0.2I run as a limiting transport result and hotfix the request executor before asking for another session. Replace `cm:repeat_callback(trans_feas_poll, 1, ...)` with one immediate `trans_feas_poll()` plus `cm:repeat_real_callback(trans_feas_poll, 250, ...)`. Add one-shot poll/request-seen telemetry and remove the real callback after packet completion or explicit rejection.

**Why:** the exact owner run proved environment, probe load, first-tick snapshot, strategic assignment, plan and request generation, but returned no results/rejection. WH3 primary documentation states `repeat_callback` is synchronized to campaign model time whereas `repeat_real_callback` follows UI updates. Requiring the owner to advance the campaign merely to wake a transport poll would violate the read-only gate design.

**Authority:** unchanged — `NO_ORDERS`, application `PROHIBITED`.

## 2026-08-01 — D096: Capture current feasibility evidence on first tick without forcing owner actions

**Decision:** use a dedicated campaign-only read probe to emit one observer-safe snapshot on the first campaign tick, then derive the exact v0.2H request locally. Do not require an end turn, army move, battle, or save merely to create evidence.

**Reason:** the live gate is query availability/semantics, not owner behavior. Forcing gameplay would add state changes and unnecessary owner work before the query surface is proven.

**Boundary:** if the current snapshot yields no v0.2G assignment, emit no request; this is a limiting observation.

## 2026-08-01 — D097: Separate canonical query planning from whitelisted runtime execution

**Decision:** the sidecar alone runs v0.2E→v0.2H and writes at most 16 exact query IDs. The Lua runtime may execute only a fixed read-query whitelist; it has no generic call adapter or campaign mutation surface.

**Reason:** this prevents runtime convenience code from manufacturing targets, broadening authority, or bypassing canonical project contracts.

## 2026-08-01 — D098: Reconstruct live plans independently before accepting results

**Decision:** the collector must rebuild the selected plan from the raw observer snapshot and accept live results only when turn, assignment, plan digest, query IDs, cardinality, environment, and probe identity all match.

**Reason:** trusting the sidecar's saved plan alone would let stale, forged, or foreign request files become evidence.

**Authority:** `NO_ORDERS`; application `PROHIBITED`.

**Corrections during preparation:** dedicated probe provenance/listener names replaced copied shadow labels; false boolean query results are preserved rather than collapsed to null; and the Windows PowerShell 5.1 external `-Confirm:$false` binding pattern was removed in favor of in-process splatting.

## 2026-08-01 — v0.2G assign strategic obligations before probing campaign order authority

**Decision:** insert an explicit theater-to-army allocation and temporal commitment layer between the v0.2F strategic portfolio and any campaign feasibility/order-authority work.

**Rationale:** a strategic portfolio without actor/resource accounting cannot reveal double booking, reserve starvation, recovery misuse, or force shortage. Conversely, probing campaign orders before stable shadow allocation would conflate “can WH3 accept something” with “the project should attempt it.” v0.2G therefore assigns only abstract commitment slots, retains shortages, and prevents geometry-driven thrashing while leaving path/action feasibility unverified.

**Corrections during implementation:** critical recovery override was made actually reachable; supersession was prevented from stealing an actor when the incoming priority was already covered elsewhere; semantic frozen metrics were normalized to JSON-native arrays.

**Authority:** `NO_ORDERS`; application `PROHIBITED`.

**Next:** build a campaign strategic feasibility/action-authority envelope and request a live owner observation only if an exact capability question cannot be closed offline.
## 2026-08-01 — v0.2E strategic challenge benchmark before strategic authority

**Decision:** after closing the four-corpus tactical policy gate, move back to the campaign north star by freezing a strategic challenge/evaluation contract before adding a more capable strategic planner.

**Rationale:** a director optimized without an explicit fairness/challenge benchmark could learn the wrong objective—more wars, hidden information, player-specific targeting, or concentrated stat bonuses. The v0.2E evaluator therefore measures visible rival concentration and front exposure while making anti-player bias, diplomacy intent, recovery capacity, and campaign quality unavailable until longitudinal evidence exists. Existing audited DCT/FreeOrion/VCMI/Wesnoth mechanisms remain architecture references; no new dependency is needed for this narrow gate.

**Authority:** `NO_ORDERS`; application `PROHIBITED`.

**Next:** build a bounded strategic/theater portfolio offline and request new owner play only when a specific missing longitudinal field or authority boundary is frozen.

## 2026-07-28 — D001: Two-layer agent instructions

**Decision:** Keep durable rules in `AGENTS.md` and repository research files. Use `prompts/CONTINUE_PROJECT.md` as the reusable autonomous continuation request.

**Reason:** A large kickoff prompt is good at establishing architecture but becomes stale and inefficient once the repository contains canonical truth.

## 2026-07-28 — D002: Personal SFO-first product

**Decision:** Optimize first for the owner's private SFO single-player experience rather than a generic public Workshop mod.

**Reason:** This permits tighter benchmarks, sharper experience goals and controlled compatibility scope.

## 2026-07-28 — D003: Gate 0 before gameplay AI

**Decision:** Freeze the actual install/mod/settings/save baseline and capability truth before implementing AI behavior.

**Reason:** WH3 exposes uneven scripting authority, and SFO changes broad campaign and battle systems. Building against assumptions would create expensive architectural rework.

## 2026-07-28 — D004: Public code repository with private local inputs

**Decision:** Keep the GitHub code repository public because the connected ChatGPT/Codex integration cannot reliably access the owner's private repositories. Keep all Creative Assembly assets, Workshop packs, saves, replays, personal logs, secrets, and other private artifacts outside Git under ignored local storage.

**Reason:** Public repository visibility is required for the collaboration workflow, but publishing third-party or personal artifacts is unnecessary and unsafe. The repository stores only project-owned code, documentation, lawful fixtures, metadata, and hashes.

## 2026-07-29 — D005: Vanilla-compatible core with optional SFO profile

**Decision:** Build core contracts and reasoning against vanilla WH3. Add SFO through an isolated compatibility profile rather than making SFO a runtime dependency.

**Reason:** This contains update breakage, supports controlled comparisons, and still prioritizes the owner's preferred environment.

## 2026-07-29 — D006: SyntheticLab tiers are authority-labeled

**Decision:** Implement Tier 0–4 offline labs, but label Tier 2–4 as uncalibrated and require Reality Gate R0 before real-game performance claims or authority.

**Reason:** Fast synthetic testing is valuable only when simulator error cannot be mistaken for WH3 evidence.

## 2026-07-29 — D007: DeepWar and Hecleas are reference environments

**Decision:** Audit their pack surfaces and use them for ablation/reference profiles. Do not combine, depend on, or copy them without row-level conflict analysis and permission.

**Reason:** Their packs overlap in 10 table families and no reuse permission has been established.

## 2026-07-29 — D008: Third-party interventions require fairness classes

**Decision:** Distinguish planner changes from stat bonuses, resource grants, mechanic bypasses, scripted recovery, direct diplomacy mutations, and player-proximity challenge events.

**Reason:** A stronger opponent is not necessarily a more intelligent opponent, and the owner explicitly values fair, explainable challenge.

## 2026-07-29 — D009: Observer and persistence probes are separate packs

**Decision:** The first R0 campaign observer is strictly read-only. Save/reload testing uses a separate, explicitly enabled persistence pack containing only one project-owned saved value.

**Reason:** A combined pack would make a read-only capability probe silently alter saves and would blur observation evidence with persistence authority.

## 2026-07-29 — D010: Narrow deterministic PFH5 writer for script-only probes

**Decision:** Use a project-owned deterministic PFH5 writer only for zero-dependency, uncompressed, script-only probe packs. Continue to treat RPFM as authoritative for schema-aware DB work and complex packs.

**Reason:** This provides a reproducible one-command build without pretending the audit writer is a general pack editor.

## 2026-07-29 — D011: Game-provided visibility boundary precedes project filtering

**Decision:** R0 foreign observations must come from WH3's player-visibility-filtered faction interfaces. The observer may not enumerate the complete foreign world and filter it afterward.

**Reason:** Project-side filtering after privileged enumeration creates hidden-information leakage and cannot prove that the runtime adapter respects legitimate information boundaries.

## 2026-07-29 — D012: Local-faction turn start is the canonical planner snapshot

**Decision:** Preserve the first-tick snapshot as lifecycle diagnostics, but use `LOCAL_FACTION_TURN_START` as the canonical initial planner observation phase.

**Reason:** In the first live run, the later phase exposed three additional foreign characters and two additional foreign regions while own-army, own-region, and war counts stayed unchanged. First tick therefore occurs before visibility state is fully stable for this purpose.

## 2026-07-29 — D013: Re-observation is not duplication

**Decision:** Count exact repeated records as duplicate defects only within the same logical snapshot or non-snapshot scope. Track identical records seen in multiple snapshots separately as expected re-observations.

**Reason:** The v0.1C parser mislabeled eight stable entities as duplicate events because they appeared in both first-tick and local-turn-start snapshots.

## 2026-07-29 — D014: Separate semantic evidence from transport metadata

**Decision:** Preserve a transport-sensitive result digest for traceability and add a separate semantic digest that excludes source filenames and structured-record line positions.

**Reason:** The second observer upload changed filenames and the corrected loader shifted later line numbers even though every structured observation record was semantically identical. Treating that as a behavior change would make replication depend on file transport.

## 2026-07-29 — D015: Exact-pack identity is required for strict observer replication

**Decision:** Two semantically equivalent runs across different pack hashes are `SUPPORTED_CROSS_REVISION`, not `REPLICATED`. Strict Reality Gate replication requires two evidence manifests that record the same installed observer-pack SHA-256 and a clean loader entrypoint.

**Reason:** A narrow source change may be behaviorally inert, but silently weakening exact revision requirements would undermine reproducibility and future compatibility diagnosis.

## 2026-07-29 — D016: Collection independence is evidence identity, not byte inequality

**Decision:** Accept byte-identical deterministic logs as replicated output when distinct evidence collections are independently identified and every other exact-pack check passes.

**Reason:** The second exact corrected-pack run reproduced the first corrected-pack log byte-for-byte. Requiring different raw hashes would punish determinism and falsely reject a stronger reproducibility result. Independence is instead established by distinct collection timestamps, evidence-manifest hashes, and collection identifiers.

## 2026-07-29 — D017: Persistence proof requires an isolated fresh-write/reload chain

**Decision:** The persistence gate requires two isolated persistence-only sessions using the same pack hash: a fresh campaign reporting `WRITE` with `0 → 1`, followed by the same saved campaign reporting `RELOAD` with `1 → 2`.

**Reason:** Merely observing two increasing values is insufficient. The verifier must also require a fresh first phase, a non-new-game second phase, the same campaign and faction, clean loader entrypoints, distinct collection evidence, and exact pack identity.


## 2026-07-29 — D018: Live persistence is a scoped control capability

**Decision:** Promote only the ability to write and recover one namespaced project integer across save/reload to `CONTROL` with `REPLICATED` evidence.

**Reason:** The disposable campaign proved a clean `WRITE 0→1` and same-save `RELOAD 1→2` chain using one exact pack hash. It does not justify arbitrary save authority, migration safety, or valued-save compatibility.

## 2026-07-29 — D019: Persistence verification has transport and semantic digests

**Decision:** Preserve a filename-sensitive result digest for artifact traceability and add a filename-invariant semantic digest for cross-upload comparison.

**Reason:** Re-verifying the same evidence under uploaded filenames changed the result digest even though every evidence hash, state transition, pack identity, and check was unchanged.

## 2026-07-29 — D020: Freeze proven probes and add a separate shadow-input pack

**Decision:** Keep the replicated observer and persistence packs unchanged. Add `transcendence_shadow_probe.pack` as a third read-only pack for expanded Army Objective Assignment inputs.

**Reason:** Modifying a proven pack would invalidate exact-hash evidence and blur baseline observation, persistence authority, and experimental planning-input acquisition.

## 2026-07-29 — D021: Foreign military estimates start with disclosed proxies

**Decision:** The first shadow slice does not consume exact foreign `military_force:strength()` or foreign garrison composition. It uses visible unit count and visible settlement structure proxies.

**Reason:** A player-filtered entity list does not automatically prove that every method on the returned object matches legitimate player knowledge. Conservative proxies preserve the hidden-information invariant while capability and fairness are tested.

## 2026-07-29 — D022: Shadow proposals have no application packet

**Decision:** The first runtime-to-planner vertical slice ends at a deterministic objective proposal labeled `SHADOW_NO_ORDERS`.

**Reason:** Observation availability and decision quality must be measured before campaign order authority, acceptance, and outcome tracking are introduced.


## 2026-07-29 — D023: Batch live tests by authority boundary

**Decision:** Replace one-field-at-a-time shadow probing with one consolidated multi-turn read-only campaign run. Require at least five consecutive local-faction turn-start snapshots and generate one orderless objective proposal per turn.

**Reason:** Observer loading, logging, exact-pack identity, parser strictness, and save persistence are already established. Repeating a fresh campaign for every additional read-only field would burden the owner without improving isolation. Read-only campaign observation may be batched, while save mutation, campaign order authority, SFO compatibility, and battle authority remain separate because they cross materially different safety and evidence boundaries.

## 2026-07-29 — D024: Campaign shadow metrics are descriptive, not pass/fail gameplay quality

**Decision:** Record objective churn, HOLD rate, state changes, and continuity across the consolidated run, but do not reject a live run solely because those values are high or low.

**Reason:** Five early-game turns are sufficient to prove the pipeline and expose pathologies, but not to calibrate optimal behavior or campaign enjoyment.

## 2026-07-29 — D025: Battles are first-class in the consolidated read-only gate

**Decision:** Supersede the campaign-only v0.1H live workflow with one v0.1I session that requires at least five campaign turns and at least one manually fought ordinary campaign battle. The same read-only pack contains separate campaign and battle scripts and exports one combined evidence bundle.

**Reason:** Battles are a central part of the owner's desired experience. Treating them as incidental campaign state changes would collect too little evidence and would force another avoidable owner session. Campaign and battle observation share the same read-only authority boundary and can be tested safely together.

## 2026-07-29 — D026: Observe ordinary battles before choosing a tactical-control architecture

**Decision:** Use the battle manager, hierarchy queries, visibility-filtered unit records, phase callbacks, synchronized samples, and command-handler telemetry only. Do not create unitcontrollers or issue orders in this gate.

**Reason:** WH3 exposes separate query and control surfaces. The project must first prove what an ordinary battle exposes and how stable/expensive the telemetry is before selecting behavior trees, assignment systems, or generated-battle control paths.

## 2026-07-29 — D027: Use layered battle sampling and explicit incompleteness

**Decision:** Record one-second alliance aggregates and three-second detailed unit samples, plus phase-triggered detailed samples. Emit foreign unit state only while WH3 reports the unit visible to the local alliance. Cap detailed hierarchy traversal at 240 units and raw combined logs at 30 MB.

**Reason:** This captures tactical evolution without logging every frame. The visibility rule prevents hidden-information leakage, while explicit hidden counts preserve awareness that enemy telemetry is incomplete.

## 2026-07-29 — D028: Command events are observations, not acknowledgements

**Decision:** Record command-handler traffic for timing and command-mix analysis, but never label it as accepted, executed, or successful.

**Reason:** An event containing a command name or target does not prove that the engine accepted the action, that the intended unit performed it, or that it caused a favorable outcome.

## 2026-07-29 — D029: Resolve collector paths after PowerShell initialization

**Decision:** Collector scripts accept an empty `RepoRoot` parameter default and derive the repository from `$PSScriptRoot` only after the parameter block and strict-mode initialization.

**Reason:** Windows PowerShell can evaluate parameter defaults before `$PSScriptRoot` is available. Resolving the path inside the parameter declaration caused the completed live session to fail only at evidence collection. The hotfix preserves the existing WH3 log, requires no campaign replay, and adds a regression test covering both campaign collectors.

## 2026-07-29 — D030: Coalesce owned and visible region views by stable identity

**Decision:** Treat `SHADOW_OWN_REGION` and `SHADOW_VISIBLE_REGION` records with the same region key as two observations of one WH3 entity. Keep exactly one scenario region, give the richer owned record deterministic precedence, count the resolved overlap, and reject same-source duplicates or conflicting owners.

**Reason:** The first consolidated live log contained Altdorf in both the controlled-faction region list and WH3's player-visible region list. Appending both records created a forged duplicate scenario entity and caused the strict SyntheticLab contract to reject the entire run. The contract was correct; the adapter failed to reconcile two legitimate interface views.


## 2026-07-30 — D031: Treat lost early/battle telemetry as an instrumentation failure

**Decision:** Do not reconstruct the owner's turns 1–3 or manually fought battles from historical logs, packaged fixtures, or recovery re-exports. Preserve the absence as `LIMITING_RESULT`.

**Reason:** Timestamp-scoped recovery found only current-session turns 4–7 and zero live `TRANS_BATTLE` records. The apparent 72 battle records and two completions were embedded deterministic fixtures. Owner testimony establishes that the gameplay occurred, but not its telemetry.

## 2026-07-30 — D032: Use a project-owned append-only cross-runtime log

**Decision:** Campaign and battle scripts append all structured records to `transcendence_runtime_log.txt`. `lua_mod_log.txt` remains a secondary diagnostic sink and is not accepted as combined-session evidence.

**Reason:** The shared WH3 mod loader creates `lua_mod_log.txt` with write/truncate mode on the first `ModLog` call in each Lua runtime. Campaign → battle → campaign transitions can therefore erase prior runtime evidence.

## 2026-07-30 — D033: Prepare and bind every combined live session

**Decision:** Before WH3, archive/delete the prior append log, verify staged and installed pack hashes, and write a prepared-session manifest. Combined collection requires that manifest and a newly written append log and refuses legacy fallback.

**Reason:** Append-only files solve runtime truncation but create stale-session risk. Explicit preparation preserves old evidence and prevents records from separate owner sessions being merged accidentally.

## 2026-07-30 — D034: Distinguish field armies from character forces explicitly

**Decision:** Army Objective Assignment accepts only records where WH3 reports a military force is an army, its commander type is `general`, and it contains at least one unit. Other forces are logged as filtered telemetry.

**Reason:** The real turn 4–7 log included two one-unit Master Engineer character forces that the legacy adapter treated as armies. Unit count alone is insufficient because a legitimate field army may consist only of its general.

## 2026-07-30 — D035: Compare like-scaled force proxies and exclude field armies from garrisons

**Decision:** Cross-faction feasibility uses a common unit-count-scale proxy; exact own force strength is telemetry only. Settlement garrison unit evidence is accepted only from armed citizenry, otherwise a structure proxy is used.

**Reason:** The prior adapter compared exact own strengths in the millions against foreign `unit_count × 10`, producing ratios up to 14537.34, and double-counted Karl's field army as settlement garrison strength. Corrected reprocessing reduced the maximum observed ratio to 1.65 and removed field-army garrison inflation.


## 2026-07-30 — D036: Promote replay observation, not tactical quality

**Decision:** Classify Battle of Eilhart replay loading, phase/result callbacks, visible-unit queries, and command-event capture as `OBSERVED`; keep command acceptance, causal effectiveness, and tactical-AI quality unverified.

**Reason:** The exact replay and original pack produced a complete read-only session, but one replay is evidence of interface feasibility and a descriptive trace—not a proof that a planner can control or improve battles.

## 2026-07-30 — D037: Make Battle 4 a Tier 4R reality-regression corpus

**Decision:** Freeze a public-safe derived corpus containing stable unit identities, outcome lower bounds, command distributions, deployment changes, source digests, explicit invalidations, and owner context. Never commit the replay binary or raw log.

**Reason:** The trace is too valuable to remain a one-off report. It should continually test simulator assumptions, identity contracts, hidden-information rules, casualty semantics, and planner safety without pretending the owner trace is optimal policy.

## 2026-07-30 — D038: Dual-clock dense replay sampling with fail-closed metrics

**Decision:** Use both model-time and real-time callbacks, deduplicate by model time, emit sampler heartbeats, and withhold time-series conclusions unless coverage and maximum-gap thresholds pass.

**Reason:** The original callback registration yielded five phase samples across a 739.6-second battle. Sparse data must not silently generate precise engagement, routing, reserve, fatigue, flank, or path claims.

## 2026-07-30 — D039: Stable battle-unit identity is unique UI identity

**Decision:** Canonical battle-unit identity is alliance plus `unique_ui_id`. Army/unit hierarchy indexes are recorded as mutable observations and may not participate in canonical identity when a unique UI ID is available.

**Reason:** The original trace emitted 50 static identities for 34 canonical units as hierarchy indexes shifted. Index-based identity inflated unit counts and corrupted continuity.

## 2026-07-30 — D040: Command attribution has two evidence grades

**Decision:** Prefer direct per-unit selection callbacks. When selection evidence is absent, allow only explicitly labeled bounded inference from dense before/after ordered position, target, and ability ownership; never call either an acknowledgement or successful execution.

**Reason:** The original command stream had 397 events and zero selected-unit IDs. Dense state deltas can support useful hypotheses, but not observed acceptance or causality.


## 2026-07-30 — D041: Hierarchy discovery may precede static unit data

**Decision:** In schema 2, accept `UNIT_HIERARCHY` before the first matching `UNIT_STATIC`, but require every pending hierarchy identity to receive static data before the session ends. `UNIT_STATE` still requires prior static identity.

**Reason:** The runtime deliberately records hierarchy discovery before static emission so index transitions are never hidden. The first dense replay was valid but the parser rejected it as `UNIT_HIERARCHY before UNIT_STATIC`.

## 2026-07-30 — D042: Sampler initialization must fail visibly and numeric helpers must collapse multiple returns

**Decision:** Never pass a multi-return safe-query helper directly as the final argument to a numeric Lua function. Normalize aggregate values before arithmetic, register and disclose both clocks before the first aggregate sample, and wrap setup in a required-capability failure guard.

**Reason:** Lua expanded `trans_battle_safe` into value plus availability boolean inside `math.max`, aborting setup before callback registration. The battle still completed and phase samples survived, but no interval sample, aggregate record, heartbeat, or selection callback could occur.


## 2026-07-30 — D043: Close Battle 4 dense observation after the corrected replay pass

The exact corrected replay pass produced complete dense interval coverage, stable identities, bounded volume, and read-only authority. Battle 4 does not require another replay for observation or SyntheticLab calibration. Direct selection attribution remains a separate limiting result.

## 2026-07-30 — D044: Preserve both the dense corpus and compact reality slices

Keep the complete public-safe dense Tier 4R corpus for research and eight visibility-safe milestone slices for deterministic planner regression. Do not commit the raw 11.8 MB log or private replay.

## 2026-07-30 — D045: Use owner play as a reality constraint, not a gold tactical policy

The 397-command trace informs workload, situations, and state transitions but is not an imitation target. The first tactical evaluator is deterministic, advisory-only, hidden-information-safe, and capped at bounded priorities. It may be falsified offline before any order authority is explored.

## 2026-07-30 — D046: Canonicalize tactical state before tactical planning

**Decision:** Introduce `TACTICAL_STATE_VISIBILITY_SAFE_V1` and `TACTICAL_STATE_TRAJECTORY_V1` before behavior trees, search, learning, or live command authority. State contains only observed local and visible-enemy fields plus disclosed deterministic proxies and uncertainty.

**Reason:** The existing slice evaluator could emit useful priorities but lacked a stable planner-facing representation, temporal trends, role-specific preservation policies, support/pressure context, recoverability, and explicit temporary-versus-terminal collapse semantics. A canonical state contract allows future planners to be compared without coupling them to raw WH3 telemetry or hidden information.

## 2026-07-30 — D047: Treat decision windows as guarded counterfactuals

**Decision:** Represent tactical alternatives as bounded decision opportunities with `PROPOSED_NOT_EXECUTED`, `UNVERIFIED`, and `ADVISORY_ONLY` labels. Limit selection to six opportunities per slice and compare priority transitions with owner command traffic only as `REFERENCE_ONLY_NOT_CAUSAL`.

**Reason:** Battle 4 can expose when a preservation or pursuit decision appears valuable, but it cannot prove that an unexecuted alternative would have improved casualties or outcome. Explicit opportunity and budget contracts preserve useful diagnoses without silently converting observation into causal policy evidence.

## 2026-07-30 — D048: Tactical observations fail closed before utility scoring

**Decision:** Add `BATTLE_TRACE_TACTICAL_INPUT_V2` and reject malformed types, ranges, consistency, identity, timing, targets, and visibility scope before tactical-state construction.

**Reason:** Python coercion and downstream clamping could transform invalid evidence into plausible tactical facts. A planner boundary must reject ambiguity rather than normalize it silently.

## 2026-07-30 — D049: Separate local condition from combined tactical phase

**Decision:** `TACTICAL_STATE_VISIBILITY_SAFE_V2` records local stability, visible-enemy collapse, and combined tactical phase independently.

**Reason:** Enemy rout is not evidence that the local force recovered. The prior coupling could hide simultaneous local collapse and produce the wrong preservation posture.

## 2026-07-30 — D050: Measure opportunity lifecycle with stable keys

**Decision:** Keep per-slice `opportunity_id` for instance auditability and add stable `opportunity_key` for continuation, retirement, and command-budget metrics.

**Reason:** Slice-specific IDs made persistent warnings appear newly created at every sample, inflating churn and weakening the meaning of command efficiency.

## 2026-07-30 — D051: Close adversarial contract hardening before planner expansion

**Decision:** Preserve 18 invalid-input and 6 metamorphic cases as a deterministic v0.1N gate. Do not add behavior trees, search, learning, or order authority until this boundary remains stable across broader tactical cohorts.

**Reason:** Contract integrity is a prerequisite for more sophisticated planning; adding planner complexity over permissive or semantically coupled inputs would amplify defects.
## 2026-07-30 — D052: Ignore generated paths relative to the repository, not the machine path

**Decision:** Repository validation evaluates ignored directory names only within the repository-relative path.

**Reason:** Filtering absolute path components allowed a checkout beneath an ancestor named `tmp`, `build`, or `dist` to hide every canonical file and weaken validation. The validator must behave identically regardless of the checkout's parent directory.

## 2026-07-30 — D053: Batch equivalent critical concerns before applying the advisory cap

**Decision:** Add `TACTICAL_PRIORITY_PORTFOLIO_V1` above the frozen v0.1N candidate generator. Group unit opportunities by type, preserve every source identity and subject, and use an explicit overflow record when critical groups exceed capacity.

**Reason:** Applying the six-item cap to per-unit instances silently suppressed whole critical concern classes under saturation. Workload control must not erase critical awareness.

## 2026-07-30 — D054: Use synthetic baseline matrices as contract tests, not tactical-quality proof

**Decision:** Compare role-aware, legacy, uniform-danger, preservation-only, pressure-only, and passive policies across 16 strict synthetic fixtures. Report alignment and disagreement without translating those results into battle-outcome claims.

**Reason:** Deterministic weak baselines expose overfitting and missing policy dimensions before owner-machine testing, but a project-authored oracle cannot prove superior gameplay.


## 2026-07-30 — D055: Separate tactical objectives from actors and execution

**Decision:** Convert selected advisory sources into explicit objectives, then assign eligible actors through a separate `NO_ORDERS` layer. Assignment records remain `PROPOSED_NOT_EXECUTED` and cannot be interpreted as a command sequence.

**Reason:** A bounded priority portfolio preserves awareness but cannot reveal whether concerns compete for the same unit, lack a responder, or concern a subject that is no longer controllable.

## 2026-07-30 — D056: Preserve three distinct unfilled states

**Decision:** Report `SUBJECT_NOT_CONTROLLABLE`, `NO_LEGAL_CANDIDATE`, and `RESOURCE_CONFLICT_WITH_HIGHER_VALUE_OBJECTIVE` separately.

**Reason:** Collapsing these cases into one generic failure hides whether the limitation comes from observed control state, eligibility constraints, or optimization conflict.

## 2026-07-30 — D057: Assignment accepts only canonical portfolio source membership

**Decision:** Validate state and portfolio digests/contracts/authority and require the selected source-opportunity set to equal a canonical portfolio rebuilt from the state. Representation order may vary; source membership may not.

**Reason:** A forged or stale adviser packet must not gain assignment authority merely by preserving the outer schema.

## 2026-07-30 — D058: Separate temporal advisory lifecycle from assignment and execution

**Decision:** Add `TACTICAL_TEMPORAL_SCHEDULE_V1` above canonical assignment and below any command adapter. Plans remain `ABSTRACT_SCHEDULED_NOT_ISSUED` and `NO_ORDERS`.

**Reason:** Per-slice exclusivity does not prevent cross-slice thrashing or explain continuation, cancellation, supersession, and review. Those semantics must be testable before execution authority exists.

## 2026-07-30 — D059: Observation gaps erase lifecycle certainty

**Decision:** Use a 30-second bounded continuity horizon. Larger gaps emit explicit reset events and clear prior commitment/cooldown state.

**Reason:** The eight Battle 4 milestone slices cannot support a claim that an abstract proposal remained active, completed, or failed between distant observations.

## 2026-07-30 — D060: Do not credit unexecuted proposals with observed resolution

**Decision:** When a canonical objective disappears, emit `PLAN_RESOLVED_BY_OBSERVATION_NOT_ATTRIBUTED` rather than success or completion.

**Reason:** Correlation across observations is not command issue, acknowledgement, execution, or causal outcome evidence.

## 2026-07-30 — Close v0.1R offline action-authority preparation before gameplay

**Decision:** add a separate read-only action-authority probe and evidence contract rather than extending the planner or issuing test orders.

**Reason:** primary WH3 interfaces expose command callbacks and unit-state queries, but command-event origin is unresolved and order issue belongs to a unitcontroller boundary. Treating callback or state matching as acknowledgement would violate the project evidence invariant.

**Implementation:** strict packet/matrix, Battle 4 boundary report, `TRANS_ACTION` parser/probe, deterministic pack, exact-pack verifier, and batched prepare/collect scripts.

**Authority:** `NO_ORDERS`. No game or remote state is modified by the repository release itself.

**Next:** one ordinary single-player observational capture after owner installation.


## 2026-07-30 — D064: Close the ordinary-battle read-only action-authority gate

**Decision:** accept the exact v0.1R public-safe capture as `OBSERVED_READ_ONLY_ACTION_AUTHORITY_CALIBRATED` and promote only the individual query/state capabilities directly supported by its counts.

**Reason:** one complete exact-pack session produced 89 selection-bound command windows, 1,287 samples, both reachability outcomes, and multiple state/interruption classes while preserving zero project issue and acknowledgement claims.

**Boundary:** selection binding is not origin attribution; state matching is not acknowledgement; movement is not causal execution; reachability is not route completion.

## 2026-07-30 — D065: Preserve the raw log privately and harden future public preparation evidence

**Decision:** do not request or commit the 732,081-byte raw log. Preserve its hash and owner-run verification result, and upgrade future collector exports to schema 2 with a sanitized preparation attestation.

**Reason:** the existing schema-1 packet proves the live gate sufficiently, but omitting the prepared manifest prevents independent replay of preparation checks from public files. A path-free attestation corrects that narrow auditability defect without weakening privacy.

**Next:** design a read-only feasibility envelope using only observed query availability. Do not request a repeat gameplay capture until a new authority boundary requires it.

## 2026-07-30 — D066: Preserve PowerShell JSON bytes while accepting UTF-8 BOM

**Decision:** repository JSON validation decodes tracked JSON with `utf-8-sig` rather than rewriting captured files.

**Reason:** the owner-generated public manifest is valid PowerShell UTF-8 JSON with a BOM. Rewriting it would destroy exact source identity; rejecting it would prevent canonical preservation of real evidence.

## 2026-07-30 — D064: Treat point reachability as exact-point evidence only

`can_reach_position` may support or veto the exact queried point at the observation instant. It may not certify a route, formation, safe arrival, command legality, acknowledgement, execution, or outcome.

## 2026-07-30 — D065: Keep aggregate live calibration separate from candidate evidence

The v0.1S aggregate true/false counts establish scoped query availability only. They cannot be projected onto Battle 4 or generated candidate points.

## 2026-07-30 — D066: Prefer no-replay re-export over another battle

Because the exact private v0.1S raw log remains preserved and hash-bound, derive detailed public-safe windows from it before requesting another owner battle. The re-export must remain read-only, path-free, and zero-issue/zero-acknowledgement.


## 2026-07-30 — D065: Qualify reachability by command semantics before using it as point evidence

**Decision:** Preserve raw probe query results, but qualify tactical point evidence only when the callback supplies an explicit finite nonzero `Move` destination. Unit-target, formation-orientation, double-click, and special-ability callbacks remain state evidence but do not contribute point reachability.

**Reason:** The detailed live export showed that all 38 raw false results came from a zero-vector sentinel on `Move Orientation Width`. Treating those values as unreachable destinations would create false negative calibration.

## 2026-07-30 — D066: Freeze valid false-point evidence as unobserved

**Decision:** The current semantic capability profile reports 191 qualified true samples and zero qualified false samples. It may not infer a false-point rate from raw non-point telemetry.

**Reason:** Evidence absence must remain explicit. A future candidate-query capture may observe a valid false point, but the current battle did not.

## 2026-07-30 — Guard readiness before simultaneous planning

Decision: candidate feasibility must pass through `TACTICAL_GUARDED_ACTION_PACKET_V1`; no future planner or provider may consume raw query telemetry as an executable instruction.

Reason: query availability and exact-point support do not establish route, legality, acknowledgement, or execution. Explicit readiness and abstention preserve the authority boundary.

## 2026-07-30 — Reserve endpoints, not routes

Decision: introduce a bounded endpoint-separation solver before route or formation modeling. Name and label the result as a shadow reservation, not a path or order.

Reason: simultaneous destination collisions are detectable offline, while route crossing and formation feasibility are not yet supported.

## 2026-07-30 — Optimization tie-breaks cannot depend on coordinate hashes

Decision: use stable packet identity and candidate rank for equal-score reservation tie-breaking.

Reason: candidate ids contain coordinates; using them made equal decisions sensitive to a uniform battlefield translation.

## 2026-07-30 — Batch v0.1U–v0.1X from owner-validated v0.1T

Decision: package the completed offline gates as one cumulative rollback-safe installer based on the exact installed v0.1T ledger rather than requiring four sequential owner installations.

Reason: reduce owner burden and prevent an unvalidated intermediate release from becoming an assumed base.


## 2026-07-30 — Seal cumulative v0.1X at 154 tests

Decision: close v0.1U through v0.1X as one cumulative offline release based on exact owner-validated v0.1T. Evidence: 73 SyntheticLab tests, 81 Runtime Probe tests, 154 total, 286 canonical hashes, deterministic artifact reproduction, and no required gameplay run.

## 2026-07-30 — Bind the first SFO live cohort to exact full artifacts

**Decision:** certify the first SFO run only when the WH3 executable, full SFO Workshop pack, deterministic probe pack, active load order, settings, and faction are hash-bound.

**Reason:** SFO materially changes campaign and battle behavior; a label such as “SFO enabled” is not a reproducible environment identity.

## 2026-07-30 — Prove append continuity with checkpoints rather than owner restarts

**Decision:** run one WH3 process and checkpoint `transcendence_runtime_log.txt` automatically. Require campaign return after each battle, but do not require save-and-quit.

**Reason:** repeated restarts add uncontrolled lifecycle transitions. Prefix checkpoints directly test the defect of interest and preserve recoverable evidence.

## 2026-07-30 — Correct the combined battle marker and private-export boundary

**Decision:** accept current `battle_replay_shadow` plus historical `battle_shadow`; keep raw logs/checkpoints private and emit a separate path-free SFO ZIP.

**Reason:** historical fixtures masked the current marker mismatch, while the generic collector's ZIP was unsuitable for public upload.


## 2026-07-30 — v0.1Y-r1 bind PowerShell common parameters in process

**Decision:** SFO preparation must invoke `prepare_live_probe.ps1` directly with splatted parameters instead of passing `-Confirm:$false` through a child `powershell.exe -File` process.

**Evidence:** The owner-machine v0.1Y preparation failed before mutation with `Cannot convert 'System.String' to System.Management.Automation.SwitchParameter required by parameter 'Confirm'`. The repository installation itself had already passed 162 tests and 298 hashes.

**Rationale:** Common-parameter expression syntax is evaluated correctly during direct script invocation, while an external process receives serialized command-line strings. The narrowest responsible correction is the wrapper boundary; the underlying probe installer remains unchanged.

**Authority:** Repository workflow hotfix only. No WH3 mutation, save change, mod activation, or live evidence claim.

## 2026-07-30 — D071: Discover WH3 used_mods across supported launcher locations

**Decision:** Resolve `used_mods.txt` from the WH3 game root first, then Steam, EOS, and GDK AppData script locations. Accept multiple copies only when their parsed pack order agrees exactly; otherwise fail closed.

**Reason:** The owner’s current launcher configuration produced no legacy Steam-AppData copy, while current WH3 tooling uses the game-root file. Hard-coding one historical location blocked a valid SFO preflight after the probe had installed successfully.

## 2026-07-30 — D072: Keep active-mod evidence path-free but source-qualified

**Decision:** Publish only a source-kind label and file digest for the selected mod-list file. Preserve the exact machine path solely in the private environment manifest.

**Reason:** Reproducibility requires knowing which launcher convention supplied the evidence, but public artifacts do not need usernames or installation paths.



## 2026-07-30 — D073: Defer prelaunch local-probe binding without weakening final certification

**Decision:** Accept an exact probe entry or a safely decorated launcher alias. If `used_mods.txt` contains only the exact SFO pack before WH3 starts, record `DEFERRED_RUNTIME_MARKER` rather than claiming the probe is active or aborting the session.

**Reason:** The owner configured SFO plus the probe, but the current launcher-state file did not expose the exact literal probe filename. Prelaunch materialization is not universal evidence. Runtime campaign and battle markers, combined with the exact prepared and installed pack hash, are stronger proof that the probe actually loaded.

**Boundary:** Deferred preflight is not two-pack certification. The final verifier passes only when the exact prepared hash matches and the read-only probe is observed in the combined campaign/battle log. Extra mods, duplicate aliases, wrong hashes, or missing markers fail closed.


## 2026-07-30 — D074: Parse the current WH3 launch-script subset, not a bare-mod approximation

**Decision:** Accept only `add_working_directory` with an absolute traversal-free Windows path and `mod` with a filename-only `.pack` value. Validate working directories but exclude them from active-mod identity and load-order counts. Reject every other directive.

**Evidence:** After an owner refresh launch, the game-root `used_mods.txt` began with `add_working_directory "C:/Program Files (x86)/Steam/steamapps/workshop/content/1142710/2792731173";`. The v0.1Y-r3 parser rejected that real line before reading the subsequent pack directives.

**Reason:** `used_mods.txt` is a launch script, not guaranteed to be a list containing only `mod` statements. Supporting the exact observed grammar removes a false blocker without weakening SFO-only certification.

## 2026-07-30 — D075: Treat READY as a human confirmation token, not a case-sensitive evidence field

**Decision:** Trim the response and compare `READY` case-insensitively.

**Reason:** Capitalization carries no evidentiary meaning, while the previous `-cne` comparison caused two safe cancellations after correct launcher configuration. Pack, environment, and runtime verification remain exact and case-normalized where identity matters.

## 2026-07-31 — D076: Bind watcher readiness to a session nonce, not a process-launcher PID

**Decision:** Generate a 256-bit session token, pass it to the checkpoint watcher, and require the same token in the atomic status document. Preserve launcher and runtime PIDs only as private diagnostics.

**Evidence:** Owner-machine SFO preflight succeeded with exact SFO, probe, WH3 executable, load order, and settings, but the watcher readiness check timed out after comparing the status writer PID to the `Start-Process` PID. Python launchers and shims may create a distinct interpreter process.

**Reason:** The evidentiary identity is the prepared session, not an implementation-dependent parent process ID. A nonce proves that the status belongs to this invocation without accepting stale status from another run.

**Boundary:** This changes startup orchestration only. Append continuity and SFO runtime compatibility remain live-unverified.

## 2026-07-31 — D077: Freeze the recovered SFO session instead of replaying the campaign

**Decision:** Treat the exact six-turn, three-battle recovery as the canonical first SFO observed baseline. Preserve only path-free aggregate facts, hashes, and bounded summaries in Git.

**Reason:** The raw log and all 130 checkpoint prefixes survived and independently establish the intended continuity gate. Repeating the campaign would add owner burden without improving the already closed evidence claim.

## 2026-07-31 — D078: Make checkpoint manifest authoritative and status diagnostic

**Decision:** Bind collection and readiness to the schema-2 checkpoint manifest plus session token. A malformed watcher status may produce a warning but cannot invalidate a healthy exact checkpoint chain.

**Reason:** The owner run had a zero-filled status file while the stopped checkpoint manifest, 130 prefixes, final log hash, and parsed lifecycle were intact.

## 2026-07-31 — D079: Use deterministic verified Python evidence archives

**Decision:** Replace SFO public transport `Compress-Archive` with a deterministic Python builder that validates member type, privacy, nonzero content, size, hash, archive integrity, and reproducibility.

**Reason:** The first PowerShell-created evidence ZIP was entirely zero-filled despite healthy source evidence.

## 2026-07-31 — D080: Deep-dive only the two exact preserved SFO replays

**Decision:** Capture Ubersreik and Marienburg one at a time under exact SFO plus the read-only replay probe. Use the captures to align visible tactics with telemetry; do not infer optimality, acknowledgement, execution causality, or broad compatibility.

**Reason:** Replays can answer formation, maneuver, collision, target-switching, routing, pursuit, and decision-window questions that aggregate runtime records cannot settle, while avoiding another campaign marathon.


## v0.1Z-r1 — Windows evidence-ZIP durability repair

The first owner-machine v0.1Z installation failed closed during repository validation because Windows rejects `os.fsync` on a read-only CRT file descriptor. The installer automatically restored the exact v0.1Y-r5 ledger. v0.1Z-r1 reopens the completed temporary ZIP with `r+b` solely for the durability barrier, adds an explicit writable-descriptor regression, and retains deterministic bytes, CRC verification, zero-filled-member rejection, and atomic replacement.

## 2026-07-31 — D081: Close the exact dual-replay visual-alignment cohort

**Decision:** accept the exact Ubersreik and Marienburg dense telemetry plus hash-bound full visual recordings as the finite v0.2A calibration source. No further playback of either replay is required.

**Reason:** both battles completed with dense schema-2 telemetry and full visual title/outcome coverage. Additional repeats would duplicate evidence without closing a new authority or battle-type gap.

## 2026-07-31 — D082: Preserve three identity layers instead of reconciling them silently

**Decision:** retain replay binary identity, runtime battlefield identity, and visually confirmed display title as separate fields.

**Reason:** both runtime corpora report `Battle of Eilhart`, while replay-selection and matchup screens visibly identify Ubersreik and Marienburg. Rewriting either source would destroy provenance.

## 2026-07-31 — D083: Separate tactical cost from victory grade

**Decision:** benchmark preservation, role losses, crisis exposure, and terminal behavior independently from win/loss or victory grade.

**Reason:** both battles were victories, but Marienburg lasted 2.100861 times as long and had a 2.341317-times greater observed local casualty lower bound.

## 2026-07-31 — D084: Treat visual evidence as bounded context, not command proof

**Decision:** use video only for title/outcome, broad geometry, phase context, and bounded qualitative facts. Movement after a command remains neither acknowledgement nor causal execution.

**Reason:** high tactical camera footage and replay event ambiguity cannot establish command acceptance, exact formation geometry, or causal effectiveness.
## 2026-07-31 — D084A: Use exact Chaos defeat as negative calibration, not imitation

**Decision:** Bind `An Ogre's Folly` by exact replay/video hashes, preserve visual diagnoses as bounded hypotheses, and require one read-only dense capture before deriving defeat-phase policies. Accept the exact frozen shadow pack only as a script-equivalent battle observer under both container and shared-script hashes.

**Reason:** The project lacks a defeat trajectory, but owner tactics are not optimal labels and the prior replay runs exposed an outer-container attestation defect.
## 2026-07-31 — D085: Close the Chaos replay gate as a limiting result

**Decision:** Accept the exact dense capture as a valid nonterminal replay-divergence fixture and stop requesting repeat playback. Preserve the owner-attested live defeat separately from the replayed simulation.

**Reason:** The exact environment and observer stream passed, but `BATTLE_COMPLETE` never appeared, terminal coverage was zero, and the replay-end zero-loss screen was not the original result. Repetition cannot convert the exhausted command stream into terminal evidence.

## 2026-07-31 — D086: Require natural completion for terminal-outcome promotion

**Decision:** Incomplete reports emit `UNVERIFIED_INCOMPLETE_SESSION`. WH3 process exit, stable log bytes, and replay-overlay exhaustion may close transport collection but never establish battle outcome.

**Reason:** The prior report generator unconditionally labeled terminal outcome `OBSERVED`, exposing a canonical-state authority defect.

## 2026-08-01 — D087: Close the first cross-corpus tactical policy gate offline

**Decision:** Reconcile Eilhart, Ubersreik, Marienburg, and the nonterminal Chaos trace through one deterministic `NO_ORDERS` policy envelope before collecting more ordinary-land-battle evidence.

**Reason:** The cohort already spans vanilla/SFO, decisive/pyrrhic outcomes, high/low tactical cost, incomplete force discovery, and a limiting nonterminal defeat replay. The highest-value next step is to force consistent policy boundaries rather than duplicate evidence.

## 2026-08-01 — D088: Preserve repeated Eilhart runtime identity as provenance, not as display truth

**Decision:** Freeze Ubersreik, Marienburg, and Chaos as a known runtime-identity alias cohort. Preserve their separate replay/display identities and prohibit silent reconciliation.

**Reason:** Canonical v0.2A/v0.2C evidence explicitly records the source-layer mismatch. Rewriting the runtime field would destroy provenance; treating it as actual display identity would mislabel the battles.

## 2026-08-01 — D089: Make severe high-value loss review ratio-based

**Decision:** Use an observed lower-bound loss ratio of 0.5 as the project-owned advisory review threshold and test model-count scale invariance.

**Reason:** Raw model counts are not comparable across characters, cavalry, artillery, infantry, and unit-scale changes. The threshold is an engineering safeguard, not a causal empirical law.

## 2026-08-01 — D090: Test executable authority surfaces, not forbidden words in documentation

**Decision:** Static safety tests inspect imports, function definitions/calls, and authority fields. They do not fail merely because documentation names `ISSUED`, acknowledgement, execution, or other states that the policy explicitly rejects.

**Reason:** The interrupted v0.2D attempt produced a false positive by confusing a rejected sentinel literal with an executable order adapter.


## 2026-08-01 — D091: Separate strategic priority arbitration from army assignment

**Decision:** Introduce a bounded strategic/theater portfolio above v0.2E challenge evaluation and below any army-to-objective assignment. Keep the portfolio `NO_ORDERS`, cap it at six top-level records, and preserve excess critical sources through an explicit overflow record.

**Reason:** Moving directly from snapshot diagnostics to per-army objectives would repeat the same architectural mistake corrected tactically in v0.1O/v0.1P: local decisions could starve globally important concern classes and a small planner/UI budget could silently drop crises.

**Boundary:** A portfolio record is not a force allocation, route, stance, order, acknowledgement, execution, or outcome.

## 2026-08-01 — D092: Let crisis and total-force recovery veto new aggressive commitment

**Decision:** Retain rival-awareness priorities for continuity, but expose no aggressive-priority channel while the v0.2E state is `LOCAL_CRISIS_OR_EXPOSED_FRONT` or every controlled field army is below the frozen recovery threshold. Aggregate fragmented hostile pressure rather than creating one commitment per war.

**Reason:** The target experience requires coherent pressure without brittle all-in behavior or anti-player dogpiles. A strategic director should first preserve fronts and recover usable force capacity instead of treating every visible war as a reason to attack.

**Boundary:** The veto and one-channel cap are engineering safeguards, not proven WH3-optimal values.

## 2026-08-01 — D093: Separate documented campaign queries from application authority

**Decision:** Introduce a v0.2H read-only campaign feasibility query layer between v0.2G army commitments and any future order adapter. Documentation may establish query vocabulary, but no query becomes owner-runtime `OBSERVED` without a bound live packet.

**Reason:** Moving directly from geometric assignment to a movement/attack helper would collapse reachability, legality, command issue, acknowledgement, execution, and outcome into one unsafe step.

**Boundary:** `NO_ORDERS`; application `PROHIBITED`.

## 2026-08-01 — D094: Do not launder faction centroids or region settlements into attack targets

**Decision:** FACTION targets remain point-reference centroids only. REGION targets may resolve to their exact settlement interface for reachability questions, but `concrete_attack_target_promoted` remains false.

**Reason:** v0.2G strategic targets are not necessarily executable targets. Silent conversion would allow a higher-level abstraction to manufacture an action identity that upstream evidence never selected.

## 2026-08-01 — D095: Exclude ambiguous garrison assault predicates from generic action legality

**Decision:** Catalog `GARRISON_RESIDENCE_SCRIPT_INTERFACE.can_assault` as documented but context-ambiguous and do not use it in v0.2H actor-target feasibility plans.

**Reason:** The documented predicate does not, by itself, bind the v0.2G source actor, target identity, route, or exact command semantics strongly enough for the project authority standard.

## 2026-08-02 — D096: Native WH3 CAI becomes the default strategic application owner

**Decision:** Supersede the default progression from v0.2E→F→G→H→I toward project-owned strategic control. Preserve v0.2E/F/G as evaluator/research infrastructure, thin/generalize v0.2H, and pause assignment-derived v0.2I. Native CAI remains planner/executor until a preregistered native+tuning falsification gate is passed.

**Reason:** Independent Grok, Kimi and Claude audits converged after correction that WH3 already owns materially richer task generation, batching, distance/stance-aware priority, force/task pairing, strength evaluation, recruitment and personality machinery than the project had reconciled before building the parallel controller chain. Code already written is not evidence for application ownership.

**Boundary:** This decision changes research/application disposition only. It does not delete code, authorize DB changes, script mutations, game orders, save writes, or remote GitHub changes.

## 2026-08-02 — D097: Row-level Native CAI reconciliation precedes further live feasibility transport

**Decision:** Make `GATE_0_NATIVE_CAI_RECONCILIATION` the active gate. Pin the exact WH3 8.1 RPFM schema, export vanilla CAI rows, compute SFO/DeepWar/Hecleas/Incata/narrow-mod row deltas, classify the Patch 8.1 priority mechanism, and map project responsibilities before another v0.2I attempt or strategic-controller expansion.

**Reason:** Offline schema/row reconciliation has materially higher architecture information gain, much lower owner burden, and lower risk of optimizing a layer later removed. Most capability discovery is answerable from schemas, packs and official sources without a live query bridge.

**Boundary:** No owner WH3 session is requested until the offline gate is substantially complete and a narrow ablation is preregistered.



## 2026-08-02 — D099: Current native allocator/task-priority rows strengthen native-primary application ownership

**Decision:** Keep v0.2F/v0.2G outside the default application path after owner-row reconciliation. Treat current native allocator/task-priority data as the first tuning surface and retain Transcendence recovery/reserve/commitment constructs as evaluator hypotheses until observable native failure is demonstrated.

**Reason:** The owner’s current vanilla DB payload contains explicit `ALLOCATOR_*` distance, recruiting, release/return and horizon variables plus timed/endgame task-generator priority groups. DeepWar, Hecleas and SFO demonstrably alter these native rows. Building a separate allocator before controlled native tuning would bypass an already-rich, engine-context-aware surface.

## 2026-08-02 — D100: Row evidence outranks pack-size/file-presence inference

**Decision:** Never infer behavior scope from a mod carrying a large CAI table file. Require row-level equality/delta evidence.

**Reason:** DeepWar’s 227-row `cai_personalities_tables` payload is byte-identical to current vanilla after its DB header despite the file’s ~175 KB size. The earlier “large file implies broad personality rewrite” inference is superseded.

## 2026-08-02 — D101: Owner CAI handoffs package extracted evidence, not raw Workshop packs

**Decision:** Acquisition manifests hash-bind raw packs in place; upload bundles exclude `.pack` bytes. Downstream processing detects whether RPFM returned TSV or binary DB payloads and decodes supported binary layouts fail-closed.

**Reason:** Raw SFO made the first handoff ~1.35 GB and exceeded platform upload limits, while the extracted CAI evidence was only ~220 KiB. RPFM server extraction also returned binary DB payloads despite an `as_tsv=true` request in this owner environment.


## 2026-08-02 — D102: Measure native strategic failure from trajectories before reviving project assignment

**Decision:** Add v0.2J as a read-only trajectory evaluator for threatened-front coverage/latency, observed recovering-army offensive use, home-zone buffer capacity, stationary-position and directional-retarget proxies. Do not use v0.2G's preferred assignment as the default native-quality oracle.

**Reason:** Official CA evidence and current owner rows already establish native task generation, task priority, distance/recruitment-aware evaluation and task/army allocation. The remaining architecture questions are behavioral outcomes, not lack of a project assignment representation.

**Boundary:** v0.2J is `NO_ORDERS` / `PROHIBITED`, has no runtime adapter, and cannot infer native internal task identity.

## 2026-08-02 — D103: Absence of trajectory pathology does not prove native memory, exclusivity, reserve intent, or hysteresis

**Decision:** Keep assignment exclusivity `UNAVAILABLE_FROM_TRAJECTORY_ONLY`, native assignment memory `UNAVAILABLE`, and native hysteresis `UNAVAILABLE` in v0.2J. Treat the healthy unengaged home-zone force count only as a reserve-capacity proxy.

**Reason:** Movement trajectories can reveal reproducible failure signatures but cannot uniquely identify engine-internal task bookkeeping or prove deliberate reserve policy. The detector must be useful for falsification without laundering non-observation into positive engine claims.

## D104 — Preserve player-visibility limits during native-CAI falsification

**Date:** 2026-08-02  
**Decision:** Do not enumerate complete foreign AI force inventories through arbitrary faction interfaces in the normal native-behavior observer. Use WH3 player-filtered foreign visibility and mark metrics that require complete faction state unavailable.

**Reason:** The project's normal application/evaluation evidence should not gain information a human player cannot observe merely to make native-CAI benchmarking easier. Script accessibility is not authority to violate the observer contract.

## D105 — Position stability is not a native-CAI failure label

**Date:** 2026-08-02  
**Decision:** Record stationary foreign-force positions as `POSITION_STABLE_NO_INTENT_INFERRED`, never as idle/stuck/bad AI without independent context.

**Reason:** The preserved owner turns 4–7 contain 36 position-stable intervals out of 37 comparable player-visible intervals, but the observer does not reveal native tasks, recruitment intent, defensive intent, hidden threats, or hidden forces. Treating stationarity as failure would manufacture a result from missing context.

## 2026-08-02 — D106: Preregister a repeated region-direction oscillation endpoint before new owner evidence

**Decision:** Freeze the first player-visible native-churn primary endpoint as two non-overlapping same-actor/same-region-pair A→B→A episodes. Each candidate requires continuous visibility, consecutive turns, unique region-direction proxies, >=120-degree heading reversals, and exact observed non-target context stability.

**Reason:** A simple direction change or even one A→B→A retarget is too easy to explain by legitimate context changes. The stricter repeated endpoint makes false-positive promotion harder and prevents post-hoc threshold selection after seeing owner data.

**Boundary:** This is a visible trajectory pathology signal only; native task identity, assignment memory and hysteresis remain engine-internal unknowns.

## 2026-08-02 — D107: Zero eligible churn exposure is not negative native evidence

**Decision:** Classify a cohort with no eligible stable-context region windows as `INSUFFICIENT_ELIGIBLE_EXPOSURE`. Do not use zero candidates or zero clusters from such a cohort to support native quality.

**Reason:** The historical turns 4–7 cohort and existing five-turn fixture both demonstrate that strict observation can legitimately yield no confirmatory windows. Missing denominator is not evidence of absence.

## 2026-08-02 — D108: v0.2L can earn a native-tuning ablation, never direct project-planner ownership

**Decision:** A positive repeated oscillation cluster may elevate a mechanistically plausible native-row treatment to preregistered ablation. It cannot directly promote v0.2G/v0.2I or any project-owned strategic application path.

**Reason:** Player-visible trajectories do not reveal native task bookkeeping, and hidden context remains possible. The native-first falsification ladder requires testing the smallest native correction before replacement.

## 2026-08-02 — D109: Acquire vanilla directional-churn exposure before requesting the SFO match

**Decision:** Run the sealed v0.2L owner protocol on vanilla first. Request the matched SFO run only if the vanilla capture contains at least one `eligible_stable_context_region_window`. If vanilla contains zero eligible windows, stop owner acquisition and redesign the observation cohort/protocol instead of spending another owner session on SFO.

**Reason:** The v0.2L endpoint is deliberately conservative and historical evidence had zero eligible windows. A matched SFO run has low information value if the instrument cannot observe the endpoint at all in the first profile. Sequential acquisition minimizes owner burden without changing the preregistered endpoint, thresholds, exclusions, or interpretation after seeing results.

**Boundary:** This is an acquisition-efficiency rule, not a treatment-success threshold. Any vanilla/SFO comparison remains descriptive only and cannot directly authorize project-owned strategic planning.


## 2026-08-02 — D110: Stop the v0.2L SFO acquisition after zero vanilla eligible exposure

**Decision:** Do not request the matched SFO directional-churn run. Treat the owner vanilla capture as an instrumentation limiting result.

**Reason:** The exact capture contained 187 possible four-frame actor windows, but 149 were visibility-censored and 38 were non-directional/stationary, leaving zero eligible primary windows. D109 explicitly preregistered redesign rather than another owner session in this case.

## 2026-08-02 — D111: Separate privileged development telemetry from application information authority

**Decision:** Preserve `PLAYER_VISIBLE_ONLY` for normal evaluator/application inputs while permitting a separately labeled `PRIVILEGED_OMNISCIENT_DIAGNOSTIC` plane for read-only offline development evidence. Privileged artifacts must be `application_eligible=false` and may not feed runtime decision/application code.

**Reason:** The player-visible instrument is too sparse to efficiently study native temporal behavior, while WH3's documented scripting surface can expose complete faction forces at faction turn events. Development observability does not require giving the shipped AI an information advantage if the planes are structurally separated.

## 2026-08-02 — D112: Qualify the diagnostic instrument before preregistering another behavior verdict

**Decision:** The first v0.2M owner diagnostic run is vanilla-only and evaluates telemetry density, not native AI quality. Qualification requires >=20 paired AI faction-turns, >=50 matched force start/end pairs, >=10 moved force-turn pairs, and >=5 consecutive non-zero trajectory pairs.

**Reason:** Freezing exposure thresholds before live diagnostic data avoids another post-hoc endpoint problem. Once the channel is proven sufficiently dense, the next behavioral hypothesis can be preregistered offline using the richer observation contract.

## 2026-08-03 — D113: Accept v0.2M-r1 diagnostic telemetry as qualified, not behavioral confirmation

**Decision:** Close the v0.2M instrumentation-density question as PASS using the successful owner vanilla capture: 1,588 paired AI faction-turns, 2,353 matched force-turn pairs, 967 moved pairs, 426 trajectory pairs, zero capability failures and zero incomplete normal AI faction turns.

**Reason:** Every preregistered exposure threshold was exceeded by a large margin and the r1 `rebels` skip survived six complete AI cycles. The instrument is dense enough for focused studies.

**Boundary:** Behavior scans of this same cohort remain exploratory because endpoints were refined after inspection and the old probe did not record battle participants.

## 2026-08-03 — D114: Require an explicit battle-telemetry declaration for every confirmatory temporal/recovery trace

**Decision:** v0.2N confirmatory evaluation refuses any parsed trace unless its loaded probe declares `battle_participant_telemetry=true`. The fresh owner collector also requires at least one complete battle sequence and rejects incomplete battle sequences/capability failures.

**Reason:** An empty battle list from an older probe is not evidence that no battle occurred. Structural provenance is required before a trajectory can be called battle-free or damaged-army movement can be interpreted against combat participation.

## 2026-08-03 — D115: Preregister fresh recovery and temporal endpoints before collecting another vanilla cohort

**Decision:** Freeze the v0.2N recovery and temporal endpoint definitions and threshold digest `4499a497bfc7dd6a33a6c0a50da4e1e52b1705d1f2f20f1a917cdfebeb5486ac` before fresh owner data. Require two non-overlapping same-force reversal windows for the repeated temporal signal; overlapping windows alone do not satisfy it.

**Reason:** The completed v0.2M-r1 trace exposed promising but ambiguous post-hoc patterns. A fresh cohort is necessary to separate discovery from confirmation and the non-overlap rule prevents one short oscillation from being double-counted.

**Authority:** `NO_ORDERS`; application `PROHIBITED`; privileged research only.

## 2026-08-03 — D116: Run fresh vanilla first and condition SFO on useful denominator

**Decision:** Acquire 10 complete AI cycles (11 Reikland turn-start markers) in a new vanilla Karl Franz campaign with normal play/autoresolve allowed. Request matched SFO only if vanilla is confirmatory-eligible and at least one preregistered endpoint has sufficient exposure.

**Reason:** v0.2M-r1 already proved dense telemetry, but recovery and battle-free stable-context denominators are narrower. Sequential acquisition minimizes owner burden without changing thresholds after results.

**Boundary:** A positive vanilla or SFO signal can earn causal review and a narrow native-row ablation only; it cannot directly revive project-owned strategic control.

## 2026-08-03 — D117: Preserve the v0.2N endpoint result before causal reinterpretation

**Decision:** Record the fresh vanilla v0.2N cohort exactly as preregistered: recovery had sufficient exposure but did not cross the frozen 20% signal threshold; temporal commitment did cross the frozen repeated-reversal endpoint.

**Reason:** Causal review must not rewrite a valid preregistered result merely because the triggering force later proves atypical. Measurement result and causal interpretation are separate evidence layers.

## 2026-08-03 — D118: Do not ablate ordinary native CAI from a special Rogue Pirate patrol trigger

**Decision:** The sole repeated v0.2N temporal trigger (`wh2_dlc11_cst_rogue_grey_point_scuttlers`, force 922) does not earn a native-row intervention for ordinary territorial CAI. Preserve the formal positive signal, but classify a special patrol-policy explanation as plausible and require ordinary-faction evidence before tuning.

**Reason:** Owner telemetry shows no owned regions, no wars, constant full-strength composition and sea-only movement. Community documentation independently characterizes Grey Point Scuttlers as a Rogue Pirate force that patrols a specific sea route. A route turn can create heading reversal without planner thrashing.

## 2026-08-03 — D119: Prospectively separate territorial and non-territorial temporal cohorts for SFO

**Decision:** In v0.2O, the primary strategic temporal population is windows whose stable owned-region set is non-empty. Empty-region-set roaming/patrol factions remain a separately reported secondary population. Retain every v0.2N movement, battle and stability threshold unchanged.

**Reason:** The population split prevents known patrol geometry from determining the strategic verdict while avoiding a brittle named-faction exclusion. Because the split was selected after vanilla inspection, vanilla subgroup values are reference-only; the definition is prospective for fresh SFO evidence.

## 2026-08-03 — D120: Bind the matched SFO study to the exact already-audited Workshop pack

**Decision:** Require Workshop `2792731173` / `sfo_grimhammer_3_main.pack` SHA-256 `ae20a0a08037aa3ebcbe7461d2589fc28dc15a5fe5d9ca4c0a9d0ff0a26da603`, plus the diagnostic probe and no other mod. Re-hash SFO after the run and exclude SFO pack bytes from all owner-kit/export artifacts.

**Reason:** Profile comparison is uninterpretable if SFO silently updates between row reconciliation and behavior acquisition. Hash binding preserves provenance without moving a 1.85 GB Workshop binary through the project.

### D121 — Freeze faction-cluster sensitivity before SFO data
**Decision:** Use the hash-frozen vanilla territorial cohort to define a descriptive leave-one-faction-out candidate-rate envelope of 0.222222–0.317073 before fresh SFO data. Do not treat it as a confidence interval or p-value.

### D122 — Make post-SFO interpretation direction-aware
**Decision:** A lower-than-envelope SFO rate with zero repeated territorial forces can nominate replication only; within-envelope yields no temporal nomination; higher-than-envelope or repeated territorial signal triggers causal review/replication and explicitly blocks copying SFO priority increases.

### D123 — Constrain SFO mechanism attribution to observed row footprint
**Decision:** The captured SFO CAI footprint has 88 changed task-priority rows, all increases, and no decoded allocator-variable override. Therefore direct attribution of any SFO recovery difference to allocator release/return rows is prohibited from this evidence.

### D124 — Pre-rank but do not authorize minimal SFO-inspired ablation candidates
**Decision:** Freeze a small generic/default task-priority candidate list before SFO behavior data. Every candidate remains dormant, replication-only, application-ineligible, and may not be installed or copied wholesale.


### D125 — Preserve frozen SFO worsening branch but block row attribution after composition review
**Decision:** Keep v0.2P `HIGHER_THAN_VANILLA_CLUSTER_ENVELOPE` as the formal fresh-SFO result. Do not promote it into row causality because shared-faction post-result direction reverses and profile composition overlap is low.
**Authority:** NO_ORDERS / PROHIBITED.

### D126 — Stage replication to minimize owner burden
**Decision:** Run one fresh SFO replicate first. Request another vanilla campaign only if SFO elevation independently replicates. No Stage-A outcome alone earns an ablation.

### D127 — Recovery is not a current intervention target
**Decision:** With both vanilla and SFO below the frozen 20% recovery signal threshold, keep collecting recovery telemetry opportunistically but do not request dedicated recovery runs or tune allocator rows.
