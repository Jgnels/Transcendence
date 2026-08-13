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


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def build_reprocess(source_path: Path) -> dict[str, Any]:
    source_bytes = source_path.read_bytes()
    report = json.loads(source_bytes.decode("utf-8-sig"))
    factions = observable_ai_factions_from_shadow_result(report, minimum_frames=2)
    if not factions:
        raise ValueError("source contains no foreign AI faction visible in at least two frames")

    analyses: list[dict[str, Any]] = []
    totals = {
        "comparable_actor_intervals": 0,
        "movement_intervals": 0,
        "position_idle_intervals": 0,
        "directional_anchor_proxy_intervals": 0,
        "ambiguous_anchor_intervals": 0,
        "unanchored_movement_intervals": 0,
        "visible_anchor_direction_change_candidate_count": 0,
        "visibility_gain_count": 0,
        "visibility_loss_count": 0,
    }
    for faction in factions:
        result = run_player_visible_native_behavior_from_shadow_result(report, faction)
        analysis = result["analysis"]
        metrics = analysis["metrics"]
        for key in totals:
            totals[key] += int(metrics[key])
        analyses.append(
            {
                "observed_ai_faction": faction,
                "analysis_result_digest": analysis["result_digest"],
                "metrics": metrics,
                "availability": analysis["availability"],
            }
        )

    comparable = totals["comparable_actor_intervals"]
    aggregate = {
        **totals,
        "position_idle_interval_rate": round(totals["position_idle_intervals"] / comparable, 6) if comparable else None,
        "foreign_faction_count": len(factions),
        "first_turn": min(item["metrics"]["first_turn"] for item in analyses),
        "last_turn": max(item["metrics"]["last_turn"] for item in analyses),
    }
    artifact: dict[str, Any] = {
        "schema_version": 1,
        "contract": "PLAYER_VISIBLE_NATIVE_BEHAVIOR_REPROCESS_v0.2K",
        "evidence_label": "SUPPORTED_DERIVED_OWNER_EVIDENCE",
        "policy_authority": "NO_ORDERS",
        "application_authority": "PROHIBITED",
        "source": {
            "path": source_path.relative_to(REPO_ROOT).as_posix(),
            "sha256": hashlib.sha256(source_bytes).hexdigest(),
            "source_result_digest": report.get("result_digest"),
            "source_evidence_status": report.get("evidence_status"),
            "profile_id": report.get("profile_id"),
            "foreign_entity_source_required": "WH3_PLAYER_FILTERED_LISTS",
        },
        "scope": {
            "observer": report["turn_results"][0]["scenario"]["controlled_faction"],
            "turns": [item["turn"] for item in report["turn_results"]],
            "foreign_ai_factions_visible_in_at_least_two_frames": factions,
            "raw_owner_log_committed": False,
            "reprocess_uses_public_safe_derived_scenarios_only": True,
        },
        "aggregate_metrics": aggregate,
        "faction_analyses": analyses,
        "interpretation": {
            "supported": [
                "Player-visible foreign force positions can be compared longitudinally across the preserved owner turns.",
                "Foreign force visibility gains and losses can be counted as observation-set transitions.",
                "Position stability and movement toward player-visible anchors can be measured as proxies.",
            ],
            "not_supported": [
                "Position-stable intervals are not proof that native CAI is idle, stuck, passive, or low quality.",
                "Visibility loss is not proof of army destruction, retreat, disbandment, or reassignment.",
                "The preserved player-visible subset cannot establish full-faction front coverage, response latency, reserve adequacy, recovery misuse, assignment exclusivity, native task identity, memory, or hysteresis.",
                "The absence of directional-anchor changes is not proof of low task churn because almost all comparable intervals are position-stable and native tasks are hidden.",
            ],
        },
        "next_gate": "Acquire or identify richer visibility-safe longitudinal evidence only when it can answer a preregistered native-failure question; do not revive v0.2G/v0.2I from this limiting result.",
    }
    artifact["result_digest"] = hashlib.sha256(_canonical(artifact)).hexdigest()
    return artifact


def main() -> int:
    parser = argparse.ArgumentParser(description="Reprocess preserved owner-safe shadow scenarios into player-visible native-CAI behavior evidence.")
    parser.add_argument(
        "--source",
        type=Path,
        default=REPO_ROOT / "research/runtime_evidence/CAMPAIGN_TURNS_4_7_REPROCESS_v0.1J.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "research/runtime_evidence/PLAYER_VISIBLE_NATIVE_BEHAVIOR_REPROCESS_v0.2K.json",
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
