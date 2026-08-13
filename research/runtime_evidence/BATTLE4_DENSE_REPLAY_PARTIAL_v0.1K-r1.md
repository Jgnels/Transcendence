# Battle 4 dense replay partial result — v0.1K-r1

**Evidence label:** `LIMITING_RESULT`  
**Battle:** Battle of Eilhart — Reikland vs Empire Secessionists  
**Replay SHA-256:** `76b8807f5cc2d223d454028f54fc18b791a254c3ce543aa587ad4286658e302b`  
**Pack SHA-256:** `185baaa832beb458797e47766a3ad121530cdcf811097e8eb90d787df50c8443`  
**Captured log SHA-256:** `35fe20fdfecd37d4abab4652cb9cef08eedc3e96bbcc1eb5fad9ed51ec438c00`

## What succeeded

The exact replay and exact pack were verified. The pack loaded, the full 739.6-second replay completed, stable schema-2 identities were emitted, 34 canonical units were observed with zero identity aliases, 397 command events were captured, and read-only authority remained intact.

Offline reprocessing after correcting the parser recovered:

- one complete replay session;
- 17 local canonical units;
- 17 visible-enemy canonical units;
- 489 local casualty lower bound;
- 1,096 visible-enemy casualty lower bound;
- 1,141 local observed-kill maximum sum;
- all five phase-boundary samples;
- deployment changes and the complete command stream.

## Why the original processor rejected valid data

The runtime intentionally emitted `UNIT_HIERARCHY` immediately before the first `UNIT_STATIC` for each stable unit. The parser incorrectly required static data first. The corrected parser permits that discovery ordering but still rejects any hierarchy identity that never receives a static record.

## Why dense sampling did not start

The log contains no `SAMPLER_START`, no `SAMPLER_HEARTBEAT`, no `ALLIANCE_AGGREGATE`, and reports zero model and real ticks. Only five phase samples exist, versus 247 expected.

The source defect is deterministic:

```lua
math.max(0, trans_battle_safe(...))
```

`trans_battle_safe` returns two Lua values: the queried value and an availability boolean. Because the call was the final argument to `math.max`, Lua expanded both values. `math.max` therefore received a boolean where it required a number. The initial aggregate incremented its counter, then setup aborted before either repeating callback was registered and before `SAMPLER_START` could be emitted.

v0.1K-r1 stores aggregate values in locals, normalizes them with `tonumber`, registers and discloses both clocks before the initial aggregate, and wraps setup in a required-capability failure guard.

## Evidence status

| Claim | Status |
|---|---|
| Exact replay and pack | `OBSERVED` |
| Complete replay | `OBSERVED` |
| Stable unit identity | `OBSERVED` |
| Local and visible-enemy unit access | `OBSERVED` |
| Terminal outcome lower bounds | `OBSERVED` |
| Command stream | `OBSERVED` |
| Read-only authority | `OBSERVED` |
| Dense interval coverage | `LIMITING_RESULT` |
| Continuous tactical timing | `INVALIDATED_BY_SPARSE_SAMPLING` |
| Selection attribution | `UNVERIFIED` |

The replay does not need to be manually refought. One further playback with the corrected pack is required only to prove continuous interval sampling and selection/inference behavior.
