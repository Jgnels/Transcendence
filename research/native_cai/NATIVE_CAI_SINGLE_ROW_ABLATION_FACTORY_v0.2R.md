# Native CAI Single-Row Ablation Factory — v0.2R

**Status:** MACHINERY READY; REAL ROW EXPERIMENT `NOT_EARNED`  
**Authority:** `NO_ORDERS`  
**Application authority:** `PROHIBITED`  
**Application eligibility:** `APPLICATION_INELIGIBLE`

## Purpose

This factory prepares the smallest deterministic PFH5 experiment container for **one** evidence-approved native CAI DB row/value change. It does not choose a row, install a pack, edit a Workshop item, mutate a game directory, or expand application authority.

The current v0.2Q evidence has **not** earned a native CAI row ablation. The only packs built during factory certification are synthetic fixtures and remain `FACTORY_VALIDATION_NOT_EARNED`.

## Fail-closed contract

`tools/native_cai_ablation_factory.py` requires one JSON object using `NATIVE_CAI_SINGLE_ROW_ABLATION_SPEC_V1`. It rejects:

- multiple row specifications or a `rows` collection;
- unknown/unverified table layouts;
- key-field changes;
- more or fewer than one changed non-key value;
- incomplete source-header or provenance data;
- real `NOT_EARNED` source rows masquerading as factory fixtures;
- an evidence-earned build unless `--allow-earned-build`, owner authorization, and an evidence digest are all present;
- a pending/provisional pinned-schema key unless both the spec and command explicitly authorize that research risk.

A successful build contains one PFH5 entry only:

`db/<table>/transcendence_single_row_ablation`

The pack timestamp is zero and the PFH5 index is deterministic. Sidecars record the original row/value, experimental row/value, table/key, exact source header, provenance, SHA-256 values, authority status, and rollback instructions.

## Key-schema discipline

The 2026-08-02 owner row-diff work proved several **binary layouts by full-file consumption**, but its reconciliation artifact also says current pinned-schema key certification remains pending. Those are different claims.

The factory therefore does not convert successful decoding into silent row-targeting authority. A future row experiment should prefer a `VERIFIED_PINNED_SCHEMA_KEY` contract. A provisional-key experiment requires a deliberate two-part override and remains research-only.

The task-generator group/generator/variable-group composite key has the stronger label `PROVISIONAL_COMPOSITE_KEY_SCHEMA_CERTIFICATION_PENDING` and receives the same fail-closed treatment.

## Rollback and installation boundary

The factory performs **no installation**. If a future separately approved experiment activates a generated pack, rollback is removal/disablement of that generated override from the experimental load order only. Native, SFO, and prior-art packs remain untouched. A rollback-clean campaign must verify that the experimental pack is absent before evidence is interpreted.

## Current disposition

- Factory machinery: ready offline.
- Real row selected: **NO**.
- Real row ablation earned: **NO**.
- Pack installed: **NO**.
- Workshop action: **NO**.
- Game-directory mutation: **NO**.
- Orders issued: **NO**.
