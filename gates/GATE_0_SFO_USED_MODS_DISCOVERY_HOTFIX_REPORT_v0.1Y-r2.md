# Gate 0 — SFO `used_mods.txt` Discovery Hotfix v0.1Y-r2

## Result

The owner-machine launcher-state blocker is corrected offline. The live SFO continuity gate remains open.

## Preserved owner result

- v0.1Y-r1 repository installation passed 73 SyntheticLab tests, 90 Runtime Probe tests, 163 total tests, and 300 canonical hashes.
- The corrected wrapper built, validated, and installed `transcendence_shadow_probe.pack` successfully.
- After the owner enabled exactly SFO and the probe, preflight failed because `%APPDATA%\The Creative Assembly\Warhammer3\scripts\used_mods.txt` did not exist.
- WH3 was not launched; the runtime log was not cleared; the checkpoint watcher was not started.

## Root cause

The preparer encoded one legacy launcher location as universal. Current WH3 tooling may place `used_mods.txt` in the game root, while Steam/EOS/GDK AppData variants remain possible.

## Correction

- Discover game-root, Steam-AppData, EOS-AppData, and GDK-AppData candidates.
- Parse every existing file with the strict active-pack parser.
- Prefer the game-root copy only when all existing copies have the same semantic ordered pack list.
- Reject conflicting copies before log clearing or watcher startup.
- Record a public path-free source kind and keep the exact path private.

## Regression coverage

- game-root discovery with no AppData copy;
- legacy Steam-AppData fallback;
- identical-copy preference;
- conflicting-copy rejection;
- static removal of the hard-coded legacy path from the preparer.

## Remaining live condition

Install v0.1Y-r2 and rerun `runtime_probe\tools\prepare_sfo_combined_session.ps1`. No gameplay or launcher cleanup is required from the failed attempt.

## Offline validation

- 73 SyntheticLab tests passed.
- 95 Runtime Probe tests passed.
- 168 total tests passed.
- 303 canonical repository files validated.
- Full repository validation passed twice.
