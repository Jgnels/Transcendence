from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

PREFIX = "TRANS_PROBE"
SCHEMA = 1
PROHIBITED_KEYS = {
    "absolute_path",
    "computer_name",
    "home",
    "install_path",
    "local_path",
    "machine_name",
    "steam_path",
    "user",
    "username",
    "windows_user",
}
ALLOWED_EVENTS = {
    "PACK_LOADED",
    "RUNTIME_BEGIN",
    "CAPABILITY",
    "ERROR",
    "FIRST_TICK",
    "SNAPSHOT_BEGIN",
    "OWN_ARMY",
    "OWN_REGION",
    "VISIBLE_CHARACTER",
    "VISIBLE_REGION",
    "SNAPSHOT_END",
    "PERSISTENCE_STATE",
    "SHADOW_ARMY",
    "SHADOW_VISIBLE_ARMY",
    "SHADOW_FILTERED_FORCE",
    "SHADOW_OWN_REGION",
    "SHADOW_VISIBLE_REGION",
    "WAR",
    "FEASIBILITY_EXECUTOR_READY",
    "FEASIBILITY_POLL_TICK",
    "FEASIBILITY_REQUEST_SEEN",
    "FEASIBILITY_REQUEST_REJECTED",
    "FEASIBILITY_QUERY_RESULT",
    "FEASIBILITY_PACKET_END",
}
FIELD_RE = re.compile(r"^[a-z][a-z0-9_]*$")


class ProbeLogError(ValueError):
    pass


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


POSITIONAL_SUMMARY_KEYS = {
    "source",
    "start_line",
    "begin_line",
    "end_line",
    "result_digest",
    "semantic_digest",
}


def semantic_projection(value: object) -> object:
    """Remove transport/location metadata from a parsed result.

    The semantic digest must remain stable when a raw log is copied under a
    different filename or unrelated non-probe lines move structured records.
    """

    if isinstance(value, dict):
        return {
            key: semantic_projection(item)
            for key, item in sorted(value.items())
            if key not in POSITIONAL_SUMMARY_KEYS
        }
    if isinstance(value, list):
        return [semantic_projection(item) for item in value]
    return value


def decode_value(value: str) -> str:
    result = value
    replacements = [
        ("%0A", "\n"),
        ("%0D", "\r"),
        ("%3D", "="),
        ("%7C", "|"),
        ("%25", "%"),
    ]
    for encoded, decoded in replacements:
        result = result.replace(encoded, decoded)
    return result


def parse_bool(value: str) -> bool | None:
    if value == "true":
        return True
    if value == "false":
        return False
    if value == "null":
        return None
    raise ProbeLogError(f"not a boolean: {value!r}")


def parse_int(value: str) -> int:
    try:
        return int(value)
    except ValueError as error:
        raise ProbeLogError(f"not an integer: {value!r}") from error


@dataclass(frozen=True)
class ProbeEvent:
    source: str
    line_number: int
    event: str
    fields: dict[str, str]
    raw: str


def parse_probe_line(source: str, line_number: int, line: str) -> ProbeEvent | None:
    marker = f"{PREFIX}|"
    offset = line.find(marker)
    if offset < 0:
        return None
    payload = line[offset:].strip()
    parts = payload.split("|")
    if len(parts) < 3:
        raise ProbeLogError(f"{source}:{line_number}: truncated probe line")
    if parts[0] != PREFIX:
        return None
    try:
        schema = int(parts[1])
    except ValueError as error:
        raise ProbeLogError(f"{source}:{line_number}: invalid schema") from error
    if schema != SCHEMA:
        raise ProbeLogError(f"{source}:{line_number}: unsupported schema {schema}")

    event = decode_value(parts[2])
    if event not in ALLOWED_EVENTS:
        raise ProbeLogError(f"{source}:{line_number}: unknown event {event!r}")

    fields: dict[str, str] = {}
    for part in parts[3:]:
        if "=" not in part:
            raise ProbeLogError(f"{source}:{line_number}: malformed field {part!r}")
        key, value = part.split("=", 1)
        key = decode_value(key)
        value = decode_value(value)
        if not FIELD_RE.match(key):
            raise ProbeLogError(f"{source}:{line_number}: invalid field name {key!r}")
        if key in PROHIBITED_KEYS or key.endswith("_path"):
            raise ProbeLogError(f"{source}:{line_number}: prohibited private field {key!r}")
        if key in fields:
            raise ProbeLogError(f"{source}:{line_number}: duplicate field {key!r}")
        fields[key] = value

    return ProbeEvent(source, line_number, event, fields, payload)


def parse_logs(paths: Iterable[Path]) -> list[ProbeEvent]:
    events: list[ProbeEvent] = []
    for path in paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        for line_number, line in enumerate(text.splitlines(), 1):
            event = parse_probe_line(path.name, line_number, line)
            if event is not None:
                events.append(event)
    if not events:
        raise ProbeLogError("no TRANS_PROBE records found")
    return events


def _snapshot_public_summary(snapshot: dict[str, object]) -> dict[str, object]:
    events: list[ProbeEvent] = snapshot["events"]
    counts: dict[str, int] = {}
    for event in events:
        counts[event.event] = counts.get(event.event, 0) + 1

    end_event: ProbeEvent | None = snapshot.get("end_event")
    return {
        "reason": snapshot["reason"],
        "turn": snapshot["turn"],
        "begin_line": snapshot["begin_line"],
        "end_line": end_event.line_number if end_event else None,
        "event_count": len(events),
        "duplicate_event_count": snapshot["duplicate_event_count"],
        "event_counts": dict(sorted(counts.items())),
        "end_fields": dict(sorted(end_event.fields.items())) if end_event else {},
    }


def _validate_sessions(events: list[ProbeEvent]) -> list[dict[str, object]]:
    sessions: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    current_snapshot: dict[str, object] | None = None
    outside_snapshot_seen: set[str] = set()
    snapshot_occurrences: dict[str, set[int]] = {}
    snapshot_index = -1

    for event in events:
        if event.event == "PACK_LOADED":
            if current:
                if current_snapshot is not None:
                    raise ProbeLogError("session ended with an open snapshot")
                sessions.append(current)

            probe_kind = event.fields.get("probe_kind")
            if probe_kind not in {"observer", "persistence", "shadow", "campaign_feasibility"}:
                raise ProbeLogError("PACK_LOADED missing valid probe_kind")
            current = {
                "probe_kind": probe_kind,
                "source": event.source,
                "start_line": event.line_number,
                "event_count": 1,
                "duplicate_event_count": 0,
                "repeated_across_snapshot_count": 0,
                "events": [event],
                "snapshots": [],
            }
            current_snapshot = None
            outside_snapshot_seen = {event.raw}
            snapshot_occurrences = {}
            snapshot_index = -1
            continue

        if current is None:
            raise ProbeLogError(f"{event.source}:{event.line_number}: event before PACK_LOADED")

        current["event_count"] = int(current["event_count"]) + 1
        current["events"].append(event)

        if event.event == "SNAPSHOT_BEGIN":
            if current["probe_kind"] not in {"observer", "shadow", "campaign_feasibility"}:
                raise ProbeLogError("non-observer session contains a snapshot")
            if current_snapshot is not None:
                raise ProbeLogError("nested SNAPSHOT_BEGIN")
            snapshot_index += 1
            current_snapshot = {
                "reason": event.fields.get("reason", "unknown"),
                "turn": parse_int(event.fields.get("turn", "-1")),
                "begin_line": event.line_number,
                "events": [],
                "seen_raw": set(),
                "duplicate_event_count": 0,
                "end_event": None,
            }
            continue

        if event.event == "SNAPSHOT_END":
            if current_snapshot is None:
                raise ProbeLogError("SNAPSHOT_END without SNAPSHOT_BEGIN")
            if event.fields.get("reason") != current_snapshot["reason"]:
                raise ProbeLogError("SNAPSHOT_END reason does not match SNAPSHOT_BEGIN")
            if parse_int(event.fields.get("turn", "-1")) != current_snapshot["turn"]:
                raise ProbeLogError("SNAPSHOT_END turn does not match SNAPSHOT_BEGIN")
            current_snapshot["end_event"] = event
            current["snapshots"].append(current_snapshot)
            current_snapshot = None
            continue

        if event.event in {
            "OWN_ARMY",
            "OWN_REGION",
            "VISIBLE_CHARACTER",
            "VISIBLE_REGION",
            "SHADOW_ARMY",
            "SHADOW_VISIBLE_ARMY",
            "SHADOW_FILTERED_FORCE",
    "SHADOW_FILTERED_FORCE",
            "SHADOW_OWN_REGION",
            "SHADOW_VISIBLE_REGION",
            "WAR",
        }:
            if current_snapshot is None:
                raise ProbeLogError(f"{event.event} outside a snapshot")

            seen_raw: set[str] = current_snapshot["seen_raw"]
            if event.raw in seen_raw:
                current_snapshot["duplicate_event_count"] = int(current_snapshot["duplicate_event_count"]) + 1
                current["duplicate_event_count"] = int(current["duplicate_event_count"]) + 1
            seen_raw.add(event.raw)

            snapshots_seen = snapshot_occurrences.setdefault(event.raw, set())
            snapshots_seen.add(snapshot_index)
            current["repeated_across_snapshot_count"] = sum(
                1 for snapshot_ids in snapshot_occurrences.values() if len(snapshot_ids) > 1
            )

            current_snapshot["events"].append(event)
            continue

        if event.event == "PERSISTENCE_STATE" and current["probe_kind"] != "persistence":
            raise ProbeLogError("observer session contains persistence state")

        if current_snapshot is not None:
            current_snapshot["events"].append(event)
        else:
            if event.raw in outside_snapshot_seen:
                current["duplicate_event_count"] = int(current["duplicate_event_count"]) + 1
            outside_snapshot_seen.add(event.raw)

    if current:
        if current_snapshot is not None:
            raise ProbeLogError("final session ended with an open snapshot")
        sessions.append(current)

    return sessions


def _int_field(fields: dict[str, str], key: str) -> int | None:
    value = fields.get(key)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _lifecycle_delta(snapshots: list[dict[str, object]]) -> dict[str, object] | None:
    first_tick = next((snapshot for snapshot in snapshots if snapshot["reason"] == "FIRST_TICK"), None)
    turn_start = next((snapshot for snapshot in snapshots if snapshot["reason"] == "LOCAL_FACTION_TURN_START"), None)
    if not first_tick or not turn_start:
        return None

    first_end: ProbeEvent | None = first_tick.get("end_event")
    turn_end: ProbeEvent | None = turn_start.get("end_event")
    if first_end is None or turn_end is None:
        return None

    keys = (
        "own_armies_emitted",
        "own_regions_emitted",
        "visible_characters_emitted",
        "visible_regions_emitted",
        "war_count",
    )
    deltas: dict[str, int] = {}
    for key in keys:
        left = _int_field(first_end.fields, key)
        right = _int_field(turn_end.fields, key)
        if left is not None and right is not None:
            deltas[key] = right - left

    return {
        "first_tick_reason": "FIRST_TICK",
        "canonical_reason": "LOCAL_FACTION_TURN_START",
        "deltas": deltas,
        "different": any(value != 0 for value in deltas.values()),
    }


def summarize(events: list[ProbeEvent]) -> dict[str, object]:
    sessions = _validate_sessions(events)
    public_sessions: list[dict[str, object]] = []
    capability_records: dict[str, bool] = {}
    persistence_states: list[dict[str, int | bool]] = []
    lifecycle_deltas: list[dict[str, object]] = []
    environments: list[dict[str, object]] = []

    for session in sessions:
        session_events: list[ProbeEvent] = session["events"]
        counts: dict[str, int] = {}
        for event in session_events:
            counts[event.event] = counts.get(event.event, 0) + 1
            if event.event == "CAPABILITY":
                name = event.fields.get("name", "unknown")
                available = parse_bool(event.fields.get("available", "false")) is True
                capability_records[name] = available
            elif event.event == "FIRST_TICK":
                environments.append(
                    {
                        "campaign": event.fields.get("campaign"),
                        "turn": _int_field(event.fields, "turn"),
                        "local_faction": event.fields.get("local_faction"),
                        "is_new_game": parse_bool(event.fields.get("is_new_game", "null")),
                        "is_multiplayer": parse_bool(event.fields.get("is_multiplayer", "null")),
                    }
                )
            elif event.event == "PERSISTENCE_STATE":
                persistence_states.append(
                    {
                        "phase": event.fields.get("phase"),
                        "campaign": event.fields.get("campaign"),
                        "turn": _int_field(event.fields, "turn"),
                        "local_faction": event.fields.get("local_faction"),
                        "is_new_game": parse_bool(event.fields.get("is_new_game", "null")),
                        "is_multiplayer": parse_bool(event.fields.get("is_multiplayer", "null")),
                        "key_version": _int_field(event.fields, "key_version"),
                        "previous_found": parse_bool(event.fields["previous_found"]) is True,
                        "previous": parse_int(event.fields["previous"]),
                        "current": parse_int(event.fields["current"]),
                    }
                )

        snapshots: list[dict[str, object]] = session["snapshots"]
        lifecycle = _lifecycle_delta(snapshots)
        if lifecycle is not None:
            lifecycle_deltas.append(lifecycle)

        public_sessions.append(
            {
                "probe_kind": session["probe_kind"],
                "source": session["source"],
                "start_line": session["start_line"],
                "event_count": session["event_count"],
                "duplicate_event_count": session["duplicate_event_count"],
                "repeated_across_snapshot_count": session["repeated_across_snapshot_count"],
                "event_counts": dict(sorted(counts.items())),
                "snapshot_count": len(snapshots),
                "snapshots": [_snapshot_public_summary(snapshot) for snapshot in snapshots],
            }
        )

    observer_events = [
        event
        for event in events
        if event.fields.get("probe_kind") == "observer"
        or event.event
        in {
            "FIRST_TICK",
            "SNAPSHOT_BEGIN",
            "OWN_ARMY",
            "OWN_REGION",
            "VISIBLE_CHARACTER",
            "VISIBLE_REGION",
            "SNAPSHOT_END",
        }
    ]
    first_tick_observed = any(event.event == "FIRST_TICK" for event in observer_events)
    local_turn_start_observed = any(
        event.event == "SNAPSHOT_END"
        and event.fields.get("reason") == "LOCAL_FACTION_TURN_START"
        for event in observer_events
    )
    own_army_observed = any(event.event == "OWN_ARMY" for event in observer_events)
    own_region_observed = any(event.event == "OWN_REGION" for event in observer_events)
    visible_character_probe = any(
        event.event == "SNAPSHOT_END"
        and event.fields.get("visible_characters_available") == "true"
        for event in observer_events
    )
    visible_region_probe = any(
        event.event == "SNAPSHOT_END"
        and event.fields.get("visible_regions_available") == "true"
        for event in observer_events
    )

    shadow_events = [
        event
        for session in sessions
        if session["probe_kind"] == "shadow"
        for event in session["events"]
    ]
    shadow_snapshot_observed = any(
        event.event == "SNAPSHOT_END"
        and event.fields.get("reason") == "LOCAL_FACTION_TURN_START"
        for event in shadow_events
    )
    shadow_army_fields_observed = any(
        event.event == "SHADOW_ARMY"
        and all(
            key in event.fields
            for key in (
                "force_strength",
                "average_unit_health_pct",
                "movement_remaining_pct",
                "action_points_per_turn",
            )
        )
        for event in shadow_events
    )
    shadow_wars_observed = any(event.event == "WAR" for event in shadow_events)
    shadow_region_fields_observed = any(
        event.event in {"SHADOW_OWN_REGION", "SHADOW_VISIBLE_REGION"}
        and all(
            key in event.fields
            for key in ("settlement_level", "walled", "under_siege")
        )
        for event in shadow_events
    )

    persistence_roundtrip = False
    for left, right in zip(persistence_states, persistence_states[1:]):
        if (
            right["previous_found"]
            and right["previous"] == left["current"]
            and right["current"] == right["previous"] + 1
        ):
            persistence_roundtrip = True
            break

    promotions = {
        "campaign_mod_pack_loaded": "OBSERVED" if sessions else "UNVERIFIED",
        "campaign_first_tick_callback": "OBSERVED" if first_tick_observed else "UNVERIFIED",
        "campaign_local_faction_turn_start_snapshot": "OBSERVED" if local_turn_start_observed else "UNVERIFIED",
        "local_army_observation": "OBSERVED" if own_army_observed else "UNVERIFIED",
        "local_region_observation": "OBSERVED" if own_region_observed else "UNVERIFIED",
        "visibility_filtered_foreign_characters": "OBSERVED" if visible_character_probe else "UNVERIFIED",
        "visibility_filtered_foreign_regions": "OBSERVED" if visible_region_probe else "UNVERIFIED",
        "save_reload_saved_value_roundtrip": "REPLICATED" if persistence_roundtrip else "UNVERIFIED",
        "shadow_local_turn_snapshot": "OBSERVED" if shadow_snapshot_observed else "UNVERIFIED",
        "shadow_own_army_strength_movement_health": "OBSERVED" if shadow_army_fields_observed else "UNVERIFIED",
        "shadow_war_identity_observation": "OBSERVED" if shadow_wars_observed else "UNVERIFIED",
        "shadow_region_structure_and_siege": "OBSERVED" if shadow_region_fields_observed else "UNVERIFIED",
    }

    warnings = [
        "Log evidence proves only the calls and fields observed in the supplied sessions.",
        "No campaign objective, order, acknowledgement, or outcome control is promoted by this parser.",
        "Repeated records across different snapshots are expected re-observations and are not duplicate-event defects.",
    ]
    if any(delta["different"] for delta in lifecycle_deltas):
        warnings.append(
            "FIRST_TICK and LOCAL_FACTION_TURN_START snapshots differ; FIRST_TICK is initialization diagnostics only, and LOCAL_FACTION_TURN_START is the canonical planner snapshot."
        )

    result: dict[str, object] = {
        "schema_version": 2,
        "evidence_status": "OBSERVED",
        "session_count": len(sessions),
        "sessions": public_sessions,
        "environments": environments,
        "lifecycle_deltas": lifecycle_deltas,
        "canonical_planner_snapshot_reason": "LOCAL_FACTION_TURN_START" if local_turn_start_observed else None,
        "capability_failures": sorted(name for name, available in capability_records.items() if not available),
        "capability_promotions": promotions,
        "persistence_states": persistence_states,
        "warnings": warnings,
    }
    result["semantic_digest"] = hashlib.sha256(
        canonical_json(semantic_projection(result))
    ).hexdigest()
    result["result_digest"] = hashlib.sha256(canonical_json(result)).hexdigest()
    return result

def main() -> int:
    parser = argparse.ArgumentParser(description="Parse Transcendence WH3 probe records from lua_mod_log files.")
    parser.add_argument("logs", type=Path, nargs="+")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    events = parse_logs(args.logs)
    result = summarize(events)
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
