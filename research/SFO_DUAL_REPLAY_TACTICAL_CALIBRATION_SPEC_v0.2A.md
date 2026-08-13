# SFO Dual-Replay Tactical Calibration Specification v0.2A

## Objective

Close the finite replay-visible alignment layer opened by v0.1Z using the exact Ubersreik and Marienburg replay cohort, dense schema-2 telemetry, and owner-provided full visual recordings. Convert only bounded, privacy-safe observations into deterministic SyntheticLab calibration rules. Do not issue orders or treat the owner trace as optimal policy.

## Exact source cohort

| Battle | Replay SHA-256 | Dense log SHA-256 | Visual evidence |
|---|---|---|---|
| Ubersreik | `e96c160ce8ca83463407d2008c676da1bcad2a0e0d2ec1f03b475097b4c4ea89` | `8ae4ee9736283755b0af4777a2738daf66e7fed84502c703d637bd6b8cd2b08f` | one 1920×1080/30 FPS recording, SHA-256 `e3a48d3f74ebd2aca9f477f2dcc5957a447e28c03002189771ed9d6704275ba1` |
| Marienburg | `844d2efc4434c18d09d5958fc5cf9c60bf21201d5ca2af2e254077666ba0c902` | `e78dbdff7322be33407bb03330d34df803e1d8dc213bafc6c9d46df66b60ceb4` | two overlapping 1920×1080/30 FPS segments, SHA-256 `c7482eea91bed31322355586c373160f6cbbc89005659412565b0768f290fee6` and `67d7cdb053d281f0a23e033d561508d880e034713652f206a0f2eedbaf952997` |

Video bytes, frames, replay bytes, raw logs, game assets, personal paths, and pack bytes remain private and excluded from the repository.

## Evidence model

The layer preserves three independent source identities:

1. replay binary identity;
2. runtime battlefield identity;
3. visually confirmed display title and outcome.

A visual title may be used for display only while the runtime identity remains unchanged as a separate source field. Visual movement after a command is not acknowledgement and is not causal execution proof.

## Deterministic inputs

- `synthetic_lab/corpora/sfo_ubersreik_observed_dense_v0.2A.json`
- `synthetic_lab/corpora/sfo_marienburg_observed_dense_v0.2A.json`
- `synthetic_lab/corpora/sfo_reikland_dual_replay_visual_alignment_v0.2A.json`

The two dense corpora contain public-safe, visibility-filtered telemetry only. The visual alignment corpus contains hashes, dimensions, durations, bounded facts, phase windows, confidence, interpretation limits, and noncommitment flags.

## Calibration output

`SFO_DUAL_REPLAY_TACTICAL_CALIBRATION_V1` derives:

- force-discovery and reinforcement-completeness timing;
- pre-contact, commitment, local-crisis, visible-enemy-break, pursuit, and terminal context;
- role-specific observed casualty and kill lower/upper-bound summaries;
- command-rate and battle-duration contrasts;
- victory-grade versus tactical-cost separation;
- identity provenance separation;
- bounded advisory rule updates.

The output is `NO_ORDERS`. It cannot become a command packet, acknowledgement, execution result, route proof, optimal-policy label, tactical-superiority claim, or broad SFO compatibility claim.

## Gate criteria

The gate closes only when:

- all exact source hashes and dense-corpus digests match;
- visual input rejects paths, bytes, unknown videos, malformed ranges, overlapping telemetry phases, foreign replays, and forbidden evidence promotions;
- replay title and runtime identity remain separate;
- both outcome grades are visually observed and telemetry winner remains consistent;
- force-completeness, outcome-cost, local-crisis, terminal-abstention, and identity-provenance rules are generated deterministically;
- output matches a frozen artifact twice;
- SyntheticLab, Runtime Probe, and full repository validation pass;
- installer, rollback, and unknown-file rejection are proven from exact v0.1Z-r1.

## Scope limits

This cohort contains two ordinary SFO land battles for Reikland. It does not establish siege, ambush, flying-heavy, allied-control, or broad faction behavior. The exact outer Transcendence pack container remains unverified because both observed captures reported the shadow-pack name while the loaded battle script was byte-identical to the dedicated replay-pack script.
