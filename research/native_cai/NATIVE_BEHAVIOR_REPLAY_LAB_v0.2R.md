# Native CAI Behavior Replay Lab — v0.2R

**Status:** OFFLINE ENGINEERING IMPLEMENTED; REAL RAW CAPTURE REPLAY PENDING CAPTURE AVAILABILITY  
**Authority:** `NO_ORDERS`  
**Application authority:** `PROHIBITED`  
**Research visibility:** `PRIVILEGED_OMNISCIENT_DIAGNOSTIC`  
**Application eligible:** `false`

## Purpose

v0.2R adds a deterministic offline replay layer around the existing native-diagnostic capture ZIP contract. It does not change the game-side diagnostic probe, the player-visible observer, any frozen v0.2N/v0.2P threshold, or the v0.2Q Stage-A replication policy.

The lab is a verifier/replayer, not a new behavior definition. Frozen behavior metrics are recomputed by calling the existing sealed evaluators:

- `analyze_native_diagnostic_behavior_study` for v0.2N recovery and temporal behavior;
- `stratify_temporal_trace` and `temporal_cluster_diagnostics` for territorial/non-territorial and cluster diagnostics;
- `analyze_sfo_benchmark` for the v0.2P SFO matched benchmark;
- `adjudicate_sfo_replication_stage_a` only when the caller explicitly declares an SFO capture as Stage A.

## Capture normalization and fail-closed rules

`runtime_probe/tools/native_behavior_replay.py`:

1. validates ZIP integrity and rejects duplicate/unsafe member names;
2. validates the public `export_manifest.json` member inventory, sizes and SHA-256 values;
3. optionally binds the whole capture ZIP to an externally supplied SHA-256;
4. enforces `NO_ORDERS`, `APPLICATION_AUTHORITY=PROHIBITED`, privileged-research visibility and `application_eligible=false` across the manifest, profile binding and parsed trace;
5. recognizes only the existing diagnostic event vocabulary and fails closed on unknown future `TRANS_DIAG` events;
6. distinguishes complete AI faction turns, incomplete turns, complete battles and incomplete battle sequences;
7. refuses frozen metric replay when battle-participant telemetry is missing/undeclared, a faction turn is incomplete, a battle sequence is incomplete, a capability failed, or human-turn continuity is absent;
8. never converts missing battle telemetry into a `no battle` conclusion;
9. checks a stored frozen result against the deterministic recomputation when the capture contains one.

Supported public export contracts are the vanilla behavior study, the SFO matched behavior benchmark and the earlier generic native diagnostic export. Only the first two are profile-qualified for vanilla↔SFO comparison.

## Longitudinal force timeline

For every paired AI faction turn and every observed force CQI, Replay Lab emits deterministic timeline rows containing where available:

- faction and military-force CQI;
- turn and start/end presence;
- start/end position and realized within-turn movement distance;
- start/end region and stance;
- start/end unit count, average health, force strength and action-points remaining;
- current war set and owned-region set;
- territorial/non-territorial classification;
- battle sequence participation and attacker/defender roles;
- telemetry-completeness marker;
- CQI identity-discontinuity flag.

A consecutive reuse of the same `(faction, force_cqi)` with a changed general/subtype identity is flagged as `FORCE_CQI_CONSECUTIVE_IDENTITY_CHANGE`. The replay lab does not silently rewrite historical frozen metrics because of that flag; it makes the discontinuity visible for causal review.

## Deterministic outputs

Single-capture replay writes:

- `normalized.json` — normalized provenance, completeness, timeline, frozen replay and exploratory diagnostics;
- `summary.json` — compact frozen-result summary;
- `timeline.csv` — per-force longitudinal rows;
- `report.md` — human-readable research-only report.

Vanilla↔SFO comparison writes:

- `comparison.json`;
- `comparison.md`.

The comparison explicitly separates:

- `PREREGISTERED_RESULT`;
- `CAUSAL_REVIEW`;
- `EXPLORATORY`;
- mechanism-nomination eligibility.

No one-vanilla/one-SFO comparison can set mechanism nomination or native-row ablation eligibility to true. A Stage-A SFO capture can only apply the already frozen v0.2Q Stage-A policy when explicitly declared with `--sfo-role stage-a`; Stage A still never earns a row ablation by itself.

## Commands

Replay one capture:

```powershell
.\runtime_probe\tools\Replay-NativeBehavior.ps1 replay `
  <capture.zip> `
  --expected-sha256 <capture_sha256> `
  --output-dir <output_directory>
```

Compare vanilla and SFO:

```powershell
.\runtime_probe\tools\Replay-NativeBehavior.ps1 compare `
  --vanilla <vanilla_capture.zip> `
  --sfo <sfo_capture.zip> `
  --output-dir <output_directory>
```

For the future v0.2Q Stage-A SFO replication only, add:

```text
--sfo-role stage-a
```

Do not infer Stage-A status from timestamps or filenames.

## Adversarial coverage

The v0.2R regression suite covers:

- payload hash mismatch / tampered manifest inventory;
- wrong externally supplied capture SHA-256;
- duplicate ZIP members;
- unknown future diagnostic event;
- missing battle telemetry;
- partial faction turn;
- incomplete battle sequence;
- duplicate force records;
- destroyed/recreated or recycled CQI identity discontinuity;
- stationary army;
- roaming/non-territorial faction;
- overlapping reversal windows;
- one-faction candidate concentration;
- insufficient denominator;
- disappearing faction observations;
- deterministic replay output bytes;
- deterministic comparison output bytes;
- explicit Stage-A policy application with no ablation authority;
- frozen v0.2Q published reference numbers and replication-policy digest;
- byte identity of both game-side Lua probes.

## Frozen reference bindings

Regression tests preserve the sealed v0.2Q reference facts:

- vanilla recovery: `38` exposures / `6` attacker-side reentries = `0.157895`;
- vanilla territorial temporal: `48` eligible / `13` reversals = `0.270833`;
- SFO recovery rate: `0.142857`;
- SFO territorial temporal: `39` eligible / `18` reversals = `0.461538`;
- v0.2Q replication-policy digest: `3171982731ca16a635723f5d5a788c6ce5fb397590f82a60cabb221e26ac0120`.

The game-side Lua probes are asserted unchanged at:

- native diagnostic: `0acb4e186a4f4077801a763dbbf5cacc8ae21a9d47ecc76d54fefe5c023ec203`;
- shadow probe: `4f8c80fb67efe288e4b7b4eeacc0c48578707a0e554f2dd8a454aa669b50ed98`.

## Current evidence boundary

The sealed v0.2Q canonical source contains the published result/reference artifacts but not the owner's raw vanilla and SFO behavior-study capture ZIPs. Therefore v0.2R can certify its replay machinery and frozen bindings offline now, but it cannot honestly claim a fresh byte-for-byte replay of those two historical raw capture ZIPs until those captures are supplied.

That absence does not block Stage-A engineering or future capture replay, and it does not alter the existing v0.2Q conclusions.
