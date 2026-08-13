# Gate 0 — SFO Watcher Handshake Hotfix v0.1Y-r5

## Result

The owner-machine checkpoint-watcher startup blocker is corrected offline. The live SFO combined-session continuity gate remains open.

## Preserved owner result

- v0.1Y-r4 installed successfully with 73 SyntheticLab tests, 104 Runtime Probe tests, 177 total tests, and 307 canonical hashes.
- Exact owner-machine preflight succeeded for the WH3 executable, SFO pack, two-pack load order, shadow-probe pack, and Legendary/Very Hard Karl Franz settings.
- SFO pack SHA-256: `ae20a0a08037aa3ebcbe7461d2589fc28dc15a5fe5d9ca4c0a9d0ff0a26da603`.
- Shadow probe SHA-256: `0714863e2081206aa7d0790ec14d7c3c3c7ae33eea416d72dba0d6a2ecd0a89e`.
- The preparation failed only because the watcher status PID did not equal the `Start-Process` launcher PID.
- WH3 was not launched for the capture; no campaign or save was loaded.

## Correction

- Generate a 256-bit per-session handshake token.
- Pass the token to the watcher and publish it in schema-2 status and checkpoint manifests.
- Accept readiness only when the status token matches, independent of launcher/interpreter PID identity.
- Preserve both launcher PID and actual watcher PID privately.
- Redirect watcher stdout and stderr to private session diagnostics.
- Surface nonzero early exit and captured diagnostics instead of a generic timeout.
- Keep all private paths and diagnostics out of the public upload bundle.
- Request shutdown for orphan watchers belonging only to incomplete sessions that never wrote `session_manifest_private.json`; canonical active sessions are never auto-stopped.
- Bind final checkpoint verification to the same session token and reject stale or foreign manifests.

## Evidence boundary

The successful environment preflight is owner-machine evidence. This hotfix does not prove append continuity, campaign observation, battle observation, or SFO compatibility; those still require the uninterrupted live session.

## Authority

Repository workflow correction only. It issues no orders, changes no saves, and does not alter the active mod list.

## Offline validation target

- 73 SyntheticLab tests.
- 108 Runtime Probe tests.
- 181 total tests.
- 309 canonical repository files.
