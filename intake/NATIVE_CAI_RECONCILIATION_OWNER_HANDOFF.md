# Owner Handoff — Native CAI Reconciliation Inputs

**Goal:** collect the remaining local/proprietary evidence without launching WH3 and without manually exporting twenty tables one by one.

## Preferred path — RPFM 5.x automated read-only export

RPFM 5 exposes its normal backend over a local WebSocket server. The project now includes a read-only client for the exact operations we need. It never saves a pack.

1. Open **RPFM 5.x** and ensure `Warhammer 3` is selected/configured. The RPFM UI starts `rpfm_server` automatically on `127.0.0.1:45127`.
2. In PowerShell from this source tree run the one-shot wrapper:

   `powershell -ExecutionPolicy Bypass -File .\tools\Run-NativeCAIReconciliationAcquisition.ps1`

   The wrapper runs discovery, read-only RPFM export, and private bundle creation in sequence. Under the hood, the discovery stage finds the exact schema, game data path, and installed target Workshop packs. It copies only the public schema and owner-installed Workshop mod packs into ignored `local_inputs/`; it never copies CA vanilla packs.

   The export stage asks RPFM itself to:
   - select WH3;
   - load vanilla CA packs read-only;
   - find only the target CAI table files;
   - export them as schema-decoded TSV;
   - decode each selected DB definition and preserve field/type/reference metadata;
   - derive a fail-closed primary-key specification from RPFM's active vanilla definitions (including `is_key` patches), so later row diffs do not guess keys;
   - close the vanilla pack;
   - open each discovered target Workshop mod read-only and export the same target families;
   - write all output only under ignored `local_inputs/native_cai_reconciliation/exports/`.

3. Upload the resulting `Transcendence_NativeCAI_OwnerInputs_*.zip` here. The bundle will also contain `rpfm_table_schema_metadata.json` and `rpfm_table_key_spec.json` when RPFM can decode the selected tables.

The three component scripts remain available for troubleshooting, but the wrapper is the preferred path.

**Do not launch WH3. Do not enable the target mods in the launcher.** Merely having/subscribing to their Workshop files is sufficient for acquisition.

## Target Workshop IDs

- SFO: `2792731173`
- DeepWar: `2978779730`
- Hecleas: `2905096541`
- Incata AI Army Tasks and Strategy: `2935815665`
- AI Camping Settlements Fix: `3594429287`
- Campaign AI Tweaks: `3485519396`
- Better AI Army Builder: `3617312541`

If one is not installed, the acquisition manifest records `NOT_FOUND`; that does not make the run fail. We can decide which missing pack is worth temporarily subscribing to after reviewing the first bundle.

## Schema check

The exact Patch 8.1 schema target is:
- commit `d12f59cb6de106d205f51b81739951adbc840c49`
- `schema_wh3.ron` Git blob SHA-1 `232216808ff5d38edd9e056c7828afdc1700d297`

If acquisition reports a different blob, use RPFM **About → Check Updates** and rerun.

## Fallback if RPFM server export fails

RPFM 5's CLI was removed in favor of `rpfm_server`. If the automated server client is incompatible with the installed RPFM build, do not troubleshoot WH3 or change game files. Upload the acquisition manifest first. The fallback is RPFM's normal schema-aware `Export TSV` / pack-tree `Extract` surface, and I will reduce that to the smallest manual selection once I see the exact RPFM version and installed inputs.

## Safety

All new tooling is research-only. It calls read/open/tree/extract/close operations and never `SavePack`, `SavePackAs`, game mutation, Workshop mutation, or launcher mutation.
