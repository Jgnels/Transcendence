from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from parse_battle_log import canonical_json


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _require_sha(value: str, name: str) -> None:
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value.lower()):
        raise ValueError(f"{name} must be a lowercase SHA-256 hex digest")


def build_corpus(
    report: dict[str, Any],
    *,
    corpus_id: str,
    replay_sha256: str,
    raw_log_sha256: str,
    capture_verification_digest: str,
    owner_context: str,
) -> dict[str, Any]:
    _require_sha(replay_sha256, "replay_sha256")
    _require_sha(raw_log_sha256, "raw_log_sha256")
    _require_sha(capture_verification_digest, "capture_verification_digest")
    if report.get("battle_count") != 1:
        raise ValueError("observed corpus builder requires exactly one battle report")
    battle = report["battle_reports"][0]
    units = []
    for item in battle["unit_metrics"]:
        units.append(
            {
                "stable_unit_id": item["stable_unit_id"],
                "local_alliance": item["local_alliance"],
                "alliance_index": item["alliance_index"],
                "unit_type": item["unit_type"],
                "unit_class": item["unit_class"],
                "role": item["role"],
                "is_commander": item["is_commander"],
                "initial_men": item["initial_men"],
                "terminal_state_observed": item["terminal_state_observed"],
                "minimum_observed_men": item["minimum_observed_men"],
                "casualties_observed_lower_bound": item["casualties_observed_lower_bound"],
                "last_observed_hitpoints_fraction": item["last_observed_hitpoints_fraction"],
                "kills_observed_max": item["kills_observed_max"],
                "starting_ammo": item["starting_ammo"],
                "ammo_spent_observed_lower_bound": item["ammo_spent_observed_lower_bound"],
                "last_observed_flags": item["last_observed_flags"],
                "first_observed_time_ms": item["first_observed_time_ms"],
                "last_observed_time_ms": item["last_observed_time_ms"],
                "distance_travelled_observed_m": item.get("distance_travelled_observed_m"),
                "ordered_path_change_observed_m": item.get("ordered_path_change_observed_m"),
                "time_series_metrics": item.get("time_series_metrics"),
            }
        )

    sampling = battle["sampling"]
    dense = sampling.get("time_series_metrics_valid") is True
    forbidden_inferences = [
        "The owner command stream is optimal tactical policy.",
        "Units absent from the terminal sample survived without losses.",
        "Visible-enemy totals equal complete enemy-army totals before all units are revealed.",
        "Observed command events prove command acceptance or causal effectiveness.",
        "One replay establishes general tactical-AI quality or SFO compatibility.",
    ]
    if not dense:
        forbidden_inferences.insert(
            1,
            "Sparse phase samples establish exact engagement, routing, reserve, fatigue, or flank timing.",
        )

    corpus: dict[str, Any] = {
        "schema_version": 1,
        "corpus_id": corpus_id,
        "tier": "4R",
        "fidelity_label": (
            "OBSERVED_WH3_REPLAY_CORPUS_DENSE_TIMELINE"
            if dense
            else "OBSERVED_WH3_REPLAY_CORPUS_SPARSE_TIMELINE"
        ),
        "evidence_status": "OBSERVED",
        "source": {
            "replay_sha256": replay_sha256,
            "raw_trans_battle_log_sha256": raw_log_sha256,
            "capture_verification_result_digest": capture_verification_digest,
            "battle_report_result_digest": report["result_digest"],
            "raw_replay_committed": False,
            "raw_log_committed": False,
        },
        "battle": {
            "identity": "Battle of Eilhart — Reikland vs Empire Secessionists",
            "duration_ms": battle["duration_ms"],
            "metadata": battle["metadata"],
            "result": battle["result"],
            "sampling": sampling,
            "identity_reconciliation": battle["identity"],
            "unit_counts": battle["unit_counts"],
            "outcome_metrics": battle["outcome_metrics"],
            "command_analysis": battle["commands"],
            "inferred_command_attribution": battle.get("inferred_command_attribution"),
            "aggregate_timeline": battle.get("aggregate_timeline", []),
            "deployment_movements": battle["deployment_movements"],
            "units": units,
        },
        "owner_context": {
            "note": owner_context,
            "outcome_grade_mapping": "UNVERIFIED",
        },
        "synthetic_lab_uses": [
            "stable unit identity and hierarchy-churn regression",
            "visibility and hidden-enemy contract regression",
            "sampling-coverage sufficiency regression",
            "terminal-state and casualty lower-bound regression",
            "command-selection attribution regression",
            "force-composition and scale calibration anchor",
            "late-battle commander/frontline/ranged stress-case generation",
        ],
        "forbidden_inferences": forbidden_inferences,
    }
    corpus["result_digest"] = hashlib.sha256(canonical_json(corpus)).hexdigest()
    return corpus


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a public-safe observed battle corpus.")
    parser.add_argument("report", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--corpus-id", default="battle4_eilhart_observed_v1")
    parser.add_argument("--replay-sha256", required=True)
    parser.add_argument("--raw-log-sha256", required=True)
    parser.add_argument("--capture-verification-digest", required=True)
    parser.add_argument("--owner-context", required=True)
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    corpus = build_corpus(
        report,
        corpus_id=args.corpus_id,
        replay_sha256=args.replay_sha256,
        raw_log_sha256=args.raw_log_sha256,
        capture_verification_digest=args.capture_verification_digest,
        owner_context=args.owner_context,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(corpus, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(corpus, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
