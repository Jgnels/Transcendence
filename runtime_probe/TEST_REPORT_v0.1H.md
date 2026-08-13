# Runtime Probe Test Report — v0.1H

## Scope

v0.1H replaces one-turn shadow processing with a consolidated multi-turn campaign pipeline while preserving the frozen observer, persistence, and shadow pack boundaries.

## Automated coverage

- 18 SyntheticLab tests;
- 30 runtime-probe tests;
- 48 total tests per full validation.

New runtime tests cover:

1. deterministic five-turn campaign processing;
2. exact five-turn verifier acceptance;
3. rejection when the minimum turn count is not met;
4. detection of foreign exact-strength policy violations;
5. rejection of nonconsecutive turns and wrong exact pack identity.

Existing tests continue to cover deterministic PFH5 output, pack parsing, observer replication, persistence verification, private-field rejection, malformed and out-of-order records, loader entrypoints, mutation-source guards, and single-turn shadow adaptation.

## Deterministic outputs

- observer pack: `0c1dd8940a697a2d840876f08092ba02f988170e90c5f77b6f934ac15c79f173`;
- persistence pack: `71bf96e4fca54d16e323f5eef9766a6098c6ea4b9416b33aa012317d5f682bd2`;
- shadow pack: `2cb66df8850d1953f42686a52d6338b62addc2a9e347d4844aba32e74dd343ae`;
- five-turn fixture report: `7adeac641b0ad95dbd039530f731e08e1301fcac8b1b3804bbc37e41a79ad45a`.

Two pack builds were byte-identical.

## Evidence limits

Passing these tests promotes only project-owned offline tooling to `CONTROL`. Expanded WH3 field availability and multi-turn live behavior remain `UNVERIFIED` until the consolidated campaign run.


## Full validation result

Two complete repository validations passed with 112 hashed files. The deterministic build result digest was `1de93c89eddbd5ca566f37f02ed9c5f914b72569a9b9127baeaf1c9f6c55d804`.
