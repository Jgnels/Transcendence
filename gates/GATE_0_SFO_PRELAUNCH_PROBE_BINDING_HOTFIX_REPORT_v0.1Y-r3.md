# Gate 0 — SFO Prelaunch Probe-Binding Hotfix v0.1Y-r3

## Result

The owner-machine prelaunch probe-binding blocker is corrected offline. The live SFO combined-session continuity gate remains open.

## Preserved owner result

- v0.1Y-r2 installed successfully with 73 SyntheticLab tests, 95 Runtime Probe tests, 168 total tests, and 303 canonical hashes.
- The preparation workflow rebuilt and installed the exact read-only shadow probe.
- A supported `used_mods.txt` was found.
- Preflight then failed because the active list did not contain the exact literal `transcendence_shadow_probe.pack`.
- WH3 was not launched; the runtime log was not cleared; the checkpoint watcher was not started.

## Evidence classification

`OBSERVED`: the exact-literal lookup failed after owner launcher configuration.

`UNVERIFIED`: whether the owner file used a safe load-order decorator or materialized only SFO before first WH3 launch. The error output did not disclose the parsed names.

## Correction

- Bind an exact probe name directly.
- Accept one launcher-decorated alias only when stripping `@`, `!`, or `~` yields the canonical probe filename; bind the record to the exact installed pack bytes.
- Reject duplicate exact/decorated aliases.
- If the launcher file contains exactly one SFO pack and no extras, emit schema-2 profile `SFO_ONLY_PLUS_READ_ONLY_PROBE_RUNTIME_DEFERRED`.
- Preserve the exact expected probe hash and require runtime confirmation.
- Final SFO certification accepts deferred preflight only when the combined gate proves the exact prepared/installed hash and observes the battle probe at runtime.
- Extra mods, unrelated aliases, missing markers, or wrong hashes fail closed.

## Authority

The correction changes repository evidence handling only. It does not enable mods, issue orders, change saves, or claim the probe loaded before runtime evidence exists.

## Offline validation

- 73 SyntheticLab tests passed.
- 99 Runtime Probe tests passed.
- 172 total tests passed.
- Full repository validation passed twice after ledger sealing.

## Smallest owner step

Install v0.1Y-r3 and rerun `runtime_probe\tools\prepare_sfo_combined_session.ps1`. No cleanup or launcher reconfiguration should be required unless the launcher no longer shows exactly SFO plus the probe.
