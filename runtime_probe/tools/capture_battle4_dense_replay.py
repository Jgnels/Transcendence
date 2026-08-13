from __future__ import annotations

import argparse
import hashlib
import json
import os
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
from parse_battle_log import BattleLogError, parse_battle_logs, summarize_battle
from run_battle_report import build_battle_report
from verify_battle4_dense_replay import (
    EXPECTED_REPLAY_SHA256,
    build_dense_replay_verification,
)

PACK_NAME = "transcendence_battle_replay_probe.pack"
REPLAY_NAME = "Auto-save.replay"
LOG_NAME = "transcendence_runtime_log.txt"
COMPLETE_MARKER = b"TRANS_BATTLE|2|BATTLE_COMPLETE|"
PACK_MARKER = b"TRANS_BATTLE|2|PACK_LOADED|probe_kind=battle_replay_shadow"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


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
    raise RuntimeError("Transcendence repository was not found under the expected Projects folder.")


def get_game_root(repo_root: Path, explicit: str | None) -> Path:
    if explicit:
        path = Path(os.path.expandvars(explicit)).expanduser()
        if path.is_dir():
            return path.resolve()
        raise RuntimeError(f"WH3 game root does not exist: {path}")
    private = repo_root / "local_inputs" / "machine_profiles" / "gaming_laptop_private.json"
    if private.is_file():
        data = json.loads(private.read_text(encoding="utf-8-sig"))
        path = Path(str(data.get("game", {}).get("install_path", "")))
        if path.is_dir():
            return path.resolve()
    default = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III")
    if default.is_dir():
        return default.resolve()
    raise RuntimeError("WH3 installation path could not be resolved.")


def replay_candidates(explicit: str | None) -> list[Path]:
    values: list[Path] = []
    if explicit:
        values.append(Path(os.path.expandvars(explicit)).expanduser())
    for name in ("APPDATA", "LOCALAPPDATA"):
        root = os.environ.get(name)
        if root:
            values.append(Path(root) / "The Creative Assembly" / "Warhammer3" / "replays" / REPLAY_NAME)
    unique: list[Path] = []
    seen: set[str] = set()
    for path in values:
        key = str(path).lower()
        if key not in seen:
            seen.add(key)
            unique.append(path)
    return unique


def find_exact_replay(explicit: str | None) -> tuple[Path, str]:
    found: list[tuple[Path, str]] = []
    for path in replay_candidates(explicit):
        if path.is_file():
            digest = sha256_path(path)
            found.append((path, digest))
            if digest == EXPECTED_REPLAY_SHA256:
                return path.resolve(), digest
    if found:
        description = "\n".join(f"  {path}: {digest}" for path, digest in found)
        raise RuntimeError(
            "Auto-save.replay is not the preserved Battle 4 replay.\n"
            f"Expected {EXPECTED_REPLAY_SHA256}\nFound:\n{description}"
        )
    raise RuntimeError("The preserved Auto-save.replay was not found in the WH3 replay folder.")


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
    except Exception:
        return False


def read_shared(path: Path) -> bytes | None:
    try:
        return path.read_bytes()
    except (PermissionError, OSError):
        return None


def zip_folder(source: Path, destination: Path) -> None:
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(source).as_posix())


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
    parser = argparse.ArgumentParser(description="Capture dense telemetry from the preserved Battle 4 replay.")
    parser.add_argument("--repo-root")
    parser.add_argument("--game-root")
    parser.add_argument("--replay-path")
    parser.add_argument("--expected-pack-sha256", required=True)
    parser.add_argument("--timeout-minutes", type=int, default=35)
    parser.add_argument("--poll-seconds", type=float, default=0.5)
    parser.add_argument("--no-prompt", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.timeout_minutes < 5 or args.timeout_minutes > 120:
        raise RuntimeError("timeout-minutes must be between 5 and 120")

    repo_root = get_repo_root(args.repo_root)
    game_root = get_game_root(repo_root, args.game_root)
    replay_path, replay_sha = find_exact_replay(args.replay_path)
    installed_pack = game_root / "data" / PACK_NAME
    staged_pack = repo_root / "local_inputs" / "runtime_probe" / "staged" / PACK_NAME
    for path in (installed_pack, staged_pack):
        if not path.is_file():
            raise RuntimeError(f"Required battle replay pack is missing: {path}")
    installed_sha = sha256_path(installed_pack)
    staged_sha = sha256_path(staged_pack)
    if installed_sha != args.expected_pack_sha256 or staged_sha != args.expected_pack_sha256:
        raise RuntimeError(
            "The installed/staged battle replay pack does not match the v0.1K contract.\n"
            f"Expected:  {args.expected_pack_sha256}\n"
            f"Installed: {installed_sha}\nStaged:    {staged_sha}"
        )
    if wh3_running():
        raise RuntimeError("Close WH3 before arming the dense replay watcher.")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    capture_root = repo_root / "local_inputs" / "runtime_probe" / "battle4_dense" / f"capture_{timestamp}"
    export_root = repo_root / "local_inputs" / "runtime_probe" / "exports"
    archive_root = repo_root / "local_inputs" / "runtime_probe" / "runtime_log_archives"
    for path in (capture_root, export_root, archive_root):
        path.mkdir(parents=True, exist_ok=True)

    runtime_log = game_root / LOG_NAME
    previous: dict[str, Any] | None = None
    if runtime_log.is_file():
        archive = archive_root / f"{LOG_NAME}.before_battle4_dense.{timestamp}.txt"
        shutil.copy2(runtime_log, archive)
        previous = {
            "size_bytes": archive.stat().st_size,
            "sha256": sha256_path(archive),
            "private_archive_name": archive.name,
        }
        runtime_log.unlink()

    print("\nTranscendence Battle 4 Dense Replay Capture")
    print("=============================================\n")
    print(f"Exact replay verified: {replay_path.name}")
    print(f"Replay SHA-256: {replay_sha}")
    print(f"Dense replay pack SHA-256: {installed_sha}\n")
    print(f"Enable ONLY {PACK_NAME} in the WH3 launcher.")
    print("Open Replays, play Auto-save.replay through the result screen, and issue no commands.")
    print("This is replay playback, not a manual refight. Leave this window open.\n")
    if not args.no_prompt:
        input("Press Enter to arm the watcher, then launch WH3... ")

    deadline = time.monotonic() + args.timeout_minutes * 60
    saw_process = False
    saw_pack = False
    saw_complete = False
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
                    detail = payload.count(b"|SAMPLE_END|")
                    aggregate = payload.count(b"|ALLIANCE_AGGREGATE|")
                    heartbeat = payload.count(b"|SAMPLER_HEARTBEAT|")
                    print(
                        f"  {len(payload):,} bytes; {detail} detail samples; "
                        f"{aggregate} alliance aggregates; {heartbeat} heartbeats"
                    )
                    last_progress = now
            if COMPLETE_MARKER in payload:
                time.sleep(2.0)
                final = read_shared(runtime_log)
                if final and b"TRANS_BATTLE|2|" in final:
                    latest = final
                saw_complete = COMPLETE_MARKER in latest
                break
        if saw_process and not running and latest:
            break
        if saw_process and not running and not latest:
            break
        time.sleep(args.poll_seconds)

    log_path = capture_root / "battle4_dense_trans_battle_log.txt"
    log_path.write_bytes(latest)
    parse_error: str | None = None
    try:
        events = parse_battle_logs([log_path])
        summary = summarize_battle(events)
        report = build_battle_report(events)
    except (BattleLogError, ValueError, OSError) as error:
        parse_error = str(error)
        summary = empty_summary(parse_error)
        report = empty_report(parse_error)

    summary_path = capture_root / "battle_summary.json"
    report_path = capture_root / "battle_report.json"
    write_json(summary_path, summary)
    write_json(report_path, report)

    manifest: dict[str, Any] = {
        "schema_version": 1,
        "captured_at_utc": utc_now(),
        "target": {
            "battle_identity": "Battle of Eilhart — Reikland vs Empire Secessionists",
            "replay_name": REPLAY_NAME,
            "replay_sha256": replay_sha,
        },
        "installed_pack_name": PACK_NAME,
        "installed_pack_sha256": installed_sha,
        "staged_pack_sha256": staged_sha,
        "expected_pack_sha256": args.expected_pack_sha256,
        "runtime_log_cleared_before_replay": True,
        "previous_runtime_log": previous,
        "wh3_process_observed": saw_process,
        "pack_marker_observed": saw_pack,
        "battle_complete_marker_observed": saw_complete,
        "timed_out": time.monotonic() >= deadline,
        "captured_log_name": log_path.name,
        "captured_log_size_bytes": log_path.stat().st_size,
        "captured_log_sha256": sha256_path(log_path),
        "parse_error": parse_error,
        "privacy": {
            "replay_binary_exported": False,
            "absolute_paths_exported": False,
            "unrelated_game_files_exported": False,
        },
    }
    manifest_path = capture_root / "capture_manifest.json"
    write_json(manifest_path, manifest)

    verification = build_dense_replay_verification(
        summary=summary,
        report=report,
        manifest=manifest,
        expected_pack_sha256=args.expected_pack_sha256,
    )
    verification_path = capture_root / "battle4_dense_verification.json"
    write_json(verification_path, verification)

    corpus_path = capture_root / "battle4_eilhart_observed_dense_v2.json"
    if report.get("battle_reports"):
        corpus = build_corpus(
            report,
            corpus_id="battle4_eilhart_observed_dense_v2",
            replay_sha256=replay_sha,
            raw_log_sha256=manifest["captured_log_sha256"],
            capture_verification_digest=verification["result_digest"],
            owner_context=(
                "Owner identifies this as the messy representative battle; three earlier "
                "manual battles were decisive, low-casualty victories."
            ),
        )
        write_json(corpus_path, corpus)

    bundle = capture_root / "upload_bundle"
    bundle.mkdir()
    files = [log_path, summary_path, report_path, manifest_path, verification_path]
    if corpus_path.is_file():
        files.append(corpus_path)
    records: list[dict[str, Any]] = []
    for source in files:
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
        "exported_at_utc": utc_now(),
        "gate": "BATTLE4_DENSE_REPLAY_CALIBRATION",
        "status": verification["status"],
        "verification_result_digest": verification["result_digest"],
        "files": records,
    }
    write_json(bundle / "export_manifest.json", export_manifest)
    zip_path = export_root / f"Transcendence_Battle4_Dense_Replay_{timestamp}.zip"
    zip_folder(bundle, zip_path)

    print("\nDense replay capture finished.")
    print(f"Status: {verification['status']}")
    print("Upload this ZIP:")
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
