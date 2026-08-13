# Battle 4 dense replay analysis — v0.1L

**Battle:** Battle of Eilhart — Reikland vs Empire Secessionists  
**Evidence:** `OBSERVED_DENSE_SELECTION_LIMITING_RESULT`  
**Duration:** 12:19  
**Replay SHA-256:** `76b8807f5cc2d223d454028f54fc18b791a254c3ce543aa587ad4286658e302b`  
**Dense log SHA-256:** `ad9a233b667c61f934aaba056c139867f1446afb1cc3a0e5ebfd4a0579a5d64d`

## Gate result

The corrected replay pass succeeded. The exact replay and exact pack were verified, the complete result was observed, and the probe remained read-only.

- 10,643 structured events;
- 249 detailed samples against 247 expected;
- coverage ratio 1.008097;
- maximum detailed-sample gap 3.4 seconds;
- 1,477 alliance aggregate records;
- 120 sampler heartbeats;
- 37 stable canonical units;
- zero identity aliases;
- 397 command events.

The dense observation gate is closed. The only limiting sub-result is direct selected-unit attribution during replay playback.

## What the battle actually looked like

This was a pyrrhic-shaped victory, not merely a high-casualty result. Reikland's heroes and missile line generated enormous output while the infantry screen, cavalry, artillery, and two key characters approached collapse.

Conservative observed lower bounds:

- Reikland casualties: at least **742**;
- visible-enemy casualties: at least **1388**;
- local per-unit observed-kill maximum sum: **1379**;
- local terminal coverage: **64.7%**;
- visible-enemy terminal coverage: **75.0%**.

Exact totals remain unavailable because several units left the observed hierarchy before the terminal sample.

## Tactical timeline

| Milestone | Time | Hidden enemies | Local state | Visible enemy state |
|---|---:|---:|---|---|
| `deployment_complete` | 2:08 | 6 | 1258 models; 0 melee; 0 routing | 1530 visible models; 0 melee; 0 routing; 0 shattered |
| `first_contact` | 2:21 | 2 | 1258 models; 0 melee; 0 routing | 1861 visible models; 0 melee; 0 routing; 0 shattered |
| `local_melee_commitment` | 4:51 | 4 | 1256 models; 1 melee; 0 routing | 1437 visible models; 0 melee; 1 routing; 0 shattered |
| `local_crisis` | 6:42 | 0 | 1070 models; 10 melee; 1 routing | 1501 visible models; 12 melee; 3 routing; 0 shattered |
| `enemy_break` | 8:51 | 0 | 740 models; 4 melee; 3 routing | 993 visible models; 8 melee; 7 routing; 1 shattered |
| `enemy_rout_majority` | 9:15 | 0 | 684 models; 2 melee; 3 routing | 901 visible models; 4 melee; 9 routing; 2 shattered |
| `victory_countdown` | 12:10 | 0 | 475 models; 0 melee; 2 routing | 524 visible models; 0 melee; 15 routing; 12 shattered |
| `battle_complete` | 12:19 | 0 | 473 models; 0 melee; 2 routing | 524 visible models; 0 melee; 15 routing; 15 shattered |

Interpretation:

1. **Deployment completed at 2:08.8.** Six enemy units were still hidden.
2. **Observed missile contact began by 2:21.1.** Only two enemy units remained hidden.
3. **The local line entered melee at 4:51.1.** Two Master Engineers had appeared as additional local units by 4:09.1, consistent with reinforcement arrival.
4. **The local crisis began around 6:42.1.** One local unit was routing while ten local units were in melee, nine were under missile pressure, and five were flank-threatened.
5. **The first enemy shatter appeared at 8:51.1.**
6. **A majority rout was visible at 9:15.1.** Nine of eighteen observed enemy units were routing.
7. **Victory countdown began at 12:10.7.** All fifteen still-observed enemy units were routing; twelve were shattered.
8. **The result completed at 12:19.6.**

## Role-level outcome

| Local role | Units | Initial models | Casualty lower bound | Casualty ratio | Observed-kill max sum | Ammo spent lower bound |
|---|---:|---:|---:|---:|---:|---:|
| Frontline | 6 | 720 | 457 | 63.5% | 296 | — |
| Ranged | 5 | 450 | 203 | 45.1% | 482 | 6150 |
| Characters | 4 | 4 | 0 | — | 474 | 29 |
| Cavalry | 1 | 60 | 44 | 73.3% | 69 | — |
| Artillery | 1 | 44 | 38 | 86.4% | 58 | 37 |

The clearest tactical pattern is **damage concentration backed by asset sacrifice**:

- four of six frontline units lost at least half their models;
- the frontline lost at least 457 of 720 models while producing 296 observed kills;
- the five ranged units produced 482 observed kills but still lost at least 203 of 450 models;
- Karl Franz ended near 16% health;
- the Fire Wizard ended near 13% health and spent meaningful time wavering or routing;
- the Reiksguard lost at least 44 of 60 models, travelled roughly 2.26 km, and was routing/shattered at its last observation;
- the Mortar lost at least 38 of 44 models and was routing/shattered at its last observation;
- the two Master Engineers produced 314 observed kills combined while remaining near 80% health.

## Control-load evidence

The replay contains 397 command events:

- median interval: 300 ms;
- 216 intervals under 500 ms;
- 150 targeted attack commands;
- 127 move commands;
- 15 ability commands.

Direct selection callbacks remained absent. The bounded state-change matcher inferred candidates for **302 commands (76.1%)**, including **121 high-confidence inferences (30.5% of all commands)**.

These are useful weak labels, but they are not order acknowledgements. The tactical AI should not imitate a 397-command human trace. It should use a bounded command budget and seek equivalent or better outcomes with fewer, explainable orders.

## SyntheticLab integration

Battle 4 now supports two complementary Tier 4R corpora:

1. `battle4_eilhart_observed_dense_v2`
   - the complete public-safe dense timeline;
   - 37 stable units;
   - one-second alliance curves;
   - three-second unit-state metrics;
   - command and bounded-inference records.

2. `battle4_eilhart_trace_slices_v1`
   - eight visibility-safe state slices;
   - deployment, first contact, melee commitment, local crisis, enemy break, majority rout, victory countdown, and completion;
   - unit-level position, health, models, ammunition, morale, fatigue, target, movement, and flank state.

Six benchmark episodes are derived without treating the owner's actions as gold policy:

- deployment and reserve design;
- ranged contact and target priority;
- melee commitment control;
- local crisis triage;
- enemy-break exploitation;
- rout-cascade termination.

## Planner invariants learned from this battle

- Preserve endangered commanders and productive missile units once marginal engagement value falls.
- Detect local morale collapse before it becomes a rout cascade.
- Protect artillery and provide a cavalry disengagement rule.
- Stop pursuit when exhausted high-value units face more risk than remaining enemy combat value justifies.
- Never consume hidden-enemy state.
- Keep direct command attribution separate from inferred state matching.
- Optimize for bounded, explainable orders rather than reproducing human click density.
- Treat this battle as a calibration anchor, not proof of general tactical superiority or SFO compatibility.

## First offline shadow evaluator

A deterministic, no-order evaluator now runs across all eight observed slices. It does not imitate the recorded command stream or claim optimal policy. It classifies the battle state and emits bounded advisory priorities.

Observed posture sequence:

| Slice | Evaluator posture | Preservation priorities |
|---|---|---:|
| Deployment complete | `DEPLOYMENT_AND_INFORMATION` | 0 |
| First contact | `RANGED_CONTACT` | 0 |
| Local melee commitment | `COMBINED_ENGAGEMENT` | 0 |
| Local crisis | `CRISIS_STABILIZATION` | 8 |
| Enemy break | `CRISIS_STABILIZATION` | 8 |
| Enemy rout majority | `TERMINATE_WITH_PRESERVATION` | 8 |
| Victory countdown | `TERMINATE_WITH_PRESERVATION` | 7 |
| Battle complete | `TERMINATE_WITH_PRESERVATION` | 7 |

This is the first concrete bridge from live WH3 evidence into a tactical decision lab. Its authority is `NO_ORDERS`; its evidence status is `HYPOTHESIS`. Future scoring changes must continue to pass the same observed slices.

## Remaining limits

- Direct selected-unit callback events were not replayed.
- Command acceptance and causal effectiveness are still unproven.
- Exact total casualties are unavailable.
- Enemy state remains visibility-limited before full reveal.
- This is one vanilla land battle, not a siege, ambush, reinforcement-heavy general benchmark, or SFO test.

## Conclusion

No further replay of Battle 4 is required for observation or SyntheticLab calibration. The next productive step is an offline read-only tactical evaluator that consumes the eight reality slices and scores candidate priorities, followed later by a minimal live shadow-adviser pass. No battle orders should be emitted yet.
