# Native CAI Offline Reconciliation — Progress Report

**Date:** 2026-08-02

## Closed offline tonight

- Reconstructed the authoritative v0.2I-r3 source tree from the owner-supplied canonical ZIP.
- Preserved all 13 external-review reports verbatim in-repository, including initial answers and correction passes.
- Preserved the architecture decision and next-gate plan as first-class research evidence.
- Confirmed the exact RPFM schema commit for WH3 Patch 8.1: `d12f59cb6de106d205f51b81739951adbc840c49`, committed 2026-07-09 as `Updated wh3 schemas for patch 8.1`.
- Confirmed that commit is one commit after the RPFM repo's previously surfaced schema pointer `229a393f8973b182458bedec8146cab4ef6d97fb`, changes only `schema_wh3.ron`, and has +863/-2 line delta.
- Preserved current master schema Git blob identity `232216808ff5d38edd9e056c7828afdc1700d297`.
- Re-verified official CA evidence for native task generation, batching, task/army pairing, force-strength prerequisites, distance-in-turns scaling, stance-aware movement, recruitment considerations and Patch 8.1 turn-dependent priorities.
- Reconciled current acquisition targets and prepared local input tooling so the remaining proprietary/local evidence can be collected in one bounded owner step.
- Verified current RPFM 5 architecture: the old CLI is removed, but `rpfm_server` exposes documented read-only WebSocket commands for `SetGameSelected`, `LoadAllCAPackFiles`, tree inspection, and schema-aware TSV extraction. Added a project client that automates target-table exports without modifying any pack.
- Added a private owner-input bundler so schema bytes, exported TSVs, manifests, and owner-installed Workshop research inputs can be returned in one integrity-hashed ZIP without copying vanilla CA pack binaries.

## Still blocked by local bytes, not by reasoning

1. Exact `schema_wh3.ron` bytes are not present in this environment. Public-host retrieval is blocked here by the file's size, so the owner acquisition script must copy the updated RPFM schema and verify the pinned Git blob SHA.
2. Vanilla WH3 DB rows live in CA packs on the owner's machine. The new RPFM-server exporter can decode/export only the target families automatically, but it must execute on that machine.
3. Current Incata / Camping Fix / Campaign AI Tweaks / recruitment pack bytes must be acquired from the owner's Workshop installation if available.
4. SFO/DeepWar/Hecleas existing audits identify table/file membership and hashes, but row semantics require the schema-aware TSV exports now automated through RPFM.

## Architectural conclusion remains unchanged

No new evidence tonight justifies restoring v0.2F/v0.2G to the application path or resuming assignment-derived v0.2I. The remaining high-information work is exact row/schema reconciliation.
