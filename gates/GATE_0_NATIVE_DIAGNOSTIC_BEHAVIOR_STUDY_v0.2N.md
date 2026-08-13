# Gate 0 — Native Diagnostic Behavior Study v0.2N

Status: **OWNER CONFIRMATORY COHORT COMPLETE — CAUSAL REVIEW CLOSED IN v0.2O**

## Gate objective

Use a fresh, profile-bound, research-only vanilla cohort to test two narrow native-CAI behavior hypotheses without granting Transcendence campaign authority:

1. materially damaged field-army attacker-side battle re-entry;
2. repeated battle-free stable-context multi-turn heading reversal.

## Binding preregistration

See `research/NATIVE_DIAGNOSTIC_BEHAVIOR_STUDY_PREREGISTRATION_v0.2N.md`.

Frozen threshold digest:

`4499a497bfc7dd6a33a6c0a50da4e1e52b1705d1f2f20f1a917cdfebeb5486ac`

## Required evidence integrity

- fresh log created after preregistration;
- exact vanilla + diagnostic-probe launcher/profile binding before and after run;
- 11 consecutive human turn-start markers (10 complete AI cycles);
- `battle_participant_telemetry=true` declared by the loaded probe;
- >=1 complete pending-battle sequence somewhere in the run;
- 0 incomplete battle sequences;
- 0 diagnostic capability failures;
- 0 incomplete normal AI faction-turn snapshots;
- privileged data remains `application_eligible=false`;
- no campaign order/application path.

## Pass/fail semantics

This gate does not have a binary “native AI good/bad” outcome.

- `SIGNAL_OBSERVED`: causal review and a mechanistically narrow native-row ablation may be earned.
- `NO_SIGNAL_WITH_SUFFICIENT_EXPOSURE`: preserve native-first architecture; no application authority change.
- `INSUFFICIENT_EXPOSURE`: redesign or extend acquisition; do not infer absence.
- `INSTRUMENTATION_INVALID`: debug the observer; do not interpret behavior.

No result directly authorizes v0.2G/v0.2I or project-owned strategic planning.

## SFO sequencing

Matched SFO acquisition is conditional. It is requested only after a confirmatory-eligible vanilla run and only if at least one endpoint has sufficient exposure.

## Offline certification before owner acquisition

- SyntheticLab: **179/179 PASS**.
- Runtime Probe: **191/191 PASS**.
- Combined direct regression: **370/370 PASS**.
- Standalone extracted owner-kit smoke test: prepare → exact profile bind → 11 synthetic turn markers → pending-battle participant parse → collect → confirmatory public-safe ZIP: **PASS**.
- Normal `transcendence_shadow_probe.lua` is byte-identical to the sealed v0.2M canonical source.
- New/modified v0.2N diagnostic tooling contains no campaign/battle order or mutation call surface under the static audit.

Whole-repository manifest validation is run again on the sealed tree before packaging.


## Owner closure — 2026-08-03

The fresh owner cohort passed confirmatory integrity. Recovery had sufficient exposure but no preregistered signal (38 exposures, 6 attacker-side reentries, 15.7895%). Temporal formally observed a repeated signal (106 eligible, 18 candidates, one repeated force), but causal review found the sole repeated trigger in the non-territorial Grey Point Scuttlers Rogue Pirate patrol. No ordinary native-CAI row ablation is earned from this gate alone. See `research/NATIVE_BEHAVIOR_STUDY_CAUSAL_REVIEW_v0.2O.md`.
