from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "runtime_probe" / "tools"))

from capture_sfo_environment import (
    DEFAULT_PROBE_NAME,
    DEFAULT_SFO_WORKSHOP_ID,
    PROBE_LAUNCHER_DECORATORS,
    WORKSHOP_APP_ID,
    _normalize_working_directory,
    classify_probe_entry,
    derive_steamapps_root,
    sha256,
    used_mods_candidates,
)

CONTRACT = "NATIVE_CAI_CHURN_PROFILE_BINDING_V1"


class NativeChurnProfileError(ValueError):
    pass


def _parse_used_mods_allow_empty(text: str) -> list[str]:
    entries: list[str] = []
    working_directories: set[str] = set()
    for line_no, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("//"):
            continue
        mod_match = re.fullmatch(r'mod\s+"([^"]+)"\s*;', line, flags=re.IGNORECASE)
        if mod_match:
            name = mod_match.group(1)
            if Path(name).name != name or not name.lower().endswith(".pack"):
                raise NativeChurnProfileError(f"unsafe or non-pack mod entry on line {line_no}: {name!r}")
            if any(existing.casefold() == name.casefold() for existing in entries):
                raise NativeChurnProfileError(f"duplicate active mod entry: {name}")
            entries.append(name)
            continue
        working_match = re.fullmatch(
            r'add_working_directory\s+"([^"]+)"\s*;', line, flags=re.IGNORECASE
        )
        if working_match:
            key = _normalize_working_directory(working_match.group(1), line_no=line_no)
            if key in working_directories:
                raise NativeChurnProfileError(f"duplicate add_working_directory directive on line {line_no}")
            working_directories.add(key)
            continue
        raise NativeChurnProfileError(f"unsupported used_mods.txt line {line_no}: {raw!r}")
    return entries


def _discover_used_mods_allow_empty(*, game_root: Path, appdata_root: Path) -> tuple[Path, str, list[str]]:
    observed: list[tuple[int, str, Path, list[str]]] = []
    candidates = used_mods_candidates(game_root=game_root, appdata_root=appdata_root)
    for priority, (source_kind, path) in enumerate(candidates):
        if not path.is_file():
            continue
        entries = _parse_used_mods_allow_empty(path.read_text(encoding="utf-8-sig"))
        observed.append((priority, source_kind, path.resolve(), entries))
    if not observed:
        rendered = ", ".join(str(path) for _, path in candidates)
        raise NativeChurnProfileError(f"used_mods.txt was not found in any supported location: {rendered}")
    semantic_sets = {tuple(entry.casefold() for entry in entries) for _, _, _, entries in observed}
    if len(semantic_sets) != 1:
        details = "; ".join(f"{kind}={path} -> {entries}" for _, kind, path, entries in observed)
        raise NativeChurnProfileError(f"conflicting used_mods.txt copies were found: {details}")
    _, source_kind, selected, entries = min(observed, key=lambda item: item[0])
    return selected, source_kind, entries


def _resolve_sfo_pack(steamapps: Path, active_name: str, workshop_id: str) -> Path:
    root = steamapps / "workshop" / "content" / WORKSHOP_APP_ID / workshop_id
    if not root.is_dir():
        raise NativeChurnProfileError(f"SFO Workshop item directory is missing: {root}")
    key = active_name.casefold()
    candidates = sorted(
        [path for path in root.rglob("*.pack") if path.name.casefold() == key],
        key=lambda path: str(path).casefold(),
    )
    if len(candidates) != 1:
        raise NativeChurnProfileError(
            f"expected exactly one SFO pack named {active_name!r} under Workshop item {workshop_id}; found {len(candidates)}"
        )
    return candidates[0]


def build_profile_binding(
    *,
    profile: str,
    game_root: Path,
    appdata_root: Path,
    probe_path: Path,
    campaign_difficulty: str,
    battle_difficulty: str,
    observer_faction: str,
    campaign_key: str,
    sfo_workshop_id: str = DEFAULT_SFO_WORKSHOP_ID,
) -> tuple[dict[str, Any], dict[str, Any]]:
    profile = profile.upper()
    if profile not in {"VANILLA", "SFO"}:
        raise NativeChurnProfileError("profile must be VANILLA or SFO")
    game_root = game_root.resolve()
    probe_path = probe_path.resolve()
    if not game_root.is_dir():
        raise NativeChurnProfileError(f"game root is missing: {game_root}")
    exe = game_root / "Warhammer3.exe"
    if not exe.is_file():
        raise NativeChurnProfileError(f"Warhammer3.exe is missing: {exe}")
    if not probe_path.is_file() or probe_path.name.casefold() != DEFAULT_PROBE_NAME.casefold():
        raise NativeChurnProfileError(f"installed read-only shadow probe is missing or misnamed: {probe_path}")

    used_mods_path, source_kind, active_names = _discover_used_mods_allow_empty(
        game_root=game_root,
        appdata_root=appdata_root,
    )
    probe_entry, probe_status = classify_probe_entry(active_names, DEFAULT_PROBE_NAME)

    sfo_record: dict[str, Any] | None = None
    sfo_pack_path: Path | None = None
    if profile == "VANILLA":
        extras = [name for name in active_names if probe_entry is None or name.casefold() != probe_entry.casefold()]
        if extras:
            raise NativeChurnProfileError(f"vanilla churn profile rejects every non-probe active mod: {extras}")
        if probe_entry is None and active_names:
            raise NativeChurnProfileError(f"vanilla churn profile could not bind active entries: {active_names}")
    else:
        non_probe = [name for name in active_names if probe_entry is None or name.casefold() != probe_entry.casefold()]
        if len(non_probe) != 1:
            raise NativeChurnProfileError(
                f"SFO churn profile requires exactly one non-probe active pack; found {non_probe}"
            )
        steamapps = derive_steamapps_root(game_root)
        sfo_pack = _resolve_sfo_pack(steamapps, non_probe[0], sfo_workshop_id)
        sfo_pack_path = sfo_pack.resolve()
        sfo_record = {
            "workshop_id": sfo_workshop_id,
            "pack_name": sfo_pack.name,
            "size_bytes": sfo_pack.stat().st_size,
            "sha256": sha256(sfo_pack),
        }

    used_bytes = used_mods_path.read_bytes()
    public: dict[str, Any] = {
        "contract": CONTRACT,
        "profile": profile,
        "binding_status": "BOUND_PRELAUNCH_WITH_RUNTIME_PROBE_CONFIRMATION_REQUIRED",
        "authority": "NO_ORDERS",
        "application_authority": "PROHIBITED",
        "game": {
            "exe_name": exe.name,
            "exe_size_bytes": exe.stat().st_size,
            "exe_sha256": sha256(exe),
        },
        "probe": {
            "pack_name": probe_path.name,
            "size_bytes": probe_path.stat().st_size,
            "sha256": sha256(probe_path),
            "launcher_binding": probe_status,
            "active_entry": probe_entry,
            "runtime_marker_required": True,
        },
        "sfo": sfo_record,
        "launcher": {
            "used_mods_source_kind": source_kind,
            "used_mods_sha256": hashlib.sha256(used_bytes).hexdigest(),
            "active_pack_entries": active_names,
        },
        "campaign_protocol": {
            "campaign_key": campaign_key,
            "observer_faction": observer_faction,
            "campaign_difficulty": campaign_difficulty,
            "battle_difficulty": battle_difficulty,
            "player_action_protocol": "PASSIVE_NO_VOLUNTARY_CAMPAIGN_ORDERS",
        },
    }
    public["binding_sha256"] = hashlib.sha256(
        json.dumps(public, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()

    private = {
        "contract": CONTRACT,
        "public_binding_sha256": public["binding_sha256"],
        "game_root": str(game_root),
        "probe_path": str(probe_path),
        "used_mods_path": str(used_mods_path),
        "appdata_root": str(appdata_root.resolve()),
        "sfo_pack_path": str(sfo_pack_path) if sfo_pack_path is not None else None,
    }
    return public, private


def main() -> int:
    parser = argparse.ArgumentParser(description="Bind an exact vanilla/SFO profile for the v0.2L native directional-churn capture.")
    parser.add_argument("--profile", choices=("VANILLA", "SFO"), required=True)
    parser.add_argument("--game-root", type=Path, required=True)
    parser.add_argument("--appdata-root", type=Path, required=True)
    parser.add_argument("--probe-path", type=Path, required=True)
    parser.add_argument("--campaign-difficulty", default="Legendary")
    parser.add_argument("--battle-difficulty", default="Very Hard")
    parser.add_argument("--observer-faction", default="wh_main_emp_empire")
    parser.add_argument("--campaign-key", default="IMMORTAL_EMPIRES_KARL_FRANZ")
    parser.add_argument("--sfo-workshop-id", default=DEFAULT_SFO_WORKSHOP_ID)
    parser.add_argument("--public-output", type=Path, required=True)
    parser.add_argument("--private-output", type=Path, required=True)
    args = parser.parse_args()
    public, private = build_profile_binding(
        profile=args.profile,
        game_root=args.game_root,
        appdata_root=args.appdata_root,
        probe_path=args.probe_path,
        campaign_difficulty=args.campaign_difficulty,
        battle_difficulty=args.battle_difficulty,
        observer_faction=args.observer_faction,
        campaign_key=args.campaign_key,
        sfo_workshop_id=args.sfo_workshop_id,
    )
    args.public_output.parent.mkdir(parents=True, exist_ok=True)
    args.private_output.parent.mkdir(parents=True, exist_ok=True)
    args.public_output.write_text(json.dumps(public, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.private_output.write_text(json.dumps(private, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(public, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
