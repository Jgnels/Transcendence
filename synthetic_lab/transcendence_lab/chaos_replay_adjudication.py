from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

from .canonical import digest

CAPTURE_CONTRACT = "SFO_CHAOS_REPLAY_STREAM_CAPTURE_V1"
CALIBRATION_CONTRACT = "SFO_CHAOS_REPLAY_DIVERGENCE_CALIBRATION_V1"
UNIT_FINDINGS_CONTRACT = "SFO_CHAOS_REPLAY_UNIT_FINDINGS_V1"

EXPECTED_REPLAY_SHA256 = "28d780d02f2af07fe16fe4a24a27cd37f41bdb870d485f11949d5ed63f838cb5"
EXPECTED_RECORDING_SHA256 = "6e008c378a8e4273ca7d2c8101ca69279839a5c21dbaf749fb5e666adde56155"
EXPECTED_BUNDLE_SHA256 = "18293f7f59fc9a2130a6c82ec48636097c946605d49980cfcb0f154a8c1a6126"
EXPECTED_RAW_LOG_SHA256 = "2175b2643f80b7e7fde9edd66443df1b8b5f2205ec3aad51fab013d48a686c0c"
EXPECTED_DENSE_SHA256 = "bafc5884ea01c5d05e472423c41989ed5c23559d9365f07d2d608f5ed89797ef"
EXPECTED_DENSE_RESULT_DIGEST = "4d84f49ec1782d29e872eff6674e93af089c3290a765b5d20c95b815ee70cea4"
EXPECTED_CAPTURE_RESULT_DIGEST = "3febf48a92ce7309d912634b1540d29e1051a30835622b847b8da360aa6e74dc"
EXPECTED_UNIT_FINDINGS_RESULT_DIGEST = "12609e324eec28eed50ee2d79ca3e42d3f71787597d2ce28362257bbb40c7ae0"
EXPECTED_BATTLE_REPORT_SHA256 = "6fdcf98c1b2930b04f1ec208fdb5de84ebab6315ed7ea046b6944cb895a3bb2c"
EXPECTED_BATTLE_REPORT_RESULT_DIGEST = "e981e480432b73fab5707f7ef1d0a9b3bb33e7bf43416eb17791b9bf4fa92371"
EXPECTED_SFO_SHA256 = "ae20a0a08037aa3ebcbe7461d2589fc28dc15a5fe5d9ca4c0a9d0ff0a26da603"
EXPECTED_PROBE_SHA256 = "6e3f8e7bbc7d66754a7fa764c802e2b5599d13e83820e0785cb85d738040f66d"
EXPECTED_SCRIPT_SHA256 = "86e18ec655c4a45a4a062d1dae7d10e6fd9a1cb77af5557757fbca9ed896562e"

_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_FORBIDDEN_KEYS = {
    "absolute_path",
    "local_path",
    "source_path",
    "video_path",
    "replay_path",
    "raw_video",
    "video_bytes",
    "frame_bytes",
    "replay_bytes",
    "raw_replay",
    "raw_log",
}
_FORBIDDEN_PROMOTIONS = {
    "ACKNOWLEDGED",
    "EXECUTED",
    "CAUSAL_EXECUTION",
    "OPTIMAL_POLICY",
    "TACTICAL_SUPERIORITY",
    "OBSERVED_DEFEAT",
    "OBSERVED_DEFEAT_GRADE",
}


class ChaosReplayAdjudicationError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ChaosReplayAdjudicationError(message)


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _validate_hash(value: object, name: str) -> str:
    _require(isinstance(value, str) and _HEX64.fullmatch(value) is not None, f"{name} must be lowercase SHA-256")
    return value


def _walk_private(value: Any, path: str = "root") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            lowered = str(key).lower()
            if lowered in _FORBIDDEN_KEYS or lowered.endswith("_path"):
                raise ChaosReplayAdjudicationError(f"private or binary field is prohibited at {path}.{key}")
            _walk_private(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_private(child, f"{path}[{index}]")
    elif isinstance(value, str):
        lowered = value.lower()
        if "c:\\users\\" in lowered or "/users/" in lowered or "/home/" in lowered or "/mnt/" in lowered:
            raise ChaosReplayAdjudicationError(f"private path string is prohibited at {path}")
        if value in _FORBIDDEN_PROMOTIONS:
            raise ChaosReplayAdjudicationError(f"forbidden claim promotion at {path}")


def _validate_result_digest(value: dict[str, Any]) -> None:
    payload = copy.deepcopy(value)
    claimed = payload.pop("result_digest", None)
    _validate_hash(claimed, "result_digest")
    _require(claimed == digest(payload), "result_digest does not match canonical payload")


def validate_chaos_replay_stream_capture(value: dict[str, Any]) -> dict[str, Any]:
    _require(isinstance(value, dict), "capture must be an object")
    _walk_private(value)
    _validate_result_digest(value)
    _require(value.get("result_digest") == EXPECTED_CAPTURE_RESULT_DIGEST, "capture identity changed")
    _require(value.get("schema_version") == 1, "schema_version must be 1")
    _require(value.get("contract") == CAPTURE_CONTRACT, "unexpected capture contract")
    _require(value.get("status") == "OBSERVED_DENSE_NONTERMINAL_REPLAY_STREAM", "unexpected capture status")
    _require(value.get("evidence_label") == "LIMITING_RESULT", "capture must remain a limiting result")
    _require(value.get("authority") == "NO_ORDERS", "authority must remain NO_ORDERS")

    source = value.get("source")
    _require(isinstance(source, dict), "source descriptor is required")
    _require(_validate_hash(source.get("private_bundle_sha256"), "source.private_bundle_sha256") == EXPECTED_BUNDLE_SHA256, "private bundle changed")
    _require(_validate_hash(source.get("raw_log_sha256"), "source.raw_log_sha256") == EXPECTED_RAW_LOG_SHA256, "raw log identity changed")
    _require(_validate_hash(source.get("dense_corpus_sha256"), "source.dense_corpus_sha256") == EXPECTED_DENSE_SHA256, "dense corpus bytes changed")
    _require(_validate_hash(source.get("dense_corpus_result_digest"), "source.dense_corpus_result_digest") == EXPECTED_DENSE_RESULT_DIGEST, "dense corpus digest changed")
    _require(source.get("export_manifest_verified") is True, "export manifest must be verified")

    identity = value.get("identity")
    _require(isinstance(identity, dict), "identity descriptor is required")
    _require(identity.get("display_title") == "An Ogre's Folly", "display title changed")
    _require(identity.get("local_faction") == "Reikland", "local faction changed")
    _require(identity.get("enemy_display") == "Warhost of the Apocalypse", "enemy display changed")
    _require(_validate_hash(identity.get("replay_sha256"), "identity.replay_sha256") == EXPECTED_REPLAY_SHA256, "replay identity changed")
    _require(_validate_hash(identity.get("recording_sha256"), "identity.recording_sha256") == EXPECTED_RECORDING_SHA256, "recording identity changed")
    _require(identity.get("replay_binary_committed") is False, "replay binary may not be committed")
    _require(identity.get("recording_committed") is False, "recording may not be committed")

    environment = value.get("environment")
    _require(isinstance(environment, dict), "environment descriptor is required")
    _require(environment.get("verified") is True, "exact environment must be verified")
    _require(environment.get("timed_out") is False, "capture may not be a timeout")
    _require(environment.get("parse_error") is None, "capture may not have a parse error")
    _require(environment.get("active_mod_count") == 2, "exact two-mod environment required")
    _require(environment.get("sfo_pack_sha256") == EXPECTED_SFO_SHA256, "SFO hash changed")
    _require(environment.get("observer_pack_sha256") == EXPECTED_PROBE_SHA256, "probe hash changed")
    _require(environment.get("shared_battle_script_sha256") == EXPECTED_SCRIPT_SHA256, "observer script changed")
    _require(environment.get("orders_emitted") is False, "orders must remain absent")
    _require(environment.get("save_modified") is False, "save must remain unmodified")

    capture = value.get("capture")
    _require(isinstance(capture, dict), "capture metrics are required")
    _require(capture.get("schema_version") == 2, "schema-2 capture required")
    _require(capture.get("battle_complete_marker_observed") is False, "BATTLE_COMPLETE was not observed")
    _require(capture.get("completed_battle_count") == 0, "completed battle count must remain zero")
    _require(capture.get("detail_samples") == 115, "detail sample count changed")
    _require(capture.get("expected_detail_samples") == 113, "expected sample count changed")
    _require(capture.get("maximum_sample_gap_ms") == 3400, "sample gap changed")
    _require(capture.get("canonical_unit_count") == 23, "canonical unit count changed")
    _require(capture.get("identity_alias_count") == 0, "identity aliases must remain zero")
    _require(capture.get("command_event_count") == 89, "command count changed")
    _require(capture.get("local_terminal_coverage_ratio") == 0.0, "local terminal coverage must remain zero")
    _require(capture.get("visible_enemy_terminal_coverage_ratio") == 0.0, "enemy terminal coverage must remain zero")

    lifecycle = value.get("visual_lifecycle_alignment")
    _require(isinstance(lifecycle, dict), "visual lifecycle alignment is required")
    _require(lifecycle.get("replay_stream_end_overlay_observed") is True, "replay end overlay must be observed")
    _require(lifecycle.get("overlay_controls_observed") == ["Load Replay", "End Battle"], "overlay controls changed")
    _require(lifecycle.get("post_stream_summary_valid_as_original_battle_result") is False, "zero-loss replay exit summary must remain invalid")
    zero = lifecycle.get("post_stream_summary_loss_counts")
    _require(isinstance(zero, dict) and zero.get("local_losses") == 0 and zero.get("enemy_losses") == 0, "zero-loss replay exit result changed")

    provenance = value.get("outcome_provenance")
    _require(isinstance(provenance, dict), "outcome provenance is required")
    original = provenance.get("original_live_battle")
    replayed = provenance.get("replayed_simulation")
    _require(isinstance(original, dict) and original.get("evidence_label") == "OWNER_ATTESTED", "original defeat must remain owner-attested")
    _require(original.get("grade") == "UNVERIFIED", "original grade must remain unverified")
    _require(isinstance(replayed, dict) and replayed.get("evidence_label") == "LIMITING_RESULT", "replay outcome must remain limiting")
    _require(replayed.get("victorious_alliance") == "UNVERIFIED", "replay victor must remain unverified")
    return copy.deepcopy(value)


def _unit_by_type(units: list[dict[str, Any]], unit_type: str) -> dict[str, Any]:
    matches = [unit for unit in units if unit.get("unit_type") == unit_type]
    _require(len(matches) == 1, f"expected exactly one unit of type {unit_type}")
    return matches[0]


def _units_by_type(units: list[dict[str, Any]], unit_type: str) -> list[dict[str, Any]]:
    matches = [unit for unit in units if unit.get("unit_type") == unit_type]
    _require(matches, f"expected units of type {unit_type}")
    return sorted(matches, key=lambda item: str(item.get("stable_unit_id")))


def validate_chaos_dense_corpus(value: dict[str, Any], capture: dict[str, Any]) -> dict[str, Any]:
    _require(isinstance(value, dict), "dense corpus must be an object")
    _walk_private(value)
    _require(value.get("result_digest") == EXPECTED_DENSE_RESULT_DIGEST, "dense corpus result digest changed")
    _require(value.get("source", {}).get("replay_sha256") == EXPECTED_REPLAY_SHA256, "dense corpus replay changed")
    _require(value.get("source", {}).get("raw_trans_battle_log_sha256") == EXPECTED_RAW_LOG_SHA256, "dense corpus raw log changed")
    _require(value.get("source", {}).get("raw_log_committed") is False, "raw log may not be committed")
    _require(value.get("source", {}).get("raw_replay_committed") is False, "raw replay may not be committed")
    _require(value.get("owner_context", {}).get("outcome_grade_mapping") == "UNVERIFIED", "dense corpus may not promote outcome grade")

    battle = value.get("battle")
    _require(isinstance(battle, dict), "dense battle is required")
    _require(battle.get("duration_ms") == 338500, "dense duration changed")
    _require(battle.get("result") == {}, "nonterminal replay must not contain a result")
    _require(battle.get("sampling", {}).get("quality") == "DENSE_INTERVAL_COVERAGE", "dense sampling quality changed")
    _require(battle.get("sampling", {}).get("observed_detail_samples") == capture["capture"]["detail_samples"], "detail sample binding failed")
    _require(battle.get("identity_reconciliation", {}).get("canonical_unit_count") == 23, "unit identity count changed")
    _require(battle.get("identity_reconciliation", {}).get("identity_alias_count") == 0, "identity alias count changed")
    _require(len(battle.get("units", [])) == 23, "unit metric count changed")
    _require(battle.get("outcome_metrics", {}).get("local_terminal_coverage_ratio") == 0.0, "local terminal coverage changed")
    _require(battle.get("outcome_metrics", {}).get("visible_enemy_terminal_coverage_ratio") == 0.0, "enemy terminal coverage changed")
    return copy.deepcopy(value)


def validate_chaos_unit_findings(value: dict[str, Any], capture: dict[str, Any]) -> dict[str, Any]:
    _require(isinstance(value, dict), "unit findings must be an object")
    _walk_private(value)
    _validate_result_digest(value)
    _require(value.get("result_digest") == EXPECTED_UNIT_FINDINGS_RESULT_DIGEST, "unit findings identity changed")
    _require(value.get("schema_version") == 1, "unit findings schema_version must be 1")
    _require(value.get("contract") == UNIT_FINDINGS_CONTRACT, "unexpected unit findings contract")
    _require(value.get("status") == "OBSERVED_DENSE_NONTERMINAL_UNIT_FINDINGS", "unexpected unit findings status")
    _require(value.get("evidence_label") == "LIMITING_RESULT", "unit findings must remain a limiting result")
    _require(value.get("authority") == "NO_ORDERS", "unit findings authority must remain NO_ORDERS")

    source = value.get("source")
    _require(isinstance(source, dict), "unit findings source is required")
    _require(source.get("replay_sha256") == EXPECTED_REPLAY_SHA256, "unit findings replay changed")
    _require(source.get("raw_log_sha256") == EXPECTED_RAW_LOG_SHA256, "unit findings raw log changed")
    _require(source.get("battle_report_sha256") == EXPECTED_BATTLE_REPORT_SHA256, "battle report bytes changed")
    _require(source.get("battle_report_result_digest") == EXPECTED_BATTLE_REPORT_RESULT_DIGEST, "battle report digest changed")
    _require(source.get("private_battle_report_committed") is False, "private battle report may not be committed")

    battle = value.get("battle")
    _require(isinstance(battle, dict), "unit findings battle is required")
    _require(battle.get("complete") is False, "unit findings may not claim completion")
    _require(battle.get("duration_ms") == capture["capture"]["duration_ms"], "unit findings duration changed")
    _require(battle.get("first_engagement_time_ms") == 49400, "first engagement time changed")
    units = battle.get("units")
    _require(isinstance(units, list) and len(units) == 23, "exact 23 unit findings required")
    stable_ids = [unit.get("stable_unit_id") for unit in units]
    _require(len(stable_ids) == len(set(stable_ids)), "duplicate stable unit identity")
    _require(all(unit.get("terminal_state_observed") is False for unit in units), "no terminal unit observation is valid")
    return copy.deepcopy(value)


def build_chaos_replay_divergence_calibration(
    capture_value: dict[str, Any],
    dense_value: dict[str, Any],
    unit_findings_value: dict[str, Any],
) -> dict[str, Any]:
    capture = validate_chaos_replay_stream_capture(capture_value)
    dense = validate_chaos_dense_corpus(dense_value, capture)
    unit_findings = validate_chaos_unit_findings(unit_findings_value, capture)
    battle = dense["battle"]
    units = unit_findings["battle"]["units"]
    local_units = [unit for unit in units if unit.get("local_alliance") is True]
    enemy_units = [unit for unit in units if unit.get("local_alliance") is False]
    _require(len(local_units) == 13 and len(enemy_units) == 10, "local/enemy unit counts changed")

    zintler = _unit_by_type(local_units, "wh_dlc04_emp_cav_zintlers_reiksguard_0")
    tattersouls = _unit_by_type(local_units, "wh_dlc04_emp_inf_tattersouls_0")
    artillery = _units_by_type(local_units, "wh_main_emp_art_helstorm_rocket_battery")
    halberds = _units_by_type(local_units, "wh_main_emp_inf_halberdiers")
    elspeth = _unit_by_type(local_units, "wh3_dlc25_emp_cha_elspeth_von_draken")
    captain = _unit_by_type(local_units, "wh_main_emp_cha_captain_0")
    archaon = _unit_by_type(enemy_units, "wh_main_chs_cha_archaon_the_everchosen_1")
    chaos_knights = _unit_by_type(enemy_units, "wh3_dlc20_chs_cav_chaos_knights_msla_lances")

    local_last = battle["aggregate_timeline"]["1"][-1]
    enemy_last = battle["aggregate_timeline"]["2"][-1]
    commands = battle["command_analysis"]
    target_map = {item["unit_type"]: item for item in commands["targets"]}
    archaon_target_count = target_map["wh_main_chs_cha_archaon_the_everchosen_1"]["command_count"]

    output: dict[str, Any] = {
        "schema_version": 1,
        "contract": CALIBRATION_CONTRACT,
        "status": "CLOSED_LIMITING_RESULT_REPLAY_DIVERGENCE",
        "evidence_label": "LIMITING_RESULT",
        "authority": "NO_ORDERS",
        "source_capture_digest": capture["result_digest"],
        "source_dense_digest": dense["result_digest"],
        "source_unit_findings_digest": unit_findings["result_digest"],
        "identity": copy.deepcopy(capture["identity"]),
        "environment": {
            "exact_sfo_pack_sha256": capture["environment"]["sfo_pack_sha256"],
            "exact_observer_pack_sha256": capture["environment"]["observer_pack_sha256"],
            "exact_shared_script_sha256": capture["environment"]["shared_battle_script_sha256"],
            "environment_verified": True,
        },
        "lifecycle_adjudication": {
            "natural_battle_complete_observed": False,
            "replay_stream_end_overlay_observed": True,
            "post_stream_zero_loss_summary_observed": True,
            "post_stream_summary_is_valid_outcome_evidence": False,
            "classification": "REPLAY_COMMAND_STREAM_EXHAUSTED_WITHOUT_BATTLE_COMPLETE",
            "original_live_battle_outcome": "OWNER_ATTESTED_DEFEAT",
            "original_live_battle_grade": "UNVERIFIED",
            "replayed_simulation_outcome": "UNVERIFIED_NONTERMINAL",
            "victorious_alliance": "UNVERIFIED",
        },
        "dense_observation": {
            "duration_ms": battle["duration_ms"],
            "detail_samples": battle["sampling"]["observed_detail_samples"],
            "aggregate_samples": sum(len(items) for items in battle["aggregate_timeline"].values()),
            "maximum_sample_gap_ms": battle["sampling"]["maximum_sample_gap_ms"],
            "canonical_units": battle["identity_reconciliation"]["canonical_unit_count"],
            "identity_aliases": battle["identity_reconciliation"]["identity_alias_count"],
            "commands_observed": commands["command_event_count"],
            "commands_inferred_to_units": battle["inferred_command_attribution"]["inferred_command_count"],
            "selection_attribution_ratio": commands["selection_attribution_ratio"],
            "first_engagement_time_ms": unit_findings["battle"]["first_engagement_time_ms"],
            "local_casualties_observed_lower_bound": battle["outcome_metrics"]["local_casualties_observed_lower_bound"],
            "visible_enemy_casualties_observed_lower_bound": battle["outcome_metrics"]["visible_enemy_casualties_observed_lower_bound"],
            "terminal_coverage_ratio": {
                "local": battle["outcome_metrics"]["local_terminal_coverage_ratio"],
                "visible_enemy": battle["outcome_metrics"]["visible_enemy_terminal_coverage_ratio"],
            },
        },
        "last_observed_snapshot": {
            "time_ms": local_last["time_ms"],
            "local": {
                "observed_units": local_last["observed_units"],
                "men_alive": local_last["men_alive"],
                "kills": local_last["kills"],
                "strategic_value_proxy": round(float(local_last["strategic_value_proxy"]), 6),
                "routing": local_last["units_routing"],
                "wavering": local_last["units_wavering"],
                "in_melee": local_last["units_in_melee"],
            },
            "visible_enemy": {
                "observed_units": enemy_last["observed_units"],
                "men_alive": enemy_last["men_alive"],
                "kills": enemy_last["kills"],
                "strategic_value_proxy": round(float(enemy_last["strategic_value_proxy"]), 6),
                "routing": enemy_last["units_routing"],
                "wavering": enemy_last["units_wavering"],
                "in_melee": enemy_last["units_in_melee"],
            },
            "interpretation": "NONTERMINAL_SNAPSHOT_NOT_OUTCOME",
        },
        "unit_findings": [
            {
                "finding_id": "cavalry_preservation_failure",
                "evidence_label": "SUPPORTED",
                "unit_type": zintler["unit_type"],
                "first_engagement_time_ms": zintler["first_engagement_time_ms"],
                "first_routing_time_ms": zintler["first_routing_time_ms"],
                "casualties_observed_lower_bound": zintler["casualties_observed_lower_bound"],
                "kills_observed_max": zintler["kills_observed_max"],
                "note": "The elite cavalry lost at least 58 of 60 models while recording one kill; this supports a preservation failure but not a causal explanation.",
            },
            {
                "finding_id": "tattersouls_local_collapse",
                "evidence_label": "SUPPORTED",
                "unit_type": tattersouls["unit_type"],
                "first_engagement_time_ms": tattersouls["first_engagement_time_ms"],
                "casualties_observed_lower_bound": tattersouls["casualties_observed_lower_bound"],
                "kills_observed_max": tattersouls["kills_observed_max"],
                "last_observed_time_ms": tattersouls["last_observed_time_ms"],
                "note": "Tattersouls fell from 160 to one observed model with four kills before the replay stream ended.",
            },
            {
                "finding_id": "artillery_early_crisis",
                "evidence_label": "SUPPORTED",
                "first_engagement_time_ms": min(unit["first_engagement_time_ms"] for unit in artillery),
                "first_routing_times_ms": [unit["first_routing_time_ms"] for unit in artillery],
                "casualties_observed_lower_bound": sum(unit["casualties_observed_lower_bound"] for unit in artillery),
                "note": "Both Helstorm batteries engaged by 49.4 seconds and first routed near 182–185 seconds; one ceased observation at 293.1 seconds.",
            },
            {
                "finding_id": "uneven_frontline_commitment",
                "evidence_label": "SUPPORTED",
                "halberd_first_engagement_times_ms": [unit["first_engagement_time_ms"] for unit in halberds],
                "halberd_casualty_lower_bounds": [unit["casualties_observed_lower_bound"] for unit in halberds],
                "note": "One Halberdier unit engaged at 140.1 seconds and lost at least 69 models; the other first engaged at 212.1 seconds and lost two, refining the visual 'no reserve' hypothesis into delayed or uneven commitment.",
            },
            {
                "finding_id": "commander_crisis",
                "evidence_label": "SUPPORTED",
                "elspeth": {
                    "first_routing_time_ms": elspeth["first_routing_time_ms"],
                    "last_hitpoints_fraction": round(float(elspeth["last_observed_hitpoints_fraction"]), 6),
                },
                "captain": {
                    "first_routing_time_ms": captain["first_routing_time_ms"],
                    "last_hitpoints_fraction": round(float(captain["last_observed_hitpoints_fraction"]), 6),
                },
                "note": "Both local commanders routed at least once and ended the observed stream at low hitpoint fractions.",
            },
        ],
        "enemy_pressure_findings": [
            {
                "finding_id": "archaon_pressure",
                "evidence_label": "OBSERVED",
                "kills_observed_max": archaon["kills_observed_max"],
                "last_hitpoints_fraction": round(float(archaon["last_observed_hitpoints_fraction"]), 6),
            },
            {
                "finding_id": "chaos_knight_pressure",
                "evidence_label": "OBSERVED",
                "kills_observed_max": chaos_knights["kills_observed_max"],
                "casualties_observed_lower_bound": chaos_knights["casualties_observed_lower_bound"],
                "last_hitpoints_fraction": round(float(chaos_knights["last_observed_hitpoints_fraction"]), 6),
            },
        ],
        "command_findings": {
            "command_counts": copy.deepcopy(commands["command_counts"]),
            "median_command_interval_ms": commands["median_command_interval_ms"],
            "sub_500ms_interval_count": commands["sub_500ms_interval_count"],
            "targeted_command_count": commands["targeted_command_count"],
            "archaon_targeted_command_count": archaon_target_count,
            "archaon_target_share": round(archaon_target_count / commands["targeted_command_count"], 6),
            "selection_attribution": "UNOBSERVED",
            "interpretation": "Observed concentration is a target-fixation hypothesis, not evidence that those commands were accepted, executed, or tactically wrong.",
        },
        "hypothesis_adjudication": [
            {
                "hypothesis_id": "wide_formation_support_failure",
                "status": "SUPPORTED_BOUNDED",
                "reason": "Visual separation and a 162.7-second spread between first local engagements support uneven mutual support; formation geometry remains visual rather than path-simulated.",
            },
            {
                "hypothesis_id": "no_protected_reserve",
                "status": "REFINED",
                "reason": "The second Halberdier unit remained nearly intact until a late 212.1-second first engagement. The stronger supported claim is delayed or uneven reserve commitment, not absence of a reserve.",
            },
            {
                "hypothesis_id": "piecemeal_commitment",
                "status": "SUPPORTED",
                "reason": "Local first-engagement times ranged from 49.4 to 212.1 seconds, with major unit losses concentrated among earlier committed elements.",
            },
            {
                "hypothesis_id": "ranged_and_artillery_firing_lane_degradation",
                "status": "SUPPORTED_BOUNDED",
                "reason": "Both artillery units routed early and ranged units retained ammunition while recording low kills; terrain and line-of-fire causality remain visually inferred.",
            },
            {
                "hypothesis_id": "target_fixation_on_archaon",
                "status": "HYPOTHESIS",
                "reason": f"Archaon received {archaon_target_count} of {commands['targeted_command_count']} observed targeted command events; selection attribution and tactical correctness remain unverified.",
            },
            {
                "hypothesis_id": "terminal_defeat_reproduced_by_replay",
                "status": "INVALIDATED",
                "reason": "The replay stream ended without BATTLE_COMPLETE, and the final observed state was nonterminal. The original defeat cannot be learned as a replayed terminal outcome.",
            },
        ],
        "policy_updates": [
            {
                "update_id": "replay_terminal_authority_guard",
                "status": "SUPPORTED",
                "rule": "Never learn outcome, victory grade, defeat irreversibility, or terminal casualty totals from replay-stream exhaustion. Require BATTLE_COMPLETE or a separately bound live result artifact.",
                "authority": "NO_ORDERS",
            },
            {
                "update_id": "reserve_state_refinement",
                "status": "SUPPORTED",
                "rule": "Distinguish reserve absent, reserve available, reserve committed late, and reserve unable to support; do not collapse them into one no-reserve diagnosis.",
                "authority": "ADVISORY_ONLY",
            },
            {
                "update_id": "elite_cavalry_loss_guard",
                "status": "SUPPORTED",
                "rule": "Raise a preservation crisis when elite cavalry incurs extreme losses with negligible observed effect; any proposed disengagement remains subject to legality and feasibility checks.",
                "authority": "ADVISORY_ONLY",
            },
            {
                "update_id": "target_concentration_review",
                "status": "HYPOTHESIS",
                "rule": "When one target absorbs a large share of targeted command traffic while multiple threats remain, trigger utility re-evaluation rather than automatically continuing focus.",
                "authority": "ADVISORY_ONLY",
            },
            {
                "update_id": "nonterminal_trace_learning_boundary",
                "status": "SUPPORTED",
                "rule": "Use the trace for state recognition, crisis timing, and lower-bound loss diagnosis only; exclude it from terminal-outcome and tactical-superiority training labels.",
                "authority": "NO_ORDERS",
            },
        ],
        "rejected_promotions": [
            "The replay reproduced the original defeat.",
            "The replay-exit zero-loss summary is a valid battle result.",
            "Observed commands were acknowledged or causally executed.",
            "The owner's tactics are optimal-policy labels.",
            "One Chaos replay proves general anti-Chaos tactical superiority.",
            "Lower-bound casualties are exact terminal totals.",
        ],
        "next_evidence_gaps": [
            "A future live battle result artifact that explicitly records the victorious alliance and grade.",
            "A naturally completed Chaos replay or live observer trace with BATTLE_COMPLETE.",
            "Selection-bound command attribution.",
            "Path, formation, collision, and line-of-fire feasibility.",
            "Independent Chaos battles before calibrating faction-general thresholds.",
        ],
    }
    output["result_digest"] = digest(output)
    return output
