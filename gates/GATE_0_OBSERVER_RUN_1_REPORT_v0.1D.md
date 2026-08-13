# Gate 0 Observer Run 1 Report — v0.1D

## Segment result

**Closed:** the first real pure-vanilla campaign observer execution and evidence adjudication.

**Gate 0 remains open:** the acceptance gate requires a second independent observer run, a disposable-save persistence round trip, expanded observation fields, and the remaining baseline/capability conditions.

## Observed

WH3 loaded the script-only observer pack and produced structured `ModLog` records in a fresh Karl Franz Immortal Empires campaign.

The session contained:

- one pack-load record;
- one first-tick callback;
- two complete snapshots;
- one local field army in each snapshot;
- two local regions in each snapshot;
- 23 total foreign-character observations;
- 20 total visible-region observations;
- no capability failure records.

## Lifecycle limiting result

The first-tick snapshot was not equivalent to the local-faction-turn-start snapshot:

- visible characters: 10 → 13;
- visible regions: 9 → 11;
- own field armies: 1 → 1;
- own regions: 2 → 2;
- wars: 2 → 2.

Therefore first tick is retained only for diagnostics. Local-faction turn start is canonical planner timing.

## Capability promotions

Promoted to `OBSERVE`/`OBSERVED`:

- script-only campaign pack loading;
- project `ModLog` output;
- first-tick callback;
- local-faction-turn-start snapshot;
- local army and region enumeration;
- game-interface-filtered foreign character and region enumeration.

Not promoted:

- complete Army Objective Assignment observation contract;
- save/reload persistence;
- campaign objective influence or control;
- order acknowledgement or outcome;
- generated or ordinary battle control;
- UI authority.

## Defect remediation

The parser's session-wide duplicate counter was incorrect for repeated observations across time. The same raw evidence now yields zero true duplicate records and eight normal cross-snapshot repeats.

The probe scripts also define inert filename-matched entrypoints so the next WH3 run should no longer print `transcendence_*_probe() not found, continuing`.

## Smallest unavoidable next task

Install the newly built v0.1D observer pack, run a second fresh pure-vanilla Karl Franz campaign to local-faction turn start, collect the log, and verify:

1. the loader warning is absent;
2. the observer capability result repeats;
3. within-snapshot duplicate count remains zero;
4. lifecycle timing remains explicit.

After that, run the separate persistence probe only on a disposable save.
