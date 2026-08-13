from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

PREFIX = "TRANS_BATTLE"
SUPPORTED_SCHEMAS = {1, 2}
ALLOWED_EVENTS = {
    "PACK_LOADED",
    "RUNTIME_BEGIN",
    "CAPABILITY",
    "ERROR",
    "BATTLE_START",
    "ARMY_STATIC",
    "PHASE",
    "SAMPLER_START",
    "SAMPLER_HEARTBEAT",
    "SAMPLE_BEGIN",
    "UNIT_STATIC",
    "UNIT_HIERARCHY",
    "UNIT_STATE",
    "SAMPLE_END",
    "ALLIANCE_AGGREGATE",
    "SELECTION",
    "COMMAND",
    "BATTLE_COMPLETE",
}
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
FIELD_RE = re.compile(r"^[a-z][a-z0-9_]*$")


class BattleLogError(ValueError):
    pass


def canonical_json(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def decode_value(value: str) -> str:
    result = value
    for encoded, decoded in (
        ("%0A", "\n"),
        ("%0D", "\r"),
        ("%3D", "="),
        ("%7C", "|"),
        ("%25", "%"),
    ):
        result = result.replace(encoded, decoded)
    return result


def as_bool(value: str) -> bool:
    if value == "true":
        return True
    if value == "false":
        return False
    raise BattleLogError(f"not a boolean: {value!r}")


def as_int(value: str) -> int:
    try:
        return int(float(value))
    except ValueError as error:
        raise BattleLogError(f"not an integer: {value!r}") from error


def as_float(value: str) -> float:
    try:
        return float(value)
    except ValueError as error:
        raise BattleLogError(f"not a number: {value!r}") from error


@dataclass(frozen=True)
class BattleEvent:
    source: str
    line_number: int
    schema: int
    event: str
    fields: dict[str, str]
    raw: str


def parse_battle_line(source: str, line_number: int, line: str) -> BattleEvent | None:
    marker = f"{PREFIX}|"
    offset = line.find(marker)
    if offset < 0:
        return None
    payload = line[offset:].strip()
    parts = payload.split("|")
    if len(parts) < 3:
        raise BattleLogError(f"{source}:{line_number}: truncated battle record")
    if parts[0] != PREFIX:
        return None
    try:
        schema = int(parts[1])
    except ValueError as error:
        raise BattleLogError(f"{source}:{line_number}: invalid schema") from error
    if schema not in SUPPORTED_SCHEMAS:
        raise BattleLogError(f"{source}:{line_number}: unsupported schema {schema}")
    event = decode_value(parts[2])
    if event not in ALLOWED_EVENTS:
        raise BattleLogError(f"{source}:{line_number}: unknown event {event!r}")
    fields: dict[str, str] = {}
    for part in parts[3:]:
        if "=" not in part:
            raise BattleLogError(f"{source}:{line_number}: malformed field {part!r}")
        key, value = part.split("=", 1)
        key = decode_value(key)
        value = decode_value(value)
        if not FIELD_RE.match(key):
            raise BattleLogError(f"{source}:{line_number}: invalid field {key!r}")
        if key in PROHIBITED_KEYS or key.endswith("_path"):
            raise BattleLogError(f"{source}:{line_number}: prohibited private field {key!r}")
        if key in fields:
            raise BattleLogError(f"{source}:{line_number}: duplicate field {key!r}")
        fields[key] = value
    return BattleEvent(source, line_number, schema, event, fields, payload)


def parse_battle_logs(paths: Iterable[Path]) -> list[BattleEvent]:
    events: list[BattleEvent] = []
    for path in paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        for line_number, line in enumerate(text.splitlines(), 1):
            parsed = parse_battle_line(path.name, line_number, line)
            if parsed is not None:
                events.append(parsed)
    if not events:
        raise BattleLogError("no TRANS_BATTLE records found")
    return events


def _require(fields: dict[str, str], keys: tuple[str, ...], event: BattleEvent) -> None:
    missing = [key for key in keys if key not in fields]
    if missing:
        raise BattleLogError(
            f"{event.source}:{event.line_number}: {event.event} missing {missing}"
        )


def stable_unit_id(fields: dict[str, str]) -> str:
    """Return the project-owned stable identity for schema-1 or schema-2 records."""
    explicit = fields.get("stable_unit_id")
    if explicit:
        return explicit
    unit_id = fields.get("unit_id", "")
    if ":u" in unit_id and unit_id.count(":") == 1:
        return unit_id
    parts = unit_id.split(":")
    if len(parts) >= 2:
        alliance = fields.get("alliance_index", parts[0])
        unique_ui_id = fields.get("unique_ui_id", parts[-1])
        if unique_ui_id not in {"", "-1", "null"}:
            return f"{alliance}:u{unique_ui_id}"
    return unit_id


def validate_battle_events(events: list[BattleEvent]) -> list[dict[str, object]]:
    sessions: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    open_sample: int | None = None
    static_units: set[str] = set()
    pending_hierarchy: dict[str, BattleEvent] = {}

    def finalize_session(session: dict[str, object] | None) -> None:
        if session is None:
            return
        if open_sample is not None:
            raise BattleLogError("battle session ended with an open sample")
        if pending_hierarchy:
            unresolved = ", ".join(sorted(pending_hierarchy))
            raise BattleLogError(
                f"UNIT_HIERARCHY identities never received UNIT_STATIC: {unresolved}"
            )
        sessions.append(session)

    for event in events:
        if event.event == "PACK_LOADED":
            finalize_session(current)
            if event.fields.get("probe_kind") not in {"battle_shadow", "battle_replay_shadow"}:
                raise BattleLogError("battle PACK_LOADED has wrong probe_kind")
            current = {
                "source": event.source,
                "start_line": event.line_number,
                "schema": event.schema,
                "events": [event],
                "event_count": 1,
                "capability_failures": [],
                "optional_unavailable": [],
                "sample_count": 0,
                "complete": False,
            }
            open_sample = None
            static_units = set()
            pending_hierarchy = {}
            continue

        if current is None:
            raise BattleLogError(
                f"{event.source}:{event.line_number}: battle event before PACK_LOADED"
            )
        current["events"].append(event)
        current["event_count"] = int(current["event_count"]) + 1

        if event.event == "CAPABILITY":
            _require(event.fields, ("name", "available"), event)
            required = as_bool(event.fields.get("required", "true"))
            if event.fields["available"] != "true":
                target = "capability_failures" if required else "optional_unavailable"
                current[target].append(event.fields["name"])
        elif event.event == "BATTLE_START":
            _require(
                event.fields,
                ("time_ms", "from_campaign", "multiplayer", "battle_type", "local_alliance"),
                event,
            )
            if current.get("battle_start") is not None:
                raise BattleLogError("duplicate BATTLE_START")
            current["battle_start"] = event
        elif event.event == "SAMPLER_START":
            _require(event.fields, ("detail_interval_ms", "aggregate_interval_ms"), event)
        elif event.event == "SAMPLE_BEGIN":
            _require(event.fields, ("sample_index", "time_ms", "reason"), event)
            if open_sample is not None:
                raise BattleLogError("nested SAMPLE_BEGIN")
            open_sample = as_int(event.fields["sample_index"])
        elif event.event == "SAMPLE_END":
            _require(event.fields, ("sample_index", "time_ms", "observed_units"), event)
            index = as_int(event.fields["sample_index"])
            if open_sample != index:
                raise BattleLogError("SAMPLE_END does not match SAMPLE_BEGIN")
            open_sample = None
            current["sample_count"] = int(current["sample_count"]) + 1
        elif event.event in {"UNIT_STATIC", "UNIT_HIERARCHY", "UNIT_STATE"}:
            _require(
                event.fields,
                ("unit_id", "alliance_index", "local_alliance", "visibility_source"),
                event,
            )
            is_local = as_bool(event.fields["local_alliance"])
            visibility = event.fields["visibility_source"]
            if not is_local and visibility != "VISIBLE_TO_LOCAL_ALLIANCE":
                raise BattleLogError(
                    f"{event.source}:{event.line_number}: foreign unit leaked without visibility"
                )
            unit_key = stable_unit_id(event.fields)
            if event.event == "UNIT_HIERARCHY":
                # The runtime deliberately emits hierarchy discovery before the
                # first static record so identity transitions are never hidden.
                # It is valid only when a matching UNIT_STATIC appears later in
                # the same session.
                if unit_key not in static_units:
                    pending_hierarchy.setdefault(unit_key, event)
            elif event.event == "UNIT_STATIC":
                if unit_key in static_units:
                    # Schema 1 used hierarchy indexes inside identity and can emit aliases.
                    if event.schema >= 2:
                        raise BattleLogError(f"duplicate UNIT_STATIC for {unit_key}")
                static_units.add(unit_key)
                pending_hierarchy.pop(unit_key, None)
            elif unit_key not in static_units:
                raise BattleLogError(f"{event.event} before UNIT_STATIC for {unit_key}")
            target = event.fields.get("current_target_id")
            if target and target != "hidden" and "HIDDEN" in target:
                raise BattleLogError("hidden target identity leaked")
        elif event.event == "COMMAND":
            _require(event.fields, ("time_ms", "command", "selected_unit_ids"), event)
        elif event.event == "BATTLE_COMPLETE":
            _require(event.fields, ("time_ms", "outcome_decided", "victorious_alliance"), event)
            current["complete"] = True
            current["battle_complete"] = event

    finalize_session(current)
    return sessions


def summarize_battle(events: list[BattleEvent]) -> dict[str, object]:
    sessions = validate_battle_events(events)
    public_sessions: list[dict[str, object]] = []
    for session in sessions:
        event_counts: dict[str, int] = {}
        for event in session["events"]:
            event_counts[event.event] = event_counts.get(event.event, 0) + 1
        start: BattleEvent | None = session.get("battle_start")
        complete: BattleEvent | None = session.get("battle_complete")
        public_sessions.append(
            {
                "source": session["source"],
                "start_line": session["start_line"],
                "schema": session["schema"],
                "event_count": session["event_count"],
                "event_counts": dict(sorted(event_counts.items())),
                "sample_count": session["sample_count"],
                "complete": session["complete"],
                "capability_failures": sorted(set(session["capability_failures"])),
                "optional_unavailable": sorted(set(session["optional_unavailable"])),
                "battle_start": dict(sorted(start.fields.items())) if start else None,
                "battle_complete": dict(sorted(complete.fields.items())) if complete else None,
            }
        )

    result: dict[str, object] = {
        "schema_version": 2,
        "evidence_status": "OBSERVED",
        "battle_session_count": len(sessions),
        "completed_battle_count": sum(1 for session in sessions if session["complete"]),
        "sessions": public_sessions,
        "capability_failures": sorted(
            {
                failure
                for session in sessions
                for failure in session["capability_failures"]
            }
        ),
        "optional_unavailable": sorted(
            {
                field
                for session in sessions
                for field in session["optional_unavailable"]
            }
        ),
        "warnings": [
            "Battle records prove only observed query and event availability.",
            "No battle order, unitcontroller, AI replacement, or tactical-quality claim is promoted.",
            "Foreign unit records are accepted only when marked visible to the local alliance.",
            "Unavailable optional fields are disclosed separately and do not invalidate the minimum gate.",
        ],
    }
    semantic = {key: value for key, value in result.items() if key != "result_digest"}
    result["result_digest"] = hashlib.sha256(canonical_json(semantic)).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse Transcendence battle telemetry.")
    parser.add_argument("logs", type=Path, nargs="+")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = summarize_battle(parse_battle_logs(args.logs))
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
