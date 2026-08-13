# SFO Chaos Defeat Capture Specification v0.2B

## Purpose

Bind the owner-recorded Reikland defeat against Warhost of the Apocalypse to the exact replay binary and prepare one read-only schema-2 telemetry capture. This is a negative-outcome calibration source, not a demonstration of optimal play and not evidence that any alternative would have won.

## Exact private inputs

- replay display title: `An Ogre's Folly`;
- battle type: land battle;
- local faction: Reikland / The Empire;
- enemy display: Warhost of the Apocalypse / Warriors of Chaos;
- replay SHA-256: `28d780d02f2af07fe16fe4a24a27cd37f41bdb870d485f11949d5ed63f838cb5`;
- replay size: 86,067 bytes;
- recording SHA-256: `6e008c378a8e4273ca7d2c8101ca69279839a5c21dbaf749fb5e666adde56155`;
- recording: 389.533 seconds, 1920×1080, 30 FPS;
- replay and recording bytes remain private and excluded.

## Current evidence

Observed visually or in the replay binary:

- exact display identity and factions;
- broad phase sequence from deployment through terminal defeat;
- embedded labels including Archaon, Chaos Giant, Chaos cavalry/chariots, Elspeth, artillery, ranged, infantry, and cavalry elements;
- the recording is consistent with a defeat, but it does not show a normal result card.

The exact defeat grade therefore remains `UNVERIFIED`; the defeat outcome is `OWNER_ATTESTED_DEFEAT_VISUALLY_CONSISTENT` rather than promoted to visually observed.

## Bounded visual hypotheses

The visual preparation preserves five hypotheses for telemetry adjudication:

1. formation-support failure;
2. absence or premature use of a tactical reserve;
3. piecemeal commitment;
4. firing-lane degradation after melee congestion;
5. failure to establish a regroup, fallback, or asset-extraction state.

These are not causal conclusions and are not labels for the correct policy.

## Required dense evidence

One exact replay playback must capture:

- stable local and enemy unit identity;
- health, model count, fatigue, morale, ammunition, and routing trajectories;
- exact engagement, wavering, route, rally, and shatter timing;
- observed command events, targets, and bounded inferred attribution;
- role-specific casualties, kills, travel, and exposure;
- battle-complete marker and victorious alliance;
- exact SFO and read-only observer environment.

## Observer-container rule

The preferred active container is `transcendence_battle_replay_probe.pack` SHA-256 `6e3f8e7bbc7d66754a7fa764c802e2b5599d13e83820e0785cb85d738040f66d`.

The exact frozen `transcendence_shadow_probe.pack` SHA-256 `0714863e2081206aa7d0790ec14d7c3c3c7ae33eea416d72dba0d6a2ecd0a89e` is accepted only as `SCRIPT_EQUIVALENT_SHADOW_PACK`, because both containers include the byte-identical battle observer script SHA-256 `86e18ec655c4a45a4a062d1dae7d10e6fd9a1cb77af5557757fbca9ed896562e`. Any other container, duplicate observer entry, extra active mod, or hash change fails closed.

## Authority

- no unit controllers;
- no orders;
- no battle-speed changes;
- no save writes;
- no visibility changes;
- command events are not acknowledgement;
- visible movement is not causal execution;
- owner play is not an optimal-policy label.
