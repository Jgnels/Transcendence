# v0.2N Owner Handoff — Native CAI Behavior Study

This owner run is a fresh **vanilla-only** research cohort. It uses privileged read-only telemetry for development and is permanently application-ineligible.

## Prepare

Extract the v0.2N owner kit into its own folder. Open PowerShell in that folder and run:

```powershell
.\runtime_probe\tools\Prepare-NativeBehaviorStudy.ps1
```

If WH3 cannot be auto-discovered:

```powershell
.\runtime_probe\tools\Prepare-NativeBehaviorStudy.ps1 -GameRoot "C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III"
```

When asked, allow the exact diagnostic pack to be copied. Configure the WH3 launcher with **only** `transcendence_native_diagnostic_probe.pack` enabled.

## Campaign protocol

Start a **new disposable Karl Franz / Reikland Immortal Empires campaign**:

- Legendary campaign difficulty;
- Very Hard battle difficulty;
- play normally;
- autoresolve is allowed;
- do not enable SFO or any other mod;
- reach the start of **Reikland turn 11** (10 complete AI end-turn cycles after turn 1 starts).

The study does not require passive play. The important controls are the fresh campaign, exact mod profile, consecutive turns and unchanged probe/profile hashes.

## Collect

Exit WH3 completely, then run:

```powershell
.\runtime_probe\tools\Collect-NativeBehaviorStudy.ps1
```

Upload the resulting `Transcendence_NativeBehaviorStudy_VANILLA_....zip`.

If WH3 crashes, do not repeatedly retry. Exit fully and run the collector anyway. A short/nonconfirmatory bundle is still useful for instrumentation debugging.

## What the study is allowed to conclude

The study tests preregistered recovery-reentry and temporal-reversal signals. A positive result is a causal-review candidate and can at most earn a narrow native-row ablation. It cannot directly authorize project-owned orders or strategic planning.
