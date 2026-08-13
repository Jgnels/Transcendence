# RPFM Read-Only Native-CAI Export Protocol Evidence

**Date:** 2026-08-02  
**Purpose:** freeze the exact public technical basis for the owner-side read-only exporter.

## Current RPFM architecture

Current RPFM source/documentation separates the UI from `rpfm_server`. The UI starts the backend and third-party clients can use the local WebSocket protocol.

Pinned RPFM source revision inspected for protocol documentation:

`c049cfad79c003b61c530da4c5e67fb4aeff74cf`

Relevant public files:
- `docs/server/client-example.md`
- `docs/server/ws-commands.md`
- `docs/server/ws-responses.md`
- `docs/server/ws-shared-types.md`
- `rpfm_lib/src/schema/mod.rs`
- `rpfm_lib/src/files/table/local.rs`

## Read operations used by Transcendence tooling

The exporter uses only:

- `SetGameSelected`
- `LoadAllCAPackFiles`
- `OpenPackFiles`
- `GetPackFileDataForTreeView`
- `DecodePackedFile`
- `ExtractPackedFiles`
- `ClosePack`
- `ClientDisconnecting`

The published `ExtractPackedFiles` command supports an `as_tsv` boolean. `ContainerPath` uses `{ "File": "..." }` / `{ "Folder": "..." }`, and source labels include `PackFile` and `GameFiles`.

No save/update/delete/import/mutation command is used by `tools/Export-NativeCAIRows-RpfmServer.ps1`.

## Why primary keys can be derived without guessing

Current RPFM schema source documents `Field.is_key` as:

> whether this field is part of the table's primary key

The same source documents that `is_key` can be overridden by schema patches.

Current `TableInMemory` source is Serde-serializable and carries:

- `table_name`
- `definition`
- `definition_patch`
- `table_data`

The documented `DecodePackedFile` response for a DB is `DBRFileInfo = [DB, RFileInfo]`. Therefore the local server can provide the actual decoded table definition and its per-table definition patch while the exact current file is open.

The project exporter uses that evidence as follows:

1. decode each selected target DB file read-only;
2. inspect every field's raw `is_key`;
3. apply a `definition_patch[field].is_key` override if present;
4. collect the effective primary-key field sequence;
5. accept a table's key spec only if all decoded **vanilla** instances agree;
6. otherwise emit `NO_PRIMARY_KEY_FIELDS_OBSERVED` or `CONFLICTING_PRIMARY_KEY_DEFINITIONS` and leave the table unresolved.

This is deliberately fail-closed. A table name, row shape, or mod convention is never used to invent a key.

## Remaining runtime uncertainty

The public protocol/source establishes that the commands and serialized metadata exist. The exact owner-installed RPFM build has not been connected from this Linux environment. Therefore:

- protocol existence: `VERIFIED_SOURCE_FACT`;
- exporter implementation against that protocol: offline/source-reviewed;
- owner-machine compatibility: `UNVERIFIED` until first run;
- pack mutation: not authorized and not implemented by the exporter.
