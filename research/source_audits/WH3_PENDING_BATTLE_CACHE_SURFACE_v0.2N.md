# WH3 Pending-Battle Cache Surface Audit — v0.2N

Date: 2026-08-03  
Purpose: justify the read-only battle-participant instrumentation used by the preregistered v0.2N diagnostic study.

## Source

WH3 campaign-manager scripting documentation generated from the game's campaign script library:

- https://chadvandy.github.io/tw_modding_resources/WH3/campaign/campaign_manager.html

The documentation states that the pending-battle cache stores participant information before battle so factions, characters and military forces remain queryable even if commanders die. It also states that `ScriptEventPendingBattle` is triggered after the cache has been populated and can be listened to before battle.

Documented read-only methods used by v0.2N:

- `campaign_manager:pending_battle_cache_num_attackers()`
- `campaign_manager:pending_battle_cache_get_attacker(index)` → character CQI, military-force CQI, faction name
- `campaign_manager:pending_battle_cache_num_defenders()`
- `campaign_manager:pending_battle_cache_get_defender(index)` → character CQI, military-force CQI, faction name

The implementation is documented in `lib_campaign_manager.lua` in the generated source documentation. v0.2N listens only to `ScriptEventPendingBattle` and serializes the returned IDs/side labels. It does not issue an order, alter battle state, resolve a battle, mutate a save, or call a campaign command surface.

## Evidence classification

- Existence and documented semantics of the cache/event/methods: `VERIFIED_SCRIPT_SOURCE_DOCUMENTATION`.
- Successful behavior of the new v0.2N event listener on the owner's exact WH3 build: `UNVERIFIED_OWNER_RUN_PENDING` until fresh capture.
- `ATTACKER` side as proof of voluntary strategic intent: `NOT_SUPPORTED`; ambush/interception/special mechanics remain possible.
- Ability to identify participating military-force CQIs: `DOCUMENTED_QUERY_SURFACE`, owner-runtime validation pending.

## Safety boundary

The battle cache is used solely in `PRIVILEGED_OMNISCIENT_DIAGNOSTIC`, `application_eligible=false` research. The normal player-visible observer is unchanged. The new listener is read-only and remains under `NO_ORDERS / PROHIBITED` authority.
