# Gate 0 — SFO Preparation PowerShell Handoff Hotfix v0.1Y-r1

## Result

The owner-machine preparation blocker is corrected offline. The live SFO continuity gate remains open.

## Preserved owner failure

- v0.1Y repository installation passed 73 SyntheticLab tests, 89 Runtime Probe tests, 162 total tests, and 298 canonical hashes.
- `prepare_sfo_combined_session.ps1` then failed before probe installation.
- Windows PowerShell reported that a `System.String` could not bind to the common `Confirm` parameter's `SwitchParameter` type.
- The failed step occurred before launcher verification, log clearing, watcher startup, or gameplay.

## Root cause

The wrapper launched `prepare_live_probe.ps1` through a second `powershell.exe -File` process while supplying `-Confirm:$false`. Across that process boundary, Windows PowerShell 5.1 received a serialized string rather than an in-process Boolean/switch expression.

## Correction

The wrapper now:

1. resolves `prepare_live_probe.ps1`;
2. constructs an in-process splatted parameter map;
3. binds `InstallShadow = $true`, `Force = $true`, and `Confirm = $false`;
4. invokes the script directly in the current PowerShell process;
5. preserves all existing build, hash, backup, and explicit-install behavior in the underlying installer.

## Regression

A repository test requires the direct splatted invocation and rejects the previous child-process `-File ... -Confirm:$false` pattern.

## Remaining live condition

After installing v0.1Y-r1, rerun `runtime_probe\tools\prepare_sfo_combined_session.ps1`. The five-turn, two-battle SFO continuity requirement is unchanged.

## Offline validation

- 73 SyntheticLab tests passed.
- 90 Runtime Probe tests passed.
- 163 total tests passed.
- Full repository validation is sealed after canonical-ledger regeneration.
