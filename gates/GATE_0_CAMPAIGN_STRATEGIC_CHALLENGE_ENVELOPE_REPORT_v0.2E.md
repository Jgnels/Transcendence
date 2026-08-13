# Gate 0 Campaign Strategic Challenge Envelope Report — v0.2E

## Segment result

**Closed offline:** deterministic strategic-challenge benchmark envelope and adversarial matrix.

**Gate 0 overall remains open:** no campaign order authority, durable late-game rival behavior, economy/recruitment recovery, diplomacy/bloc intent, targeting-history anti-player analysis, broad factions, or owner-rated late-game experience is proven.

## Why this gate

After v0.2D, another ordinary land-battle replay would mostly increase tactical overfitting. The highest-value offline step is to define the campaign-level quality boundary before implementing a stronger strategic director: coherent rival powers and meaningful fronts should count as challenge; unrelated wars, hidden information, and player identity should not.

## Exact inputs

- corrected owner-observed vanilla turns 4–7 report: `8189081fb1b4ad57fb09592f5c9594480b42cf3f575d76eed94014cec7dc37a5`;
- synthetic late-game pressure reference: `105578f0496b7357c45af0a0330e3c25686d0ebb1e4dcd3c1b55a404f57d3aa9`;
- adversarial suite: `a9d67d027d3c2bab1a711b1d923c9804b96d8143d00696299e34e6b17ad8df44`.

## Frozen outputs

- strategic challenge envelope result digest: `4cbc5cb253b5cc16966807e889e4c05354a284100cd8f237b90b493281bc9423`;
- strategic challenge envelope file SHA-256: `be22be9c661ac80347c286333d4bdc833b2e70260f796ee82e0241dfaeb28302`;
- adversarial matrix result digest: `4acfa02699cd9f78eace303889d2b7bba274b82b65582b2ea21f3cd70690e3df`;
- adversarial matrix file SHA-256: `1aac9853f394f62a514c07fd55ebf7537e9cc8593000fdd715740e8c5d1ee443`.

## Observed-input findings

The evaluator does not rewrite the source evidence. On the four preserved turn-start snapshots:

- turns 4–6 contain two wars but no visible at-war hostile army/region assets in the supplied observer-safe snapshot, so visible pressure remains low rather than being inflated from war count;
- turn 7 contains three wars and two visible Marienburg armies plus one observed Marienburg region; under the project-owned benchmark this becomes `COHERENT_VISIBLE_RIVAL_CANDIDATE`;
- the visible Marienburg hostile-to-controlled army proxy ratio is `1.602033` on turn 7;
- that label is a snapshot candidate only, not proof of strategic coordination, durable power, or native CAI quality.

The synthetic late-game reference reports one covered threatened front, one low-replenishment controlled army, and only one visible player army because the hidden player army is correctly excluded.

## Adversarial results

- 8/8 contract cases pass;
- 5/5 metamorphic checks pass;
- hidden-enemy injection is semantically inert;
- `player_empire` → `npc_empire` relabeling is semantically inert;
- input-order, coordinate-translation, and uniform-strength-scale invariants pass;
- private-path input fails closed;
- same-faction co-location is explicitly not promoted to coordination.

## Validation

- 115/115 SyntheticLab tests pass;
- 139/139 Runtime Probe tests pass;
- 254/254 direct regression tests pass;
- campaign envelope regeneration is byte-identical across two independent runs and matches the frozen artifact;
- adversarial-matrix regeneration is byte-identical across two independent runs and matches the frozen artifact;
- the full smoke result is byte-identical across two runs and contains the same v0.2E envelope and matrix result digests;
- `compileall` passes for project Python source/tests/tools;
- `python tools/validate_repository.py` completes `PASS repository validation (368 hashed files)`;
- 500-asset snapshot evaluation is deterministic across 10 timed runs: mean 0.0459 s, maximum 0.0998 s in the validation environment.

## Authority

- `NO_ORDERS`;
- application `PROHIBITED`;
- no runtime adapter;
- no campaign mutation;
- no human/player identity feature;
- no hidden enemy consumption.

## Remaining uncertainty

This gate cannot establish whether WH3/SFO factions actually form durable rival blocs, recover after defeats, target the player disproportionately, coordinate armies, or create a more enjoyable late game. Those require longitudinal campaign-state evidence and eventual owner experience ratings. The 2.0-turn, 0.65-replenishment, 0.50-coherence, and 0.65-fragmentation thresholds remain engineering contracts.

## Smallest next project step

Continue offline into a bounded strategic/theater portfolio that consumes this benchmark and the existing observer-safe campaign contract. Do not request a new WH3 session until that portfolio identifies a specific missing longitudinal field or a separately frozen campaign authority gate.
