# Gate 0 — SFO Dual-Replay Tactical Calibration v0.2A

**Status:** CLOSED OFFLINE AGAINST EXACT OWNER REPLAY, TELEMETRY, AND VISUAL EVIDENCE  
**Evidence:** `OBSERVED` + `SUPPORTED` bounded visual interpretation + `CONTROL_OFFLINE` derivation  
**Authority:** `NO_ORDERS`

## Gate closed

The optional replay-visible alignment layer from v0.1Z is closed for the exact Ubersreik and Marienburg cohort. No additional replay capture is required.

## Observed source facts

### Ubersreik

- replay SHA-256 `e96c160ce8ca83463407d2008c676da1bcad2a0e0d2ec1f03b475097b4c4ea89`;
- raw dense log SHA-256 `8ae4ee9736283755b0af4777a2738daf66e7fed84502c703d637bd6b8cd2b08f`;
- visual recording SHA-256 `e3a48d3f74ebd2aca9f477f2dcc5957a447e28c03002189771ed9d6704275ba1`;
- visibly confirmed title `Battle of Ubersreik`, land battle, Reikland versus Empire Secessionists;
- visibly confirmed `Decisive Victory`;
- 499.7 seconds, 169 detail samples, 998 aggregate records, 28 canonical units, and 183 command events;
- 3 initially observed local units and 16 final local units;
- local casualty lower bound 334; visible-enemy casualty lower bound 981.

### Marienburg

- replay SHA-256 `844d2efc4434c18d09d5958fc5cf9c60bf21201d5ca2af2e254077666ba0c902`;
- raw dense log SHA-256 `e78dbdff7322be33407bb03330d34df803e1d8dc213bafc6c9d46df66b60ceb4`;
- visual segments SHA-256 `c7482eea91bed31322355586c373160f6cbbc89005659412565b0768f290fee6` and `67d7cdb053d281f0a23e033d561508d880e034713652f206a0f2eedbaf952997`;
- visibly confirmed title `Battle of Marienburg`, land battle, Reikland versus Marienburg;
- visibly confirmed `Pyrrhic Victory`;
- 1,049.8 seconds, 352 detail samples, 1,960 aggregate records, 35 canonical units, and 328 command events;
- 1 initially observed local unit and 20 final local units;
- local casualty lower bound 782; visible-enemy casualty lower bound 1,314.

## Deterministic calibration result

Frozen artifact:

`research/runtime_evidence/SFO_REIKLAND_DUAL_REPLAY_TACTICAL_CALIBRATION_v0.2A.json`

Result digest:

`364431a064ef1f15bc6ab7da4417b688d882ac7f2035be753728d9d75870565e`

The cross-battle contrast shows that Marienburg lasted 2.100861 times as long and had a 2.341317-times larger observed local casualty lower bound, despite both battles being victories. Therefore win/loss and victory grade are not sufficient tactical-quality benchmarks.

## Rules promoted

Promoted only as bounded advisory calibration:

1. **Force-completeness guard:** do not treat the initial local hierarchy as the complete force while reinforcement discovery is changing.
2. **Outcome-cost separation:** evaluate preservation, role losses, and crisis exposure independently from victory status.
3. **Local-crisis independence:** retain local recovery priorities after visible enemy collapse begins.
4. **Terminal commitment abstention:** after outcome-decided or victory-countdown evidence, prohibit new high-commitment objectives; permit only bounded pursuit, disengagement, or reformation hypotheses.
5. **Identity provenance:** display the visually confirmed replay title while retaining the runtime battlefield identity separately.

## Defects and limiting results preserved

- Both runtime corpora identify `Battle of Eilhart — Reikland vs Empire Secessionists`; visual evidence proves Ubersreik and Marienburg titles. The sources are separated rather than silently reconciled.
- Both replay captures named the shadow pack in launcher-state attestation. The battle script was byte-identical to the dedicated replay probe, so tactical telemetry is usable; exact outer pack identity remains `UNVERIFIED`.
- High tactical camera footage supports broad geometry and phase review but not continuous unit-card, exact frontage, or formation-depth measurement.
- Command events remain `OBSERVED_NOT_ACKNOWLEDGED`; visual movement is not causal execution evidence.
- Owner play remains reference behavior, not an optimal-policy label.

## Capability adjudication

Promoted for the exact cohort:

- exact replay identity;
- dense SFO replay time series;
- visually confirmed display title and outcome;
- reinforcement-aware force discovery;
- bounded cross-battle tactical-cost calibration;
- local-crisis/enemy-collapse overlap;
- post-victory terminal-tail observation.

Not promoted:

- command acknowledgement;
- command execution causality;
- tactical superiority;
- exact outer probe-pack container;
- siege, ambush, flying-heavy, allied-control, or multi-faction generalization.

## Privacy and authority

No video, frame, replay, save, raw log, game asset, SFO content, generated pack, personal path, or owner identifier is committed. The output has no runtime adapter and no order authority.

## Validation result

- SyntheticLab: 85/85 passed;
- Runtime Probe: 126/126 passed;
- total tests: 211;
- canonical hashed files: 331;
- full repository validation: passed twice after final ledger generation;
- public GitHub seed remains unchanged at `16c4fa0d5290822a9fcba150b4dffcc8152f1b52`.
