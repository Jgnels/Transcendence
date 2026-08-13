from __future__ import annotations

from typing import Any, Iterable
import hashlib
import json

from .canonical import digest

PACKET_CONTRACT = "TACTICAL_ACTION_AUTHORITY_EVIDENCE_PACKET_V1"
REPORT_CONTRACT = "TACTICAL_ACTION_AUTHORITY_BOUNDARY_REPORT_V1"

_ALLOWED_ORIGINS = {
    "GAME_COMMAND_EVENT_ORIGIN_UNRESOLVED",
    "OWNER_INPUT_DECLARED_BY_FIXTURE",
    "SCRIPT_INPUT_DECLARED_BY_FIXTURE",
    "NO_COMMAND_EVENT",
}
_ALLOWED_REACHABILITY = {
    "QUERY_TRUE",
    "QUERY_FALSE",
    "UNAVAILABLE",
    "NOT_APPLICABLE",
}
_ALLOWED_INTERRUPTIONS = {
    "NONE",
    "SUBSEQUENT_COMMAND",
    "CONTROL_LOST",
    "ROUTED",
    "SHATTERED",
    "TERMINAL",
    "WINDOW_TIMEOUT",
}


class ActionAuthorityError(ValueError):
    pass


def _verified_digest(record: dict[str, Any], label: str) -> None:
    claimed = record.get("result_digest")
    if not isinstance(claimed, str) or len(claimed) != 64:
        raise ActionAuthorityError(f"{label} result digest missing or invalid")
    payload = dict(record)
    payload.pop("result_digest", None)
    compact = digest(payload)
    newline = hashlib.sha256(
        (json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")
    ).hexdigest()
    if claimed not in {compact, newline}:
        raise ActionAuthorityError(f"{label} result digest mismatch")


def _strict_bool(value: Any, label: str) -> bool:
    if type(value) is not bool:
        raise ActionAuthorityError(f"{label} must be boolean")
    return value


def _string_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise ActionAuthorityError(f"{label} must be a string list")
    if len(value) != len(set(value)):
        raise ActionAuthorityError(f"{label} must be unique")
    return sorted(value)


def _position(value: Any, label: str) -> dict[str, float] | None:
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != {"x", "y", "z"}:
        raise ActionAuthorityError(f"{label} must be null or x/y/z object")
    result: dict[str, float] = {}
    for key in ("x", "y", "z"):
        item = value[key]
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise ActionAuthorityError(f"{label}.{key} must be numeric")
        numeric = float(item)
        if numeric != numeric or numeric in {float("inf"), float("-inf")}:
            raise ActionAuthorityError(f"{label}.{key} must be finite")
        result[key] = round(numeric, 6)
    return result


def build_action_authority_packet(observation: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(observation, dict):
        raise ActionAuthorityError("observation must be an object")
    command_event_observed = _strict_bool(
        observation.get("command_event_observed"), "command_event_observed"
    )
    project_issue_attempted = _strict_bool(
        observation.get("project_issue_attempted"), "project_issue_attempted"
    )
    direct_ack_observed = _strict_bool(
        observation.get("direct_ack_observed"), "direct_ack_observed"
    )
    if project_issue_attempted:
        raise ActionAuthorityError("v0.1R packet is read-only and forbids project issue attempts")
    if direct_ack_observed:
        raise ActionAuthorityError("v0.1R has no direct acknowledgement source")

    origin = observation.get("command_origin")
    if origin not in _ALLOWED_ORIGINS:
        raise ActionAuthorityError("unsupported command origin")
    if command_event_observed and origin == "NO_COMMAND_EVENT":
        raise ActionAuthorityError("observed command cannot use NO_COMMAND_EVENT origin")
    if not command_event_observed and origin != "NO_COMMAND_EVENT":
        raise ActionAuthorityError("missing command event must use NO_COMMAND_EVENT origin")

    selected = _string_list(observation.get("selected_unit_ids", []), "selected_unit_ids")
    actor = observation.get("actor_unit_id")
    if actor is not None and (not isinstance(actor, str) or not actor):
        raise ActionAuthorityError("actor_unit_id must be null or nonempty string")
    if actor is not None and selected and actor not in selected:
        raise ActionAuthorityError("actor must be included in selected units")

    command_name = observation.get("command_name")
    if command_event_observed:
        if not isinstance(command_name, str) or not command_name:
            raise ActionAuthorityError("observed command requires command_name")
    elif command_name is not None:
        raise ActionAuthorityError("missing command event cannot have command_name")

    reachability = observation.get("reachability")
    if reachability not in _ALLOWED_REACHABILITY:
        raise ActionAuthorityError("invalid reachability classification")
    target_position = _position(observation.get("target_position"), "target_position")
    target_unit_id = observation.get("target_unit_id")
    if target_unit_id is not None and (not isinstance(target_unit_id, str) or not target_unit_id):
        raise ActionAuthorityError("target_unit_id must be null or nonempty string")
    if target_unit_id and "hidden" in target_unit_id.lower():
        raise ActionAuthorityError("hidden target identity is prohibited")
    if reachability in {"QUERY_TRUE", "QUERY_FALSE"} and target_position is None:
        raise ActionAuthorityError("reachability query requires target position")

    ordered_position_match = _strict_bool(
        observation.get("ordered_position_match"), "ordered_position_match"
    )
    target_match = _strict_bool(observation.get("target_match"), "target_match")
    moving_after = _strict_bool(observation.get("moving_after"), "moving_after")
    leaving_after = _strict_bool(observation.get("leaving_after"), "leaving_after")
    control_lost = _strict_bool(observation.get("control_lost"), "control_lost")
    interruption = observation.get("interruption")
    if interruption not in _ALLOWED_INTERRUPTIONS:
        raise ActionAuthorityError("invalid interruption classification")

    state_matches: list[str] = []
    if ordered_position_match:
        state_matches.append("ORDERED_POSITION_MATCH")
    if target_match:
        state_matches.append("CURRENT_TARGET_MATCH")
    if moving_after:
        state_matches.append("MOVEMENT_OBSERVED")
    if leaving_after:
        state_matches.append("LEAVING_BATTLE_OBSERVED")

    if not command_event_observed:
        binding_status = "NO_COMMAND_EVENT"
        execution_status = "NO_ISSUE_ATTEMPT"
    elif actor is None or not selected:
        binding_status = "UNBOUND_COMMAND_EVENT"
        execution_status = "UNBOUND_COMMAND_NO_EXECUTION_CLAIM"
    else:
        binding_status = "BOUND_TO_OBSERVED_SELECTION"
        if interruption != "NONE" or control_lost:
            execution_status = "INTERRUPTED_OR_CONTROL_LOST"
        elif state_matches:
            execution_status = "OBSERVED_STATE_MATCH_NOT_CAUSALLY_ATTRIBUTED"
        else:
            execution_status = "NO_MATCHING_STATE_CHANGE_OBSERVED"

    if reachability == "QUERY_TRUE":
        feasibility_status = "POSITION_QUERY_REACHABLE"
    elif reachability == "QUERY_FALSE":
        feasibility_status = "POSITION_QUERY_UNREACHABLE"
    elif reachability == "NOT_APPLICABLE":
        feasibility_status = "REACHABILITY_NOT_APPLICABLE"
    else:
        feasibility_status = "REACHABILITY_UNVERIFIED"

    packet = {
        "schema_version": 1,
        "packet_contract": PACKET_CONTRACT,
        "authority": "NO_ORDERS",
        "project_issue_status": "NOT_ATTEMPTED",
        "command_event_status": (
            "OBSERVED_GAME_COMMAND_EVENT" if command_event_observed else "NOT_OBSERVED"
        ),
        "command_origin": origin,
        "binding_status": binding_status,
        "actor_unit_id": actor,
        "selected_unit_ids": selected,
        "command_name": command_name,
        "target_unit_id": target_unit_id,
        "target_position": target_position,
        "reachability_query": reachability,
        "feasibility_status": feasibility_status,
        "state_match_evidence": state_matches,
        "execution_status": execution_status,
        "interruption": interruption,
        "direct_acknowledgement_status": "UNAVAILABLE_NOT_OBSERVED",
        "acknowledgement_claim": "NOT_ACKNOWLEDGED",
        "outcome_attribution": "UNVERIFIED_NOT_ATTRIBUTED",
        "interpretation_limits": [
            "A command callback does not identify whether player or script originated the command.",
            "Ordered-position, target, movement, or withdrawal matches are state evidence, not direct acknowledgement.",
            "A reachability query is a point-in-time engine query, not proof of route completion.",
            "No project order was issued and no causal gameplay outcome is claimed.",
        ],
    }
    packet["result_digest"] = digest(packet)
    return packet


def build_action_authority_matrix(suite: dict[str, Any]) -> dict[str, Any]:
    if suite.get("schema_version") != 1:
        raise ActionAuthorityError("unsupported matrix schema")
    scenarios = suite.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        raise ActionAuthorityError("matrix scenarios must be a nonempty list")
    ids: set[str] = set()
    results: list[dict[str, Any]] = []
    for scenario in scenarios:
        scenario_id = scenario.get("scenario_id")
        if not isinstance(scenario_id, str) or not scenario_id or scenario_id in ids:
            raise ActionAuthorityError("scenario IDs must be unique nonempty strings")
        ids.add(scenario_id)
        expect_error = bool(scenario.get("expect_error", False))
        try:
            packet = build_action_authority_packet(scenario["observation"])
            error = None
        except (ActionAuthorityError, KeyError) as exc:
            packet = None
            error = str(exc)
        passed = (error is not None) if expect_error else (error is None)
        if passed and packet is not None:
            expected = scenario.get("expect", {})
            for key, value in expected.items():
                if packet.get(key) != value:
                    passed = False
                    error = f"expected {key}={value!r}, got {packet.get(key)!r}"
                    break
        results.append(
            {
                "scenario_id": scenario_id,
                "passed": passed,
                "expect_error": expect_error,
                "error": error,
                "packet": packet,
            }
        )
    report = {
        "schema_version": 1,
        "report_contract": "TACTICAL_ACTION_AUTHORITY_MATRIX_REPORT_V1",
        "seed": suite.get("seed"),
        "authority": "NO_ORDERS",
        "scenario_count": len(results),
        "passed_count": sum(1 for item in results if item["passed"]),
        "failed_count": sum(1 for item in results if not item["passed"]),
        "scenarios": results,
    }
    report["result_digest"] = digest(report)
    return report


def build_battle4_authority_boundary_report(
    dense_corpus: dict[str, Any], schedule: dict[str, Any]
) -> dict[str, Any]:
    _verified_digest(dense_corpus, "dense corpus")
    _verified_digest(schedule, "temporal schedule")
    battle = dense_corpus.get("battle", {})
    command_analysis = battle.get("command_analysis", {})
    inference = battle.get("inferred_command_attribution", {})
    records = inference.get("records", [])
    if not isinstance(records, list):
        raise ActionAuthorityError("dense corpus inferred records must be a list")
    confidence_counts: dict[str, int] = {}
    for record in records:
        confidence = record.get("confidence", "UNKNOWN")
        confidence_counts[confidence] = confidence_counts.get(confidence, 0) + 1

    report = {
        "schema_version": 1,
        "report_contract": REPORT_CONTRACT,
        "source_id": dense_corpus.get("corpus_id"),
        "source_dense_corpus_digest": dense_corpus["result_digest"],
        "source_temporal_schedule_digest": schedule["result_digest"],
        "authority": "NO_ORDERS",
        "evidence_status": "CONTROL_OFFLINE_DERIVED_FROM_OBSERVED_INPUT",
        "command_event_count": int(command_analysis.get("command_event_count", 0)),
        "direct_selection_attributed_command_count": int(
            command_analysis.get("selection_attributed_command_count", 0)
        ),
        "candidate_inferred_attribution_count": int(
            inference.get("inferred_command_count", 0)
        ),
        "inferred_attribution_status": inference.get("status"),
        "inferred_confidence_counts": dict(sorted(confidence_counts.items())),
        "project_issue_attempt_count": 0,
        "direct_acknowledgement_count": 0,
        "execution_claim_count": 0,
        "outcome_attribution_count": 0,
        "reachability_query_count": 0,
        "temporal_schedule_active_plan_max": int(
            schedule.get("summary", {}).get("maximum_active_plans_in_one_slice", 0)
        ),
        "limiting_results": [
            "Replay command callbacks observed game command events but did not identify player-versus-script origin.",
            "Zero commands had direct selection-callback attribution in the replay.",
            "Candidate state-matching attribution remains INFERRED_NOT_ACKNOWLEDGED.",
            "The existing replay corpus contains no can_reach_position query at command time.",
            "No unitcontroller was created and no project issue attempt occurred.",
        ],
        "required_future_live_evidence": [
            "ordinary live battle rather than replay-only selection behavior",
            "command-bound local actor identity",
            "point-in-time reachability query for positional commands",
            "ordered-position or current-target state after the command",
            "control-state loss, routing, shattering, halt, or subsequent-command interruption",
            "explicit preservation of direct acknowledgement as unavailable unless a real callback is found",
        ],
    }
    report["result_digest"] = digest(report)
    return report
