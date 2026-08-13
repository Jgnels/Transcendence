from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

CONTRACT = "NATIVE_CAI_DIRECTIONAL_CHURN_VANILLA_SFO_COMPARISON_V1"


class NativeChurnComparisonError(ValueError):
    pass


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise NativeChurnComparisonError(f"{path} must contain an object")
    return value


def _metrics(capture: dict[str, Any]) -> dict[str, Any]:
    batch = capture.get("churn_batch")
    if not isinstance(batch, dict):
        raise NativeChurnComparisonError("capture is missing churn_batch")
    metrics = batch.get("aggregate_metrics")
    if not isinstance(metrics, dict):
        raise NativeChurnComparisonError("capture is missing aggregate churn metrics")
    return metrics


def build_comparison(
    *,
    vanilla_capture: dict[str, Any],
    vanilla_binding: dict[str, Any],
    sfo_capture: dict[str, Any],
    sfo_binding: dict[str, Any],
) -> dict[str, Any]:
    pairs = [
        ("VANILLA", vanilla_capture, vanilla_binding),
        ("SFO", sfo_capture, sfo_binding),
    ]
    for expected, capture, binding in pairs:
        if capture.get("contract") != "NATIVE_CAI_DIRECTIONAL_CHURN_CAPTURE_VERIFICATION_V1":
            raise NativeChurnComparisonError(f"{expected} capture contract mismatch")
        if binding.get("contract") != "NATIVE_CAI_CHURN_PROFILE_BINDING_V1":
            raise NativeChurnComparisonError(f"{expected} binding contract mismatch")
        if capture.get("profile") != expected or binding.get("profile") != expected:
            raise NativeChurnComparisonError(f"{expected} profile mismatch")
        if capture.get("profile_binding_sha256") != binding.get("binding_sha256"):
            raise NativeChurnComparisonError(f"{expected} capture/binding digest mismatch")
        if capture.get("authority") != "NO_ORDERS" or capture.get("application_authority") != "PROHIBITED":
            raise NativeChurnComparisonError(f"{expected} authority mismatch")
        if capture.get("campaign_checks", {}).get("owner_action_protocol") != "OWNER_ATTESTED_PASSIVE_NO_VOLUNTARY_CAMPAIGN_ORDERS":
            raise NativeChurnComparisonError(f"{expected} owner action protocol is not confirmatory")

    vanilla_protocol = vanilla_binding.get("campaign_protocol")
    sfo_protocol = sfo_binding.get("campaign_protocol")
    if vanilla_protocol != sfo_protocol:
        raise NativeChurnComparisonError(
            f"campaign protocols differ across profiles: vanilla={vanilla_protocol!r}, sfo={sfo_protocol!r}"
        )
    vanilla_min = vanilla_capture.get("campaign_checks", {}).get("minimum_turns")
    sfo_min = sfo_capture.get("campaign_checks", {}).get("minimum_turns")
    if vanilla_min != sfo_min:
        raise NativeChurnComparisonError("minimum turn requirements differ across profiles")

    vm = _metrics(vanilla_capture)
    sm = _metrics(sfo_capture)
    def row(metrics: dict[str, Any]) -> dict[str, Any]:
        return {
            "eligible_stable_context_region_windows": int(metrics.get("eligible_stable_context_region_windows", 0)),
            "oscillation_candidate_count": int(metrics.get("oscillation_candidate_count", 0)),
            "repeated_oscillation_cluster_count": int(metrics.get("repeated_oscillation_cluster_count", 0)),
            "candidate_rate_per_eligible_window": metrics.get("candidate_rate_per_eligible_window"),
        }

    profiles = {"VANILLA": row(vm), "SFO": row(sm)}
    result: dict[str, Any] = {
        "contract": CONTRACT,
        "authority": "NO_ORDERS",
        "application_authority": "PROHIBITED",
        "campaign_protocol": vanilla_protocol,
        "minimum_turns_per_run": vanilla_min,
        "profiles": profiles,
        "comparison_status": "DESCRIPTIVE_ONLY_NO_CAUSAL_OR_SIGNIFICANCE_CLAIM",
        "interpretation": [
            "Different eligible-window exposure is reported rather than normalized away.",
            "A lower candidate/cluster count in SFO does not by itself prove an SFO causal fix because the campaigns are stochastic and unmatched at hidden state.",
            "A profile difference may nominate a bounded native-row treatment for a later preregistered ablation.",
            "No comparison result can directly authorize v0.2G/v0.2I or another project-owned strategic planner.",
        ],
    }
    result["result_digest"] = hashlib.sha256(
        json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare profile-bound vanilla and SFO v0.2L native churn captures descriptively.")
    parser.add_argument("--vanilla-capture", type=Path, required=True)
    parser.add_argument("--vanilla-binding", type=Path, required=True)
    parser.add_argument("--sfo-capture", type=Path, required=True)
    parser.add_argument("--sfo-binding", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build_comparison(
        vanilla_capture=_load(args.vanilla_capture),
        vanilla_binding=_load(args.vanilla_binding),
        sfo_capture=_load(args.sfo_capture),
        sfo_binding=_load(args.sfo_binding),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
