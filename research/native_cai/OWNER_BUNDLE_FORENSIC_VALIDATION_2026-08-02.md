# Owner Native-CAI Evidence Bundle — Forensic Validation

**Date:** 2026-08-02  
**Authority:** `READ_ONLY_RESEARCH_EVIDENCE`  
**Input:** `Transcendence_NativeCAI_UploadSafe_20260802T173523Z.zip`  
**Input SHA-256:** `b85c0db70deccbb1dd19df21100531f89b1483f1ceb0a81ec1040f111f7d0f9b`

## Result

`PASS_WITH_EXPORT_HELPER_LIMITATIONS`

The upload-safe ZIP is structurally sound and the evidence it contains is useful. No owner rerun is required for the row families decoded in this pass.

### Integrity checks

- ZIP integrity: PASS.
- Upload-safe archive size: approximately 220 KiB.
- `SHA256SUMS.txt`: 68/68 listed entries verified during ingestion.
- Upload-safe manifest: 67/67 included file sizes matched during ingestion.
- Raw Workshop packs were intentionally omitted from the upload-safe archive after their identities were captured.

### Source identities captured on the owner machine

| Source | Workshop ID | Captured SHA-256 |
|---|---:|---|
| SFO: Grimhammer III | 2792731173 | `ae20a0a08037aa3ebcbe7461d2589fc28dc15a5fe5d9ca4c0a9d0ff0a26da603` |
| DeepWar AI | 2978779730 | `f02bd8b5a70f899a8b4827af41da3231c71a7f595c06442177ec70f3fd407d50` |
| Hecleas AI Overhaul | 2905096541 | `5945102b4eac8ed73065bcc054d935f878d4ffd2b4af191ed4a15b0c31abedf8` |

The DeepWar and Hecleas hashes match the previously frozen pack-audit identities, closing provenance drift for those two sources.

## Export-helper limitations discovered

Two helper defects are recorded explicitly:

1. `rpfm_table_key_spec.json` is empty because the metadata helper queried the dependency cache incorrectly.
2. Files the helper labelled as TSV exports are actually exact binary DB payloads extracted by RPFM.

These defects do **not** imply corruption of the owner data. The binary DB headers, row counts and multiple complete table layouts were decoded offline in this pass. The owner should not repeat acquisition solely because of these helper defects.

## Schema pin status

The acquisition manifest expected RPFM schema commit `d12f59cb6de106d205f51b81739951adbc840c49` and blob `232216808ff5d38edd9e056c7828afdc1700d297`, but `schema_candidates` was empty and `selected_schema_exact=false`.

Therefore:

- exact current-schema byte pin: **NOT YET OWNER-CAPTURED**;
- binary row evidence: **VALID**;
- composite-key claims that depend on schema `is_key` metadata remain explicitly provisional unless independently established.

## Captured native/mod surface

- Vanilla: 26 targeted CAI table files.
- DeepWar: 11 targeted files.
- Hecleas: 16 targeted files.
- SFO: 9 targeted files.
- Incata AI Army Tasks and Strategy: not present locally in the acquisition.
- AI Camping Settlements Fix: not present locally.
- Campaign AI Tweaks: not present locally.

This is sufficient to proceed with the highest-value native-vs-major-mod reconciliation while leaving narrow-mod acquisition as a later optional evidence completion task.
