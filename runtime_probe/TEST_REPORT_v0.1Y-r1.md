# Runtime Probe Test Report — v0.1Y-r1

## Result

- SyntheticLab: 73 passed.
- Runtime Probe: 90 passed.
- Total: 163 passed.

## Owner-observed failure preserved

The first v0.1Y SFO preparation attempt failed before mutation because `-Confirm:$false` crossed a child `powershell.exe -File` boundary and reached Windows PowerShell 5.1 as a string instead of a `SwitchParameter`.

## Regression

`test_v01y_r1_probe_install_invocation_binds_confirm_in_process` requires direct in-process invocation with a splatted `Confirm = $false` parameter and rejects the former external invocation pattern.

## Limit

PowerShell is not available in the offline build environment. The direct Windows PowerShell execution remains owner-machine validation. The live SFO five-turn/two-battle continuity gate remains open.
