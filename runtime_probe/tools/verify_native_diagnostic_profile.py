from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

PROBE_NAME = "transcendence_native_diagnostic_probe.pack"
CONTRACT = "NATIVE_CAI_DIAGNOSTIC_PROFILE_BINDING_V1"


class NativeDiagnosticProfileError(ValueError):
    pass


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _parse_used_mods(text: str) -> list[str]:
    entries: list[str] = []
    for line_no, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("//"):
            continue
        match = re.fullmatch(r'mod\s+"([^"]+)"\s*;', line, flags=re.IGNORECASE)
        if match:
            name = match.group(1)
            if Path(name).name != name or not name.lower().endswith(".pack"):
                raise NativeDiagnosticProfileError(f"unsafe mod entry on line {line_no}: {name!r}")
            entries.append(name)
            continue
        if re.fullmatch(r'add_working_directory\s+"[^"]+"\s*;', line, flags=re.IGNORECASE):
            continue
        raise NativeDiagnosticProfileError(f"unsupported used_mods line {line_no}: {raw!r}")
    if len({item.casefold() for item in entries}) != len(entries):
        raise NativeDiagnosticProfileError("duplicate active mod entry")
    return entries


def discover_used_mods(game_root: Path, appdata_root: Path) -> tuple[Path, str, list[str]]:
    candidates = [
        ("GAME_ROOT", game_root / "used_mods.txt"),
        ("APPDATA", appdata_root / "The Creative Assembly" / "Warhammer3" / "scripts" / "used_mods.txt"),
    ]
    observed = []
    for priority, (kind, path) in enumerate(candidates):
        if path.is_file():
            observed.append((priority, kind, path.resolve(), _parse_used_mods(path.read_text(encoding="utf-8-sig"))))
    if not observed:
        raise NativeDiagnosticProfileError("used_mods.txt was not found in supported locations")
    semantic = {tuple(x.casefold() for x in rows) for _, _, _, rows in observed}
    if len(semantic) != 1:
        raise NativeDiagnosticProfileError("conflicting used_mods.txt copies were found")
    _, kind, path, rows = min(observed, key=lambda item: item[0])
    return path, kind, rows


def build_profile_binding(*, game_root: Path, appdata_root: Path, probe_path: Path, profile_name: str = "VANILLA_DIAGNOSTIC", player_action_protocol: str = "UNRESTRICTED_FOR_INSTRUMENTATION_QUALIFICATION_ONLY") -> tuple[dict[str, Any], dict[str, Any]]:
    game_root = game_root.resolve()
    probe_path = probe_path.resolve()
    exe = game_root / "Warhammer3.exe"
    if not exe.is_file():
        raise NativeDiagnosticProfileError("Warhammer3.exe is missing")
    if not probe_path.is_file() or probe_path.name.casefold() != PROBE_NAME.casefold():
        raise NativeDiagnosticProfileError("native diagnostic probe is missing or misnamed")
    used_path, source_kind, active = discover_used_mods(game_root, appdata_root)
    if [item.casefold() for item in active] != [PROBE_NAME.casefold()]:
        raise NativeDiagnosticProfileError(f"diagnostic vanilla profile requires exactly {PROBE_NAME}; observed {active}")
    public: dict[str, Any] = {
        "contract": CONTRACT,
        "profile": profile_name,
        "authority": "NO_ORDERS",
        "application_authority": "PROHIBITED",
        "research_visibility": "PRIVILEGED_OMNISCIENT_DIAGNOSTIC",
        "application_eligible": False,
        "game": {"exe_name": exe.name, "size_bytes": exe.stat().st_size, "sha256": sha256(exe)},
        "probe": {"pack_name": probe_path.name, "size_bytes": probe_path.stat().st_size, "sha256": sha256(probe_path)},
        "launcher": {"used_mods_source_kind": source_kind, "used_mods_sha256": hashlib.sha256(used_path.read_bytes()).hexdigest(), "active_pack_entries": active},
        "campaign_protocol": {
            "campaign_key": "IMMORTAL_EMPIRES_KARL_FRANZ",
            "observer_faction": "wh_main_emp_empire",
            "campaign_difficulty": "Legendary",
            "battle_difficulty": "Very Hard",
            "player_action_protocol": player_action_protocol,
        },
    }
    public["binding_sha256"] = hashlib.sha256(json.dumps(public, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    private = {
        "contract": CONTRACT,
        "public_binding_sha256": public["binding_sha256"],
        "game_root": str(game_root),
        "probe_path": str(probe_path),
        "used_mods_path": str(used_path),
        "appdata_root": str(appdata_root.resolve()),
    }
    return public, private
