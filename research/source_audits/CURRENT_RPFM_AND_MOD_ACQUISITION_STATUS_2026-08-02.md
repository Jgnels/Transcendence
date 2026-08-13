# Current RPFM + Native-CAI Acquisition Status

**Date:** 2026-08-02  
**Gate:** `GATE_0_NATIVE_CAI_RECONCILIATION`  
**Authority:** research-only / no game mutation

## RPFM current architecture

RPFM 5 uses `rpfm_server` as its backend. The desktop UI starts the server and the server exposes a local WebSocket endpoint at `ws://127.0.0.1:45127/ws`. The published protocol includes the exact read operations this project needs:

- `SetGameSelected`
- `LoadAllCAPackFiles`
- `OpenPackFiles`
- `GetPackFileDataForTreeView`
- `ExtractPackedFiles`
- `ClosePack`
- `ClientDisconnecting`

`ExtractPackedFiles` supports schema-decoded TSV output. The project exporter deliberately does **not** invoke `SavePack`, `SavePackAs`, or any mutation command.

Primary sources:
- https://github.com/Frodo45127/rpfm
- https://github.com/Frodo45127/rpfm/blob/c049cfad79c003b61c530da4c5e67fb4aeff74cf/docs/server/client-example.md
- https://github.com/Frodo45127/rpfm/blob/c049cfad79c003b61c530da4c5e67fb4aeff74cf/docs/server/ws-commands.md
- https://github.com/Frodo45127/rpfm/blob/c049cfad79c003b61c530da4c5e67fb4aeff74cf/docs/server/ws-shared-types.md

## Exact WH3 8.1 schema target

Pinned upstream schema commit:

`d12f59cb6de106d205f51b81739951adbc840c49`

Commit message: `Updated wh3 schemas for patch 8.1`

Parent:

`229a393f8973b182458bedec8146cab4ef6d97fb`

`schema_wh3.ron` Git blob SHA-1 at that commit:

`232216808ff5d38edd9e056c7828afdc1700d297`

The commit is one commit ahead of the previously observed schema pointer and changes only `schema_wh3.ron` (+863/-2 in the Git comparison).

Upstream source:
- https://github.com/Frodo45127/rpfm-schemas/tree/d12f59cb6de106d205f51b81739951adbc840c49

The exact file is larger than the current connected-source retrieval limit. Therefore the commit and blob identity are pinned, but the full bytes are intentionally **not** marked acquired until the owner's current RPFM schema copy matches that Git blob.

## Acquisition automation now present

`tools/Acquire-NativeCAIInputs.ps1`
- discovers Steam libraries and WH3/Workshop locations;
- discovers `schema_wh3.ron` candidates;
- computes both SHA-256 and Git blob SHA-1;
- identifies exact 8.1 schema bytes by the pinned blob ID;
- discovers/hashes target Workshop packs;
- optionally copies only owner-installed Workshop packs into ignored `local_inputs/`;
- never copies Creative Assembly vanilla packs.

`tools/Export-NativeCAIRows-RpfmServer.ps1`
- uses the documented local RPFM server;
- loads vanilla CA packs read-only;
- locates only the target CAI table families;
- exports those tables as TSV;
- calls RPFM's documented `DecodePackedFile` on the selected tables and records the decoded table definition;
- derives effective primary-key fields from `Field.is_key`, honoring `definition_patch` overrides;
- opens owner-local target Workshop packs read-only and exports the same families;
- writes output only under ignored `local_inputs/native_cai_reconciliation/`.

`tools/Run-NativeCAIReconciliationAcquisition.ps1`
- one-shot wrapper for discovery -> RPFM export -> private bundle creation;
- preserves component-script failure output rather than attempting WH3/game changes.

`tools/Build-NativeCAIInputBundle.ps1`
- produces one private owner-to-research ZIP;
- writes SHA-256 hashes for all bundled inputs;
- excludes any vanilla `.pack` even if one somehow appears in the staging tree.

## Target Workshop evidence

| Mod | Workshop ID | Existing evidence | Remaining local need |
|---|---:|---|---|
| SFO: Grimhammer III | `2792731173` | prior extracted source audit | current schema-decoded target rows |
| DeepWar AI | `2978779730` | prior exact pack audit | current schema-decoded target rows |
| Hecleas AI Overhaul | `2905096541` | prior exact pack audit | current schema-decoded target rows |
| Incata AI Army Tasks and Strategy | `2935815665` | current identity externally corroborated; no frozen pack | current pack + rows |
| AI Camping Settlements Fix | `3594429287` | current identity externally corroborated; no frozen pack | current pack + rows |
| Campaign AI Tweaks | `3485519396` | 2026 activity externally observed; exact 8.1 state unverified | current pack + rows |
| Better AI Army Builder | `3617312541` | current identity externally corroborated; no frozen pack | current pack + rows |

Workshop descriptions and community reports remain discovery evidence only. Final semantics must come from exact owner-local packs plus schema-aware rows where obtainable.

## Current hard boundary

No WH3 launch is justified yet. The remaining blocked evidence is filesystem-local rather than gameplay-local:

1. byte-verify the owner's exact `schema_wh3.ron` against the pinned Git blob;
2. export current vanilla target CAI rows through RPFM;
3. export current installed target-mod rows;
4. use RPFM-emitted `rpfm_table_key_spec.json` to feed those exports into the fail-closed row-diff pipeline without guessing primary keys.

Only after those steps should the gate preregister a live ablation.
