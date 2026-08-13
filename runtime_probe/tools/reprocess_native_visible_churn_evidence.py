from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "runtime_probe" / "tools"))
sys.path.insert(0, str(REPO_ROOT / "synthetic_lab"))

from run_native_visible_behavior import (
    observable_ai_factions_from_shadow_result,
    run_player_visible_native_behavior_from_shadow_result,
)
from transcendence_lab.canonical import digest
from transcendence_lab.native_churn import analyze_visible_directional_churn

CONTRACT = "PLAYER_VISIBLE_NATIVE_DIRECTIONAL_CHURN_REPROCESS_v0.2L"


def build_reprocess(source_path: Path) -> dict[str, Any]:
    source_bytes = source_path.read_bytes()
    report = json.loads(source_bytes.decode("utf-8-sig"))
    factions = observable_ai_factions_from_shadow_result(report, minimum_frames=4)
    if not factions:
        raise ValueError("source contains no foreign AI faction visible in at least four frames")

    analyses: list[dict[str, Any]] = []
    totals = {
        "eligible_stable_context_region_windows": 0,
        "oscillation_candidate_count": 0,
        "repeated_oscillation_cluster_count": 0,
    }
    for faction in factions:
        visible = run_player_visible_native_behavior_from_shadow_result(report, faction)
        analysis = analyze_visible_directional_churn(visible["trace"])
        metrics = analysis["metrics"]
        for key in totals:
            totals[key] += int(metrics[key])
        analyses.append(
            {
                "observed_ai_faction": faction,
                "analysis_result_digest": analysis["result_digest"],
                "status": analysis["status"],
                "metrics": metrics,
                "availability": analysis["availability"],
            }
        )

    artifact: dict[str, Any] = {
        "schema_version": 1,
        "contract": CONTRACT,
        "evidence_label": "SUPPORTED_DERIVED_OWNER_EVIDENCE_LIMITING_RESULT",
        "policy_authority": "NO_ORDERS",
        "application_authority": "PROHIBITED",
        "source": {
            "path": source_path.relative_to(REPO_ROOT).as_posix(),
            "sha256": hashlib.sha256(source_bytes).hexdigest(),
            "source_result_digest": report.get("result_digest"),
            "profile_id": report.get("profile_id"),
            "foreign_entity_source_required": "WH3_PLAYER_FILTERED_LISTS",
        },
        "scope": {
            "turns": [item["turn"] for item in report.get("turn_results", [])],
            "foreign_ai_factions_visible_in_all_four_preserved_frames": factions,
            "raw_owner_log_committed": False,
        },
        "aggregate_metrics": {
            **totals,
            "candidate_rate_per_eligible_window": (
                round(totals["oscillation_candidate_count"] / totals["eligible_stable_context_region_windows"], 6)
                if totals["eligible_stable_context_region_windows"]
                else None
            ),
        },
        "faction_analyses": analyses,
        "interpretation": {
            "supported": [
                "The preserved four-turn owner-safe cohort can be re-evaluated under the v0.2L preregistration without reconstructing a private raw log.",
            ],
            "not_supported": [
                "Zero eligible windows is not evidence that native CAI has good hysteresis; it is insufficient primary-endpoint exposure.",
                "A four-frame source cannot contain the two non-overlapping A->B->A episodes required for the repeated primary signal unless longer evidence exists elsewhere.",
                "No project-owned strategic planner or application authority is earned by this limiting result.",
            ],
        },
        "next_gate": "A future owner session must collect a longer visibility-safe cohort only after the run protocol is frozen; do not infer native hysteresis from this historical cohort.",
    }
    artifact["result_digest"] = digest(artifact)
    return artifact


def main() -> int:
    parser = argparse.ArgumentParser(description="Reprocess preserved owner-safe turns under the v0.2L directional-churn preregistration.")
    parser.add_argument(
        "--source",
        type=Path,
        default=REPO_ROOT / "research/runtime_evidence/CAMPAIGN_TURNS_4_7_REPROCESS_v0.1J.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "research/runtime_evidence/PLAYER_VISIBLE_NATIVE_DIRECTIONAL_CHURN_REPROCESS_v0.2L.json",
    )
    args = parser.parse_args()
    result = build_reprocess(args.source.resolve())
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
