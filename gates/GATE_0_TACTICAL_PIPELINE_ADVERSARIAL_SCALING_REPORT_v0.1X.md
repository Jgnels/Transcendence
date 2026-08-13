# Gate 0 Report — v0.1X Tactical Pipeline Adversarial and Scaling Audit

## Gate decision

**Closed offline.**

The complete v0.1N–v0.1W tactical pipeline passes deterministic adversarial, representation-invariance, authority, and structural-scale checks.

## Results

- 256/256 full-pipeline cases passed;
- 12/12 scale cases passed;
- 289 guarded packets processed;
- 867 candidate points processed;
- 102 endpoint reservations produced in synthetic true-evidence cases;
- maximum normal-case exact-search work: 9 nodes;
- structural scaling reached 160 ready packets;
- authority remained `NO_ORDERS` and application authority `PROHIBITED`.

## Defects found and corrected

### Duplicate plan identity collapse

Before correction, a forged feasibility envelope could append a duplicate valid plan record and survive source comparison because dictionary conversion collapsed the duplicate key.

Correction: validate plan-list type, unique identities, exact cardinality, envelope counts, and candidate counts before canonical shape comparison.

### Coordinate-hash optimization tie-break

Before correction, equal-weight reservation solutions used candidate hashes containing coordinates. A uniform battlefield translation could change the chosen equal solution.

Correction: optimization tie-breaking now uses stable packet identity and canonical candidate rank. The preserved fixture demonstrates that the legacy signature changes under translation and the corrected semantic output does not.

### Guarded identity attacks

The audit additionally samples forged guarded packet IDs and duplicate actor identities. Both fail closed under canonical packet-source binding and one-packet-per-actor validation.

## Exact evidence

- Audit report SHA-256: `8c40e9a13ad1c3e6a1f966d10c068c19da87b265beecdd1beb3f67bd6dd79bac`.
- Audit result digest: `6297bc4b3962a5a104231f79996da8c64866133a2a88ffac985cc5be25bd9de0`.
- Suite SHA-256: `23d5f68e76b5a3d9df10027741a617f8e46386390a2e59e59c425be11fe8ed88`.
- Suite result digest: `81e676c5ebb526d0a654d16b8e34352bf8a11fe35e777bf31d7508e3308aacf1`.
- Seed: `20260730`.

## Interpretation

Passing establishes deterministic offline contract robustness and bounded structural scaling. It does not establish WH3 timing, route or formation feasibility, command legality, acknowledgement, execution, casualty reduction, tactical superiority, SFO compatibility, or broad battle generalization.

## Final repository validation

- 73 SyntheticLab tests passed;
- 81 Runtime Probe tests passed;
- 154 total tests passed;
- 286 canonical repository files are hash-bound;
- all v0.1U–v0.1X generated artifacts reproduced byte-for-byte;
- the cumulative release is based on exact owner-validated v0.1T and requires no gameplay run.
