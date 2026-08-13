# Gate 0 Segment — Campaign Feasibility Live Observation Preparation v0.2I

## Result

**CLOSED OFFLINE / LIVE OBSERVATION OPEN.** The dedicated read-only SFO campaign-feasibility capture path is prepared, deterministic, adversarially checked, and bounded to exact v0.2H query IDs. No owner-runtime capability is promoted yet.

## Implemented

- standalone campaign-only read-only PFH5 probe;
- first-tick observer-safe campaign snapshot to avoid forced turn advancement;
- deterministic local sidecar that runs the canonical v0.2E→v0.2H stack on the current snapshot;
- deterministic one-assignment selection with no request when no current assignment exists;
- atomically written bounded request file, maximum 16 queries;
- hard-coded in-game whitelist for only documented v0.2H read-query surfaces;
- exact turn/query/assignment/plan bindings in every live result;
- independent collector reconstruction of the plan from the raw snapshot;
- duplicate, foreign, stale, cardinality, environment, pack, and authority fail-closed checks;
- public-safe deterministic export with raw logs and personal paths excluded;
- generic SFO environment capture support for a named read-only probe without weakening the historical shadow-probe default.


## Defects found and corrected

1. The copied campaign probe initially emitted the historical shadow-probe script label and reused its listener name. The script provenance label and listener identity are now dedicated to `transcendence_campaign_feasibility_probe`, with a regression preventing relabel drift.
2. The first runtime result emitter used a Lua boolean-coalescing idiom that would have serialized a legitimate `false` query result as `null` while marking it observed. The emitter now preserves boolean `false` explicitly, and the live-artifact regression contains an observed false result.
3. The first preparation wrapper reintroduced the historical Windows PowerShell 5.1 `powershell.exe -File ... -Confirm:$false` binding defect. It now invokes `prepare_live_probe.ps1` in-process with a splatted Boolean common parameter, and a regression forbids the external invocation pattern.

## Offline evidence

- 150/150 SyntheticLab tests pass unchanged.
- 151/151 Runtime Probe tests pass, including six new v0.2I tests.
- Sidecar integration was exercised end-to-end with a first-tick fixture: plan generated, 13-query request written, synthetic query results appended, and `CAPTURE_COMPLETE` reached.
- The current-snapshot plan/request derivation repeated 100 times with one plan digest; mean 0.005381 s, max 0.007058 s in the build container (reference only, not owner-runtime performance).
- Dedicated pack builds deterministically as SHA-256 `ccc5b6d5d73386d0814e2f89e02720abdf26772ed4af739bf4c4bea72ee4deea` before packaging.

## Still unverified

Exact owner-runtime availability/behavior of each requested campaign query under the current WH3 executable and SFO revision; whether the current loaded state yields a v0.2G force assignment; live true/false/unavailable query distribution; any route/ZOC/interception semantics; any order, acknowledgement, execution, or outcome semantics.

## Next gate

Run exactly one dedicated SFO read-only campaign-map observation. No battle or replay is required. If the loaded state produces no current force assignment, the result is a valid limiting observation but does not close the query-execution gate; another suitable state may then be required.
