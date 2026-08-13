from __future__ import annotations

from copy import deepcopy
from typing import Any

from .campaign_challenge import (
    APPLICATION_AUTHORITY,
    AUTHORITY,
    build_campaign_challenge_envelope,
    evaluate_campaign_snapshot,
)
from .canonical import digest
from .contracts import validate_campaign_scenario

CONTRACT = "CAMPAIGN_STRATEGIC_THEATER_PRIORITY_PORTFOLIO_V1"
CROSS_EVIDENCE_CONTRACT = "CAMPAIGN_STRATEGIC_THEATER_CROSS_EVIDENCE_PORTFOLIO_V1"
MAX_SELECTED_PRIORITIES = 6
MAX_AGGRESSIVE_PRIORITIES = 1

SEVERITY_RANK = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
AGGRESSIVE_TYPES = {
    "CONTAIN_COHERENT_VISIBLE_RIVAL",
    "TRACK_SINGLE_VISIBLE_RIVAL",
    "MANAGE_FRAGMENTED_VISIBLE_PRESSURE",
}


class StrategicPortfolioError(ValueError):
    pass


def _priority(
    priority_type: str,
    severity: str,
    scope: str,
    target_kind: str | None,
    target_id: str | None,
    utility: float,
    rationale: list[str],
    evidence: dict[str, Any],
) -> dict[str, Any]:
    if severity not in SEVERITY_RANK:
        raise StrategicPortfolioError(f"unsupported severity: {severity}")
    record = {
        "priority_type": priority_type,
        "severity": severity,
        "scope": scope,
        "target_kind": target_kind,
        "target_id": target_id,
        "utility": round(float(utility), 6),
        "rationale": list(rationale),
        "evidence": deepcopy(evidence),
        "authority": AUTHORITY,
        "application_authority": APPLICATION_AUTHORITY,
    }
    identity = {
        "priority_type": record["priority_type"],
        "scope": record["scope"],
        "target_kind": record["target_kind"],
        "target_id": record["target_id"],
    }
    record["portfolio_id"] = digest(identity)
    record["result_digest"] = digest(record)
    return record


def _verify_challenge(scenario: dict[str, Any], challenge: dict[str, Any]) -> dict[str, Any]:
    expected = evaluate_campaign_snapshot(scenario)
    if challenge != expected:
        raise StrategicPortfolioError("challenge envelope is stale, forged, or foreign to scenario")
    if challenge.get("authority") != AUTHORITY or challenge.get("application_authority") != APPLICATION_AUTHORITY:
        raise StrategicPortfolioError("challenge envelope crosses authority boundary")
    return expected


def _posture(challenge: dict[str, Any]) -> str:
    metrics = challenge["metrics"]
    if challenge["pressure_class"] == "LOCAL_CRISIS_OR_EXPOSED_FRONT":
        return "CRISIS_STABILIZATION"
    if metrics["controlled_recovery_army_count"] > 0 and metrics["threatened_front_count"] > 0:
        return "RECOVERY_AND_DEFENSE"
    if challenge["rival_structure"] == "COHERENT_VISIBLE_RIVAL_CANDIDATE":
        return "COHERENT_RIVAL_CONTAINMENT"
    if challenge["rival_structure"] == "FRAGMENTED_VISIBLE_PRESSURE":
        return "FRAGMENTED_PRESSURE_MANAGEMENT"
    if challenge["rival_structure"] == "SINGLE_OR_PARTIAL_VISIBLE_RIVAL":
        return "VISIBLE_RIVAL_WATCH"
    if metrics["controlled_recovery_army_count"] > 0:
        return "RECOVERY_AND_CONSOLIDATION"
    return "CONSOLIDATE_AND_RESERVE"


def _candidate_priorities(challenge: dict[str, Any]) -> list[dict[str, Any]]:
    metrics = challenge["metrics"]
    candidates: list[dict[str, Any]] = []

    for front in challenge["fronts"]:
        if front["under_siege"] and not front["covered_by_visible_controlled_force"]:
            candidates.append(
                _priority(
                    "RELIEVE_SIEGED_EXPOSED_FRONT", "CRITICAL", "FRONT", "REGION", front["region_id"],
                    900.0 + front["region_value"],
                    ["observed controlled region is under siege", "no visible controlled field-force coverage is within the benchmark horizon"],
                    {"front_state": front["front_state"], "region_value": front["region_value"]},
                )
            )
        elif front["under_siege"]:
            candidates.append(
                _priority(
                    "MAINTAIN_SIEGE_RELIEF_COVERAGE", "CRITICAL", "FRONT", "REGION", front["region_id"],
                    850.0 + front["region_value"],
                    ["observed controlled region is under siege", "visible controlled coverage exists and should not be silently abandoned"],
                    {"front_state": front["front_state"], "region_value": front["region_value"]},
                )
            )
        elif front["threatened"] and not front["covered_by_visible_controlled_force"]:
            candidates.append(
                _priority(
                    "STABILIZE_EXPOSED_FRONT", "CRITICAL", "FRONT", "REGION", front["region_id"],
                    800.0 + front["region_value"],
                    ["visible hostile pressure reaches the benchmark front horizon", "no visible controlled field-force coverage is present"],
                    {"front_state": front["front_state"], "region_value": front["region_value"]},
                )
            )
        elif front["threatened"]:
            candidates.append(
                _priority(
                    "MAINTAIN_THREATENED_FRONT_COVERAGE", "HIGH", "FRONT", "REGION", front["region_id"],
                    500.0 + front["region_value"],
                    ["visible hostile pressure reaches the benchmark front horizon", "visible controlled coverage already exists"],
                    {"front_state": front["front_state"], "region_value": front["region_value"]},
                )
            )

    recovery_count = int(metrics["controlled_recovery_army_count"])
    army_count = int(metrics["controlled_army_count"])
    if recovery_count > 0:
        all_recovering = army_count > 0 and recovery_count == army_count
        candidates.append(
            _priority(
                "PROTECT_RECOVERING_FIELD_FORCE",
                "CRITICAL" if all_recovering else "HIGH",
                "RECOVERY",
                None,
                None,
                700.0 if all_recovering else 460.0 + 100.0 * float(metrics["controlled_recovery_strength_fraction"] or 0.0),
                ["one or more controlled field armies are below the frozen recovery threshold", "recovery is protected as strategic capacity rather than treated as free offensive strength"],
                {
                    "recovering_army_count": recovery_count,
                    "recovery_strength_fraction": metrics["controlled_recovery_strength_fraction"],
                    "all_controlled_armies_recovering": all_recovering,
                },
            )
        )

    coherent = [item for item in challenge["rivals"] if item["coherent_visible_rival_candidate"]]
    for rival in coherent:
        candidates.append(
            _priority(
                "CONTAIN_COHERENT_VISIBLE_RIVAL", "HIGH", "RIVAL", "FACTION", rival["faction"],
                420.0 + 100.0 * float(rival["visible_army_strength_share"]) + 10.0 * float(rival["observed_region_value"]),
                ["same visible hostile faction has multiple armies, observed territory, and benchmark share support", "containment is a theater priority, not an order or proof of hostile coordination"],
                {
                    "visible_army_count": rival["visible_army_count"],
                    "visible_army_strength_share": rival["visible_army_strength_share"],
                    "observed_region_count": rival["observed_region_count"],
                },
            )
        )

    if challenge["rival_structure"] == "FRAGMENTED_VISIBLE_PRESSURE":
        candidates.append(
            _priority(
                "MANAGE_FRAGMENTED_VISIBLE_PRESSURE", "MEDIUM", "RIVAL_SET", None, None,
                300.0 + 100.0 * (1.0 - float(metrics["dominant_visible_hostile_army_share"])),
                ["visible pressure is split across multiple hostile factions", "do not turn war count into multiple independent aggression commitments"],
                {"concentration_hhi": metrics["visible_hostile_army_concentration_hhi"], "dominant_share": metrics["dominant_visible_hostile_army_share"]},
            )
        )
    elif challenge["rival_structure"] == "SINGLE_OR_PARTIAL_VISIBLE_RIVAL":
        candidates.append(
            _priority(
                "TRACK_SINGLE_VISIBLE_RIVAL", "MEDIUM", "RIVAL_SET", None, None,
                280.0,
                ["visible hostile assets exist but do not satisfy the coherent-rival benchmark", "retain pressure awareness without inventing a durable-rival claim"],
                {"visible_hostile_army_count": metrics["visible_hostile_army_count"], "observed_hostile_region_count": metrics["observed_hostile_region_count"]},
            )
        )

    if army_count >= 2:
        candidates.append(
            _priority(
                "PRESERVE_STRATEGIC_RESERVE", "MEDIUM", "RESERVE", None, None,
                260.0 + min(40.0, 5.0 * army_count),
                ["multiple controlled field armies exist", "reserve preservation limits total commitment and reduces strategic brittleness"],
                {"controlled_army_count": army_count},
            )
        )

    if challenge["rival_structure"] == "NO_VISIBLE_HOSTILE_ASSETS" and not any(
        item["severity"] == "CRITICAL" for item in candidates
    ):
        candidates.append(
            _priority(
                "CONSOLIDATE_LOW_PRESSURE_POSITION", "LOW", "THEATER", None, None,
                100.0,
                ["no observer-safe hostile army or hostile region asset is present", "low pressure does not justify manufacturing an offensive target"],
                {"pressure_class": challenge["pressure_class"]},
            )
        )

    return candidates


def _sort_key(item: dict[str, Any]) -> tuple[int, int, str, str]:
    return (
        -SEVERITY_RANK[item["severity"]],
        -int(round(float(item["utility"]) * 1_000_000)),
        str(item["priority_type"]),
        str(item["target_id"] or ""),
    )


def _select_priorities(candidates: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    ordered = sorted(candidates, key=_sort_key)
    critical = [item for item in ordered if item["severity"] == "CRITICAL"]
    if len(ordered) <= MAX_SELECTED_PRIORITIES:
        return ordered, None
    if len(critical) > MAX_SELECTED_PRIORITIES:
        direct = critical[: MAX_SELECTED_PRIORITIES - 1]
        overflow_sources = critical[MAX_SELECTED_PRIORITIES - 1 :]
        overflow = _priority(
            "CRITICAL_STRATEGIC_OVERFLOW", "CRITICAL", "OVERFLOW", None, None,
            min(item["utility"] for item in overflow_sources),
            ["critical strategic obligations exceed the bounded portfolio record budget", "overflow preserves every omitted critical source without pretending they are assigned or sequenced"],
            {
                "source_portfolio_ids": [item["portfolio_id"] for item in overflow_sources],
                "source_priority_types": [item["priority_type"] for item in overflow_sources],
                "source_count": len(overflow_sources),
            },
        )
        return direct + [overflow], overflow
    selected = critical + [item for item in ordered if item["severity"] != "CRITICAL"][: MAX_SELECTED_PRIORITIES - len(critical)]
    return selected, None


def build_strategic_theater_portfolio(
    raw_scenario: dict[str, Any], challenge_envelope: dict[str, Any] | None = None
) -> dict[str, Any]:
    scenario = validate_campaign_scenario(raw_scenario)
    challenge = (
        _verify_challenge(scenario, challenge_envelope)
        if challenge_envelope is not None
        else evaluate_campaign_snapshot(scenario)
    )
    candidates = _candidate_priorities(challenge)
    selected, overflow = _select_priorities(candidates)

    critical_ids = {item["portfolio_id"] for item in candidates if item["severity"] == "CRITICAL"}
    covered_critical_ids = {item["portfolio_id"] for item in selected if item["severity"] == "CRITICAL" and item["priority_type"] != "CRITICAL_STRATEGIC_OVERFLOW"}
    if overflow:
        covered_critical_ids.update(overflow["evidence"]["source_portfolio_ids"])
    critical_coverage = 1.0 if not critical_ids else round(len(covered_critical_ids & critical_ids) / len(critical_ids), 6)

    crisis = challenge["pressure_class"] == "LOCAL_CRISIS_OR_EXPOSED_FRONT"
    all_recovering = (
        challenge["metrics"]["controlled_army_count"] > 0
        and challenge["metrics"]["controlled_recovery_army_count"] == challenge["metrics"]["controlled_army_count"]
    )
    aggressive_allowed = not crisis and not all_recovering
    selected_aggressive = [item for item in selected if item["priority_type"] in AGGRESSIVE_TYPES]
    if not aggressive_allowed:
        selected_aggressive = []

    result = {
        "schema_version": 1,
        "contract": CONTRACT,
        "scenario_id": scenario["scenario_id"],
        "turn": scenario["turn"],
        "controlled_faction": scenario["controlled_faction"],
        "scenario_digest": digest(scenario),
        "challenge_result_digest": challenge["result_digest"],
        "authority": AUTHORITY,
        "application_authority": APPLICATION_AUTHORITY,
        "evidence_status": "CONTROL_OFFLINE_OVER_OBSERVER_SAFE_STRATEGIC_BENCHMARK",
        "strategic_posture": _posture(challenge),
        "portfolio_constraints": {
            "maximum_selected_priorities": MAX_SELECTED_PRIORITIES,
            "maximum_aggressive_priorities": MAX_AGGRESSIVE_PRIORITIES,
            "aggressive_commitment_allowed": aggressive_allowed,
            "all_controlled_armies_recovering": all_recovering,
            "force_assignment_status": "NOT_PERFORMED",
            "route_or_action_status": "NOT_EVALUATED",
            "coordination_claim_from_colocation": "PROHIBITED",
            "human_or_player_identity_consumed": False,
            "war_count_rewarded": False,
        },
        "candidate_priorities": candidates,
        "selected_priorities": selected,
        "selected_aggressive_priorities": selected_aggressive[:MAX_AGGRESSIVE_PRIORITIES],
        "critical_overflow": overflow,
        "metrics": {
            "candidate_priority_count": len(candidates),
            "selected_priority_count": len(selected),
            "critical_source_count": len(critical_ids),
            "critical_source_coverage": critical_coverage,
            "selected_critical_count": sum(1 for item in selected if item["severity"] == "CRITICAL"),
            "selected_high_count": sum(1 for item in selected if item["severity"] == "HIGH"),
            "selected_aggressive_priority_count": len(selected_aggressive[:MAX_AGGRESSIVE_PRIORITIES]),
            "unselected_noncritical_count": sum(
                1
                for item in candidates
                if item["severity"] != "CRITICAL"
                and item["portfolio_id"] not in {selected_item["portfolio_id"] for selected_item in selected}
            ),
        },
        "guardrails": [
            "Front crises and total-force recovery can veto new aggressive commitment.",
            "War count does not create one priority per enemy faction.",
            "Visible faction identity may name a rival target but human/player identity has no scoring privilege.",
            "A coherent visible rival candidate is not proof of coordination, diplomacy, economy, or durable power.",
            "Portfolio records are priorities only; army assignment, route feasibility, command construction, acknowledgement, execution, and outcome remain separate gates.",
        ],
    }
    result["result_digest"] = digest(result)
    return result


def build_cross_evidence_strategic_theater_portfolio(
    observed_report: dict[str, Any],
    late_game_scenario: dict[str, Any],
    challenge_envelope: dict[str, Any],
) -> dict[str, Any]:
    expected_challenge = build_campaign_challenge_envelope(observed_report, late_game_scenario)
    if challenge_envelope != expected_challenge:
        raise StrategicPortfolioError("v0.2E challenge envelope does not match exact supplied sources")
    observed_portfolios = []
    for turn_item, challenge_turn in zip(observed_report["turn_results"], challenge_envelope["observed_turns"], strict=True):
        observed_portfolios.append(build_strategic_theater_portfolio(turn_item["scenario"], challenge_turn))
    late_game = build_strategic_theater_portfolio(
        late_game_scenario, challenge_envelope["synthetic_late_game_reference"]
    )
    result = {
        "schema_version": 1,
        "contract": CROSS_EVIDENCE_CONTRACT,
        "authority": AUTHORITY,
        "application_authority": APPLICATION_AUTHORITY,
        "evidence_status": "CONTROL_OFFLINE_OVER_V0_2E_BENCHMARK",
        "source_challenge_result_digest": challenge_envelope["result_digest"],
        "observed_source_report_digest": observed_report.get("result_digest"),
        "observed_turns": observed_portfolios,
        "synthetic_late_game_reference": late_game,
        "portfolio_design_limits": [
            "The six-record priority budget and one-aggressive-priority cap are project-owned engineering constraints, not empirical WH3 optima.",
            "The portfolio does not assign armies, prove routes, issue commands, or predict outcomes.",
            "Observed calibration remains early Reikland turns 4-7; the late-game case remains synthetic.",
            "Economy, recruitment, diplomacy, replenishment history, native CAI intent, and SFO strategic behavior remain outside this gate.",
        ],
    }
    result["result_digest"] = digest(result)
    return result


def semantic_portfolio_metrics(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "strategic_posture": result["strategic_posture"],
        "selected_priority_types": sorted(item["priority_type"] for item in result["selected_priorities"]),
        "selected_severities": sorted(item["severity"] for item in result["selected_priorities"]),
        "selected_aggressive_types": sorted(item["priority_type"] for item in result["selected_aggressive_priorities"]),
        "critical_source_count": result["metrics"]["critical_source_count"],
        "critical_source_coverage": result["metrics"]["critical_source_coverage"],
        "candidate_priority_count": result["metrics"]["candidate_priority_count"],
        "selected_priority_count": result["metrics"]["selected_priority_count"],
        "aggressive_commitment_allowed": result["portfolio_constraints"]["aggressive_commitment_allowed"],
        "all_controlled_armies_recovering": result["portfolio_constraints"]["all_controlled_armies_recovering"],
        "critical_overflow_source_count": 0 if result["critical_overflow"] is None else result["critical_overflow"]["evidence"]["source_count"],
    }
