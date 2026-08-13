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

from parse_probe_log import parse_logs
from run_native_visible_behavior import _extract_snapshots
from run_native_visible_churn import run_native_visible_churn_batch
from verify_native_churn_profile import _parse_used_mods_allow_empty
from capture_sfo_environment import DEFAULT_PROBE_NAME, classify_probe_entry

CONTRACT = "NATIVE_CAI_DIRECTIONAL_CHURN_CAPTURE_VERIFICATION_V1"


class NativeChurnCaptureError(ValueError):
    pass


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _binding_digest(public: dict[str, Any]) -> str:
    unsigned = dict(public)
    unsigned.pop("binding_sha256", None)
    return hashlib.sha256(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _validate_launcher_profile(public: dict[str, Any], active_entries: list[str]) -> dict[str, Any]:
    expected_entries = list(public.get("launcher", {}).get("active_pack_entries", []))
    if not all(isinstance(item, str) for item in expected_entries):
        raise NativeChurnCaptureError("profile binding active pack entries are malformed")

    expected_probe, expected_probe_status = classify_probe_entry(expected_entries, DEFAULT_PROBE_NAME)
    observed_probe, observed_probe_status = classify_probe_entry(active_entries, DEFAULT_PROBE_NAME)

    expected_non_probe = [
        item for item in expected_entries
        if expected_probe is None or item.casefold() != expected_probe.casefold()
    ]
    observed_non_probe = [
        item for item in active_entries
        if observed_probe is None or item.casefold() != observed_probe.casefold()
    ]
    if [item.casefold() for item in observed_non_probe] != [item.casefold() for item in expected_non_probe]:
        raise NativeChurnCaptureError(
            f"non-probe active mod entries changed after preregistration: expected {expected_non_probe}, observed {observed_non_probe}"
        )

    if expected_probe_status == "DEFERRED_RUNTIME_MARKER":
        # Current launcher paths do not always materialize a local pack entry before
        # WH3 starts. Runtime PACK_LOADED + exact installed/staged hash is the
        # confirmatory evidence, so the local probe may remain absent or appear as
        # one safe exact/decorated entry after launch.
        if observed_probe_status not in {"DEFERRED_RUNTIME_MARKER", "EXACT_ACTIVE_ENTRY", "DECORATED_ACTIVE_ALIAS"}:
            raise NativeChurnCaptureError(f"unsupported runtime probe launcher state: {observed_probe_status}")
        deferred_probe_materialized = observed_probe is not None
    else:
        if observed_probe is None or observed_probe.casefold() != str(expected_probe).casefold():
            raise NativeChurnCaptureError(
                f"active shadow-probe launcher entry changed after preregistration: expected {expected_probe!r}, observed {observed_probe!r}"
            )
        deferred_probe_materialized = False

    return {
        "expected_probe_launcher_status": expected_probe_status,
        "observed_probe_launcher_status": observed_probe_status,
        "deferred_probe_materialized_after_binding": deferred_probe_materialized,
        "non_probe_entries_match": True,
    }


def verify_capture(
    *,
    log_path: Path,
    evidence_manifest_path: Path,
    public_binding_path: Path,
    private_binding_path: Path,
    minimum_turns: int,
    owner_protocol_attested: bool,
) -> dict[str, Any]:
    if minimum_turns < 7:
        raise NativeChurnCaptureError("minimum_turns must be at least 7 for the repeated non-overlapping endpoint")
    public = json.loads(public_binding_path.read_text(encoding="utf-8-sig"))
    private = json.loads(private_binding_path.read_text(encoding="utf-8-sig"))
    evidence = json.loads(evidence_manifest_path.read_text(encoding="utf-8-sig"))
    if public.get("contract") != "NATIVE_CAI_CHURN_PROFILE_BINDING_V1":
        raise NativeChurnCaptureError("profile binding contract mismatch")
    expected_binding = public.get("binding_sha256")
    if not isinstance(expected_binding, str) or _binding_digest(public) != expected_binding:
        raise NativeChurnCaptureError("public profile binding digest mismatch")
    if private.get("public_binding_sha256") != expected_binding:
        raise NativeChurnCaptureError("private/public profile binding mismatch")
    if public.get("authority") != "NO_ORDERS" or public.get("application_authority") != "PROHIBITED":
        raise NativeChurnCaptureError("profile binding authority mismatch")

    game_root = Path(str(private["game_root"]))
    probe_path = Path(str(private["probe_path"]))
    exe_path = game_root / "Warhammer3.exe"
    if not exe_path.is_file() or _sha256(exe_path) != public["game"]["exe_sha256"]:
        raise NativeChurnCaptureError("WH3 executable changed after profile binding")
    if not probe_path.is_file() or _sha256(probe_path) != public["probe"]["sha256"]:
        raise NativeChurnCaptureError("read-only shadow probe changed after profile binding")
    if public.get("profile") == "SFO":
        sfo_path_raw = private.get("sfo_pack_path")
        if not sfo_path_raw:
            raise NativeChurnCaptureError("private SFO pack path is unavailable")
        sfo_path = Path(str(sfo_path_raw))
        if not sfo_path.is_file() or _sha256(sfo_path) != public["sfo"]["sha256"]:
            raise NativeChurnCaptureError("SFO pack changed after profile binding")

    if evidence.get("evidence_phase") != "campaign_shadow":
        raise NativeChurnCaptureError("capture evidence phase must be campaign_shadow")
    loaded_kinds = evidence.get("loaded_probe_kinds")
    if loaded_kinds != ["shadow"]:
        raise NativeChurnCaptureError(f"capture must load only the shadow probe kind; observed {loaded_kinds!r}")
    if evidence.get("unexpected_loaded_probe_kinds"):
        raise NativeChurnCaptureError("unexpected Transcendence probe kinds were loaded")
    installed = [
        row for row in evidence.get("installed_probe_packs", [])
        if row.get("name") == "transcendence_shadow_probe.pack"
    ]
    if len(installed) != 1:
        raise NativeChurnCaptureError("evidence manifest does not bind exactly one installed shadow probe")
    installed_probe = installed[0]
    if installed_probe.get("installed_sha256") != public["probe"]["sha256"]:
        raise NativeChurnCaptureError("captured installed probe hash differs from preregistered binding")
    if installed_probe.get("matches_staged") is not True or installed_probe.get("loaded_in_log") is not True:
        raise NativeChurnCaptureError("captured shadow probe was not both staged-identical and runtime-observed")

    used_mods = evidence.get("used_mods")
    if not isinstance(used_mods, dict) or not used_mods.get("private_copy"):
        raise NativeChurnCaptureError("capture did not preserve used_mods.txt")
    captured_used_mods = Path(str(used_mods["private_copy"]))
    if not captured_used_mods.is_file():
        raise NativeChurnCaptureError("captured used_mods.txt private copy is missing")
    active_entries = _parse_used_mods_allow_empty(captured_used_mods.read_text(encoding="utf-8-sig"))
    launcher_profile_check = _validate_launcher_profile(public, active_entries)

    events = parse_logs([log_path])
    snapshots = _extract_snapshots(events)
    turns = [int(begin.fields["turn"]) for begin, _rows, _end in snapshots]
    if len(turns) < minimum_turns:
        raise NativeChurnCaptureError(f"capture has {len(turns)} local-player snapshots; minimum is {minimum_turns}")
    if any(right - left != 1 for left, right in zip(turns, turns[1:])):
        raise NativeChurnCaptureError(f"local-player snapshot turns are not consecutive: {turns}")
    observer = snapshots[0][0].fields.get("local_faction")
    if observer != public["campaign_protocol"]["observer_faction"]:
        raise NativeChurnCaptureError(
            f"observer faction mismatch: expected {public['campaign_protocol']['observer_faction']}, observed {observer}"
        )

    batch = run_native_visible_churn_batch(
        [log_path],
        profile=public["profile"],
        minimum_frames=4,
    )
    eligible = batch["aggregate_metrics"]["eligible_stable_context_region_windows"]
    if owner_protocol_attested:
        protocol_status = "OWNER_ATTESTED_PASSIVE_NO_VOLUNTARY_CAMPAIGN_ORDERS"
    else:
        protocol_status = "OWNER_PROTOCOL_NOT_ATTESTED_NONCONFIRMATORY"

    if not owner_protocol_attested:
        status = "PROFILE_BOUND_CAPTURE_OBSERVED_PROTOCOL_DEVIATION_NONCONFIRMATORY"
    elif eligible == 0:
        status = "PROFILE_BOUND_CAPTURE_OBSERVED_INSUFFICIENT_PRIMARY_EXPOSURE"
    else:
        status = "PROFILE_BOUND_CAPTURE_OBSERVED_PRIMARY_ENDPOINT_EVALUABLE"

    result: dict[str, Any] = {
        "contract": CONTRACT,
        "verification_status": status,
        "authority": "NO_ORDERS",
        "application_authority": "PROHIBITED",
        "profile": public["profile"],
        "profile_binding_sha256": expected_binding,
        "profile_checks": {
            "exe_hash_unchanged": True,
            "probe_hash_unchanged": True,
            "sfo_hash_unchanged_if_applicable": True,
            "captured_launcher_profile_matches_preregistration": True,
            "launcher_profile_detail": launcher_profile_check,
            "shadow_probe_staged_identical": True,
            "shadow_probe_runtime_observed": True,
        },
        "campaign_checks": {
            "observer_faction": observer,
            "first_turn": turns[0],
            "last_turn": turns[-1],
            "snapshot_count": len(turns),
            "consecutive_turns": True,
            "minimum_turns": minimum_turns,
            "owner_action_protocol": protocol_status,
        },
        "churn_batch": batch,
        "interpretation": [
            "Profile and probe identity are bound before and after the run.",
            "Owner passive-action protocol remains attestation rather than engine telemetry; non-attestation makes the run nonconfirmatory.",
            "Zero eligible primary windows is insufficient exposure, not evidence of good native hysteresis.",
            "A positive repeated cluster remains a player-visible causal-review signal and cannot directly authorize a project planner.",
        ],
    }
    unsigned = dict(result)
    result["result_digest"] = hashlib.sha256(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a profile-bound v0.2L native directional-churn owner capture.")
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--evidence-manifest", type=Path, required=True)
    parser.add_argument("--public-binding", type=Path, required=True)
    parser.add_argument("--private-binding", type=Path, required=True)
    parser.add_argument("--minimum-turns", type=int, default=12)
    parser.add_argument("--owner-protocol-attested", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = verify_capture(
        log_path=args.log.resolve(),
        evidence_manifest_path=args.evidence_manifest.resolve(),
        public_binding_path=args.public_binding.resolve(),
        private_binding_path=args.private_binding.resolve(),
        minimum_turns=args.minimum_turns,
        owner_protocol_attested=args.owner_protocol_attested,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
