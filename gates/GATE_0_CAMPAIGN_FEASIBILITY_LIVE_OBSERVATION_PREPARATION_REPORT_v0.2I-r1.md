# Gate 0 Segment — Campaign Feasibility Live Observation Preparation v0.2I-r1

## Result

**HOTFIX CLOSED OFFLINE / LIVE OBSERVATION REMAINS OPEN.** The first owner-runtime v0.2I observation produced a valid current plan and request but no query result/rejection/packet-end. The request executor's model-synchronized polling timer was inappropriate for an intentionally idle campaign-map workload. v0.2I-r1 replaces it with an immediate poll plus a UI-synchronized real timer while preserving the same read-only query whitelist and `NO_ORDERS` / application `PROHIBITED` boundary.

## Owner-runtime limiting evidence

- exact two-pack SFO + v0.2I probe preflight passed;
- campaign first tick and full observer-safe snapshot passed;
- v0.2E→v0.2H sidecar produced plan `1c498493b05ca4a8e69215938f3604332874b7f9b5bacab582534b5c0c3d5d37` for turn 6 / actor `force:928`;
- five-query request SHA-256 `782ef566a6c1d2aaaec64f5352370aa5e55c14a350ece484d1ff0107ef47ede1` was written before the runtime log's last write;
- `FEASIBILITY_EXECUTOR_READY=1`; query results, explicit rejection, and packet end all remained zero;
- authority stayed `NO_ORDERS`; no save write or campaign order was emitted.

## Root-cause correction

WH3 campaign-manager documentation distinguishes model-synchronized `repeat_callback` from UI-update-synchronized `repeat_real_callback`. Since the owner is explicitly instructed not to advance the turn or issue an order, the transport poll must not depend on campaign-model time.

v0.2I-r1 therefore:

- calls `trans_feas_poll()` once immediately;
- uses `cm:repeat_real_callback(trans_feas_poll, 250, ...)`;
- emits one `FEASIBILITY_POLL_TICK` marker;
- emits one `FEASIBILITY_REQUEST_SEEN` marker after a valid bound request is parsed;
- removes the real callback after packet completion or explicit rejection;
- improves the collector's failure message with poll/request/result/rejection diagnostics.

## Offline regression target

- 150 SyntheticLab tests;
- 152 Runtime Probe tests;
- 302 direct tests total;
- deterministic dedicated probe SHA-256 `86843cb3bbed02ddb99f90fe084b45ca784fc0e5e70d03dfea99cab613b2236d`;
- preparation control digest `24c1563c53fbc25f53db4eba298700a6ec7392ff05faf59152c2ef5871e8f93e`.

## Remaining uncertainty

The timer correction is strongly supported by the owner limiting result and primary documentation, but the exact owner runtime still must be rerun to observe `FEASIBILITY_POLL_TICK`, `FEASIBILITY_REQUEST_SEEN`, and the query packet. No route/action/order authority is promoted by this hotfix.

## Next gate

Install v0.2I-r1, then rerun one dedicated read-only SFO campaign-map observation. No battle, replay, turn advance, army movement, or save is required.
