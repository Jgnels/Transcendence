# Gate 0 — Action Authority and Feasibility Preparation Report v0.1R

## Decision

**Offline preparation gate: CLOSED.**  
**Live observation gate: OPEN.**  
**Authority: `NO_ORDERS`.**

## What closed

- strict `TACTICAL_ACTION_AUTHORITY_EVIDENCE_PACKET_V1` offline packet;
- 12-scenario action-authority matrix;
- Battle 4 boundary report preserving 397 observed command events, zero direct selection attribution, 302 inferred candidates, and zero issue/acknowledgement/reachability evidence;
- project-authored read-only `TRANS_ACTION` schema-1 battle probe;
- deterministic PFH5 action-authority pack;
- strict parser and exact-pack capture verifier;
- one-command prepare and one-command collect workflows;
- public-safe packet template and raw-log exclusion;
- primary-source action-authority API audit.

## Defects prevented

1. Game command callbacks are not accepted as project issue attempts.
2. Selection/state matching is not accepted as direct acknowledgement.
3. Movement, target, ordered-position, or leaving state is not credited as project-caused execution.
4. Point-in-time reachability is not treated as path completion.
5. Hidden target identity, foreign local-unit records, multiplayer capture, malformed ordering, stale logs, and pack mismatch fail closed.
6. Public exports exclude raw logs, machine paths, mod-list paths, and game installation paths.

## Deterministic evidence

- Matrix seed: `20260730`.
- Matrix: 12/12 passed.
- Battle 4 boundary: 397 command events; 0 direct selection-attributed; 302 `INFERRED_NOT_ACKNOWLEDGED`; 0 reachability queries; 0 project issue attempts; 0 direct acknowledgements.
- Action-authority pack SHA-256: `3acf60520b60f87f8c18e13532512324cb7a539626996ce19897fad94cf2d25d`.
- Five-pack build result digest: `8342c70f6e8712c5c0e768d6d7f2c0072659c1b7fcb0fa406664f83c22dd816e`.
- Build manifest SHA-256: `d297f798c798eefed48b0f70912370d0e47d12fa19f37034f3711f57acb932f6`.

## Validation

- SyntheticLab: 56 passed.
- Runtime Probe: 68 passed.
- Total: 124 passed.
- Canonical repository hashes: 231 validated.
- Matrix report result digest: `3c9d5e9cbb6ccf0d8c2e8868827df5b4c1172b821573e25345f99195c24fb61d`.
- Battle 4 boundary result digest: `96f72f77206b783d1e2c1e9ad60af4ffc233ff567bff4283ac2a40ee238f1672`.
- Capture-template result digest: `2a0eba9ce4c9bb176bb3ca0e8247d01db7dba769e721ada243e92946a034cde2`.
- Fixture-verification result digest: `691d19f127e5e24a895651cd7d606a0d3be025d23a2b9fcba8bbbcdad2f1a4b2`.
- Canonical file count: 231. The release ledger SHA-256 is reported with the sealed installer artifact.

## Remaining live condition

One ordinary single-player battle must be captured with the exact pack after owner installation. The run is observational only. It may promote ordinary-battle selection binding, state-window sampling, reachability-query availability, and interruption visibility to `OBSERVED`; it cannot promote project issue, acknowledgement, causal execution, or outcome.
