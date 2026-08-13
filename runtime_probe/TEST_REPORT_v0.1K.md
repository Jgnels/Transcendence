# Runtime Probe and SyntheticLab Test Report — v0.1K

## Scope

Calibrate the Battle of Eilhart replay as a reusable observed corpus and prepare a dense, battle-only, read-only replay probe.

## Test suites

- SyntheticLab: 20 tests
- Runtime Probe: 56 tests
- Total: 76 tests per complete validation

## New deterministic fixtures

- `battle_log_identity_churn_v1_valid.txt`
  - preserves schema-1 hierarchy-index churn;
  - reconciles aliases by unique UI identity.
- `battle_log_dense_v2_valid.txt`
  - schema-2 replay session;
  - stable identity without aliases;
  - dual-sampler start and heartbeat;
  - dense unit and alliance samples;
  - direct selection attribution;
  - complete terminal result.

## New adversarial and integration checks

- stable identity survives hierarchy-index changes;
- schema-2 duplicate stable identities fail;
- sparse phase-only traces cannot produce timing claims;
- dense traces enable state-duration, trajectory, target-switch, and aggregate metrics;
- dense verifier requires exact replay and pack identity;
- dense verifier requires heartbeats, bounded gaps, local and visible-enemy units, and read-only authority;
- selection callback absence is preserved as a limiting result rather than failing the dense observation result;
- dense corpus retains aggregate timeline, unit trajectories, and attribution labels;
- Tier 4R accepts both reconciled sparse evidence and stable no-alias dense evidence;
- watcher reads only `transcendence_runtime_log.txt`, verifies schema 2, and exports no replay binary;
- dedicated replay pack contains only the battle script;
- battle source has no order or mutation tokens;
- all four probe packs remain deterministic PFH5 mod packs.

## Observed-corpus regressions

All ten Battle 4 Tier 4R checks pass:

- stable identity contract;
- sampling claim matches coverage;
- casualty claim matches terminal coverage;
- command attribution is explicit;
- visibility filtering is preserved;
- commander-survival stress case;
- frontline-collapse stress case;
- ranged-output stress case;
- enemy-rout stress case;
- unknown terminal-state stress case.

## Deterministic outputs

- reconciled report result digest: `1f151473c0530a43f768ea2c3c01ae2df1faa397d79de5e1d6a001daef8352cb`
- Tier 4R corpus result digest: `24af79128738bc648504094784eaced4d872ca05bf680c0e5f16061eac47da8d`
- Tier 4R regression result digest: `0d93daf622e65e1bdf498c9a8526c2d34a79c93bbd29099a0d2c31c6ce149e02`
- Battle 4 analysis result digest: `ff77f7792b005bb4b2e7ad242618e4fe578fec3c24555c951ee062bda67f4bff`
- probe-build result digest: `bb06bff155cfd1e69182c82080e1ae865b8ef1a19008f80990c0a716e2b9710c`
- build-manifest SHA-256: `d88b383cccc9c26e9f5b4193130ba52ff25c18ebf7699d9f15c8cb735b940644`

## Pack outputs

- observer: `0c1dd8940a697a2d840876f08092ba02f988170e90c5f77b6f934ac15c79f173`
- persistence: `71bf96e4fca54d16e323f5eef9766a6098c6ea4b9416b33aa012317d5f682bd2`
- combined shadow: `782f7e69c97059c9f66eb6dad5736236c3af9c54bee8b62b6a40a4d9fbf99da8`
- dedicated battle replay: `185baaa832beb458797e47766a3ad121530cdcf811097e8eb90d787df50c8443`

Two complete builds were byte-identical.

## Final repository validation

| Run | Result | Time | Maximum resident memory |
|---:|---|---:|---:|
| 1 | PASS | 2.04 seconds | 114,828 KB |
| 2 | PASS | 1.86 seconds | 111,668 KB |

Each run executed 76 tests and verified 150 canonical repository files. No random seed is used by the replay parser, reporter, corpus builder, or verifier.
