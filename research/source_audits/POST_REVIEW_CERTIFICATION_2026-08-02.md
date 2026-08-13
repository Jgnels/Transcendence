# Post-Review Native-First Pivot Certification

**Date:** 2026-08-02  
**Input baseline:** `Transcendence_v0.2I-r3_CanonicalSource.zip`  
**Input SHA-256:** `01e19aa331f9b358a52e300eacb4a56fcc134a6e904bec5946ee9f13f12a1ecb`

## Scope certified

This certification covers the documentation/research-state pivot from the v0.2I-r3 application trajectory to `GATE_0_NATIVE_CAI_RECONCILIATION`.

It does **not** certify any new WH3 runtime behavior, native CAI row semantics, Patch 8.1 modder exposure, or RPFM-server behavior on the owner's machine. Those remain evidence-gated.

## Baseline byte comparison

A separate untouched extraction of the original v0.2I-r3 ZIP was compared against the post-review tree.

Result:

- existing `synthetic_lab/` implementation changed: **NO**
- existing `runtime_probe/` implementation changed: **NO**
- original files removed: **0**
- changed original paths are canonical-facing documentation/research state only
- additions are external-review evidence, research/gate documents, and offline acquisition/diff tooling

Machine-readable comparison:

`research/source_audits/POST_REVIEW_BASELINE_DIFF_2026-08-02.json`

## External-review provenance

All 13 copied verbatim reviewer reports were SHA-256 checked against the supplied research-freeze manifest.

Result: **13/13 exact report hashes PASS**.

The research-freeze baseline identifies the exact v0.2I-r3 canonical source SHA used by reviewers as the same SHA-256 shown above.

## Existing test baseline

After the post-review pivot:

### SyntheticLab

- **150 tests run**
- **150 PASS**
- runtime: approximately 32.35 seconds in this certification environment

### Runtime Probe

- **159 tests run**
- **159 PASS**
- runtime: approximately 0.94 seconds in this certification environment

### Combined

- **309/309 PASS**

No existing implementation test was removed to obtain this result.

## New research-tool checks

`tools/extract_wh3_schema_targets.py`
- Python compile: PASS
- fails closed unless the supplied schema Git blob matches the pinned Patch 8.1 blob.

`tools/native_cai_row_diff.py`
- Python compile: PASS
- synthetic RPFM TSV parse/diff: PASS for both observed metadata-first and column-first header arrangements;
- deterministic keyed row test: added/removed/changed rows identified correctly;
- missing primary-key specification: correctly returns `KEY_SPEC_REQUIRED` rather than guessing.

`tools/process_native_cai_owner_bundle.py`
- Python compile: PASS
- synthetic extracted-directory integrity + row-diff orchestration: PASS;
- synthetic ZIP safe-extraction + SHA-256 validation + row-diff orchestration: PASS;
- verified output on fixture: one added row, one removed row, one changed row, no invented keys.

PowerShell acquisition/export scripts and the one-shot `Run-NativeCAIReconciliationAcquisition.ps1` wrapper were source-reviewed against the published RPFM 5 WebSocket protocol. They cannot be execution-certified here because this environment is Linux and has neither the owner's Windows RPFM server nor WH3 installation. The exporter is intentionally limited to read/open/tree/decode/extract/close protocol commands and contains no pack-save command. Current RPFM source confirms decoded tables serialize their `definition` and `definition_patch`, and current schema source defines `Field.is_key` as primary-key membership; this is the basis for the generated fail-closed key spec.

## Manifest

`SHA256SUMS.txt` is regenerated after final source assembly and is the package-level integrity authority. Private/local acquisition content under `local_inputs/` is intentionally excluded except `local_inputs/.gitkeep`.

## Certification conclusion

**PASS — research/application disposition changed without changing the existing v0.2I-r3 executable strategic/tactical/probe implementation.**

The next unresolved work is acquisition and row-level reconciliation of owner-local current WH3/Workshop data, not another runtime transport attempt.
