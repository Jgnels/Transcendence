# Native CAI Reconciliation — Correction / Retraction Ledger Addendum

**Date:** 2026-08-02

## R001 — DeepWar personalities file-size inference

Earlier external-review analysis inferred from the ~175 KB `cai_personalities_tables` file that DeepWar likely overrode a broad personality surface.

**Status:** `SUPERSEDED_BY_ROW_EVIDENCE`

Owner-acquired current DeepWar and vanilla files have byte-identical decoded payloads after the DB header. DeepWar carries the vanilla table redundantly; current evidence does not support claiming personality-row changes from this file.

**Rule reinforced:** file presence/size is not behavior scope. Row-level comparison is required.

## R002 — “Native allocator is mostly opaque” framing

Earlier analysis treated native task-to-force allocation as known mainly through CA prose.

**Status:** `NARROWED_BY_ROW_EVIDENCE`

Current vanilla DB rows expose allocator policy variables for distance scaling, recruitment thresholds, release/return thresholds, and separate recruiting/non-recruiting distance horizons. Internal selection logic remains partly opaque, but important policy surfaces are explicitly data-tunable.

## R003 — Patch 8.1 modder exposure

Earlier review correctly classified the exact 8.1 table/variable surface as unverified.

**Status:** `PARTIALLY_RESOLVED`

Current vanilla pack data now shows endgame override groups and elapsed-round/timed-priority variable groups matching the officially described behavior. This strongly supports DB participation. Exact causal provenance to 8.1 and full schema mapping remain unverified.
