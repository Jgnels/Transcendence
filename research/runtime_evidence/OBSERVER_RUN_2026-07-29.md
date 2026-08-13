# Observer Run Evidence — 2026-07-29

## Status

`OBSERVED`

One pure-vanilla Karl Franz Immortal Empires session successfully loaded the read-only Transcendence observer pack and emitted structured campaign evidence.

This closes the first live observer execution, but not the Gate 0 requirement for two independent observer runs.

## Frozen private-input hashes

| Artifact | SHA-256 |
|---|---|
| `lua_mod_log.txt` | `ddf462130e6551c034ddd5e79dfc916fba0a133cfa0cf6ef715e6df7afd1f9f7` |
| original v0.1C `probe_summary.json` | `5177ee7ba8db6214e3cd605d035e73912e2708679e72f2b3b9ee60a197d51a6b` |
| `evidence_manifest.json` | `96e388d0013ca182113e89598d99efdaae3b79fe789e8da1e0b70ff0ab73b165` |
| v0.1D reparsed summary | `d8215b9f93664401c64c7842d190cef57042bc38115e8085bdcea30485a3b992` |

The raw files remain private. The repository stores only this derived report and a sanitized machine-readable evidence record.

## Observed session

- campaign: `wh3_main_combi`;
- local faction: `wh_main_emp_empire`;
- turn: 1;
- new game: true;
- multiplayer: false;
- probe sessions: 1;
- structured probe events: 55;
- capability failures: 0;
- snapshots: 2.

### First-tick snapshot

- own field armies emitted: 1;
- own regions emitted: 2;
- visible foreign characters emitted: 10;
- visible regions emitted: 9;
- wars counted: 2.

### Local-faction-turn-start snapshot

- own field armies emitted: 1;
- own regions emitted: 2;
- visible foreign characters emitted: 13;
- visible regions emitted: 11;
- wars counted: 2.

The later snapshot contained three additional visible characters and two additional visible regions. Therefore `FIRST_TICK` is an initialization diagnostic, not canonical planner input. `LOCAL_FACTION_TURN_START` becomes the canonical initial observation phase.

## Capability promotions

| Capability | Status |
|---|---|
| script-only campaign Mod pack loads | OBSERVED |
| `ModLog` emits parseable project records | OBSERVED |
| first-tick callback executes | OBSERVED |
| local-faction-turn-start snapshot executes | OBSERVED |
| local army identity, position, region, subtype and unit count | OBSERVED |
| local region identity, position and abandoned state | OBSERVED |
| game-interface-filtered foreign character list | OBSERVED |
| game-interface-filtered foreign region list | OBSERVED |
| saved-value persistence through save/reload | UNVERIFIED |
| campaign objective or order authority | UNVERIFIED |
| acknowledgement or outcome observation | UNVERIFIED |

The foreign observations are classified as game-interface-filtered because the adapter calls the explicit `get_foreign_visible_*_for_player` interfaces. This run proves those calls returned data; it does not prove every possible hidden-information edge case.

## Defect found and corrected

The v0.1C parser reported eight duplicate events because it compared exact records across the entire session. Those were normal repeated observations across two different snapshots.

The v0.1D parser now distinguishes:

- `duplicate_event_count`: exact duplicates inside the same logical snapshot or non-snapshot scope;
- `repeated_across_snapshot_count`: neutral re-observations appearing in multiple snapshots.

Reparsing the same evidence produces:

- duplicate events: 0;
- repeated records across snapshots: 8;
- result digest: `4391fed3eb2a87244e558797625eabdad0f8a4672a7f4073b6305cf271ce4f27`.

## Remaining observation-contract gaps

The current probe does not yet prove all Army Objective Assignment inputs. Still missing or insufficient:

- remaining campaign movement;
- replenishment state;
- strength estimate beyond raw unit count;
- prior project objective;
- explicit enemy/friendly war-pair identities rather than only war count;
- region siege state;
- garrison estimate;
- strategic-value and threat proxies;
- order acknowledgement and outcomes.

No gameplay-control claim is promoted from this run.
