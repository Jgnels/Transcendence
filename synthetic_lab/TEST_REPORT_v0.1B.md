# SyntheticLab v0.1B Construction Test Report

**Environment:** Python 3 standard library in the build container  
**Date:** 2026-07-29

## Test suite

- 18 tests executed.
- 18 passed.
- No third-party Python packages required.

Coverage includes:

- canonical digest order independence;
- campaign contract validation;
- prohibited private-field rejection;
- hidden-army filtering;
- deterministic Tier 1 replay;
- exactly one objective per controlled army;
- no hidden-target leakage;
- deterministic Tier 2 replay for identical seeds;
- seed-sensitive Tier 2 variation;
- Tier 3 distribution output;
- deterministic Tier 4 execution;
- PFH5 index parsing and table classification;
- duplicate-army and target-capacity enforcement;
- wrong-format and compressed-entry rejection;
- extracted ZIP/script intervention classification;
- shared-table conflict detection.

## Performance and repeatability

- test suite: 0.57 seconds, maximum RSS 111,008 KB;
- smoke run 1: 0.54 seconds, maximum RSS 111,132 KB;
- smoke run 2: 0.58 seconds, maximum RSS 111,096 KB;
- smoke output files were byte-identical: `6eaa096a29242a7dbba120574361e47f280a81eb07592a7fbaa9739ea56afffd`;
- source audit run 1: 0.95 seconds, maximum RSS 143,540 KB;
- source audit run 2: 0.92 seconds, maximum RSS 143,372 KB;
- all four source-audit JSON outputs were byte-identical between runs.

## Smoke run

Configuration:

- profile: `vanilla_wh3_8_1_1_build_48122_4194776`;
- Tier 2/3 scenario: `tier2_late_game_pressure_v1`;
- Tier 4 scenario: `tier4_outnumbered_empire_v1`;
- Tier 2 seed: `101`;
- Tier 3 seeds: `101,102,103,104,105`;
- turns: `8`.

Digests:

- Tier 1 result: `454bb087f6314bec55f5eab8792f2f844d31990dfe16c4953343c1eb4fcb5675`
- Tier 2 result: `d463c9770c9165334a3e5da305a2e2054a4b97d6a4adccf36fe0e63eb006dd3c`
- Tier 2 final state: `049caee8c9b3e0b0546e1ee97675d7ba888d5d415543223bf534b4c9479c5a18`
- Tier 3 result: `017937b6096e3b9513130af31f30b3a86de4bad93022a13effaa4e2fe83373de`
- Tier 4 result: `a7ec35c20fbbe4a119cd7d1639b22f01877cee4d76e577d5ee05106664e5fba2`

Tier 2 smoke metrics:

- battles: 2;
- captures: 1;
- controlled armies final: 3;
- controlled regions final: 3;
- hold rate: 0.625;
- objective changes: 6;
- objective churn rate: 0.25.

Tier 4 winner in the deliberately outnumbered fixture: `greenskins`.

## Source audit run

Derived-output SHA-256 digests:

- comparison: `487b6c9459765e5dc7932c42b6f53e506af269d52b19690cf87d408cba4cefa0`;
- DeepWar audit: `9a31116582eca3d9cd9bd7fc2bf018eb6092803e668edb363dd3fba573e3a0eb`;
- Hecleas audit: `8f48bf1f8f0a298416f748a6f1fbdf777763f936b7c98b909ab29229c4477a5b`;
- SFO audit: `55abf4ecd0c39d710595c8ea72b7622737fa18ea5eeec30031b6304563dd344d`.

- DeepWar: 15 DB files; 14 direct-native-CAI classifications; source hash frozen.
- Hecleas: 28 DB files; direct CAI, diplomacy, campaign behavior, and autoresolve families; source hash frozen.
- SFO extracted audit: 709 files, 338 table families, 43 Lua scripts; source hash frozen.
- DeepWar/Hecleas overlap: 10 table families.
- DeepWar/SFO overlap: 2 table families.
- Hecleas/SFO overlap: 5 table families.
- Shared by all three: 1 table family.

## Limitations

This report proves only construction-environment execution. Owner-machine PowerShell execution, pinned RPFM/schema validation, pack building, WH3 loading, and Reality Gate R0 remain open.
