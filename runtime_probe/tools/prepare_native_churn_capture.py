from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "runtime_probe" / "tools"))

from build_probe_packs import build_manifest
from verify_native_churn_profile import build_profile_binding

SESSION_CONTRACT = "NATIVE_CAI_DIRECTIONAL_CHURN_PREPARED_SESSION_V1"
DEFAULT_MINIMUM_TURNS = 12


class NativeChurnPreparationError(ValueError):
    pass


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _steam_library_roots() -> list[Path]:
    steam_roots: list[Path] = []
    for key in ("PROGRAMFILES(X86)", "PROGRAMFILES"):
        value = os.environ.get(key)
        if value:
            steam_roots.append(Path(value) / "Steam")
    steam_roots.append(Path(r"C:\Program Files (x86)\Steam"))

    if sys.platform == "win32":
        try:
            import winreg  # type: ignore

            registry_candidates = [
                (winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam", "SteamPath"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam", "InstallPath"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam", "InstallPath"),
            ]
            for hive, key_path, value_name in registry_candidates:
                try:
                    with winreg.OpenKey(hive, key_path) as key_handle:
                        value, _kind = winreg.QueryValueEx(key_handle, value_name)
                    if value:
                        steam_roots.append(Path(str(value)))
                except OSError:
                    continue
        except ImportError:
            pass

    libraries: list[Path] = []
    seen: set[str] = set()
    for steam_root in steam_roots:
        key = str(steam_root).casefold()
        if key not in seen:
            seen.add(key)
            libraries.append(steam_root)
        library_vdf = steam_root / "steamapps" / "libraryfolders.vdf"
        if not library_vdf.is_file():
            continue
        try:
            text = library_vdf.read_text(encoding="utf-8-sig", errors="replace")
        except OSError:
            continue
        for match in re.finditer(r'"path"\s*"([^"]+)"', text, flags=re.IGNORECASE):
            raw = match.group(1)
            library = Path(raw)
            library_key = str(library).casefold()
            if library_key not in seen:
                seen.add(library_key)
                libraries.append(library)
    return libraries


def resolve_game_root(explicit: Path | None, repo_root: Path = REPO_ROOT) -> Path:
    if explicit is not None:
        root = explicit.expanduser().resolve()
        if (root / "Warhammer3.exe").is_file():
            return root
        raise NativeChurnPreparationError(f"explicit WH3 game root is invalid: {root}")
    manifest = repo_root / "local_inputs" / "machine_profiles" / "gaming_laptop_private.json"
    if manifest.is_file():
        data = json.loads(manifest.read_text(encoding="utf-8-sig"))
        value = data.get("game", {}).get("install_path") if isinstance(data, dict) else None
        if value:
            root = Path(str(value)).expanduser()
            if (root / "Warhammer3.exe").is_file():
                return root.resolve()
    for library in _steam_library_roots():
        root = library / "steamapps" / "common" / "Total War WARHAMMER III"
        if (root / "Warhammer3.exe").is_file():
            return root.resolve()
    raise NativeChurnPreparationError(
        "WH3 game root could not be resolved from the private machine profile or Steam libraries. Supply --game-root."
    )


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _confirm(prompt: str, assume_yes: bool) -> None:
    if assume_yes:
        return
    answer = input(f"{prompt}\nType YES to continue: ").strip()
    if answer != "YES":
        raise NativeChurnPreparationError("owner confirmation was not provided")


def prepare_session(
    *,
    profile: str,
    game_root: Path,
    appdata_root: Path,
    minimum_turns: int = DEFAULT_MINIMUM_TURNS,
    campaign_difficulty: str = "Legendary",
    battle_difficulty: str = "Very Hard",
    assume_yes: bool = False,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    profile = profile.upper()
    if profile not in {"VANILLA", "SFO"}:
        raise NativeChurnPreparationError("profile must be VANILLA or SFO")
    if minimum_turns < 7:
        raise NativeChurnPreparationError("minimum_turns must be at least 7")
    game_root = game_root.resolve()
    appdata_root = appdata_root.resolve()

    stage_root = repo_root / "local_inputs" / "runtime_probe" / "native_churn_staged"
    shadow_manifest = repo_root / "runtime_probe" / "manifests" / "shadow_pack.json"
    shadow_row = build_manifest(repo_root, shadow_manifest, stage_root)
    if shadow_row.get("probe_kind") != "shadow":
        raise NativeChurnPreparationError("shadow manifest did not produce a shadow probe")
    if shadow_row.get("save_mutation") is not False or shadow_row.get("gameplay_mutation") is not False:
        raise NativeChurnPreparationError("shadow manifest mutation authority changed")
    staged_probe = stage_root / str(shadow_row["pack_name"])
    staged_sha = sha256(staged_probe)
    installed_probe = game_root / "data" / staged_probe.name
    installed_probe.parent.mkdir(parents=True, exist_ok=True)

    backup_path: Path | None = None
    if not installed_probe.is_file() or sha256(installed_probe) != staged_sha:
        _confirm(
            "The read-only Transcendence shadow probe must be copied into WH3\\data. This does not enable the mod or modify a save.",
            assume_yes,
        )
        if installed_probe.is_file():
            backup_root = repo_root / "local_inputs" / "runtime_probe" / "native_churn_backups" / _timestamp()
            backup_root.mkdir(parents=True, exist_ok=True)
            backup_path = backup_root / installed_probe.name
            shutil.copy2(installed_probe, backup_path)
        shutil.copy2(staged_probe, installed_probe)
    if sha256(installed_probe) != staged_sha:
        raise NativeChurnPreparationError("installed shadow probe hash does not match deterministic staged probe")

    if profile == "VANILLA":
        launcher_instruction = (
            "Open the WH3 launcher. Enable ONLY transcendence_shadow_probe.pack and disable every other mod. "
            "Close the launcher after the load order is saved."
        )
    else:
        launcher_instruction = (
            "Open the WH3 launcher. Enable ONLY SFO: Grimhammer III and transcendence_shadow_probe.pack; "
            "disable every other mod. Close the launcher after the load order is saved."
        )
    if not assume_yes:
        print("\n" + launcher_instruction)
        ready = input("Type READY after the launcher is configured exactly as above: ").strip().upper()
        if ready != "READY":
            raise NativeChurnPreparationError("launcher profile was not confirmed")

    session_root = repo_root / "local_inputs" / "runtime_probe" / "native_churn_sessions"
    stamp = _timestamp()
    run_root = session_root / f"{profile.lower()}_{stamp}"
    run_root.mkdir(parents=True, exist_ok=True)
    public_binding_path = run_root / "profile_binding_public.json"
    private_binding_path = run_root / "profile_binding_private.json"
    public_binding, private_binding = build_profile_binding(
        profile=profile,
        game_root=game_root,
        appdata_root=appdata_root,
        probe_path=installed_probe,
        campaign_difficulty=campaign_difficulty,
        battle_difficulty=battle_difficulty,
        observer_faction="wh_main_emp_empire",
        campaign_key="IMMORTAL_EMPIRES_KARL_FRANZ",
    )
    public_binding_path.write_text(json.dumps(public_binding, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    private_binding_path.write_text(json.dumps(private_binding, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    runtime_log = game_root / "transcendence_runtime_log.txt"
    archived_log: dict[str, Any] | None = None
    if runtime_log.is_file():
        archive_root = repo_root / "local_inputs" / "runtime_probe" / "native_churn_log_archives"
        archive_root.mkdir(parents=True, exist_ok=True)
        archive = archive_root / f"transcendence_runtime_log_before_{profile.lower()}_{stamp}.txt"
        shutil.copy2(runtime_log, archive)
        archived_log = {"path": str(archive), "sha256": sha256(archive), "size_bytes": archive.stat().st_size}
        runtime_log.unlink()

    prepared = {
        "contract": SESSION_CONTRACT,
        "prepared_at_utc": datetime.now(timezone.utc).isoformat(),
        "profile": profile,
        "minimum_turns": minimum_turns,
        "game_root": str(game_root),
        "runtime_log": str(runtime_log),
        "staged_probe": str(staged_probe),
        "staged_probe_sha256": staged_sha,
        "installed_probe": str(installed_probe),
        "installed_probe_sha256": sha256(installed_probe),
        "probe_backup": str(backup_path) if backup_path else None,
        "profile_binding_public": str(public_binding_path),
        "profile_binding_private": str(private_binding_path),
        "profile_binding_sha256": public_binding["binding_sha256"],
        "previous_runtime_log": archived_log,
        "campaign_protocol": public_binding["campaign_protocol"],
        "owner_run_instructions": [
            "Start a NEW disposable Karl Franz / Reikland Immortal Empires campaign.",
            f"Use {campaign_difficulty} campaign difficulty and {battle_difficulty} battle difficulty.",
            f"Observe at least {minimum_turns} consecutive Reikland turn starts.",
            "During the confirmatory observation window issue NO voluntary campaign orders: do not move armies/agents, recruit, change stance, initiate diplomacy, build, or spend resources.",
            "Only resolve mandatory prompts/battles needed for the campaign to continue; note any unavoidable deviation when collecting.",
            "Do not activate any additional mods during the run.",
            "Exit WH3 completely after the final observed turn start, then run the collection wrapper.",
        ],
        "authority": "NO_ORDERS",
        "application_authority": "PROHIBITED",
    }
    prepared_path = run_root / "prepared_session_private.json"
    prepared_path.write_text(json.dumps(prepared, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    latest = session_root / "latest.json"
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text(json.dumps({"prepared_session": str(prepared_path)}, indent=2) + "\n", encoding="utf-8")
    return prepared


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare a profile-bound, read-only v0.2L native directional-churn owner capture.")
    parser.add_argument("--profile", choices=("VANILLA", "SFO"), required=True)
    parser.add_argument("--game-root", type=Path)
    parser.add_argument("--appdata-root", type=Path, default=Path(os.environ.get("APPDATA", "")))
    parser.add_argument("--minimum-turns", type=int, default=DEFAULT_MINIMUM_TURNS)
    parser.add_argument("--campaign-difficulty", default="Legendary")
    parser.add_argument("--battle-difficulty", default="Very Hard")
    parser.add_argument("--yes", action="store_true", help="Noninteractive test mode; do not use casually on the owner machine.")
    args = parser.parse_args()
    if not str(args.appdata_root):
        raise NativeChurnPreparationError("APPDATA is unavailable; supply --appdata-root")
    game_root = resolve_game_root(args.game_root)
    prepared = prepare_session(
        profile=args.profile,
        game_root=game_root,
        appdata_root=args.appdata_root,
        minimum_turns=args.minimum_turns,
        campaign_difficulty=args.campaign_difficulty,
        battle_difficulty=args.battle_difficulty,
        assume_yes=args.yes,
    )
    print("\nNATIVE CHURN CAPTURE PREPARED")
    print(f"Profile: {prepared['profile']}")
    print(f"Profile binding SHA-256: {prepared['profile_binding_sha256']}")
    print("\nRun protocol:")
    for line in prepared["owner_run_instructions"]:
        print(f"- {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
