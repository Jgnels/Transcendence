# Gate 0 Report — v0.1U Action Feasibility Semantic Calibration

## Gate decision

**Closed offline.**

The owner-installed v0.1T repository is the canonical base. The owner-provided no-replay detailed export was verified, frozen, and semantically adjudicated without another WH3 run.

## Defect found

`NONPOINT_ZERO_VECTOR_REACHABILITY_MISCLASSIFICATION`

The legacy read-only probe called `can_reach_position` whenever the command callback returned a non-nil position object. Several non-point or opaque command callbacks exposed the zero vector. This made raw query counts look like point-feasibility evidence even when no explicit destination was available.

Preserved before-state:

- 1,249 raw `QUERY_TRUE` samples;
- 38 raw `QUERY_FALSE` samples;
- zero unavailable;
- all 38 false samples located in `Move Orientation Width` window `w5`;
- two affected actors;
- zero ordered-position matches and zero observed movement for those actors during that window.

## Correction

The evidence layer now separates raw engine telemetry from semantically qualified point evidence.

Only explicit, finite, nonzero `Move` callback positions qualify in this capture. Unit-target and opaque callbacks retain state evidence but their raw point query is classified as not applicable.

Corrected live point evidence:

- 16 explicit point windows;
- 16 actor-windows;
- 191 qualified samples;
- 191 `QUERY_TRUE`;
- zero qualified `QUERY_FALSE`;
- zero unavailable;
- valid explicit-point false evidence remains unobserved.

## Additional observed calibration

- 16/16 explicit Move actor-windows matched ordered position in the initial sample;
- 12/16 showed movement during the window;
- 48/49 visible Attack Unit actor-windows matched current target in the initial sample;
- 30/49 showed movement during the window.

These remain state matches, not acknowledgement or causal execution.

## Implementation

Added:

- strict semantic adjudicator;
- frozen public-safe detailed window and manifest documents;
- frozen semantic calibration artifact;
- semantic capability-profile builder;
- regression coverage for zero-vector Move rejection, issue-claim rejection, false-result disqualification, and Battle 4 nonpromotion;
- updated capability, claim, risk, decision, source, architecture, benchmark, and continuation records.

## Evidence classification

Promoted:

- explicit Move point query true results: `OBSERVED`, scoped to one ordinary vanilla battle;
- semantic command-modality adjudication: `CONTROL_OFFLINE`;
- semantically qualified capability profile: `OBSERVED_SEMANTICALLY_QUALIFIED_CAPABILITY_PROFILE`.

Downgraded or corrected:

- raw false point-query evidence: `LIMITING_RESULT_CORRECTED_AT_EVIDENCE_LAYER`;
- valid explicit-point false result: `UNVERIFIED_NONE_OBSERVED`;
- aggregate v0.1S/v0.1T raw profile: frozen historical evidence, not current planner calibration.

Still unverified:

- any generated Battle 4 candidate point;
- valid false result on an explicit nonzero point;
- routes, formation, collision, arrival, command legality, issue, acknowledgement, execution, or outcome;
- SFO and other battle-type generalization.

## Authority

`NO_ORDERS`. No WH3 file, save, Workshop item, active mod list, or remote GitHub state is modified by this gate.

## Validation

- SyntheticLab: 64 tests passed.
- Runtime Probe: 81 tests passed.
- Total: 145 tests passed.
- Canonical repository files: 266.
- The complete repository suite passed repeatedly from the final tree.
- The three generated v0.1U artifacts rebuilt byte-for-byte in independent directories.
- No generated pack, replay, save, raw private log, executable, personal path, secret, Creative Assembly asset, or SFO content is included.

## Exact identities

- Owner detailed re-export ZIP: `83b7c3d851605f290c6a50045be920cdddc7224c8f9e7e63deefba5323e2ff7d`.
- Observed windows file: `e56e2e32fc5037bf104ea7da05184c7e591bec2394920b482174f808de7fa18f`.
- Observed manifest file: `37a6669f48d3b1eeb6a7ba1b5dcda0041f7d4cbd6ceaec1d25ef03bcedbe2afb`.
- Semantic calibration file: `59b3653987e1262309321357512e9190ceeb3f5d0908dfda0cee86ed00641485`; result `c1eda3165c7898eaafa81a73529ca7a51c92b1b27c8eedf35def03bfc9935d0c`.
- Semantic capability-profile file: `3af02b821a0efb46dee33585fd8ac48b6eb0c5b85c34e5bf5b269920f316f071`; result `c497fa8ddc494b9746830b2c8bb14f63444250d37a2b597f39eebe39ab2856b2`.
- Battle 4 v0.1U envelope file: `02bc66eeb9c76808d48352786fdc46bc6ac33ff3950a6b1d459304090d41ddea`; result `34a170c48f2e215246454bc314d88fb934cfc2ab55e709ad0a44918b4e5102fb`.
