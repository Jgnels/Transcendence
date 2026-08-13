# Native CAI Directional-Churn Owner Handoff — v0.2L

**Date:** 2026-08-02  
**Authority:** `NO_ORDERS`  
**Application:** `PROHIBITED`  
**First live profile:** `VANILLA`  
**SFO run:** conditional on vanilla producing at least one eligible primary window

## Why this owner run exists

v0.2L preregisters one narrow, player-visible native-CAI failure signal before seeing new owner data. It asks whether a continuously visible foreign army repeatedly oscillates between two visible region anchors in an `A -> B -> A` pattern while all other observed anchors remain exactly stable.

This is **not** a general campaign-AI quality test. It is an instrumentation/falsification run designed to determine whether the conservative endpoint is observable under normal WH3 player-visibility limits.

## Do not run SFO first

Run **VANILLA only** first.

After the vanilla upload is processed:

- if `eligible_stable_context_region_windows == 0`, stop. Do not spend owner time on the SFO match; the observation protocol needs redesign or a different cohort;
- if `eligible_stable_context_region_windows > 0`, the endpoint is at least observable and a matched SFO run may be requested for descriptive comparison.

This sequencing changes owner burden only. It does not change the frozen endpoint, thresholds, exclusions, or interpretation.

## Preparation

1. Extract the sealed v0.2L owner kit.
2. Close WH3 if it is running.
3. Open PowerShell in the extracted kit root.
4. Run:

```powershell
.\runtime_probe\tools\Prepare-NativeChurnCapture.ps1 -Profile VANILLA
```

The preparation script:

- builds only the deterministic read-only shadow probe;
- verifies its mutation flags remain false;
- copies it into `WH3\data` only after explicit confirmation if needed;
- asks you to configure the launcher to **only** the shadow probe for vanilla;
- binds the exact WH3 executable, probe, launcher profile and campaign protocol before launch;
- archives any prior Transcendence runtime log;
- does not launch WH3 and does not enable/disable mods itself.

If WH3 cannot be found automatically, rerun with the exact install folder:

```powershell
.\runtime_probe\tools\Prepare-NativeChurnCapture.ps1 -Profile VANILLA -GameRoot "D:\SteamLibrary\steamapps\common\Total War WARHAMMER III"
```

Use your actual path; the example path is not assumed.

## Vanilla observation protocol

After preparation succeeds:

1. Launch WH3 normally.
2. Start a **new disposable Karl Franz / Reikland Immortal Empires** campaign.
3. Campaign difficulty: **Legendary**.
4. Battle difficulty: **Very Hard**.
5. Observe at least **12 consecutive Reikland turn starts**.
6. During the observation window issue **no voluntary campaign orders**:
   - no army/agent movement;
   - no recruitment;
   - no stance changes;
   - no initiated diplomacy;
   - no construction;
   - no voluntary spending.
7. Resolve only mandatory prompts or battles necessary to keep the campaign advancing. If the passive protocol is broken, do not hide it; the collector will mark the capture nonconfirmatory unless you truthfully attest the protocol.
8. Do not activate another mod during the run.
9. After the final observed turn start, exit WH3 completely.

The deliberately passive player is an experimental control to keep **observed** context stable. Results are not generalized to ordinary active play without later evidence.

## Collection

Back in PowerShell, run:

```powershell
.\runtime_probe\tools\Collect-NativeChurnCapture.ps1
```

The collector asks whether the passive protocol was followed. Type `YES` only if true.

It then:

- verifies the prelaunch hashes again;
- verifies the runtime loaded exactly the read-only shadow probe kind;
- checks the launcher profile did not drift;
- permits only the specifically modeled case where a local probe entry was absent prelaunch and materialized at runtime;
- requires consecutive Reikland snapshots;
- runs the frozen v0.2L endpoint;
- packages only public-safe evidence.

The upload ZIP contains only:

- `export_manifest.json`
- `native_churn_capture_verification.json`
- `native_churn_profile_binding.json`
- `probe_summary.json`
- `transcendence_runtime_log.txt`

It excludes private local paths, `used_mods` private copies, raw SFO pack bytes, and private binding material.

Upload the generated `Transcendence_NativeChurn_VANILLA_*.zip` to the project chat.

## What counts as a result

A valid run can still be scientifically useful if the answer is **insufficient exposure**.

Possible capture statuses include:

- `PROFILE_BOUND_CAPTURE_OBSERVED_PRIMARY_ENDPOINT_EVALUABLE`
- `PROFILE_BOUND_CAPTURE_OBSERVED_INSUFFICIENT_PRIMARY_EXPOSURE`
- `PROFILE_BOUND_CAPTURE_OBSERVED_PROTOCOL_DEVIATION_NONCONFIRMATORY`

A positive repeated cluster is only a player-visible causal-review signal. It cannot directly authorize v0.2G, v0.2I, or another project-owned strategic planner.
