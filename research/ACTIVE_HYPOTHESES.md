## v0.2P active hypotheses

- **H-NATIVE-SFO-TEMPORAL-DIFF:** Fresh SFO territorial single-window reversal rate may fall outside the vanilla faction-cluster sensitivity envelope. Status: `UNTESTED_FRESH_SFO_REQUIRED`. Even if observed, it is a replication nomination, not causal row proof.
- **H-NATIVE-SFO-RECOVERY-DIFF:** Fresh SFO may cross the unchanged v0.2N damaged-army attacker-side threshold. Status: `UNTESTED_FRESH_SFO_REQUIRED`. Direct attribution to SFO allocator rows is ineligible because no decoded SFO allocator override is observed.
- **H-SFO-GENERIC-TASK-PRIORITIES:** Generic/default SFO task-priority increases may contribute to a directionally favorable territorial benchmark difference. Status: `DORMANT_HYPOTHESIS_REPLICATION_REQUIRED`; no application authorization.

## 2026-08-02 native-first hypotheses — AUTHORITATIVE

- **H-NATIVE-01:** current WH3 native CAI + bounded supported tuning can satisfy most strategic application requirements more safely and with richer internal state than the existing project allocator. Status: `SUPPORTED_BY_OWNER_ROW_EVIDENCE / ABLATION_PENDING`; allocator/task-priority tuning surfaces are now directly observed.
- **H-NATIVE-02:** v0.2E/F/G retain high value as independent evaluators even if removed from application control. Status: `SUPPORTED_BY_ARCHITECTURE_REVIEW`, player-value calibration pending.
- **H-NATIVE-03:** explicit native recovery protection, land-army reserve policy, assignment exclusivity, temporal commitment and reassignment hysteresis may or may not exist. Status: `UNKNOWN_ENGINE_INTERNAL/UNVERIFIED`; absence must not be assumed.
- **H-NATIVE-04:** Patch 8.1 turn-dependent prioritisation partially overlaps v0.2F phase/priority behavior. Status: `SUPPORTED_BEHAVIORAL_OVERLAP + CURRENT_DB_PARTICIPATION_STRONGLY_INFERRED`; current vanilla contains endgame/timed priority groups, while exact 8.1 causal provenance remains unverified.
- **H-NATIVE-05:** assignment-derived v0.2I is not worth further owner/runtime effort unless a later architecture decision restores a requirement for hypothetical project-assignment feasibility. Status: `SUPPORTED_BY_REVIEW_CONVERGENCE`.

- **H-NATIVE-06:** privileged v0.2M-r1 diagnostic telemetry is dense and stable enough for fresh preregistered native-behavior studies. Status: `SUPPORTED_BY_OWNER_RUNTIME`; 1,588 paired faction-turns, 2,353 matched army-turns, 967 moved pairs, 426 trajectory pairs, zero capability/incomplete-normal-faction failures.
- **H-NATIVE-07:** native CAI may re-enter materially damaged (<65% average unit health) field armies into attacker-side battles during their own faction turn at a rate high enough to merit narrow native tuning. Status: `PREREGISTERED_FRESH_VANILLA_COHORT_PENDING`; old v0.2M-r1 data cannot test it because battle participants were not recorded.
- **H-NATIVE-08:** native CAI may exhibit repeated battle-free stable-context realized heading reversals consistent with weak temporal commitment. Status: `V0.2N_FORMAL_SIGNAL_OBSERVED_BUT_SPECIAL_PATROL_CAUSAL_CONFOUNDER`; the sole repeated trigger is a non-territorial Rogue Pirate patrol, while ordinary territorial repeated behavior remains unresolved.

- **H-NATIVE-09:** SFO may materially change damaged-army attacker-side re-entry or repeated territorial reversal behavior relative to the hash-frozen vanilla reference. Status: `V0.2O_MATCHED_SFO_COHORT_PENDING`; profile difference is not row-level causality.

## v0.2I-r2 live campaign-feasibility hypotheses

- **SUPPORTED:** the real/UI polling timer executes while the owner leaves the campaign map idle; the second owner-runtime attempt observed `FEASIBILITY_POLL_TICK`.
- **SUPPORTED:** the second limiting result was caused by local parser-contract drift, not by WH3 failing to run the polling callback.
- **OPEN:** after parser repair, the next owner-runtime attempt should progress at least to `FEASIBILITY_REQUEST_SEEN` or an explicit request rejection.
- **OPEN:** individual WH3 read-query surfaces remain unverified until the exact query packet returns.
- No hypothesis grants order, route, legality, acknowledgement, execution, or causal authority.

# Active Hypotheses

## v0.2I-r1 live campaign-feasibility hypotheses

- **H-V02I-R1-01:** replacing model-time polling with an immediate poll plus 250 ms UI-synchronized real polling will allow the already-observed valid owner-runtime request to be consumed while the campaign map is idle. Status: `SUPPORTED`, owner-runtime confirmation pending.
- **H-V02I-R1-02:** the request file is readable from the same relative game-root working directory used successfully by the append log. Status: `UNVERIFIED`; r1 `FEASIBILITY_REQUEST_SEEN` telemetry distinguishes transport readability from query-surface failure.
- **H-V02I-R1-03:** at least the five query surfaces selected by the observed turn-6 plan can return typed results or recorded `observed=false` without campaign mutation. Status: `UNVERIFIED_OWNER_RUNTIME`.

## v0.2I live campaign-feasibility hypotheses

- **H-V02I-01:** the dedicated first-tick campaign probe will load under the owner's exact current WH3 + SFO two-mod environment and emit the expected observer-safe snapshot. Status: `UNVERIFIED_OWNER_RUNTIME`.
- **H-V02I-02:** at least one suitable current loaded campaign state will produce a v0.2G force assignment and therefore an exact v0.2H query request. Status: `UNVERIFIED`; a no-assignment state is a valid limiting observation.
- **H-V02I-03:** each requested model-hierarchy query will either return a typed result or fail in a way the probe can record without mutating campaign state. Status: `UNVERIFIED_OWNER_RUNTIME`.
- **H-V02I-04:** first-tick sampling plus delayed request polling will keep snapshot turn identity stable long enough to execute the bound query packet. Status: `HYPOTHESIS`; stale-turn rejection is implemented.
- **H-V02I-05:** true/false reachability results can improve later strategic pruning while remaining insufficient for route/ZOC/interception/action legality. Status: `HYPOTHESIS`; authority boundary frozen.

## v0.2H campaign feasibility hypotheses

- **H-V02H-01:** the documented model-hierarchy reachability queries are available with compatible semantics in the owner's exact WH3 build. Status: `UNVERIFIED`; requires a read-only live packet.
- **H-V02H-02:** same-turn reachability booleans will be useful enough to prune impossible strategic assignments without needing full route geometry. Status: `HYPOTHESIS`.
- **H-V02H-03:** stance-specific reachability should be queried only for an explicit stance candidate; current stance alone is not permission to change stance. Status: `SUPPORTED_BY_CONTRACT`, live semantics unverified.
- **H-V02H-04:** REGION→settlement resolution is a safe way to ask settlement reachability while preserving the strategic target identity. Status: `DOCUMENTED_QUERY`, owner-runtime unverified.
- **H-V02H-05:** faction-centroid point reachability is useful theater geometry but is not a legal attack-target surrogate. Status: `SUPPORTED_BY_CONTRACT`.
- **H-V02H-06:** `can_assault` is too context-ambiguous to serve as generic actor-target attack legality. Status: `HYPOTHESIS/SAFETY_ABSTENTION`; excluded until narrower evidence exists.

## v0.2G force-allocation hypotheses

- A severity-first greedy assignment with explicit actor exclusivity is sufficient at the current strategic abstraction; no global optimizer is justified until adversarial cases expose a concrete deficiency.
- Protecting armies below replenishment `0.65` from noncritical commitments improves strategic continuity, while critical obligations may require an explicit emergency override. This threshold is inherited project policy, not empirical WH3 optimum.
- Preserving one healthy unclaimed army as abstract reserve capacity when possible reduces overcommitment; its optimal size and conditions remain uncalibrated.
- A 2-turn minimum commitment, 4-turn reassignment review, and 0.15 score-improvement margin can reduce strategic thrashing without making the director inert. The observed turn-4–7 cohort cannot calibrate these constants.
- Straight-line geometry plus movement is useful for candidate ranking but is not sufficient for campaign route feasibility; the next gate must keep that distinction fail-closed.
- Critical-overflow expansion before assignment prevents a bounded strategic portfolio from hiding real resource conflicts.
## v0.2F strategic/theater portfolio hypotheses

- **A bounded strategic portfolio can preserve crisis, recovery, reserve, and rival-pressure concerns before assigning armies:** `SUPPORTED_OFFLINE` for the frozen 12-case matrix and v0.2E source cohort.
- **Every war should independently generate an offensive commitment:** `INVALIDATED_BY_CONTRACT`; fragmented pressure is aggregated and an empty war edge is semantically inert.
- **A local crisis should still permit a new rival-pressure commitment if the rival is coherent:** `INVALIDATED_BY_CONTRACT`; the rival priority remains visible but the aggressive channel is vetoed.
- **Critical strategic obligations can exceed a small UI/planner budget without information loss:** `SUPPORTED_OFFLINE` through explicit overflow with 100% critical-source coverage.
- **Six priorities and one aggressive channel are optimal for WH3:** `UNVERIFIED`; these remain project-owned engineering bounds.
- **The next layer can deterministically map portfolio priorities to legal field armies without thrashing or double-booking:** `HYPOTHESIS_NEXT`.

## v0.2E strategic challenge hypotheses

- **Late-game challenge collapse is primarily a coherence/pressure problem rather than a raw war-count problem:** remains `HYPOTHESIS`, but v0.2E now provides a deterministic discriminator that does not reward unrelated wars.
- **A visible concentrated rival candidate is sufficient evidence of durable strategic opposition:** `INVALIDATED` as a claim; the snapshot lacks economy, recruitment, diplomacy, intent, and longitudinal outcomes.
- **Same-faction armies near one front prove coordinated operations:** `INVALIDATED`; v0.2E records only co-location.
- **Player identity is needed to preserve late-game challenge:** `UNSUPPORTED`; v0.2E's semantic benchmark is explicitly invariant to player/NPC labels.
- **The observed turn-7 Marienburg state is a useful early calibration case for visible rival concentration:** `SUPPORTED_OFFLINE`, bounded to the exact v0.1J snapshot.
- **A deterministic theater/rival-power portfolio can be built before campaign order authority:** `HYPOTHESIS_NEXT`, now the preferred next offline gate.

## v0.2C Chaos replay adjudication

- **Replay reproduces the original terminal defeat:** `INVALIDATED` for this exact replay; no `BATTLE_COMPLETE`, zero terminal coverage, nonterminal final snapshot.
- **No protected reserve existed:** `REFINED`; telemetry supports delayed or uneven commitment because the second Halberdier unit first engaged at 212.1 seconds and lost only two models.
- **Elite cavalry preservation failed:** `SUPPORTED` as a lower-bound diagnosis; 58/60 models lost for one observed kill.
- **Artillery entered early crisis:** `SUPPORTED`; both Helstorms engaged at 49.4 seconds and first routed near 182–185 seconds.
- **Archaon target fixation contributed materially:** remains `HYPOTHESIS`; Archaon received 12/37 targeted commands, but selection attribution and causality are absent.
- **A different policy would have won:** `UNVERIFIED`; no executed counterfactual exists.

## v0.2B Chaos defeat hypotheses before dense telemetry (historical)

| ID | Hypothesis | Current evidence | Required discriminator |
|---|---|---|---|
| H-CHAOS-1 | The broad initial line created a mutual-support deficit under rapid Chaos pressure. | `SUPPORTED` visual | unit positions, engagement timing, local force ratios |
| H-CHAOS-2 | No protected reserve remained when the first local crisis formed. | `HYPOTHESIS` | command/engagement history and uncommitted-unit state |
| H-CHAOS-3 | Piecemeal commitment let Chaos maintain superior local combat power. | `SUPPORTED` visual | stable unit engagement and movement timeline |
| H-CHAOS-4 | Melee congestion degraded ranged/artillery firing opportunities. | `HYPOTHESIS` | ammunition, target, firing, position, and obstruction proxies |
| H-CHAOS-5 | A regroup/fallback/asset-extraction transition was not established after the first unfavorable exchange. | `SUPPORTED` visual | route, rally, movement, command, and terminal-state timing |

None is a causal or optimal-policy claim.


1. Late-game challenge collapse is driven more by fragmented factions, poor army concentration, weak target selection, diplomacy churn, failure to recover, and insufficient escalation around dominant powers than by tactical battle AI alone.
2. A Three-Kingdoms-inspired rival-power system can improve late game without creating a universal anti-player coalition.
3. DeepWar's narrow native-CAI focus and Hecleas's broader strategic/diplomatic scope provide useful ablation references, but neither should become a dependency.
4. SFO changes both native CAI inputs and the broader environment; apparent intelligence must be separated from mechanic bypasses, direct bonuses, scripted recovery, and player-proximity challenge events.
5. Shadow-mode Army Objective Assignment can be evaluated before any campaign-state intervention.
6. Multiple synthetic tiers should model different fidelity/cost levels rather than one lab claiming full WH3 fidelity.
7. Profile hashes and table overlap can detect update/conflict risk early enough to fail safely.
8. Synthetic improvements that do not survive seed ensembles or later WH3 calibration should be rejected.
9. WH3's player-visibility-filtered faction interfaces expose foreign character and region state without privileged complete-world enumeration. **Replicated for baseline fields; expanded shadow sufficiency remains unproven.**
10. Script-only PFH5 Mod packs are sufficient for replicated observation and one namespaced save/reload control path; expanded shadow fields can likely use the same boundary.
11. Controlled-army force strength, action points, unit soldier percentage, siege state, settlement level, and own garrison strength are sufficient to replace several SyntheticLab placeholders without privileged foreign data.
12. Visible-unit-count and settlement-structure proxies can support a useful first shadow ranking while preserving fairness, but their movement and threat scales will require calibration.

13. One five-turn read-only campaign session can establish expanded-field availability, lifecycle stability, orderless proposal determinism, churn behavior, proxy compliance, and basic performance without separate live runs for each field.

14. One combined read-only campaign-and-battle session can establish ordinary-battle script feasibility, phase/sample stability, visibility-safe unit telemetry, command-event observability, and basic performance without a separate live run for every tactical field.
15. Battle-manager phase callbacks plus synchronized one-second aggregate and three-second detailed sampling will be low enough overhead for one ordinary battle, but this remains unverified until owner-machine evidence.
16. Observed command traffic and unit-state changes can support future command-quality analysis, but no causal command-effectiveness claim is valid until attempted, accepted, and successful orders are separately instrumented.

## v0.1J updates

16. A single append-only project log can preserve campaign and ordinary-battle telemetry across WH3's separate Lua runtimes. **Supported by primary loader implementation and offline source/tests; live continuity remains unverified.**
17. `military_force:is_army()` plus `character_type_key=general` can distinguish field armies from embedded character forces without excluding a legitimate single-general army. **Supported by interface audit and source contract; live expanded records pending.**
18. Unit-count-scale feasibility proxies are more coherent than comparing exact controlled strength against visible foreign unit-count proxies. **Supported by real-input reprocessing; gameplay quality remains uncalibrated.**
19. Armed-citizenry identity is sufficient to prevent a stationed field army from being double-counted as a settlement garrison. **Supported offline; additional live settlement/siege cases pending.**


## H-BATTLE-006 — Dual-clock sampling survives replay playback

**Status:** OBSERVED for the exact Battle of Eilhart replay.

The corrected pack produced 249 detailed samples, 1,477 alliance aggregates, 739 model ticks, 1,206 real ticks, 120 heartbeats, and a 3.4-second maximum gap across 739.6 seconds. Equivalence to ordinary live campaign battles remains unverified.

## H-BATTLE-007 — Per-unit selection callbacks restore command context

**Status:** LIMITING_RESULT for replay playback.

Corrected per-unit callbacks emitted zero selection events while all 397 command events replayed. Dense state-delta matching inferred candidates for 302 commands, including 121 high-confidence records, but remains explicitly `INFERRED_NOT_ACKNOWLEDGED`. Live ordinary-battle selection behavior remains unverified.

## H-BATTLE-008 — Battle 4 reality regressions improve synthetic safety

**Status:** OBSERVED INPUT / REPLICATED OFFLINE DERIVATION.

The dense Tier 4R corpus and eight reality slices catch identity errors, sampling overclaim, hidden-information leakage, terminal-state assumptions, commander endangerment, frontline collapse, cavalry/artillery overextension, ranged preservation, rout cascades, and excessive control-load assumptions.

## H-BATTLE-009 — A bounded tactical shadow evaluator can reduce pyrrhic losses without imitating human click density

**Status:** HYPOTHESIS.

A deterministic state evaluator using preservation, crisis-stabilization, visible-target, and pursuit-termination priorities may produce a stronger and more maintainable tactical policy than copying the owner's 397-command trace. It currently has `NO_ORDERS` authority and must first pass the Battle 4 slices and later broader battle cohorts.

## H-BATTLE-010 — Decision opportunities can identify avoidable severity without overclaiming counterfactual outcomes

**Status:** HYPOTHESIS WITH REPLICATED OFFLINE DERIVATION.

v0.1M identifies early preservation or disengagement windows and separates `PLAUSIBLY_PREVENTABLE_SEVERITY` from insufficient evidence. Battle 4 produces four plausible cases and seven insufficient-evidence cases. This classification remains a hypothesis until accepted/executed interventions, terrain/pathfinding feasibility, and matched battle cohorts exist.

## H-BATTLE-011 — Tactical quality can be measured independently of victory

**Status:** HYPOTHESIS CONTRACT IMPLEMENTED.

The framework defines asset preservation, avoidable danger exposure, frontline/morale stability, reserve timing, ammunition/output preservation, pursuit discipline, high-severity coverage, and advisory churn as independent dimensions. Calibration and weighting remain unverified.

## H-BATTLE-012 — Strict tactical validation prevents silent evidence corruption

**Status:** CONTROL_OFFLINE CONTRACT REPLICATED; RUNTIME GENERALIZATION UNVERIFIED.

`BATTLE_TRACE_TACTICAL_INPUT_V2` rejects 18 preserved malformed-input mutations that v0.1M could coerce or normalize. This supports the contract, not a claim that every future WH3 adapter defect is covered.

## H-BATTLE-013 — Local condition and global phase must remain independent

**Status:** CONTROL_OFFLINE CONTRACT REPLICATED; TACTICAL QUALITY HYPOTHESIS.

Synthetic simultaneous-collapse testing demonstrates that enemy rout cannot safely overwrite local collapse. The resulting phase separation is deterministic, but its thresholds and gameplay quality remain uncalibrated.

## H-BATTLE-014 — Stable opportunity identity is required for command-budget measurement

**Status:** CONTROL_OFFLINE REPLICATED.

Using per-slice instance IDs inflated Battle 4 advisory transitions to 50. Stable lifecycle keys produce 28 transitions and 11 continuations. This corrects measurement semantics; it does not prove that 28 commands are sufficient or optimal.

## H-BATTLE-015 — Grouped tactical portfolios preserve critical awareness under bounded workload

**Status:** CONTROL_OFFLINE REPLICATED; EXECUTION QUALITY UNVERIFIED.

The legacy six-instance selector covered 66.6667% and 60% of critical source opportunities in preserved saturation fixtures. Type-grouped portfolios and explicit overflow preserve 100% source awareness while retaining at most six top-level records. This does not prove a feasible assignment or sequence.

## H-BATTLE-016 — Heterogeneous synthetic fixtures can reject simplistic planner baselines before live testing

**Status:** CONTROL_SYNTHETIC CONTRACT IMPLEMENTED; TACTICAL QUALITY UNVERIFIED.

The role-aware portfolio passes all 16 current fixture contracts while uniform-danger, preservation-only, pressure-only, passive, and legacy controls diverge. These fixtures are regression oracles, not observed gold actions or outcome evidence.


## H-BATTLE-017 — Explicit assignment can expose infeasibility without fabricating control

**Status:** CONTROL_OFFLINE REPLICATED; LIVE FEASIBILITY UNVERIFIED.

Battle 4 and synthetic fixtures distinguish assigned objectives, uncontrollable self-directed subjects, no-legal-responder conditions, and conflicts for one legal actor. This supports honest planner-development evidence but does not prove a WH3 route or command channel.

## H-BATTLE-018 — Assignment semantics should be independent of representation order

**Status:** CONTROL_SYNTHETIC REPLICATED.

Reversing unit order or selected portfolio order and uniformly translating coordinates preserves the tested assignment semantics. This protects against sequence artifacts; broader geometric, temporal, and floating-point invariants remain open.

## H-BATTLE-019 — Explicit temporal lifecycle reduces advisory thrashing without hiding emergencies

**Status:** Supported synthetically for the frozen matrix. Minimum commitment, review, cooldown, self-preservation supersession, and critical override pass deterministic contracts. Live tactical quality and timing calibration remain unverified.

## H-BATTLE-020 — Sparse milestone slices cannot establish command-plan continuity

**Status:** Supported as a limiting result. Battle 4's compact eight-slice corpus produces 18 continuity-reset events and zero plan continuations. A denser future action-authority capture is required before any live continuity claim.

## v0.1R action-authority hypotheses

- **H-R1:** ordinary live battle selection callbacks may bind a useful subset of player command events even though replay selection callbacks produced a limiting result. Status: `SUPPORTED_OBSERVED`; 89/89 windows were selection-bound, but origin remains unresolved.
- **H-R2:** `can_reach_position`, ordered position, current target, movement, and control-state queries remain available inside short post-command windows. Status: `SUPPORTED_OBSERVED`; all required capabilities were available and both true/false reachability values occurred.
- **H-R3:** five seconds at 250 ms real-time sampling is sufficient to characterize query availability and interruption classes without claiming command completion. Status: `SUPPORTED_FOR_OBSERVABILITY`; 1,287 samples and three close classes were captured, but adequacy for action completion or tactical timing remains unverified.
- **H-R4:** command-event origin cannot be resolved from the inspected callback contract. Status: `LIMITING_RESULT` until a primary interface proves otherwise.
- **H-R5:** no state-match combination should be promoted to direct acknowledgement or causal outcome without a separate source. Status: `INVARIANT`.


## v0.1S live-calibration hypotheses

- **H-S1:** selection-bound state windows can support a future read-only feasibility envelope without resolving command origin. Status: `SUPPORTED_OBSERVED`; 89/89 windows bound, with origin explicitly unresolved.
- **H-S2:** point reachability can safely serve as one bounded feasibility feature if route completion, formation width, safety, and arrival remain separate. Status: `SUPPORTED_OBSERVED_FOR_EXPLICIT_POINT_TRUE_ONLY`; false-point behavior and tactical utility remain hypotheses.
- **H-S3:** the observed 97.0474% true reachability rate is representative of broader battles. Status: `UNVERIFIED`; one custom land battle and command mix cannot establish generalization.
- **H-S4:** public preparation attestation improves independent packet auditability without exposing private paths. Status: `CONTROL_OFFLINE`; future schema-2 export is regression-tested, no repeat capture required.

## v0.1T feasibility hypotheses

- **H-T1:** role-aware bounded point generation can narrow later feasibility queries without creating order authority. **Status:** `CONTROL_OFFLINE`; 15/15 matrix scenarios pass.
- **H-T2:** a true point query is useful as a local veto/support feature while remaining insufficient for route or formation feasibility. **Status:** query availability `OBSERVED`; tactical utility still `HYPOTHESIS`.
- **H-T3:** aggregate reachability prevalence can calibrate candidate-specific feasibility. **Status:** `REJECTED`; aggregate live counts are kept separate from Battle 4 candidates.
- **H-T4:** the preserved v0.1S private log contains enough detailed windows for a no-replay public re-export. **Status:** workflow and fixture `CONTROL_OFFLINE`; owner-log run pending.
- **H-T5:** three candidates and 120 m are optimal live values. **Status:** `UNVERIFIED`; these are bounded project-owned development limits, not measured WH3 optima.


- **H-U1:** explicit-point query evidence can reduce obviously invalid candidate points without creating route or execution claims. Status: `SUPPORTED_FOR_TRUE_QUERY_AVAILABILITY`; valid false-point runtime evidence remains absent.
- **H-U2:** command-modality gating will prevent sentinel and opaque callback values from contaminating future feasibility calibration. Status: `CONTROL_OFFLINE`; future broader command vocabularies remain unverified.

## v0.1V guarded-packet hypotheses

- **H-V1:** exact-point support plus strict source authentication is a useful necessary gate before simultaneous planning. **Status:** `CONTROL_OFFLINE`; live tactical utility remains unverified.
- **H-V2:** explicit abstention is safer than carrying aggregate calibration into candidate readiness. **Status:** `SUPPORTED_BY_CONTRACT`; Battle 4 correctly produces 34 deferrals.

## v0.1W endpoint-reservation hypotheses

- **H-W1:** endpoint separation can remove a class of obvious simultaneous destination conflicts before any route model exists. **Status:** `CONTROL_SYNTHETIC`; live formation and route value remain unverified.
- **H-W2:** a 12 m endpoint separation is appropriate across unit types. **Status:** `UNVERIFIED`; development bound only.
- **H-W3:** exact optimization through 16 ready packets is sufficient for expected tactical workload. **Status:** `HYPOTHESIS`; fallback is explicit and tested through 160 packets.

## v0.1X pipeline-audit hypotheses

- **H-X1:** deterministic fuzzing will expose representation and source-authentication defects before live authority work. **Status:** `SUPPORTED`; two defects found and corrected.
- **H-X2:** structural solver work through 160 packets indicates acceptable live performance. **Status:** `REJECTED_AS_INFERENCE`; structural work is not live frame-time evidence.

## v0.1Y SFO combined-session hypotheses

- **H-Y1:** one append-only project log can preserve campaign → battle → campaign evidence in a single SFO process. **Status:** `CONTROL_OFFLINE_PREPARED`; owner live continuity pending.
- **H-Y2:** automatic full-file prefix checkpoints can detect or recover from transport truncation without requiring save-and-quit after each battle. **Status:** deterministic control replicated; live owner evidence pending.
- **H-Y3:** exact full-pack and load-order hashing is sufficient to define one reproducible SFO observation cohort. **Status:** contract implemented; later update/generalization policy remains selective revalidation.
- **H-Y4:** the current combined collector recognizes the current battle probe identifier. **Status:** `CONTROL_OFFLINE`; mismatch found and corrected.
- **H-Y5:** one SFO run can establish tactical superiority or broad compatibility. **Status:** `REJECTED`; it can establish only scoped observation, continuity, and performance evidence for the exact profile and events observed.

## v0.2A replay-calibration updates

20. Initial local-force visibility is not a reliable force-complete signal during reinforcement discovery. **SUPPORTED for the exact Ubersreik and Marienburg replays; generalization pending.**
21. Victory grade and tactical cost must be separate benchmark dimensions. **SUPPORTED by Decisive-versus-Pyrrhic contrast and observed casualty/duration ratios.**
22. Visible enemy rout cascade does not erase local crisis or recovery needs. **SUPPORTED for Marienburg; broader battle types pending.**
23. New high-commitment objectives after victory countdown are more likely to create waste than strategic value. **SUPPORTED as an advisory abstention rule; causal benefit remains unverified.**
24. Replay display title and runtime battlefield identity may refer to different identity layers. **OBSERVED for both exact replays; extractor semantics remain unresolved.**

## v0.2D cross-corpus policy updates

25. Force-discovery incompleteness should block whole-force assumptions. **SUPPORTED_MULTI_CORPUS** for Eilhart, Ubersreik, and Marienburg; other battle types pending.
26. Victory grade is insufficient as a tactical-quality score without preservation/cost dimensions. **SUPPORTED_MULTI_CORPUS** by Ubersreik versus Marienburg; causal policy benefit remains unverified.
27. Severe high-value-asset preservation review should scale with loss fraction rather than raw models. **SUPPORTED_MULTI_CORPUS as an advisory engineering rule**; the 0.5 threshold is not faction-general empirical truth.
28. Local preservation should remain first when local crisis and terminal evidence coexist. **CONTROL_SYNTHETIC + source-supported boundary**; live benefit unverified.
29. High target-command concentration indicates tactical fixation. **HYPOTHESIS_SINGLE_CORPUS** from Chaos; absent selection attribution it must remain review-only.


## v0.2Q active native-CAI hypotheses

### H-NATIVE-020 — SFO aggregate territorial reversal elevation is profile-level rather than campaign-composition noise
**Status:** REPLICATION_REQUIRED. First SFO rate 0.461538 exceeds vanilla envelope, but shared-faction post-result review reverses direction. Stage-A fresh SFO replication is required before another vanilla run.

### H-NATIVE-021 — SFO task-priority increases causally worsen territorial temporal coherence
**Status:** NOT_EARNED / CAUSAL_ATTRIBUTION_BLOCKED. Captured SFO CAI rows are 88/88 task-priority increases, but one-vs-one profile data cannot identify row causality. No ablation until staged replication and mechanism-selection review.

### H-NATIVE-022 — SFO materially changes damaged-army offensive reentry
**Status:** NOT_SUPPORTED_IN_CURRENT_COHORTS. Vanilla 0.157895 and SFO 0.142857 are both below the frozen 0.20 signal threshold. Continue telemetry opportunistically only.
