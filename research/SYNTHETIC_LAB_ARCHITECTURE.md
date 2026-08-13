# SyntheticLab Architecture — v0.1B

## Purpose

SyntheticLab makes strategic and tactical hypotheses cheap to falsify before any policy gains authority in WH3. It does not claim to recreate WH3. Every result declares its tier, fidelity label, profile, scenario digest, seed, controller revision, and evidence status.

## Tier 0 — Contract and determinism lab

Validates schemas, rejects prohibited private fields, filters hidden enemy armies, canonicalizes inputs, and proves repeatable digests.

**Authority:** structural only.

## Tier 1 — Decision lab

Generates and scores `DEFEND_REGION`, `RELIEVE_SIEGE`, `ATTACK_ARMY`, `CAPTURE_REGION`, `REPLENISH`, and `HOLD` candidates. It emits one objective per controlled army with component scores, rationale, and alternatives.

**Authority:** decision-quality hypothesis only.

## Tier 2 — Operational campaign surrogate

Rolls abstract campaign state forward under seeded uncertainty. It measures objective churn, hold rate, captures, battle count, controlled regions, and surviving armies.

**Authority:** uncalibrated comparative surrogate.

## Tier 3 — Ensemble lab

Runs Tier 2 across explicit seeds and reports mean, median, p10, p90, minimum, and maximum. It is intended to reveal brittle policies and favorable-seed overfitting.

**Authority:** uncertainty analysis over Tier 2; inherits every Tier 2 limitation.

## Tier 4 — Tactical battle surrogate

Exercises target selection, frontline/ranged/artillery/cavalry/reserve roles, ammunition, reserve timing, morale, idle actions, and deterministic damage resolution.

**Authority:** contract and regression testing only until calibrated against observed WH3 battles.

## Reality Gate R0

R0 is a future live-game shadow observer. It records what Transcendence would recommend, what the game actually does, and what happens next without mutating the campaign.

No synthetic result may be presented as real-game performance evidence. No policy may gain authority without a proven capability classification of `CONTROL` or `INFLUENCE` and R0 evidence.

## Environment profiles

- `vanilla_wh3_8_1_1_build_48122_4194776`: current owner-observed settings baseline.
- `deepwar_reference_unverified_2978779730`: reference-only table profile.
- `hecleas_reference_unverified_2905096541`: reference-only table profile.
- `sfo_reference_unverified_2792731173`: optional compatibility template.

The core never assumes any optional profile is present. A profile hash change revokes certification.

## Reproducibility contract

Every result contains:

- schema version;
- tier and fidelity label;
- scenario/profile identifiers and digests;
- seed or seed ensemble;
- decisions, explanations, metrics, and warnings;
- final/result digests;
- evidence status.

## Implementation boundary

v0.1B uses only the Python standard library. It has no game-write capability, no network access, no self-modification, and no third-party runtime dependency.


## Tier 4R — Observed battle reality regression

Tier 4R is neither the Tier 4 surrogate nor a learned imitation dataset. It stores public-safe derived evidence from a real WH3 battle and uses it to constrain future tactical systems.

Battle of Eilhart currently supplies:

- one full dense observed corpus;
- eight visibility-safe unit-state slices;
- deterministic stress cases for commander danger, frontline collapse, ranged preservation, cavalry overextension, artillery loss, rout cascades, hidden information, and incomplete terminal coverage;
- a deterministic offline adviser that emits no orders and labels every output `HYPOTHESIS`.

Tier 4R may invalidate unsafe assumptions and compare candidate evaluators. It may not establish tactical superiority, command authority, SFO compatibility, or a universally optimal action.

## Tier 4R-SHADOW — Offline tactical assessment

The first shadow evaluator consumes one observed slice and produces:

- a global posture;
- bounded local preservation priorities;
- visible-only target candidates;
- a maximum priority-change budget;
- rationale and authority labels.

It has no WH3 runtime dependency and no game-write path. Promotion beyond offline hypothesis requires a later live shadow-adviser probe, then a separate order-authority sandbox.

## v0.1R action-authority contract layer

`TACTICAL_ACTION_AUTHORITY_EVIDENCE_PACKET_V1` tests the separation between event observation, unresolved origin, local selection binding, point reachability, state matching, interruption, acknowledgement, and outcome. The 12-scenario matrix includes valid state evidence and fail-closed issue, acknowledgement, and hidden-target cases. Battle 4 is used only to freeze the existing limiting boundary; it is not reinterpreted as acknowledged command execution.
