from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "synthetic_lab"))
sys.path.insert(0, str(REPO_ROOT / "runtime_probe" / "tools"))

from parse_probe_log import ProbeEvent, canonical_json, parse_logs
from run_shadow_assignment import ShadowPipelineError, build_shadow_scenario
from transcendence_lab.decision import assign_objectives


ENTITY_EVENTS = {
    "SHADOW_ARMY",
    "SHADOW_VISIBLE_ARMY",
    "SHADOW_OWN_REGION",
    "SHADOW_VISIBLE_REGION",
    "SHADOW_FILTERED_FORCE",
    "WAR",
}


def _shadow_pack_loaded(events: list[ProbeEvent]) -> ProbeEvent:
    matches = [
        event
        for event in events
        if event.event == "PACK_LOADED"
        and event.fields.get("probe_kind") == "shadow"
    ]
    if not matches:
        raise ShadowPipelineError("no shadow PACK_LOADED record found")
    return matches[0]


def extract_canonical_snapshots(
    events: list[ProbeEvent],
) -> list[tuple[ProbeEvent, list[ProbeEvent], ProbeEvent]]:
    """Return every complete local-faction-turn-start shadow snapshot."""

    _shadow_pack_loaded(events)
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
            if event.fields.get("turn") != begin.fields.get("turn"):
                raise ShadowPipelineError("snapshot turn mismatch")
            if begin.fields.get("reason") == "LOCAL_FACTION_TURN_START":
                completed.append((begin, list(collected), event))
            begin = None
            collected = []
            continue

        if begin is not None and event.event in ENTITY_EVENTS:
            collected.append(event)

    if begin is not None:
        raise ShadowPipelineError("unterminated shadow snapshot")
    if not completed:
        raise ShadowPipelineError("no LOCAL_FACTION_TURN_START shadow snapshot")
    return completed


def _assignment_map(decision: dict[str, object]) -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    assignments = decision.get("assignments")
    if not isinstance(assignments, list):
        return result
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


def _apply_previous_objectives(
    scenario: dict[str, object],
    previous: dict[str, dict[str, object]],
) -> None:
    armies = scenario.get("armies")
    controlled = scenario.get("controlled_faction")
    if not isinstance(armies, list) or not isinstance(controlled, str):
        return
    for army in armies:
        if not isinstance(army, dict):
            continue
        army_id = army.get("id")
        if army.get("faction") == controlled and isinstance(army_id, str):
            objective = previous.get(army_id)
            if objective is not None:
                army["current_objective"] = dict(objective)


def _objective_changes(
    previous: dict[str, dict[str, object]],
    current: dict[str, dict[str, object]],
) -> tuple[int, int]:
    changes = 0
    comparable = 0
    for army_id in sorted(set(previous) & set(current)):
        comparable += 1
        if previous[army_id] != current[army_id]:
            changes += 1
    return changes, comparable


def run_shadow_campaign(
    log_paths: list[Path],
    profile_path: Path,
) -> dict[str, object]:
    events = parse_logs(log_paths)
    pack_loaded = _shadow_pack_loaded(events)
    snapshots = extract_canonical_snapshots(events)
    profile = json.loads(profile_path.read_text(encoding="utf-8-sig"))

    capability_failures = sorted(
        {
            event.fields.get("name", "unknown")
            for event in events
            if event.event == "CAPABILITY"
            and event.fields.get("available") == "false"
        }
    )

    previous: dict[str, dict[str, object]] = {}
    total_changes = 0
    total_comparable = 0
    hold_assignments = 0
    total_assignments = 0
    turns: list[int] = []
    turn_results: list[dict[str, object]] = []
    proxy_violations: list[str] = []
    state_change_count = 0
    previous_scenario_digest: str | None = None

    for begin, entity_events, end in snapshots:
        isolated_events = [pack_loaded, begin, *entity_events, end]
        scenario, metadata = build_shadow_scenario(isolated_events)
        _apply_previous_objectives(scenario, previous)
        decision = assign_objectives(scenario, profile)

        current = _assignment_map(decision)
        changes, comparable = _objective_changes(previous, current)
        if previous:
            total_changes += changes
            total_comparable += comparable

        assignments = decision.get("assignments", [])
        if isinstance(assignments, list):
            total_assignments += len(assignments)
            for assignment in assignments:
                if (
                    isinstance(assignment, dict)
                    and isinstance(assignment.get("objective"), dict)
                    and assignment["objective"].get("type") == "HOLD"
                ):
                    hold_assignments += 1

        scenario_digest = str(decision.get("scenario_digest"))
        if previous_scenario_digest is not None and scenario_digest != previous_scenario_digest:
            state_change_count += 1
        previous_scenario_digest = scenario_digest

        for event in entity_events:
            if (
                event.event == "SHADOW_VISIBLE_ARMY"
                and event.fields.get("strength_source") != "VISIBLE_UNIT_COUNT_PROXY"
            ):
                proxy_violations.append(
                    f"turn {begin.fields.get('turn')}: visible army used "
                    f"{event.fields.get('strength_source')!r}"
                )
            if (
                event.event == "SHADOW_VISIBLE_REGION"
                and event.fields.get("garrison_source")
                != "SETTLEMENT_STRUCTURE_PROXY_ONLY"
            ):
                proxy_violations.append(
                    f"turn {begin.fields.get('turn')}: visible region used "
                    f"{event.fields.get('garrison_source')!r}"
                )
            if (
                event.event == "SHADOW_VISIBLE_ARMY"
                and "force_strength" in event.fields
            ):
                proxy_violations.append(
                    f"turn {begin.fields.get('turn')}: exact foreign force_strength present"
                )

        turn = int(begin.fields["turn"])
        turns.append(turn)
        turn_results.append(
            {
                "turn": turn,
                "scenario": scenario,
                "metadata": metadata,
                "decision": decision,
                "objective_changes_from_previous": changes if previous else 0,
                "comparable_armies_from_previous": comparable if previous else 0,
            }
        )
        previous = current

    consecutive = all(
        right == left + 1 for left, right in zip(turns, turns[1:])
    )
    churn = (
        round(total_changes / total_comparable, 6)
        if total_comparable
        else 0.0
    )
    hold_rate = (
        round(hold_assignments / total_assignments, 6)
        if total_assignments
        else 0.0
    )

    result: dict[str, object] = {
        "schema_version": 1,
        "mode": "SHADOW_NO_ORDERS",
        "evidence_status": "HYPOTHESIS",
        "profile_id": profile.get("profile_id", "unnamed"),
        "turn_results": turn_results,
        "metrics": {
            "turn_count": len(turns),
            "turns": turns,
            "consecutive_turns": consecutive,
            "first_turn": turns[0],
            "last_turn": turns[-1],
            "total_assignments": total_assignments,
            "comparable_assignment_pairs": total_comparable,
            "objective_changes": total_changes,
            "objective_churn_rate": churn,
            "hold_assignments": hold_assignments,
            "hold_rate": hold_rate,
            "scenario_state_change_count": state_change_count,
            "capability_failure_count": len(capability_failures),
            "capability_failures": capability_failures,
            "foreign_proxy_violation_count": len(proxy_violations),
            "foreign_proxy_violations": proxy_violations,
        },
        "authority": {
            "game_orders_emitted": False,
            "save_values_written": False,
            "canonical_game_state_owned": False,
            "proposal_only": True,
        },
        "warnings": [
            "Every proposal is offline shadow output; no campaign order was attempted.",
            "Foreign army strength uses visible unit count rather than exact force strength.",
            "Foreign garrisons use settlement-structure proxies rather than observed composition.",
            "Five-turn stability is not a gameplay-quality claim and remains uncalibrated.",
        ],
    }
    result["result_digest"] = hashlib.sha256(canonical_json(result)).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run the deterministic Army Objective Assignment pipeline over "
            "every local-turn-start snapshot in one WH3 shadow log."
        )
    )
    parser.add_argument("logs", type=Path, nargs="+")
    parser.add_argument(
        "--profile",
        type=Path,
        default=REPO_ROOT / "synthetic_lab/profiles/vanilla_8_1_1.json",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    result = run_shadow_campaign(args.logs, args.profile)
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
