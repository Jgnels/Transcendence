# Gate 0 — SFO Observed Calibration and Recovery Hardening v0.1Z-r1

**Status:** CLOSED OFFLINE AGAINST RECOVERED OWNER EVIDENCE  
**Evidence class:** `OBSERVED` runtime facts + `CONTROL_OFFLINE` recovery/adjudication + `CONTROL_SYNTHETIC` regressions  
**Authority:** `NO_ORDERS`

## Purpose

Convert the recovered owner-machine SFO campaign into a frozen, privacy-safe calibration baseline; repair every collector defect exposed by that run; and prepare an exact two-replay deep-dive workflow without granting order authority.

## Frozen owner-machine baseline

The source session is bound to:

- WH3 executable SHA-256 `b7315fa718fd84e2e018e2c4df06600e9df0076156b474f148d9d558c939aa55`;
- SFO Workshop item `2792731173`, pack SHA-256 `ae20a0a08037aa3ebcbe7461d2589fc28dc15a5fe5d9ca4c0a9d0ff0a26da603`;
- read-only shadow probe SHA-256 `0714863e2081206aa7d0790ec14d7c3c3c7ae33eea416d72dba0d6a2ecd0a89e`;
- exact two-pack load order: SFO, then shadow probe;
- Karl Franz / Reikland, Legendary campaign, Very Hard battle, ironman, battle realism.

Observed scope:

- six consecutive local-faction turns;
- three completed ordinary land battles;
- a distinct campaign-runtime return after each battle;
- 130 append-only checkpoints ending at the exact 24,658,918-byte raw log;
- 698 detailed battle samples, 4,000 alliance aggregate records, 683 command events, 1,025 selection events, and 80 canonical unit records;
- no project order issue, unitcontroller creation, save mutation, active-mod-list mutation, or authority violation.

The raw log, checkpoints, saves, replays, personal paths, and Workshop assets remain excluded from the repository.

## Defects closed

1. **Schema-2 transition mismatch.** Campaign/battle continuity now recognizes current `TRANS_BATTLE|2` markers as well as historical schema 1.
2. **Zero-filled watcher status.** Control JSON uses a unique temporary file, flush, `fsync`, atomic replacement, and exact post-write verification.
3. **Redundant-status collector failure.** The checkpoint manifest and handshake token are authoritative; a missing or malformed status file is diagnostic only.
4. **Zero-filled PowerShell ZIP.** Public evidence transport uses a deterministic Python builder that rejects empty, all-zero, private-path, or hash-mismatched members and verifies the completed archive.
5. **Rollback SwitchParameter handoff.** SFO rollback invokes the underlying script in process with splatted switch values.
6. **Generic private ZIP duplication.** The SFO collector can suppress the generic raw-log ZIP and build only the verified path-free transport artifact.

## Replay deep-dive cohort

The next optional owner evidence is exactly two preserved campaign replays, each hash-bound to the same campaign session:

- `test1.replay` / Battle of Ubersreik / SHA-256 `e96c160ce8ca83463407d2008c676da1bcad2a0e0d2ec1f03b475097b4c4ea89`;
- `Auto-save(1).replay` / Battle of Marienburg / SHA-256 `844d2efc4434c18d09d5958fc5cf9c60bf21201d5ca2af2e254077666ba0c902`.

The deep dive is battle-only, read-only, exact-replay, exact-SFO, and exact-probe. It is intended to align visible formations, maneuver, collision, targeting, routing, pursuit, and decision windows with the recovered telemetry. It does not treat owner play as optimal policy and does not issue orders.

## Capability adjudication

Promoted to observed for the exact frozen environment:

- exact SFO environment identity;
- SFO campaign observation;
- SFO ordinary-land-battle observation;
- schema-2 dense battle time series;
- campaign → battle → campaign append continuity;
- selection-event observation;
- command-event observation, explicitly `OBSERVED_NOT_ACKNOWLEDGED`.

Still unobserved or unproven:

- order acknowledgement;
- causal order execution;
- tactical superiority;
- siege, ambush, reinforcement, and broad-faction coverage;
- full normal-mod-stack compatibility;
- generalization across later WH3/SFO builds.

## Gate closure criteria

- frozen observed fixture validates exact environment, metrics, authority, privacy, and digest;
- recovered three-battle calibration corpus validates exact aggregates and forbidden inferences;
- transition recovery passes three schema-2 cycles;
- checkpoint manifest remains authoritative when status is malformed;
- public and private ZIP builders are deterministic and reject zero-filled members;
- exact replay bindings and exact two-pack SFO replay state are regression-covered;
- full repository validation passes twice;
- installer, rollback, and unknown-file rejection pass on an exact v0.1Y-r5 base.


## Owner-machine installation correction — v0.1Z-r1

The first v0.1Z installer reached the new deterministic ZIP regression and failed on Windows because `os.fsync` was called on a read-only descriptor. The transaction failed closed and automatically restored all 309 canonical v0.1Y-r5 files. v0.1Z-r1 uses a writable durability descriptor, adds a direct descriptor-mode regression, and preserves the original gate scope and authority boundaries.
