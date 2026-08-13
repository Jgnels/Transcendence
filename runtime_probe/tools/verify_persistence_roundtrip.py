from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Sequence

from parse_probe_log import canonical_json, parse_logs, summarize

PERSISTENCE_ENTRYPOINT = "transcendence_persistence_probe"
PERSISTENCE_PACK_NAME = "transcendence_persistence_probe.pack"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _loader_status(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    start = f"Executing mod function {PERSISTENCE_ENTRYPOINT}()"
    end = f"{PERSISTENCE_ENTRYPOINT}() executed successfully"
    missing = f"{PERSISTENCE_ENTRYPOINT}() not found"
    if start in text and end in text:
        return "SUCCESS"
    if missing in text:
        return "MISSING"
    return "UNKNOWN"


def _manifest_record(
    manifest_path: Path,
    *,
    expected_log_sha256: str,
) -> dict[str, object]:
    manifest = _load_json(manifest_path)
    collected_at = manifest.get("collected_at_utc")
    if not isinstance(collected_at, str) or not collected_at:
        raise ValueError(f"{manifest_path.name}: missing collected_at_utc")

    log_hashes = {
        str(record.get("sha256")).lower()
        for record in manifest.get("logs", [])
        if record.get("sha256")
    }
    if expected_log_sha256.lower() not in log_hashes:
        raise ValueError(
            f"{manifest_path.name}: manifest does not contain supplied log SHA-256"
        )

    pack_sha: str | None = None
    for record in manifest.get("installed_probe_packs", []):
        if record.get("name") == PERSISTENCE_PACK_NAME:
            value = record.get("installed_sha256")
            if isinstance(value, str):
                pack_sha = value.lower()
            break

    manifest_sha = sha256_file(manifest_path)
    collection_id = hashlib.sha256(
        canonical_json(
            {
                "manifest_sha256": manifest_sha,
                "collected_at_utc": collected_at,
                "log_sha256": expected_log_sha256.lower(),
            }
        )
    ).hexdigest()
    return {
        "manifest_name": manifest_path.name,
        "manifest_sha256": manifest_sha,
        "manifest_schema_version": manifest.get("schema_version"),
        "collected_at_utc": collected_at,
        "collection_id": collection_id,
        "persistence_pack_sha256": pack_sha,
    }


def _state_environment(state: dict[str, object]) -> tuple[object, ...]:
    return (
        state.get("campaign"),
        state.get("local_faction"),
        state.get("key_version"),
        state.get("is_multiplayer"),
    )


PERSISTENCE_TRANSPORT_KEYS = {
    "log_name",
    "manifest_name",
    "result_digest",
    "semantic_digest",
}


def persistence_semantic_projection(value: object) -> object:
    """Remove filenames and derived digests while preserving evidence identity.

    Evidence hashes, collection identifiers, timestamps, pack hashes, states,
    checks, and warnings remain in the projection. Renaming uploaded files
    therefore cannot change the semantic digest, while substituting different
    evidence still does.
    """

    if isinstance(value, dict):
        return {
            key: persistence_semantic_projection(item)
            for key, item in sorted(value.items())
            if key not in PERSISTENCE_TRANSPORT_KEYS
        }
    if isinstance(value, list):
        return [persistence_semantic_projection(item) for item in value]
    return value


def build_persistence_report(
    log_paths: Sequence[Path],
    *,
    evidence_manifest_paths: Sequence[Path] | None = None,
    pack_sha256s: Sequence[str] | None = None,
    expected_pack_sha256: str | None = None,
) -> dict[str, object]:
    if len(log_paths) != 2:
        raise ValueError("exactly two logs are required: fresh write, then reload")
    if evidence_manifest_paths is not None and len(evidence_manifest_paths) != 2:
        raise ValueError("exactly two evidence manifests are required")
    if pack_sha256s is not None and len(pack_sha256s) != 2:
        raise ValueError("pack_sha256s must contain exactly two values")

    runs: list[dict[str, object]] = []
    for index, path in enumerate(log_paths):
        summary = summarize(parse_logs([path]))
        sessions = summary["sessions"]
        isolated_persistence_session = (
            len(sessions) == 1
            and sessions[0]["probe_kind"] == "persistence"
        )
        states = summary["persistence_states"]
        exactly_one_state = len(states) == 1
        state = states[0] if exactly_one_state else None
        log_sha = sha256_file(path)

        manifest_record = None
        if evidence_manifest_paths is not None:
            manifest_record = _manifest_record(
                evidence_manifest_paths[index],
                expected_log_sha256=log_sha,
            )

        explicit_sha = (
            pack_sha256s[index].lower()
            if pack_sha256s is not None
            else None
        )
        manifest_sha = (
            manifest_record.get("persistence_pack_sha256")
            if manifest_record is not None
            else None
        )
        if explicit_sha and manifest_sha and explicit_sha != manifest_sha:
            raise ValueError(
                f"run {index + 1}: explicit persistence pack hash does not match manifest"
            )
        resolved_sha = manifest_sha or explicit_sha

        run: dict[str, object] = {
            "phase_index": index + 1,
            "expected_phase": "WRITE" if index == 0 else "RELOAD",
            "log_name": path.name,
            "log_sha256": log_sha,
            "log_size_bytes": path.stat().st_size,
            "isolated_persistence_session": isolated_persistence_session,
            "exactly_one_state": exactly_one_state,
            "state": state,
            "loader_entrypoint": _loader_status(path),
            "persistence_pack_sha256": resolved_sha,
            "pack_identity_source": (
                "EVIDENCE_MANIFEST"
                if manifest_sha
                else "EXPLICIT_PROVENANCE"
                if explicit_sha
                else "UNVERIFIED"
            ),
            "capability_failures": summary["capability_failures"],
        }
        if manifest_record is not None:
            run["evidence_manifest"] = {
                key: value
                for key, value in manifest_record.items()
                if key != "persistence_pack_sha256"
            }
        runs.append(run)

    write_state = runs[0]["state"]
    reload_state = runs[1]["state"]

    write_state_valid = bool(
        isinstance(write_state, dict)
        and write_state.get("phase") == "WRITE"
        and write_state.get("previous_found") is False
        and write_state.get("previous") == 0
        and write_state.get("current") == 1
        and write_state.get("is_new_game") is True
        and write_state.get("is_multiplayer") is False
    )
    reload_state_valid = bool(
        isinstance(reload_state, dict)
        and reload_state.get("phase") == "RELOAD"
        and reload_state.get("previous_found") is True
        and reload_state.get("previous") == 1
        and reload_state.get("current") == 2
        and reload_state.get("is_new_game") is False
        and reload_state.get("is_multiplayer") is False
    )
    chain_valid = bool(
        isinstance(write_state, dict)
        and isinstance(reload_state, dict)
        and reload_state.get("previous") == write_state.get("current")
        and reload_state.get("current") == int(reload_state.get("previous", -1)) + 1
    )
    same_environment = bool(
        isinstance(write_state, dict)
        and isinstance(reload_state, dict)
        and _state_environment(write_state) == _state_environment(reload_state)
        and write_state.get("campaign") not in {None, "unknown"}
        and write_state.get("local_faction") not in {None, "unknown"}
    )

    pack_hashes = [run["persistence_pack_sha256"] for run in runs]
    exact_pack_verified = bool(
        all(value is not None for value in pack_hashes)
        and len(set(pack_hashes)) == 1
        and (
            expected_pack_sha256 is None
            or pack_hashes[0] == expected_pack_sha256.lower()
        )
    )

    collection_ids = [
        run.get("evidence_manifest", {}).get("collection_id")
        if isinstance(run.get("evidence_manifest"), dict)
        else None
        for run in runs
    ]
    independent_collections_verified = bool(
        all(value is not None for value in collection_ids)
        and len(set(collection_ids)) == 2
    )

    checks = {
        "isolated_persistence_sessions": all(
            bool(run["isolated_persistence_session"]) for run in runs
        ),
        "one_state_per_phase": all(bool(run["exactly_one_state"]) for run in runs),
        "no_capability_failures": all(not run["capability_failures"] for run in runs),
        "loader_entrypoint_clean": all(
            run["loader_entrypoint"] == "SUCCESS" for run in runs
        ),
        "write_state_valid": write_state_valid,
        "reload_state_valid": reload_state_valid,
        "saved_value_chain_valid": chain_valid,
        "same_campaign_and_faction": same_environment,
        "exact_pack_verified": exact_pack_verified,
        "independent_collections_verified": independent_collections_verified,
    }
    replicated = all(checks.values())
    result: dict[str, object] = {
        "schema_version": 1,
        "status": "REPLICATED" if replicated else "UNVERIFIED",
        "evidence_label": "REPLICATED" if replicated else "UNVERIFIED",
        "expected_pack_sha256": (
            expected_pack_sha256.lower() if expected_pack_sha256 else None
        ),
        "checks": checks,
        "runs": runs,
        "warnings": [
            "This proves only one project-owned saved integer survived a save/reload cycle in the tested disposable campaign.",
            "It does not prove campaign objective control, order authority, migration safety for future schemas, or compatibility with valued saves.",
        ],
    }
    result["semantic_digest"] = hashlib.sha256(
        canonical_json(persistence_semantic_projection(result))
    ).hexdigest()
    result["result_digest"] = hashlib.sha256(canonical_json(result)).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify a two-phase Transcendence disposable-save persistence round trip."
    )
    parser.add_argument("logs", type=Path, nargs=2)
    parser.add_argument("--evidence-manifest", type=Path, action="append")
    parser.add_argument("--pack-sha256", action="append")
    parser.add_argument("--expected-pack-sha256")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = build_persistence_report(
        args.logs,
        evidence_manifest_paths=args.evidence_manifest,
        pack_sha256s=args.pack_sha256,
        expected_pack_sha256=args.expected_pack_sha256,
    )
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
