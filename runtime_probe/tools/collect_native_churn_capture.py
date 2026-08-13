from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "runtime_probe" / "tools"))
sys.path.insert(0, str(REPO_ROOT / "synthetic_lab"))

from parse_probe_log import parse_logs, summarize
from verify_native_churn_capture import verify_capture
from verify_native_churn_profile import _discover_used_mods_allow_empty

EXPORT_CONTRACT = "NATIVE_CAI_DIRECTIONAL_CHURN_PUBLIC_EXPORT_V1"


class NativeChurnCollectionError(ValueError):
    pass


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _deterministic_zip(files: list[tuple[str, Path]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, path in sorted(files, key=lambda item: item[0]):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())


def _latest_prepared(repo_root: Path) -> Path:
    latest = repo_root / "local_inputs" / "runtime_probe" / "native_churn_sessions" / "latest.json"
    if not latest.is_file():
        raise NativeChurnCollectionError("native churn latest session is missing; run preparation first")
    record = json.loads(latest.read_text(encoding="utf-8-sig"))
    path = Path(str(record.get("prepared_session", "")))
    if not path.is_file():
        raise NativeChurnCollectionError(f"prepared session does not exist: {path}")
    return path


def collect_session(
    *,
    prepared_path: Path,
    owner_protocol_attested: bool,
    repo_root: Path = REPO_ROOT,
) -> tuple[dict[str, Any], Path]:
    prepared = json.loads(prepared_path.read_text(encoding="utf-8-sig"))
    if prepared.get("contract") != "NATIVE_CAI_DIRECTIONAL_CHURN_PREPARED_SESSION_V1":
        raise NativeChurnCollectionError("prepared session contract mismatch")
    runtime_log = Path(str(prepared["runtime_log"]))
    if not runtime_log.is_file() or runtime_log.stat().st_size == 0:
        raise NativeChurnCollectionError(f"runtime log is missing or empty: {runtime_log}")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence_root = repo_root / "local_inputs" / "runtime_probe" / "native_churn_evidence" / f"{prepared['profile'].lower()}_{stamp}"
    evidence_root.mkdir(parents=True, exist_ok=True)
    log_copy = evidence_root / "transcendence_runtime_log.txt"
    shutil.copy2(runtime_log, log_copy)

    public_binding_path = Path(str(prepared["profile_binding_public"]))
    private_binding_path = Path(str(prepared["profile_binding_private"]))
    public_binding = json.loads(public_binding_path.read_text(encoding="utf-8-sig"))
    private_binding = json.loads(private_binding_path.read_text(encoding="utf-8-sig"))
    game_root = Path(str(private_binding["game_root"]))
    appdata_root = Path(str(private_binding["appdata_root"]))
    used_mods_path, _source_kind, _active = _discover_used_mods_allow_empty(game_root=game_root, appdata_root=appdata_root)
    used_mods_copy = evidence_root / "used_mods_private.txt"
    shutil.copy2(used_mods_path, used_mods_copy)

    installed_probe = Path(str(prepared["installed_probe"]))
    staged_probe = Path(str(prepared["staged_probe"]))
    events = parse_logs([log_copy])
    loaded_kinds = sorted({event.fields.get("probe_kind") for event in events if event.event == "PACK_LOADED" and event.fields.get("probe_kind")})
    summary_path = evidence_root / "probe_summary.json"
    summary_path.write_text(json.dumps(summarize(events), indent=2, sort_keys=True) + "\n", encoding="utf-8")

    evidence_manifest = {
        "schema_version": 1,
        "evidence_phase": "campaign_shadow",
        "loaded_probe_kinds": loaded_kinds,
        "unexpected_loaded_probe_kinds": [kind for kind in loaded_kinds if kind != "shadow"],
        "installed_probe_packs": [
            {
                "name": "transcendence_shadow_probe.pack",
                "installed_sha256": sha256(installed_probe),
                "staged_sha256": sha256(staged_probe),
                "matches_staged": sha256(installed_probe) == sha256(staged_probe),
                "loaded_in_log": "shadow" in loaded_kinds,
            }
        ],
        "used_mods": {
            "private_copy": str(used_mods_copy),
            "sha256": sha256(used_mods_copy),
        },
    }
    evidence_manifest_path = evidence_root / "evidence_manifest_private.json"
    evidence_manifest_path.write_text(json.dumps(evidence_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    verification = verify_capture(
        log_path=log_copy,
        evidence_manifest_path=evidence_manifest_path,
        public_binding_path=public_binding_path,
        private_binding_path=private_binding_path,
        minimum_turns=int(prepared["minimum_turns"]),
        owner_protocol_attested=owner_protocol_attested,
    )
    verification_path = evidence_root / "native_churn_capture_verification.json"
    verification_path.write_text(json.dumps(verification, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    public_binding_copy = evidence_root / "native_churn_profile_binding.json"
    shutil.copy2(public_binding_path, public_binding_copy)

    export_manifest = {
        "contract": EXPORT_CONTRACT,
        "profile": prepared["profile"],
        "authority": "NO_ORDERS",
        "application_authority": "PROHIBITED",
        "verification_status": verification["verification_status"],
        "files": [],
        "excluded_private_material": [
            "profile_binding_private.json",
            "evidence_manifest_private.json",
            "used_mods_private.txt",
            "game/install paths",
            "raw SFO pack bytes",
        ],
    }
    public_files = [
        ("native_churn_capture_verification.json", verification_path),
        ("native_churn_profile_binding.json", public_binding_copy),
        ("probe_summary.json", summary_path),
        ("transcendence_runtime_log.txt", log_copy),
    ]
    for name, path in public_files:
        export_manifest["files"].append({"name": name, "size_bytes": path.stat().st_size, "sha256": sha256(path)})
    export_manifest_path = evidence_root / "export_manifest.json"
    export_manifest_path.write_text(json.dumps(export_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    public_files.append(("export_manifest.json", export_manifest_path))

    exports = repo_root / "local_inputs" / "runtime_probe" / "exports"
    zip_path = exports / f"Transcendence_NativeChurn_{prepared['profile']}_{stamp}.zip"
    _deterministic_zip(public_files, zip_path)
    return verification, zip_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect, verify and package a v0.2L native directional-churn owner run.")
    parser.add_argument("--prepared", type=Path)
    parser.add_argument("--owner-protocol-attested", action="store_true")
    parser.add_argument("--no-prompt", action="store_true")
    args = parser.parse_args()
    prepared = args.prepared.resolve() if args.prepared else _latest_prepared(REPO_ROOT)
    attested = bool(args.owner_protocol_attested)
    if not args.no_prompt and not attested:
        answer = input(
            "During the observation window, did you avoid ALL voluntary campaign orders (movement, recruitment, stance changes, diplomacy, building/spending), aside from mandatory prompts/battles? Type YES only if true: "
        ).strip()
        attested = answer == "YES"
    verification, zip_path = collect_session(prepared_path=prepared, owner_protocol_attested=attested)
    print("\nNATIVE CHURN CAPTURE COLLECTED")
    print(f"Status: {verification['verification_status']}")
    print(f"Upload ZIP: {zip_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
