# Runtime Probe Test Report — v0.1I

## Scope

v0.1I supersedes the campaign-only v0.1H live plan with one combined five-turn campaign and ordinary-battle observation gate. The combined pack remains read-only.

## Automated coverage

- 18 SyntheticLab tests;
- 38 runtime-probe tests;
- 56 total tests per full validation.

New battle and combined-gate tests cover:

1. static battle-source order/controller/visibility guards;
2. deterministic battle-log parsing and reporting;
3. hidden enemy identifying-record rejection;
4. unclosed detailed-sample rejection;
5. combined five-turn plus one-battle verifier acceptance;
6. explicit `PARTIAL_NO_BATTLE` classification when campaign evidence exists without a battle.

Existing tests continue to cover deterministic PFH5 output, observer replication, persistence verification, private-field rejection, malformed and out-of-order records, loader entrypoints, campaign mutation guards, five-turn campaign processing, proxy-policy enforcement, exact pack identity, and orderless outputs.

## Deterministic outputs

- observer pack: `0c1dd8940a697a2d840876f08092ba02f988170e90c5f77b6f934ac15c79f173`;
- persistence pack: `71bf96e4fca54d16e323f5eef9766a6098c6ea4b9416b33aa012317d5f682bd2`;
- combined campaign/battle shadow pack: `c23b8187dde9e0f162b1564b47910714501b9d088b756cb95dfe16cad470b551`;
- pack-build result digest: `2b18a01f5b9c75100de50dda59774ae5d265352f29594b29941dce4534da4550`;
- build-manifest SHA-256: `64d736885bff93fccd9207c33663eb987f610301ad12556b6894a3b605b64b65`;
- campaign fixture result: `7adeac641b0ad95dbd039530f731e08e1301fcac8b1b3804bbc37e41a79ad45a`;
- battle fixture result: `e4793e9e43e3663b568c1438b66a4331aab398bd272ec443d29346ec1df3e266`;
- combined fixture verifier: `91b8809710d90d251f8924ef6c8dd72ef42cfabc6934b9669a8163fd19270f2b`.

Two pack builds were byte-identical before the final repository manifest was frozen.

## Evidence limits

Passing these tests promotes only project-owned offline tooling to `CONTROL`. Live ordinary-battle script loading, field availability, sampling overhead, and command-event contexts remain `UNVERIFIED` until the owner-machine session. No battle-control or tactical-quality claim is promoted.

## Complete validation repetitions

Two complete repository validations passed with 122 hashed files and all 56 tests:

| Run | Elapsed | Maximum resident memory |
|---|---:|---:|
| 1 | 1.72 seconds | 111,496 KB |
| 2 | 1.67 seconds | 111,200 KB |

The two deterministic pack builds were byte-identical. Python compilation passed for every runtime tool. PowerShell and live Lua execution remain owner-machine checks; this environment has neither PowerShell nor the WH3 Lua runtime.
