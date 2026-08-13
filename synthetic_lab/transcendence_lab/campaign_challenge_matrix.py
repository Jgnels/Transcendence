from __future__ import annotations

from copy import deepcopy
from typing import Any

from .campaign_challenge import evaluate_campaign_snapshot, semantic_snapshot_metrics
from .canonical import digest
from .contracts import ContractError

CONTRACT = "CAMPAIGN_STRATEGIC_CHALLENGE_ADVERSARIAL_MATRIX_V1"


class CampaignChallengeMatrixError(ValueError):
    pass


def _translate(scenario: dict[str, Any], dx: float, dy: float) -> dict[str, Any]:
    out = deepcopy(scenario)
    for group in ("armies", "regions"):
        for item in out[group]:
            item["x"] = float(item["x"]) + dx
            item["y"] = float(item["y"]) + dy
    out["scenario_id"] = f"{out['scenario_id']}:translated"
    return out


def _scale_strength(scenario: dict[str, Any], factor: float) -> dict[str, Any]:
    out = deepcopy(scenario)
    for army in out["armies"]:
        army["strength"] = float(army["strength"]) * factor
    for region in out["regions"]:
        region["garrison_strength"] = float(region["garrison_strength"]) * factor
    out["scenario_id"] = f"{out['scenario_id']}:scaled"
    return out


def _reverse_input(scenario: dict[str, Any]) -> dict[str, Any]:
    out = deepcopy(scenario)
    out["armies"] = list(reversed(out["armies"]))
    out["regions"] = list(reversed(out["regions"]))
    out["wars"] = [list(reversed(war)) for war in reversed(out["wars"])]
    out["scenario_id"] = f"{out['scenario_id']}:reversed"
    return out


def _rename_factions(scenario: dict[str, Any], mapping: dict[str, str]) -> dict[str, Any]:
    out = deepcopy(scenario)
    out["controlled_faction"] = mapping.get(out["controlled_faction"], out["controlled_faction"])
    for army in out["armies"]:
        army["faction"] = mapping.get(army["faction"], army["faction"])
        army["visible_to"] = [mapping.get(value, value) for value in army.get("visible_to", [])]
    for region in out["regions"]:
        region["owner"] = mapping.get(region["owner"], region["owner"])
    out["wars"] = [[mapping.get(a, a), mapping.get(b, b)] for a, b in out["wars"]]
    out["scenario_id"] = f"{out['scenario_id']}:renamed"
    return out


def _add_hidden_enemy(scenario: dict[str, Any]) -> dict[str, Any]:
    out = deepcopy(scenario)
    enemy = next((b if a == out["controlled_faction"] else a for a, b in out["wars"] if a == out["controlled_faction"] or b == out["controlled_faction"]), "hidden_enemy")
    out["armies"].append(
        {
            "id": "hidden_adversarial_army",
            "faction": enemy,
            "strength": 99999.0,
            "x": out["regions"][0]["x"],
            "y": out["regions"][0]["y"],
            "movement": 99.0,
            "replenishment": 1.0,
            "visible_to": [],
        }
    )
    out["scenario_id"] = f"{out['scenario_id']}:hidden"
    return out


def _expect(case: dict[str, Any], result: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected = case.get("expected", {})
    for key in ("rival_structure", "pressure_class"):
        if key in expected and result.get(key) != expected[key]:
            errors.append(f"{key}: expected {expected[key]!r}, got {result.get(key)!r}")
    metrics = expected.get("metrics", {})
    for key, value in metrics.items():
        if result["metrics"].get(key) != value:
            errors.append(f"metrics.{key}: expected {value!r}, got {result['metrics'].get(key)!r}")
    if expected.get("no_hidden_consumption") is True and result["visibility_policy"]["hidden_enemy_armies_consumed"] is not False:
        errors.append("hidden enemy consumption was not false")
    if expected.get("no_human_identity") is True and result["visibility_policy"]["human_or_player_identity_consumed"] is not False:
        errors.append("human/player identity consumption was not false")
    return errors


def run_campaign_challenge_matrix(suite: dict[str, Any]) -> dict[str, Any]:
    if suite.get("schema_version") != 1 or suite.get("suite_id") != "campaign_challenge_adversarial_matrix_v0.2E":
        raise CampaignChallengeMatrixError("unexpected campaign challenge suite identity")
    cases = suite.get("cases")
    if not isinstance(cases, list) or not cases:
        raise CampaignChallengeMatrixError("campaign challenge suite cases missing")

    records: list[dict[str, Any]] = []
    for case in cases:
        scenario = case.get("scenario")
        if not isinstance(scenario, dict):
            raise CampaignChallengeMatrixError("case scenario missing")
        try:
            result = evaluate_campaign_snapshot(scenario)
            errors = _expect(case, result)
            passed = not errors
            records.append(
                {
                    "case_id": case["case_id"],
                    "passed": passed,
                    "errors": errors,
                    "result_digest": result["result_digest"],
                    "semantic_metrics": semantic_snapshot_metrics(result),
                }
            )
        except (ContractError, ValueError) as error:
            expect_error = case.get("expect_error")
            passed = bool(expect_error and expect_error in str(error))
            records.append(
                {
                    "case_id": case["case_id"],
                    "passed": passed,
                    "errors": [] if passed else [str(error)],
                    "result_digest": None,
                    "semantic_metrics": None,
                }
            )

    base = suite["metamorphic_base"]
    base_result = evaluate_campaign_snapshot(base)
    baseline_semantics = semantic_snapshot_metrics(base_result)
    metamorphic: list[dict[str, Any]] = []
    transforms = [
        ("input_order", _reverse_input(base)),
        ("coordinate_translation", _translate(base, 1000.0, -750.0)),
        ("uniform_strength_scale", _scale_strength(base, 10.0)),
        ("hidden_enemy_injection", _add_hidden_enemy(base)),
    ]
    for name, scenario in transforms:
        result = evaluate_campaign_snapshot(scenario)
        semantics = semantic_snapshot_metrics(result)
        metamorphic.append(
            {
                "check_id": name,
                "passed": semantics == baseline_semantics,
                "semantic_digest": digest(semantics),
            }
        )

    renamed = _rename_factions(base, {"player_empire": "npc_empire"})
    renamed_result = evaluate_campaign_snapshot(renamed)
    renamed_semantics = semantic_snapshot_metrics(renamed_result)
    # Faction IDs are deliberately excluded from semantic metrics. This is the
    # benchmark's player-label invariance check, not a runtime claim about CAI.
    metamorphic.append(
        {
            "check_id": "player_label_to_npc_label",
            "passed": renamed_semantics == baseline_semantics,
            "semantic_digest": digest(renamed_semantics),
        }
    )

    result = {
        "schema_version": 1,
        "contract": CONTRACT,
        "suite_id": suite["suite_id"],
        "authority": "NO_ORDERS",
        "application_authority": "PROHIBITED",
        "case_count": len(records),
        "passed_case_count": sum(1 for record in records if record["passed"]),
        "cases": records,
        "metamorphic_check_count": len(metamorphic),
        "metamorphic_pass_count": sum(1 for record in metamorphic if record["passed"]),
        "metamorphic_checks": metamorphic,
        "result": "PASS" if all(record["passed"] for record in records + metamorphic) else "FAIL",
    }
    result["result_digest"] = digest(result)
    return result
