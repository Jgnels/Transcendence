from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
PRIVATE_PATH_RE = re.compile(r"(?:[A-Za-z]:[\\/]|/home/|/Users/|\\\\)")


class SfoObservedBaselineError(ValueError):
    pass


def canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and bool(SHA256_RE.fullmatch(value.lower()))


def _walk_public(value: object, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = str(key).lower()
            if lowered in {
                "private_path",
                "absolute_path",
                "repository_path",
                "runtime_log_path",
                "checkpoint_root_private_path",
                "log_private_path",
            }:
                raise SfoObservedBaselineError(f"private path field is prohibited: {path}.{key}")
            _walk_public(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _walk_public(item, f"{path}[{index}]")
    elif isinstance(value, str) and PRIVATE_PATH_RE.search(value):
        raise SfoObservedBaselineError(f"private path-like value is prohibited: {path}")


def validate_sfo_observed_baseline(value: dict[str, Any]) -> dict[str, Any]:
    required = {
        "schema_version",
        "release",
        "fixture_id",
        "evidence_status",
        "fidelity_label",
        "source",
        "environment",
        "campaign",
        "continuity",
        "aggregate_metrics",
        "battles",
        "authority",
        "promoted_capabilities",
        "forbidden_inferences",
        "result_digest",
    }
    missing = sorted(required - value.keys())
    if missing:
        raise SfoObservedBaselineError(f"baseline fixture is missing fields: {missing}")
    if value["schema_version"] != 1:
        raise SfoObservedBaselineError("unsupported SFO observed baseline schema")
    if value["release"] != "v0.1Z":
        raise SfoObservedBaselineError("unexpected release label")
    if value["evidence_status"] != "OBSERVED_SFO_COMBINED_CONTINUITY":
        raise SfoObservedBaselineError("baseline must remain observed SFO combined continuity")

    source = value["source"]
    for key in (
        "rescue_zip_sha256",
        "private_raw_log_sha256",
        "recovered_public_bundle_sha256",
        "campaign_summary_result_digest",
        "campaign_battle_result_digest",
        "sfo_combined_result_digest",
    ):
        if not _is_sha256(source.get(key)):
            raise SfoObservedBaselineError(f"invalid source digest: {key}")
    if source.get("private_raw_log_committed") is not False:
        raise SfoObservedBaselineError("private raw log must not be committed")
    if source.get("private_raw_log_size_bytes") != 24_658_918:
        raise SfoObservedBaselineError("unexpected recovered raw-log size")

    environment = value["environment"]
    for key in ("wh3_executable_sha256", "sfo_pack_sha256", "shadow_probe_sha256"):
        if not _is_sha256(environment.get(key)):
            raise SfoObservedBaselineError(f"invalid environment digest: {key}")
    if environment.get("sfo_workshop_id") != "2792731173":
        raise SfoObservedBaselineError("unexpected SFO Workshop identity")
    if environment.get("load_order") != [
        "sfo_grimhammer_3_main.pack",
        "transcendence_shadow_probe.pack",
    ]:
        raise SfoObservedBaselineError("exact two-pack load order changed")

    campaign = value["campaign"]
    if campaign.get("turns") != [1, 2, 3, 4, 5, 6] or campaign.get("turn_count") != 6:
        raise SfoObservedBaselineError("observed consecutive campaign-turn cohort changed")
    if campaign.get("capability_failures") != []:
        raise SfoObservedBaselineError("campaign capability failures must remain empty")

    continuity = value["continuity"]
    expected_continuity = {
        "battle_runtime_count": 3,
        "completed_battle_count": 3,
        "campaign_return_after_each_battle": [True, True, True],
        "checkpoint_count": 130,
        "checkpoint_prefix_chain_valid": True,
        "final_checkpoint_matches_raw_log": True,
        "checkpoint_reported_violations": [],
    }
    for key, expected in expected_continuity.items():
        if continuity.get(key) != expected:
            raise SfoObservedBaselineError(f"continuity regression: {key}")

    aggregate = value["aggregate_metrics"]
    expected_aggregate = {
        "battle_detail_samples": 698,
        "battle_aggregate_samples": 2072,
        "battle_command_events": 683,
        "selection_events": 1025,
        "canonical_unit_static_records": 80,
    }
    for key, expected in expected_aggregate.items():
        if aggregate.get(key) != expected:
            raise SfoObservedBaselineError(f"aggregate metric regression: {key}")

    battles = value["battles"]
    if not isinstance(battles, list) or len(battles) != 3:
        raise SfoObservedBaselineError("exactly three observed battles are required")
    if [battle.get("battle_index") for battle in battles] != [1, 2, 3]:
        raise SfoObservedBaselineError("battle order changed")
    if any(battle.get("source_schema") != 2 for battle in battles):
        raise SfoObservedBaselineError("all observed battles must use schema 2")
    if any(battle.get("metadata", {}).get("battle_type") != "land_normal" for battle in battles):
        raise SfoObservedBaselineError("baseline contains an unobserved battle type")
    if any(battle.get("metadata", {}).get("from_campaign") != "true" for battle in battles):
        raise SfoObservedBaselineError("baseline battle is not campaign-derived")
    if any(battle.get("complete") is not True for battle in battles):
        raise SfoObservedBaselineError("baseline contains an incomplete battle")
    if any(battle.get("capability_failures") != [] for battle in battles):
        raise SfoObservedBaselineError("battle capability failures must remain empty")
    if any(battle.get("sampling", {}).get("time_series_metrics_valid") is not True for battle in battles):
        raise SfoObservedBaselineError("dense time-series validity regressed")
    if any(battle.get("authority", {}).get("orders_emitted") is not False for battle in battles):
        raise SfoObservedBaselineError("observed fixture cannot claim project-issued orders")

    authority = value["authority"]
    if any(authority.get(key) is not False for key in (
        "active_mod_list_modified_by_collector",
        "battle_orders_emitted",
        "campaign_orders_emitted",
        "save_values_written",
        "unitcontrollers_created",
    )):
        raise SfoObservedBaselineError("authority boundary regressed")

    _walk_public(value)
    body = dict(value)
    digest = body.pop("result_digest")
    expected_digest = hashlib.sha256(canonical_json(body)).hexdigest()
    if digest != expected_digest:
        raise SfoObservedBaselineError("baseline result digest mismatch")
    return value


def build_capability_matrix(value: dict[str, Any]) -> dict[str, Any]:
    value = validate_sfo_observed_baseline(value)
    matrix = {
        "schema_version": 1,
        "source_fixture_id": value["fixture_id"],
        "source_fixture_digest": value["result_digest"],
        "capabilities": {
            "exact_sfo_environment_identity": "OBSERVED",
            "sfo_campaign_observation": "OBSERVED",
            "sfo_ordinary_land_battle_observation": "OBSERVED",
            "campaign_battle_campaign_append_continuity": "OBSERVED",
            "schema2_dense_battle_time_series": "OBSERVED",
            "selection_event_observation": "OBSERVED",
            "command_event_observation": "OBSERVED_NOT_ACKNOWLEDGED",
            "order_acknowledgement": "UNOBSERVED",
            "order_execution_causality": "UNOBSERVED",
            "tactical_superiority": "UNPROVEN",
            "sfo_siege_coverage": "UNOBSERVED",
            "sfo_ambush_coverage": "UNOBSERVED",
            "sfo_reinforcement_coverage": "UNOBSERVED",
            "broad_faction_coverage": "UNOBSERVED",
            "full_mod_stack_compatibility": "UNOBSERVED",
        },
        "scope": {
            "campaign_turns": value["campaign"]["turn_count"],
            "completed_battles": value["continuity"]["completed_battle_count"],
            "battle_types": sorted({battle["metadata"]["battle_type"] for battle in value["battles"]}),
            "faction": value["environment"]["settings"]["faction"],
        },
        "forbidden_inferences": list(value["forbidden_inferences"]),
    }
    matrix["result_digest"] = hashlib.sha256(canonical_json(matrix)).hexdigest()
    return matrix


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the frozen v0.1Z SFO owner-machine baseline.")
    parser.add_argument("fixture", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    value = json.loads(args.fixture.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise SfoObservedBaselineError("fixture must be a JSON object")
    matrix = build_capability_matrix(value)
    payload = json.dumps(matrix, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
