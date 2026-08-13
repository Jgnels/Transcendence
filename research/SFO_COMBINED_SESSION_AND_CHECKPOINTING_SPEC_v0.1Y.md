# SFO Combined Session and Checkpointing Specification v0.1Y

## Purpose

Prepare one exact owner-machine SFO campaign-and-battle observation session that can test campaign → battle → campaign continuity without requiring WH3 to be saved and closed after each battle.

## Environment contract

The preflight records and hash-binds:

- `Warhammer3.exe` identity;
- SFO Workshop item `2792731173` and the exact active SFO pack file;
- the exact deterministic Transcendence shadow-probe pack;
- active load order from `used_mods.txt`;
- campaign and battle difficulty, ironman, battle-realism/battlefield-limitation setting, and faction;
- exactly two active packs: SFO plus the read-only Transcendence probe.

Additional active mods fail closed for this certification cohort. This does not change the owner's normal mod stack or assert that SFO is generally incompatible with other mods.

## Append-continuity contract

Campaign and battle runtimes append to `transcendence_runtime_log.txt`. A separate read-only watcher:

- takes a first-observation checkpoint;
- takes checkpoints after runtime-marker changes, bounded time intervals, or bounded log growth;
- verifies each captured file is a byte prefix of the next;
- records sizes, SHA-256 identities, marker counts, and transition order;
- fails on truncation or prefix divergence;
- takes a final checkpoint before collection.

The required live sequence is:

`campaign → battle complete → campaign → battle complete → campaign`

with at least five local-faction turn-start snapshots and two manually fought campaign battles. The owner should return fully to the campaign after each battle but does not need to save, exit, or relaunch WH3 between battles.

## Privacy and authority

The raw append log, full checkpoints, and path-bearing session manifest remain beneath `local_inputs/`. The public export contains only path-free, hash-bound summaries, reports, the SFO environment attestation, verification result, and export manifest.

The workflow emits no campaign or battle orders, writes no save values, and does not modify the active mod list. Probe installation and launcher enablement remain explicit owner actions.

## Evidence boundary

A passing live session may establish scoped observation and compatibility for one exact WH3 executable, SFO pack, load order, settings profile, faction, and observed battle types. It does not establish tactical superiority, command acknowledgement, route completion, broad SFO compatibility, or compatibility with the owner's full mod stack.

## v0.1Y-r5 watcher startup amendment

Watcher readiness is identified by a 256-bit per-session handshake token, not equality between the PID returned by PowerShell `Start-Process` and Python `os.getpid()`. The private status and checkpoint manifest use schema 2 and publish the token plus the actual watcher PID. PowerShell preserves the launcher PID separately, captures private stdout/stderr, and reports nonzero early exit. No watcher diagnostics are exported publicly.

### Incomplete-session cleanup

Before creating a new session, preparation requests shutdown for watcher processes associated with prior `sfo_combined_*` directories only when no canonical private session manifest exists. This handles a possible child interpreter left by the historical PID-equality failure without terminating a valid prepared capture.
