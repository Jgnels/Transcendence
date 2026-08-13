from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

WORKSHOP_APP_ID = "1142710"
DEFAULT_SFO_WORKSHOP_ID = "2792731173"
DEFAULT_PROBE_NAME = "transcendence_shadow_probe.pack"
PROBE_LAUNCHER_DECORATORS = "@!~"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _normalize_working_directory(value: str, *, line_no: int) -> str:
    normalized = value.strip().replace("\\", "/")
    if not normalized:
        raise ValueError(f"empty add_working_directory path on line {line_no}")
    is_drive_absolute = re.fullmatch(r"[A-Za-z]:/.*", normalized) is not None
    is_unc_absolute = normalized.startswith("//") and len(normalized.split("/")) >= 4
    if not (is_drive_absolute or is_unc_absolute):
        raise ValueError(
            f"add_working_directory must use an absolute Windows path on line {line_no}: {value!r}"
        )
    components = [part for part in normalized.split("/") if part and not part.endswith(":")]
    if any(part in {".", ".."} for part in components):
        raise ValueError(f"unsafe add_working_directory traversal on line {line_no}: {value!r}")
    return normalized.rstrip("/").casefold()


def parse_used_mods(text: str) -> list[str]:
    """Parse the strict WH3 launch-script subset used for active mods.

    Current CA launcher output may include absolute ``add_working_directory``
    directives before ``mod`` directives. Working directories affect pack lookup
    in WH3 but are not active packs themselves, so they are syntax-validated and
    excluded from the returned load-order list. Every other directive fails closed.
    """
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
                raise ValueError(f"unsafe or non-pack mod entry on line {line_no}: {name!r}")
            key = name.casefold()
            if any(existing.casefold() == key for existing in entries):
                raise ValueError(f"duplicate active mod entry: {name}")
            entries.append(name)
            continue

        working_match = re.fullmatch(
            r'add_working_directory\s+"([^"]+)"\s*;', line, flags=re.IGNORECASE
        )
        if working_match:
            key = _normalize_working_directory(working_match.group(1), line_no=line_no)
            if key in working_directories:
                raise ValueError(f"duplicate add_working_directory directive on line {line_no}")
            working_directories.add(key)
            continue

        raise ValueError(f"unsupported used_mods.txt line {line_no}: {raw!r}")
    if not entries:
        raise ValueError("used_mods.txt contains no active pack entries")
    return entries




def classify_probe_entry(active_names: list[str], probe_name: str = DEFAULT_PROBE_NAME) -> tuple[str | None, str]:
    """Resolve the probe entry without treating prelaunch launcher materialization as universal.

    Some launcher paths preserve a load-order decorator on a local pack name, while
    others do not materialize the local pack in ``used_mods.txt`` until WH3 starts.
    Exact and safely decorated names are accepted. Absence is explicitly deferred to
    the runtime marker and exact prepared-pack hash; unrelated aliases still fail.
    """
    exact: list[str] = []
    decorated: list[str] = []
    expected = probe_name.casefold()
    for name in active_names:
        key = name.casefold()
        if key == expected:
            exact.append(name)
            continue
        stripped = key.lstrip(PROBE_LAUNCHER_DECORATORS)
        if stripped == expected and len(stripped) < len(key):
            decorated.append(name)
    matches = exact + decorated
    if len(matches) > 1:
        raise ValueError(f"the active mod list contains multiple Transcendence shadow probe entries: {matches}")
    if exact:
        return exact[0], "EXACT_ACTIVE_ENTRY"
    if decorated:
        return decorated[0], "DECORATED_ACTIVE_ALIAS"
    return None, "DEFERRED_RUNTIME_MARKER"


def used_mods_candidates(*, game_root: Path, appdata_root: Path) -> list[tuple[str, Path]]:
    game_root = game_root.resolve()
    appdata_root = appdata_root.resolve()
    return [
        ("GAME_ROOT", game_root / "used_mods.txt"),
        (
            "APPDATA_STEAM",
            appdata_root / "The Creative Assembly" / "Warhammer3" / "scripts" / "used_mods.txt",
        ),
        (
            "APPDATA_EOS",
            appdata_root / "The Creative Assembly" / "Warhammer3" / "EOS" / "scripts" / "used_mods.txt",
        ),
        (
            "APPDATA_GDK",
            appdata_root / "The Creative Assembly" / "Warhammer3" / "GDK" / "scripts" / "used_mods.txt",
        ),
    ]


def discover_used_mods_path(*, game_root: Path, appdata_root: Path) -> tuple[Path, str, list[str]]:
    observed: list[tuple[int, str, Path, list[str]]] = []
    candidates = used_mods_candidates(game_root=game_root, appdata_root=appdata_root)
    for priority, (source_kind, path) in enumerate(candidates):
        if not path.is_file():
            continue
        entries = parse_used_mods(path.read_text(encoding="utf-8-sig"))
        observed.append((priority, source_kind, path.resolve(), entries))

    if not observed:
        rendered = ", ".join(str(path) for _, path in candidates)
        raise ValueError(f"used_mods.txt was not found in any supported location: {rendered}")

    semantic_sets = {tuple(entry.casefold() for entry in entries) for _, _, _, entries in observed}
    if len(semantic_sets) != 1:
        details = "; ".join(
            f"{source_kind}={path} -> {entries}"
            for _, source_kind, path, entries in observed
        )
        raise ValueError(f"conflicting used_mods.txt copies were found: {details}")

    _, source_kind, selected, entries = min(observed, key=lambda item: item[0])
    return selected, source_kind, entries


def _vdf_tokens(text: str) -> list[str]:
    tokens: list[str] = []
    index = 0
    while index < len(text):
        char = text[index]
        if char.isspace():
            index += 1
            continue
        if text.startswith("//", index):
            end = text.find("\n", index)
            index = len(text) if end < 0 else end + 1
            continue
        if char in "{}":
            tokens.append(char)
            index += 1
            continue
        if char != '"':
            raise ValueError(f"unsupported VDF token near character {index}")
        index += 1
        value: list[str] = []
        while index < len(text):
            char = text[index]
            if char == "\\" and index + 1 < len(text):
                value.append(text[index + 1])
                index += 2
                continue
            if char == '"':
                index += 1
                break
            value.append(char)
            index += 1
        else:
            raise ValueError("unterminated VDF string")
        tokens.append("".join(value))
    return tokens


def parse_vdf(text: str) -> dict[str, Any]:
    tokens = _vdf_tokens(text)
    cursor = 0

    def parse_object(expect_close: bool) -> dict[str, Any]:
        nonlocal cursor
        result: dict[str, Any] = {}
        while cursor < len(tokens):
            token = tokens[cursor]
            if token == "}":
                if not expect_close:
                    raise ValueError("unexpected VDF close brace")
                cursor += 1
                return result
            if token == "{":
                raise ValueError("unexpected VDF open brace")
            key = token
            cursor += 1
            if cursor >= len(tokens):
                raise ValueError(f"missing VDF value for {key!r}")
            if tokens[cursor] == "{":
                cursor += 1
                value: Any = parse_object(True)
            elif tokens[cursor] == "}":
                raise ValueError(f"missing VDF value for {key!r}")
            else:
                value = tokens[cursor]
                cursor += 1
            result[key] = value
        if expect_close:
            raise ValueError("unterminated VDF object")
        return result

    parsed = parse_object(False)
    if cursor != len(tokens):
        raise ValueError("trailing VDF tokens")
    return parsed


def derive_steamapps_root(game_root: Path) -> Path:
    resolved = game_root.resolve()
    for candidate in (resolved, *resolved.parents):
        if candidate.name.casefold() == "steamapps":
            return candidate
    raise ValueError("could not derive steamapps root from the WH3 installation path")


def _find_case_insensitive(root: Path, filename: str) -> list[Path]:
    key = filename.casefold()
    return sorted(
        (path for path in root.rglob("*.pack") if path.name.casefold() == key),
        key=lambda path: str(path).casefold(),
    )


def _read_workshop_metadata(steamapps_root: Path, workshop_id: str) -> dict[str, Any]:
    acf = steamapps_root / "workshop" / f"appworkshop_{WORKSHOP_APP_ID}.acf"
    if not acf.is_file():
        return {
            "acf_present": False,
            "manifest_id": None,
            "time_updated_unix": None,
            "reported_size_bytes": None,
        }
    parsed = parse_vdf(acf.read_text(encoding="utf-8-sig"))
    root = parsed.get("AppWorkshop", {})
    item: Any = {}
    if isinstance(root, dict):
        for container_name in ("WorkshopItemsInstalled", "WorkshopItemDetails"):
            container = root.get(container_name, {})
            if isinstance(container, dict) and isinstance(container.get(workshop_id), dict):
                item = container[workshop_id]
                break
    if not isinstance(item, dict):
        item = {}

    def optional_int(name: str) -> int | None:
        raw = item.get(name)
        if raw is None:
            return None
        try:
            return int(str(raw))
        except ValueError:
            return None

    return {
        "acf_present": True,
        "acf_sha256": sha256(acf),
        "manifest_id": item.get("manifest"),
        "time_updated_unix": optional_int("timeupdated"),
        "reported_size_bytes": optional_int("size"),
    }


def build_environment_manifests(
    *,
    game_root: Path,
    used_mods_path: Path,
    shadow_pack_path: Path,
    sfo_workshop_id: str = DEFAULT_SFO_WORKSHOP_ID,
    steamapps_root: Path | None = None,
    campaign_difficulty: str,
    battle_difficulty: str,
    ironman: bool,
    battle_realism: bool,
    battlefield_limitations: str,
    faction: str,
    used_mods_source_kind: str = "EXPLICIT",
    probe_name: str = DEFAULT_PROBE_NAME,
) -> tuple[dict[str, Any], dict[str, Any]]:
    game_root = game_root.resolve()
    used_mods_path = used_mods_path.resolve()
    shadow_pack_path = shadow_pack_path.resolve()
    if not game_root.is_dir():
        raise ValueError(f"WH3 installation path is missing: {game_root}")
    if not used_mods_path.is_file():
        raise ValueError(f"used_mods.txt is missing: {used_mods_path}")
    if not shadow_pack_path.is_file():
        raise ValueError(f"installed shadow probe is missing: {shadow_pack_path}")
    if shadow_pack_path.name.casefold() != probe_name.casefold():
        raise ValueError(f"unexpected probe filename: {shadow_pack_path.name}")

    steamapps = (steamapps_root or derive_steamapps_root(game_root)).resolve()
    sfo_root = steamapps / "workshop" / "content" / WORKSHOP_APP_ID / sfo_workshop_id
    if not sfo_root.is_dir():
        raise ValueError(f"SFO Workshop item directory is missing: {sfo_root}")

    active_names = parse_used_mods(used_mods_path.read_text(encoding="utf-8-sig"))
    probe_entry, probe_binding_status = classify_probe_entry(active_names, probe_name)

    sfo_candidates: list[tuple[str, Path]] = []
    for name in active_names:
        if probe_entry is not None and name.casefold() == probe_entry.casefold():
            continue
        matches = _find_case_insensitive(sfo_root, name)
        if len(matches) == 1:
            sfo_candidates.append((name, matches[0]))
        elif len(matches) > 1:
            raise ValueError(f"ambiguous SFO pack filename {name!r}: {len(matches)} matches")
    if len(sfo_candidates) != 1:
        raise ValueError(
            "SFO-only certification requires exactly one active pack resolved inside Workshop item "
            f"{sfo_workshop_id}; found {len(sfo_candidates)}; active entries were {active_names}"
        )
    sfo_name, sfo_pack = sfo_candidates[0]
    allowed = {sfo_name.casefold()}
    if probe_entry is not None:
        allowed.add(probe_entry.casefold())
    extras = [name for name in active_names if name.casefold() not in allowed]
    if extras:
        raise ValueError(f"SFO-only certification rejects additional active mods: {extras}")
    if probe_entry is None and len(active_names) != 1:
        raise ValueError(
            "the Transcendence probe entry is absent and the remaining launcher list is not SFO-only; "
            f"active entries were {active_names}"
        )

    exe = game_root / "Warhammer3.exe"
    if not exe.is_file():
        raise ValueError(f"WH3 executable is missing: {exe}")
    workshop = _read_workshop_metadata(steamapps, sfo_workshop_id)

    active_records = []
    for index, name in enumerate(active_names):
        is_probe = probe_entry is not None and name.casefold() == probe_entry.casefold()
        path = shadow_pack_path if is_probe else sfo_pack
        active_records.append(
            {
                "load_order_index": index,
                "name": name,
                "canonical_pack_name": probe_name if is_probe else sfo_pack.name,
                "size_bytes": path.stat().st_size,
                "sha256": sha256(path),
                "role": "READ_ONLY_TRANSCENDENCE_PROBE"
                if is_probe
                else "SFO_TOTAL_OVERHAUL",
            }
        )

    deferred_probe = probe_entry is None
    profile_id = (
        "SFO_ONLY_PLUS_READ_ONLY_PROBE_RUNTIME_DEFERRED"
        if deferred_probe
        else "SFO_ONLY_PLUS_READ_ONLY_PROBE"
    )
    public: dict[str, Any] = {
        "schema_version": 2,
        "profile_id": profile_id,
        "evidence_label": "OWNER_MACHINE_PREFLIGHT",
        "captured_at_utc": None,
        "game": {
            "app_id": WORKSHOP_APP_ID,
            "executable_name": exe.name,
            "executable_size_bytes": exe.stat().st_size,
            "executable_sha256": sha256(exe),
        },
        "sfo": {
            "workshop_id": sfo_workshop_id,
            "pack_name": sfo_pack.name,
            "pack_size_bytes": sfo_pack.stat().st_size,
            "pack_sha256": sha256(sfo_pack),
            **workshop,
        },
        "active_mods": active_records,
        "active_mod_count": len(active_records),
        "probe_binding": {
            "status": probe_binding_status,
            "launcher_entry": probe_entry,
            "runtime_confirmation_required": deferred_probe,
        },
        "expected_probe": {
            "canonical_pack_name": probe_name,
            "pack_size_bytes": shadow_pack_path.stat().st_size,
            "pack_sha256": sha256(shadow_pack_path),
            "gameplay_mutation": False,
            "save_mutation": False,
        },
        "used_mods_sha256": sha256(used_mods_path),
        "used_mods_source_kind": used_mods_source_kind,
        "settings": {
            "campaign_difficulty": campaign_difficulty,
            "battle_difficulty": battle_difficulty,
            "ironman": bool(ironman),
            "battle_realism": bool(battle_realism),
            "battlefield_limitations": battlefield_limitations,
            "faction": faction,
        },
        "authority": {
            "active_mod_list_modified": False,
            "save_modified": False,
            "orders_emitted": False,
        },
        "certification_scope": [
            "exact_owner_machine_wh3_executable",
            "exact_sfo_workshop_pack",
            (
                "sfo_only_launcher_state_plus_runtime_probe_confirmation_required"
                if deferred_probe
                else "exact_two-pack_launcher_state"
            ),
            "exact_installed_read_only_transcendence_probe",
        ],
        "limitations": [
            (
                "The prelaunch launcher-state file did not materialize the local probe entry; "
                "the exact prepared-pack hash and runtime markers must confirm loading after WH3 starts."
                if deferred_probe
                else "Preflight identity does not prove that the expected packs successfully loaded in WH3."
            ),
            "One run cannot generalize across later SFO or WH3 updates, additional mods, factions, or battle types.",
        ],
    }
    public_bytes = json.dumps(public, sort_keys=True, separators=(",", ":")).encode("utf-8")
    public["profile_digest"] = hashlib.sha256(public_bytes).hexdigest()

    private = {
        **public,
        "private_paths": {
            "game_root": str(game_root),
            "game_executable": str(exe),
            "steamapps_root": str(steamapps),
            "sfo_workshop_root": str(sfo_root),
            "sfo_pack": str(sfo_pack),
            "shadow_pack": str(shadow_pack_path),
            "used_mods": str(used_mods_path),
        },
    }
    return private, public


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture an exact SFO-only WH3 environment profile.")
    parser.add_argument("--game-root", type=Path, required=True)
    parser.add_argument("--used-mods", type=Path)
    parser.add_argument("--appdata-root", type=Path)
    parser.add_argument("--shadow-pack", type=Path, required=True)
    parser.add_argument("--probe-name", default=DEFAULT_PROBE_NAME)
    parser.add_argument("--steamapps-root", type=Path)
    parser.add_argument("--sfo-workshop-id", default=DEFAULT_SFO_WORKSHOP_ID)
    parser.add_argument("--campaign-difficulty", default="Legendary")
    parser.add_argument("--battle-difficulty", default="Very Hard")
    parser.add_argument("--ironman", choices=("true", "false"), default="true")
    parser.add_argument("--battle-realism", choices=("true", "false"), default="true")
    parser.add_argument("--battlefield-limitations", default="OWNER_CONFIGURED")
    parser.add_argument("--faction", default="Karl Franz / Reikland")
    parser.add_argument("--private-output", type=Path, required=True)
    parser.add_argument("--public-output", type=Path, required=True)
    args = parser.parse_args()
    if args.used_mods is not None:
        used_mods_path = args.used_mods
        used_mods_source_kind = "EXPLICIT"
    else:
        appdata_root = args.appdata_root
        if appdata_root is None:
            appdata_value = os.environ.get("APPDATA")
            if not appdata_value:
                raise ValueError("APPDATA is unavailable; supply --appdata-root or --used-mods")
            appdata_root = Path(appdata_value)
        used_mods_path, used_mods_source_kind, _ = discover_used_mods_path(
            game_root=args.game_root,
            appdata_root=appdata_root,
        )
    private, public = build_environment_manifests(
        game_root=args.game_root,
        used_mods_path=used_mods_path,
        shadow_pack_path=args.shadow_pack,
        steamapps_root=args.steamapps_root,
        sfo_workshop_id=args.sfo_workshop_id,
        campaign_difficulty=args.campaign_difficulty,
        battle_difficulty=args.battle_difficulty,
        ironman=args.ironman == "true",
        battle_realism=args.battle_realism == "true",
        battlefield_limitations=args.battlefield_limitations,
        faction=args.faction,
        used_mods_source_kind=used_mods_source_kind,
        probe_name=args.probe_name,
    )
    args.private_output.parent.mkdir(parents=True, exist_ok=True)
    args.public_output.parent.mkdir(parents=True, exist_ok=True)
    args.private_output.write_text(json.dumps(private, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.public_output.write_text(json.dumps(public, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(public, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
