from __future__ import annotations

import statistics
from typing import Any

from .canonical import digest
from .campaign import run_campaign


def _percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    position = (len(ordered) - 1) * p
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def run_ensemble(
    scenario: dict[str, Any],
    profile: dict[str, Any],
    turns: int,
    seeds: list[int],
) -> dict[str, Any]:
    if not seeds:
        raise ValueError("seeds must not be empty")
    runs = [run_campaign(scenario, profile, turns, seed) for seed in seeds]
    metric_names = sorted(runs[0]["metrics"])
    distributions: dict[str, dict[str, float]] = {}
    for name in metric_names:
        values = [float(run["metrics"][name]) for run in runs]
        distributions[name] = {
            "mean": round(statistics.fmean(values), 6),
            "median": round(statistics.median(values), 6),
            "p10": round(_percentile(values, 0.10), 6),
            "p90": round(_percentile(values, 0.90), 6),
            "min": round(min(values), 6),
            "max": round(max(values), 6),
        }
    result = {
        "schema_version": 1,
        "tier": 3,
        "fidelity_label": "UNCALIBRATED_ENSEMBLE_OVER_TIER_2",
        "scenario_id": scenario["scenario_id"],
        "profile_id": profile.get("profile_id", "unnamed"),
        "turns": turns,
        "seeds": seeds,
        "distributions": distributions,
        "run_digests": [run["result_digest"] for run in runs],
        "warnings": ["Inherits every limitation of the Tier 2 surrogate."],
        "evidence_status": "HYPOTHESIS",
    }
    result["result_digest"] = digest(result)
    return result
