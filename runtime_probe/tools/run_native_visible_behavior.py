from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "synthetic_lab"))
sys.path.insert(0, str(REPO_ROOT / "runtime_probe" / "tools"))

from parse_probe_log import ProbeEvent, parse_logs
class NativeVisiblePipelineError(ValueError):
    pass


from transcendence_lab.native_visible_behavior import (
    APPLICATION_AUTHORITY,
    AUTHORITY,
    TRACE_CONTRACT,
    VISIBILITY_SOURCE,
    analyze_player_visible_native_trace,
)


ENTITY_EVENTS = {
    "SHADOW_ARMY",
    "SHADOW_VISIBLE_ARMY",
    "SHADOW_OWN_REGION",
    "SHADOW_VISIBLE_REGION",
    "SHADOW_FILTERED_FORCE",
    "WAR",
}


def _extract_snapshots(events: list[ProbeEvent]) -> list[tuple[ProbeEvent, list[ProbeEvent], ProbeEvent]]:
    loaded = [
        event for event in events
        if event.event == "PACK_LOADED" and event.fields.get("probe_kind") == "shadow"
    ]
    if not loaded:
        raise NativeVisiblePipelineError("no shadow PACK_LOADED record found")
    begin: ProbeEvent | None = None
    collected: list[ProbeEvent] = []
    completed: list[tuple[ProbeEvent, list[ProbeEvent], ProbeEvent]] = []
    for event in events:
        if event.event == "SNAPSHOT_BEGIN":
            if begin is not None:
                raise NativeVisiblePipelineError("nested shadow snapshot")
            begin = event
            collected = []
            continue
        if event.event == "SNAPSHOT_END":
            if begin is None:
                raise NativeVisiblePipelineError("SNAPSHOT_END without SNAPSHOT_BEGIN")
            if event.fields.get("reason") != begin.fields.get("reason"):
                raise NativeVisiblePipelineError("snapshot reason mismatch")
            if event.fields.get("turn") != begin.fields.get("turn"):
                raise NativeVisiblePipelineError("snapshot turn mismatch")
            if begin.fields.get("reason") == "LOCAL_FACTION_TURN_START":
                completed.append((begin, list(collected), event))
            begin = None
            collected = []
            continue
        if begin is not None and event.event in ENTITY_EVENTS:
            collected.append(event)
    if begin is not None:
        raise NativeVisiblePipelineError("unterminated shadow snapshot")
    if len(completed) < 2:
        raise NativeVisiblePipelineError("player-visible native behavior trace requires at least two local-faction snapshots")
    return completed


def _float(fields: dict[str, str], key: str) -> float:
    try:
        return float(fields[key])
    except (KeyError, ValueError) as exc:
        raise NativeVisiblePipelineError(f"{key} is required and must be numeric") from exc


def _int(fields: dict[str, str], key: str) -> int:
    try:
        return int(fields[key])
    except (KeyError, ValueError) as exc:
        raise NativeVisiblePipelineError(f"{key} is required and must be an integer") from exc


def _visible_army_record(event: ProbeEvent, observer: str) -> dict[str, Any]:
    fields = event.fields
    force_cqi = _int(fields, "force_cqi")
    character_cqi = _int(fields, "character_cqi")
    stable_id = f"visible-force:{force_cqi}" if force_cqi >= 0 else f"visible-character:{character_cqi}"
    return {
        "id": stable_id,
        "faction": fields.get("faction", "unknown"),
        "x": _float(fields, "x"),
        "y": _float(fields, "y"),
        "visibility_source": VISIBILITY_SOURCE,
        "observer_faction": observer,
    }


def _own_army_record(event: ProbeEvent, observer: str) -> dict[str, Any]:
    fields = event.fields
    force_cqi = _int(fields, "force_cqi")
    return {
        "id": f"observer-force:{force_cqi}",
        "faction": observer,
        "x": _float(fields, "x"),
        "y": _float(fields, "y"),
        "visibility_source": "OBSERVER_OWN_STATE",
        "observer_faction": observer,
    }


def _region_record(event: ProbeEvent, observer: str) -> dict[str, Any]:
    fields = event.fields
    region_id = fields.get("region")
    if not region_id or region_id == "unknown":
        raise NativeVisiblePipelineError("visible behavior region has no stable id")
    owner = fields.get("owner", "unknown")
    return {
        "id": region_id,
        "owner": owner,
        "x": _float(fields, "x"),
        "y": _float(fields, "y"),
        "visibility_source": "OBSERVER_OWN_STATE" if event.event == "SHADOW_OWN_REGION" else VISIBILITY_SOURCE,
        "observer_faction": observer,
    }


def build_player_visible_native_trace(events: list[ProbeEvent], observed_ai_faction: str) -> dict[str, Any]:
    snapshots = _extract_snapshots(events)
    frames: list[dict[str, Any]] = []
    observer: str | None = None
    for begin, entity_events, end in snapshots:
        current_observer = begin.fields.get("local_faction")
        if not current_observer or current_observer == "unknown":
            raise NativeVisiblePipelineError("snapshot local faction is unavailable")
        if observer is None:
            observer = current_observer
        elif observer != current_observer:
            raise NativeVisiblePipelineError("trace spans multiple observer factions")
        if observed_ai_faction == observer:
            raise NativeVisiblePipelineError("observed AI faction must be foreign to the human observer")
        if end.fields.get("visible_armies_available") == "false" or end.fields.get("visible_regions_available") == "false":
            raise NativeVisiblePipelineError("WH3 player-filtered foreign visibility lists were unavailable")

        armies: list[dict[str, Any]] = []
        regions: dict[str, dict[str, Any]] = {}
        for event in entity_events:
            if event.event == "SHADOW_VISIBLE_ARMY":
                armies.append(_visible_army_record(event, current_observer))
            elif event.event == "SHADOW_ARMY":
                armies.append(_own_army_record(event, current_observer))
            elif event.event in {"SHADOW_OWN_REGION", "SHADOW_VISIBLE_REGION"}:
                record = _region_record(event, current_observer)
                prior = regions.get(record["id"])
                if prior is None or event.event == "SHADOW_OWN_REGION":
                    regions[record["id"]] = record
        frames.append(
            {
                "turn": int(begin.fields["turn"]),
                "visible_armies": sorted(armies, key=lambda item: item["id"]),
                "visible_regions": sorted(regions.values(), key=lambda item: item["id"]),
            }
        )

    if observer is None:
        raise NativeVisiblePipelineError("no canonical snapshot")
    trace = {
        "contract": TRACE_CONTRACT,
        "authority": AUTHORITY,
        "application_authority": APPLICATION_AUTHORITY,
        "foreign_visibility_source": VISIBILITY_SOURCE,
        "observer_faction": observer,
        "observed_ai_faction": observed_ai_faction,
        "frames": frames,
    }
    return trace


def run_player_visible_native_behavior(log_paths: list[Path], observed_ai_faction: str) -> dict[str, Any]:
    events = parse_logs(log_paths)
    trace = build_player_visible_native_trace(events, observed_ai_faction)
    analysis = analyze_player_visible_native_trace(trace)
    return {"trace": trace, "analysis": analysis}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Measure only player-visible foreign-AI trajectory proxies from Transcendence shadow logs."
    )
    parser.add_argument("logs", type=Path, nargs="+")
    parser.add_argument("--observed-ai-faction", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_player_visible_native_behavior(args.logs, args.observed_ai_faction)
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


def _shadow_result_frames(report: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    turn_results = report.get("turn_results")
    if not isinstance(turn_results, list) or len(turn_results) < 2:
        raise NativeVisiblePipelineError("shadow result requires at least two turn_results")
    observer: str | None = None
    frames: list[dict[str, Any]] = []
    for turn_result in turn_results:
        if not isinstance(turn_result, dict) or not isinstance(turn_result.get("scenario"), dict):
            raise NativeVisiblePipelineError("shadow turn result is missing scenario")
        scenario = turn_result["scenario"]
        controlled = scenario.get("controlled_faction")
        if not isinstance(controlled, str) or not controlled:
            raise NativeVisiblePipelineError("shadow scenario controlled_faction is unavailable")
        if observer is None:
            observer = controlled
        elif observer != controlled:
            raise NativeVisiblePipelineError("shadow result spans multiple observer factions")
        metadata = turn_result.get("metadata")
        provenance = metadata.get("provenance") if isinstance(metadata, dict) else None
        if not isinstance(provenance, dict) or provenance.get("foreign_entity_source") != VISIBILITY_SOURCE:
            raise NativeVisiblePipelineError("shadow result foreign provenance is not WH3 player-filtered")

        armies: list[dict[str, Any]] = []
        for army in scenario.get("armies", []):
            if not isinstance(army, dict):
                continue
            faction = army.get("faction")
            observation = army.get("observation") if isinstance(army.get("observation"), dict) else {}
            if faction == controlled:
                force_cqi = observation.get("force_cqi")
                army_id = f"observer-force:{force_cqi}" if isinstance(force_cqi, int) else f"observer:{army.get('id')}"
            else:
                if controlled not in army.get("visible_to", []):
                    raise NativeVisiblePipelineError("foreign shadow-result army is not explicitly player-visible")
                force_cqi = observation.get("force_cqi")
                if not isinstance(force_cqi, int):
                    raise NativeVisiblePipelineError("foreign shadow-result army lacks stable force_cqi")
                army_id = f"visible-force:{force_cqi}"
            armies.append(
                {
                    "id": army_id,
                    "faction": faction,
                    "x": float(army["x"]),
                    "y": float(army["y"]),
                }
            )

        regions: list[dict[str, Any]] = []
        for region in scenario.get("regions", []):
            if not isinstance(region, dict):
                continue
            regions.append(
                {
                    "id": str(region["id"]),
                    "owner": str(region["owner"]),
                    "x": float(region["x"]),
                    "y": float(region["y"]),
                }
            )
        frames.append(
            {
                "turn": int(scenario["turn"]),
                "visible_armies": sorted(armies, key=lambda item: item["id"]),
                "visible_regions": sorted(regions, key=lambda item: item["id"]),
            }
        )
    if observer is None:
        raise NativeVisiblePipelineError("shadow result has no observer faction")
    return observer, frames


def observable_ai_factions_from_shadow_result(report: dict[str, Any], *, minimum_frames: int = 2) -> list[str]:
    observer, frames = _shadow_result_frames(report)
    counts: dict[str, int] = {}
    for frame in frames:
        present = {
            army["faction"]
            for army in frame["visible_armies"]
            if army["faction"] != observer
        }
        for faction in present:
            counts[faction] = counts.get(faction, 0) + 1
    return sorted(faction for faction, count in counts.items() if count >= minimum_frames)


def run_player_visible_native_behavior_from_shadow_result(report: dict[str, Any], observed_ai_faction: str) -> dict[str, Any]:
    observer, frames = _shadow_result_frames(report)
    trace = {
        "contract": TRACE_CONTRACT,
        "authority": AUTHORITY,
        "application_authority": APPLICATION_AUTHORITY,
        "foreign_visibility_source": VISIBILITY_SOURCE,
        "observer_faction": observer,
        "observed_ai_faction": observed_ai_faction,
        "frames": frames,
    }
    analysis = analyze_player_visible_native_trace(trace)
    return {"trace": trace, "analysis": analysis}


if __name__ == "__main__":
    raise SystemExit(main())
