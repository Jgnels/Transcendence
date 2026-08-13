# Native/SFO Matched Behavior Benchmark Preregistration — v0.2O

Status: **FROZEN BEFORE SFO OWNER DATA**

## Purpose

Acquire one fresh SFO Grimhammer III cohort under the same Karl Franz / Immortal Empires / Legendary / Very Hard / normal-play protocol used by v0.2N and compare research-only diagnostic behavior against the hash-frozen vanilla reference.

This is a benchmark, not randomized causal identification. SFO changes many campaign systems, so observed differences cannot be attributed to any single DB row without later ablation.

## Source identities

Vanilla reference bundle SHA-256:

`9416e0b73765570e6ffda1c1855a0430133b447e14cd63d307c966312987429d`

Vanilla v0.2N result digest:

`ebe747ca69a8b7da86586a7ea6759d65e2f81f5128cf45917fd9c41c495a8542`

SFO Workshop ID:

`2792731173`

Pinned owner-verified SFO pack name / SHA-256 from the 2026-08-02 Native CAI acquisition:

`sfo_grimhammer_3_main.pack`

`ae20a0a08037aa3ebcbe7461d2589fc28dc15a5fe5d9ca4c0a9d0ff0a26da603`

If the owner SFO pack hash differs, the SFO study fails closed and must be re-bound/reconciled before collection.

## Campaign protocol

- new disposable Karl Franz / Reikland Immortal Empires campaign;
- Legendary campaign difficulty;
- Very Hard battle difficulty;
- normal player actions allowed;
- autoresolve allowed;
- exactly SFO main pack + `transcendence_native_diagnostic_probe.pack` enabled; no other mods;
- at least 11 consecutive Reikland turn-start markers (10 full AI cycles);
- same privileged research telemetry remains `application_eligible=false` and `NO_ORDERS`.

## Base endpoints retained unchanged

The complete v0.2N behavior evaluator is retained unchanged and reported in full.

Base frozen threshold digest:

`4499a497bfc7dd6a33a6c0a50da4e1e52b1705d1f2f20f1a917cdfebeb5486ac`

### Recovery

- recovering threshold: start-of-own-turn average unit health <65%;
- minimum exposure: 10 damaged army-turns;
- positive signal requires >=2 attacker-side re-entry army-turns and >=20% attacker-side rate;
- defender-side participation is not promoted to offensive re-entry.

### Temporal

v0.2N stable-context/battle-free/direction thresholds are retained exactly:

- consecutive turn-end observations;
- war set unchanged;
- owned-region set unchanged;
- stance unchanged;
- health range <=5 percentage points;
- strength ratio <=1.10;
- unit-count range <=1;
- both movements >=5 campaign-coordinate units;
- no recorded battle involving the force between endpoints;
- heading reversal >=120 degrees (cosine <= -0.5);
- repeated signal requires two non-overlapping qualifying reversal episodes for the same force or the existing exact A-B-A-B-A route signal.

## Prospectively frozen population split

### Primary strategic population — TERRITORIAL

A temporal window is territorial when the stable owned-region set is **non-empty** throughout the window.

This population is primary because ordinary strategic CAI is responsible for defending/expanding territorial factions, whereas the sole repeated vanilla trigger was a non-territorial fixed-route Rogue Pirate patrol.

Primary temporal exposure is sufficient only at >=20 eligible territorial windows.

### Secondary population — NON-TERRITORIAL

Stable owned-region set is empty throughout the window. Report the same metrics separately. Do not mix these windows into the primary strategic interpretation.

## Hash-frozen vanilla reference values

These subgroup values are retrospective for vanilla and therefore **reference-only**, but their definitions are frozen before SFO data:

- territorial: 48 eligible, 13 reversal candidates, rate 0.270833, 0 repeated forces;
- non-territorial: 58 eligible, 5 reversal candidates, rate 0.086207, 1 repeated force;
- recovery: 38 damaged army-turns, 6 attacker-side reentries, rate 0.157895, no preregistered recovery signal.

## SFO interpretation

Report:

1. full sealed v0.2N endpoint result;
2. territorial eligible windows, reversal candidates/rate and repeated-force count;
3. non-territorial equivalents;
4. recovery exposure and attacker-side re-entry rate;
5. descriptive SFO-minus-vanilla rate deltas.

Allowed conclusions:

- `INSUFFICIENT_EXPOSURE`;
- `NO_REPEATED_TERRITORIAL_REVERSAL_SIGNAL_IN_COHORT`;
- `REPEATED_TERRITORIAL_REVERSAL_SIGNAL_OBSERVED`;
- unchanged v0.2N recovery statuses;
- descriptive profile difference requiring causal/mechanistic review.

Forbidden conclusions:

- “SFO proves row X fixes native AI” without a later narrow ablation;
- “no signal means native/SFO hysteresis is generally good”;
- any use of privileged diagnostic state by the application;
- direct revival of project-owned strategic planning or v0.2G/v0.2I.

## Architecture rule

No SFO result changes application authority. A credible profile difference may only earn a **narrow row/mechanism ablation design** that is separately preregistered and tested.
