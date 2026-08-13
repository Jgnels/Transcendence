# Gate 0 — SFO Chaos Replay Divergence Calibration v0.2C

**Status:** CLOSED AS A LIMITING RESULT  
**Evidence:** exact environment + dense nonterminal replay stream + hash-bound visual lifecycle  
**Authority:** `NO_ORDERS`

## Gate decision

The required exact replay playback was completed and captured successfully. It did not reproduce a natural terminal battle state. The evidence gate is therefore closed honestly as `CLOSED_LIMITING_RESULT_REPLAY_DIVERGENCE`, not left open for repeated owner playback and not falsely passed as an observed defeat.

## Exact result

- private evidence ZIP SHA-256: `18293f7f59fc9a2130a6c82ec48636097c946605d49980cfcb0f154a8c1a6126`;
- raw log SHA-256: `2175b2643f80b7e7fde9edd66443df1b8b5f2205ec3aad51fab013d48a686c0c`;
- calibration result digest: `a69f2ed4e09034dc79ac5462aefa7f9c949c09a33a3e4e843e4a8cdecddcaab4`;
- exact SFO/probe environment: verified;
- detail samples: 115;
- aggregate records: 637;
- canonical units: 23 with zero aliases;
- commands: 89, with 64 bounded inferred attributions and zero selection attribution;
- `BATTLE_COMPLETE`: absent;
- completed battle count: 0;
- terminal coverage: 0% for both alliances.

## Defects found and corrected

1. **Terminal-outcome overpromotion** — `run_battle_report.py` labeled terminal outcome `OBSERVED` even for incomplete sessions. It now emits `UNVERIFIED_INCOMPLETE_SESSION` unless the session is naturally complete.
2. **Post-process-exit log race** — the replay collector stopped immediately when WH3 exited. It now performs bounded consecutive-read stabilization so late log appends are retained. Process exit is explicitly never completion evidence.
3. **Reserve diagnosis overstatement** — visual evidence suggested no reserve. Exact unit timing instead supports delayed or uneven reserve commitment.
4. **Replay terminal-equivalence assumption** — invalidated for this exact replay. Replay stream exhaustion did not reproduce the owner-attested defeat.

## Claims supported

- exact dense nonterminal SFO trace: `OBSERVED`;
- replay divergence / missing natural completion: `LIMITING_RESULT`;
- crisis and lower-bound role-loss findings: `SUPPORTED`;
- reserve diagnosis refinement: `SUPPORTED`;
- owner-attested original defeat: preserved as `OWNER_ATTESTED`.

## Claims rejected or withheld

- observed defeat grade;
- replayed terminal defeat;
- victorious alliance in the replayed simulation;
- exact terminal casualties;
- command acknowledgement or causal execution;
- owner commands as optimal policy;
- anti-Chaos tactical superiority or faction-general thresholds.

## Remaining owner work

No repeat of `An Ogre's Folly` is required. After installing v0.2C, remove the replay probe and restore the normal launcher configuration. A future live result artifact or a different naturally completing Chaos battle may close terminal-outcome evidence, but it is not required for this gate.
