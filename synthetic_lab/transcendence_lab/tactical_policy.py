from __future__ import annotations

import copy
import math
import re
from typing import Any

from .canonical import digest
from .observed_battle import validate_observed_battle_corpus

POLICY_CONTRACT = "TACTICAL_CROSS_CORPUS_POLICY_ENVELOPE_V1"
EVALUATION_CONTRACT = "TACTICAL_POLICY_EVALUATION_V1"

EXPECTED_DENSE_DIGESTS = {
    "eilhart": "442e187638c4d2b3457910efdbb50d13f16fd27a8391e7ac9bd2d6aaed47c33d",
    "ubersreik": "a93340421c1c7a0623f21381d6d83de209299276e93c418ed193adb65ca8a5ec",
    "marienburg": "058f10ad125b554d3d63a0c1f768ed58ef8a9818473c2aebf515ac1458f957c0",
    "chaos": "4d84f49ec1782d29e872eff6674e93af089c3290a765b5d20c95b815ee70cea4",
}
EXPECTED_DUAL_CALIBRATION_DIGEST = "364431a064ef1f15bc6ab7da4417b688d882ac7f2035be753728d9d75870565e"
EXPECTED_CHAOS_CALIBRATION_DIGEST = "a69f2ed4e09034dc79ac5462aefa7f9c949c09a33a3e4e843e4a8cdecddcaab4"

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
    "hidden_enemy_state",
    "hidden_enemy_identity",
    "private_enemy_state",
}
_FORBIDDEN_PROMOTIONS = {
    "ISSUED",
    "ACKNOWLEDGED",
    "EXECUTED",
    "CAUSAL_EXECUTION",
    "OPTIMAL_POLICY",
    "TACTICAL_SUPERIORITY",
}
_ALLOWED_RESERVE_STATES = {
    "UNKNOWN",
    "ABSENT",
    "AVAILABLE",
    "COMMITTED_LATE",
    "UNABLE_TO_SUPPORT",
}


class TacticalPolicyError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise TacticalPolicyError(message)


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _walk_private(value: Any, path: str = "root") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            lowered = str(key).lower()
            if lowered in _FORBIDDEN_KEYS or lowered.endswith("_path"):
                raise TacticalPolicyError(f"private or hidden field is prohibited at {path}.{key}")
            _walk_private(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_private(child, f"{path}[{index}]")
    elif isinstance(value, str):
        lowered = value.lower()
        if "c:\\users\\" in lowered or "/users/" in lowered or "/home/" in lowered or "/mnt/" in lowered:
            raise TacticalPolicyError(f"private path string is prohibited at {path}")


def _validate_digest(value: object, name: str) -> str:
    _require(isinstance(value, str) and _HEX64.fullmatch(value) is not None, f"{name} must be lowercase SHA-256")
    return value


def _validate_result_digest(value: dict[str, Any], *, contract: str | None = None) -> dict[str, Any]:
    _require(isinstance(value, dict), "artifact must be an object")
    _walk_private(value)
    claimed = _validate_digest(value.get("result_digest"), "result_digest")
    payload = copy.deepcopy(value)
    payload.pop("result_digest", None)
    _require(claimed == digest(payload), "result_digest does not match canonical payload")
    if contract is not None:
        _require(value.get("contract") == contract, f"unexpected contract; expected {contract}")
    return copy.deepcopy(value)


def _validate_dual_calibration(value: dict[str, Any]) -> dict[str, Any]:
    result = _validate_result_digest(value, contract="SFO_DUAL_REPLAY_TACTICAL_CALIBRATION_V1")
    _require(result["result_digest"] == EXPECTED_DUAL_CALIBRATION_DIGEST, "dual replay calibration identity changed")
    _require(result.get("authority") == "NO_ORDERS", "dual replay calibration authority changed")
    _require(result.get("source_dense_result_digests") == {
        "marienburg": EXPECTED_DENSE_DIGESTS["marienburg"],
        "ubersreik": EXPECTED_DENSE_DIGESTS["ubersreik"],
    }, "dual replay dense provenance changed")
    by_id = {item.get("battle_id"): item for item in result.get("battles", [])}
    _require(set(by_id) == {"ubersreik", "marienburg"}, "dual replay cohort changed")
    for battle_id in ("ubersreik", "marienburg"):
        record = by_id[battle_id]
        _require(record.get("identity_resolution") == "VISUAL_TITLE_FOR_DISPLAY_RUNTIME_IDENTITY_RETAINED", f"{battle_id} identity provenance is not explicit")
        _require(record.get("runtime_identity") == "Battle of Eilhart — Reikland vs Empire Secessionists", f"{battle_id} runtime identity changed")
        _require(isinstance(record.get("visual_title"), str) and record["visual_title"].startswith("Battle of "), f"{battle_id} visual title missing")
    return result


def _validate_chaos_calibration(value: dict[str, Any]) -> dict[str, Any]:
    result = _validate_result_digest(value, contract="SFO_CHAOS_REPLAY_DIVERGENCE_CALIBRATION_V1")
    _require(result["result_digest"] == EXPECTED_CHAOS_CALIBRATION_DIGEST, "Chaos calibration identity changed")
    _require(result.get("authority") == "NO_ORDERS", "Chaos calibration authority changed")
    _require(result.get("source_dense_digest") == EXPECTED_DENSE_DIGESTS["chaos"], "Chaos dense provenance changed")
    lifecycle = result.get("lifecycle_adjudication", {})
    _require(lifecycle.get("natural_battle_complete_observed") is False, "Chaos replay must remain nonterminal")
    _require(lifecycle.get("replayed_simulation_outcome") == "UNVERIFIED_NONTERMINAL", "Chaos replay outcome was promoted")
    identity = result.get("identity", {})
    _require(identity.get("runtime_battlefield_identity") == "Battle of Eilhart — Reikland vs Empire Secessionists", "Chaos runtime identity changed")
    _require(identity.get("display_title") == "An Ogre's Folly", "Chaos display identity changed")
    return result


def _local_units(dense: dict[str, Any]) -> list[dict[str, Any]]:
    return [unit for unit in dense["battle"]["units"] if unit.get("local_alliance") is True]


def _role_summary(dense: dict[str, Any]) -> dict[str, dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for unit in _local_units(dense):
        role = str(unit["role"])
        bucket = buckets.setdefault(
            role,
            {
                "unit_count": 0,
                "initial_models": 0,
                "casualties_observed_lower_bound": 0,
                "kills_observed_max_sum": 0,
                "routing_units_observed": 0,
            },
        )
        bucket["unit_count"] += 1
        bucket["initial_models"] += int(unit["initial_men"])
        bucket["casualties_observed_lower_bound"] += int(unit["casualties_observed_lower_bound"])
        bucket["kills_observed_max_sum"] += int(unit["kills_observed_max"])
        if float(unit["time_series_metrics"].get("routing_sample_ratio", 0.0)) > 0.0:
            bucket["routing_units_observed"] += 1
    for bucket in buckets.values():
        initial = bucket["initial_models"]
        bucket["casualty_lower_bound_ratio"] = round(bucket["casualties_observed_lower_bound"] / initial, 6) if initial else 0.0
    return dict(sorted(buckets.items()))


def _identity_descriptor(
    battle_id: str,
    dense: dict[str, Any],
    dual: dict[str, Any],
    chaos: dict[str, Any],
) -> dict[str, Any]:
    runtime = dense["battle"]["identity"]
    if battle_id in {"ubersreik", "marienburg"}:
        record = next(item for item in dual["battles"] if item["battle_id"] == battle_id)
        return {
            "runtime_battlefield_identity": runtime,
            "display_identity": record["visual_title"],
            "identity_resolution": record["identity_resolution"],
            "source_layers_agree": runtime == record["visual_title"],
        }
    if battle_id == "chaos":
        identity = chaos["identity"]
        return {
            "runtime_battlefield_identity": runtime,
            "display_identity": identity["display_title"],
            "enemy_display": identity["enemy_display"],
            "identity_resolution": "DISPLAY_IDENTITY_RETAINED_SEPARATELY_FROM_RUNTIME_BATTLEFIELD_IDENTITY",
            "source_layers_agree": runtime == identity["display_title"],
        }
    return {
        "runtime_battlefield_identity": runtime,
        "display_identity": "Battle of Eilhart",
        "identity_resolution": "RUNTIME_IDENTITY_PRIMARY_NO_VISUAL_TITLE_OVERRIDE",
        "source_layers_agree": runtime.startswith("Battle of Eilhart"),
    }


def _battle_summary(
    battle_id: str,
    dense: dict[str, Any],
    dual: dict[str, Any],
    chaos: dict[str, Any],
) -> dict[str, Any]:
    battle = dense["battle"]
    local = _local_units(dense)
    _require(local, f"{battle_id} has no local units")
    initial_models = sum(int(unit["initial_men"]) for unit in local)
    casualties = int(battle["outcome_metrics"]["local_casualties_observed_lower_bound"])
    first_seen = sorted(int(unit["first_observed_time_ms"]) for unit in local)
    initial_observed = sum(time <= 100 for time in first_seen)
    natural_completion = bool(battle.get("result")) and battle.get("result", {}).get("outcome_decided") == "true"

    if battle_id in {"ubersreik", "marienburg"}:
        record = next(item for item in dual["battles"] if item["battle_id"] == battle_id)
        outcome_grade = record["outcome"]["visual_grade"]
        victorious = record["outcome"]["telemetry_victorious_alliance"]
        environment = "SFO"
    elif battle_id == "chaos":
        outcome_grade = chaos["lifecycle_adjudication"]["replayed_simulation_outcome"]
        victorious = chaos["lifecycle_adjudication"]["victorious_alliance"]
        environment = "SFO"
    else:
        outcome_grade = "UNVERIFIED"
        victorious = battle.get("result", {}).get("victorious_alliance", "UNVERIFIED")
        environment = "VANILLA"

    summary: dict[str, Any] = {
        "battle_id": battle_id,
        "environment": environment,
        "battle_type": battle["metadata"]["battle_type"],
        "source_dense_digest": dense["result_digest"],
        "identity": _identity_descriptor(battle_id, dense, dual, chaos),
        "duration_ms": int(battle["duration_ms"]),
        "local_units": len(local),
        "initial_local_units_observed": initial_observed,
        "force_initial_fraction": round(initial_observed / len(local), 6),
        "force_discovery_end_ms": max(first_seen),
        "local_initial_models": initial_models,
        "local_casualties_observed_lower_bound": casualties,
        "local_casualty_lower_bound_ratio": round(casualties / initial_models, 6) if initial_models else 0.0,
        "visible_enemy_casualties_observed_lower_bound": int(battle["outcome_metrics"]["visible_enemy_casualties_observed_lower_bound"]),
        "local_terminal_coverage_ratio": float(battle["outcome_metrics"]["local_terminal_coverage_ratio"]),
        "visible_enemy_terminal_coverage_ratio": float(battle["outcome_metrics"]["visible_enemy_terminal_coverage_ratio"]),
        "command_events": int(battle["command_analysis"]["command_event_count"]),
        "selection_attribution_ratio": float(battle["command_analysis"].get("selection_attribution_ratio") or 0.0),
        "natural_completion_observed": natural_completion,
        "outcome_grade": outcome_grade,
        "victorious_alliance": victorious,
        "role_summary": _role_summary(dense),
    }
    if battle_id == "chaos":
        summary["original_live_outcome"] = chaos["lifecycle_adjudication"]["original_live_battle_outcome"]
    return summary


def _policy_rules(summaries: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    # Rules are deliberately declarative. They never emit runtime commands.
    return [
        {
            "rule_id": "terminal_evidence_authority_guard",
            "status": "SUPPORTED_MULTI_CORPUS",
            "supporting_battles": ["eilhart", "ubersreik", "marienburg", "chaos"],
            "rule": "Never infer a terminal result from replay exhaustion, process exit, stable log bytes, or a post-replay summary. Outcome labels require natural completion or a separately bound result artifact.",
            "application": "ABSTAIN_FROM_TERMINAL_LEARNING_WITHOUT_TERMINAL_EVIDENCE",
            "authority": "NO_ORDERS",
        },
        {
            "rule_id": "identity_provenance_separation",
            "status": "OBSERVED_MULTI_SOURCE",
            "supporting_battles": ["ubersreik", "marienburg", "chaos"],
            "rule": "Preserve runtime battlefield identity and replay/display identity as separate provenance layers when they disagree; never silently rewrite either source.",
            "application": "PRESERVE_IDENTITY_LAYERS",
            "authority": "NO_ORDERS",
        },
        {
            "rule_id": "force_completeness_guard",
            "status": "SUPPORTED_MULTI_CORPUS",
            "supporting_battles": [battle_id for battle_id in ("eilhart", "ubersreik", "marienburg") if summaries[battle_id]["force_initial_fraction"] < 1.0],
            "rule": "Treat the currently observed local hierarchy as incomplete while force discovery is changing; defer whole-force assumptions until the observation boundary stabilizes.",
            "application": "DEFER_WHOLE_FORCE_ASSUMPTIONS_WHILE_DISCOVERY_CHANGES",
            "authority": "ADVISORY_ONLY",
        },
        {
            "rule_id": "victory_grade_cost_separation",
            "status": "SUPPORTED_MULTI_CORPUS",
            "supporting_battles": ["ubersreik", "marienburg"],
            "rule": "Evaluate victory grade separately from preservation cost, role-specific losses, crisis exposure, and duration.",
            "application": "SCORE_COST_DIMENSIONS_SEPARATELY_FROM_WIN_STATUS",
            "authority": "ADVISORY_ONLY",
        },
        {
            "rule_id": "local_crisis_preservation_priority",
            "status": "SUPPORTED_MULTI_CORPUS",
            "supporting_battles": ["eilhart", "marienburg", "chaos"],
            "rule": "When local morale or high-value assets are in crisis, preserve those assets before adding discretionary commitment, including when visible enemy collapse or terminal evidence is also present.",
            "application": "PRESERVATION_FIRST_DURING_LOCAL_CRISIS",
            "authority": "ADVISORY_ONLY",
        },
        {
            "rule_id": "severe_asset_loss_ratio_guard",
            "status": "SUPPORTED_MULTI_CORPUS",
            "supporting_battles": ["eilhart", "chaos"],
            "rule": "Trigger preservation review from loss fraction, not an absolute model-loss count. A 50% observed lower-bound loss is severe regardless of unit model count.",
            "application": "REVIEW_HIGH_VALUE_ASSET_AT_OR_ABOVE_HALF_LOSS",
            "authority": "ADVISORY_ONLY",
            "severe_loss_ratio_threshold": 0.5,
        },
        {
            "rule_id": "reserve_state_refinement",
            "status": "SUPPORTED_BOUNDED",
            "supporting_battles": ["chaos"],
            "rule": "Distinguish reserve unknown, absent, available, committed late, and unable to support. Never collapse delayed or uneven commitment into a no-reserve label.",
            "application": "RETAIN_EXPLICIT_RESERVE_STATE",
            "authority": "ADVISORY_ONLY",
        },
        {
            "rule_id": "terminal_commitment_abstention",
            "status": "SUPPORTED_MULTI_CORPUS",
            "supporting_battles": ["eilhart", "ubersreik", "marienburg"],
            "rule": "After natural outcome-decision evidence, prohibit new high-commitment proposals; bounded preservation, disengagement, reformation, and pursuit review may remain advisory.",
            "application": "NO_NEW_HIGH_COMMITMENT_AFTER_TERMINAL_EVIDENCE",
            "authority": "ADVISORY_ONLY",
        },
        {
            "rule_id": "target_concentration_review",
            "status": "HYPOTHESIS_SINGLE_CORPUS",
            "supporting_battles": ["chaos"],
            "rule": "When a large share of targeted command traffic concentrates on one target while other threats remain, request utility re-evaluation only. Without selection-bound attribution this is not a finding of tactical error.",
            "application": "HYPOTHESIS_REVIEW_ONLY",
            "authority": "ADVISORY_ONLY",
        },
        {
            "rule_id": "owner_command_churn_reference_only",
            "status": "SUPPORTED_BOUNDARY",
            "supporting_battles": ["eilhart", "ubersreik", "marienburg", "chaos"],
            "rule": "Observed owner command counts are workload and chronology references, not target control rates, acknowledgements, execution proof, or optimal-policy labels.",
            "application": "REFERENCE_ONLY_NOT_CAUSAL",
            "authority": "NO_ORDERS",
        },
    ]


def build_cross_corpus_policy_envelope(
    dense_corpora: dict[str, dict[str, Any]],
    dual_replay_calibration: dict[str, Any],
    chaos_replay_calibration: dict[str, Any],
) -> dict[str, Any]:
    _require(set(dense_corpora) == set(EXPECTED_DENSE_DIGESTS), "exact four-corpus cohort is required")
    dual = _validate_dual_calibration(dual_replay_calibration)
    chaos = _validate_chaos_calibration(chaos_replay_calibration)

    validated: dict[str, dict[str, Any]] = {}
    replay_hashes: set[str] = set()
    for battle_id in sorted(dense_corpora):
        dense = copy.deepcopy(validate_observed_battle_corpus(dense_corpora[battle_id]))
        _walk_private(dense)
        _require(dense.get("result_digest") == EXPECTED_DENSE_DIGESTS[battle_id], f"foreign or altered dense corpus for {battle_id}")
        replay_hash = _validate_digest(dense["source"].get("replay_sha256"), f"{battle_id}.replay_sha256")
        _require(replay_hash not in replay_hashes, "duplicate replay binary identity in four-corpus cohort")
        replay_hashes.add(replay_hash)
        validated[battle_id] = dense

    _require(dual["source_dense_result_digests"]["ubersreik"] == validated["ubersreik"]["result_digest"], "Ubersreik calibration binding changed")
    _require(dual["source_dense_result_digests"]["marienburg"] == validated["marienburg"]["result_digest"], "Marienburg calibration binding changed")
    _require(chaos["source_dense_digest"] == validated["chaos"]["result_digest"], "Chaos calibration binding changed")

    battle_summaries = [
        _battle_summary(battle_id, validated[battle_id], dual, chaos)
        for battle_id in sorted(validated)
    ]
    by_id = {item["battle_id"]: item for item in battle_summaries}
    policy_rules = _policy_rules(by_id)

    output: dict[str, Any] = {
        "schema_version": 1,
        "contract": POLICY_CONTRACT,
        "policy_id": "reikland_cross_corpus_tactical_policy_envelope_v0.2D",
        "authority": "NO_ORDERS",
        "application_authority": "PROHIBITED",
        "evidence_status": "CONTROL_OFFLINE_OVER_OBSERVED_AND_LIMITING_INPUTS",
        "source_provenance": {
            "dense_result_digests": {battle_id: validated[battle_id]["result_digest"] for battle_id in sorted(validated)},
            "replay_sha256": {battle_id: validated[battle_id]["source"]["replay_sha256"] for battle_id in sorted(validated)},
            "dual_replay_calibration_digest": dual["result_digest"],
            "chaos_replay_calibration_digest": chaos["result_digest"],
        },
        "identity_provenance_boundary": {
            "runtime_identity_field_is_authoritative_for_runtime_source": True,
            "display_identity_may_differ": True,
            "silent_identity_reconciliation_prohibited": True,
            "known_runtime_identity_alias_cohort": ["ubersreik", "marienburg", "chaos"],
            "interpretation": "The repeated Battle of Eilhart runtime battlefield identity is preserved because v0.2A/v0.2C source evidence explicitly binds different replay/display identities. This is provenance, not a claim that those battles were Eilhart.",
        },
        "battle_summaries": battle_summaries,
        "benchmark_dimensions": [
            "outcome_status",
            "outcome_grade_when_observed",
            "local_casualty_lower_bound",
            "role_specific_loss",
            "commander_crisis",
            "force_discovery",
            "reserve_state",
            "terminal_discipline",
            "identity_provenance",
            "command_churn_reference_only",
        ],
        "policy_rules": policy_rules,
        "generalization_limits": [
            "All four dense corpora are ordinary land-battle replays.",
            "The SFO calibration cohort is Reikland-only and contains two naturally completed victories plus one nonterminal Chaos divergence trace.",
            "The vanilla Eilhart replay is a single battle and cannot establish cross-faction or SFO behavior.",
            "No source proves project command acknowledgement, command execution causality, route completion, formation feasibility, line of fire, or tactical optimality.",
            "No policy threshold in this envelope is faction-general, siege-general, ambush-general, multiplayer-safe, or a learned causal effect.",
            "Owner command traces are observational references and never training truth for required command frequency.",
        ],
        "rejected_promotions": [
            "No observed command event is promoted to project issue, acceptance, acknowledgement, or causal execution.",
            "No nonterminal Chaos observation is promoted to a replayed defeat or terminal grade.",
            "No owner action sequence is promoted to optimal policy.",
            "No policy rule may consume hidden enemy identity or state.",
            "No runtime or order adapter is introduced by this offline policy layer.",
        ],
    }
    output["result_digest"] = digest(output)
    return output


def validate_cross_corpus_policy_envelope(value: dict[str, Any]) -> dict[str, Any]:
    result = _validate_result_digest(value, contract=POLICY_CONTRACT)
    _require(result.get("schema_version") == 1, "policy schema_version must be 1")
    _require(result.get("authority") == "NO_ORDERS", "policy authority must remain NO_ORDERS")
    _require(result.get("application_authority") == "PROHIBITED", "policy application authority must remain PROHIBITED")
    provenance = result.get("source_provenance", {})
    _require(provenance.get("dense_result_digests") == dict(sorted(EXPECTED_DENSE_DIGESTS.items())), "policy dense provenance changed")
    _require(provenance.get("dual_replay_calibration_digest") == EXPECTED_DUAL_CALIBRATION_DIGEST, "policy dual calibration provenance changed")
    _require(provenance.get("chaos_replay_calibration_digest") == EXPECTED_CHAOS_CALIBRATION_DIGEST, "policy Chaos calibration provenance changed")
    summaries = result.get("battle_summaries")
    _require(isinstance(summaries, list) and {item.get("battle_id") for item in summaries} == set(EXPECTED_DENSE_DIGESTS), "policy must preserve exact four battle summaries")
    identity_boundary = result.get("identity_provenance_boundary", {})
    _require(identity_boundary.get("silent_identity_reconciliation_prohibited") is True, "silent identity reconciliation must remain prohibited")
    _require(identity_boundary.get("known_runtime_identity_alias_cohort") == ["ubersreik", "marienburg", "chaos"], "known runtime-identity alias cohort changed")
    rules = result.get("policy_rules")
    _require(isinstance(rules, list) and len(rules) >= 9, "policy rule set is incomplete")
    ids = [item.get("rule_id") for item in rules]
    _require(len(ids) == len(set(ids)), "duplicate policy rule id")
    # Rejection text is allowed to name forbidden states. Validate executable/status
    # fields rather than flagging literals that document what the policy forbids.
    _require(all(item.get("authority") in {"NO_ORDERS", "ADVISORY_ONLY"} for item in rules), "policy rule authority promotion is prohibited")
    prohibited_status_fields = {"project_issue_status", "execution_status", "direct_acknowledgement_status", "causal_execution_status"}
    _require(not any(field in result for field in prohibited_status_fields), "runtime execution status fields do not belong in the offline policy envelope")
    return result


def _validate_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    _require(isinstance(snapshot, dict), "policy snapshot must be an object")
    _walk_private(snapshot)
    _require(snapshot.get("schema_version") == 1, "snapshot schema_version must be 1")
    _require(snapshot.get("authority") == "NO_ORDERS", "snapshot authority must remain NO_ORDERS")
    _require(snapshot.get("evidence_status") in {"CONTROL_SYNTHETIC", "OBSERVED"}, "snapshot evidence status is unsupported")
    _require(isinstance(snapshot.get("snapshot_id"), str) and snapshot["snapshot_id"], "snapshot_id is required")
    _require(snapshot.get("reserve_state") in _ALLOWED_RESERVE_STATES, "reserve_state is invalid")
    _require(isinstance(snapshot.get("force_discovery_complete"), bool), "force_discovery_complete must be boolean")
    _require(isinstance(snapshot.get("natural_completion_observed"), bool), "natural_completion_observed must be boolean")
    _require(isinstance(snapshot.get("outcome_decided_observed"), bool), "outcome_decided_observed must be boolean")
    _require(not snapshot["outcome_decided_observed"] or snapshot["natural_completion_observed"], "outcome_decided requires natural completion in this policy snapshot")
    _require(isinstance(snapshot.get("observation_stale"), bool), "observation_stale must be boolean")
    concentration = snapshot.get("target_concentration_share")
    _require(concentration is None or (_is_number(concentration) and 0.0 <= float(concentration) <= 1.0), "target concentration must be null or [0,1]")
    _require(isinstance(snapshot.get("selection_attribution_observed"), bool), "selection_attribution_observed must be boolean")
    assets = snapshot.get("local_assets")
    _require(isinstance(assets, list), "local_assets must be a list")
    seen: set[str] = set()
    for asset in assets:
        _require(isinstance(asset, dict), "asset must be an object")
        asset_id = asset.get("asset_id")
        _require(isinstance(asset_id, str) and asset_id and asset_id not in seen, "asset ids must be unique")
        seen.add(asset_id)
        initial = asset.get("initial_models")
        casualties = asset.get("casualties_observed_lower_bound")
        _require(isinstance(initial, int) and not isinstance(initial, bool) and initial >= 1, "asset initial_models must be positive integer")
        _require(isinstance(casualties, int) and not isinstance(casualties, bool) and 0 <= casualties <= initial, "asset casualties are invalid")
        _require(isinstance(asset.get("high_value"), bool), "asset high_value must be boolean")
        _require(isinstance(asset.get("commander"), bool), "asset commander must be boolean")
        _require(isinstance(asset.get("routing"), bool), "asset routing must be boolean")
        hp = asset.get("hitpoints_fraction")
        _require(hp is None or (_is_number(hp) and 0.0 <= float(hp) <= 1.0), "asset hitpoints_fraction is invalid")
    return copy.deepcopy(snapshot)


def _review(
    review_id: str,
    priority: int,
    status: str,
    basis: str,
    asset_id: str | None = None,
) -> dict[str, Any]:
    result = {
        "review_id": review_id,
        "priority": priority,
        "status": status,
        "basis": basis,
        "authority": "ADVISORY_ONLY",
        "application_status": "PROHIBITED_NO_ORDER_AUTHORITY",
        "project_issue_status": "NOT_ATTEMPTED",
        "execution_status": "NOT_ISSUED",
        "causal_outcome_status": "UNVERIFIED",
    }
    if asset_id is not None:
        result["asset_id"] = asset_id
    return result


def evaluate_tactical_policy(policy_value: dict[str, Any], snapshot_value: dict[str, Any]) -> dict[str, Any]:
    policy = validate_cross_corpus_policy_envelope(policy_value)
    snapshot = _validate_snapshot(snapshot_value)
    severe_rule = next(item for item in policy["policy_rules"] if item["rule_id"] == "severe_asset_loss_ratio_guard")
    severe_threshold = float(severe_rule["severe_loss_ratio_threshold"])

    reviews: list[dict[str, Any]] = []
    abstentions: list[str] = []
    local_crisis = False

    if snapshot["observation_stale"]:
        abstentions.append("STALE_OBSERVATION_NO_TACTICAL_COMMITMENT_REVIEW")
    else:
        for asset in sorted(snapshot["local_assets"], key=lambda item: item["asset_id"]):
            loss_ratio = asset["casualties_observed_lower_bound"] / asset["initial_models"]
            hp = asset.get("hitpoints_fraction")
            commander_crisis = asset["commander"] and (asset["routing"] or (hp is not None and float(hp) < 0.25))
            severe_high_value = asset["high_value"] and loss_ratio >= severe_threshold
            if commander_crisis:
                local_crisis = True
                reviews.append(_review("COMMANDER_PRESERVATION_REVIEW", 0, "SUPPORTED_REVIEW", "commander routing or low observed hitpoints", asset["asset_id"]))
            if severe_high_value:
                local_crisis = True
                reviews.append(_review("HIGH_VALUE_ASSET_PRESERVATION_REVIEW", 1, "SUPPORTED_REVIEW", f"observed loss lower-bound ratio {loss_ratio:.6f} >= {severe_threshold:.6f}", asset["asset_id"]))

        if not snapshot["force_discovery_complete"]:
            reviews.append(_review("FORCE_COMPLETENESS_REVIEW", 3, "SUPPORTED_REVIEW", "local force discovery is incomplete"))

        reserve_state = snapshot["reserve_state"]
        if reserve_state in {"COMMITTED_LATE", "UNABLE_TO_SUPPORT"}:
            reviews.append(_review("RESERVE_STATE_REVIEW", 2, "SUPPORTED_BOUNDED_REVIEW", f"reserve state is {reserve_state}"))
        elif reserve_state == "UNKNOWN":
            abstentions.append("RESERVE_STATE_UNKNOWN_DO_NOT_INFER_ABSENCE")

        concentration = snapshot.get("target_concentration_share")
        if concentration is not None and float(concentration) >= 0.30:
            status = "HYPOTHESIS_REVIEW_ONLY" if not snapshot["selection_attribution_observed"] else "SUPPORTED_OBSERVATION_REVIEW"
            reviews.append(_review("TARGET_CONCENTRATION_UTILITY_REVIEW", 5, status, f"targeted command concentration share {float(concentration):.6f}"))

        if snapshot["natural_completion_observed"] and snapshot["outcome_decided_observed"]:
            abstentions.append("NO_NEW_HIGH_COMMITMENT_AFTER_TERMINAL_EVIDENCE")
        elif not snapshot["natural_completion_observed"]:
            abstentions.append("NO_TERMINAL_OUTCOME_LEARNING_FROM_NONTERMINAL_STATE")

    reviews.sort(key=lambda item: (item["priority"], item.get("asset_id", ""), item["review_id"]))
    if local_crisis and snapshot["natural_completion_observed"]:
        ordering = "PRESERVATION_FIRST_EVEN_WITH_TERMINAL_EVIDENCE"
    elif local_crisis:
        ordering = "PRESERVATION_FIRST_LOCAL_CRISIS"
    elif snapshot["natural_completion_observed"]:
        ordering = "TERMINAL_DISCIPLINE_FIRST"
    elif snapshot["observation_stale"]:
        ordering = "ABSTAIN_STALE_OBSERVATION"
    else:
        ordering = "NO_LOCAL_CRISIS_DETECTED"

    output: dict[str, Any] = {
        "schema_version": 1,
        "contract": EVALUATION_CONTRACT,
        "source_policy_digest": policy["result_digest"],
        "snapshot_id": snapshot["snapshot_id"],
        "authority": "NO_ORDERS",
        "application_authority": "PROHIBITED",
        "evidence_status": snapshot["evidence_status"],
        "local_crisis_detected": local_crisis,
        "priority_ordering": ordering,
        "review_count": len(reviews),
        "reviews": reviews,
        "abstentions": sorted(set(abstentions)),
        "terminal_outcome_label": "OBSERVED_TERMINAL_BOUNDARY" if snapshot["natural_completion_observed"] else "UNVERIFIED_NONTERMINAL",
        "project_orders_emitted": False,
        "direct_acknowledgement_claimed": False,
        "causal_execution_claimed": False,
    }
    output["result_digest"] = digest(output)
    return output
