from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from parse_battle_log import parse_battle_logs, summarize_battle
from run_battle_report import build_battle_report
from verify_battle4_dense_replay import build_dense_replay_verification


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def find_latest_capture(repo_root: Path) -> Path:
    parent = repo_root / "local_inputs" / "runtime_probe" / "battle4_dense"
    candidates = sorted(
        (
            path for path in parent.glob("capture_*")
            if (path / "battle4_dense_trans_battle_log.txt").is_file()
        ),
        reverse=True,
    )
    if not candidates:
        raise RuntimeError(f"No dense Battle 4 capture was found beneath {parent}")
    return candidates[0]


def reprocess_capture(repo_root: Path, capture_root: Path) -> dict[str, Any]:
    log_path = capture_root / "battle4_dense_trans_battle_log.txt"
    manifest_path = capture_root / "capture_manifest.json"
    if not log_path.is_file() or not manifest_path.is_file():
        raise RuntimeError("Capture folder is missing its log or capture manifest.")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_pack = str(manifest.get("expected_pack_sha256", ""))
    if len(expected_pack) != 64:
        raise RuntimeError("Capture manifest does not contain a valid expected pack SHA-256.")

    events = parse_battle_logs([log_path])
    summary = summarize_battle(events)
    report = build_battle_report(events)
    verification = build_dense_replay_verification(
        summary=summary,
        report=report,
        manifest=manifest,
        expected_pack_sha256=expected_pack,
    )

    outputs = {
        "battle_summary_reprocessed.json": summary,
        "battle_report_reprocessed.json": report,
        "battle4_dense_verification_reprocessed.json": verification,
    }
    for name, value in outputs.items():
        write_json(capture_root / name, value)

    export_root = repo_root / "local_inputs" / "runtime_probe" / "exports"
    export_root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle = capture_root / f"reprocessed_bundle_{timestamp}"
    bundle.mkdir()
    records: list[dict[str, Any]] = []
    for name in outputs:
        source = capture_root / name
        destination = bundle / name
        shutil.copy2(source, destination)
        records.append({
            "name": name,
            "size_bytes": destination.stat().st_size,
            "sha256": sha256_path(destination),
        })
    reprocess_manifest = {
        "schema_version": 1,
        "reprocessed_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_log_sha256": sha256_path(log_path),
        "source_log_size_bytes": log_path.stat().st_size,
        "source_capture_manifest_sha256": sha256_path(manifest_path),
        "status": verification["status"],
        "verification_result_digest": verification["result_digest"],
        "raw_log_exported": False,
        "files": records,
    }
    write_json(bundle / "reprocess_manifest.json", reprocess_manifest)

    zip_path = export_root / f"Transcendence_Battle4_Dense_Reprocessed_{timestamp}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(bundle.iterdir()):
            archive.write(path, arcname=path.name)
    return {
        "capture_root": str(capture_root),
        "zip_path": str(zip_path),
        "status": verification["status"],
        "verification_result_digest": verification["result_digest"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Reprocess a preserved Battle 4 dense capture without replaying WH3.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--capture-root", type=Path)
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    capture_root = args.capture_root.resolve() if args.capture_root else find_latest_capture(repo_root)
    result = reprocess_capture(repo_root, capture_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
