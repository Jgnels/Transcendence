# Gate 0 — v0.2R Offline Engineering Integration

**Status:** CLOSED PASS — PROMOTED TO GITHUB `main`
**Authority:** `NO_ORDERS`  
**Application authority:** `PROHIBITED`

## Scope

v0.2R is an offline engineering milestone layered on the sealed v0.2Q evidence. It does not consume a new Stage-A SFO campaign and does not change any frozen v0.2Q threshold or decision rule.

### Track A — Native Behavior Replay Lab

- deterministic capture ZIP normalization with manifest/SHA/provenance/completeness checks;
- explicit missing-battle-telemetry handling: missing telemetry is never interpreted as “no battle”;
- per-force longitudinal timelines and deterministic JSON/CSV/Markdown outputs;
- frozen v0.2N–v0.2Q metric/policy reuse rather than reimplementation;
- separate preregistered, causal-review, and `EXPLORATORY` outputs;
- adversarial coverage for partial turns, duplicate records, incomplete battles, CQI identity reuse, stationary/roaming forces, overlapping reversals, concentration, tampering, unknown events, and insufficient denominators;
- no change to either game-side Lua probe.

Raw historical vanilla/SFO diagnostic capture ZIPs are not in the canonical source. The lab is therefore certified against adversarial fixtures and frozen published references without claiming to have replayed unavailable owner captures.

### Track B — Single-Row Native CAI Ablation Factory

- one-row/one-value deterministic PFH5 machinery;
- exact table/key/original/experimental/header/provenance manifest;
- deterministic SHA-256 and rollback instructions;
- fail closed on multiple rows, key changes, unsupported layouts, and uncertified keys unless a future explicit research override is present;
- real evidence-earned builds additionally require a future explicit build gate, owner authorization, and evidence digest;
- no real row selected, no real ablation pack committed, no Workshop/game installation.

Current experiment status: `NOT_EARNED`. Application status: `APPLICATION_INELIGIBLE`.

### Track C — Native-First Active-Document Audit

- v0.2Q made authoritative at the front of active state documentation;
- paused v0.2I and evaluator-only v0.2G/v0.2H sections relabeled historical where active headings were misleading;
- old “next gate must add portfolio-to-army assignment” language retired as an active mitigation while preserving the historical proposal;
- false SFO allocator attribution, Grey Point Scuttlers generalization, privileged-state application leakage, and absence-as-capability claims remain explicitly blocked;
- decision/evidence history remains preserved.

## Frozen boundaries

- Stage-A SFO replication policy unchanged.
- Recovery threshold unchanged.
- Temporal definitions/envelope unchanged.
- Captured SFO row-footprint interpretation unchanged.
- `NO_NATIVE_ROW_ABLATION_EARNED` remains binding.
- Privileged diagnostic telemetry remains permanently `application_eligible=false`.
- v0.2G/v0.2I remain outside the application path.
- No campaign or battle order authority is granted.

## Gate close results

All promotion requirements were satisfied before canonicalization:

1. SyntheticLab: **203/203 PASS**.
2. Runtime Probe: **219/219 PASS**.
3. Combined direct tests: **422/422 PASS**.
4. repository validator / manifest: **PASS — 600 hashed files**.
5. forbidden-artifact scan: **PASS**; zero tracked `.pack` artifacts.
6. both frozen game-side Lua hashes unchanged.
7. exact v0.2R promotion inventory recorded: 18 changed files relative to canonical v0.2Q `main`.
8. v0.2R was built on exact sealed v0.2Q tree `e665e7808aff3d4797ac40793ad145ff19a9aa0b`, not stale historical `main`.
9. exact validated v0.2R tree `3f4b8a721eec479a023561e5324fb4e8f48e8193` was promoted through PR #2; `main` reached merge commit `fae5ccdf44b98823182558c96d2f4c87218ac54c` before this documentation-only closeout.

This gate is closed. The active evidence gate remains `GATE_0_NATIVE_SFO_REPLICATION_v0.2Q.md`; no promotion result grants row-ablation or gameplay-order authority.
