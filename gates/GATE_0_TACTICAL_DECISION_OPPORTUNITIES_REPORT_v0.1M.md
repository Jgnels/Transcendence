# Gate 0 — Tactical decision opportunities report v0.1M

## Classification

- canonical tactical-state trajectory: `CONTROL_OFFLINE`, derived from `OBSERVED` Battle 4 slices;
- decision-opportunity extraction: `CONTROL_OFFLINE` implementation, tactical recommendations remain `HYPOTHESIS`;
- loss-prevention diagnosis: `HYPOTHESIS`, counterfactual status `UNVERIFIED`;
- command-budget comparison: `REFERENCE_ONLY_NOT_CAUSAL`;
- authority: `NO_ORDERS`.

No Battle 4 replay or owner-machine action was required.

## Inputs

- dense Battle 4 corpus: `synthetic_lab/corpora/battle4_eilhart_observed_dense_v2.json`;
- dense corpus result digest: `442e187638c4d2b3457910efdbb50d13f16fd27a8391e7ac9bd2d6aaed47c33d`;
- trace slices: `synthetic_lab/corpora/battle4_eilhart_trace_slices_v1.json`;
- trace-slice result digest: `ccb23dc2e24102b53c5833ecae9047ebfd449476cd0508aacd4ec0fd6dc56360`.

No replay, raw private log, save, game asset, personal path, or generated pack entered the repository.

## Implemented artifacts

### Canonical tactical-state trajectory

Path:

`research/runtime_evidence/BATTLE4_EILHART_TACTICAL_STATE_TRAJECTORY_v0.1M.json`

- state contract: `TACTICAL_STATE_VISIBILITY_SAFE_V1`;
- trajectory contract: `TACTICAL_STATE_TRAJECTORY_V1`;
- states: 8;
- result digest: `cec345739fc6d4231b88f2cfb6814082ab0be970530da704f3b36d881f63cbb5`;
- file SHA-256: `7e9c50ebe2eebf89324c825fed57f35c8be315964a98295334fa4560d061b287`.

### Tactical decision opportunities

Path:

`research/runtime_evidence/BATTLE4_EILHART_TACTICAL_DECISION_OPPORTUNITIES_v0.1M.json`

- result digest: `5af29dc6a23af6e82c8288ab321f1a06d1bb9583c8ddfea39b2c6f501d80670b`;
- file SHA-256: `9fd42b83c94a0f887d036027d6b66a8f1487091cb699aea874db74ce9d863fce`;
- candidate decision opportunities: 37;
- selected opportunities: 25;
- maximum selected in one slice: 6;
- minimum critical-opportunity coverage: 1.0;
- advisory priority transitions: 50;
- owner command-event reference: 397;
- transition/reference ratio: `0.125945`;
- comparison status: `REFERENCE_ONLY_NOT_CAUSAL`.

## Battle-state result

The eight observed milestones classify as:

| Slice | Local stability | Visible-enemy state | Advisory posture |
|---|---|---|---|
| deployment complete | `STABLE` | `CONTESTED` | `DEPLOYMENT_AND_INFORMATION` |
| first contact | `STABLE` | `CONTESTED` | `RANGED_CONTACT` |
| local melee commitment | `STABLE` | `PRESSURED` | `COMBINED_ENGAGEMENT` |
| local crisis | `LOCAL_CRISIS` | `PRESSURED` | `CRISIS_STABILIZATION` |
| enemy break | `LOCAL_CRISIS` | `BREAKING` | `CRISIS_STABILIZATION` |
| enemy rout majority | `RECOVERY_REQUIRED` | `ROUT_CASCADE` | `TERMINATE_WITH_PRESERVATION` |
| victory countdown | `RECOVERY_REQUIRED` | `TERMINAL_COUNTDOWN` | `TERMINATE_WITH_PRESERVATION` |
| battle complete | `TERMINAL` | `TERMINAL` | no actionable decision window |

Battle 4 never enters `IRREVERSIBLE_COLLAPSE`. The evaluator therefore distinguishes a severe but recoverable local crisis from terminal defeat.

## Plausible loss-prevention findings

Eleven local units satisfy the dense corpus's severe-degradation condition. The evaluator separates them into:

- 4 `PLAUSIBLY_PREVENTABLE_SEVERITY` diagnoses;
- 7 `INSUFFICIENT_EVIDENCE_OF_PREVENTABLE_SEVERITY` diagnoses.

The four plausible cases are:

- Reiksguard: a cavalry disengagement window appeared at 291.1 seconds with 309.0 seconds of later observed trace and recoverability proxy `0.465891`;
- Karl Franz: a commander extraction window appeared at 402.1 seconds with 337.5 seconds of later observed trace and recoverability proxy `0.459139`;
- Fire Wizard: a commander extraction window appeared at 531.1 seconds with 208.5 seconds of later observed trace and recoverability proxy `0.467474`;
- one ranged unit: a repositioning window appeared at 402.1 seconds with 337.5 seconds of later observed trace and recoverability proxy `0.580193`.

These are diagnoses, not causal claims. The evaluator does not state that an alternative would definitely have saved the unit or improved the battle.

The Mortar is deliberately not promoted to a plausible-prevention claim. Its first selected evacuation warning occurs after the recoverability proxy has fallen to `0.068604`. This supports an earlier-protection hypothesis but does not establish that extraction remained feasible at the observed crisis point.

## Deterministic architecture result

The milestone establishes:

- a visibility-safe tactical-state schema;
- role-specific preservation thresholds;
- support and visible-pressure measurements;
- danger, asset-value, recoverability, collapse-risk, and marginal-engagement utilities;
- local-stability and visible-enemy-collapse state machines;
- explicit commander, artillery, ranged, cavalry, frontline, morale, reserve, pursuit, and reformation opportunities;
- bounded per-slice advisory workload;
- outcome-independent tactical-quality dimensions;
- explicit deferral of behavior trees, HTN/search, and learning.

## Validation

- 34 SyntheticLab tests passed;
- 60 Runtime Probe tests passed;
- 94 total tests passed;
- 177 canonical repository files passed SHA-256 validation;
- Python compilation completed for the modified lab and existing probe tooling;
- both v0.1M JSON artifacts were rebuilt twice and were byte-identical;
- both rebuilds matched the committed canonical artifacts exactly;
- no runtime-probe pack, WH3 file, save, Workshop item, or remote GitHub state changed.

## Remaining uncertainty

Not established:

- that any proposed alternative would reduce casualties;
- terrain-aware withdrawal routes;
- WH3 pathfinding or formation execution;
- command acceptance or success;
- ordinary live campaign-battle generalization;
- siege, ambush, reinforcement, monster/flying, artillery-heavy, and SFO behavior;
- calibration of utility weights across factions and unit scales.

## Next step

The next offline step is adversarial expansion of the state/opportunity contract beyond Battle 4 using synthetic perturbations and future heterogeneous observed battles. The next live condition remains append-log continuity across campaign → battle → campaign, preferably batched with a broad vanilla/SFO compatibility session.
