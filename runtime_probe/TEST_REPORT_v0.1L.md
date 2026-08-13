# Runtime Probe and SyntheticLab test report — v0.1L

## Scope

Close the corrected Battle of Eilhart dense replay-calibration segment, preserve the direct-selection limiting result, convert the observed trace into reusable public-safe reality slices, and add a deterministic no-order tactical shadow evaluator.

## Test suites

- SyntheticLab: 24 tests
- Runtime Probe: 60 tests
- Total: 84 tests per complete repository validation

All tests passed. Two complete repository validations also passed with 172 canonical hashed files.

- validation run 1: 2.04 seconds, maximum RSS 114,700 KB;
- validation run 2: 1.90 seconds, maximum RSS 114,868 KB.

Measured standalone suite runs in the packaging environment:

- SyntheticLab: 0.58 seconds, maximum RSS 115,012 KB;
- Runtime Probe: 0.63 seconds, maximum RSS 115,048 KB.

## New SyntheticLab coverage

- dense Battle 4 corpus validates with stable identities and valid time-series coverage;
- visibility-safe trace slices validate deterministically;
- foreign units are rejected unless marked visible to the local alliance;
- trace slices contain no replay, raw log, personal path, or private artifact;
- tactical trace benchmarks are deterministic and bound to the exact dense-corpus digest;
- the shadow evaluator is deterministic, authority `NO_ORDERS`, and evidence status `HYPOTHESIS`;
- the crisis and termination postures produce explicit preservation priorities;
- smoke output now includes sparse Tier 4R regressions, dense Tier 4R regressions, tactical trace benchmarks, and the shadow evaluator.

## Existing runtime coverage retained

The 60 Runtime Probe tests continue to cover:

- deterministic PFH5 pack construction and round-trip parsing;
- read-only campaign and battle source boundaries;
- observer replication and exact pack identity;
- isolated persistence roundtrip;
- campaign snapshot ordering and five-turn verification;
- region identity overlap reconciliation;
- field-army eligibility, common strength proxies, and garrison exclusion;
- append-only campaign/battle logging contracts;
- schema-1 identity churn reconciliation;
- schema-2 stable identity and hierarchy/static discovery ordering;
- sparse-sampling claim rejection;
- dense dual-clock sampling and selection-limiting-result verification;
- preserved dense-capture reprocessing without raw-log export;
- hidden-enemy leakage rejection;
- required versus optional capability failures.

## Deterministic derived outputs

- dense corpus result digest: `442e187638c4d2b3457910efdbb50d13f16fd27a8391e7ac9bd2d6aaed47c33d`;
- trace-slice corpus result digest: `ccb23dc2e24102b53c5833ecae9047ebfd449476cd0508aacd4ec0fd6dc56360`;
- tactical trace benchmark result digest: `b3364537be82cd96ef760db7c9e767fdd96a159f8ca87722a554779b87a8ca13`;
- offline shadow evaluator result digest: `1d5892cf47c900e1bbe1eeae09466a28500abd3a735e1f332776f42f82606742`;
- dense analysis result digest: `f37db53c05b152ac5c92bd93df87c1013940fe76c178d24f97501e1fc5f76874`.

## Deterministic probe build

Two independent four-pack builds were byte-identical.

| Pack | SHA-256 | Bytes |
|---|---|---:|
| `transcendence_battle_replay_probe.pack` | `6e3f8e7bbc7d66754a7fa764c802e2b5599d13e83820e0785cb85d738040f66d` | 40,708 |
| `transcendence_observer_probe.pack` | `0c1dd8940a697a2d840876f08092ba02f988170e90c5f77b6f934ac15c79f173` | 16,525 |
| `transcendence_persistence_probe.pack` | `71bf96e4fca54d16e323f5eef9766a6098c6ea4b9416b33aa012317d5f682bd2` | 3,456 |
| `transcendence_shadow_probe.pack` | `0714863e2081206aa7d0790ec14d7c3c3c7ae33eea416d72dba0d6a2ecd0a89e` | 68,448 |

- build result digest: `1d87b0d345a5994eb400be4d7c5cc9c6a816910ab2aef4f9539572c53af1916a`;
- build-manifest SHA-256: `37a6321b4234af19dd9aaff0501bcdc09b67631812be820d3d524a21dc560576`.

No generated `.pack`, replay, save, executable, private raw log, or personal path is included in the canonical repository.

## Gate result

- dense replay observation: `OBSERVED`;
- direct selected-unit replay callback: `LIMITING_RESULT`;
- bounded state-matching attribution: `INFERRED_NOT_ACKNOWLEDGED`;
- tactical shadow evaluator: `HYPOTHESIS`, `NO_ORDERS`.

No further Battle 4 replay is required for current calibration.
