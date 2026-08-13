# Gate 0 Report — v0.1Y SFO Combined Session Preparation and Checkpointing

## Gate decision

**Offline preparation gate closed. Live SFO continuity gate open.**

The repository now contains a fail-closed, one-session workflow for exact SFO environment identity, campaign/battle append-log checkpointing, privacy-safe collection, and continuity adjudication.

## Implemented

- exact SFO Workshop pack, WH3 executable, probe pack, active-mod order, and owner-settings capture;
- exact-two-pack SFO certification profile;
- append-only full-file checkpoints with prefix-chain validation;
- campaign → battle → campaign transition analysis;
- five-turn/two-battle minimum verification;
- path-free public export with private raw/checkpoint preservation;
- batched prepare, collect, and rollback PowerShell workflows;
- deterministic control fixture and frozen preparation artifact.

## Defects found and corrected

### Current battle probe identifier mismatch

The combined collector recognized historical `battle_shadow`, while the current probe emits `battle_replay_shadow`. Existing historical fixtures masked the live mismatch.

Correction: accept both identifiers for compatibility and regression-test the current emitted marker.

### Private materials in the legacy generic upload bundle

The older combined collector's generic ZIP includes the raw append log and path-bearing private session material.

Correction: the SFO wrapper preserves those files locally, exports a new path-free bundle, and removes only the newly generated generic ZIP.

### No recoverable append-continuity chain

Append mode was covered by source and fixture tests, but an uninterrupted owner session could still fail without intermediate recoverability or proof that the file never truncated.

Correction: a separate watcher creates hash-bound prefix checkpoints and reports any truncation or divergence.

### One late campaign return could satisfy multiple battles

The first transition verifier accepted any later campaign runtime as the return for each preceding battle. Two completed battles followed by one final campaign runtime could therefore be misclassified as two valid returns.

Correction: every battle completion now requires a campaign runtime before the next battle begins, or after the final battle. A preserved negative fixture fails closed.

### SFO identity was not bound to the session

The prior workflow did not certify the exact full SFO pack, WH3 executable, active two-pack load order, or owner settings.

Correction: strict owner-machine preflight and public attestation. No live SFO compatibility claim is promoted before collection.

## Deterministic control evidence

- fixture SHA-256: `e94117b090cbc234ab433352ae03540d81cd5a0de71d0c6e9910ac6f7cecb062`;
- preparation result digest: `2723d63682e16234e91df781b90b386f9ad4d85893a7f5946ba7c76532c67efe`;
- six checkpoint prefixes;
- five campaign turn snapshots;
- two battle runtime starts and completions;
- campaign return after both battles;
- current `battle_replay_shadow` marker present;
- no orders, save writes, or active-mod-list edits.

## Live condition still open

One exact owner-machine session must pass with SFO plus the read-only shadow probe, at least five local turn starts, two manually fought campaign battles, and a return to campaign after each battle. No save-and-quit cycle is required between battles.
