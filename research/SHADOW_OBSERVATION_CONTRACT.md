# Shadow Observation Contract v3

## Purpose

Convert every read-only `LOCAL_FACTION_TURN_START` snapshot from one bounded campaign session into deterministic Army Objective Assignment proposals without issuing any WH3 order.

## Runtime boundary

The shadow pack may:

- read the local faction's field armies and owned regions;
- read foreign characters and regions only from WH3's player-filtered visibility lists;
- read explicit wars from the local faction;
- emit bounded structured telemetry.

It may not:

- enumerate the complete foreign world;
- write saved values;
- issue campaign orders;
- mutate diplomacy, economy, armies, regions, units, or effect bundles;
- use game or Lua randomness.

## Candidate observations

### Controlled armies

- force and general identifiers;
- subtype, position, current region, stance, and unit count;
- `military_force:is_army()`, commander `character_type_key`, and explicit planner eligibility;
- exact `military_force:strength()` as telemetry only;
- general movement remaining and action points per turn;
- average unit soldier percentage.

### Visible foreign armies

- visible character and force identifiers;
- faction, subtype, position, and unit count.

The first shadow profile deliberately does **not** query foreign `military_force:strength()` or foreign unit-health internals. Enemy strength is a transparent visible-unit-count proxy until a fairness review establishes a stronger field is legitimately player-visible.

### Regions

Owned regions expose settlement structure and siege state. A unit-count garrison proxy is accepted only when the residence force reports armed citizenry. A normal field army occupying the settlement is excluded and cannot be counted twice.

Foreign regions come only from the visibility-filtered region list. The planner does not consume foreign garrison composition or exact force strength. It uses a disclosed settlement-level/walls proxy.

### Wars and prior objectives

The runtime emits exact local-faction war pairs. Prior objectives are project-owned history supplied to the offline adapter; they are not read from or written to WH3.

## Deterministic proxy policy

- own feasibility strength: unit count × health fraction × fixed coefficient;
- exact own force strength: telemetry only, never compared directly with foreign proxies;
- own replenishment: average unit soldier percentage;
- own movement: movement-remaining percentage proxy, explicitly uncalibrated;
- foreign army strength: visible unit count × fixed coefficient;
- foreign garrison: settlement level and wall proxy;
- threat: only visible hostile armies at war, distance, and visible siege state;
- `HOLD`: always legal;
- every output remains `HYPOTHESIS` until calibrated against live outcomes.

## Multi-turn session contract

- one prepared combined-session manifest;
- one append-only `transcendence_runtime_log.txt` spanning campaign and battle runtimes;
- one or more `PACK_LOADED` runtime sessions from the same exact pack;
- at least five complete consecutive local-turn-start snapshots;
- one proposal set per snapshot;
- prior proposals may be attached only as bounded continuity history;
- no proposal is treated as attempted, accepted, or completed;
- gaps, malformed boundaries, capability failures, and foreign-proxy violations remain visible;
- one upload bundle contains raw log, parsed summary, campaign report, verification, and hashes.

## Output

The offline pipeline produces:

1. one observer-safe scenario per turn;
2. field-provenance maps;
3. deterministic objective proposals with rationale and alternatives;
4. objective churn, HOLD rate, state-change, proxy, volume, and processing metrics;
5. a campaign result digest;
6. explicit `SHADOW_NO_ORDERS` mode.

No application packet exists in this gate.
