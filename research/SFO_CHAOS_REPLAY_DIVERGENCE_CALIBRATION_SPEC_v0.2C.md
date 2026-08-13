# SFO Chaos Replay Divergence Calibration Specification v0.2C

## Purpose

Adjudicate the exact `An Ogre's Folly` SFO replay capture without converting replay-stream exhaustion into a completed defeat. The source is useful for nonterminal state recognition, crisis timing, lower-bound loss diagnosis, and replay-lifecycle hardening. It is excluded from terminal-outcome, defeat-grade, tactical-superiority, and optimal-policy labels.

## Exact source binding

- private bundle SHA-256: `18293f7f59fc9a2130a6c82ec48636097c946605d49980cfcb0f154a8c1a6126`;
- replay SHA-256: `28d780d02f2af07fe16fe4a24a27cd37f41bdb870d485f11949d5ed63f838cb5`;
- recording SHA-256: `6e008c378a8e4273ca7d2c8101ca69279839a5c21dbaf749fb5e666adde56155`;
- raw log SHA-256: `2175b2643f80b7e7fde9edd66443df1b8b5f2205ec3aad51fab013d48a686c0c`;
- public-safe dense corpus SHA-256: `bafc5884ea01c5d05e472423c41989ed5c23559d9365f07d2d608f5ed89797ef`;
- dense result digest: `4d84f49ec1782d29e872eff6674e93af089c3290a765b5d20c95b815ee70cea4`;
- public capture fixture digest: `3febf48a92ce7309d912634b1540d29e1051a30835622b847b8da360aa6e74dc`;
- unit-findings digest: `12609e324eec28eed50ee2d79ca3e42d3f71787597d2ce28362257bbb40c7ae0`.

No replay, recording, frame, raw log, private report, save, pack, personal path, or game asset is committed.

## Lifecycle adjudication

The exact environment and dense observer stream are valid, but the replay did not emit `BATTLE_COMPLETE`:

- schema-2 detail samples: 115;
- aggregate records: 637;
- canonical units: 23;
- command events: 89;
- dense duration: 338.5 seconds;
- terminal unit coverage: 0% local and 0% visible enemy;
- natural completed battle count: 0.

The recording shows WH3's replay-end overlay (`Load Replay`, `End Battle`). The subsequent zero-loss summary is a replay-exit artifact and not the original battle result. Classification:

`REPLAY_COMMAND_STREAM_EXHAUSTED_WITHOUT_BATTLE_COMPLETE`

Original live outcome remains `OWNER_ATTESTED_DEFEAT`; exact grade remains `UNVERIFIED`. Replayed simulation outcome is `UNVERIFIED_NONTERMINAL`.

## Supported nonterminal findings

- elite cavalry preservation failure: Zintler's Reiksguard lost at least 58 of 60 models while recording one observed kill;
- Tattersouls local collapse: at least 159 of 160 models lost before the stream ended;
- artillery early crisis: both Helstorm batteries engaged at 49.4 seconds and first routed near 182–185 seconds;
- delayed or uneven reserve commitment: one Halberdier unit engaged at 140.1 seconds and lost at least 69 models, while the second first engaged at 212.1 seconds and lost two;
- commander crisis: Elspeth and the Empire Captain both routed during the observed stream and ended at low hitpoint fractions;
- enemy pressure: Archaon recorded 99 observed kills and remained at 66.75% health; Chaos Knights recorded 117 kills for one casualty.

These findings do not prove causality, preventability, or a winning alternative.

## Policy boundaries

1. Never learn outcome, grade, irreversibility, or terminal casualties from replay exhaustion.
2. Distinguish reserve absent, available, committed late, and unable to support.
3. Permit an elite-asset preservation warning from extreme lower-bound losses, but route any proposal through legality and feasibility gates.
4. Treat concentrated command traffic on Archaon as a review hypothesis only because selection attribution is absent.
5. Use this trace for state and crisis recognition only; exclude it from terminal policy labels.

## Runtime hardening

- incomplete battle reports emit `UNVERIFIED_INCOMPLETE_SESSION`, never `OBSERVED`, for terminal outcome;
- after WH3 exits, the capture process performs bounded consecutive-read stabilization to preserve late filesystem appends;
- process exit and stable log bytes are never promoted to `BATTLE_COMPLETE`.

## Authority

`NO_ORDERS`. Command events remain observed traffic, not acknowledgement, execution, or causal proof.
