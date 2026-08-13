# Gate 0 — SFO Launch-Script Grammar Hotfix v0.1Y-r4

## Result

The owner-machine current `used_mods.txt` grammar blocker is corrected offline. The live SFO combined-session continuity gate remains open.

## Preserved owner result

- v0.1Y-r3 installed successfully with 73 SyntheticLab tests, 99 Runtime Probe tests, 172 total tests, and 305 canonical hashes.
- The launcher visibly showed only SFO and the Transcendence shadow probe enabled.
- A refresh launch reached the WH3 main menu and exited without loading a campaign.
- The refreshed game-root `used_mods.txt` began with an `add_working_directory` directive for Workshop item `2792731173`.
- Preflight rejected that line because the parser accepted only `mod` directives.
- No runtime log clearing, watcher startup, campaign load, save mutation, or gameplay capture occurred.

## Correction

- Accept `add_working_directory "<absolute Windows path>";`.
- Accept `mod "<filename>.pack";`.
- Validate but do not count working directories as active mods.
- Require absolute drive or UNC paths and reject `.`/`..` traversal.
- Reject duplicate working directories, unknown directives, unsafe/path-bearing pack names, duplicate packs, extra packs, and ambiguous SFO resolution.
- Trim and compare the human `READY` confirmation case-insensitively.

## Evidence boundary

This parser correction does not certify that SFO or the probe loaded. Final certification still requires exact installed hashes and observed campaign plus battle runtime markers.

## Authority

Repository workflow correction only. It does not issue orders, change saves, alter the launcher state, or make a runtime compatibility claim.

## Offline validation target

- 73 SyntheticLab tests.
- 104 Runtime Probe tests.
- 177 total tests.
- Full repository validation twice after ledger sealing.

## Smallest owner step

Install v0.1Y-r4 and rerun `runtime_probe\tools\prepare_sfo_combined_session.ps1`. The currently enabled SFO plus shadow-probe launcher state may remain unchanged.
