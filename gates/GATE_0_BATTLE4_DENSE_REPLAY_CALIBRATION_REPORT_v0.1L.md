# Gate 0 — Battle 4 dense replay calibration report v0.1L

## Classification

- Dense Battle of Eilhart observation: `OBSERVED`
- Overall result: `OBSERVED_DENSE_SELECTION_LIMITING_RESULT`
- Direct selected-unit replay callback: `LIMITING_RESULT`
- Bounded state-matching attribution: `INFERRED_NOT_ACKNOWLEDGED`
- Offline tactical shadow evaluator: `HYPOTHESIS`, authority `NO_ORDERS`

No additional Battle 4 replay is required for the current gate.

## Frozen owner-machine evidence

- battle: Battle of Eilhart — Reikland vs Empire Secessionists;
- replay SHA-256: `76b8807f5cc2d223d454028f54fc18b791a254c3ce543aa587ad4286658e302b`;
- corrected dedicated replay-pack SHA-256: `6e3f8e7bbc7d66754a7fa764c802e2b5599d13e83820e0785cb85d738040f66d`;
- dense log SHA-256: `ad9a233b667c61f934aaba056c139867f1446afb1cc3a0e5ebfd4a0579a5d64d`;
- dense log size: 11,832,720 bytes;
- verification result digest: `a8f9e724d0c86cbff82af0a48842eb4e257356186a895b67f2660e6ddaba59d8`;
- summary result digest: `cc75f626329f3ceae381d30a4dc17743b111cd06088a3d6b8b1fbc2def9fde8f`.

The exact installed, staged, and expected pack hashes matched. The exact replay matched. No parse error occurred.

## Dense continuity result

The complete 739.6-second replay produced:

- 249 detail samples against 247 expected;
- coverage ratio `1.008097`;
- maximum detailed-sample gap 3.4 seconds;
- 1,477 alliance aggregate records;
- 120 sampler heartbeats;
- 739 model-time callback ticks;
- 1,206 real/UI-time callback ticks;
- 37 stable canonical units;
- zero identity aliases;
- 397 command events;
- 10,643 structured records total.

This closes the sparse-sampling defect from the first capture. Time-series interpretation is now permitted for this replay under the declared density and maximum-gap contract.

## Authority boundary

The evidence records all of the following as false:

- orders emitted;
- unitcontrollers created;
- battle speed modified;
- save values written;
- visibility modified.

The replay establishes observation and calibration only. It does not establish command acceptance, pathfinding success, causal effectiveness, tactical superiority, ordinary live campaign-battle equivalence, or SFO compatibility.

## Selection and command attribution

The corrected per-unit selection callback registration emitted no selection events during replay playback. This is preserved as a replay-specific limiting result rather than generalized to all ordinary battles.

The bounded state matcher produced candidate attributions for 302 of 397 commands, including 121 high-confidence candidates. These records are weak labels only and remain explicitly `INFERRED_NOT_ACKNOWLEDGED`.

## Outcome lower bounds

The dense corpus conservatively records:

- at least 742 local casualties;
- at least 1,388 visible-enemy casualties;
- local observed-kill maximum sum 1,379;
- local terminal coverage 64.7059%;
- visible-enemy terminal coverage 75%.

Exact totals remain withheld because units can leave the observed hierarchy before the terminal sample.

## Tier 4R calibration artifacts

### Dense corpus

`synthetic_lab/corpora/battle4_eilhart_observed_dense_v2.json`

Result digest:

`442e187638c4d2b3457910efdbb50d13f16fd27a8391e7ac9bd2d6aaed47c33d`

### Visibility-safe trace slices

`synthetic_lab/corpora/battle4_eilhart_trace_slices_v1.json`

Result digest:

`ccb23dc2e24102b53c5833ecae9047ebfd449476cd0508aacd4ec0fd6dc56360`

The eight slices cover deployment complete, first contact, local melee commitment, local crisis, enemy break, enemy rout majority, victory countdown, and battle completion. Foreign unit details are retained only when marked visible to the local alliance.

### Tactical trace benchmark

`research/runtime_evidence/BATTLE4_EILHART_TACTICAL_TRACE_BENCHMARKS_v0.1L.json`

Result digest:

`b3364537be82cd96ef760db7c9e767fdd96a159f8ca87722a554779b87a8ca13`

The benchmark freezes six evaluation episodes without declaring the owner trace optimal:

- deployment and reserve design;
- ranged contact and target priority;
- melee commitment control;
- local crisis triage;
- enemy-break exploitation;
- rout-cascade termination.

### Offline tactical shadow evaluator

`research/runtime_evidence/BATTLE4_EILHART_OFFLINE_SHADOW_EVALUATION_v0.1L.json`

Result digest:

`1d5892cf47c900e1bbe1eeae09466a28500abd3a735e1f332776f42f82606742`

The evaluator is deterministic, consumes only frozen observed slices, has authority `NO_ORDERS`, and remains `HYPOTHESIS`. It identifies deployment uncertainty, ranged-contact posture, melee commitment, crisis stabilization, asset preservation, and pursuit termination.

## Tactical calibration findings

Battle 4 is a useful pyrrhic-loss benchmark because victory was paired with severe asset degradation:

- frontline casualty lower bound 457 of 720 models;
- ranged casualty lower bound 203 of 450 models despite 482 observed kills;
- Reiksguard casualty lower bound 44 of 60 models;
- Mortar casualty lower bound 38 of 44 models;
- Karl Franz ended near 16% health;
- the Fire Wizard ended near 13% health;
- the two Master Engineers produced 314 observed kills combined while remaining near 80% health.

The resulting planner invariants emphasize preserving productive assets, detecting morale collapse, protecting artillery, disengaging cavalry, terminating pursuit when marginal value falls, respecting hidden information, and using bounded explainable command budgets instead of imitating human click density.

## Capability promotions and rejections

Promoted to observed:

- replay-safe dual-clock callback continuity;
- dense three-second unit sampling;
- one-second alliance aggregation;
- heartbeat monitoring;
- stable unique-unit identity;
- local and visibility-filtered enemy trajectories;
- terminal-coverage reporting;
- complete read-only replay observation.

Preserved as limiting or unverified:

- direct selected-unit callback events during replay playback;
- accepted or executed command attribution;
- battle-order authority;
- tactical-AI quality;
- generalization beyond this vanilla land battle;
- SFO compatibility.

## Remaining gate work

No owner action is required for Battle 4. The next offline step is adversarial refinement of the `NO_ORDERS` tactical shadow evaluator against the frozen slices. The next live campaign condition is append-log continuity across campaign → battle → campaign, which should be batched with a later broad vanilla/SFO compatibility session.
