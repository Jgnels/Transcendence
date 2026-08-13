from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "synthetic_lab"))
sys.path.insert(0, str(REPO_ROOT / "runtime_probe" / "tools"))

from parse_probe_log import ProbeEvent, ProbeLogError, canonical_json, parse_bool, parse_int, parse_logs
from transcendence_lab.decision import assign_objectives


class ShadowPipelineError(ValueError):
    pass


ENTITY_EVENTS = {
    "SHADOW_ARMY",
    "SHADOW_VISIBLE_ARMY",
    "SHADOW_OWN_REGION",
    "SHADOW_VISIBLE_REGION",
    "SHADOW_FILTERED_FORCE",
    "WAR",
}


def _float(fields: dict[str, str], key: str, fallback: float = -1.0) -> float:
    value = fields.get(key)
    if value is None:
        return fallback
    try:
        return float(value)
    except ValueError:
        return fallback


def _int(fields: dict[str, str], key: str, fallback: int = -1) -> int:
    value = fields.get(key)
    if value is None:
        return fallback
    try:
        return int(value)
    except ValueError:
        return fallback


def _bool(fields: dict[str, str], key: str, fallback: bool = False) -> bool:
    value = fields.get(key)
    if value is None:
        return fallback
    try:
        parsed = parse_bool(value)
    except ProbeLogError:
        return fallback
    return fallback if parsed is None else parsed


def _canonical_snapshot(events: Iterable[ProbeEvent]) -> tuple[ProbeEvent, list[ProbeEvent], ProbeEvent]:
    shadow_loaded = any(
        event.event == "PACK_LOADED" and event.fields.get("probe_kind") == "shadow"
        for event in events
    )
    if not shadow_loaded:
        raise ShadowPipelineError("no shadow PACK_LOADED record")

    begin: ProbeEvent | None = None
    collected: list[ProbeEvent] = []
    completed: list[tuple[ProbeEvent, list[ProbeEvent], ProbeEvent]] = []

    for event in events:
        if event.event == "SNAPSHOT_BEGIN":
            if begin is not None:
                raise ShadowPipelineError("nested shadow snapshot")
            begin = event
            collected = []
            continue
        if event.event == "SNAPSHOT_END":
            if begin is None:
                raise ShadowPipelineError("SNAPSHOT_END without SNAPSHOT_BEGIN")
            if event.fields.get("reason") != begin.fields.get("reason"):
                raise ShadowPipelineError("snapshot reason mismatch")
            completed.append((begin, list(collected), event))
            begin = None
            collected = []
            continue
        if begin is not None and event.event in ENTITY_EVENTS:
            collected.append(event)

    if begin is not None:
        raise ShadowPipelineError("unterminated shadow snapshot")

    canonical = [
        snapshot
        for snapshot in completed
        if snapshot[0].fields.get("reason") == "LOCAL_FACTION_TURN_START"
    ]
    if len(canonical) != 1:
        raise ShadowPipelineError(
            f"expected exactly one LOCAL_FACTION_TURN_START snapshot, found {len(canonical)}"
        )
    return canonical[0]


def _previous_objectives(path: Path | None) -> dict[str, dict[str, object]]:
    if path is None:
        return {}
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    assignments = data.get("assignments")
    if assignments is None and isinstance(data.get("decision"), dict):
        assignments = data["decision"].get("assignments")
    if not isinstance(assignments, list):
        raise ShadowPipelineError("previous assignment file has no assignments list")

    result: dict[str, dict[str, object]] = {}
    for item in assignments:
        if not isinstance(item, dict):
            continue
        army_id = item.get("army_id")
        objective = item.get("objective")
        if isinstance(army_id, str) and isinstance(objective, dict):
            result[army_id] = {
                "type": objective.get("type"),
                "target_id": objective.get("target_id"),
            }
    return result


def _distance(left: dict[str, Any], right: dict[str, Any]) -> float:
    return math.hypot(float(left["x"]) - float(right["x"]), float(left["y"]) - float(right["y"]))


def build_shadow_scenario(
    events: list[ProbeEvent],
    *,
    previous_assignments: Path | None = None,
) -> tuple[dict[str, object], dict[str, object]]:
    begin, entities, end = _canonical_snapshot(events)
    controlled = begin.fields.get("local_faction")
    if not controlled or controlled == "unknown":
        raise ShadowPipelineError("canonical snapshot has no local faction")
    turn = _int(begin.fields, "turn")
    if turn < 1:
        raise ShadowPipelineError("canonical snapshot has invalid turn")

    previous = _previous_objectives(previous_assignments)
    armies: list[dict[str, object]] = []
    regions_by_id: dict[str, tuple[str, dict[str, object]]] = {}
    region_overlap_resolution_count = 0
    filtered_force_count = 0
    legacy_nonfield_force_count = 0
    field_army_garrison_exclusion_count = 0
    wars: list[list[str]] = []
    provenance: dict[str, object] = {
        "canonical_snapshot_reason": "LOCAL_FACTION_TURN_START",
        "foreign_entity_source": "WH3_PLAYER_FILTERED_LISTS",
        "controlled_army_strength": "OWN_UNIT_COUNT_TIMES_HEALTH_PROXY",
        "controlled_army_exact_strength": "OBSERVED_FOR_TELEMETRY_NOT_CROSS_FACTION_SCORING",
        "controlled_army_replenishment": "AVERAGE_UNIT_SOLDIER_PERCENT",
        "controlled_army_movement": "MOVEMENT_REMAINING_PERCENT_PROXY",
        "foreign_army_strength": "VISIBLE_UNIT_COUNT_PROXY",
        "owned_region_garrison": "ARMED_CITIZENRY_UNIT_COUNT_OR_STRUCTURE_PROXY",
        "foreign_region_garrison": "SETTLEMENT_STRUCTURE_PROXY_NOT_ACTUAL_GARRISON",
        "region_threat": "VISIBLE_HOSTILE_ARMY_DISTANCE_PROXY_PLUS_SIEGE",
        "region_identity_resolution": "OWN_RECORD_PRECEDENCE_OVER_VISIBLE_DUPLICATE",
    }

    for event in entities:
        fields = event.fields
        if event.event == "SHADOW_ARMY":
            force_cqi = _int(fields, "force_cqi")
            army_id = f"force:{force_cqi}"
            movement_pct = max(0.0, _float(fields, "movement_remaining_pct", 0.0))
            action_points = max(0.0, _float(fields, "action_points_per_turn", 0.0))
            movement_proxy = max(1.0, movement_pct)
            health_pct = _float(fields, "average_unit_health_pct", -1.0)
            replenishment = (
                max(0.0, min(1.0, health_pct / 100.0))
                if health_pct >= 0
                else 1.0
            )
            unit_count = max(0, _int(fields, "unit_count"))
            planner_eligible_raw = fields.get("planner_eligible")
            if planner_eligible_raw is None:
                planner_eligible = unit_count > 1
                if not planner_eligible:
                    legacy_nonfield_force_count += 1
            else:
                planner_eligible = _bool(fields, "planner_eligible")
            if not planner_eligible:
                filtered_force_count += 1
                continue

            exact_strength = _float(fields, "force_strength", -1.0)
            strength_proxy = float(unit_count * 10) * replenishment
            army: dict[str, object] = {
                "id": army_id,
                "faction": controlled,
                "strength": max(0.0, strength_proxy),
                "x": _float(fields, "x", 0.0),
                "y": _float(fields, "y", 0.0),
                "movement": movement_proxy,
                "replenishment": replenishment,
                "visible_to": [controlled],
                "observation": {
                    "force_cqi": force_cqi,
                    "general_cqi": _int(fields, "general_cqi"),
                    "subtype": fields.get("subtype"),
                    "character_type_key": fields.get("character_type_key"),
                    "is_army": _bool(fields, "is_army", True),
                    "planner_eligible": planner_eligible,
                    "unit_count": unit_count,
                    "exact_force_strength": exact_strength,
                    "planner_strength_proxy": strength_proxy,
                    "planner_strength_source": "OWN_UNIT_COUNT_TIMES_HEALTH_PROXY",
                    "movement_remaining_pct": movement_pct,
                    "action_points_per_turn": action_points,
                    "average_unit_health_pct": health_pct,
                    "stance": fields.get("stance"),
                    "region": fields.get("region"),
                },
            }
            if army_id in previous:
                army["current_objective"] = previous[army_id]
            armies.append(army)

        elif event.event == "SHADOW_VISIBLE_ARMY":
            character_cqi = _int(fields, "character_cqi")
            unit_count = max(0, _int(fields, "unit_count"))
            planner_eligible_raw = fields.get("planner_eligible")
            planner_eligible = (
                unit_count > 1
                if planner_eligible_raw is None
                else _bool(fields, "planner_eligible")
            )
            if not planner_eligible:
                filtered_force_count += 1
                if planner_eligible_raw is None:
                    legacy_nonfield_force_count += 1
                continue
            armies.append(
                {
                    "id": f"visible-character:{character_cqi}",
                    "faction": fields.get("faction", "unknown"),
                    "strength": float(unit_count * 10),
                    "x": _float(fields, "x", 0.0),
                    "y": _float(fields, "y", 0.0),
                    "movement": 5.0,
                    "replenishment": 1.0,
                    "visible_to": [controlled],
                    "observation": {
                        "character_cqi": character_cqi,
                        "force_cqi": _int(fields, "force_cqi"),
                        "subtype": fields.get("subtype"),
                        "character_type_key": fields.get("character_type_key"),
                        "is_army": _bool(fields, "is_army", True),
                        "planner_eligible": planner_eligible,
                        "unit_count": unit_count,
                        "strength_source": fields.get("strength_source"),
                    },
                }
            )

        elif event.event == "SHADOW_FILTERED_FORCE":
            filtered_force_count += 1

        elif event.event in {"SHADOW_OWN_REGION", "SHADOW_VISIBLE_REGION"}:
            region_id = fields.get("region")
            if not region_id or region_id == "unknown":
                raise ShadowPipelineError("region observation has no stable region id")

            level = max(0, _int(fields, "settlement_level"))
            walled = _bool(fields, "walled")
            under_siege = _bool(fields, "under_siege")
            owner = fields.get("owner", "unknown")
            source_kind = "OWN" if event.event == "SHADOW_OWN_REGION" else "VISIBLE"

            structure_proxy = 25.0 + max(level, 1) * 12.0 + (15.0 if walled else 0.0)
            if source_kind == "OWN":
                if owner != controlled:
                    raise ShadowPipelineError(
                        f"owned region {region_id} reports foreign owner {owner!r}"
                    )
                garrison_units = max(0, _int(fields, "garrison_unit_count"))
                source_field = fields.get("garrison_source")
                armed_citizenry = _bool(
                    fields, "garrison_force_is_armed_citizenry", False
                )
                if source_field == "ARMED_CITIZENRY_FORCE" and armed_citizenry:
                    garrison = max(structure_proxy, garrison_units * 10.0)
                    garrison_source = "ARMED_CITIZENRY_UNIT_COUNT_PROXY"
                else:
                    garrison = structure_proxy
                    garrison_source = "SETTLEMENT_STRUCTURE_PROXY"
                    if _float(fields, "garrison_strength", -1.0) >= 0:
                        field_army_garrison_exclusion_count += 1
            else:
                garrison = structure_proxy
                garrison_source = "SETTLEMENT_STRUCTURE_PROXY"

            region_record: dict[str, object] = {
                "id": region_id,
                "owner": owner,
                "x": _float(fields, "x", 0.0),
                "y": _float(fields, "y", 0.0),
                "value": 0.35 + max(level, 1) * 0.2 + (0.15 if walled else 0.0),
                "threat": 0.8 if under_siege and owner == controlled else 0.0,
                "under_siege": under_siege,
                "garrison_strength": max(0.0, garrison),
                "observation": {
                    "settlement_level": level,
                    "walled": walled,
                    "abandoned": _bool(fields, "abandoned"),
                    "garrison_source": garrison_source,
                    "record_source": source_kind,
                },
            }

            existing = regions_by_id.get(region_id)
            if existing is None:
                regions_by_id[region_id] = (source_kind, region_record)
            else:
                existing_kind, existing_record = existing
                if existing_kind == source_kind:
                    raise ShadowPipelineError(
                        f"duplicate {source_kind.lower()} region record: {region_id}"
                    )
                if existing_record.get("owner") != owner:
                    raise ShadowPipelineError(
                        f"conflicting owners for region {region_id}: "
                        f"{existing_record.get('owner')!r} versus {owner!r}"
                    )

                # WH3's player-visible region list legitimately includes regions
                # already present in the controlled faction's owned-region list.
                # They are two views of one entity, not two scenario regions.
                # The owned record is richer and therefore deterministically wins.
                if source_kind == "OWN":
                    regions_by_id[region_id] = (source_kind, region_record)
                region_overlap_resolution_count += 1

        elif event.event == "WAR":
            left = fields.get("faction_a")
            right = fields.get("faction_b")
            if left and right and left != right:
                pair = [left, right]
                if pair not in wars and [right, left] not in wars:
                    wars.append(pair)

    regions = [record for _, record in regions_by_id.values()]

    own_armies = [army for army in armies if army["faction"] == controlled]
    if not own_armies:
        raise ShadowPipelineError("canonical snapshot contains no controlled armies")
    if not regions:
        raise ShadowPipelineError("canonical snapshot contains no regions")

    hostile_factions = {
        pair[1] if pair[0] == controlled else pair[0]
        for pair in wars
        if controlled in pair
    }
    visible_hostiles = [
        army
        for army in armies
        if army["faction"] in hostile_factions and army["faction"] != controlled
    ]
    for region in regions:
        visible_pressure = 0.0
        for army in visible_hostiles:
            distance = _distance(region, army)
            visible_pressure += float(army["strength"]) / max(distance + 1.0, 1.0) / 100.0
        region["threat"] = round(
            min(1.5, float(region["threat"]) + visible_pressure),
            6,
        )

    scenario: dict[str, object] = {
        "schema_version": 1,
        "scenario_id": f"shadow:{controlled}:turn:{turn}",
        "turn": turn,
        "controlled_faction": controlled,
        "wars": sorted(wars),
        "armies": sorted(armies, key=lambda item: str(item["id"])),
        "regions": sorted(regions, key=lambda item: str(item["id"])),
    }
    metadata: dict[str, object] = {
        "schema_version": 1,
        "input_evidence_label": "UNVERIFIED_LIVE_UNTIL_MANIFEST_REVIEW",
        "decision_evidence_label": "HYPOTHESIS",
        "snapshot_begin_line": begin.line_number,
        "snapshot_end_line": end.line_number,
        "entity_event_count": len(entities),
        "region_overlap_resolution_count": region_overlap_resolution_count,
        "filtered_force_count": filtered_force_count,
        "legacy_nonfield_force_count": legacy_nonfield_force_count,
        "field_army_garrison_exclusion_count": field_army_garrison_exclusion_count,
        "provenance": provenance,
        "warnings": [
            "No game order is emitted; this is shadow mode only.",
            "Foreign army strength uses visible unit count, not privileged force strength.",
            "Foreign garrison strength is a settlement-structure proxy, not observed garrison composition.",
            "Movement scaling and every utility weight remain uncalibrated against WH3 outcomes.",
            "Own and foreign field-army feasibility use unit-count-scale proxies; exact own force strength is retained only as telemetry.",
            "Non-field character forces are excluded from Army Objective Assignment.",
            "A field army standing in a settlement is not counted as the settlement garrison.",
            "Owned regions may also appear in WH3 player-visible region lists; the adapter coalesces them by stable region id and gives the richer owned record precedence.",
        ],
    }
    return scenario, metadata


def run_shadow_pipeline(
    log_paths: list[Path],
    profile_path: Path,
    *,
    previous_assignments: Path | None = None,
) -> dict[str, object]:
    events = parse_logs(log_paths)
    scenario, metadata = build_shadow_scenario(
        events,
        previous_assignments=previous_assignments,
    )
    profile = json.loads(profile_path.read_text(encoding="utf-8-sig"))
    decision = assign_objectives(scenario, profile)
    result: dict[str, object] = {
        "schema_version": 1,
        "mode": "SHADOW_NO_ORDERS",
        "scenario": scenario,
        "metadata": metadata,
        "decision": decision,
    }
    result["result_digest"] = hashlib.sha256(canonical_json(result)).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert a Transcendence shadow probe log into an observer-safe scenario and deterministic objective proposal."
    )
    parser.add_argument("logs", type=Path, nargs="+")
    parser.add_argument(
        "--profile",
        type=Path,
        default=REPO_ROOT / "synthetic_lab/profiles/vanilla_8_1_1.json",
    )
    parser.add_argument("--previous", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    result = run_shadow_pipeline(
        args.logs,
        args.profile,
        previous_assignments=args.previous,
    )
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
