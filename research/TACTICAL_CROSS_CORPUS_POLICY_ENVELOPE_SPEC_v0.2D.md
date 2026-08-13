# Tactical Cross-Corpus Policy Envelope Specification v0.2D

## Purpose

Convert the four currently frozen ordinary-land-battle evidence corpora into a deterministic, read-only tactical policy envelope that distinguishes cohort-supported safeguards from single-battle hypotheses without issuing orders or treating owner play as optimal-policy truth.

The exact cohort is:

1. vanilla Eilhart complete victory (`442e1876…`);
2. SFO Ubersreik Decisive Victory (`a9334042…`);
3. SFO Marienburg Pyrrhic Victory (`058f10ad…`);
4. SFO `An Ogre's Folly` Chaos replay divergence (`4d84f49e…`), which is nonterminal and must remain `UNVERIFIED_NONTERMINAL`.

## Authority

- policy authority: `NO_ORDERS`;
- application authority: `PROHIBITED`;
- output is advisory/offline only;
- no runtime adapter, game API, unitcontroller, order issue, acknowledgement, execution, or outcome attribution is introduced.

## Exact source binding

The builder fails closed unless all four dense result digests match the frozen cohort and the v0.2A/v0.2C calibration digests are exact. Replay SHA-256 identities must remain unique. SFO display/replay identity and runtime battlefield identity remain separate provenance layers.

The repeated runtime identity `Battle of Eilhart — Reikland vs Empire Secessionists` for Ubersreik, Marienburg, and the Chaos replay is not silently corrected. v0.2A and v0.2C explicitly bind those runtime records to different display/replay identities. The policy must preserve both sources and mark their disagreement.

## Policy classes

The envelope freezes these evidence classes:

- `SUPPORTED_MULTI_CORPUS`: safeguards supported across more than one frozen battle;
- `SUPPORTED_BOUNDED`: a bounded supported rule with narrower evidence;
- `OBSERVED_MULTI_SOURCE`: provenance behavior directly established by multiple source layers;
- `HYPOTHESIS_SINGLE_CORPUS`: review-only behavior that may not be generalized;
- `SUPPORTED_BOUNDARY`: an authority or interpretation boundary rather than a tactical-quality claim.

## Core policy rules

1. Terminal result learning requires natural completion or a separately bound result artifact.
2. Runtime and display identities remain separate when source layers disagree.
3. Whole-force assumptions are deferred while local-force discovery changes.
4. Victory grade is scored separately from casualties, role loss, crisis exposure, and duration.
5. Local preservation remains higher priority than discretionary commitment during crisis, even when terminal evidence is present.
6. Severe high-value-asset review is ratio-based at an observed lower-bound loss fraction of 0.5, not an absolute model count.
7. Reserve state remains explicit: unknown, absent, available, committed late, or unable to support.
8. Natural terminal evidence blocks new high-commitment proposals.
9. Target concentration is review-only and remains a single-corpus hypothesis; absent selection attribution it is explicitly `HYPOTHESIS_REVIEW_ONLY`.
10. Owner command traffic is reference-only and not a target command frequency, acknowledgement, execution proof, or optimal-policy label.

## Adversarial matrix

The v0.2D matrix covers 17 scenarios and three metamorphic checks:

- nonterminal replay exhaustion;
- terminal commitment abstention;
- incomplete force discovery;
- ratio-based elite preservation at/above and below threshold;
- commander routing and low-hitpoint crisis;
- simultaneous terminal evidence and local crisis;
- late/unknown reserve states;
- target concentration with and without selection attribution;
- stale observations;
- hidden-enemy field injection;
- authority promotion;
- foreign policy provenance;
- asset-order invariance;
- model-count scale invariance;
- policy-rule order invariance.

## Generalization boundary

This policy is not a learned causal controller. It does not establish siege, ambush, interception, flying-heavy, multi-army, allied-control, cross-faction, multiplayer, route, formation, collision, line-of-fire, command-legality, acknowledgement, execution, or tactical-superiority claims.
