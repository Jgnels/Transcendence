# SFO Observed Calibration and Replay Deep-Dive Specification v0.1Z

## Objective

Use the recovered six-turn, three-battle SFO session as the first multi-battle observed calibration baseline, then use the two preserved replays to answer tactical questions that event telemetry alone cannot settle.

## Evidence layers

### Layer A — frozen runtime facts

`runtime_probe/fixtures/sfo_observed_combined_v0.1Z.json` records only path-free identities, counts, hashes, authority facts, and scope limits derived from the recovered session.

### Layer B — SyntheticLab calibration summaries

`synthetic_lab/corpora/sfo_reikland_three_battle_calibration_v0.1Z.json` preserves one compact episode per observed battle. It supports threshold robustness, decision-window frequency, command-budget stress, role-policy disagreement, and replay-alignment planning. It is not a game simulator and the owner trace is not an optimal-policy label.

### Layer C — replay-visible tactical alignment

The replay cohort is exact and finite. Each playback should preserve dense schema-2 telemetry while the owner observes, or later reviews, visible battlefield behavior. The useful questions are:

1. What formations and frontage changes precede first contact?
2. Which movement/attack commands are visibly carried out, interrupted, or superseded?
3. When do collision, pathing, unit cohesion, or terrain explain apparently poor movement?
4. Which target switches are tactically sensible versus command thrashing?
5. When do local crises become recovery, terminal collapse, pursuit, or reformation opportunities?
6. How do cavalry, artillery, ranged, characters, and frontline units differ in commitment and disengagement timing?
7. Which telemetry-derived decision windows correspond to visible tactical opportunities, and which are artifacts of sparse or ambiguous state?
8. Are repeated owner commands corrections, confirmations, camera/UI effects, or genuine policy changes?

## Deep-dive protocol

- exact replay hash must match the frozen cohort;
- enable exactly SFO plus `transcendence_battle_replay_probe.pack`;
- do not issue commands during playback;
- allow the replay to reach completion;
- preserve private raw telemetry in a deterministic verified ZIP;
- treat visual interpretation as annotated evidence, not automatic truth;
- never promote a command event to acknowledgement or causal execution without a separate supported signal;
- never include replay bytes, saves, Creative Assembly assets, SFO content, or personal paths in public artifacts.

## Prioritization

1. Ubersreik first because it is the smaller, earlier battle and is best for validating the workflow.
2. Marienburg second because the larger mixed-force roster offers more cavalry, ranged, artillery, and character interactions.
3. Only after both exact replay captures should v0.1Z derive cross-battle tactical calibration changes.

## Stop conditions

Stop and preserve evidence if:

- replay hash differs;
- active mod set is not exact;
- the replay probe hash differs;
- schema-2 runtime markers are absent;
- the replay fails to complete;
- private ZIP verification fails;
- WH3 or SFO version changes before the cohort is captured.
