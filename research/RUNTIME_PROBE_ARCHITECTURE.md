# Runtime Probe Architecture

## Purpose

Reality Gate R0 begins with observation, not intervention. The first pack must prove script loading, campaign lifecycle access, observer-safe state access, structured logging, and evidence ingestion before any order or campaign-state authority is considered.

## Separation of authority

1. **Observer pack:** frozen replicated baseline; no campaign or save mutation.
2. **Persistence pack:** frozen replicated one-value namespace proof; no gameplay mutation.
3. **Shadow-input pack:** experimental read-only acquisition; no save mutation and no order path.
4. **Offline parser/adaptor:** converts only `TRANS_PROBE` records into evidence and a proposed scenario.
5. **SyntheticLab:** advisory ranking only; cannot consume live authority automatically.
6. **Future intervention packs:** prohibited until capability, fairness, acknowledgement, and outcome gates pass.

## Observer-safe data boundary

The probe may read:

- local faction armies, units, characters, and regions;
- local faction wars;
- foreign characters returned by `get_foreign_visible_characters_for_player`;
- foreign regions returned by `get_foreign_visible_regions_for_player`.

It may not enumerate the complete foreign world and then apply a project-side visibility filter. The game-provided visibility boundary is part of the evidence being tested.

## Evidence protocol

Records use a bounded pipe-delimited schema:

```text
TRANS_PROBE|1|EVENT|key=value|key=value
```

Values escape `%`, `|`, `=`, carriage returns, and newlines. The parser rejects unknown events, duplicate fields, prohibited personal/path fields, malformed records, events before `PACK_LOADED`, and snapshot records outside `SNAPSHOT_BEGIN`/`SNAPSHOT_END`.

## Pack format

The project-owned builder writes deterministic, uncompressed, zero-dependency PFH5 Mod packs. This is intentionally narrow and is not a general replacement for RPFM. RPFM remains the authoritative inspection tool for schemas, DB editing, and complex pack operations.

## Capability promotion

A documentation claim remains `UNVERIFIED`. A successful owner-machine record may promote only the exact observed capability:

- pack loaded;
- first-tick callback ran;
- local armies or regions were enumerated;
- visibility-filtered foreign lists were returned;
- a saved value survived a save/reload round trip.

The one namespaced save value is now `CONTROL` with `REPLICATED` evidence, scoped only to the tested disposable campaign and key version.

No objective control, order acceptance, order success, battle control, or AI improvement follows from observation or persistence evidence.

## Lifecycle timing

The first owner-machine run observed that foreign visibility expanded between `FIRST_TICK` and `LOCAL_FACTION_TURN_START` on turn 1. Consequently:

- `FIRST_TICK` is capability and initialization diagnostics;
- `LOCAL_FACTION_TURN_START` is canonical planner input;
- every record remains phase-labeled;
- a profile may not promote first tick to planner authority without replicated equivalence evidence.

## Duplicate semantics

An entity observed unchanged in two snapshots is a re-observation, not a duplicate defect. The parser:

- counts exact repeats within one snapshot as duplicates;
- tracks exact records recurring across snapshots separately;
- preserves lifecycle deltas so initialization changes are visible.

## Replication identity

Deterministic runs may produce byte-identical logs. Session independence is therefore not inferred from raw-hash inequality. It is proven through distinct evidence collections bound to:

- collection timestamp;
- evidence-manifest hash;
- raw log hash;
- derived collection identifier.

Strict observer replication additionally requires exact installed pack identity and clean loader entrypoints.

## Persistence acceptance

Persistence is tested only in an isolated disposable campaign. The first phase must report:

- `phase=WRITE`;
- `is_new_game=true`;
- `previous_found=false`;
- `previous=0`;
- `current=1`.

After manually saving and reloading that exact campaign, the second phase must report:

- `phase=RELOAD`;
- `is_new_game=false`;
- `previous_found=true`;
- `previous=1`;
- `current=2`.

Both phases must use the same persistence pack hash, campaign, faction, and key version, with no observer session loaded.


## Shadow-input policy

The first shadow pack reads controlled-army force strength, action points, unit soldier percentage, stance, owned settlement structure, own garrison, siege state, and explicit wars.

Foreign entities still originate only from the player-filtered lists. The pack does not query exact foreign force strength or foreign garrison composition. The offline adapter uses:

- visible unit count as foreign army strength proxy;
- settlement level and walls as foreign garrison proxy;
- visible hostile distance and siege state as threat proxy.

The adapter output is `SHADOW_NO_ORDERS`. It has no campaign application packet.

## Digest semantics

Observer and persistence tools preserve:

- transport-sensitive result digests for exact artifact traceability;
- semantic digests that remove filenames/line-position metadata for comparison.

Evidence hashes, pack identity, collection identifiers, timestamps, states, and checks remain inside semantic projections.

## Cross-runtime append log

`ModLog` remains useful for loader diagnostics, but it is not a durable combined-session transport. The engine's shared mod loader creates `lua_mod_log.txt` with write/truncate mode on the first call in each Lua runtime. Since campaign and ordinary battle are separate runtimes, transitions can erase the preceding segment.

The v0.1J combined pack therefore appends every `TRANS_PROBE` and `TRANS_BATTLE` line to:

```text
transcendence_runtime_log.txt
```

The campaign and battle scripts both open this file only in append mode. Before a combined run, `prepare_combined_session.ps1`:

- archives any previous append log under ignored `local_inputs`;
- removes the game-root copy;
- verifies the installed shadow pack matches the staged build;
- writes a timestamped prepared-session manifest.

For `campaign_battle` evidence, the collector requires both the manifest and a newly written append log. It refuses to fall back to `lua_mod_log.txt`, preventing a campaign-only final runtime from being mistaken for a complete combined session.

## Field-army eligibility and proxy alignment

New campaign records explicitly include `is_army`, `character_type_key`, and `planner_eligible`. Nonfield character forces are logged separately and excluded from objective assignment.

The planner never compares exact own force strength against visible-unit-count foreign strength. It uses a common unit-count-scale proxy for relative feasibility and preserves exact own strength as telemetry only.

Owned settlement garrison telemetry accepts a unit-count proxy only when the residence army reports `is_armed_citizenry()`. A normal field army in the settlement is excluded, and the structure proxy is used instead.

## v0.1R action-authority capture path

```text
prepare exact deterministic action-authority pack
  → explicit owner-approved copy into WH3 data
  → archive and clear append-only runtime log
  → ordinary single-player battle with normal owner input
  → TRANS_ACTION schema-1 local-unit windows
  → strict parse and exact-pack verification
  → public summary + verification + manifest ZIP
  → raw log remains local-only
```

The probe is battle-only and read-only. It registers local selection and game command callbacks, then samples local unit queries for a bounded five-second window. No unitcontroller is created. The preparer does not enable the pack, edit `used_mods.txt`, or touch saves. The rollback script restores a prior same-name pack or removes the installed probe only after hash checks.

## v0.1S public capture adjudication

`adjudicate_action_authority_export.py` validates the exact public member set, member hashes, exact pack identity, cross-document counts, verification digest, authority, and zero issue/acknowledgement invariants. It emits capability-specific adjudications rather than a general execution claim.

Future action-authority exports use schema 2 with a sanitized preparation attestation. The raw log and private prepared manifest remain beneath `local_inputs`; the public attestation contains no filesystem path.
