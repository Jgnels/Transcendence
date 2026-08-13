from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from prepare_native_diagnostic_capture import _steam_library_roots
from verify_native_diagnostic_profile import PROBE_NAME, discover_used_mods, sha256

SFO_WORKSHOP_ID = "2792731173"
SFO_PACK_NAME = "sfo_grimhammer_3_main.pack"
SFO_EXPECTED_SHA256 = "ae20a0a08037aa3ebcbe7461d2589fc28dc15a5fe5d9ca4c0a9d0ff0a26da603"
CONTRACT = "NATIVE_CAI_DIAGNOSTIC_SFO_PROFILE_BINDING_V1"


class NativeDiagnosticSfoProfileError(ValueError):
    pass


def discover_sfo_pack(explicit: Path | None = None) -> Path:
    candidates: list[Path] = []
    if explicit is not None:
        candidates.append(explicit.expanduser())
    for library in _steam_library_roots():
        candidates.append(library / "steamapps" / "workshop" / "content" / "1142710" / SFO_WORKSHOP_ID / SFO_PACK_NAME)
    seen: set[str] = set()
    existing: list[Path] = []
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        key = str(resolved).casefold()
        if key in seen:
            continue
        seen.add(key)
        if resolved.is_file() and resolved.name.casefold() == SFO_PACK_NAME.casefold():
            existing.append(resolved)
    if not existing:
        raise NativeDiagnosticSfoProfileError(
            f"SFO pack {SFO_PACK_NAME} (Workshop {SFO_WORKSHOP_ID}) was not found; rerun with -SfoPackPath if Steam autodiscovery misses it"
        )
    hashes = {sha256(path) for path in existing}
    if len(hashes) != 1:
        raise NativeDiagnosticSfoProfileError("multiple discovered SFO pack copies disagree by SHA-256")
    return sorted(existing, key=lambda p: str(p).casefold())[0]


def build_sfo_profile_binding(
    *,
    game_root: Path,
    appdata_root: Path,
    probe_path: Path,
    sfo_pack_path: Path,
    profile_name: str,
    player_action_protocol: str,
    expected_sfo_sha256: str = SFO_EXPECTED_SHA256,
) -> tuple[dict[str, Any], dict[str, Any]]:
    game_root = game_root.resolve()
    probe_path = probe_path.resolve()
    sfo_pack_path = sfo_pack_path.resolve()
    exe = game_root / "Warhammer3.exe"
    if not exe.is_file():
        raise NativeDiagnosticSfoProfileError("Warhammer3.exe is missing")
    if not probe_path.is_file() or probe_path.name.casefold() != PROBE_NAME.casefold():
        raise NativeDiagnosticSfoProfileError("native diagnostic probe is missing or misnamed")
    if not sfo_pack_path.is_file() or sfo_pack_path.name.casefold() != SFO_PACK_NAME.casefold():
        raise NativeDiagnosticSfoProfileError("SFO main pack is missing or misnamed")
    actual_sfo_sha = sha256(sfo_pack_path)
    if actual_sfo_sha != expected_sfo_sha256:
        raise NativeDiagnosticSfoProfileError(
            f"SFO pack identity drifted: expected {expected_sfo_sha256}, observed {actual_sfo_sha}. Stop and reconcile the new SFO build before benchmarking."
        )

    used_path, source_kind, active = discover_used_mods(game_root, appdata_root)
    expected_names = {PROBE_NAME.casefold(), SFO_PACK_NAME.casefold()}
    observed_names = {item.casefold() for item in active}
    if observed_names != expected_names or len(active) != 2:
        raise NativeDiagnosticSfoProfileError(
            f"SFO benchmark requires exactly {SFO_PACK_NAME} + {PROBE_NAME}; observed {active}"
        )

    public: dict[str, Any] = {
        "contract": CONTRACT,
        "profile": profile_name,
        "authority": "NO_ORDERS",
        "application_authority": "PROHIBITED",
        "research_visibility": "PRIVILEGED_OMNISCIENT_DIAGNOSTIC",
        "application_eligible": False,
        "game": {"exe_name": exe.name, "size_bytes": exe.stat().st_size, "sha256": sha256(exe)},
        "probe": {"pack_name": probe_path.name, "size_bytes": probe_path.stat().st_size, "sha256": sha256(probe_path)},
        "sfo": {
            "workshop_id": SFO_WORKSHOP_ID,
            "pack_name": sfo_pack_path.name,
            "size_bytes": sfo_pack_path.stat().st_size,
            "sha256": actual_sfo_sha,
            "expected_sha256": expected_sfo_sha256,
        },
        "launcher": {
            "used_mods_source_kind": source_kind,
            "used_mods_sha256": hashlib.sha256(used_path.read_bytes()).hexdigest(),
            "active_pack_entries": active,
        },
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
        "sfo_pack_path": str(sfo_pack_path),
        "used_mods_path": str(used_path),
        "appdata_root": str(appdata_root.resolve()),
    }
    return public, private
