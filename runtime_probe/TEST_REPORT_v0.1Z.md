# Runtime Probe / SyntheticLab Test Report v0.1Z-r1

## Target

SFO observed calibration, recovery hardening, deterministic evidence transport, and exact replay deep-dive preparation.

## Automated suites

- SyntheticLab: 76 tests.
- Runtime Probe: 124 tests.
- Total: 200 tests.

## New regression coverage

- current schema-2 battle markers count in checkpoint summaries;
- three independent campaign-return cycles pass continuity analysis;
- atomic control JSON is exact and nonzero;
- checkpoint manifest is authoritative when watcher status is malformed;
- preparation readiness can use the checkpoint manifest;
- path-free public ZIP output is deterministic and member-hash verified;
- zero-filled public members fail closed;
- recovered SFO baseline identity, metrics, authority, privacy, and digest are frozen;
- baseline metric or capability-promotion tampering fails closed;
- exact Ironman save and two-replay cohort hashes are bound;
- replay-probe aliases and exact two-pack SFO replay state are strict;
- dense replay verification accepts a supplied exact replay identity without weakening Battle 4 defaults;
- private replay evidence ZIP is deterministic and nonzero;
- replay prepare/run/rollback scripts remain read-only and invoke switch parameters in process;
- three-battle calibration digest, episode totals, battle type, and authority boundaries are frozen.

## Expected full validation result

`tools/validate.ps1` must report 322 canonical hashes and all 200 tests passing. The final installer is not sealed until the full repository validation passes twice and simulated install/rollback/unknown-file tests pass.


## v0.1Z-r1 owner-machine regression

- reproduces the Windows read-only-descriptor `fsync` failure contract;
- requires the descriptor supplied to `fsync` to accept a zero-length write;
- preserves deterministic archive identity and all completed ZIP verification checks.
