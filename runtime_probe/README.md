## v0.2I-r2 campaign feasibility parser-contract hotfix

The r1 real/UI timer is retained unchanged. The second owner-runtime attempt observed `FEASIBILITY_POLL_TICK`, then the local sidecar failed because the shared parser did not allow that new event. r2 updates the parser vocabulary, supports `campaign_feasibility` session summaries, adds a static emitted-event→parser allowlist regression. The dedicated game-side pack remains byte-identical to r1.

# Runtime Probe v0.1Z-r1

## v0.2I-r1 campaign feasibility timer hotfix

The dedicated campaign-feasibility executor now polls its asynchronous request with an immediate call plus `cm:repeat_real_callback(..., 250, ...)`. Do not revert this to `repeat_callback`: the first owner-runtime run showed that the campaign can remain idle after `FEASIBILITY_EXECUTOR_READY` while the external sidecar has already written the request. One-shot `FEASIBILITY_POLL_TICK` and `FEASIBILITY_REQUEST_SEEN` events distinguish timer progress from request-file or query-surface failures. The probe remains read-only and contains no campaign order/mutation adapter.

## Campaign feasibility live observation v0.2I

`transcendence_campaign_feasibility_probe.pack` is a dedicated campaign-only, read-only observation pack. It emits one first-tick observer-safe campaign snapshot and then polls a relative request file for at most 16 exact v0.2H query IDs produced by the local canonical sidecar. The Lua executor has a hard-coded whitelist; it cannot dispatch arbitrary campaign calls.

Prepare a session with:

```powershell
.\runtime_probe\tools\prepare_campaign_feasibility_observation.ps1
```

After the script asks for launcher state, enable exactly SFO: Grimhammer III and `transcendence_campaign_feasibility_probe.pack`, close the launcher, and type `READY`. Then load a current SFO campaign and remain on the campaign map long enough for the packet to complete. No turn advance, battle, army order, or save is required by the protocol.

After exiting WH3, collect with:

```powershell
.\runtime_probe\tools\collect_campaign_feasibility_observation.ps1
```

The collector accepts results only if the raw snapshot independently reproduces the exact sidecar plan and query identity/cardinality. The public ZIP excludes the raw log and personal paths. All results remain `NO_ORDERS` / application `PROHIBITED`; a true reachability query is not a route, legal action, acknowledgement, execution, or outcome.

## v0.1Z-r1 recovered SFO baseline and replay deep dive

The recovered owner session proves exact SFO campaign/battle append continuity across six turns and three completed ordinary land battles. The checkpoint manifest is authoritative; watcher status is diagnostic. Public exports use the deterministic verified Python builder and reject empty, zero-filled, private-path, or hash-mismatched members.

The exact replay cohort is prepared through `prepare_sfo_replay_deep_dive.ps1`, `run_sfo_replay_deep_dive.ps1`, and `rollback_sfo_replay_deep_dive.ps1`. It permits only SFO plus the read-only battle replay probe, exact replay hashes, no orders, and private deterministic telemetry transport.


Runtime Probe advances WH3-backed Reality Gate R0 without granting Transcendence campaign- or battle-order authority.

## Frozen proven packs

### Observer

`transcendence_observer_probe.pack`

`0c1dd8940a697a2d840876f08092ba02f988170e90c5f77b6f934ac15c79f173`

Strictly replicated in two independent pure-vanilla Karl Franz sessions.

### Persistence

`transcendence_persistence_probe.pack`

`71bf96e4fca54d16e323f5eef9766a6098c6ea4b9416b33aa012317d5f682bd2`

One disposable campaign proved `WRITE 0→1` then same-save `RELOAD 1→2`.

### Dense replay calibration

`transcendence_battle_replay_probe.pack`

`6e3f8e7bbc7d66754a7fa764c802e2b5599d13e83820e0785cb85d738040f66d`

The corrected pack completed the exact Battle of Eilhart replay and produced:

- 249 detailed samples against 247 expected;
- 1,477 one-second alliance aggregates;
- 120 sampler heartbeats;
- a 3.4-second maximum detailed-sample gap;
- 37 stable canonical units with zero identity aliases;
- all 397 replay command events;
- a complete 739.6-second result;
- no orders, unitcontrollers, speed changes, save writes, or visibility mutation.

Dense observation is `OBSERVED_DENSE_SELECTION_LIMITING_RESULT`. Direct per-unit selection callbacks emitted no replay events. Bounded state matching produced 302 candidate attributions, 121 high-confidence, but every result remains `INFERRED_NOT_ACKNOWLEDGED`.

No additional Battle 4 playback is required for current observation or SyntheticLab calibration.

## Dedicated replay probe scope

The battle-only pack records stable identity, hierarchy changes, army context, unit trajectories, targets, movement, melee and missile pressure, morale, routing, fatigue, ammunition, flank threats, ability ownership, aggregate force curves, callback health, command traffic, and terminal coverage.

The pack has no unitcontroller, order, speed, save, damage, healing, ammunition, visibility, or randomness path. It remains available as a frozen calibration instrument, not as a gameplay mod.

## Build and stage

```powershell
.\runtime_probe\tools\prepare_live_probe.ps1
```

This builds into ignored local output and does not modify WH3. Installation remains explicit and opt-in.

## SyntheticLab Tier 4R

Public-safe derived corpora under `synthetic_lab/corpora/` preserve the dense timeline and eight visibility-filtered state slices. They contain no replay binary, raw log, personal path, or proprietary asset.

## Cross-runtime logging

Campaign and battle scripts append structured records to:

```text
transcendence_runtime_log.txt
```

`lua_mod_log.txt` remains only a secondary loader diagnostic because WH3 truncates it when a new Lua runtime first writes. Live campaign → battle → campaign append continuity remains an open condition for a later broad campaign session.

## Rollback

```powershell
.\runtime_probe\tools\rollback_live_probe.ps1
```

Live rollback proof remains pending.

## Action-authority probe v0.1R

`transcendence_action_authority_probe.pack` is a battle-only, read-only instrument. It observes local selection, game command callbacks, five-second state windows, point reachability, ordered position, current target, movement, withdrawal, routing, shattering, and control loss. It never creates a unitcontroller or issues an order.

Prepare and later collect one batched ordinary-battle session:

```powershell
.\runtime_probe\tools\prepare_action_authority_capture.ps1
.\runtime_probe\tools\collect_action_authority_capture.ps1
.\runtime_probe\tools\rollback_action_authority_probe.ps1
```

The first command explicitly installs but does not enable the pack or modify the active mod list. The second creates one public-safe ZIP without the raw log or personal paths.


## Observed action-authority capture v0.1S

The first ordinary-battle capture passed exact-pack verification: 89/89 command windows were selection-bound and produced 1,287 read-only samples. Raw callback-position reachability returned both true and false. v0.1U later established that only explicit Move points were semantically qualified: 191 true and zero valid false samples; all 38 raw false samples came from a zero-vector formation callback. All project issue and direct acknowledgement counts remain zero.

Adjudicate a future public-safe ZIP offline:

```powershell
python .\runtime_probe\tools\adjudicate_action_authority_export.py `
  <Transcendence_ActionAuthorityCapture.zip>
```

Future collector exports use public manifest schema 2 and include `public_preparation_attestation.json`, a path-free record of exact pack identity and nonmutation flags. Raw logs and private prepared manifests remain local-only.

## Detailed action-feasibility re-export v0.1T

The exact v0.1S private raw log can be converted into richer public-safe command windows without replaying or launching WH3:

```powershell
.\runtime_probe\tools\reexport_action_feasibility_capture.ps1
```

The workflow locates the raw log by exact SHA-256, verifies the exact action-authority pack and prepared-session nonmutation flags, and writes `Transcendence_ActionFeasibilityWindows_<timestamp>.zip` beneath the private exports directory. The ZIP contains no raw lines, personal paths, project issue attempts, or acknowledgements. Verify a packet with:

```powershell
python .\runtime_probe\tools\verify_action_feasibility_reexport.py `
  <Transcendence_ActionFeasibilityWindows.zip>
```


## Semantic action-feasibility adjudication v0.1U

Adjudicate the exact detailed re-export with:

```powershell
python .\runtime_probe\tools\adjudicate_action_feasibility_semantics.py `
  <Transcendence_ActionFeasibilityWindows.zip>
```

The adjudicator preserves raw query totals but qualifies exact-point evidence only for explicit finite nonzero `Move` callbacks. Unit-target and opaque command callbacks remain state evidence and their zero-vector query results are not point-feasibility evidence.

## SFO combined campaign+battle session v0.1Y

Prepare one exact SFO-only plus read-only shadow-probe session:

```powershell
.\runtime_probe\tools\prepare_sfo_combined_session.ps1
```

The preflight requires exactly SFO and `transcendence_shadow_probe.pack` active. It records exact pack, executable, load-order, and settings identities, clears the old project log, and starts an append-prefix checkpoint watcher.

v0.1Y-r1 invokes the shared probe installer directly in the current Windows PowerShell process. This preserves the `Confirm = $false` Boolean binding and avoids the string-to-`SwitchParameter` failure produced by a child `powershell.exe -File` boundary.

Use one WH3 process. Play through at least five local turn starts and manually fight two campaign battles. Return fully to campaign after each battle; do not save and quit merely for data collection. After exiting WH3 once, run:

```powershell
.\runtime_probe\tools\collect_sfo_combined_session.ps1
.\runtime_probe\tools\rollback_sfo_combined_session.ps1 -RemoveProbePack -Force
```

Upload only `Transcendence_SFO_CombinedSession_<timestamp>.zip`. Raw logs, checkpoints, and path-bearing manifests remain local.

## SFO launcher-state discovery hotfix v0.1Y-r2

The SFO preparer no longer assumes that the active mod list exists only beneath the legacy Steam AppData scripts directory. It searches, in deterministic priority order:

1. `<WH3 game root>\used_mods.txt`;
2. Steam AppData scripts;
3. EOS AppData scripts;
4. GDK AppData scripts.

Every existing candidate is parsed with the strict two-pack load-order parser. If copies disagree, preparation fails before clearing the append log or starting the checkpoint watcher. If they agree, the game-root copy is preferred and the public environment profile records only `used_mods_source_kind`, never the personal path.



## v0.1Y-r3 prelaunch probe binding

The SFO preparer no longer assumes that a local probe must appear with one exact literal filename before WH3 starts. It supports:

- exact `transcendence_shadow_probe.pack`;
- a single safe load-order-decorated alias using `@`, `!`, or `~`;
- SFO-only prelaunch materialization with `DEFERRED_RUNTIME_MARKER`.

Deferred status is not certification. The final verifier requires the exact prepared/installed probe SHA-256 and observed shadow campaign plus battle runtime markers. Extra mods, duplicate aliases, mismatched hashes, and absent runtime markers remain hard failures.


## v0.1Y-r4 current WH3 used_mods grammar

The active-mod parser accepts the exact guarded launch-script subset observed on the owner machine:

```text
add_working_directory "C:/absolute/path";
mod "pack_name.pack";
```

`add_working_directory` paths are validated as absolute and traversal-free, then excluded from the active pack list. Unknown commands, relative paths, traversal, duplicate directories, duplicate pack entries, path-bearing pack names, and non-`.pack` entries fail closed. The launcher confirmation accepts trimmed case variants of `READY`; all artifact and runtime identities remain exact.

## v0.1Y-r5 watcher startup

`prepare_sfo_combined_session.ps1` binds the detached checkpoint watcher to a random session token. This avoids false startup failures when `python`, `py.exe`, an app-execution alias, or another shim launches the long-lived interpreter under a different PID. Private stdout/stderr are retained beneath the session directory for exact failure diagnosis.

The preparer also requests shutdown for read-only watchers from incomplete historical SFO preparation directories that never reached a private session manifest. Valid prepared sessions are excluded from this cleanup.


## v0.1Z-r1 Windows ZIP durability repair

The deterministic public evidence builder performs `fsync` through an `r+b` descriptor. This is a durability-only reopen; archive bytes are not modified. Windows rejects the prior read-only descriptor with `EBADF`, so the writable-descriptor property is now directly regression-tested.

## v0.2R offline native-behavior Replay Lab

`native_behavior_replay.py` verifies and deterministically replays public native-diagnostic capture ZIPs without changing either game-side Lua probe. It validates member hashes/provenance, refuses incomplete or battle-telemetry-ambiguous captures for frozen metric replay, reconstructs per-force longitudinal timelines, reuses the frozen v0.2N/v0.2P evaluators, and emits deterministic JSON/CSV/Markdown outputs.

Use the thin Windows wrapper:

```powershell
.\runtime_probe\tools\Replay-NativeBehavior.ps1 replay <capture.zip> --output-dir <directory>
```

For vanilla↔SFO comparison:

```powershell
.\runtime_probe\tools\Replay-NativeBehavior.ps1 compare --vanilla <vanilla.zip> --sfo <sfo.zip> --output-dir <directory>
```

Only a capture explicitly identified as the v0.2Q Stage-A SFO replication should use `--sfo-role stage-a`. Replay Lab is research-only: `NO_ORDERS`, application authority `PROHIBITED`, privileged telemetry permanently application-ineligible.
