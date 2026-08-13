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
from run_native_visible_behavior import (
    NativeVisiblePipelineError,
    _extract_snapshots,
    build_player_visible_native_trace,
)
from transcendence_lab.canonical import digest
from transcendence_lab.native_churn import analyze_visible_directional_churn
from transcendence_lab.native_visible_behavior import APPLICATION_AUTHORITY, AUTHORITY, VISIBILITY_SOURCE

CONTRACT = "NATIVE_CAI_VISIBLE_DIRECTIONAL_CHURN_RUNTIME_BATCH_V1"


class NativeVisibleChurnPipelineError(ValueError):
    pass


def discover_observed_ai_factions(events: list[ProbeEvent], *, minimum_frames: int = 4) -> list[str]:
    if minimum_frames < 2:
        raise NativeVisibleChurnPipelineError("minimum_frames must be at least 2")
    snapshots = _extract_snapshots(events)
    observer: str | None = None
    frame_counts: dict[str, int] = {}
    for begin, entity_events, _end in snapshots:
        local_faction = begin.fields.get("local_faction")
        if not local_faction or local_faction == "unknown":
            raise NativeVisibleChurnPipelineError("snapshot local faction is unavailable")
        if observer is None:
            observer = local_faction
        elif observer != local_faction:
            raise NativeVisibleChurnPipelineError("trace spans multiple observer factions")
        present = {
            event.fields.get("faction")
            for event in entity_events
            if event.event == "SHADOW_VISIBLE_ARMY"
            and event.fields.get("faction")
            and event.fields.get("faction") != local_faction
        }
        for faction in present:
            frame_counts[str(faction)] = frame_counts.get(str(faction), 0) + 1
    return sorted(faction for faction, count in frame_counts.items() if count >= minimum_frames)


def run_native_visible_churn_batch(
    log_paths: list[Path], *, profile: str, minimum_frames: int = 4
) -> dict[str, Any]:
    if profile not in {"VANILLA", "SFO"}:
        raise NativeVisibleChurnPipelineError("profile must be VANILLA or SFO")
    events = parse_logs(log_paths)
    factions = discover_observed_ai_factions(events, minimum_frames=minimum_frames)
    analyses: list[dict[str, Any]] = []
    for faction in factions:
        try:
            trace = build_player_visible_native_trace(events, faction)
        except NativeVisiblePipelineError as exc:
            raise NativeVisibleChurnPipelineError(str(exc)) from exc
        analyses.append(
            {
                "observed_ai_faction": faction,
                "analysis": analyze_visible_directional_churn(trace),
            }
        )

    eligible = sum(
        row["analysis"]["metrics"]["eligible_stable_context_region_windows"] for row in analyses
    )
    candidates = sum(row["analysis"]["metrics"]["oscillation_candidate_count"] for row in analyses)
    clusters = sum(row["analysis"]["metrics"]["repeated_oscillation_cluster_count"] for row in analyses)
    result: dict[str, Any] = {
        "contract": CONTRACT,
        "authority": AUTHORITY,
        "application_authority": APPLICATION_AUTHORITY,
        "foreign_visibility_source": VISIBILITY_SOURCE,
        "profile": profile,
        "minimum_frames_for_faction_inclusion": minimum_frames,
        "observed_ai_faction_count": len(analyses),
        "factions": analyses,
        "aggregate_metrics": {
            "eligible_stable_context_region_windows": eligible,
            "oscillation_candidate_count": candidates,
            "repeated_oscillation_cluster_count": clusters,
            "candidate_rate_per_eligible_window": round(candidates / eligible, 6) if eligible else None,
        },
        "interpretation": "BATCH_SUMMARY_OF_PLAYER_VISIBLE_PARTIAL_TRACES_NOT_FULL_FACTION_STATE",
    }
    result["result_digest"] = digest(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the preregistered player-visible native directional-churn evaluator across all sufficiently observed AI factions."
    )
    parser.add_argument("logs", type=Path, nargs="+")
    parser.add_argument("--profile", choices=("VANILLA", "SFO"), required=True)
    parser.add_argument("--minimum-frames", type=int, default=4)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_native_visible_churn_batch(
        args.logs,
        profile=args.profile,
        minimum_frames=args.minimum_frames,
    )
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
