# WH3 Script Diagnostic-Telemetry Surface — v0.2M

**Date:** 2026-08-02  
**Purpose:** document the scripting surface used by the research-only native diagnostic probe.  
**Authority:** `NO_ORDERS / PROHIBITED`

## Documentation facts

Primary documentation:

- `https://chadvandy.github.io/tw_modding_resources/WH3/campaign/scripted_events.html`
- `https://chadvandy.github.io/tw_modding_resources/WH3/scripting_doc.html`

Documented facts used by v0.2M:

1. Campaign scripts can register persistent listeners with `core:add_listener`.
2. `FactionTurnStart` is an available campaign event and its context exposes `context:faction()`.
3. `FactionTurnEnd` is an available campaign event and its context exposes `context:faction()`.
4. `FACTION_SCRIPT_INTERFACE:military_force_list()` is documented as returning all military forces in the faction.
5. `FACTION_SCRIPT_INTERFACE:region_list()` and `factions_at_war_with()` are documented query surfaces.

These are **documented scripting-surface facts**, not proof that the new v0.2M probe has already executed successfully in the owner's current Patch 8.1 build. Live capability remains unverified until the qualification capture.

## Architectural boundary

The same API reachability that makes complete-faction research telemetry possible is **not** permission to use hidden faction state in normal Transcendence gameplay evaluation/application. v0.2M therefore uses a different log prefix, different pack, different trace contract, and `application_eligible=false` marker.

The existing `transcendence_shadow_probe.lua` remains the player-visible normal observer and is not modified by v0.2M.
