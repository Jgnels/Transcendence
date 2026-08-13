from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

from export_action_feasibility_windows import EXPORT_CONTRACT, EXPECTED_PACK_SHA256


VERIFICATION_CONTRACT = "ACTION_FEASIBILITY_REEXPORT_VERIFICATION_V1"
EXPECTED_MEMBERS = {
    "action_feasibility_windows.json",
    "public_reexport_manifest.json",
}
EXPECTED_SOURCE_RAW_SHA256 = "b4f8c4ca9c285018772d50a4eda92f34572f742dd97967bca8229b0a6b3ce951"
EXPECTED_SOURCE_PUBLIC_CAPTURE_SHA256 = "a1c03ec12a4c2b70945311fc57b54f978fcca892a37b12d46a5daa6f22ebf579"
REACHABILITY = {"QUERY_TRUE", "QUERY_FALSE", "UNAVAILABLE", "NOT_APPLICABLE"}
PRIVATE_PATTERN = re.compile(r"(?i)([a-z]:\\users\\|steamapps\\common|/home/|/users/)")


class ActionFeasibilityVerificationError(ValueError):
    pass


def _canonical_digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _sha256(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def _decode(blob: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(blob.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ActionFeasibilityVerificationError(f"{label} is not valid UTF-8 JSON") from error
    if not isinstance(value, dict):
        raise ActionFeasibilityVerificationError(f"{label} must be an object")
    return value


def _verify_digest(record: dict[str, Any], label: str) -> None:
    claimed = record.get("result_digest")
    if not isinstance(claimed, str) or len(claimed) != 64:
        raise ActionFeasibilityVerificationError(f"{label} result_digest is invalid")
    material = dict(record)
    material.pop("result_digest", None)
    if _canonical_digest(material) != claimed:
        raise ActionFeasibilityVerificationError(f"{label} result_digest mismatch")


def _scan_private(value: Any, path: str = "$.") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            lower = str(key).lower()
            if lower.endswith("_path") or lower in {"username", "user", "home", "install_path", "machine_name", "computer_name"}:
                raise ActionFeasibilityVerificationError(f"private field prohibited at {path}{key}")
            _scan_private(item, f"{path}{key}.")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _scan_private(item, f"{path}[{index}].")
    elif isinstance(value, str) and PRIVATE_PATTERN.search(value):
        raise ActionFeasibilityVerificationError(f"private path-like value prohibited at {path}")


def _require_int(value: Any, label: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ActionFeasibilityVerificationError(f"{label} must be an integer >= {minimum}")
    return value


def _verify_windows(
    document: dict[str, Any],
    *,
    expected_raw_log_sha256: str,
    expected_pack_sha256: str,
) -> tuple[int, int]:
    if document.get("schema_version") != 1 or document.get("export_contract") != EXPORT_CONTRACT:
        raise ActionFeasibilityVerificationError("unsupported detailed window export")
    if document.get("authority") != "NO_ORDERS":
        raise ActionFeasibilityVerificationError("detailed export authority must remain NO_ORDERS")
    if document.get("source_raw_log_sha256") != expected_raw_log_sha256:
        raise ActionFeasibilityVerificationError("detailed export raw-log identity mismatch")
    if document.get("installed_pack_sha256") != expected_pack_sha256:
        raise ActionFeasibilityVerificationError("detailed export pack identity mismatch")
    if document.get("raw_log_in_export") is not False:
        raise ActionFeasibilityVerificationError("raw log may not appear in detailed export")
    if document.get("project_issue_attempt_count") != 0 or document.get("direct_acknowledgement_count") != 0:
        raise ActionFeasibilityVerificationError("detailed export may not claim issue or acknowledgement")
    windows = document.get("windows")
    if not isinstance(windows, list) or not windows:
        raise ActionFeasibilityVerificationError("detailed export requires windows")
    seen_windows: set[str] = set()
    sample_count = 0
    for window in windows:
        if not isinstance(window, dict):
            raise ActionFeasibilityVerificationError("window must be an object")
        _verify_digest(window, "window")
        window_id = window.get("window_id")
        if not isinstance(window_id, str) or not window_id or window_id in seen_windows:
            raise ActionFeasibilityVerificationError("window IDs must be unique")
        seen_windows.add(window_id)
        selected = window.get("selected_unit_ids")
        actors = window.get("actors")
        if not isinstance(selected, list) or len(selected) != len(set(selected)):
            raise ActionFeasibilityVerificationError("selected_unit_ids invalid")
        if not isinstance(actors, list) or len(actors) != window.get("actor_count"):
            raise ActionFeasibilityVerificationError("actor count mismatch")
        if sorted(item.get("unit_id") for item in actors) != sorted(selected):
            raise ActionFeasibilityVerificationError("actor identities differ from selection")
        target = window.get("target_unit_id")
        if isinstance(target, str) and "hidden" in target.lower():
            raise ActionFeasibilityVerificationError("hidden target identity is prohibited")
        if window.get("project_issue_attempted") is not False or window.get("direct_acknowledgement_observed") is not False:
            raise ActionFeasibilityVerificationError("window may not claim issue or acknowledgement")
        for actor in actors:
            if not isinstance(actor, dict):
                raise ActionFeasibilityVerificationError("actor must be an object")
            _verify_digest(actor, "actor")
            samples = actor.get("samples")
            summary = actor.get("summary")
            if not isinstance(samples, list) or not samples or not isinstance(summary, dict):
                raise ActionFeasibilityVerificationError("actor samples or summary invalid")
            if summary.get("sample_count") != len(samples):
                raise ActionFeasibilityVerificationError("actor sample count mismatch")
            previous_offset = -1
            counts = {key: 0 for key in sorted(REACHABILITY)}
            for sample in samples:
                if not isinstance(sample, dict):
                    raise ActionFeasibilityVerificationError("sample must be an object")
                offset = _require_int(sample.get("time_offset_ms"), "time_offset_ms")
                if offset < previous_offset:
                    raise ActionFeasibilityVerificationError("sample offsets are out of order")
                previous_offset = offset
                if sample.get("unit_id") != actor.get("unit_id"):
                    raise ActionFeasibilityVerificationError("sample actor identity mismatch")
                reachability = sample.get("reachability")
                if reachability not in REACHABILITY:
                    raise ActionFeasibilityVerificationError("invalid reachability")
                counts[reachability] += 1
                current_target = sample.get("current_target_id")
                if isinstance(current_target, str) and "hidden" in current_target.lower():
                    raise ActionFeasibilityVerificationError("hidden current target is prohibited")
                for boolean_field in (
                    "controllable", "player_controlled", "ai_controlled", "script_controlled",
                    "moving", "idle", "leaving", "routing", "shattered",
                    "ordered_position_match", "current_target_match",
                ):
                    if type(sample.get(boolean_field)) is not bool:
                        raise ActionFeasibilityVerificationError(f"{boolean_field} must be boolean")
            if summary.get("reachability_counts") != counts:
                raise ActionFeasibilityVerificationError("actor reachability summary mismatch")
            sample_count += len(samples)
    if document.get("window_count") != len(windows):
        raise ActionFeasibilityVerificationError("document window count mismatch")
    if document.get("sample_count") != sample_count:
        raise ActionFeasibilityVerificationError("document sample count mismatch")
    _verify_digest(document, "detailed export")
    _scan_private(document)
    return len(windows), sample_count


def verify_action_feasibility_reexport_zip(
    path: Path,
    *,
    expected_raw_log_sha256: str = EXPECTED_SOURCE_RAW_SHA256,
    expected_pack_sha256: str = EXPECTED_PACK_SHA256,
    expected_source_public_capture_sha256: str = EXPECTED_SOURCE_PUBLIC_CAPTURE_SHA256,
) -> dict[str, Any]:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ActionFeasibilityVerificationError("duplicate ZIP member")
        for name in names:
            pure = PurePosixPath(name)
            if pure.is_absolute() or ".." in pure.parts or "\\" in name:
                raise ActionFeasibilityVerificationError("unsafe ZIP member path")
        if set(names) != EXPECTED_MEMBERS:
            raise ActionFeasibilityVerificationError("unexpected re-export member set")
        blobs = {name: archive.read(name) for name in names}
    document = _decode(blobs["action_feasibility_windows.json"], "windows document")
    manifest = _decode(blobs["public_reexport_manifest.json"], "public manifest")
    if manifest.get("schema_version") != 1 or manifest.get("capture_kind") != "action_feasibility_window_reexport":
        raise ActionFeasibilityVerificationError("unsupported re-export manifest")
    if manifest.get("source_public_capture_sha256") != expected_source_public_capture_sha256:
        raise ActionFeasibilityVerificationError("source public capture mismatch")
    if manifest.get("source_raw_log_sha256") != expected_raw_log_sha256:
        raise ActionFeasibilityVerificationError("manifest raw-log identity mismatch")
    if manifest.get("installed_pack_sha256") != expected_pack_sha256:
        raise ActionFeasibilityVerificationError("manifest pack identity mismatch")
    if manifest.get("action_feasibility_windows_sha256") != _sha256(blobs["action_feasibility_windows.json"]):
        raise ActionFeasibilityVerificationError("windows member hash mismatch")
    if manifest.get("authority") != "NO_ORDERS":
        raise ActionFeasibilityVerificationError("manifest authority must remain NO_ORDERS")
    if manifest.get("source_raw_log_in_export") is not False or manifest.get("personal_paths_in_export") is not False:
        raise ActionFeasibilityVerificationError("manifest privacy boundary is invalid")
    if manifest.get("project_issue_attempt_count") != 0 or manifest.get("direct_acknowledgement_count") != 0:
        raise ActionFeasibilityVerificationError("manifest may not claim issue or acknowledgement")
    window_count, sample_count = _verify_windows(
        document,
        expected_raw_log_sha256=expected_raw_log_sha256,
        expected_pack_sha256=expected_pack_sha256,
    )
    if manifest.get("window_count") != window_count or manifest.get("sample_count") != sample_count:
        raise ActionFeasibilityVerificationError("manifest counts differ from detailed export")
    _scan_private(manifest)
    result: dict[str, Any] = {
        "schema_version": 1,
        "verification_contract": VERIFICATION_CONTRACT,
        "source_zip_sha256": _sha256(path.read_bytes()),
        "source_raw_log_sha256": expected_raw_log_sha256,
        "installed_pack_sha256": expected_pack_sha256,
        "window_count": window_count,
        "sample_count": sample_count,
        "authority": "NO_ORDERS",
        "project_issue_attempt_count": 0,
        "direct_acknowledgement_count": 0,
        "status": "VERIFIED_PUBLIC_SAFE_DETAILED_REEXPORT",
        "interpretation_limits": [
            "Command origin remains unresolved.",
            "Point reachability and state matches do not establish route completion, acknowledgement, execution, arrival, or outcome.",
        ],
    }
    result["result_digest"] = _canonical_digest(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a public-safe action-feasibility window re-export")
    parser.add_argument("capture_zip", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify_action_feasibility_reexport_zip(args.capture_zip)
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
