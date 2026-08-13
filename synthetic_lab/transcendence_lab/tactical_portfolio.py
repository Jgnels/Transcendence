from __future__ import annotations

from collections import defaultdict
from typing import Any

from .battle_shadow import (
    MAX_SELECTED_OPPORTUNITIES_PER_SLICE,
    SEVERITY_RANK,
    collect_tactical_opportunity_candidates,
)
from .canonical import digest
from .tactical_state import build_tactical_state_trajectory


PORTFOLIO_CONTRACT = "TACTICAL_PRIORITY_PORTFOLIO_V1"


def _confidence_floor(items: list[dict[str, Any]]) -> dict[str, Any]:
    rank = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
    level = min(
        (item["confidence"]["level"] for item in items),
        key=lambda value: rank[value],
    )
    limitations = sorted(
        {
            limitation
            for item in items
            for limitation in item["confidence"]["limitations"]
        }
    )
    return {
        "level": level,
        "basis": "minimum confidence across grouped source opportunities",
        "limitations": limitations,
    }


def _group_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for candidate in candidates:
        scope = "UNIT_GROUP" if candidate["scope"] == "UNIT" else "BATTLE"
        grouped[(scope, candidate["opportunity_type"])].append(candidate)

    portfolio: list[dict[str, Any]] = []
    for (scope, opportunity_type), items in sorted(grouped.items()):
        items = sorted(
            items,
            key=lambda item: (
                -SEVERITY_RANK[item["severity"]],
                -item["utility_score"],
                item["opportunity_id"],
            ),
        )
        representative = items[0]
        highest_rank = max(SEVERITY_RANK[item["severity"]] for item in items)
        severity = next(
            name for name, value in SEVERITY_RANK.items() if value == highest_rank
        )
        subjects = sorted(
            {
                unit_id
                for item in items
                for unit_id in item["subject_unit_ids"]
            }
        )
        source_critical = [item for item in items if item["severity"] == "CRITICAL"]
        record: dict[str, Any] = {
            "portfolio_id": f"{scope}:{opportunity_type}",
            "opportunity_type": opportunity_type,
            "scope": scope,
            "subject_unit_ids": subjects,
            "severity": severity,
            "utility_score": max(item["utility_score"] for item in items),
            "mean_utility_score": round(
                sum(item["utility_score"] for item in items) / len(items), 6
            ),
            "grouped_source_count": len(items),
            "critical_source_count": len(source_critical),
            "source_opportunity_ids": [item["opportunity_id"] for item in items],
            "source_opportunity_keys": [item["opportunity_key"] for item in items],
            "tactical_diagnosis": representative["tactical_diagnosis"],
            "proposed_alternatives": representative["proposed_alternatives"],
            "confidence": _confidence_floor(items),
            "counterfactual_status": "UNVERIFIED",
            "authority": "ADVISORY_ONLY",
        }
        record["result_digest"] = digest(record)
        portfolio.append(record)
    return sorted(
        portfolio,
        key=lambda item: (
            -SEVERITY_RANK[item["severity"]],
            -item["utility_score"],
            item["portfolio_id"],
        ),
    )


def _overflow_record(items: list[dict[str, Any]]) -> dict[str, Any]:
    subjects = sorted(
        {unit_id for item in items for unit_id in item["subject_unit_ids"]}
    )
    record: dict[str, Any] = {
        "portfolio_id": "PORTFOLIO:CRITICAL_OVERFLOW",
        "opportunity_type": "CRITICAL_PORTFOLIO_OVERFLOW",
        "scope": "PORTFOLIO",
        "subject_unit_ids": subjects,
        "severity": "CRITICAL",
        "utility_score": max(item["utility_score"] for item in items),
        "mean_utility_score": round(
            sum(item["utility_score"] for item in items) / len(items), 6
        ),
        "grouped_source_count": sum(item["grouped_source_count"] for item in items),
        "critical_source_count": sum(item["critical_source_count"] for item in items),
        "source_opportunity_ids": sorted(
            source_id for item in items for source_id in item["source_opportunity_ids"]
        ),
        "source_opportunity_keys": sorted(
            source_key for item in items for source_key in item["source_opportunity_keys"]
        ),
        "tactical_diagnosis": (
            "More distinct critical advisory groups exist than the bounded portfolio can "
            "represent individually; the remaining groups are preserved as an explicit "
            "overflow rather than silently suppressed."
        ),
        "proposed_alternatives": [
            {
                "alternative_id": "REVIEW_CRITICAL_OVERFLOW_GROUPS",
                "description": "Resolve the preserved critical groups through a later assignment layer.",
                "tradeoff": "This retains awareness but does not establish a feasible command sequence.",
                "status": "PROPOSED_NOT_EXECUTED",
            }
        ],
        "confidence": _confidence_floor(items),
        "counterfactual_status": "UNVERIFIED",
        "authority": "ADVISORY_ONLY",
    }
    record["result_digest"] = digest(record)
    return record


def build_tactical_priority_portfolio(state: dict[str, Any]) -> dict[str, Any]:
    candidates = collect_tactical_opportunity_candidates(state)
    groups = _group_candidates(candidates)
    critical_groups = [item for item in groups if item["severity"] == "CRITICAL"]
    noncritical_groups = [item for item in groups if item["severity"] != "CRITICAL"]

    if len(critical_groups) <= MAX_SELECTED_OPPORTUNITIES_PER_SLICE:
        selected = critical_groups + noncritical_groups[
            : MAX_SELECTED_OPPORTUNITIES_PER_SLICE - len(critical_groups)
        ]
        overflow = None
    else:
        direct = critical_groups[: MAX_SELECTED_OPPORTUNITIES_PER_SLICE - 1]
        overflow = _overflow_record(
            critical_groups[MAX_SELECTED_OPPORTUNITIES_PER_SLICE - 1 :]
        )
        selected = direct + [overflow]

    covered_source_ids = {
        source_id
        for item in selected
        for source_id in item["source_opportunity_ids"]
    }
    critical_source_ids = {
        item["opportunity_id"]
        for item in candidates
        if item["severity"] == "CRITICAL"
    }
    selected_source_ids = {
        item["opportunity_id"]
        for item in candidates
        if item["opportunity_id"] in covered_source_ids
    }
    result: dict[str, Any] = {
        "schema_version": 1,
        "portfolio_contract": PORTFOLIO_CONTRACT,
        "slice_id": state["slice_id"],
        "time_ms": state["time_ms"],
        "source_tactical_state_digest": state["result_digest"],
        "candidate_opportunity_count": len(candidates),
        "grouped_priority_count": len(groups),
        "selected_priority_count": len(selected),
        "maximum_selected_priorities": MAX_SELECTED_OPPORTUNITIES_PER_SLICE,
        "critical_source_opportunity_count": len(critical_source_ids),
        "critical_source_coverage": round(
            len(critical_source_ids & covered_source_ids) / len(critical_source_ids)
            if critical_source_ids
            else 1.0,
            6,
        ),
        "all_source_coverage": round(
            len(selected_source_ids) / len(candidates) if candidates else 1.0, 6
        ),
        "critical_overflow_used": overflow is not None,
        "selected_priorities": selected,
        "suppressed_noncritical_group_count": max(
            0,
            len(noncritical_groups)
            - max(0, MAX_SELECTED_OPPORTUNITIES_PER_SLICE - len(critical_groups)),
        ),
        "constraints": [
            "No game command is emitted.",
            "Equivalent unit-level concerns are batched by opportunity type.",
            "Critical source opportunities are never silently discarded.",
            "An overflow record preserves critical awareness when group capacity is exceeded.",
            "Portfolio membership does not establish assignment, sequence, pathfinding, acknowledgement, or outcome.",
        ],
        "evidence_status": "CONTROL_OFFLINE",
        "authority": "NO_ORDERS",
    }
    result["result_digest"] = digest(result)
    return result


def build_trace_priority_portfolios(trace_corpus: dict[str, Any]) -> dict[str, Any]:
    trajectory = build_tactical_state_trajectory(trace_corpus)
    portfolios = [build_tactical_priority_portfolio(state) for state in trajectory["states"]]
    result: dict[str, Any] = {
        "schema_version": 1,
        "portfolio_contract": "TACTICAL_PRIORITY_PORTFOLIO_TRAJECTORY_V1",
        "source_trace_digest": trajectory["source_trace_digest"],
        "source_tactical_state_trajectory_digest": trajectory["result_digest"],
        "portfolio_count": len(portfolios),
        "portfolios": portfolios,
        "summary": {
            "candidate_opportunity_count": sum(
                item["candidate_opportunity_count"] for item in portfolios
            ),
            "grouped_priority_count": sum(
                item["grouped_priority_count"] for item in portfolios
            ),
            "selected_priority_count": sum(
                item["selected_priority_count"] for item in portfolios
            ),
            "maximum_selected_in_one_slice": max(
                (item["selected_priority_count"] for item in portfolios), default=0
            ),
            "minimum_critical_source_coverage": min(
                (item["critical_source_coverage"] for item in portfolios), default=1.0
            ),
            "critical_overflow_slice_count": sum(
                item["critical_overflow_used"] for item in portfolios
            ),
        },
        "evidence_status": "CONTROL_OFFLINE_OVER_OBSERVED_INPUT",
        "authority": "NO_ORDERS",
        "interpretation": (
            "Portfolio batching preserves advisory awareness and workload bounds; "
            "it does not establish assignment feasibility, command acceptance, or tactical quality."
        ),
    }
    result["result_digest"] = digest(result)
    return result
