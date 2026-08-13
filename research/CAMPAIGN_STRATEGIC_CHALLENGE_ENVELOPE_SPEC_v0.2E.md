# Campaign Strategic Challenge Envelope Specification — v0.2E

## Purpose

v0.2E reconnects the mature tactical work to the project's primary product problem: late-game campaign challenge collapse. It does **not** add a strategic order adapter. It freezes a deterministic benchmark/evaluation layer that can tell later strategic-director work whether pressure comes from coherent visible rivals and meaningful fronts rather than simply counting wars, omniscient threats, or player-targeted dogpiles.

## Authority

- policy authority: `NO_ORDERS`;
- application authority: `PROHIBITED`;
- hidden enemy armies are removed through the existing observer-safe campaign contract;
- human/player identity is not an evaluator input or utility feature;
- co-location is not command coordination, and a single snapshot cannot establish native CAI intent or anti-player bias.

## Exact inputs

1. `research/runtime_evidence/CAMPAIGN_TURNS_4_7_REPROCESS_v0.1J.json`
   - file SHA-256 `8189081fb1b4ad57fb09592f5c9594480b42cf3f575d76eed94014cec7dc37a5`;
   - four owner-observed vanilla Reikland turn-start snapshots, turns 4–7, reprocessed under the corrected v0.1J observer-safe proxy contract;
   - source mode `SHADOW_NO_ORDERS`.
2. `synthetic_lab/scenarios/tier2_late_game_pressure.json`
   - file SHA-256 `105578f0496b7357c45af0a0330e3c25686d0ebb1e4dcd3c1b55a404f57d3aa9`;
   - synthetic late-game rival-bloc reference only; no WH3 outcome claim.
3. `synthetic_lab/scenarios/campaign_challenge_adversarial_matrix_v0.2E.json`
   - file SHA-256 `a9d67d027d3c2bab1a711b1d923c9804b96d8143d00696299e34e6b17ad8df44`;
   - eight adversarial cases plus five metamorphic checks.

## Snapshot diagnostics

`CAMPAIGN_STRATEGIC_CHALLENGE_ENVELOPE_V1` measures only observer-safe state supplied by the campaign scenario contract:

- controlled and visible hostile army counts and like-scaled strength;
- controlled and observed hostile region counts/value;
- visible hostile force-balance ratio;
- hostile force concentration by faction;
- candidate rival structure;
- threatened, covered, and exposed controlled regions;
- geometric two-turn front proximity;
- same-faction pressure co-location with an explicit `NOT_INFERRED_FROM_COLOCATION` coordination label;
- controlled low-replenishment load.

The following are explicitly unavailable from this contract:

- anti-player bias;
- diplomatic-bloc intent;
- durable recovery capacity;
- native CAI intent;
- campaign quality.

They require longitudinal targeting/diplomacy/economy/recruitment/outcome evidence rather than a position snapshot.

## Project-owned thresholds

The initial thresholds are deterministic engineering definitions, not empirical WH3 truths:

- front horizon: 2.0 geometric movement turns;
- controlled recovery review: replenishment below 0.65;
- coherent visible rival candidate: at least two visible armies, at least one observed region, and at least 50% of visible hostile army strength;
- fragmented visible pressure: at least two hostile asset factions with no faction above a 65% visible hostile army share.

They may organize scenarios and regressions. They may not be described as optimal strategy, learned behavior, or validated player-experience thresholds.

## Rival-structure labels

- `NO_VISIBLE_HOSTILE_ASSETS`;
- `SINGLE_OR_PARTIAL_VISIBLE_RIVAL`;
- `FRAGMENTED_VISIBLE_PRESSURE`;
- `COHERENT_VISIBLE_RIVAL_CANDIDATE`.

`COHERENT_VISIBLE_RIVAL_CANDIDATE` means only that the visible snapshot satisfies the project-owned concentration/presence contract. It does not establish alliance coordination, economy, staying power, or intelligent planning.

## Front labels

- `QUIET`;
- `CONTESTED`;
- `EXPOSED`;
- `SIEGED_COVERED`;
- `SIEGED_EXPOSED`.

A siege may establish crisis state without revealing or inventing an enemy army identity.

## Adversarial acceptance

The matrix must prove:

1. coherent visible-rival structure and front coverage remain separate dimensions;
2. three unrelated hostile factions are not rewarded as coherent challenge merely because war count is high;
3. visible pressure without a controlled field force reports an exposed front;
4. a huge hidden hostile army has zero effect on semantic output;
5. an observed siege can create a crisis without fabricated enemy identity;
6. recovery load is reported without claiming economy/recruitment recovery capacity;
7. one dominant rival plus a minor enemy is not mislabeled a fragmented dogpile;
8. private/path-bearing fields fail closed;
9. army/region/war input order does not alter semantic output;
10. coordinate translation does not alter semantic output;
11. uniform strength/garrison scaling does not alter ratio/classification semantics;
12. hidden-enemy injection does not alter output;
13. renaming the same enemy from `player_empire` to `npc_empire` does not alter semantic output.

## Source-acquisition relationship

No new third-party runtime dependency is introduced. The previously audited FreeOrion/DCT/VCMI/Wesnoth-style strategic decomposition work remains architecture inspiration only. v0.2E intentionally implements the smallest project-owned metric/guardrail layer before adding theater assignment, diplomacy, HTN/search, or learned ranking.

## Next boundary

The next strategic implementation may consume this envelope to build a deterministic theater/rival-power portfolio, but it must remain `NO_ORDERS` until campaign application authority is separately proven. Before durable late-game rival formation can be called calibrated, the project still needs longitudinal campaign evidence with economy/recruitment/diplomacy/targeting history and owner-rated tension/fairness/tedium.
