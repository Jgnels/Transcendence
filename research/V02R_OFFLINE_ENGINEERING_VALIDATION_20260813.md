# v0.2R Offline Engineering Integration Validation — 2026-08-13

**Candidate status:** OFFLINE VALIDATED; NOT YET GITHUB-CANONICAL  
**Authority:** `NO_ORDERS`  
**Application authority:** `PROHIBITED`  
**Application eligibility:** unchanged

## Base provenance

The integration candidate was assembled from the exact sealed v0.2Q canonical source archive whose SHA-256 is:

`653d2d4cd231f91d3acae91d3ae117907cde9bc3a93ddf3642565304cb557f6c`

That source validated before modification at 193/193 SyntheticLab, 198/198 Runtime Probe, 391/391 combined, and 588/588 manifest hashes.

## Integrated tracks

1. Native Behavior Replay Lab.
2. Single-Row Native CAI Ablation Factory.
3. Native-First Active-Document Audit.

The tracks were developed in isolated local copies and combined by copying only intentional source/test/document changes. Generated local-input sessions, caches, temporary files, and synthetic `.pack` outputs were excluded from the integration tree.

## Direct regression before final ledger seal

- SyntheticLab: **203/203 PASS**.
- Runtime Probe: **219/219 PASS**.
- Combined direct tests: **422/422 PASS**.
- Python compileall: **PASS**.
- Native-first active-document audit: **12/12 invariants PASS**.

## Game-side Lua isolation

Frozen hashes remain:

- `runtime_probe/source/script/campaign/mod/transcendence_native_diagnostic_probe.lua`  
  `0acb4e186a4f4077801a763dbbf5cacc8ae21a9d47ecc76d54fefe5c023ec203`
- `runtime_probe/source/script/campaign/mod/transcendence_shadow_probe.lua`  
  `4f8c80fb67efe288e4b7b4eeacc0c48578707a0e554f2dd8a454aa669b50ed98`

No game-side Lua modification was made.

## Repository validator

After integrating the three tracks and the v0.2R gate, the repository validator passed with **599 hashed files** and the same 203 + 219 test split. This validation report is then added as the final audit record; the SHA ledger is regenerated and the validator is rerun so the externally reported final repository count includes this file.

## Preserved experiment semantics

- v0.2Q Stage-A SFO policy unchanged.
- Frozen vanilla sensitivity ceiling remains 31.7073%.
- No new Stage-A SFO capture consumed.
- No native-row ablation earned.
- No SFO priority increase copied.
- No SFO allocator release/return attribution promoted.
- Grey Point Scuttlers remains special-policy causal-review evidence, not ordinary territorial thrashing proof.
- Privileged diagnostic state remains permanently `application_eligible=false`.
- v0.2G/v0.2I remain outside the application path.
- No order, save, Workshop, or game-directory mutation is introduced.

## Remaining boundary

GitHub `main` is still the stale July 29 repository until the exact sealed v0.2Q tree is transported into the existing canonical-cutover branch and reviewed through a draft PR. v0.2R must branch from that verified v0.2Q GitHub base; it must not be layered directly onto stale `main`.
