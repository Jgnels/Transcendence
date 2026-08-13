# Native CAI Diagnostic Telemetry Owner Handoff — v0.2M

**Authority:** `NO_ORDERS`  
**Application authority:** `PROHIBITED`  
**Research visibility:** `PRIVILEGED_OMNISCIENT_DIAGNOSTIC`  
**Application eligible:** `false`

## Why this replaces an immediate SFO churn run

The v0.2L vanilla capture produced 14 consecutive player turns and exact profile/probe binding, but zero eligible directional-churn windows. Of 187 possible four-frame actor windows, 149 were right-censored by player visibility and the remaining 38 were non-directional/stationary. Under frozen decision D109, **do not run the v0.2L SFO match**.

v0.2M does not relax the v0.2L endpoint after seeing the result. It qualifies a separate research-only telemetry plane that can inspect complete AI-faction forces at that faction's own turn start/end. Those hidden inputs are permanently forbidden from the application/runtime decision architecture.

## Preparation

1. Extract the v0.2M owner kit.
2. Close WH3.
3. Open PowerShell in the extracted kit root.
4. Run:

```powershell
.\runtime_probe\tools\Prepare-NativeDiagnosticCapture.ps1
```

The script builds the deterministic research-only pack, asks before copying it into `WH3\data`, and then asks you to configure the launcher with **only**:

`transcendence_native_diagnostic_probe.pack`

No SFO and no other mods for this qualification run.

## Run

Start a **new disposable Karl Franz / Reikland Immortal Empires** campaign:

- Legendary campaign difficulty
- Very Hard battle difficulty
- advance through at least **6 consecutive Reikland turn starts**

You may play normally. This is an instrumentation-density qualification only, not a native-AI quality verdict, so there is no passive-action attestation.

The probe is read-only. It listens to AI `FactionTurnStart`/`FactionTurnEnd` events and records full AI faction armies/regions/wars for offline research. It does not issue orders, change DB rows, mutate saves, or modify campaign state.

## Collection

Exit WH3 completely, then run:

```powershell
.\runtime_probe\tools\Collect-NativeDiagnosticCapture.ps1
```

Upload the generated:

`Transcendence_NativeDiagnostic_VANILLA_*.zip`

The upload contains the diagnostic log, public profile binding, verification, summary, and hash manifest. It excludes private machine paths.

## Qualification rule frozen before live data

The diagnostic channel qualifies for a later preregistered behavior study only if the capture contains at least:

- 20 paired AI faction-turn start/end observations;
- 50 matched force start/end pairs;
- 10 moved force-turn pairs;
- 5 pairs of consecutive non-zero movement vectors suitable for trajectory analysis.

Passing these thresholds is **not evidence that native CAI is good or bad**. It only proves the research instrument has enough exposure to justify freezing the next behavioral hypothesis.
