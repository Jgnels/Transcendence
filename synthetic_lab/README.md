# SyntheticLab v0.1Z

## v0.2H campaign strategic feasibility/action-authority envelope

SyntheticLab now converts v0.2G shadow assignments into bounded read-only query plans and adversarially checks target identity, stance abstention, stale/foreign packet rejection, and authority preservation. Documentation-derived query availability is not treated as owner-runtime observation. Mutation APIs remain outside the lab/runtime boundary.

```powershell
$env:PYTHONPATH = "synthetic_lab"
python -m transcendence_lab.cli strategic-feasibility `
  research\runtime_evidence\CAMPAIGN_TURNS_4_7_REPROCESS_v0.1J.json `
  research\runtime_evidence\REIKLAND_CAMPAIGN_STRATEGIC_FORCE_ALLOCATION_v0.2G.json
python -m transcendence_lab.cli strategic-feasibility-matrix `
  synthetic_lab\scenarios\campaign_strategic_feasibility_adversarial_matrix_v0.2H.json
```

Frozen envelope digest: `b6519eb75d141642a925f919f20fe1cf7300655b40300660dd1aabf8a873f553`. Frozen matrix digest: `08614e2a7e292b495ecb93a54375bc7782b7e7b7a02502d1c4e8a56d59f07cea`.

## v0.2C Chaos replay divergence calibration

The exact Chaos replay capture is a dense **nonterminal** limiting-result corpus. SyntheticLab validates its source hashes, lifecycle, unit findings, and authority; derives bounded crisis/loss findings; refines the reserve hypothesis; and forbids terminal-outcome or optimal-policy learning.

```powershell
.\synthetic_lab\tools\run.ps1 sfo-chaos-replay-adjudication `
  runtime_probe\fixtures\sfo_chaos_replay_stream_capture_v0.2C.json `
  synthetic_lab\corpora\sfo_chaos_replay_stream_observed_dense_v0.2C.json `
  runtime_probe\fixtures\sfo_chaos_replay_unit_findings_v0.2C.json
```

Frozen result digest: `a69f2ed4e09034dc79ac5462aefa7f9c949c09a33a3e4e843e4a8cdecddcaab4`.

## v0.2B Chaos defeat visual preparation (historical)

The v0.2B visual-only layer binds the exact Chaos defeat replay and recording without committing either. It deterministically preserves six broad deterioration phases, five bounded hypotheses, missing telemetry requirements, and a `NO_ORDERS` capture-readiness result. It deliberately withholds exact grade, casualties, health/morale/ammunition curves, command chronology, preventability, causality, and optimality until the exact replay is captured.

```powershell
.\synthetic_lab\tools\run.ps1 sfo-chaos-defeat-preparation `
  synthetic_lab\corpora\sfo_chaos_defeat_visual_preparation_v0.2B.json
```

Frozen readiness digest: `8ffd0b9d0b7f4b2599db7ea6b870af279dfd07eb1405dede4ad53a8b9fc28d8f`.

## v0.2A exact SFO dual-replay calibration

The v0.2A layer combines two public-safe dense telemetry corpora with a hash-only visual-alignment contract. It preserves title/runtime identity provenance, force discovery, outcome-cost contrast, local-crisis overlap, and terminal abstention without treating owner commands as optimal policy or issuing orders.

```powershell
.\synthetic_lab\tools\run.ps1 sfo-dual-replay-calibration `
  synthetic_lab\corpora\sfo_reikland_dual_replay_visual_alignment_v0.2A.json `
  synthetic_lab\corpora\sfo_ubersreik_observed_dense_v0.2A.json `
  synthetic_lab\corpora\sfo_marienburg_observed_dense_v0.2A.json
```

Frozen result digest: `364431a064ef1f15bc6ab7da4417b688d882ac7f2035be753728d9d75870565e`.

## v0.1Z three-battle SFO calibration

`corpora/sfo_reikland_three_battle_calibration_v0.1Z.json` adds three observed ordinary-land-battle summaries from one exact Reikland/SFO session. It supports cross-battle threshold robustness, decision-window frequency, command-budget stress, role-policy disagreement, and replay-to-telemetry alignment. It does not label owner commands as optimal, acknowledge commands, prove execution causality, or generalize to unobserved battle types and factions.


SyntheticLab is the offline hypothesis, scenario, regression, and observed-trace environment for Transcendence.

It is deliberately not a WH3 simulator claim. Tier 2–4 outputs remain uncalibrated hypotheses unless a specific result is tied to observed game evidence. Tier 4R preserves real observations without treating the owner's decisions as optimal policy.

## Tier 4R observed corpora

Battle of Eilhart now supplies two public-safe corpora:

- `battle4_eilhart_observed_dense_v2.json`: dense unit trajectories, alliance curves, command events, stable identities, explicit visibility, sampling quality, and conservative terminal lower bounds;
- `battle4_eilhart_trace_slices_v1.json`: eight visibility-safe snapshots at deployment, first contact, melee commitment, local crisis, enemy break, majority rout, victory countdown, and completion.

Neither corpus contains the replay, raw battle log, personal paths, or Creative Assembly assets. Enemy unit detail is included only after WH3 reports that unit visible to the local alliance.

## Tier 4R-SHADOW v0.1N

The tactical shadow evaluator now validates every slice with `BATTLE_TRACE_TACTICAL_INPUT_V2`, builds a canonical V2 eight-state trajectory, separates local condition from combined tactical phase, and tracks persistent warnings with stable opportunity keys. It includes role-specific preservation policies, support and visible-pressure geometry, danger and recoverability proxies, temporary-versus-terminal collapse states, pursuit termination, guarded loss-prevention diagnoses, and a bounded advisory budget.

Its authority is `NO_ORDERS` and its recommendations remain `HYPOTHESIS`. Every alternative is `PROPOSED_NOT_EXECUTED`, every counterfactual diagnosis is `UNVERIFIED`, and the owner command comparison is `REFERENCE_ONLY_NOT_CAUSAL`. The v0.1N adversarial suite rejects 18 malformed inputs and passes 6 metamorphic invariants under seed `20260730`.


## Tactical portfolio and assignment v0.1O–v0.1P

The v0.1O portfolio groups equivalent concerns before applying the six-record advisory bound and preserves excess critical sources through explicit overflow. v0.1P expands those canonical sources into self-directed and support objectives, filters illegal abstract responders, and resolves one `UNIT_ACTION_SLOT` per local unit. Uncontrollable subjects, absent legal responders, and conflicts for one actor remain explicit. No output is an executable WH3 command.

## Quick start

From the repository root on Windows:

```powershell
.\synthetic_lab\tools\run.ps1 test
.\synthetic_lab\tools\run.ps1 smoke
.\synthetic_lab\tools\run.ps1 tier4r synthetic_lab\corpora\battle4_eilhart_observed_dense_v2.json
.\synthetic_lab\tools\run.ps1 tier4r-trace `
  synthetic_lab\corpora\battle4_eilhart_observed_dense_v2.json `
  synthetic_lab\corpora\battle4_eilhart_trace_slices_v1.json
.\synthetic_lab\tools\run.ps1 tier4r-shadow `
  synthetic_lab\corpora\battle4_eilhart_trace_slices_v1.json `
  --dense-corpus synthetic_lab\corpora\battle4_eilhart_observed_dense_v2.json
.\synthetic_lab\tools\run.ps1 tier4r-adversary `
  synthetic_lab\corpora\battle4_eilhart_trace_slices_v1.json `
  synthetic_lab\scenarios\tactical_contract_adversarial_suite_v0.1N.json
.\synthetic_lab\tools\run.ps1 tier4r-assignment `
  synthetic_lab\corpora\battle4_eilhart_trace_slices_v1.json
.\synthetic_lab\tools\run.ps1 assignment-matrix `
  synthetic_lab\corpora\battle4_eilhart_trace_slices_v1.json `
  synthetic_lab\scenarios\tactical_baseline_matrix_v0.1O.json `
  synthetic_lab\scenarios\tactical_assignment_matrix_v0.1P.json
```

On Linux/macOS:

```bash
./synthetic_lab/tools/run.sh test
./synthetic_lab/tools/run.sh smoke
./synthetic_lab/tools/run.sh tier4r synthetic_lab/corpora/battle4_eilhart_observed_dense_v2.json
./synthetic_lab/tools/run.sh tier4r-trace \
  synthetic_lab/corpora/battle4_eilhart_observed_dense_v2.json \
  synthetic_lab/corpora/battle4_eilhart_trace_slices_v1.json
./synthetic_lab/tools/run.sh tier4r-shadow \
  synthetic_lab/corpora/battle4_eilhart_trace_slices_v1.json \
  --dense-corpus synthetic_lab/corpora/battle4_eilhart_observed_dense_v2.json
./synthetic_lab/tools/run.sh tier4r-adversary \
  synthetic_lab/corpora/battle4_eilhart_trace_slices_v1.json \
  synthetic_lab/scenarios/tactical_contract_adversarial_suite_v0.1N.json
./synthetic_lab/tools/run.sh tier4r-assignment \
  synthetic_lab/corpora/battle4_eilhart_trace_slices_v1.json
./synthetic_lab/tools/run.sh assignment-matrix \
  synthetic_lab/corpora/battle4_eilhart_trace_slices_v1.json \
  synthetic_lab/scenarios/tactical_baseline_matrix_v0.1O.json \
  synthetic_lab/scenarios/tactical_assignment_matrix_v0.1P.json
```

## Synthetic scenario commands

```powershell
.\synthetic_lab\tools\run.ps1 tier1 synthetic_lab\scenarios\tier1_karl_franz_front.json
.\synthetic_lab\tools\run.ps1 tier2 synthetic_lab\scenarios\tier2_late_game_pressure.json --turns 20 --seed 101
.\synthetic_lab\tools\run.ps1 tier3 synthetic_lab\scenarios\tier2_late_game_pressure.json --turns 20 --seeds 101,102,103,104,105
.\synthetic_lab\tools\run.ps1 tier4 synthetic_lab\scenarios\tier4_outnumbered_empire.json --seed 101
```

## Local artifact audits

```powershell
.\synthetic_lab\tools\run.ps1 audit-mods `
  --pack deepwar_2978779730=local_inputs\mods\deepwar\2978779730\original\DeepWar_AI.pack `
  --pack hecleas_2905096541=local_inputs\mods\hecleas\2905096541\original\hecleas_ai_overhaul.pack `
  --extracted-zip sfo_2792731173=local_inputs\mods\sfo\2792731173\extracted_ai_audit\SFO_audit.zip `
  --output-dir local_inputs\generated\mod_audits
```

The PFH5 reader is audit-only. It supports uncompressed, zero-dependency PFH5 packs and refuses broader cases rather than pretending to be a pack editor.

## Tactical temporal scheduling v0.1Q

`TACTICAL_TEMPORAL_SCHEDULE_V1` carries canonical v0.1P assignments across observations with explicit starts, continuations, minimum-commitment retention, reviewed reassignment, self-preservation supersession, cancellation, cooldown, maximum-commitment review, observational retirement, and continuity reset. Timing windows are project-owned anti-thrashing contracts, not WH3 movement estimates. All plans remain `ABSTRACT_SCHEDULED_NOT_ISSUED` and `NO_ORDERS`.

Run the Battle 4 schedule and temporal matrix:

```powershell
.\synthetic_lab\tools\run.ps1 tier4r-schedule `
  synthetic_lab\corpora\battle4_eilhart_trace_slices_v1.json
.\synthetic_lab\tools\run.ps1 schedule-matrix `
  synthetic_lab\corpora\battle4_eilhart_trace_slices_v1.json `
  synthetic_lab\scenarios\tactical_baseline_matrix_v0.1O.json `
  synthetic_lab\scenarios\tactical_schedule_matrix_v0.1Q.json
```

## Action-authority boundary v0.1R

Run the 12-scenario matrix and Battle 4 boundary report:

```powershell
.\synthetic_lab\tools\run.ps1 action-authority-matrix `
  synthetic_lab\scenarios\action_authority_matrix_v0.1R.json
.\synthetic_lab\tools\run.ps1 battle4-action-authority `
  synthetic_lab\corpora\battle4_eilhart_observed_dense_v2.json `
  research\runtime_evidence\BATTLE4_EILHART_TACTICAL_TEMPORAL_SCHEDULE_v0.1Q.json
```

These outputs test claim separation only. They do not issue commands or prove acknowledgement, execution, or outcome.

## Bounded tactical feasibility v0.1T

`TACTICAL_FEASIBILITY_ENVELOPE_V1` generates at most three role-aware candidate points for each active v0.1Q plan. Query evidence is exact-point-only: true supports that point at that instant, false vetoes that point, and neither establishes a route, formation, legal order, acknowledgement, execution, or outcome.

```powershell
.\synthetic_lab\tools\run.ps1 tier4r-feasibility `
  synthetic_lab\corpora\battle4_eilhart_trace_slices_v1.json
.\synthetic_lab\tools\run.ps1 feasibility-matrix `
  synthetic_lab\corpora\battle4_eilhart_trace_slices_v1.json `
  synthetic_lab\scenarios\tactical_feasibility_matrix_v0.1T.json
```

The Battle 4 artifact remains query-ready but unobserved at candidate level. The separate v0.1S aggregate profile is never projected onto those points.


## Semantic feasibility capability profile v0.1U

`TACTICAL_FEASIBILITY_SEMANTIC_CAPABILITY_PROFILE_V2` consumes the exact observed semantic calibration. It records 191 qualified explicit-point true samples and zero qualified false samples. The profile is capability context only and cannot populate any generated candidate result. Battle 4 therefore remains 34 query-ready envelopes and 102 unobserved points.


## Guarded and reserved tactical pipeline v0.1V–v0.1X

Run the new deterministic layers:

```powershell
.\tools\run.ps1 tier4r-guarded ..\synthetic_lab\corpora\battle4_eilhart_trace_slices_v1.json
.\tools\run.ps1 guarded-matrix ..\synthetic_lab\corpora\battle4_eilhart_trace_slices_v1.json ..\synthetic_lab\scenarios\tactical_guarded_action_matrix_v0.1V.json
.\tools\run.ps1 tier4r-reservations ..\synthetic_lab\corpora\battle4_eilhart_trace_slices_v1.json
.\tools\run.ps1 reservation-matrix ..\synthetic_lab\scenarios\tactical_endpoint_reservation_matrix_v0.1W.json
.\tools\run.ps1 pipeline-audit ..\synthetic_lab\corpora\battle4_eilhart_trace_slices_v1.json ..\synthetic_lab\scenarios\tactical_pipeline_adversarial_scaling_v0.1X.json
```

The guarded layer fails closed unless packet identity, source plan digest, actor uniqueness, source geometry, and exact `QUERY_TRUE` evidence agree. The reservation layer guarantees only endpoint-coordinate separation. The v0.1X audit exercises the full state-to-reservation chain under deterministic fuzzing, representation changes, authority attacks, and structural scale. None of these commands issues a WH3 order.
