from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "runtime_probe" / "tools"))
from build_probe_packs import build_manifest
from verify_native_diagnostic_profile import PROBE_NAME, build_profile_binding, sha256

MINIMUM_TURNS = 6


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
            for hive, key_path, value_name in (
                (winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam", "SteamPath"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam", "InstallPath"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam", "InstallPath"),
            ):
                try:
                    with winreg.OpenKey(hive, key_path) as handle:
                        value, _ = winreg.QueryValueEx(handle, value_name)
                    if value:
                        steam_roots.append(Path(str(value)))
                except OSError:
                    pass
        except ImportError:
            pass
    libraries: list[Path] = []
    seen: set[str] = set()
    for steam_root in steam_roots:
        candidates = [steam_root]
        vdf = steam_root / "steamapps" / "libraryfolders.vdf"
        if vdf.is_file():
            try:
                text = vdf.read_text(encoding="utf-8-sig", errors="replace")
                candidates.extend(Path(match.group(1).replace("\\\\", "\\")) for match in re.finditer(r'"path"\s*"([^"]+)"', text, flags=re.IGNORECASE))
            except OSError:
                pass
        for library in candidates:
            key = str(library).casefold()
            if key not in seen:
                seen.add(key)
                libraries.append(library)
    return libraries


def resolve_game_root(explicit: Path | None) -> Path:
    if explicit is not None:
        root = explicit.expanduser().resolve()
        if (root / "Warhammer3.exe").is_file():
            return root
        raise ValueError(f"explicit WH3 game root is invalid: {root}")
    for library in _steam_library_roots():
        root = library / "steamapps" / "common" / "Total War WARHAMMER III"
        if (root / "Warhammer3.exe").is_file():
            return root.resolve()
    raise ValueError("WH3 game root could not be auto-discovered; rerun with -GameRoot.")

def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def prepare(game_root: Path, appdata_root: Path, assume_yes: bool = False) -> dict:
    stage = REPO_ROOT / "local_inputs" / "runtime_probe" / "native_diagnostic_staged"
    record = build_manifest(REPO_ROOT, REPO_ROOT / "runtime_probe/manifests/native_diagnostic_pack.json", stage)
    if record["probe_kind"] != "native_diagnostic" or record["save_mutation"] or record["gameplay_mutation"]:
        raise ValueError("diagnostic probe manifest authority changed")
    staged = stage / PROBE_NAME
    installed = game_root / "data" / PROBE_NAME
    installed.parent.mkdir(parents=True, exist_ok=True)
    if not installed.is_file() or sha256(installed) != sha256(staged):
        if not assume_yes:
            answer = input("Copy the read-only, research-only native diagnostic probe into WH3\\data? Type YES: ").strip()
            if answer != "YES": raise ValueError("owner confirmation not provided")
        shutil.copy2(staged, installed)
    if not assume_yes:
        print(f"\nOpen the WH3 launcher and enable ONLY {PROBE_NAME}. Disable every other mod, then close the launcher.")
        if input("Type READY when the launcher profile is saved: ").strip().upper() != "READY":
            raise ValueError("launcher profile not confirmed")
    public, private = build_profile_binding(game_root=game_root, appdata_root=appdata_root, probe_path=installed)
    run_root = REPO_ROOT / "local_inputs/runtime_probe/native_diagnostic_sessions" / f"vanilla_{stamp()}"
    run_root.mkdir(parents=True, exist_ok=True)
    pub_path = run_root / "profile_binding_public.json"
    priv_path = run_root / "profile_binding_private.json"
    pub_path.write_text(json.dumps(public, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    priv_path.write_text(json.dumps(private, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    log = game_root / "transcendence_native_diagnostic_log.txt"
    archived = None
    if log.is_file():
        archive_dir = REPO_ROOT / "local_inputs/runtime_probe/native_diagnostic_log_archives"
        archive_dir.mkdir(parents=True, exist_ok=True)
        archive = archive_dir / f"before_{stamp()}.txt"
        shutil.copy2(log, archive)
        archived = {"sha256": sha256(archive), "size_bytes": archive.stat().st_size}
        log.unlink()
    prepared = {
        "contract":"NATIVE_CAI_DIAGNOSTIC_PREPARED_SESSION_V1",
        "profile_binding_public":str(pub_path),
        "profile_binding_private":str(priv_path),
        "game_root":str(game_root),
        "appdata_root":str(appdata_root),
        "installed_probe":str(installed),
        "runtime_log":str(log),
        "minimum_human_turn_starts":MINIMUM_TURNS,
        "previous_log":archived,
        "authority":"NO_ORDERS",
        "application_authority":"PROHIBITED",
        "research_visibility":"PRIVILEGED_OMNISCIENT_DIAGNOSTIC",
        "application_eligible":False,
    }
    prepared_path = run_root / "prepared_session_private.json"
    prepared_path.write_text(json.dumps(prepared, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    latest = REPO_ROOT / "local_inputs/runtime_probe/native_diagnostic_sessions/latest.json"
    latest.write_text(json.dumps({"prepared_session":str(prepared_path)}, indent=2)+"\n", encoding="utf-8")
    return prepared


def main() -> int:
    parser=argparse.ArgumentParser(description="Prepare v0.2M research-only native CAI diagnostic capture")
    parser.add_argument("--game-root", type=Path)
    parser.add_argument("--appdata-root", type=Path, default=Path(os.environ.get("APPDATA", "")))
    parser.add_argument("--yes", action="store_true")
    args=parser.parse_args()
    if not str(args.appdata_root): raise ValueError("APPDATA unavailable")
    game_root=resolve_game_root(args.game_root)
    result=prepare(game_root, args.appdata_root.resolve(), args.yes)
    print("\nNATIVE DIAGNOSTIC CAPTURE PREPARED")
    print("Start a NEW disposable Karl Franz Immortal Empires campaign on Legendary / Very Hard.")
    print(f"Advance through at least {result['minimum_human_turn_starts']} consecutive Reikland turn starts.")
    print("You may play normally; this run qualifies telemetry density only and is not a behavioral verdict.")
    print("Exit WH3 completely, then run Collect-NativeDiagnosticCapture.ps1.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
