# Runtime Probe test report v0.1K-r1

## Scope

Dense replay parser ordering correction, sampler initialization correction, setup-failure observability, and regression coverage for the exact structural failure seen in the first v0.1K replay pass.

## Validation

- SyntheticLab tests: **20**
- Runtime-probe tests: **60**
- Total tests: **80**
- Canonical repository files verified: **159**
- Full repository validation: **PASS**

## New regressions

- schema-2 `UNIT_HIERARCHY → UNIT_STATIC` discovery ordering is accepted;
- unresolved hierarchy identities are rejected;
- a synthetic setup-abort trace is parsed and classified `PARTIAL`, not discarded;
- source forbids direct `math.max(0, trans_battle_safe(...))`;
- aggregate values are normalized before arithmetic;
- `SAMPLER_START` is emitted before the initial aggregate;
- setup failure emits required capability `battle.setup`;
- preserved dense captures can be reprocessed without exporting the raw log.

## Reprocessed owner evidence

- complete replay session recovered offline;
- 34 canonical units;
- zero identity aliases;
- 397 command events;
- five phase samples;
- zero interval samples;
- zero sampler heartbeats;
- dense coverage ratio `0.020243`;
- maximum sample gap `601900 ms`;
- reprocessed verification status `PARTIAL`.

## Deterministic pack build

- observer: `0c1dd8940a697a2d840876f08092ba02f988170e90c5f77b6f934ac15c79f173`
- persistence: `71bf96e4fca54d16e323f5eef9766a6098c6ea4b9416b33aa012317d5f682bd2`
- corrected combined shadow: `0714863e2081206aa7d0790ec14d7c3c3c7ae33eea416d72dba0d6a2ecd0a89e`
- corrected dedicated replay: `6e3f8e7bbc7d66754a7fa764c802e2b5599d13e83820e0785cb85d738040f66d`
- build result digest: `1d87b0d345a5994eb400be4d7c5cc9c6a816910ab2aef4f9539572c53af1916a`
- build-manifest SHA-256: `37a6321b4234af19dd9aaff0501bcdc09b67631812be820d3d524a21dc560576`

Two independent builds were byte-identical for all four packs.
