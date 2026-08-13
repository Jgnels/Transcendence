# Gate 0 Persistence Closure and Shadow Preparation v0.1G

**Date:** 2026-07-29

## Closed

### Disposable-save persistence

Status: `REPLICATED`

- exact pack SHA-256: `71bf96e4fca54d16e323f5eef9766a6098c6ea4b9416b33aa012317d5f682bd2`;
- fresh write: `0 → 1`;
- same-save reload: `1 → 2`;
- same campaign, faction, key version, and single-player environment;
- isolated persistence-only sessions;
- clean loader entrypoint;
- verifier semantic digest: `b996cc93f07275bc8d36fa428baa5e055ee03ba19bebc113175beedf048198bb`.

### Offline shadow-input preparation

Status: closed offline.

- separate read-only pack;
- deterministic PFH5 build;
- no save write, order, mutation, or randomness path;
- controlled-army strength/movement/readiness candidates;
- owned-region siege/garrison candidates;
- explicit war pairs;
- WH3-filtered foreign entity boundary;
- conservative foreign strength/garrison proxies;
- deterministic runtime-log-to-proposal pipeline;
- `SHADOW_NO_ORDERS`.

Shadow pack SHA-256:

`2cb66df8850d1953f42686a52d6338b62addc2a9e347d4844aba32e74dd343ae`

## Defect corrected

The persistence verifier result digest changed when the same evidence was uploaded under different filenames. v0.1G adds a semantic projection that excludes filenames and derived digests but retains evidence hashes, timestamps, collection IDs, states, pack identity, checks, and warnings.

## Tests

- 18 SyntheticLab tests passed twice;
- 25 runtime tests passed twice;
- 43 tests total per repetition;
- two pack builds byte-identical;
- two shadow fixture pipelines byte-identical;
- two persistence re-verifications byte-identical.

See `runtime_probe/TEST_REPORT_v0.1G.md`.

## Capability promotions

- namespaced project integer save/reload: `CONTROL`, evidence `REPLICATED`;
- exact two-phase persistence verifier: `CONTROL`;
- shadow input conversion and objective proposal: `CONTROL` offline, evidence `SUPPORTED`;
- expanded WH3 runtime fields: remain `UNVERIFIED`;
- campaign order authority: remains `UNVERIFIED`.

## Gate state

Gate 0 overall remains open. The next unavoidable live step is one pure-vanilla run of the exact v0.1G shadow pack, collection of the canonical local-turn snapshot, and review of the generated orderless proposal.
