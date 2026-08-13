from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Sequence

from parse_probe_log import canonical_json, parse_logs, summarize

OBSERVER_ENTRYPOINT = "transcendence_observer_probe"
OBSERVER_PACK_NAME = "transcendence_observer_probe.pack"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def loader_entrypoint_status(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    success_start = f"Executing mod function {OBSERVER_ENTRYPOINT}()"
    success_end = f"{OBSERVER_ENTRYPOINT}() executed successfully"
    missing = f"{OBSERVER_ENTRYPOINT}() not found"

    if success_start in text and success_end in text:
        return "SUCCESS"
    if missing in text:
        return "MISSING"
    return "UNKNOWN"


def _environment_key(summary: dict[str, object]) -> tuple[object, ...] | None:
    environments = summary.get("environments", [])
    if not environments:
        return None
    environment = environments[0]
    return (
        environment.get("campaign"),
        environment.get("turn"),
        environment.get("local_faction"),
        environment.get("is_new_game"),
        environment.get("is_multiplayer"),
    )


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _manifest_log_hashes(manifest: dict[str, object]) -> set[str]:
    hashes: set[str] = set()
    for record in manifest.get("logs", []):
        value = record.get("sha256")
        if isinstance(value, str):
            hashes.add(value.lower())
    return hashes


def _manifest_observer_hash(manifest: dict[str, object]) -> str | None:
    for record in manifest.get("installed_probe_packs", []):
        if record.get("name") != OBSERVER_PACK_NAME:
            continue
        value = record.get("installed_sha256")
        if isinstance(value, str):
            return value.lower()
    return None


def _manifest_collection_record(
    manifest_path: Path,
    *,
    expected_log_sha256: str,
) -> dict[str, object]:
    manifest = _load_json(manifest_path)
    manifest_sha = sha256_file(manifest_path)
    collected_at = manifest.get("collected_at_utc")
    if not isinstance(collected_at, str) or not collected_at:
        raise ValueError(f"{manifest_path.name}: missing collected_at_utc")

    log_hashes = _manifest_log_hashes(manifest)
    if expected_log_sha256.lower() not in log_hashes:
        raise ValueError(
            f"{manifest_path.name}: manifest does not contain supplied log SHA-256 "
            f"{expected_log_sha256.lower()}"
        )

    observer_sha = _manifest_observer_hash(manifest)
    identity_payload = {
        "manifest_sha256": manifest_sha,
        "collected_at_utc": collected_at,
        "log_sha256": expected_log_sha256.lower(),
    }
    collection_id = hashlib.sha256(canonical_json(identity_payload)).hexdigest()
    return {
        "manifest_name": manifest_path.name,
        "manifest_sha256": manifest_sha,
        "manifest_schema_version": manifest.get("schema_version"),
        "collected_at_utc": collected_at,
        "collection_id": collection_id,
        "observer_pack_sha256": observer_sha,
    }


def build_replication_report(
    log_paths: Sequence[Path],
    *,
    pack_sha256s: Sequence[str] | None = None,
    expected_pack_sha256: str | None = None,
    evidence_manifest_paths: Sequence[Path] | None = None,
    collection_ids: Sequence[str] | None = None,
) -> dict[str, object]:
    if len(log_paths) < 2:
        raise ValueError("at least two observer logs are required")
    if pack_sha256s is not None and len(pack_sha256s) != len(log_paths):
        raise ValueError("pack_sha256s must contain one value per log")
    if evidence_manifest_paths is not None and len(evidence_manifest_paths) != len(log_paths):
        raise ValueError("evidence_manifest_paths must contain one value per log")
    if collection_ids is not None and len(collection_ids) != len(log_paths):
        raise ValueError("collection_ids must contain one value per log")

    runs: list[dict[str, object]] = []
    summaries: list[dict[str, object]] = []

    for index, path in enumerate(log_paths, 1):
        summary = summarize(parse_logs([path]))
        summaries.append(summary)
        sessions = summary["sessions"]
        observer_only = (
            len(sessions) == 1
            and sessions[0]["probe_kind"] == "observer"
        )

        log_sha = sha256_file(path)
        manifest_record: dict[str, object] | None = None
        if evidence_manifest_paths is not None:
            manifest_record = _manifest_collection_record(
                evidence_manifest_paths[index - 1],
                expected_log_sha256=log_sha,
            )

        explicit_pack_sha = (
            pack_sha256s[index - 1].lower()
            if pack_sha256s is not None
            else None
        )
        manifest_pack_sha = (
            manifest_record.get("observer_pack_sha256")
            if manifest_record is not None
            else None
        )
        if (
            explicit_pack_sha is not None
            and manifest_pack_sha is not None
            and explicit_pack_sha != manifest_pack_sha
        ):
            raise ValueError(
                f"run {index}: explicit observer pack SHA-256 does not match evidence manifest"
            )
        resolved_pack_sha = manifest_pack_sha or explicit_pack_sha
        if manifest_pack_sha is not None:
            pack_identity_source = "EVIDENCE_MANIFEST"
        elif explicit_pack_sha is not None:
            pack_identity_source = "EXPLICIT_PROVENANCE"
        else:
            pack_identity_source = "UNVERIFIED"

        if manifest_record is not None:
            collection_id = manifest_record["collection_id"]
            collection_source = "EVIDENCE_MANIFEST"
        elif collection_ids is not None:
            collection_id = collection_ids[index - 1]
            collection_source = "EXPLICIT_COLLECTION_ID"
        else:
            collection_id = None
            collection_source = "UNVERIFIED"

        run: dict[str, object] = {
            "run_index": index,
            "log_name": path.name,
            "log_sha256": log_sha,
            "log_size_bytes": path.stat().st_size,
            "result_digest": summary["result_digest"],
            "semantic_digest": summary["semantic_digest"],
            "loader_entrypoint": loader_entrypoint_status(path),
            "observer_session_valid": observer_only,
            "capability_failures": summary["capability_failures"],
            "environment": summary["environments"][0] if summary["environments"] else None,
            "pack_sha256": resolved_pack_sha,
            "pack_identity_source": pack_identity_source,
            "collection_id": collection_id,
            "collection_identity_source": collection_source,
        }
        if manifest_record is not None:
            run["evidence_manifest"] = {
                key: value
                for key, value in manifest_record.items()
                if key != "observer_pack_sha256"
            }
        runs.append(run)

    semantic_digests = {summary["semantic_digest"] for summary in summaries}
    raw_hashes = {run["log_sha256"] for run in runs}
    environment_keys = {_environment_key(summary) for summary in summaries}
    observer_sessions_valid = all(run["observer_session_valid"] for run in runs)
    no_capability_failures = all(not run["capability_failures"] for run in runs)
    same_semantics = len(semantic_digests) == 1
    byte_identical_raw_logs = len(raw_hashes) == 1
    same_environment = len(environment_keys) == 1 and None not in environment_keys
    loader_entrypoint_clean = all(run["loader_entrypoint"] == "SUCCESS" for run in runs)

    resolved_collection_ids = [run["collection_id"] for run in runs]
    independent_collections_verified = (
        all(value is not None for value in resolved_collection_ids)
        and len(set(resolved_collection_ids)) == len(runs)
    )

    pack_hashes = [run["pack_sha256"] for run in runs]
    exact_pack_verified = False
    if all(value is not None for value in pack_hashes):
        exact_pack_verified = len(set(pack_hashes)) == 1
        if expected_pack_sha256 is not None:
            exact_pack_verified = (
                exact_pack_verified
                and pack_hashes[0] == expected_pack_sha256.lower()
            )

    semantic_replication = all(
        (
            observer_sessions_valid,
            no_capability_failures,
            same_semantics,
            independent_collections_verified,
            same_environment,
        )
    )
    strict_replication = all(
        (
            semantic_replication,
            exact_pack_verified,
            loader_entrypoint_clean,
        )
    )

    if strict_replication:
        status = "REPLICATED"
        evidence_label = "REPLICATED"
    elif semantic_replication:
        status = "SUPPORTED_CROSS_REVISION"
        evidence_label = "SUPPORTED"
    else:
        status = "UNVERIFIED"
        evidence_label = "UNVERIFIED"

    warnings = [
        "Semantic equivalence does not prove campaign control, order authority, acknowledgement, outcome control, or save persistence.",
    ]
    if byte_identical_raw_logs:
        warnings.append(
            "The raw structured logs are byte-identical. This is compatible with deterministic replication; independence is established by distinct collection evidence, not by forcing content differences."
        )
    if status == "SUPPORTED_CROSS_REVISION":
        warnings.append(
            "Observer behavior repeated, but exact corrected-pack identity was not verified for every independent collection."
        )
    if not independent_collections_verified:
        warnings.append(
            "Independent sessions were not proven by distinct evidence-manifest or explicit collection identities."
        )

    result: dict[str, object] = {
        "schema_version": 2,
        "status": status,
        "evidence_label": evidence_label,
        "run_count": len(runs),
        "expected_pack_sha256": expected_pack_sha256.lower() if expected_pack_sha256 else None,
        "checks": {
            "observer_sessions_valid": observer_sessions_valid,
            "no_capability_failures": no_capability_failures,
            "same_semantic_observation": same_semantics,
            "byte_identical_raw_logs": byte_identical_raw_logs,
            "independent_collections_verified": independent_collections_verified,
            "same_environment": same_environment,
            "exact_pack_verified": exact_pack_verified,
            "loader_entrypoint_clean": loader_entrypoint_clean,
        },
        "shared_semantic_digest": next(iter(semantic_digests)) if same_semantics else None,
        "runs": runs,
        "warnings": warnings,
    }
    result["result_digest"] = hashlib.sha256(canonical_json(result)).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify repeated Transcendence observer runs without conflating transport metadata, deterministic byte identity, or pack revision."
    )
    parser.add_argument("logs", type=Path, nargs="+")
    parser.add_argument("--pack-sha256", action="append", default=None)
    parser.add_argument("--expected-pack-sha256")
    parser.add_argument("--evidence-manifest", type=Path, action="append", default=None)
    parser.add_argument("--collection-id", action="append", default=None)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    result = build_replication_report(
        args.logs,
        pack_sha256s=args.pack_sha256,
        expected_pack_sha256=args.expected_pack_sha256,
        evidence_manifest_paths=args.evidence_manifest,
        collection_ids=args.collection_id,
    )
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
