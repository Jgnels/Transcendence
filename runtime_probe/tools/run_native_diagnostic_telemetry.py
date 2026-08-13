from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "synthetic_lab"))
from transcendence_lab.native_diagnostic import (
    APPLICATION_AUTHORITY,
    AUTHORITY,
    RESEARCH_VISIBILITY,
    TRACE_CONTRACT,
    analyze_native_diagnostic_exposure,
)

PREFIX = "TRANS_DIAG"


def _decode(value: str) -> str:
    for encoded, decoded in (("%0A", "\n"), ("%0D", "\r"), ("%3D", "="), ("%7C", "|"), ("%25", "%")):
        value = value.replace(encoded, decoded)
    return value


def _parse_scalar(value: str) -> Any:
    if value == "true": return True
    if value == "false": return False
    if value == "null": return None
    try:
        if value and value.lstrip("-").isdigit(): return int(value)
        return float(value) if any(ch in value for ch in ".eE") else value
    except ValueError:
        return value


def parse_line(line: str) -> tuple[str, dict[str, Any]] | None:
    line = line.strip()
    if not line.startswith(PREFIX + "|"):
        return None
    parts = line.split("|")
    if len(parts) < 3 or parts[1] != "1":
        raise ValueError("unsupported diagnostic log schema")
    event = _decode(parts[2])
    fields: dict[str, Any] = {}
    for item in parts[3:]:
        if "=" not in item:
            raise ValueError(f"malformed diagnostic field: {item!r}")
        key, value = item.split("=", 1)
        key = _decode(key)
        if key in fields:
            raise ValueError(f"duplicate diagnostic field: {key}")
        fields[key] = _parse_scalar(_decode(value))
    return event, fields


def parse_diagnostic_trace(path: Path) -> dict[str, Any]:
    """Parse the complete diagnostic stream while preserving event-order boundaries.

    `parse_diagnostic_log` intentionally returns a compact public summary. The richer
    event-order representation from this function is research-only input for later
    preregistered analyses. It remains NO_ORDERS / application-ineligible.
    """
    events: list[tuple[int, str, dict[str, Any]]] = []
    for event_index, raw in enumerate(path.read_text(encoding="utf-8-sig").splitlines()):
        parsed = parse_line(raw)
        if parsed is not None:
            event, fields = parsed
            events.append((event_index, event, fields))
    if not events:
        raise ValueError("no TRANS_DIAG events found")

    pack = next((fields for _, event, fields in events if event == "PACK_LOADED"), None)
    if not pack:
        raise ValueError("diagnostic PACK_LOADED marker missing")
    expected = {
        "probe_kind": "native_diagnostic",
        "read_only": True,
        "research_visibility": RESEARCH_VISIBILITY,
        "application_eligible": False,
        "authority": AUTHORITY,
        "application_authority": APPLICATION_AUTHORITY,
    }
    for key, value in expected.items():
        if pack.get(key) != value:
            raise ValueError(f"diagnostic marker mismatch for {key}: {pack.get(key)!r}")

    snapshots: dict[tuple[int, str, str], dict[str, Any]] = {}
    human_turn_starts: list[int] = []
    capabilities: list[dict[str, Any]] = []
    skipped_factions: list[dict[str, Any]] = []
    battles: dict[int, dict[str, Any]] = {}

    for event_index, event, fields in events:
        if event == "HUMAN_TURN_MARKER" and fields.get("phase") == "TURN_START":
            human_turn_starts.append(int(fields["turn"]))
        elif event == "CAPABILITY":
            capabilities.append({**fields, "event_index": event_index})
        elif event == "AI_FACTION_SKIPPED":
            skipped_factions.append({**fields, "event_index": event_index})
        elif event == "AI_SNAPSHOT_BEGIN":
            key = (int(fields["turn"]), str(fields["faction"]), str(fields["phase"]))
            if key in snapshots:
                raise ValueError(f"duplicate diagnostic snapshot begin: {key}")
            snapshots[key] = {
                "forces": [], "regions": [], "wars": [], "complete": False,
                "begin_event_index": event_index,
            }
        elif event in {"AI_FORCE", "AI_REGION", "AI_WAR"}:
            key = (int(fields["turn"]), str(fields["faction"]), str(fields["phase"]))
            if key not in snapshots:
                raise ValueError(f"diagnostic row before snapshot begin: {key}")
            bucket = {"AI_FORCE": "forces", "AI_REGION": "regions", "AI_WAR": "wars"}[event]
            snapshots[key][bucket].append({**fields, "event_index": event_index})
        elif event == "AI_SNAPSHOT_END":
            key = (int(fields["turn"]), str(fields["faction"]), str(fields["phase"]))
            if key not in snapshots:
                raise ValueError(f"diagnostic snapshot end before begin: {key}")
            snapshots[key]["complete"] = True
            snapshots[key]["end_fields"] = fields
            snapshots[key]["end_event_index"] = event_index
            counts = {
                "forces": int(fields.get("forces_emitted", -1)),
                "regions": int(fields.get("regions_emitted", -1)),
                "wars": int(fields.get("wars_emitted", -1)),
            }
            for bucket, expected_count in counts.items():
                if expected_count >= 0 and len(snapshots[key][bucket]) != expected_count:
                    raise ValueError(f"diagnostic {bucket} count mismatch for {key}")
        elif event == "AI_BATTLE_BEGIN":
            battle_sequence = int(fields["battle_sequence"])
            if battle_sequence in battles:
                raise ValueError(f"duplicate diagnostic battle begin: {battle_sequence}")
            battles[battle_sequence] = {
                "battle_sequence": battle_sequence,
                "turn": int(fields["turn"]),
                "begin_event_index": event_index,
                "begin_fields": fields,
                "participants": [],
                "complete": False,
            }
        elif event == "AI_BATTLE_PARTICIPANT":
            battle_sequence = int(fields["battle_sequence"])
            battle = battles.get(battle_sequence)
            if battle is None:
                raise ValueError(f"diagnostic battle participant before begin: {battle_sequence}")
            battle["participants"].append({**fields, "event_index": event_index})
        elif event == "AI_BATTLE_END":
            battle_sequence = int(fields["battle_sequence"])
            battle = battles.get(battle_sequence)
            if battle is None:
                raise ValueError(f"diagnostic battle end before begin: {battle_sequence}")
            battle["complete"] = True
            battle["end_event_index"] = event_index
            battle["end_fields"] = fields
            expected_attackers = int(fields.get("attackers_emitted", -1))
            expected_defenders = int(fields.get("defenders_emitted", -1))
            actual_attackers = sum(1 for row in battle["participants"] if row.get("side") == "ATTACKER")
            actual_defenders = sum(1 for row in battle["participants"] if row.get("side") == "DEFENDER")
            if expected_attackers >= 0 and actual_attackers != expected_attackers:
                raise ValueError(f"diagnostic attacker count mismatch for battle {battle_sequence}")
            if expected_defenders >= 0 and actual_defenders != expected_defenders:
                raise ValueError(f"diagnostic defender count mismatch for battle {battle_sequence}")

    paired: list[dict[str, Any]] = []
    incomplete: list[dict[str, Any]] = []
    keys = {(turn, faction) for turn, faction, _ in snapshots}
    for turn, faction in sorted(keys):
        start = snapshots.get((turn, faction, "TURN_START"))
        end = snapshots.get((turn, faction, "TURN_END"))
        if start and end and start.get("complete") and end.get("complete"):
            paired.append({"turn": turn, "faction": faction, "start": start, "end": end})
        else:
            incomplete.append({
                "turn": turn,
                "faction": faction,
                "has_start": bool(start and start.get("complete")),
                "has_end": bool(end and end.get("complete")),
            })

    complete_battles = [battles[key] for key in sorted(battles) if battles[key].get("complete")]
    incomplete_battles = [
        {"battle_sequence": key, "turn": battles[key].get("turn"), "participant_count": len(battles[key].get("participants", []))}
        for key in sorted(battles) if not battles[key].get("complete")
    ]
    unique_human_turns = sorted(set(human_turn_starts))
    consecutive = all(b - a == 1 for a, b in zip(unique_human_turns, unique_human_turns[1:]))

    return {
        "contract": "NATIVE_CAI_PRIVILEGED_DIAGNOSTIC_PARSED_TRACE_V2",
        "authority": AUTHORITY,
        "application_authority": APPLICATION_AUTHORITY,
        "research_visibility": RESEARCH_VISIBILITY,
        "application_eligible": False,
        "battle_participant_telemetry_declared": pack.get("battle_participant_telemetry") is True,
        "human_turn_starts": unique_human_turns,
        "human_turns_consecutive": consecutive,
        "observations": paired,
        "incomplete_ai_faction_turns": incomplete,
        "capabilities": capabilities,
        "skipped_factions": skipped_factions,
        "battle_sequences": complete_battles,
        "incomplete_battle_sequences": incomplete_battles,
    }


def parse_diagnostic_log(path: Path) -> dict[str, Any]:
    parsed = parse_diagnostic_trace(path)
    trace = {
        "contract": TRACE_CONTRACT,
        "authority": AUTHORITY,
        "application_authority": APPLICATION_AUTHORITY,
        "research_visibility": RESEARCH_VISIBILITY,
        "application_eligible": False,
        "observations": parsed["observations"],
    }
    analysis = analyze_native_diagnostic_exposure(trace)
    return {
        "contract": "NATIVE_CAI_PRIVILEGED_DIAGNOSTIC_RUNTIME_SUMMARY_V2",
        "authority": AUTHORITY,
        "application_authority": APPLICATION_AUTHORITY,
        "research_visibility": RESEARCH_VISIBILITY,
        "application_eligible": False,
        "battle_participant_telemetry_declared": parsed["battle_participant_telemetry_declared"],
        "human_turn_starts": parsed["human_turn_starts"],
        "human_turns_consecutive": parsed["human_turns_consecutive"],
        "paired_ai_faction_turns": len(parsed["observations"]),
        "incomplete_ai_faction_turns": parsed["incomplete_ai_faction_turns"],
        "capability_failure_count": len([row for row in parsed["capabilities"] if row.get("available") is False]),
        "skipped_faction_event_count": len(parsed["skipped_factions"]),
        "complete_battle_sequence_count": len(parsed["battle_sequences"]),
        "incomplete_battle_sequence_count": len(parsed["incomplete_battle_sequences"]),
        "analysis": analysis,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse and qualify research-only native CAI diagnostic telemetry.")
    parser.add_argument("log", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = parse_diagnostic_log(args.log)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
