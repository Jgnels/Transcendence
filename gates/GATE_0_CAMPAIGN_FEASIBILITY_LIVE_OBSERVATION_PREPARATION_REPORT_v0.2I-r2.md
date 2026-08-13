# Gate 0 Segment — Campaign Feasibility Live Observation Preparation v0.2I-r2

## Result

**PARSER-CONTRACT HOTFIX CLOSED OFFLINE / LIVE OBSERVATION REMAINS OPEN.** The second owner-runtime attempt proved that the v0.2I-r1 real/UI polling timer actually fires (`poll_tick=True`). It then stopped in `WAITING_RETRY_AFTER_PARSE_OR_PIPELINE_ERROR` before `FEASIBILITY_REQUEST_SEEN`, query results, or rejection. Offline code audit found that the sidecar's shared log parser had not been updated to allow the two diagnostic events added in r1.

## Owner-runtime limiting evidence

- collector state: `WAITING_RETRY_AFTER_PARSE_OR_PIPELINE_ERROR`;
- `FEASIBILITY_POLL_TICK`: observed;
- `FEASIBILITY_REQUEST_SEEN`: not observed;
- query result: not observed;
- explicit request rejection: not observed;
- therefore the r1 timer correction is supported in the exact owner runtime, but request transport remains unverified.

Frozen public-safe limiting-result digest: `a581d864bceb8696d07a9756cae40c53ee4f59b4bd65762ec816e0b6a9726ba7`.

## Root cause

`runtime_probe/tools/watch_campaign_feasibility.py` parses the append log through `parse_probe_log.parse_logs`. r1 added `FEASIBILITY_POLL_TICK` and `FEASIBILITY_REQUEST_SEEN` to the Lua emitter but did not add those event names to the shared parser allowlist. The first real poll therefore made the sidecar's next parse fail closed before it could derive/write the live request. The summarized-session validator also lacked `campaign_feasibility` as a valid snapshot-bearing probe kind.

## r2 correction

- allowlists both r1 diagnostic events;
- allows `campaign_feasibility` sessions and their observer-safe snapshots in the generic summary validator;
- adds a regression that extracts every static `trans_probe_emit("...")` event from the feasibility Lua and requires it to be parser-allowlisted;
- adds a synthetic campaign-feasibility log summary regression containing both diagnostic events;
- binds the generic log-parser SHA-256 into the active preparation artifact.

The game-side probe is unchanged from r1 and remains SHA-256 `86843cb3bbed02ddb99f90fe084b45ca784fc0e5e70d03dfea99cab613b2236d`.

## Authority

`NO_ORDERS`; application `PROHIBITED`. No campaign order, mutation, save write, acknowledgement, execution, route, or causal-outcome claim is introduced.

## Offline regression

- 150/150 SyntheticLab tests PASS;
- 155/155 Runtime Probe tests PASS;
- 305/305 direct tests PASS;
- `compileall` PASS;
- 126 canonical JSON documents parsed;
- parser-to-emitter allowlist regression passes;
- dedicated probe pack remains byte-identical to r1.

## Next gate

Install v0.2I-r2 and repeat one dedicated read-only SFO campaign-map observation. No battle, replay, turn advance, army movement, or save is required.
