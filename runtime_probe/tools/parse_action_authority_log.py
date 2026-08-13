from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

PREFIX = "TRANS_ACTION"
SUPPORTED_SCHEMAS = {1}
ALLOWED_EVENTS = {
    "PACK_LOADED",
    "RUNTIME_BEGIN",
    "CAPABILITY",
    "BATTLE_START",
    "UNIT_STATIC",
    "SELECTION",
    "COMMAND_OBSERVED",
    "ACTION_WINDOW_OPEN",
    "ACTION_SAMPLE",
    "ACTION_WINDOW_CLOSE",
    "BATTLE_COMPLETE",
}
PROHIBITED_KEYS = {
    "absolute_path", "computer_name", "home", "install_path", "local_path",
    "machine_name", "steam_path", "user", "username", "windows_user",
}
FIELD_RE = re.compile(r"^[a-z][a-z0-9_]*$")
REACHABILITY = {"QUERY_TRUE", "QUERY_FALSE", "UNAVAILABLE", "NOT_APPLICABLE"}
CLOSE_REASONS = {
    "WINDOW_TIMEOUT", "SUBSEQUENT_COMMAND", "CONTROL_LOST", "ROUTED",
    "SHATTERED", "TERMINAL", "UNBOUND_SELECTION",
}


class ActionAuthorityLogError(ValueError):
    pass


@dataclass(frozen=True)
class ActionEvent:
    source: str
    line_number: int
    schema: int
    event: str
    fields: dict[str, str]
    raw: str


def decode_value(value: str) -> str:
    result = value
    for encoded, decoded in (
        ("%0A", "\n"), ("%0D", "\r"), ("%3D", "="),
        ("%7C", "|"), ("%25", "%"),
    ):
        result = result.replace(encoded, decoded)
    return result


def as_bool(value: str) -> bool:
    if value == "true":
        return True
    if value == "false":
        return False
    raise ActionAuthorityLogError(f"not a boolean: {value!r}")


def as_int(value: str) -> int:
    try:
        numeric = float(value)
    except ValueError as error:
        raise ActionAuthorityLogError(f"not an integer: {value!r}") from error
    if not numeric.is_integer():
        raise ActionAuthorityLogError(f"not an integer: {value!r}")
    return int(numeric)


def parse_action_line(source: str, line_number: int, line: str) -> ActionEvent | None:
    marker = f"{PREFIX}|"
    offset = line.find(marker)
    if offset < 0:
        return None
    payload = line[offset:].strip()
    parts = payload.split("|")
    if len(parts) < 3 or parts[0] != PREFIX:
        raise ActionAuthorityLogError(f"{source}:{line_number}: truncated action record")
    try:
        schema = int(parts[1])
    except ValueError as error:
        raise ActionAuthorityLogError(f"{source}:{line_number}: invalid schema") from error
    if schema not in SUPPORTED_SCHEMAS:
        raise ActionAuthorityLogError(f"{source}:{line_number}: unsupported schema {schema}")
    event = decode_value(parts[2])
    if event not in ALLOWED_EVENTS:
        raise ActionAuthorityLogError(f"{source}:{line_number}: unknown event {event!r}")
    fields: dict[str, str] = {}
    for part in parts[3:]:
        if "=" not in part:
            raise ActionAuthorityLogError(f"{source}:{line_number}: malformed field {part!r}")
        key, value = part.split("=", 1)
        key, value = decode_value(key), decode_value(value)
        if not FIELD_RE.match(key):
            raise ActionAuthorityLogError(f"{source}:{line_number}: invalid field {key!r}")
        if key in PROHIBITED_KEYS or key.endswith("_path"):
            raise ActionAuthorityLogError(f"{source}:{line_number}: prohibited private field {key!r}")
        if key in fields:
            raise ActionAuthorityLogError(f"{source}:{line_number}: duplicate field {key!r}")
        fields[key] = value
    return ActionEvent(source, line_number, schema, event, fields, payload)


def parse_action_logs(paths: Iterable[Path]) -> list[ActionEvent]:
    events: list[ActionEvent] = []
    for path in paths:
        for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            event = parse_action_line(path.name, line_number, line)
            if event is not None:
                events.append(event)
    if not events:
        raise ActionAuthorityLogError("no TRANS_ACTION records found")
    return events


def _require(event: ActionEvent, *keys: str) -> None:
    missing = [key for key in keys if key not in event.fields]
    if missing:
        raise ActionAuthorityLogError(
            f"{event.source}:{event.line_number}: {event.event} missing {missing}"
        )


def _ids(value: str) -> list[str]:
    if value == "":
        return []
    values = value.split(",")
    if any(not item for item in values) or len(values) != len(set(values)):
        raise ActionAuthorityLogError("unit identity list is malformed or duplicated")
    return sorted(values)


def validate_action_events(events: list[ActionEvent]) -> list[dict[str, object]]:
    sessions: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    local_units: set[str] = set()
    commands: dict[int, ActionEvent] = {}
    windows: dict[str, dict[str, object]] = {}
    last_time = -1

    def finalize() -> None:
        nonlocal current, local_units, commands, windows, last_time
        if current is None:
            return
        if windows:
            raise ActionAuthorityLogError(f"session ended with open windows: {sorted(windows)}")
        sessions.append(current)
        current = None
        local_units = set()
        commands = {}
        windows = {}
        last_time = -1

    for event in events:
        if event.event == "PACK_LOADED":
            finalize()
            _require(event, "probe_kind", "read_only", "gameplay_mutation", "project_orders_enabled", "unitcontrollers_created", "command_origin_policy", "direct_ack_policy")
            if event.fields["probe_kind"] != "action_authority_shadow":
                raise ActionAuthorityLogError("wrong probe kind")
            if not as_bool(event.fields["read_only"]):
                raise ActionAuthorityLogError("action-authority probe must be read-only")
            if as_bool(event.fields["gameplay_mutation"]):
                raise ActionAuthorityLogError("gameplay mutation must be false")
            if as_bool(event.fields["project_orders_enabled"]):
                raise ActionAuthorityLogError("project orders must be disabled")
            if as_bool(event.fields["unitcontrollers_created"]):
                raise ActionAuthorityLogError("unitcontrollers must remain absent")
            if event.fields["command_origin_policy"] != "GAME_COMMAND_EVENT_ORIGIN_UNRESOLVED":
                raise ActionAuthorityLogError("command-origin policy must remain unresolved")
            if event.fields["direct_ack_policy"] != "UNAVAILABLE_NOT_OBSERVED":
                raise ActionAuthorityLogError("direct acknowledgement policy is invalid")
            current = {
                "source": event.source,
                "schema": event.schema,
                "events": [event],
                "complete": False,
                "capability_failures": [],
            }
            continue
        if current is None:
            raise ActionAuthorityLogError(
                f"{event.source}:{event.line_number}: action event before PACK_LOADED"
            )
        current["events"].append(event)

        time_value = event.fields.get("time_ms")
        if time_value is not None:
            time_ms = as_int(time_value)
            if time_ms < last_time:
                raise ActionAuthorityLogError("action events are out of order")
            last_time = time_ms

        if event.event == "RUNTIME_BEGIN":
            _require(event, "time_ms", "runtime")
            if event.fields["runtime"] != "battle":
                raise ActionAuthorityLogError("action-authority runtime must be battle")
        elif event.event == "CAPABILITY":
            _require(event, "name", "available", "required")
            if not as_bool(event.fields["available"]) and as_bool(event.fields["required"]):
                current["capability_failures"].append(event.fields["name"])
        elif event.event == "BATTLE_START":
            _require(event, "time_ms", "local_alliance", "multiplayer", "replay")
            if as_bool(event.fields["multiplayer"]):
                raise ActionAuthorityLogError("action-authority capture is single-player only")
        elif event.event == "UNIT_STATIC":
            _require(event, "time_ms", "unit_id", "local_alliance", "visibility_source")
            if not as_bool(event.fields["local_alliance"]):
                raise ActionAuthorityLogError("authority probe may emit UNIT_STATIC only for local units")
            if event.fields["visibility_source"] != "LOCAL_ALLIANCE":
                raise ActionAuthorityLogError("local UNIT_STATIC has wrong visibility source")
            unit_id = event.fields["unit_id"]
            if unit_id in local_units:
                raise ActionAuthorityLogError(f"duplicate UNIT_STATIC for {unit_id}")
            local_units.add(unit_id)
        elif event.event == "SELECTION":
            _require(event, "time_ms", "unit_id", "selected", "local_alliance")
            if event.fields["unit_id"] not in local_units:
                raise ActionAuthorityLogError("selection references unknown local unit")
            if not as_bool(event.fields["local_alliance"]):
                raise ActionAuthorityLogError("foreign selection is prohibited")
            as_bool(event.fields["selected"])
        elif event.event == "COMMAND_OBSERVED":
            _require(
                event, "time_ms", "command_index", "command", "selected_unit_ids",
                "command_origin", "project_issue_attempted", "direct_ack_available",
            )
            index = as_int(event.fields["command_index"])
            if index in commands:
                raise ActionAuthorityLogError("duplicate command index")
            selected = _ids(event.fields["selected_unit_ids"])
            if any(unit_id not in local_units for unit_id in selected):
                raise ActionAuthorityLogError("command selection references unknown unit")
            if event.fields["command_origin"] != "GAME_COMMAND_EVENT_ORIGIN_UNRESOLVED":
                raise ActionAuthorityLogError("runtime command origin must remain unresolved")
            if as_bool(event.fields["project_issue_attempted"]):
                raise ActionAuthorityLogError("runtime probe must not report project issue attempt")
            if as_bool(event.fields["direct_ack_available"]):
                raise ActionAuthorityLogError("v0.1R direct acknowledgement is unavailable")
            target = event.fields.get("target_unit_id", "none")
            if "hidden" in target.lower():
                raise ActionAuthorityLogError("hidden target identity leaked")
            commands[index] = event
        elif event.event == "ACTION_WINDOW_OPEN":
            _require(
                event, "time_ms", "window_id", "command_index", "selected_unit_ids",
                "issue_classification", "project_issue_attempted", "direct_ack_available",
            )
            window_id = event.fields["window_id"]
            if window_id in windows:
                raise ActionAuthorityLogError("duplicate action window")
            command_index = as_int(event.fields["command_index"])
            if command_index not in commands:
                raise ActionAuthorityLogError("action window references unknown command")
            selected = _ids(event.fields["selected_unit_ids"])
            command_selected = _ids(commands[command_index].fields["selected_unit_ids"])
            if selected != command_selected:
                raise ActionAuthorityLogError("action window selection differs from command")
            if event.fields["issue_classification"] != "OBSERVED_COMMAND_EVENT_NOT_PROJECT_ISSUE":
                raise ActionAuthorityLogError("invalid issue classification")
            if as_bool(event.fields["project_issue_attempted"]):
                raise ActionAuthorityLogError("project issue attempt is prohibited")
            if as_bool(event.fields["direct_ack_available"]):
                raise ActionAuthorityLogError("direct acknowledgement must remain unavailable")
            windows[window_id] = {
                "open": event,
                "samples": [],
                "actors": selected,
                "command": commands[command_index],
            }
        elif event.event == "ACTION_SAMPLE":
            _require(
                event, "time_ms", "window_id", "sample_index", "unit_id", "local_alliance",
                "controllable", "player_controlled", "ai_controlled", "script_controlled",
                "moving", "idle", "leaving", "routing", "shattered", "reachability",
                "ordered_position_match", "current_target_match",
            )
            window_id = event.fields["window_id"]
            if window_id not in windows:
                raise ActionAuthorityLogError("sample references unknown action window")
            unit_id = event.fields["unit_id"]
            if unit_id not in windows[window_id]["actors"] or unit_id not in local_units:
                raise ActionAuthorityLogError("sample actor is not bound to window")
            if not as_bool(event.fields["local_alliance"]):
                raise ActionAuthorityLogError("foreign action sample is prohibited")
            for key in (
                "controllable", "player_controlled", "ai_controlled", "script_controlled",
                "moving", "idle", "leaving", "routing", "shattered",
                "ordered_position_match", "current_target_match",
            ):
                as_bool(event.fields[key])
            if event.fields["reachability"] not in REACHABILITY:
                raise ActionAuthorityLogError("invalid reachability classification")
            windows[window_id]["samples"].append(event)
        elif event.event == "ACTION_WINDOW_CLOSE":
            _require(
                event, "time_ms", "window_id", "reason", "sample_count",
                "project_issue_attempted", "direct_ack_observed",
            )
            window_id = event.fields["window_id"]
            if window_id not in windows:
                raise ActionAuthorityLogError("close references unknown action window")
            if event.fields["reason"] not in CLOSE_REASONS:
                raise ActionAuthorityLogError("invalid action-window close reason")
            if as_bool(event.fields["project_issue_attempted"]):
                raise ActionAuthorityLogError("project issue attempt is prohibited")
            if as_bool(event.fields["direct_ack_observed"]):
                raise ActionAuthorityLogError("direct acknowledgement must remain false")
            if as_int(event.fields["sample_count"]) != len(windows[window_id]["samples"]):
                raise ActionAuthorityLogError("action-window sample count mismatch")
            windows[window_id]["close"] = event
            current.setdefault("windows", []).append(windows.pop(window_id))
        elif event.event == "BATTLE_COMPLETE":
            _require(event, "time_ms", "project_issue_attempt_count", "direct_ack_count", "commands_observed")
            if as_int(event.fields["project_issue_attempt_count"]) != 0:
                raise ActionAuthorityLogError("project issue count must remain zero")
            if as_int(event.fields["direct_ack_count"]) != 0:
                raise ActionAuthorityLogError("direct acknowledgement count must remain zero")
            if as_int(event.fields["commands_observed"]) != len(commands):
                raise ActionAuthorityLogError("battle-complete command count mismatch")
            if windows:
                raise ActionAuthorityLogError("battle completed with open action windows")
            current["complete"] = True
    finalize()
    return sessions


def summarize_action_events(events: list[ActionEvent]) -> dict[str, object]:
    sessions = validate_action_events(events)
    public: list[dict[str, object]] = []
    for session in sessions:
        counts: dict[str, int] = {}
        for event in session["events"]:
            counts[event.event] = counts.get(event.event, 0) + 1
        windows = session.get("windows", [])
        reachability_counts = {key: 0 for key in sorted(REACHABILITY)}
        close_reason_counts = {key: 0 for key in sorted(CLOSE_REASONS)}
        state_match_counts = {
            "ordered_position_match": 0,
            "current_target_match": 0,
            "movement_observed": 0,
            "leaving_battle_observed": 0,
            "control_lost_observed": 0,
            "routing_observed": 0,
            "shattered_observed": 0,
        }
        for window in windows:
            close_reason_counts[window["close"].fields["reason"]] += 1
            for sample in window["samples"]:
                reachability_counts[sample.fields["reachability"]] += 1
                if as_bool(sample.fields["ordered_position_match"]):
                    state_match_counts["ordered_position_match"] += 1
                if as_bool(sample.fields["current_target_match"]):
                    state_match_counts["current_target_match"] += 1
                if as_bool(sample.fields["moving"]):
                    state_match_counts["movement_observed"] += 1
                if as_bool(sample.fields["leaving"]):
                    state_match_counts["leaving_battle_observed"] += 1
                if not as_bool(sample.fields["controllable"]):
                    state_match_counts["control_lost_observed"] += 1
                if as_bool(sample.fields["routing"]):
                    state_match_counts["routing_observed"] += 1
                if as_bool(sample.fields["shattered"]):
                    state_match_counts["shattered_observed"] += 1
        public.append(
            {
                "source": session["source"],
                "schema": session["schema"],
                "complete": session["complete"],
                "event_counts": dict(sorted(counts.items())),
                "command_event_count": counts.get("COMMAND_OBSERVED", 0),
                "selection_event_count": counts.get("SELECTION", 0),
                "window_count": len(windows),
                "bound_window_count": sum(1 for item in windows if item["actors"]),
                "unbound_window_count": sum(1 for item in windows if not item["actors"]),
                "sample_count": sum(len(item["samples"]) for item in windows),
                "reachability_counts": reachability_counts,
                "state_match_counts": state_match_counts,
                "close_reason_counts": close_reason_counts,
                "project_issue_attempt_count": 0,
                "direct_acknowledgement_count": 0,
                "capability_failures": sorted(set(session["capability_failures"])),
            }
        )
    return {
        "schema_version": 1,
        "authority": "NO_ORDERS",
        "sessions": public,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse Transcendence action-authority logs")
    parser.add_argument("logs", nargs="+", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = summarize_action_events(parse_action_logs(args.logs))
    blob = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(blob, encoding="utf-8")
    print(blob, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
