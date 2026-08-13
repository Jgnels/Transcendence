# Native CAI Behavior Acquisition Specification — v0.2K

**Date:** 2026-08-02  
**Status:** `OFFLINE_ACQUISITION_BOUNDARY_PREPARED`  
**Policy authority:** `NO_ORDERS`  
**Application authority:** `PROHIBITED`

## Purpose

v0.2J defined what Transcendence would like to measure about native Campaign AI without reviving a project-owned planner: threatened-front response, recovery misuse, reserve adequacy, position stability, directional retarget candidates, assignment exclusivity, native memory, and hysteresis.

v0.2K answers the prerequisite question: **which of those measurements can the existing read-only owner-safe campaign observer actually acquire without using hidden foreign state?**

The answer is intentionally narrower than v0.2J. The current safe observer can measure longitudinal movement of foreign armies that WH3 exposes to the human player. It cannot certify complete foreign-faction army inventories or hidden native tasks.

## Visibility boundary

The existing `transcendence_shadow_probe.lua` acquires:

- the local human faction's own military forces through its own faction interface;
- the local human faction's own regions;
- foreign characters only through `get_foreign_visible_characters_for_player()`;
- foreign regions only through `get_foreign_visible_regions_for_player()`.

It emits the provenance marker:

`foreign_visibility_source=WH3_PLAYER_FILTERED_LISTS`

The WH3 campaign scripting model hierarchy documents that a `FactionTurnStart` context can expose a faction interface and that faction interfaces can be navigated to their military forces. That documented capability is **not** adopted here for foreign AI factions. Enumerating every foreign faction force merely because Lua can reach it would cross the project's observer-safe hidden-information boundary.

Relevant scripting documentation:

- https://chadvandy.github.io/tw_modding_resources/WH3/campaign/scripted_events.html
- https://chadvandy.github.io/tw_modding_resources/WH3/campaign/campaign_index.html
- https://chadvandy.github.io/tw_modding_resources/WH3/scripting_doc.html

These pages establish scripting-surface availability, not owner-runtime behavior of any new Transcendence probe.

## New partial-trace contract

`NATIVE_CAI_PLAYER_VISIBLE_PARTIAL_TRACE_V1`

Required authority:

- `authority = NO_ORDERS`
- `application_authority = PROHIBITED`
- `foreign_visibility_source = WH3_PLAYER_FILTERED_LISTS`

A trace names:

- one human `observer_faction`;
- one foreign `observed_ai_faction`;
- at least two chronologically increasing frames;
- player-visible army positions;
- player-visible/observer-owned region positions.

Foreign force continuity is keyed to observed force CQI when the runtime adapter has it. A force leaving the player-visible set is right-censored; disappearance is not promoted to destruction, retreat, disbandment, or reassignment.

## What v0.2K can measure safely

| Question | v0.2K classification | Reason |
|---|---|---|
| Did a continuously visible foreign force change position? | `OBSERVE` | positions are player-visible |
| Was it position-stable between observations? | `OBSERVE_PROXY` | position stability only; not native idleness |
| Did movement uniquely approach a player-visible anchor? | `OBSERVE_PROXY` | direction only; no native task identity |
| Did the directional anchor proxy change? | `OBSERVE_REVIEW_CANDIDATE` | candidate only; not task churn |
| Did a force enter/leave the visible set? | `OBSERVE_CENSORED_TRANSITION` | visibility transition, not entity lifecycle |
| Full foreign-faction front coverage | `UNAVAILABLE_INCOMPLETE_FOREIGN_FACTION_VISIBILITY` | hidden forces/regions can exist |
| Full foreign-faction response latency | `UNAVAILABLE_INCOMPLETE_FOREIGN_FACTION_VISIBILITY` | denominator/front inventory incomplete |
| Recovery misuse | `UNAVAILABLE_NO_SAFE_FOREIGN_REPLENISHMENT_AT_ENGAGEMENT` | current safe foreign records do not carry engagement-time replenishment |
| Reserve adequacy | `UNAVAILABLE_INCOMPLETE_FOREIGN_FACTION_VISIBILITY` | unseen healthy forces may exist |
| Native task identity | `UNAVAILABLE` | task telemetry not exposed by this trace |
| Assignment exclusivity | `UNAVAILABLE_FROM_TRAJECTORY_ONLY` | movement cannot prove internal allocation slots |
| Native assignment memory | `UNAVAILABLE` | engine internal |
| Native hysteresis | `UNAVAILABLE` | engine internal |

## Fail-closed directional inference

A movement interval receives a directional-anchor proxy only when one prior-frame player-visible anchor has a uniquely strongest positive approach delta.

If multiple anchors are effectively tied, the interval is:

`AMBIGUOUS_VISIBLE_ANCHOR_APPROACH`

If an army is position-stable, the interval is:

`POSITION_STABLE_NO_INTENT_INFERRED`

If the directional proxy changes between comparable intervals, v0.2K emits:

`VISIBLE_ANCHOR_DIRECTION_CHANGE_CANDIDATE_NOT_TASK_CHURN`

No such record is a native task, assignment, hysteresis failure, or proof of thrashing.

## Existing owner evidence reprocessed now

v0.2K reprocesses the already-preserved public-safe artifact:

`research/runtime_evidence/CAMPAIGN_TURNS_4_7_REPROCESS_v0.1J.json`

That artifact is derived from the owner's frozen combined-session campaign log and already records `foreign_entity_source = WH3_PLAYER_FILTERED_LISTS`. No private log was reconstructed or required.

Frozen v0.2K reprocess:

`research/runtime_evidence/PLAYER_VISIBLE_NATIVE_BEHAVIOR_REPROCESS_v0.2K.json`

Result digest:

`5d2e6fdf9f2286225815842488977d631d31dae49c74acae22e27f025e6e831d`

Observed scope across turns 4–7:

- 7 foreign AI factions visible in at least two frames;
- 37 comparable continuously visible foreign-force intervals;
- 36 position-stable intervals;
- 1 movement interval;
- that one movement interval is directionally ambiguous;
- 0 directional-anchor proxies;
- 0 directional-anchor change candidates;
- 6 visibility gains;
- 6 visibility losses.

### Interpretation of the historical result

The 36/37 position-stable result is **not evidence that native CAI is idle, stuck, passive, or poor**. The preserved observer-safe data does not reveal native task identity, recruitment intent, garrison intent, defensive posture, hidden threats, hidden forces, or the full context of other AI wars. The result is therefore a `SUPPORTED_DERIVED_OWNER_EVIDENCE` limiting result, not a native-CAI failure.

It does prove something useful about experiment design: a future test cannot use raw position stability as a sufficient failure criterion.

## Tooling

Pure evaluator:

`synthetic_lab/transcendence_lab/native_visible_behavior.py`

Runtime-log adapter:

`runtime_probe/tools/run_native_visible_behavior.py`

Historical owner-evidence reprocessor:

`runtime_probe/tools/reprocess_native_visible_behavior_evidence.py`

Frozen synthetic integration result:

`runtime_probe/fixtures/native_visible_behavior_5_turns_expected.json`

The runtime adapter deliberately does not import v0.2F/v0.2G assignment modules and contains no campaign order adapter.

## Owner-run decision

**Do not request a WH3 run merely because v0.2K exists.**

A future owner observation is justified only after a preregistered native-failure question can be answered by the information the observer is allowed to collect. If a candidate requires hidden full-faction inventories, the project must either redesign the metric for partial observability or explicitly authorize a separate research-only omniscient experiment. It must not silently weaken the normal observer boundary.

## Architecture consequence

v0.2K does not revive v0.2G or v0.2I. It strengthens the native-first research architecture by making missing information explicit:

`native CAI execution -> player-visible observation -> bounded failure candidates -> evidence adjudication -> native tuning first -> bounded correction only if earned`
