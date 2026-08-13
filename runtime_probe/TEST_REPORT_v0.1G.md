# Runtime Probe Test Report v0.1G

**Date:** 2026-07-29  
**Result:** PASS

## Scope

- integrate real disposable-save persistence evidence;
- add filename-invariant persistence semantic digests;
- preserve the replicated observer and persistence pack hashes;
- add a separate read-only shadow-input pack;
- add deterministic shadow-log conversion and Army Objective Assignment;
- preserve hidden-information, no-order, and no-save-mutation boundaries.

## Tests

Two complete offline repetitions were run.

| Suite/operation | Count or result | Run 1 | Run 2 |
|---|---:|---:|---:|
| SyntheticLab tests | 18 passed | 0.65 s / 111,212 KB | 0.60 s / 110,844 KB |
| Runtime-probe tests | 25 passed | 0.60 s / 110,852 KB | 0.57 s / 110,768 KB |
| Probe pack build | byte-identical | 0.53 s / 110,264 KB | 0.57 s / 110,164 KB |
| Shadow fixture pipeline | byte-identical | 0.57 s / 110,984 KB | 0.56 s / 111,016 KB |
| Live persistence evidence re-verification | byte-identical | 0.55 s / 110,584 KB | 0.55 s / 110,544 KB |

Total automated tests per repetition: **43**.

The complete repository validator also passed twice:

| Validation | Run 1 | Run 2 |
|---|---:|---:|
| 106-file hash/JSON/safety check plus both test suites | 1.66 s / 112,408 KB | 1.62 s / 110,888 KB |


## Deterministic pack outputs

| Pack | SHA-256 |
|---|---|
| observer | `0c1dd8940a697a2d840876f08092ba02f988170e90c5f77b6f934ac15c79f173` |
| persistence | `71bf96e4fca54d16e323f5eef9766a6098c6ea4b9416b33aa012317d5f682bd2` |
| shadow input | `2cb66df8850d1953f42686a52d6338b62addc2a9e347d4844aba32e74dd343ae` |
| aggregate build manifest | `1ad861908b6849c1868bb428cbfa865cc7514ceb3670f8ed8fdc1c5ab55ebec5` |

The observer and persistence pack hashes are unchanged from their live-proven revisions.

## Deterministic shadow fixture

- pipeline result digest: `d0ff72a55893b064d59e3756b278b992495d7ec2280fb63ceaab9cac0f6578ed`;
- decision result digest: `1a132b488704d06d689eba9268fe52e230a71f6974200ef0bde18cd69ffe6add`;
- scenario: three observed/proxy armies, three regions, one war pair, two controlled-army assignments;
- mode: `SHADOW_NO_ORDERS`.

## Persistence evidence

- status: `REPLICATED`;
- transport result digest: `e824800620a019a760772e8b219b89d9dd4eca5185ba9b56623481393da82d0c`;
- filename-invariant semantic digest: `b996cc93f07275bc8d36fa428baa5e055ee03ba19bebc113175beedf048198bb`.

## Adversarial coverage

The runtime suite verifies:

- unsafe pack paths and duplicate internal paths are rejected;
- observer and shadow sources contain no mutation or randomness tokens;
- the shadow source does not enumerate the complete foreign world;
- persistence mutation remains one `get_saved_value` and one `set_saved_value`;
- private, malformed, and out-of-order records are rejected;
- first-tick snapshots cannot enter the shadow pipeline;
- exact-pack observer replication and collection independence;
- fresh-write/reload persistence chain constraints;
- renamed persistence artifacts preserve semantic digest but not transport digest;
- foreign armies use visible-unit-count proxy;
- foreign regions use settlement-structure garrison proxy;
- identical shadow input yields identical proposal output;
- no order list or application packet exists.

## Limitation

PowerShell and Lua were statically inspected in the construction environment but could not be executed against Windows/WH3 here. The next owner-machine run must prove the new shadow pack's API calls and collector workflow.
