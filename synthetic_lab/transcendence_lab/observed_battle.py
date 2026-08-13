from __future__ import annotations

import hashlib
import json
from typing import Any

from .canonical import digest


class ObservedBattleCorpusError(ValueError):
    pass


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(char in "0123456789abcdef" for char in value.lower())
    )


def validate_observed_battle_corpus(corpus: dict[str, Any]) -> dict[str, Any]:
    required = {
        "schema_version",
        "corpus_id",
        "tier",
        "fidelity_label",
        "evidence_status",
        "source",
        "battle",
        "forbidden_inferences",
    }
    missing = sorted(required - corpus.keys())
    if missing:
        raise ObservedBattleCorpusError(f"observed battle corpus missing: {missing}")
    if corpus["schema_version"] != 1:
        raise ObservedBattleCorpusError("unsupported observed battle corpus schema")
    if corpus["tier"] != "4R":
        raise ObservedBattleCorpusError("observed battle corpus must use tier 4R")
    if corpus["evidence_status"] != "OBSERVED":
        raise ObservedBattleCorpusError("observed battle corpus must be OBSERVED")
    source = corpus["source"]
    for key in (
        "replay_sha256",
        "raw_trans_battle_log_sha256",
        "capture_verification_result_digest",
        "battle_report_result_digest",
    ):
        if not _is_sha256(source.get(key)):
            raise ObservedBattleCorpusError(f"invalid source digest: {key}")
    if source.get("raw_replay_committed") is not False:
        raise ObservedBattleCorpusError("raw replay must not be committed")
    if source.get("raw_log_committed") is not False:
        raise ObservedBattleCorpusError("raw battle log must not be committed")

    battle = corpus["battle"]
    units = battle.get("units")
    if not isinstance(units, list) or not units:
        raise ObservedBattleCorpusError("observed battle corpus requires units")
    ids = [unit.get("stable_unit_id") for unit in units]
    if len(ids) != len(set(ids)):
        raise ObservedBattleCorpusError("duplicate stable unit identity in observed corpus")
    if any(not isinstance(unit_id, str) or ":u" not in unit_id for unit_id in ids):
        raise ObservedBattleCorpusError("observed corpus requires stable unique-ui identities")

    sampling = battle.get("sampling", {})
    time_series_valid = sampling.get("time_series_metrics_valid")
    if time_series_valid not in {True, False}:
        raise ObservedBattleCorpusError("sampling validity must be explicit")
    if time_series_valid and sampling.get("quality") != "DENSE_INTERVAL_COVERAGE":
        raise ObservedBattleCorpusError("valid time series requires dense interval coverage")
    outcome = battle.get("outcome_metrics", {})
    if outcome.get("exact_total_casualties_available") not in {True, False}:
        raise ObservedBattleCorpusError("casualty exactness must be explicit")
    commands = battle.get("command_analysis", {})
    ratio = commands.get("selection_attribution_ratio")
    if ratio is not None and not (0.0 <= float(ratio) <= 1.0):
        raise ObservedBattleCorpusError("selection attribution ratio is out of range")
    return corpus


def derive_reality_regressions(corpus: dict[str, Any]) -> dict[str, Any]:
    corpus = validate_observed_battle_corpus(corpus)
    battle = corpus["battle"]
    units = battle["units"]
    local = [unit for unit in units if unit["local_alliance"]]
    enemy = [unit for unit in units if not unit["local_alliance"]]

    endangered_commanders = sorted(
        unit["stable_unit_id"]
        for unit in local
        if unit["is_commander"]
        and unit["last_observed_hitpoints_fraction"] >= 0
        and unit["last_observed_hitpoints_fraction"] < 0.25
    )
    collapsed_frontline = sorted(
        unit["stable_unit_id"]
        for unit in local
        if unit["role"] == "frontline"
        and unit["initial_men"] > 0
        and unit["casualties_observed_lower_bound"] / unit["initial_men"] >= 0.5
    )
    high_output_ranged = sorted(
        unit["stable_unit_id"]
        for unit in local
        if unit["role"] in {"ranged", "specialist", "commander"}
        and unit["kills_observed_max"] >= 90
        and (unit["ammo_spent_observed_lower_bound"] or 0) >= 900
    )
    routed_enemy_terminal = sorted(
        unit["stable_unit_id"]
        for unit in enemy
        if unit["terminal_state_observed"]
        and unit["last_observed_flags"].get("routing") is True
    )
    disappeared_before_terminal = sorted(
        unit["stable_unit_id"]
        for unit in units
        if not unit["terminal_state_observed"]
    )

    checks = {
        "stable_identity_contract_holds": (
            not battle["identity_reconciliation"].get("identity_conflicts")
            and battle["identity_reconciliation"]["canonical_unit_count"] > 0
            and (
                (battle["identity_reconciliation"]["identity_alias_count"] > 0
                 and battle["identity_reconciliation"]["canonical_unit_count"]
                 < battle["identity_reconciliation"]["raw_unit_static_count"])
                or
                (battle["identity_reconciliation"]["identity_alias_count"] == 0
                 and battle["identity_reconciliation"]["canonical_unit_count"]
                 == battle["identity_reconciliation"]["raw_unit_static_count"])
            )
        ),
        "sampling_claims_match_coverage": (
            (battle["sampling"]["time_series_metrics_valid"] is False
             and battle["sampling"]["quality"] != "DENSE_INTERVAL_COVERAGE")
            or (battle["sampling"]["time_series_metrics_valid"] is True
                and battle["sampling"]["quality"] == "DENSE_INTERVAL_COVERAGE")
        ),
        "casualty_claim_matches_terminal_coverage": (
            battle["outcome_metrics"]["exact_total_casualties_available"]
            == (battle["outcome_metrics"].get("local_terminal_coverage_ratio") == 1.0
                and battle["outcome_metrics"].get("visible_enemy_terminal_coverage_ratio") == 1.0)
        ),
        "command_attribution_is_explicit": (
            battle["command_analysis"].get("selection_attribution_ratio") is not None
        ),
        "visibility_filter_observed_hidden_enemy_units": any(
            sample.get("hidden_enemy_units", 0) > 0
            for sample in battle.get("sampling", {}).get("samples", [])
        ) or battle["unit_counts"]["visible_enemy_canonical"] > 0,
        "commander_survival_stress_case_present": bool(endangered_commanders),
        "frontline_collapse_stress_case_present": bool(collapsed_frontline),
        "ranged_output_stress_case_present": bool(high_output_ranged),
        "enemy_rout_stress_case_present": bool(routed_enemy_terminal),
        "unknown_terminal_state_stress_case_present": bool(disappeared_before_terminal),
    }

    result: dict[str, Any] = {
        "schema_version": 1,
        "tier": "4R",
        "fidelity_label": "OBSERVED_TRACE_REGRESSION_NOT_SIMULATION",
        "corpus_id": corpus["corpus_id"],
        "source_corpus_digest": corpus["result_digest"],
        "checks": checks,
        "stress_cases": {
            "endangered_commanders": endangered_commanders,
            "collapsed_frontline": collapsed_frontline,
            "high_output_ranged_or_specialists": high_output_ranged,
            "routed_enemy_terminal": routed_enemy_terminal,
            "units_without_terminal_state": disappeared_before_terminal,
        },
        "calibration_anchors": {
            "duration_ms": battle["duration_ms"],
            "canonical_unit_count": battle["identity_reconciliation"]["canonical_unit_count"],
            "command_event_count": battle["command_analysis"]["command_event_count"],
            "local_casualties_observed_lower_bound": battle["outcome_metrics"][
                "local_casualties_observed_lower_bound"
            ],
            "visible_enemy_casualties_observed_lower_bound": battle["outcome_metrics"][
                "visible_enemy_casualties_observed_lower_bound"
            ],
            "local_kills_observed_max_sum": battle["outcome_metrics"][
                "local_kills_observed_max_sum"
            ],
        },
        "policy_constraints": [
            "Never interpret absent terminal units as undamaged or idle.",
            "Never compute timing metrics when sampling coverage is invalid.",
            "Never attribute commands to units without selection or explicitly labeled bounded inference evidence.",
            "Never include hidden enemy unit identity or state.",
            "Never treat the owner trace as an optimal policy label.",
        ],
        "evidence_status": "OBSERVED",
        "warnings": list(corpus["forbidden_inferences"]),
    }
    result["result_digest"] = digest(result)
    return result
