# Gate 0 Tactical Priority Portfolio and Baseline Matrix Report — v0.1O

## Decision

**Offline heterogeneous tactical portfolio segment: CLOSED.**

v0.1O preserves all v0.1N authority boundaries while adding bounded critical-priority batching and a 16-scenario synthetic baseline matrix.

## Canonical base

- Owner-validated release: `v0.1N Tactical Contract Hardening`.
- Owner-machine result: 37 SyntheticLab tests, 61 Runtime Probe tests, 98 total tests, 24 adversarial cases, and 184 canonical hashes.
- Public repository head remains `16c4fa0d5290822a9fcba150b4dffcc8152f1b52`; remote state was not modified.
- v0.1M and v0.1N evidence artifacts remain frozen.

## Defect found and corrected

### F-O001 — bounded selector silently starved critical concern classes

**Classification:** `CONTROL_OFFLINE` portfolio-arbitration defect.

The legacy selector applied the six-item budget directly to per-unit opportunity instances. Under eight simultaneous critical unit failures it selected six instances but represented only four concern types, covering 66.6667% of critical sources. With a fresh reserve creating seven distinct critical groups, coverage fell to 60%.

**Correction:** `TACTICAL_PRIORITY_PORTFOLIO_V1` groups equivalent unit concerns before applying the six-priority limit. Six critical groups fit directly. Seven groups use five direct priorities plus one explicit critical-overflow record. Both stress fixtures preserve 100% critical source-opportunity coverage.

The overflow is not an executable plan. It preserves awareness for a later assignment and sequencing layer.

## Battle 4 portfolio result

- source candidate opportunities: 44;
- grouped priorities: 25;
- selected priorities across eight slices: 23;
- maximum selected in one slice: 6;
- minimum critical source coverage: 1.0;
- critical-overflow slices: 0;
- result digest: `2650af7860758b542308039412ff32032f69da58966b41a4c0d9afa7744b3eb0`;
- file SHA-256: `5109e676a816133524c2c60f6c65da898384228ac598aefe71bf97b81a472332`.

## Heterogeneous matrix result

- scenarios: 16;
- state-contract passes: 16/16;
- role-aware portfolio passes: 16/16;
- required-intent recall: 1.0;
- forbidden-intent safety: 1.0;
- scale-equivalence checks: 1/1;
- all outputs: `NO_ORDERS`;
- matrix result digest: `65835d6bceb1cd7bb5e1944f8a923f3cfed720a322695960677c8d2b3fbd7435`;
- matrix file SHA-256: `1440e93f7aab3e1d385625f0fcff0674985c07b2fce7a5aedec80e2711a77afe`.

Baseline contract-pass counts:

| Policy | Passes | Required-intent recall | Forbidden-intent safety |
|---|---:|---:|---:|
| `ROLE_AWARE_PORTFOLIO_V1` | 16/16 | 1.0 | 1.0 |
| `LEGACY_ROLE_AWARE_V2` | 14/16 | 0.9 | 1.0 |
| `UNIFORM_DANGER_045` | 1/16 | 0.333333 | 0.964286 |
| `PRESERVATION_ONLY_035` | 2/16 | 0.466667 | 0.892857 |
| `PRESSURE_ONLY` | 2/16 | 0.033333 | 0.892857 |
| `PASSIVE_HOLD` | 2/16 | 0.0 | 1.0 |

These are synthetic contract-alignment measurements, not evidence of battle outcomes or tactical superiority.

## Validation

- SyntheticLab: 41 tests passed.
- Runtime Probe: 61 tests passed.
- Total: 102 tests passed.
- Deterministic artifacts rebuilt twice with identical bytes.
- Canonical repository hash count and final manifest digest are recorded by the release installer.

## Claims

Promoted:

- critical opportunity grouping and explicit overflow are `CONTROL_OFFLINE`;
- shared strict validation applies to observed and synthetic tactical slices without changing evidence labels;
- the 16-scenario matrix and one unit-scale equivalence pair are deterministic;
- the role-aware portfolio satisfies all current synthetic fixture contracts;
- baseline disagreement is measurable without issuing orders.

Rejected:

- a six-instance cap always preserves critical concern coverage;
- synthetic contract wins establish tactical superiority;
- an overflow record is an executable assignment or order sequence.

Still unverified:

- tactical-quality improvement and causal casualty reduction;
- pathfinding and formation feasibility;
- live command authority and acknowledgement;
- ordinary-live, SFO, siege, ambush, reinforcement, other-faction, monster/flying, and unit-scale generalization beyond the preserved equivalence pair.

## Authority and safety

`NO_ORDERS`. No WH3 installation, game file, save, Workshop content, active mod list, runtime behavior, or remote GitHub state was modified.

## Smallest next step

Continue offline with explicit unit-to-objective assignment, incompatibility constraints, and sequence-independent portfolio validation. Defer live order authority until a separate generated/ordinary-battle capability probe can distinguish issue, acceptance, acknowledgement, execution, and outcome.
