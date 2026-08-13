from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import replace
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "synthetic_lab"))
sys.path.insert(0, str(REPO_ROOT / "runtime_probe" / "tools"))

from parse_probe_log import ProbeEvent, parse_logs
from run_shadow_assignment import ENTITY_EVENTS, build_shadow_scenario
from transcendence_lab.campaign_challenge import evaluate_campaign_snapshot
from transcendence_lab.strategic_assignment import build_theater_to_army_assignment
from transcendence_lab.strategic_feasibility import build_campaign_strategic_feasibility_plan
from transcendence_lab.strategic_portfolio import build_strategic_theater_portfolio

PROBE_KIND = "campaign_feasibility"
REQUEST_PREFIX = "TRANS_FEAS_REQ"
REQUEST_SCHEMA = "1"
MAX_QUERIES = 16
SEVERITY_RANK = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temp, path)


def _encode(value: Any) -> str:
    if value is None:
        text = "null"
    elif value is True:
        text = "true"
    elif value is False:
        text = "false"
    else:
        text = str(value)
    return (
        text.replace("%", "%25")
        .replace("|", "%7C")
        .replace("=", "%3D")
        .replace("\r", "%0D")
        .replace("\n", "%0A")
    )


def _request_text(plan: dict[str, Any]) -> str:
    queries = plan["queries"]
    if not 1 <= len(queries) <= MAX_QUERIES:
        raise ValueError(f"live request query count out of bounds: {len(queries)}")
    header_fields = {
        "plan_digest": plan["result_digest"],
        "scenario_id": plan["scenario_id"],
        "turn": plan["turn"],
        "assignment_id": plan["source_assignment_id"],
        "query_count": len(queries),
        "authority": plan["authority"],
        "application_authority": plan["application_authority"],
    }
    lines = [
        "|".join(
            [REQUEST_PREFIX, REQUEST_SCHEMA, "REQUEST"]
            + [f"{_encode(key)}={_encode(value)}" for key, value in header_fields.items()]
        )
    ]
    for query in queries:
        fields: dict[str, Any] = {
            "plan_digest": plan["result_digest"],
            "query_id": query["query_id"],
            "query_key": query["query_key"],
        }
        for key, value in query["parameters"].items():
            fields[key] = value
        lines.append(
            "|".join(
                [REQUEST_PREFIX, REQUEST_SCHEMA, "QUERY"]
                + [f"{_encode(key)}={_encode(value)}" for key, value in fields.items()]
            )
        )
    return "\n".join(lines) + "\n"


def _complete_snapshots(events: list[ProbeEvent]) -> list[tuple[ProbeEvent, list[ProbeEvent], ProbeEvent]]:
    if not any(
        event.event == "PACK_LOADED" and event.fields.get("probe_kind") == PROBE_KIND
        for event in events
    ):
        return []
    begin: ProbeEvent | None = None
    collected: list[ProbeEvent] = []
    completed: list[tuple[ProbeEvent, list[ProbeEvent], ProbeEvent]] = []
    for event in events:
        if event.event == "SNAPSHOT_BEGIN":
            if begin is not None:
                begin = None
                collected = []
                continue
            begin = event
            collected = []
            continue
        if event.event == "SNAPSHOT_END":
            if begin is None:
                continue
            if event.fields.get("reason") == begin.fields.get("reason") and event.fields.get("turn") == begin.fields.get("turn"):
                if begin.fields.get("reason") in {"LOCAL_FACTION_FIRST_TICK", "LOCAL_FACTION_TURN_START"}:
                    completed.append((begin, list(collected), event))
            begin = None
            collected = []
            continue
        if begin is not None and event.event in ENTITY_EVENTS:
            collected.append(event)
    return completed


def _normalize_snapshot(snapshot: tuple[ProbeEvent, list[ProbeEvent], ProbeEvent]) -> list[ProbeEvent]:
    begin, entities, end = snapshot
    fake_pack = ProbeEvent(
        source=begin.source,
        line_number=max(0, begin.line_number - 1),
        event="PACK_LOADED",
        fields={"probe_kind": "shadow"},
        raw="",
    )
    begin_fields = dict(begin.fields)
    end_fields = dict(end.fields)
    begin_fields["reason"] = "LOCAL_FACTION_TURN_START"
    end_fields["reason"] = "LOCAL_FACTION_TURN_START"
    return [
        fake_pack,
        replace(begin, fields=begin_fields),
        *entities,
        replace(end, fields=end_fields),
    ]


def derive_plan_from_snapshot(snapshot: tuple[ProbeEvent, list[ProbeEvent], ProbeEvent]) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    scenario, metadata = build_shadow_scenario(_normalize_snapshot(snapshot))
    challenge = evaluate_campaign_snapshot(scenario)
    portfolio = build_strategic_theater_portfolio(scenario, challenge)
    allocation = build_theater_to_army_assignment(scenario, challenge, portfolio)
    assignments = allocation.get("assignments", [])
    if not assignments:
        return None, {
            "state": "WAITING_FOR_CURRENT_ASSIGNMENT",
            "turn": scenario["turn"],
            "scenario_id": scenario["scenario_id"],
            "strategic_posture": portfolio["strategic_posture"],
            "unfilled_count": len(allocation.get("unfilled_priorities", [])),
        }
    selected = sorted(
        assignments,
        key=lambda item: (
            SEVERITY_RANK.get(str(item.get("severity")), 99),
            str(item.get("priority_type")),
            str(item.get("actor_id")),
            str(item.get("assignment_id")),
        ),
    )[0]
    plan = build_campaign_strategic_feasibility_plan(scenario, selected)
    context = {
        "state": "PLAN_READY",
        "scenario": scenario,
        "snapshot_metadata": metadata,
        "challenge": challenge,
        "portfolio": portfolio,
        "allocation": allocation,
        "selected_assignment": selected,
        "plan": plan,
    }
    return plan, context


def derive_current_plan(events: list[ProbeEvent]) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    snapshots = _complete_snapshots(events)
    if not snapshots:
        return None, {"state": "WAITING_FOR_SNAPSHOT"}
    return derive_plan_from_snapshot(snapshots[-1])


def _packet_complete(events: list[ProbeEvent], plan_digest: str, query_count: int) -> bool:
    for event in events:
        if (
            event.event == "FEASIBILITY_PACKET_END"
            and event.fields.get("plan_digest") == plan_digest
            and event.fields.get("query_count") == str(query_count)
            and event.fields.get("orders_emitted") == "false"
            and event.fields.get("save_values_written") == "false"
        ):
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate one exact v0.2H live feasibility request from the current read-only campaign snapshot.")
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--request-file", type=Path, required=True)
    parser.add_argument("--session-root", type=Path, required=True)
    parser.add_argument("--status", type=Path, required=True)
    parser.add_argument("--stop-file", type=Path, required=True)
    parser.add_argument("--poll-seconds", type=float, default=0.5)
    args = parser.parse_args()

    args.session_root.mkdir(parents=True, exist_ok=True)
    requested_digest: str | None = None
    last_status: dict[str, Any] | None = None

    while True:
        if args.stop_file.exists():
            _atomic_json(args.status, {"schema_version": 1, "state": "STOPPED", "plan_digest": requested_digest})
            return 0
        if not args.log.exists():
            status = {"schema_version": 1, "state": "WAITING_FOR_LOG", "plan_digest": requested_digest}
        else:
            try:
                events = parse_logs([args.log])
                if requested_digest is not None:
                    plan = json.loads((args.session_root / "current_feasibility_plan.json").read_text(encoding="utf-8"))
                    if _packet_complete(events, requested_digest, int(plan["query_count"])):
                        status = {
                            "schema_version": 1,
                            "state": "CAPTURE_COMPLETE",
                            "plan_digest": requested_digest,
                            "turn": plan["turn"],
                            "scenario_id": plan["scenario_id"],
                            "query_count": plan["query_count"],
                        }
                        _atomic_json(args.status, status)
                        (args.session_root / "capture_complete.flag").write_text("complete\n", encoding="utf-8")
                        return 0
                    status = {"schema_version": 1, "state": "WAITING_FOR_QUERY_RESULTS", "plan_digest": requested_digest}
                else:
                    plan, context = derive_current_plan(events)
                    if plan is None:
                        status = {"schema_version": 1, **context, "plan_digest": None}
                    else:
                        for name in ("scenario", "challenge", "portfolio", "allocation", "selected_assignment", "plan"):
                            payload = context[name]
                            target = args.session_root / ("current_feasibility_plan.json" if name == "plan" else f"current_{name}.json")
                            _atomic_json(target, payload)
                        request = _request_text(plan)
                        temp = args.request_file.with_suffix(args.request_file.suffix + ".tmp")
                        temp.write_text(request, encoding="utf-8", newline="\n")
                        os.replace(temp, args.request_file)
                        requested_digest = str(plan["result_digest"])
                        status = {
                            "schema_version": 1,
                            "state": "REQUEST_WRITTEN",
                            "plan_digest": requested_digest,
                            "turn": plan["turn"],
                            "scenario_id": plan["scenario_id"],
                            "query_count": plan["query_count"],
                            "actor_id": plan["actor"]["actor_id"],
                        }
            except Exception as exc:
                status = {
                    "schema_version": 1,
                    "state": "WAITING_RETRY_AFTER_PARSE_OR_PIPELINE_ERROR",
                    "plan_digest": requested_digest,
                    "error_type": type(exc).__name__,
                    "error": str(exc)[:1000],
                }
        if status != last_status:
            _atomic_json(args.status, status)
            last_status = status
        time.sleep(max(0.1, args.poll_seconds))


if __name__ == "__main__":
    raise SystemExit(main())
