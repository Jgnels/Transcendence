# Gate 0 — Battle 4 dense replay sampler hotfix v0.1K-r1

## Classification

`LIMITING_RESULT` for the first dense replay pass; corrected replay pack prepared offline.

## Preserved live evidence

- exact Battle of Eilhart replay verified;
- exact v0.1K replay pack verified;
- complete 739.6-second battle and result observed;
- 34 canonical schema-2 units, zero identity aliases;
- 397 command events;
- read-only authority preserved;
- captured log SHA-256 `35fe20fdfecd37d4abab4652cb9cef08eedc3e96bbcc1eb5fad9ed51ec438c00`.

## Defects

1. The parser rejected valid `UNIT_HIERARCHY → UNIT_STATIC` discovery ordering.
2. The initial aggregate expanded `trans_battle_safe`'s two Lua returns into `math.max`, causing a numeric type error.
3. Setup ended before `SAMPLER_START`, repeat callbacks, heartbeats, aggregate records, and selection callbacks.

## Corrections

- pending hierarchy identities are allowed and reconciled;
- unresolved hierarchy identities remain fatal;
- aggregate values are normalized with `tonumber` before arithmetic;
- both model and real callbacks are registered before the initial aggregate;
- `SAMPLER_START` is emitted before aggregation;
- setup failures emit required capability `battle.setup`;
- a synthetic partial fixture reproduces the exact structural failure;
- dense verification now classifies the first pass as partial rather than unparseable.

## Remaining live condition

Play the preserved replay once with the corrected dedicated replay pack and prove:

- nonzero model or real callback ticks;
- sampler heartbeats;
- interval detail samples and alliance aggregates;
- maximum detail gap within the declared bound;
- selection callbacks or explicitly bounded inference.

No manual refight is required.
