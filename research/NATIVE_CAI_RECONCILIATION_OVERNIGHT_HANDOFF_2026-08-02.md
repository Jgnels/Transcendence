# Native CAI Reconciliation — Overnight Handoff

**Date:** 2026-08-02  
**Canonical input:** `Transcendence_v0.2I-r3_CanonicalSource.zip`  
**Canonical input SHA-256:** `01e19aa331f9b358a52e300eacb4a56fcc134a6e904bec5946ee9f13f12a1ecb`  
**Post-review authority:** `NO_ORDERS`; application `PROHIBITED`

## What was completed without owner intervention

### 1. Architecture-review preservation

The complete external-review phase is now first-class canonical research rather than chat-only context. Thirteen verbatim Grok/Kimi/Claude reports and their correction passes are preserved under:

`research/external_reviews/native_cai_reconciliation_20260801/`

The post-review architecture decision is frozen in:

`research/NATIVE_CAI_RECONCILIATION_DECISION_2026-08-02.md`

The previous default:

`v0.2E -> v0.2F -> v0.2G -> v0.2H -> v0.2I -> project-owned strategic control`

is superseded by:

`Native WH3 CAI planner/executor -> Transcendence observation/evaluation -> native row-level tuning -> narrowly bounded correction only after a measured native failure survives native tuning`

No project-owned strategic controller is assumed necessary merely because one already exists in shadow code.

### 2. Canonical project state updated

Binding post-review sections were added to the current canonical-facing documents, including:

- `AGENTS.md`
- `README.md`
- `prompts/CONTINUE_PROJECT.md`
- `research/ARCHITECTURE.md`
- `research/CURRENT_STATE.md`
- `research/ACTIVE_HYPOTHESES.md`
- `research/CAPABILITY_MATRIX.md`
- `research/CLAIM_REGISTER.md`
- `research/KNOWN_RISKS.md`
- `research/DECISION_LOG.md`
- `research/SOURCE_LEDGER.md`

Decision entries D096 and D097 bind the native-first application owner and the row-level reconciliation gate.

### 3. New active gate created

`gates/GATE_0_NATIVE_CAI_RECONCILIATION.md`

The gate requires exact current schema/row evidence before another v0.2I attempt. It explicitly prohibits:

- v0.2I-r4 or another assignment-derived transport retry;
- campaign orders;
- tuning v0.2F/v0.2G application constants;
- a new strategic director/allocator/bloc controller;
- promoting historical/beta numeric values to current 8.1 truth.

### 4. Current Creative Assembly facts frozen

`research/source_audits/WH3_8_1_OFFICIAL_NATIVE_CAI_FACTS_2026-08-02.md`

Current/shipped official evidence establishes responsibility-level native support for:

- foreign-threat query/influence-map sensing;
- distinct threat and strength evaluation;
- task generation;
- multiple generators contributing to a task;
- task/army pairing in allocation;
- same-type/same-target batching;
- force-strength gating/recruitment behavior;
- priority modification by distance measured in turns;
- stance-aware movement distance;
- Patch 8.1 turn-since-campaign-start priority modulation.

It does **not** establish native reserve preservation, recovery protection, assignment exclusivity, temporal memory, hysteresis, or the project 2–4-turn / 0.15 reassignment policy.

### 5. Exact schema target pinned

RPFM schema commit:

`d12f59cb6de106d205f51b81739951adbc840c49`

Commit title: `Updated wh3 schemas for patch 8.1`

`schema_wh3.ron` Git blob SHA-1:

`232216808ff5d38edd9e056c7828afdc1700d297`

The connected environment cannot retrieve the >10 MB file bytes, so exact bytes are deliberately still owner-local evidence. This is a retrieval limitation, not an unresolved identity guess.

### 6. Reconciliation and acquisition tooling built

New research tooling:

- `tools/Acquire-NativeCAIInputs.ps1`
- `tools/Export-NativeCAIRows-RpfmServer.ps1`
- `tools/Build-NativeCAIInputBundle.ps1`
- `tools/extract_wh3_schema_targets.py`
- `tools/native_cai_row_diff.py`
- `tools/process_native_cai_owner_bundle.py`
- `tools/Run-NativeCAIReconciliationAcquisition.ps1`

The RPFM exporter uses only documented local-server read/open/tree/decode/extract/close operations and never saves a pack. It now also extracts RPFM's decoded `definition`/`definition_patch` metadata and emits a fail-closed vanilla primary-key spec from effective `Field.is_key` values. This removes the need to guess row keys later. It was source-reviewed against the current RPFM 5 protocol, but cannot be runtime-tested in this Linux research container because the owner's Windows RPFM/WH3 installation is the required endpoint.

The Python schema/row tools compile successfully. The private owner-bundle processor was tested against both extracted-directory and ZIP fixtures. The row diff was synthetic-tested against both observed RPFM TSV header arrangements and correctly fails closed with `KEY_SPEC_REQUIRED` rather than guessing a primary key.

### 7. Preliminary responsibility matrix completed

`research/source_audits/NATIVE_CAI_PRELIMINARY_RESPONSIBILITY_MATRIX_2026-08-02.md`

Current working dispositions include:

- task generation -> `ALREADY_NATIVE`
- task batching -> `ALREADY_NATIVE`
- task/army pairing -> `ALREADY_NATIVE`
- turn-distance priority -> `ALREADY_NATIVE`
- stance-aware distance -> `ALREADY_NATIVE`
- recruitment-aware resourcing -> `ALREADY_NATIVE`
- Patch 8.1 time-dependent priority behavior -> `ALREADY_NATIVE` behavior / exposure `UNVERIFIED`
- v0.2E/F/G distinctive safeguards -> primarily `PROJECT_SHOULD_MEASURE`
- v0.2I assignment-coupled transport -> paused / `UNAVAILABLE_OR_UNVERIFIED` pending architecture need

No `PROJECT_MUST_OWN` strategic responsibility is justified yet.

## Behavior-preservation proof

The untouched v0.2I-r3 source was separately extracted and compared against this post-review tree.

Existing implementation under `synthetic_lab/` and `runtime_probe/` remains byte-identical to v0.2I-r3. No existing planner/probe/gameplay implementation file was changed by the architecture pivot.

Existing canonical-facing files changed only to bind the new research/application disposition; new files are review evidence, research documents and offline acquisition/diff tooling.

Validation after the pivot:

- SyntheticLab: **150/150 PASS**
- Runtime Probe: **159/159 PASS**
- Combined direct tests: **309/309 PASS**
- Repository validation: **PASS** after manifest regeneration

The final package manifest should be treated as the byte-level identity for this post-review source package.

## The only owner-local step still required

No WH3 launch is required.

From the post-review source tree on the owner's Windows gaming PC:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\Run-NativeCAIReconciliationAcquisition.ps1
```

The component scripts remain available separately if a stage needs diagnosis.

Prerequisite: open RPFM 5.x first with Warhammer 3 configured. Its UI starts the local `rpfm_server` used by the read-only exporter.

Then upload the generated:

`Transcendence_NativeCAI_OwnerInputs_*.zip`

If the exporter reports a protocol/version error, do **not** launch WH3 or modify any packs. Upload `local_inputs/native_cai_reconciliation/acquisition_manifest.json` and `ACQUISITION_SUMMARY.txt`; that is sufficient to resolve the fallback path.

## What happens immediately after the owner bundle arrives

The remaining gate work is again offline:

1. byte-verify exact Patch 8.1 schema;
2. derive exact field/key definitions for target CAI families;
3. run vanilla -> SFO -> DeepWar -> Hecleas -> Incata/narrow-mod row diffs;
4. isolate Patch 8.1's new priority mechanism or classify it engine-internal/unverified;
5. promote every strategic responsibility to a supported disposition;
6. write explicit deletion/demotion thresholds for v0.2F/v0.2G/v0.2I;
7. preregister the smallest live native-first ablation that could actually change the architecture.

Only then should another WH3 session be requested.


## Owner evidence ingested — 2026-08-02

Owner upload `Transcendence_NativeCAI_UploadSafe_20260802T173523Z.zip` was ingested and hash-validated. The acquisition helper's files were binary DB payloads rather than TSV; offline decoders recovered nine high-value table families without requiring an owner rerun.

New evidence materially strengthens the native-primary decision: allocator distance/recruit/release-return variables, timed/endgame task-priority groups, and explicit player threat/strength multipliers are present in current vanilla rows. v0.2I remains paused.

See `research/native_cai/` for the machine-readable row diff, row atlas, Patch 8.1 evidence reconciliation, responsibility map and correction ledger.
