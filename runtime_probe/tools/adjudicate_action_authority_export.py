from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

EXPECTED_MEMBERS_V1 = {
    "action_authority_summary.json",
    "action_authority_verification.json",
    "public_capture_manifest.json",
}
EXPECTED_MEMBERS_V2 = EXPECTED_MEMBERS_V1 | {"public_preparation_attestation.json"}
EXPECTED_PACK_SHA256 = "3acf60520b60f87f8c18e13532512324cb7a539626996ce19897fad94cf2d25d"
ALLOWED_CLOSE_REASONS = {
    "CONTROL_LOST",
    "ROUTED",
    "SHATTERED",
    "SUBSEQUENT_COMMAND",
    "TERMINAL",
    "UNBOUND_SELECTION",
    "WINDOW_TIMEOUT",
}
ALLOWED_REACHABILITY = {"QUERY_TRUE", "QUERY_FALSE", "UNAVAILABLE", "NOT_APPLICABLE"}
ALLOWED_STATE_MATCHES = {
    "control_lost_observed",
    "current_target_match",
    "leaving_battle_observed",
    "movement_observed",
    "ordered_position_match",
    "routing_observed",
    "shattered_observed",
}


class ActionAuthorityExportError(ValueError):
    pass


def _canonical_json(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def _sha256(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def _require_dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ActionAuthorityExportError(f"{label} must be an object")
    return value


def _require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ActionAuthorityExportError(f"{label} must be a list")
    return value


def _require_bool(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise ActionAuthorityExportError(f"{label} must be a boolean")
    return value


def _require_int(value: Any, label: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ActionAuthorityExportError(f"{label} must be an integer >= {minimum}")
    return value


def _require_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ActionAuthorityExportError(f"{label} must be non-empty text")
    return value


def _require_sha(value: Any, label: str) -> str:
    value = _require_text(value, label)
    if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise ActionAuthorityExportError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _require_count_map(
    value: Any,
    label: str,
    allowed: set[str],
) -> dict[str, int]:
    raw = _require_dict(value, label)
    if set(raw) != allowed:
        missing = sorted(allowed - set(raw))
        extra = sorted(set(raw) - allowed)
        raise ActionAuthorityExportError(
            f"{label} keys mismatch; missing={missing}, extra={extra}"
        )
    return {
        key: _require_int(raw[key], f"{label}.{key}")
        for key in sorted(allowed)
    }


def _rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 6)


def _validate_timestamp(value: Any, label: str) -> str:
    text = _require_text(value, label)
    try:
        datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as error:
        raise ActionAuthorityExportError(f"{label} is not an ISO-8601 timestamp") from error
    return text


def _decode_json(blob: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(blob.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ActionAuthorityExportError(f"{label} is not valid UTF-8 JSON") from error
    return _require_dict(value, label)


def _verification_digest(verification: Mapping[str, Any]) -> str:
    material = dict(verification)
    claimed = material.pop("result_digest", None)
    if claimed is None:
        raise ActionAuthorityExportError("verification result_digest is missing")
    return _sha256(_canonical_json(material))


def _validate_preparation_attestation(
    attestation: dict[str, Any] | None,
    manifest: dict[str, Any],
    expected_pack_sha256: str,
) -> str:
    if attestation is None:
        return "NOT_PUBLIC_IN_SCHEMA_V1"
    if attestation.get("schema_version") != 1:
        raise ActionAuthorityExportError("unsupported preparation attestation schema")
    if attestation.get("capture_kind") != "action_authority":
        raise ActionAuthorityExportError("preparation attestation has wrong capture kind")
    _validate_timestamp(attestation.get("prepared_at_utc"), "prepared_at_utc")
    if attestation.get("pack_name") != "transcendence_action_authority_probe.pack":
        raise ActionAuthorityExportError("preparation attestation has wrong pack name")
    staged = _require_sha(attestation.get("staged_pack_sha256"), "attested staged pack SHA-256")
    installed = _require_sha(attestation.get("installed_pack_sha256"), "attested installed pack SHA-256")
    if staged != expected_pack_sha256 or installed != expected_pack_sha256:
        raise ActionAuthorityExportError("preparation attestation pack mismatch")
    required_false = {
        "active_mod_list_modified": False,
        "wh3_save_modified": False,
        "project_orders_enabled": False,
    }
    for key, expected in required_false.items():
        if _require_bool(attestation.get(key), key) is not expected:
            raise ActionAuthorityExportError(f"preparation attestation {key} must be false")
    if _require_bool(attestation.get("runtime_log_cleared"), "runtime_log_cleared") is not True:
        raise ActionAuthorityExportError("preparation attestation must record a cleared runtime log")
    _require_sha(
        manifest.get("preparation_attestation_sha256"),
        "preparation attestation SHA-256",
    )
    actual = _sha256(_canonical_json(attestation))
    # PowerShell's ConvertTo-Json formatting is not canonical. The manifest binds
    # the exact emitted file bytes; callers using documents directly may supply
    # that digest separately. For a ZIP caller this is checked before decoding.
    if manifest.get("preparation_attestation_canonical_sha256") is not None:
        canonical_claim = _require_sha(
            manifest.get("preparation_attestation_canonical_sha256"),
            "canonical preparation attestation SHA-256",
        )
        if canonical_claim != actual:
            raise ActionAuthorityExportError("canonical preparation attestation hash mismatch")
    return "PUBLIC_SANITIZED_ATTESTATION_VERIFIED"


def adjudicate_action_authority_documents(
    *,
    summary: dict[str, Any],
    verification: dict[str, Any],
    manifest: dict[str, Any],
    source_export_sha256: str,
    expected_pack_sha256: str = EXPECTED_PACK_SHA256,
    preparation_attestation: dict[str, Any] | None = None,
    preparation_attestation_file_sha256: str | None = None,
) -> dict[str, Any]:
    source_export_sha256 = _require_sha(source_export_sha256, "source export SHA-256")
    expected_pack_sha256 = _require_sha(expected_pack_sha256, "expected pack SHA-256")

    manifest_schema = _require_int(manifest.get("schema_version"), "manifest schema", minimum=1)
    if manifest_schema not in {1, 2}:
        raise ActionAuthorityExportError("unsupported public manifest schema")
    if manifest.get("capture_kind") != "action_authority":
        raise ActionAuthorityExportError("public manifest has wrong capture kind")
    _validate_timestamp(manifest.get("collected_at_utc"), "collected_at_utc")
    if manifest.get("authority") != "NO_ORDERS":
        raise ActionAuthorityExportError("public manifest authority must remain NO_ORDERS")
    if _require_bool(manifest.get("raw_log_included_in_export"), "raw_log_included_in_export"):
        raise ActionAuthorityExportError("public export must not contain the raw log")
    _require_sha(manifest.get("raw_log_sha256"), "raw log SHA-256")
    _require_int(manifest.get("raw_log_size_bytes"), "raw log size", minimum=1)
    _require_sha(manifest.get("prepared_manifest_sha256"), "prepared manifest SHA-256")
    installed_pack = _require_sha(manifest.get("installed_pack_sha256"), "installed pack SHA-256")
    if installed_pack != expected_pack_sha256:
        raise ActionAuthorityExportError("public manifest pack does not match the pinned probe")
    if _require_int(manifest.get("project_issue_attempt_count"), "manifest issue attempts") != 0:
        raise ActionAuthorityExportError("public manifest may not claim project issue attempts")
    if _require_int(manifest.get("direct_acknowledgement_count"), "manifest acknowledgements") != 0:
        raise ActionAuthorityExportError("public manifest may not claim acknowledgements")

    if summary.get("schema_version") != 1 or summary.get("authority") != "NO_ORDERS":
        raise ActionAuthorityExportError("summary is not a schema-1 NO_ORDERS document")
    sessions = _require_list(summary.get("sessions"), "summary.sessions")
    if len(sessions) != 1:
        raise ActionAuthorityExportError("exactly one action-authority session is required")
    session = _require_dict(sessions[0], "summary.sessions[0]")
    if session.get("complete") is not True:
        raise ActionAuthorityExportError("the action-authority session is incomplete")
    if _require_list(session.get("capability_failures"), "capability_failures"):
        raise ActionAuthorityExportError("required capability failures are present")

    window_count = _require_int(session.get("window_count"), "window_count", minimum=1)
    bound_window_count = _require_int(session.get("bound_window_count"), "bound_window_count")
    unbound_window_count = _require_int(session.get("unbound_window_count"), "unbound_window_count")
    command_event_count = _require_int(session.get("command_event_count"), "command_event_count")
    selection_event_count = _require_int(session.get("selection_event_count"), "selection_event_count")
    sample_count = _require_int(session.get("sample_count"), "sample_count", minimum=1)
    if bound_window_count + unbound_window_count != window_count:
        raise ActionAuthorityExportError("bound and unbound windows do not sum to window_count")
    if command_event_count != window_count:
        raise ActionAuthorityExportError("each observed command must open exactly one window")
    if selection_event_count < bound_window_count:
        raise ActionAuthorityExportError("bound windows exceed observed selection events")
    if _require_int(session.get("project_issue_attempt_count"), "session issue attempts") != 0:
        raise ActionAuthorityExportError("session may not claim project issue attempts")
    if _require_int(session.get("direct_acknowledgement_count"), "session acknowledgements") != 0:
        raise ActionAuthorityExportError("session may not claim acknowledgements")

    reachability = _require_count_map(
        session.get("reachability_counts"),
        "reachability_counts",
        ALLOWED_REACHABILITY,
    )
    if sum(reachability.values()) != sample_count:
        raise ActionAuthorityExportError("reachability counts do not sum to sample_count")
    state_matches = _require_count_map(
        session.get("state_match_counts"),
        "state_match_counts",
        ALLOWED_STATE_MATCHES,
    )
    if any(count > sample_count for count in state_matches.values()):
        raise ActionAuthorityExportError("a state-match count exceeds sample_count")
    close_reasons = _require_count_map(
        session.get("close_reason_counts"),
        "close_reason_counts",
        ALLOWED_CLOSE_REASONS,
    )
    if sum(close_reasons.values()) != window_count:
        raise ActionAuthorityExportError("close-reason counts do not sum to window_count")

    if verification.get("schema_version") != 1:
        raise ActionAuthorityExportError("unsupported verification schema")
    if verification.get("verification_contract") != "ACTION_AUTHORITY_CAPTURE_VERIFICATION_V1":
        raise ActionAuthorityExportError("unexpected verification contract")
    if verification.get("status") != "OBSERVED_READ_ONLY_ACTION_AUTHORITY":
        raise ActionAuthorityExportError("capture verification did not reach OBSERVED status")
    if verification.get("authority") != "NO_ORDERS":
        raise ActionAuthorityExportError("verification authority must remain NO_ORDERS")
    checks = _require_dict(verification.get("checks"), "verification.checks")
    if not checks or any(value is not True for value in checks.values()):
        raise ActionAuthorityExportError("not all capture-verification checks passed")
    if _require_sha(verification.get("expected_pack_sha256"), "verified expected pack") != expected_pack_sha256:
        raise ActionAuthorityExportError("verification expected-pack mismatch")
    if _require_sha(verification.get("prepared_manifest_pack_sha256"), "verified prepared pack") != expected_pack_sha256:
        raise ActionAuthorityExportError("verification prepared-pack mismatch")
    if _require_int(verification.get("project_issue_attempt_count"), "verified issue attempts") != 0:
        raise ActionAuthorityExportError("verification may not claim project issue attempts")
    if _require_int(verification.get("direct_acknowledgement_count"), "verified acknowledgements") != 0:
        raise ActionAuthorityExportError("verification may not claim acknowledgements")
    if verification.get("acknowledgement_claim") != "NOT_ACKNOWLEDGED":
        raise ActionAuthorityExportError("verification acknowledgement claim changed")
    if verification.get("execution_attribution") != "OBSERVED_STATE_ONLY_NOT_CAUSALLY_ATTRIBUTED":
        raise ActionAuthorityExportError("verification execution attribution changed")
    if verification.get("outcome_attribution") != "UNVERIFIED_NOT_ATTRIBUTED":
        raise ActionAuthorityExportError("verification outcome attribution changed")
    claimed_result_digest = _require_sha(verification.get("result_digest"), "verification result digest")
    if _verification_digest(verification) != claimed_result_digest:
        raise ActionAuthorityExportError("verification result digest mismatch")

    # File hashes are validated by the ZIP reader. Document callers additionally
    # bind to the manifest values supplied from the exact capture files.
    _require_sha(manifest.get("summary_sha256"), "summary SHA-256")
    _require_sha(manifest.get("verification_sha256"), "verification SHA-256")

    cross_checks = {
        "window_count": window_count,
        "bound_window_count": bound_window_count,
        "unbound_window_count": unbound_window_count,
        "sample_count": sample_count,
        "reachability_counts": reachability,
        "state_match_counts": state_matches,
        "close_reason_counts": close_reasons,
    }
    for key, expected in cross_checks.items():
        if verification.get(key) != expected:
            raise ActionAuthorityExportError(f"summary/verification mismatch for {key}")

    attestation_status = _validate_preparation_attestation(
        preparation_attestation,
        manifest,
        expected_pack_sha256,
    )
    if preparation_attestation is not None and preparation_attestation_file_sha256 is not None:
        if _require_sha(preparation_attestation_file_sha256, "attestation file SHA-256") != _require_sha(
            manifest.get("preparation_attestation_sha256"),
            "manifest attestation SHA-256",
        ):
            raise ActionAuthorityExportError("preparation attestation file hash mismatch")

    observed_capabilities = {
        "ordinary_battle_local_selection_events": {
            "classification": "OBSERVED",
            "evidence_count": selection_event_count,
        },
        "selected_unit_command_window_binding": {
            "classification": "OBSERVED",
            "bound_windows": bound_window_count,
            "unbound_windows": unbound_window_count,
            "binding_rate": _rate(bound_window_count, window_count),
            "claim_boundary": "SELECTION_BOUND_NOT_COMMAND_ORIGIN_ATTRIBUTED",
        },
        "read_only_action_state_sampling": {
            "classification": "OBSERVED",
            "sample_count": sample_count,
        },
        "point_reachability_query": {
            "classification": "OBSERVED",
            "query_true": reachability["QUERY_TRUE"],
            "query_false": reachability["QUERY_FALSE"],
            "unavailable": reachability["UNAVAILABLE"],
            "claim_boundary": "POINT_IN_TIME_QUERY_NOT_ROUTE_COMPLETION",
        },
        "ordered_position_state_match": {
            "classification": "OBSERVED",
            "evidence_count": state_matches["ordered_position_match"],
            "claim_boundary": "STATE_MATCH_NOT_ACKNOWLEDGEMENT",
        },
        "current_target_state_match": {
            "classification": "OBSERVED",
            "evidence_count": state_matches["current_target_match"],
            "claim_boundary": "STATE_MATCH_NOT_ACKNOWLEDGEMENT",
        },
        "movement_state_visibility": {
            "classification": "OBSERVED",
            "evidence_count": state_matches["movement_observed"],
            "claim_boundary": "OBSERVED_STATE_NOT_CAUSALLY_ATTRIBUTED",
        },
        "routing_state_visibility": {
            "classification": "OBSERVED",
            "evidence_count": state_matches["routing_observed"],
        },
        "control_loss_state_visibility": {
            "classification": "OBSERVED",
            "evidence_count": state_matches["control_lost_observed"],
        },
        "window_interruption_visibility": {
            "classification": "OBSERVED",
            "close_reason_counts": close_reasons,
        },
    }
    if state_matches["leaving_battle_observed"] == 0:
        observed_capabilities["leaving_battle_state_visibility"] = {
            "classification": "UNVERIFIED",
            "evidence_count": 0,
        }
    else:
        observed_capabilities["leaving_battle_state_visibility"] = {
            "classification": "OBSERVED",
            "evidence_count": state_matches["leaving_battle_observed"],
        }
    if state_matches["shattered_observed"] == 0:
        observed_capabilities["shattered_state_visibility"] = {
            "classification": "UNVERIFIED",
            "evidence_count": 0,
        }
    else:
        observed_capabilities["shattered_state_visibility"] = {
            "classification": "OBSERVED",
            "evidence_count": state_matches["shattered_observed"],
        }

    result: dict[str, Any] = {
        "schema_version": 1,
        "adjudication_contract": "ACTION_AUTHORITY_LIVE_ADJUDICATION_V1",
        "status": "OBSERVED_READ_ONLY_ACTION_AUTHORITY_CALIBRATED",
        "authority": "NO_ORDERS",
        "source_export_sha256": source_export_sha256,
        "source_raw_log_sha256": _require_sha(manifest.get("raw_log_sha256"), "raw log SHA-256"),
        "source_raw_log_size_bytes": _require_int(manifest.get("raw_log_size_bytes"), "raw log size", minimum=1),
        "source_raw_log_in_repository": False,
        "source_capture_collected_at_utc": manifest["collected_at_utc"],
        "expected_pack_sha256": expected_pack_sha256,
        "manifest_schema_version": manifest_schema,
        "public_preparation_attestation": attestation_status,
        "session_metrics": {
            "local_unit_count": _require_int(session.get("event_counts", {}).get("UNIT_STATIC"), "local UNIT_STATIC count"),
            "selection_event_count": selection_event_count,
            "command_event_count": command_event_count,
            "window_count": window_count,
            "bound_window_count": bound_window_count,
            "unbound_window_count": unbound_window_count,
            "selection_binding_rate": _rate(bound_window_count, window_count),
            "sample_count": sample_count,
            "samples_per_window": _rate(sample_count, window_count),
            "reachability_counts": reachability,
            "reachability_true_rate": _rate(reachability["QUERY_TRUE"], sample_count),
            "reachability_false_rate": _rate(reachability["QUERY_FALSE"], sample_count),
            "state_match_counts": state_matches,
            "close_reason_counts": close_reasons,
        },
        "capability_adjudications": observed_capabilities,
        "claims_rejected": [
            "Command-window selection binding identifies command origin.",
            "Ordered-position or current-target matching is direct acknowledgement.",
            "Movement after a command proves project-caused execution.",
            "Point reachability proves route completion or formation feasibility.",
            "Observed state change proves an outcome caused by Transcendence.",
        ],
        "limiting_results": [
            "The public schema-1 export omits the prepared-session manifest; its exact preparation checks are preserved through the owner-run verifier output and manifest digest, not independently replayable from the public packet.",
            "The raw log remains private and is not present in the repository, so raw-event reparsing is not independently reproducible from public artifacts.",
            "The capture contains no observed leaving-battle or shattered sample.",
            "No project order was issued, accepted, acknowledged, executed, or credited with an outcome.",
        ],
        "next_gate_boundary": {
            "live_capture_repeat_required": False,
            "safe_next_work": "Use observed query availability to design a read-only feasibility envelope and retain all route, formation, issue, acknowledgement, execution, and outcome claims as UNVERIFIED.",
        },
    }
    result["result_digest"] = _sha256(_canonical_json(result))
    return result


def adjudicate_action_authority_zip(
    path: Path,
    *,
    expected_pack_sha256: str = EXPECTED_PACK_SHA256,
) -> dict[str, Any]:
    blob = path.read_bytes()
    source_export_sha256 = _sha256(blob)
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        if len(names) != len(set(names)):
            raise ActionAuthorityExportError("public export contains duplicate member paths")
        for name in names:
            pure = PurePosixPath(name)
            if pure.is_absolute() or ".." in pure.parts or "\\" in name:
                raise ActionAuthorityExportError(f"unsafe ZIP member path: {name!r}")
            if name.endswith("/"):
                raise ActionAuthorityExportError("public export may not contain directories")
        members = set(names)
        if members == EXPECTED_MEMBERS_V1:
            manifest_schema = 1
        elif members == EXPECTED_MEMBERS_V2:
            manifest_schema = 2
        else:
            raise ActionAuthorityExportError(
                f"unexpected public export members: {sorted(members)}"
            )
        files = {name: archive.read(name) for name in names}

    summary = _decode_json(files["action_authority_summary.json"], "summary")
    verification = _decode_json(files["action_authority_verification.json"], "verification")
    manifest = _decode_json(files["public_capture_manifest.json"], "manifest")
    if manifest.get("schema_version") != manifest_schema:
        raise ActionAuthorityExportError("manifest schema does not match ZIP member set")
    if _sha256(files["action_authority_summary.json"]) != _require_sha(
        manifest.get("summary_sha256"), "summary SHA-256"
    ):
        raise ActionAuthorityExportError("summary file hash mismatch")
    if _sha256(files["action_authority_verification.json"]) != _require_sha(
        manifest.get("verification_sha256"), "verification SHA-256"
    ):
        raise ActionAuthorityExportError("verification file hash mismatch")

    attestation = None
    attestation_hash = None
    if manifest_schema == 2:
        attestation_blob = files["public_preparation_attestation.json"]
        attestation_hash = _sha256(attestation_blob)
        if attestation_hash != _require_sha(
            manifest.get("preparation_attestation_sha256"),
            "preparation attestation SHA-256",
        ):
            raise ActionAuthorityExportError("preparation attestation file hash mismatch")
        attestation = _decode_json(attestation_blob, "preparation attestation")

    return adjudicate_action_authority_documents(
        summary=summary,
        verification=verification,
        manifest=manifest,
        source_export_sha256=source_export_sha256,
        expected_pack_sha256=expected_pack_sha256,
        preparation_attestation=attestation,
        preparation_attestation_file_sha256=attestation_hash,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Adjudicate a public-safe Transcendence action-authority capture ZIP"
    )
    parser.add_argument("capture_zip", type=Path)
    parser.add_argument(
        "--expected-pack-sha256",
        default=EXPECTED_PACK_SHA256,
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = adjudicate_action_authority_zip(
        args.capture_zip,
        expected_pack_sha256=args.expected_pack_sha256,
    )
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
