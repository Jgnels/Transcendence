# v0.2N Native CAI Diagnostic Behavior Study — Preregistration

Date frozen: 2026-08-03  
Status: **FROZEN BEFORE FRESH CONFIRMATORY OWNER DATA**  
Authority: `NO_ORDERS`  
Application authority: `PROHIBITED`  
Research visibility: `PRIVILEGED_OMNISCIENT_DIAGNOSTIC`  
Application eligible: `false`

## Why this study exists

The completed v0.2M-r1 owner qualification capture proved that privileged read-only campaign telemetry is dense enough to study native CAI behavior: 1,588 paired AI faction turns, 2,353 matched army-turn pairs, 967 moving army-turns, and 426 multi-turn trajectory pairs across six complete AI cycles, with zero capability failures and zero incomplete normal AI faction turns.

That same capture is **exploratory only** for behavior. The next endpoints below were refined after inspecting it, and v0.2M-r1 had no pending-battle participant channel. Therefore the old cohort is structurally ineligible for confirmation. v0.2N requires a fresh campaign log created after this preregistration is frozen.

Frozen threshold digest: `4499a497bfc7dd6a33a6c0a50da4e1e52b1705d1f2f20f1a917cdfebeb5486ac`.

## Research question A — recovery protection

**Question:** In a fresh vanilla cohort, does native CAI place materially damaged field armies on the attacker side of a pending battle during that faction's own turn often enough to merit causal review and a native-row ablation?

### Frozen exposure definition

A `recovering army-turn` is a field army observed at its faction `TURN_START` with average unit health below **65%**. The 65% threshold is inherited from the existing Transcendence recovery engineering hypothesis; it is **not** claimed to be a Creative Assembly constant or an empirically optimal cutoff.

### Frozen event definition

A recovery re-entry candidate requires that same faction + military-force CQI to appear on the `ATTACKER` side of a `ScriptEventPendingBattle` cache record between its own `TURN_START` snapshot end and `TURN_END` snapshot begin.

Defender-side participation is counted separately and **never** promoted to offensive recovery misuse. Attacker-side status is still only a stronger proxy: ambush, interception, scripted or unusual battle mechanics may require causal review before intent is inferred.

### Frozen primary recovery endpoint

- minimum recovery exposure: **10 recovering army-turns**;
- minimum attacker-side recovery re-entry army-turns: **2**;
- minimum attacker-side recovery re-entry rate: **20%** of recovering army-turns.

Classification:

- exposure <10 → `INSUFFICIENT_RECOVERY_EXPOSURE`;
- exposure >=10 and both signal thresholds pass → `RECOVERING_ATTACKER_SIDE_REENTRY_SIGNAL_OBSERVED`;
- otherwise → `NO_PREREGISTERED_RECOVERY_SIGNAL_IN_COHORT`.

A positive signal does **not** prove broken recovery logic. It earns causal review and, if a mechanistically relevant current native DB surface exists, the smallest plausible native-row ablation.

## Research question B — temporal commitment / directional persistence

**Question:** In a fresh vanilla cohort, do the same native AI field armies repeatedly reverse realized multi-turn movement direction under stable observed own-context and with no recorded battle participation?

The endpoint studies an observable pathology proxy. It does not expose native task IDs, assignment memory, or engine-internal hysteresis.

### Frozen three-endpoint window eligibility

For the same faction + force CQI at three consecutive `TURN_END` observations:

1. turns must be consecutive;
2. war set must be exactly unchanged;
3. owned-region set must be exactly unchanged;
4. stance must be unchanged;
5. average unit-health range must be <= **5 percentage points**;
6. force-strength max/min ratio must be <= **1.10**;
7. unit-count range must be <= **1**;
8. each realized movement vector must be at least **5 campaign-coordinate units**;
9. the force must have **no recorded pending-battle participation on either side** between the first and last endpoint.

An eligible window is a reversal candidate when cosine between the two movement vectors is <= **-0.5**, i.e. a heading reversal of at least 120 degrees.

### Frozen primary temporal endpoint

The cohort must contain at least **20 eligible battle-free stable-context directional windows** before any negative or positive temporal result can be interpreted.

A positive temporal signal requires either:

- the same faction + force CQI to have at least **2 non-overlapping** eligible reversal windows; or
- an exact five-endpoint region pattern `A -> B -> A -> B -> A` under the same stability, movement-distance, heading-reversal, consecutive-turn and battle-exclusion rules.

Classification:

- eligible denominator <20 → `INSUFFICIENT_TEMPORAL_EXPOSURE`;
- denominator >=20 and repeated/non-overlapping or exact-ABABA condition passes → `REPEATED_BATTLE_FREE_REVERSAL_SIGNAL_OBSERVED`;
- otherwise → `NO_PREREGISTERED_TEMPORAL_SIGNAL_IN_COHORT`.

Nearest visible/diagnostic enemy-force and enemy-region distances may be reported for causal review but are **descriptive only** and are not primary eligibility criteria.

## Battle-telemetry integrity requirement

The confirmatory evaluator refuses a trace unless its loaded probe explicitly declares `battle_participant_telemetry=true`. This prevents the v0.2M-r1 cohort—or any older log with no battle channel—from being retrospectively treated as battle-free merely because no battle records exist.

The owner collector additionally requires:

- at least one complete battle sequence somewhere in the fresh cohort, proving the battle marker surface was observed;
- zero incomplete battle sequences;
- zero diagnostic capability failures;
- zero incomplete normal AI faction-turn snapshots;
- exact profile/hash binding preserved after the run.

Failure of these integrity checks makes the capture nonconfirmatory, but it may still be retained for instrumentation debugging.

## Fresh owner cohort

Profile: vanilla WH3 + `transcendence_native_diagnostic_probe.pack` only.  
Campaign: new disposable Karl Franz / Reikland Immortal Empires.  
Difficulty: Legendary campaign / Very Hard battle.  
Player actions: unrestricted normal play; autoresolve is allowed.  
Duration: **10 complete AI cycles**, operationalized as consecutive Reikland turn-start markers **1 through 11** or an equivalent 11 consecutive markers from a fresh campaign.

The log is cleared after exact profile binding and before campaign launch. Data produced before this preregistration is not confirmatory input.

## Sequential SFO rule

Do **not** request the SFO match before vanilla is collected and adjudicated.

Request a matched SFO cohort only if:

1. the vanilla capture is confirmatory-eligible; and
2. at least one endpoint has sufficient exposure (`recovery_status != INSUFFICIENT_RECOVERY_EXPOSURE` or `temporal_status != INSUFFICIENT_TEMPORAL_EXPOSURE`).

If both endpoints are exposure-insufficient, redesign acquisition rather than spending another owner session on SFO. This sequencing rule may not change the frozen vanilla endpoint after seeing results.

## Interpretation ladder

Positive signal:

`fresh diagnostic signal -> causal review -> identify mechanistically relevant native DB surface -> preregister narrow native-row ablation -> compare outcomes`

Never:

`diagnostic signal -> project strategic planner`

Negative signal:

A sufficiently exposed cohort with no signal means only that the preregistered signal was not observed in that campaign window. It does not prove native recovery protection, assignment memory, hysteresis, reserve policy, or general strategic quality.

## Application boundary

Every v0.2N trace and result is research-only and `application_eligible=false`. Complete foreign faction state and pending-battle diagnostics may not be wired into shipping/application-time decisions. Native WH3 CAI remains the default planner/executor while this gate is active.
