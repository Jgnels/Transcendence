from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TOOLS_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS_ROOT))

from build_battle_corpus import build_corpus
from capture_sfo_environment import (
    DEFAULT_SFO_WORKSHOP_ID,
    WORKSHOP_APP_ID,
    _find_case_insensitive,
    derive_steamapps_root,
    discover_used_mods_path,
)
from parse_battle_log import BattleLogError, parse_battle_logs, summarize_battle
from run_battle_report import build_battle_report
from verify_battle4_dense_replay import build_dense_replay_verification

PACK_NAME = "transcendence_battle_replay_probe.pack"
EQUIVALENT_PACK_NAME = "transcendence_shadow_probe.pack"
DEFAULT_EQUIVALENT_PACK_SHA256 = "0714863e2081206aa7d0790ec14d7c3c3c7ae33eea416d72dba0d6a2ecd0a89e"
SHARED_BATTLE_SCRIPT_SHA256 = "86e18ec655c4a45a4a062d1dae7d10e6fd9a1cb77af5557757fbca9ed896562e"
LOG_NAME = "transcendence_runtime_log.txt"
COMPLETE_MARKER = b"TRANS_BATTLE|2|BATTLE_COMPLETE|"
PACK_MARKER = b"TRANS_BATTLE|2|PACK_LOADED|probe_kind=battle_replay_shadow"
DEFAULT_PACK_SHA256 = "6e3f8e7bbc7d66754a7fa764c802e2b5599d13e83820e0785cb85d738040f66d"


class SfoReplayCaptureError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def get_repo_root(explicit: str | None) -> Path:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(os.path.expandvars(explicit)).expanduser())
    if os.name == "nt" and os.environ.get("USERPROFILE"):
        candidates.append(Path(os.environ["USERPROFILE"]) / "Projects" / "Transcendence")
    candidates.append(Path.home() / "Projects" / "Transcendence")
    for candidate in candidates:
        if candidate.is_dir() and (candidate / "AGENTS.md").is_file():
            return candidate.resolve()
    raise SfoReplayCaptureError("Transcendence repository was not found.")


def get_game_root(repo_root: Path, explicit: str | None) -> Path:
    if explicit:
        candidate = Path(os.path.expandvars(explicit)).expanduser()
        if candidate.is_dir():
            return candidate.resolve()
        raise SfoReplayCaptureError(f"WH3 game root does not exist: {candidate}")
    private = repo_root / "local_inputs" / "machine_profiles" / "gaming_laptop_private.json"
    if private.is_file():
        value = json.loads(private.read_text(encoding="utf-8-sig"))
        candidate = Path(str(value.get("game", {}).get("install_path", "")))
        if candidate.is_dir():
            return candidate.resolve()
    default = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III")
    if default.is_dir():
        return default.resolve()
    raise SfoReplayCaptureError("WH3 installation path could not be resolved.")


def wh3_running() -> bool:
    if os.name != "nt":
        return False
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq Warhammer3.exe", "/NH"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        return "Warhammer3.exe" in result.stdout
    except OSError:
        return False


def read_shared(path: Path) -> bytes | None:
    try:
        return path.read_bytes()
    except (PermissionError, OSError):
        return None




def stabilize_runtime_log(
    path: Path,
    *,
    stable_reads_required: int = 2,
    poll_seconds: float = 0.25,
    timeout_seconds: float = 2.0,
) -> tuple[bytes, int, bool]:
    """Read a shared append-only log until consecutive byte-identical reads stabilize.

    Stabilization preserves late filesystem flushes after WH3 exits. It never promotes
    process exit or a stable file to BATTLE_COMPLETE.
    """
    if stable_reads_required < 2:
        raise SfoReplayCaptureError("stable_reads_required must be at least 2")
    deadline = time.monotonic() + max(0.0, timeout_seconds)
    latest = read_shared(path) or b""
    latest_hash = hashlib.sha256(latest).hexdigest() if latest else None
    stable_reads = 1 if latest else 0
    while time.monotonic() < deadline and stable_reads < stable_reads_required:
        time.sleep(max(0.0, poll_seconds))
        candidate = read_shared(path) or b""
        candidate_hash = hashlib.sha256(candidate).hexdigest() if candidate else None
        if candidate_hash is not None and candidate_hash == latest_hash:
            stable_reads += 1
        else:
            latest = candidate
            latest_hash = candidate_hash
            stable_reads = 1 if candidate else 0
    return latest, stable_reads, stable_reads >= stable_reads_required

def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_")
    return slug[:64] or "sfo_replay"


def _matches_pack_alias(name: str, expected: str) -> bool:
    folded = name.casefold()
    target = expected.casefold()
    return folded == target or (folded and folded[0] in "@!~" and folded[1:] == target)


def classify_replay_probe_entry(active_names: list[str]) -> str:
    matches = [name for name in active_names if _matches_pack_alias(name, PACK_NAME)]
    if len(matches) != 1:
        raise SfoReplayCaptureError(
            "exactly one Transcendence battle replay probe entry is required; "
            f"found {matches or 'none'} in {active_names}"
        )
    return matches[0]


def classify_battle_observer_entry(active_names: list[str]) -> dict[str, str]:
    matches: list[dict[str, str]] = []
    for name in active_names:
        if _matches_pack_alias(name, PACK_NAME):
            matches.append({"entry": name, "container_kind": "DEDICATED_REPLAY_PACK"})
        elif _matches_pack_alias(name, EQUIVALENT_PACK_NAME):
            matches.append({"entry": name, "container_kind": "SCRIPT_EQUIVALENT_SHADOW_PACK"})
    if len(matches) != 1:
        raise SfoReplayCaptureError(
            "exactly one accepted Transcendence battle observer entry is required; "
            f"found {[item['entry'] for item in matches] or 'none'} in {active_names}"
        )
    return matches[0]


def validate_sfo_replay_mod_state(
    *,
    game_root: Path,
    appdata_root: Path,
    installed_pack: Path,
    expected_pack_sha256: str,
    expected_sfo_pack_sha256: str,
    expected_equivalent_pack_sha256: str = DEFAULT_EQUIVALENT_PACK_SHA256,
    sfo_workshop_id: str = DEFAULT_SFO_WORKSHOP_ID,
) -> dict[str, Any]:
    used_mods_path, source_kind, active_names = discover_used_mods_path(
        game_root=game_root,
        appdata_root=appdata_root,
    )
    if len(active_names) != 2:
        raise SfoReplayCaptureError(
            f"SFO replay certification requires exactly two active mods; found {active_names}"
        )
    observer = classify_battle_observer_entry(active_names)
    probe_entry = observer["entry"]
    if sha256_path(installed_pack) != expected_pack_sha256:
        raise SfoReplayCaptureError("installed battle replay probe hash changed")
    if observer["container_kind"] == "DEDICATED_REPLAY_PACK":
        active_observer_pack = installed_pack
        expected_active_observer_sha256 = expected_pack_sha256
        profile_id = "SFO_PLUS_READ_ONLY_BATTLE_REPLAY_PROBE"
        observer_role = "READ_ONLY_BATTLE_REPLAY_PROBE"
    else:
        active_observer_pack = game_root / "data" / EQUIVALENT_PACK_NAME
        expected_active_observer_sha256 = expected_equivalent_pack_sha256
        profile_id = "SFO_PLUS_READ_ONLY_SCRIPT_EQUIVALENT_BATTLE_OBSERVER"
        observer_role = "READ_ONLY_SCRIPT_EQUIVALENT_BATTLE_OBSERVER"
    if not active_observer_pack.is_file():
        raise SfoReplayCaptureError(f"active battle observer pack is missing: {active_observer_pack}")
    active_observer_sha256 = sha256_path(active_observer_pack)
    if active_observer_sha256 != expected_active_observer_sha256:
        raise SfoReplayCaptureError(
            "active battle observer pack hash changed; "
            f"expected {expected_active_observer_sha256}, found {active_observer_sha256}"
        )

    steamapps = derive_steamapps_root(game_root)
    sfo_root = steamapps / "workshop" / "content" / WORKSHOP_APP_ID / sfo_workshop_id
    sfo_names = [name for name in active_names if name.casefold() != probe_entry.casefold()]
    if len(sfo_names) != 1:
        raise SfoReplayCaptureError("could not isolate the SFO launcher entry")
    if active_names.index(sfo_names[0]) != 0 or active_names.index(probe_entry) != 1:
        raise SfoReplayCaptureError(
            "SFO replay certification requires exact load order: SFO first, read-only battle observer second"
        )
    matches = _find_case_insensitive(sfo_root, sfo_names[0])
    if len(matches) != 1:
        raise SfoReplayCaptureError(
            f"SFO launcher entry did not resolve uniquely inside Workshop item {sfo_workshop_id}"
        )
    sfo_pack = matches[0]
    sfo_sha = sha256_path(sfo_pack)
    if sfo_sha != expected_sfo_pack_sha256:
        raise SfoReplayCaptureError(
            "SFO pack hash changed from the replay cohort contract; "
            f"expected {expected_sfo_pack_sha256}, found {sfo_sha}"
        )
    return {
        "schema_version": 1,
        "profile_id": profile_id,
        "used_mods_source_kind": source_kind,
        "active_mod_count": 2,
        "active_mods": [
            {
                "load_order_index": active_names.index(sfo_names[0]),
                "canonical_pack_name": sfo_pack.name,
                "role": "SFO_TOTAL_OVERHAUL",
                "sha256": sfo_sha,
                "size_bytes": sfo_pack.stat().st_size,
            },
            {
                "load_order_index": active_names.index(probe_entry),
                "canonical_pack_name": active_observer_pack.name,
                "role": observer_role,
                "sha256": active_observer_sha256,
                "size_bytes": active_observer_pack.stat().st_size,
                "container_kind": observer["container_kind"],
                "shared_battle_script_sha256": SHARED_BATTLE_SCRIPT_SHA256,
            },
        ],
        "authority": {
            "orders_emitted": False,
            "save_modified": False,
            "active_mod_list_modified": False,
        },
        "private_used_mods_path_exported": False,
        "used_mods_sha256": sha256_path(used_mods_path),
    }


def deterministic_zip(source: Path, destination: Path) -> dict[str, Any]:
    members = sorted(path for path in source.iterdir() if path.is_file())
    if not members:
        raise SfoReplayCaptureError("replay capture bundle is empty")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.unlink(missing_ok=True)
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path in members:
                data = path.read_bytes()
                if not data or not any(data):
                    raise SfoReplayCaptureError(f"capture bundle member is empty or zero-filled: {path.name}")
                info = zipfile.ZipInfo(path.name)
                info.date_time = (1980, 1, 1, 0, 0, 0)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    with zipfile.ZipFile(destination) as archive:
        if archive.testzip() is not None:
            raise SfoReplayCaptureError("replay capture ZIP failed CRC verification")
        if archive.namelist() != [path.name for path in members]:
            raise SfoReplayCaptureError("replay capture ZIP path set changed")
        for path in members:
            if archive.read(path.name) != path.read_bytes():
                raise SfoReplayCaptureError(f"replay capture ZIP member mismatch: {path.name}")
    return {
        "name": destination.name,
        "size_bytes": destination.stat().st_size,
        "sha256": sha256_path(destination),
        "member_count": len(members),
    }


def empty_summary(message: str) -> dict[str, Any]:
    return {
        "schema_version": 2,
        "evidence_status": "UNVERIFIED",
        "battle_session_count": 0,
        "completed_battle_count": 0,
        "sessions": [],
        "capability_failures": ["dense_battle_probe_not_observed"],
        "optional_unavailable": [],
        "warnings": [message],
    }


def empty_report(message: str) -> dict[str, Any]:
    return {
        "schema_version": 2,
        "mode": "BATTLE_OBSERVATION_NO_ORDERS",
        "evidence_label": "UNVERIFIED",
        "battle_count": 0,
        "completed_battle_count": 0,
        "battle_reports": [],
        "authority": {
            "unitcontrollers_created": False,
            "orders_emitted": False,
            "battle_speed_modified": False,
            "save_values_written": False,
            "visibility_modified": False,
        },
        "interpretation_limits": [message],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture dense schema-2 telemetry from one exact SFO replay.")
    parser.add_argument("--repo-root")
    parser.add_argument("--game-root")
    parser.add_argument("--replay-path", type=Path, required=True)
    parser.add_argument("--expected-replay-sha256", required=True)
    parser.add_argument("--battle-label", required=True)
    parser.add_argument("--expected-pack-sha256", default=DEFAULT_PACK_SHA256)
    parser.add_argument("--expected-sfo-pack-sha256", required=True)
    parser.add_argument("--expected-equivalent-pack-sha256", default=DEFAULT_EQUIVALENT_PACK_SHA256)
    parser.add_argument("--source-contract-digest")
    parser.add_argument("--corpus-version", default="v0.1Z")
    parser.add_argument("--sfo-workshop-id", default=DEFAULT_SFO_WORKSHOP_ID)
    parser.add_argument("--timeout-minutes", type=int, default=45)
    parser.add_argument("--poll-seconds", type=float, default=0.5)
    parser.add_argument("--no-prompt", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.timeout_minutes < 5 or args.timeout_minutes > 120:
        raise SfoReplayCaptureError("timeout-minutes must be between 5 and 120")

    repo_root = get_repo_root(args.repo_root)
    game_root = get_game_root(repo_root, args.game_root)
    replay_path = args.replay_path.expanduser().resolve()
    if not replay_path.is_file():
        raise SfoReplayCaptureError(f"replay file does not exist: {replay_path}")
    replay_sha = sha256_path(replay_path)
    if replay_sha != args.expected_replay_sha256:
        raise SfoReplayCaptureError(
            f"replay hash mismatch; expected {args.expected_replay_sha256}, found {replay_sha}"
        )

    installed_pack = game_root / "data" / PACK_NAME
    staged_pack = repo_root / "local_inputs" / "runtime_probe" / "staged" / PACK_NAME
    for path in (installed_pack, staged_pack):
        if not path.is_file():
            raise SfoReplayCaptureError(f"required replay probe pack is missing: {path}")
    installed_sha = sha256_path(installed_pack)
    staged_sha = sha256_path(staged_pack)
    if installed_sha != args.expected_pack_sha256 or staged_sha != args.expected_pack_sha256:
        raise SfoReplayCaptureError(
            "installed/staged replay probe does not match the exact contract; "
            f"installed={installed_sha}, staged={staged_sha}"
        )
    if wh3_running():
        raise SfoReplayCaptureError("close WH3 before arming the replay watcher")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    label_slug = slugify(args.battle_label)
    capture_root = (
        repo_root
        / "local_inputs"
        / "runtime_probe"
        / "sfo_replay_deep_dive"
        / f"{label_slug}_{timestamp}"
    )
    export_root = repo_root / "local_inputs" / "runtime_probe" / "exports"
    archive_root = repo_root / "local_inputs" / "runtime_probe" / "runtime_log_archives"
    for path in (capture_root, export_root, archive_root):
        path.mkdir(parents=True, exist_ok=True)

    runtime_log = game_root / LOG_NAME
    previous: dict[str, Any] | None = None
    if runtime_log.is_file():
        archive = archive_root / f"{LOG_NAME}.before_sfo_replay.{label_slug}.{timestamp}.txt"
        shutil.copy2(runtime_log, archive)
        previous = {
            "size_bytes": archive.stat().st_size,
            "sha256": sha256_path(archive),
            "private_archive_name": archive.name,
        }
        runtime_log.unlink()

    print("\nTranscendence SFO Replay Deep Dive")
    print("===================================\n")
    print(f"Exact replay: {args.battle_label}")
    print(f"Replay SHA-256: {replay_sha}")
    print(f"Replay probe SHA-256: {installed_sha}\n")
    print("In the WH3 launcher enable exactly:")
    print("  1. SFO: Grimhammer III")
    print(f"  2. {PACK_NAME}")
    print("Disable every other mod.")
    print(f"Open Replays and play: {replay_path.name}")
    print("Let it run through the result screen without issuing commands, then exit WH3.")
    print("Leave this window open.\n")
    if not args.no_prompt:
        input("Press Enter to arm the watcher, then launch WH3... ")

    deadline = time.monotonic() + args.timeout_minutes * 60
    saw_process = False
    saw_pack = False
    saw_complete = False
    process_exit_observed = False
    post_exit_stable_reads = 0
    post_exit_log_stabilized = False
    latest = b""
    latest_sha: str | None = None
    last_progress = 0.0
    print("\nWatcher armed. Waiting for schema-2 replay telemetry...")
    while time.monotonic() < deadline:
        running = wh3_running()
        saw_process = saw_process or running
        payload = read_shared(runtime_log)
        if payload and b"TRANS_BATTLE|2|" in payload:
            latest = payload
            saw_pack = saw_pack or PACK_MARKER in payload
            digest = hashlib.sha256(payload).hexdigest()
            if digest != latest_sha:
                latest_sha = digest
                now = time.monotonic()
                if now - last_progress >= 5:
                    print(
                        f"  {len(payload):,} bytes; {payload.count(b'|SAMPLE_END|')} detail samples; "
                        f"{payload.count(b'|ALLIANCE_AGGREGATE|')} aggregates; "
                        f"{payload.count(b'|COMMAND|')} commands"
                    )
                    last_progress = now
            if COMPLETE_MARKER in payload:
                time.sleep(2.0)
                final = read_shared(runtime_log)
                if final and b"TRANS_BATTLE|2|" in final:
                    latest = final
                saw_complete = COMPLETE_MARKER in latest
                break
        if saw_process and not running:
            process_exit_observed = True
            stabilized, post_exit_stable_reads, post_exit_log_stabilized = stabilize_runtime_log(
                runtime_log
            )
            if stabilized and b"TRANS_BATTLE|2|" in stabilized:
                latest = stabilized
                saw_pack = saw_pack or PACK_MARKER in latest
                saw_complete = COMPLETE_MARKER in latest
            break
        time.sleep(args.poll_seconds)

    raw_log = capture_root / "sfo_replay_trans_battle_log.txt"
    raw_log.write_bytes(latest)
    parse_error: str | None = None
    try:
        events = parse_battle_logs([raw_log])
        summary = summarize_battle(events)
        report = build_battle_report(events)
    except (BattleLogError, ValueError, OSError) as error:
        parse_error = str(error)
        summary = empty_summary(parse_error)
        report = empty_report(parse_error)

    appdata = Path(os.environ.get("APPDATA", ""))
    environment_error: str | None = None
    environment: dict[str, Any] | None = None
    try:
        if not appdata.is_dir():
            raise SfoReplayCaptureError("APPDATA could not be resolved")
        environment = validate_sfo_replay_mod_state(
            game_root=game_root,
            appdata_root=appdata,
            installed_pack=installed_pack,
            expected_pack_sha256=args.expected_pack_sha256,
            expected_sfo_pack_sha256=args.expected_sfo_pack_sha256,
            expected_equivalent_pack_sha256=args.expected_equivalent_pack_sha256,
            sfo_workshop_id=args.sfo_workshop_id,
        )
    except (ValueError, OSError, SfoReplayCaptureError) as error:
        environment_error = str(error)

    summary_path = capture_root / "battle_summary.json"
    report_path = capture_root / "battle_report.json"
    environment_path = capture_root / "sfo_replay_environment_attestation.json"
    write_json(summary_path, summary)
    write_json(report_path, report)
    write_json(
        environment_path,
        environment
        if environment is not None
        else {
            "schema_version": 1,
            "profile_id": "UNVERIFIED",
            "error": environment_error,
            "private_paths_exported": False,
        },
    )

    manifest: dict[str, Any] = {
        "schema_version": 1,
        "captured_at_utc": utc_now(),
        "target": {
            "battle_identity": args.battle_label,
            "replay_name": replay_path.name,
            "replay_sha256": replay_sha,
            "source_contract_digest": args.source_contract_digest,
        },
        "installed_pack_name": PACK_NAME,
        "installed_pack_sha256": installed_sha,
        "staged_pack_sha256": staged_sha,
        "expected_pack_sha256": args.expected_pack_sha256,
        "expected_sfo_pack_sha256": args.expected_sfo_pack_sha256,
        "expected_equivalent_pack_sha256": args.expected_equivalent_pack_sha256,
        "environment_verified": environment is not None,
        "environment_error": environment_error,
        "runtime_log_cleared_before_replay": True,
        "previous_runtime_log": previous,
        "wh3_process_observed": saw_process,
        "process_exit_observed": process_exit_observed,
        "post_exit_log_stabilized": post_exit_log_stabilized,
        "post_exit_stable_reads": post_exit_stable_reads,
        "process_exit_promoted_to_battle_complete": False,
        "pack_marker_observed": saw_pack,
        "battle_complete_marker_observed": saw_complete,
        "timed_out": time.monotonic() >= deadline,
        "captured_log_name": raw_log.name,
        "captured_log_size_bytes": raw_log.stat().st_size,
        "captured_log_sha256": sha256_path(raw_log),
        "parse_error": parse_error,
        "privacy": {
            "replay_binary_exported": False,
            "absolute_paths_exported": False,
            "unrelated_game_files_exported": False,
            "raw_probe_log_in_private_upload": True,
        },
    }
    manifest_path = capture_root / "capture_manifest.json"
    write_json(manifest_path, manifest)

    verification = build_dense_replay_verification(
        summary=summary,
        report=report,
        manifest=manifest,
        expected_pack_sha256=args.expected_pack_sha256,
        expected_replay_sha256=args.expected_replay_sha256,
        battle_identity=args.battle_label,
    )
    verification["checks"]["exact_sfo_replay_environment_verified"] = environment is not None
    if not all(verification["checks"].values()):
        verification["status"] = "PARTIAL" if saw_complete else "UNVERIFIED"
        verification["evidence_label"] = "UNVERIFIED"
    body = dict(verification)
    body.pop("result_digest", None)
    verification["result_digest"] = hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    verification_path = capture_root / "sfo_replay_verification.json"
    write_json(verification_path, verification)

    corpus_version = re.sub(r"[^A-Za-z0-9._-]+", "_", args.corpus_version).strip("_") or "v0.1Z"
    corpus_path = capture_root / f"{label_slug}_observed_dense_{corpus_version}.json"
    if report.get("battle_reports"):
        corpus = build_corpus(
            report,
            corpus_id=f"{label_slug}_observed_dense_{corpus_version}",
            replay_sha256=replay_sha,
            raw_log_sha256=manifest["captured_log_sha256"],
            capture_verification_digest=verification["result_digest"],
            owner_context=(
                "Exact SFO replay hash-bound to a project capture contract; used for "
                "replay-to-live-telemetry alignment, not as an optimal policy label."
            ),
        )
        write_json(corpus_path, corpus)

    bundle = capture_root / "private_upload_bundle"
    bundle.mkdir()
    sources = [raw_log, summary_path, report_path, environment_path, manifest_path, verification_path]
    if corpus_path.is_file():
        sources.append(corpus_path)
    records: list[dict[str, Any]] = []
    for source in sources:
        destination = bundle / source.name
        shutil.copy2(source, destination)
        records.append(
            {
                "name": destination.name,
                "size_bytes": destination.stat().st_size,
                "sha256": sha256_path(destination),
            }
        )
    export_manifest = {
        "schema_version": 1,
        "gate": "SFO_REPLAY_DEEP_DIVE",
        "battle_identity": args.battle_label,
        "status": verification["status"],
        "verification_result_digest": verification["result_digest"],
        "private_upload": True,
        "replay_binary_included": False,
        "files": records,
    }
    write_json(bundle / "export_manifest.json", export_manifest)
    zip_path = export_root / f"Transcendence_SFO_ReplayDeepDive_{label_slug}_{timestamp}.zip"
    zip_result = deterministic_zip(bundle, zip_path)

    print("\nSFO replay deep dive finished.")
    print(f"Status: {verification['status']}")
    print(f"ZIP SHA-256: {zip_result['sha256']}")
    print("Upload this private ZIP here:")
    print(zip_path)
    return 0 if str(verification["status"]).startswith("OBSERVED_DENSE") else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nCapture cancelled.", file=sys.stderr)
        raise SystemExit(130)
    except Exception as error:
        print(f"\nERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
