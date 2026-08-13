# Gate 0 Live-Probe Preparation Report — v0.1C

## Segment result

**Closed:** the first live observation package is fully prepared, deterministic, rollback-bounded, and offline-tested.

**Gate 0 remains open:** the pack has not yet been installed, enabled, loaded, or observed inside the owner's WH3 installation.

## Implemented

- deterministic script-only PFH5 Mod pack writer;
- separate read-only campaign observer pack;
- separate opt-in save/reload persistence pack;
- observer-safe local and game-filtered foreign observation boundary;
- bounded structured log schema;
- adversarial log parser and capability-promotion report;
- stage/install scripts with explicit confirmation and no active-mod-list edits;
- private evidence collector and hasher;
- hash-guarded rollback with pre-existing-file restoration;
- repository validation integration.

## Defects found and corrected

1. Build outputs under ignored `dist/` would still be scanned by the repository validator and rejected as forbidden pack binaries. The validator now ignores all declared build-output roots.
2. A combined observer/persistence pack would make a supposedly read-only test write to saves. The functions were separated into independent packs.
3. A complete-world scan followed by project-side filtering could leak hidden information. The probe instead calls the game's player-visibility-filtered faction interfaces.
4. Free-form logs could carry personal paths or malformed state. The parser rejects prohibited fields, bad ordering, unknown events, and malformed snapshots.
5. Reinstall/rollback could overwrite unrelated files. Installation records exact hashes and rollback refuses to remove changed files without explicit force.

## Remaining live conditions

- owner installs and manually enables only the observer pack;
- WH3 produces `lua_mod_log.txt` records;
- collector parses the real log without capability errors;
- observer result is repeated once;
- persistence pack is tested only on a disposable save;
- resulting private/sanitized evidence is reviewed and canonical capability labels are updated.

## Smallest unavoidable next task

Run `runtime_probe/tools/prepare_live_probe.ps1 -InstallObserver`, enable the observer pack in the launcher, load a fresh vanilla Karl Franz campaign to the first turn, exit, then run `runtime_probe/tools/collect_probe_logs.ps1`.
