# v0.2O Owner Handoff — Matched SFO Native-CAI Behavior Benchmark

This is the matched SFO follow-up earned by the completed v0.2N vanilla cohort. It uses the same read-only privileged diagnostic probe and remains permanently application-ineligible.

## Prepare

Extract the v0.2O owner kit into its own folder. Open PowerShell in that folder and run:

```powershell
.\runtime_probe\tools\Prepare-NativeSFOBehaviorBenchmark.ps1
```

The preparer will:

1. auto-discover WH3;
2. auto-discover SFO Workshop item `2792731173`;
3. verify `sfo_grimhammer_3_main.pack` against the owner-verified SHA-256 `ae20a0a08037aa3ebcbe7461d2589fc28dc15a5fe5d9ca4c0a9d0ff0a26da603`;
4. build/install the exact read-only diagnostic probe;
5. require the launcher to contain exactly SFO main + `transcendence_native_diagnostic_probe.pack` and no other mods;
6. bind the WH3 executable, SFO pack, probe pack and exact `used_mods.txt` bytes before clearing the old diagnostic log.

If Steam/SFO autodiscovery fails, you may provide explicit paths:

```powershell
.\runtime_probe\tools\Prepare-NativeSFOBehaviorBenchmark.ps1 -GameRoot "C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III" -SfoPackPath "C:\Program Files (x86)\Steam\steamapps\workshop\content\1142710\2792731173\sfo_grimhammer_3_main.pack"
```

If the SFO hash has changed, **stop**. Do not bypass the check; the benchmark must first be rebound to the new SFO version.

## Campaign protocol

Start a **new disposable Karl Franz / Reikland Immortal Empires SFO campaign**:

- Legendary campaign difficulty;
- Very Hard battle difficulty;
- play normally;
- autoresolve is allowed and preferred for speed;
- exactly SFO main + the diagnostic probe enabled;
- no other mods;
- reach the start of **Reikland turn 11** (10 complete AI cycles).

This is a research benchmark. The probe issues no orders and does not modify gameplay.

## Collect

Exit WH3 completely, then run:

```powershell
.\runtime_probe\tools\Collect-NativeSFOBehaviorBenchmark.ps1
```

Upload the resulting `Transcendence_NativeBehaviorStudy_SFO_....zip`.

The collector re-hashes WH3, SFO, the probe and launcher profile before accepting the run. The upload contains the behavior telemetry and public hashes but **does not contain the 1.85 GB SFO pack or local machine paths**.

If WH3 crashes, do not repeatedly retry. Exit fully and report the crash before changing the profile; preserve the diagnostic log.

## Interpretation boundary

The primary strategic temporal population is prospectively frozen as territorial factions (non-empty stable owned-region set). Non-territorial/roaming factions are reported separately. The original v0.2N thresholds remain unchanged.

Any SFO/vanilla difference is a benchmark signal only. It cannot identify a specific SFO row as causal and cannot authorize project-owned campaign orders.
