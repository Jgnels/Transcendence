# WH3 Shadow-Input API Audit v0.1G

**Date:** 2026-07-29  
**Purpose:** identify the narrow read-only campaign fields needed by the first Army Objective Assignment shadow slice.

## Sources

- WH3 generated scripting interface documentation:  
  `https://chadvandy.github.io/tw_modding_resources/WH3/scripting_doc.html`
- WH3 model hierarchy:  
  `https://chadvandy.github.io/tw_modding_resources/WH3/campaign/model_hierarchy.html`

These are interface documentation sources, not runtime proof.

## Candidate interfaces

| Semantic field | WH3 interface | Project treatment |
|---|---|---|
| controlled movement remaining | `CHARACTER_SCRIPT_INTERFACE:action_points_remaining_percent()` | candidate observation; uncalibrated map-distance scaling |
| controlled action-point capacity | `CHARACTER_SCRIPT_INTERFACE:action_points_per_turn()` | candidate observation |
| controlled force strength | `MILITARY_FORCE_SCRIPT_INTERFACE:strength()` | candidate observation |
| controlled unit soldier percentage | `UNIT_SCRIPT_INTERFACE:percentage_proportion_of_full_strength()` | average as replenishment/readiness proxy |
| owned garrison unit count | `GARRISON_RESIDENCE_SCRIPT_INTERFACE:unit_count()` | candidate observation |
| owned garrison strength | `GARRISON_RESIDENCE_SCRIPT_INTERFACE:army():strength()` | candidate observation with fallback |
| siege state | `GARRISON_RESIDENCE_SCRIPT_INTERFACE:is_under_siege()` | candidate map-state observation |
| settlement level | `SETTLEMENT_SCRIPT_INTERFACE:primary_slot():building():building_level()` | candidate structure proxy |
| walls | `SETTLEMENT_SCRIPT_INTERFACE:is_walled_settlement()` | candidate structure proxy |
| explicit wars | local faction `factions_at_war_with()` list | candidate legal-target boundary |

## Hidden-information conclusion

The documentation establishes that these methods exist. It does not establish that every method on a foreign object returned by a visibility-filtered list corresponds to information legitimately shown to the player.

Therefore the first shadow policy:

- does not call foreign `military_force:strength()`;
- does not average foreign unit health;
- does not read foreign garrison army strength or composition;
- uses foreign visible unit count as a disclosed strength proxy;
- uses visible settlement level and walls as a disclosed garrison proxy;
- records all proxy provenance.

This is a conservative design inference, not a claim about WH3 internals.

## Authority conclusion

Every audited method is a query. The v0.1G shadow source contains no save write, campaign order, diplomacy mutation, resource mutation, force creation, region transfer, effect-bundle application, or randomness call.

The next live run may promote only the exact fields successfully emitted. It cannot promote objective control or AI improvement.
