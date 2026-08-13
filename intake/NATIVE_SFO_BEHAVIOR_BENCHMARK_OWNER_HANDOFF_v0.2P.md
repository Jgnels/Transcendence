# v0.2P Matched SFO Behavior Benchmark — Owner Handoff

The owner action is unchanged in substance from v0.2O, but the collector now emits v0.2P cluster diagnostics and the precommitted mechanistic decision branch automatically.

## Prepare

From the extracted owner kit in PowerShell:

```powershell
.\runtime_probe\tools\Prepare-NativeSFOBehaviorBenchmark.ps1
```

The tool must verify the pinned SFO pack identity and the exact active two-pack launcher profile:

- `sfo_grimhammer_3_main.pack`
- `transcendence_native_diagnostic_probe.pack`

No other mods.

## Campaign

Start a new disposable Karl Franz / Reikland Immortal Empires campaign:

- Legendary campaign difficulty;
- Very Hard battle difficulty;
- normal play allowed;
- autoresolve allowed;
- reach at least the start of Reikland turn 11.

## Collect

Exit WH3 completely, then run:

```powershell
.\runtime_probe\tools\Collect-NativeSFOBehaviorBenchmark.ps1
```

Upload the produced `Transcendence_NativeBehaviorStudy_SFO_*.zip`.

## Important

v0.2P is still research-only. The diagnostic observer is privileged and permanently `application_eligible=false`. The benchmark cannot issue orders or modify campaign behavior.
