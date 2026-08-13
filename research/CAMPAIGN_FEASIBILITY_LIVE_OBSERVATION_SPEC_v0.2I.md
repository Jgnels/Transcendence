## v0.2I-r3 embedded-request addendum

When an owner session reaches real polling and local plan generation but WH3 does not observe the runtime-created request file, the gate must not keep retrying the same inbound channel. The approved retry freezes the exact saved plan and semantically equivalent request, generates a one-session PFH5 whose Lua contains those request records before process start, and binds its exact hash during SFO-only preflight. The runtime still checks the request turn and executes only the existing 13-key read whitelist. Final adjudication independently rebuilds v0.2E→v0.2H from the new snapshot and requires exact equality with the frozen plan. A mismatch invalidates the evidence; it does not become an order or outcome claim.

## v0.2I-r2 parser-contract addendum

The probe→sidecar event vocabulary is now a tested contract. New diagnostic telemetry may not be added to the dedicated feasibility Lua unless `parse_probe_log.py` accepts it in the same release. `campaign_feasibility` is an explicit snapshot-bearing read-only probe kind. The r1 real/UI polling mechanism remains the required idle-campaign transport.

# Campaign Feasibility Live Observation Specification v0.2I

## v0.2I-r1 hotfix addendum

The asynchronous request executor must not depend on campaign-model time while the owner is instructed to leave the campaign map idle. After `FEASIBILITY_EXECUTOR_READY`, the probe performs one immediate poll and registers `cm:repeat_real_callback(trans_feas_poll, 250, ...)`. The first real poll emits `FEASIBILITY_POLL_TICK`; parsing a valid bound request emits `FEASIBILITY_REQUEST_SEEN`. Packet completion or explicit rejection removes the real callback. These are transport/lifecycle events only and do not alter the read-only authority boundary.

## Purpose

Observe whether the exact owner WH3 + SFO runtime executes a bounded subset of v0.2H campaign read-query surfaces as documented. This gate is evidence collection only. It does not test or authorize campaign orders.

## One-session flow

1. Build and install `transcendence_campaign_feasibility_probe.pack`.
2. Require the launcher to contain exactly SFO: Grimhammer III plus that probe.
3. Capture exact WH3 executable, SFO pack, probe pack, and launcher-state hashes.
4. Clear/archive the old project append log and any stale request file.
5. Start the local read-only sidecar.
6. Load any suitable current SFO campaign and remain on the campaign map.
7. On first tick, the probe emits one complete observer-safe campaign snapshot; no turn advance is required.
8. The sidecar runs the canonical v0.2E→F→G→H pipeline over that exact snapshot. If there is no v0.2G force assignment, no feasibility query is run.
9. If an assignment exists, the sidecar selects one deterministic assignment and writes only its exact v0.2H query IDs and parameters to `transcendence_campaign_feasibility_request.txt` in the game root.
10. The in-game probe executes only its hard-coded read-query whitelist and records results to the append log.
11. After WH3 exits, the collector independently reconstructs the plan from the raw snapshot, verifies exact query identity/cardinality, adjudicates through v0.2H, and creates one public-safe ZIP.

## Authority boundary

Allowed runtime surfaces are read/query-only: model CQI existence and lookup, force active stance, current/stance-specific/long-horizon point or settlement reachability, region settlement resolution, and current siege state. Timer callbacks and file I/O are transport/lifecycle mechanisms and do not mutate campaign model state.

The probe contains no movement, attack, attack-region, stance-change, garrison, action-point, movement-enable/disable, pathfinding-restriction, save-value, or campaign-order call. The sidecar has no WH3 process-control or game-memory interface.

`QUERY_TRUE` means only that the exact read query returned true for the exact actor/target representation/stance/turn instant. It never implies route geometry, ZOC safety, interception safety, attack legality, order acknowledgement, execution, or causal outcome.

## Fail-closed behavior

- No current v0.2G force assignment → no request file and no query execution.
- More than 16 planned queries → preparation error.
- Stale turn → in-game request rejection.
- Unknown query key → in-game request error; no fallback surface.
- Duplicate/foreign query ID → collector rejection.
- Saved sidecar plan not reproducible from the raw snapshot → collector rejection.
- Missing packet end, wrong cardinality, order/save attestation change, pack mismatch, or environment mismatch → collector rejection.

## Owner workload

The intended successful run requires no battle, no replay, no turn advance, no army movement, and no save. The owner only prepares the exact two-mod launcher state, launches WH3, loads a current SFO campaign, waits on the campaign map, exits WH3, and runs the collector.
