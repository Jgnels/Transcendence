from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "synthetic_lab"))
sys.path.insert(0, str(REPO_ROOT / "runtime_probe" / "tools"))

from parse_probe_log import ProbeEvent, canonical_json, parse_bool, parse_logs
from transcendence_lab.canonical import digest
from transcendence_lab.strategic_feasibility import (
    adjudicate_campaign_strategic_feasibility_observation,
    build_observation_packet_template,
)
from watch_campaign_feasibility import _complete_snapshots, derive_plan_from_snapshot

PROBE_KIND = "campaign_feasibility"
PACK_NAME = "transcendence_campaign_feasibility_probe.pack"


class CampaignFeasibilityLiveError(ValueError):
    pass


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _verified_plan_from_log(events: list[ProbeEvent], saved_plan: dict[str, Any]) -> dict[str, Any]:
    matches: list[dict[str, Any]] = []
    for snapshot in _complete_snapshots(events):
        try:
            plan, _ = derive_plan_from_snapshot(snapshot)
        except Exception:
            continue
        if plan is not None and plan.get("result_digest") == saved_plan.get("result_digest"):
            matches.append(plan)
    if len(matches) != 1:
        raise CampaignFeasibilityLiveError(
            f"expected exactly one observer snapshot to reproduce the saved live plan, found {len(matches)}"
        )
    if matches[0] != saved_plan:
        raise CampaignFeasibilityLiveError("saved live plan differs from independent log reconstruction")
    return matches[0]


def _result_events(events: list[ProbeEvent], plan: dict[str, Any]) -> tuple[list[dict[str, Any]], ProbeEvent]:
    expected = {item["query_id"]: item for item in plan["queries"]}
    observed: dict[str, dict[str, Any]] = {}
    for event in events:
        if event.event != "FEASIBILITY_QUERY_RESULT" or event.fields.get("plan_digest") != plan["result_digest"]:
            continue
        fields = event.fields
        query_id = fields.get("query_id")
        if query_id not in expected:
            raise CampaignFeasibilityLiveError("live result contains foreign query id")
        if query_id in observed:
            raise CampaignFeasibilityLiveError("live result contains duplicate query id")
        source = expected[query_id]
        if fields.get("query_key") != source["query_key"]:
            raise CampaignFeasibilityLiveError("live query key does not match query id")
        if fields.get("scenario_id") != plan["scenario_id"] or fields.get("turn") != str(plan["turn"]):
            raise CampaignFeasibilityLiveError("live result scenario/turn mismatch")
        if fields.get("assignment_id") != plan["source_assignment_id"]:
            raise CampaignFeasibilityLiveError("live result assignment mismatch")
        if fields.get("read_only") != "true":
            raise CampaignFeasibilityLiveError("live result missing read-only attestation")
        try:
            was_observed = parse_bool(fields.get("observed", ""))
        except Exception as exc:
            raise CampaignFeasibilityLiveError("live observed flag malformed") from exc
        if not isinstance(was_observed, bool):
            raise CampaignFeasibilityLiveError("live observed flag must be boolean")
        if was_observed:
            raw = fields.get("value")
            if source["query_key"] == "FORCE_ACTIVE_STANCE":
                if raw is None or raw in {"", "null"}:
                    raise CampaignFeasibilityLiveError("observed stance missing")
                value: Any = raw
            else:
                try:
                    value = parse_bool(raw or "")
                except Exception as exc:
                    raise CampaignFeasibilityLiveError("observed boolean result malformed") from exc
                if not isinstance(value, bool):
                    raise CampaignFeasibilityLiveError("observed query result must be boolean")
        else:
            value = None
        observed[query_id] = {
            "query_id": query_id,
            "query_key": source["query_key"],
            "observed": was_observed,
            "value": value,
        }

    packet_ends = [
        event
        for event in events
        if event.event == "FEASIBILITY_PACKET_END" and event.fields.get("plan_digest") == plan["result_digest"]
    ]
    if len(packet_ends) != 1:
        raise CampaignFeasibilityLiveError(f"expected exactly one matching packet end, found {len(packet_ends)}")
    end = packet_ends[0]
    if end.fields.get("query_count") != str(plan["query_count"]):
        raise CampaignFeasibilityLiveError("packet-end query count mismatch")
    if end.fields.get("orders_emitted") != "false" or end.fields.get("save_values_written") != "false" or end.fields.get("read_only") != "true":
        raise CampaignFeasibilityLiveError("packet-end authority attestation malformed")
    if len(observed) != len(expected):
        raise CampaignFeasibilityLiveError(
            f"live result cardinality mismatch: {len(observed)} of {len(expected)} queries recorded"
        )
    ordered = [observed[item["query_id"]] for item in plan["queries"]]
    return ordered, end


def build_live_artifacts(
    *,
    log_path: Path,
    saved_plan_path: Path,
    environment_public_path: Path,
    expected_pack_sha256: str,
) -> dict[str, Any]:
    events = parse_logs([log_path])
    saved_plan = json.loads(saved_plan_path.read_text(encoding="utf-8-sig"))
    plan = _verified_plan_from_log(events, saved_plan)

    pack_loads = [
        event for event in events if event.event == "PACK_LOADED" and event.fields.get("probe_kind") == PROBE_KIND
    ]
    if len(pack_loads) != 1:
        raise CampaignFeasibilityLiveError(f"expected one {PROBE_KIND} PACK_LOADED marker, found {len(pack_loads)}")

    environment = json.loads(environment_public_path.read_text(encoding="utf-8-sig"))
    probe = environment.get("expected_probe") if isinstance(environment, dict) else None
    if not isinstance(probe, dict):
        raise CampaignFeasibilityLiveError("environment attestation missing probe record")
    if probe.get("canonical_pack_name") != PACK_NAME or probe.get("pack_sha256") != expected_pack_sha256:
        raise CampaignFeasibilityLiveError("environment attestation does not bind the exact feasibility probe")

    results, end = _result_events(events, plan)
    packet = build_observation_packet_template(plan)
    packet["results"] = results
    packet.pop("result_digest", None)
    packet["result_digest"] = digest(packet)
    adjudication = adjudicate_campaign_strategic_feasibility_observation(plan, packet)

    observed_count = sum(1 for item in results if item["observed"])
    unavailable_count = len(results) - observed_count
    verification: dict[str, Any] = {
        "schema_version": 1,
        "contract": "CAMPAIGN_STRATEGIC_FEASIBILITY_LIVE_VERIFICATION_V1",
        "status": "OBSERVED_READ_ONLY" if observed_count > 0 else "UNVERIFIED_NO_QUERY_SUCCEEDED",
        "authority": "NO_ORDERS",
        "application_authority": "PROHIBITED",
        "inputs": {
            "raw_log_sha256": sha256(log_path),
            "saved_plan_sha256": sha256(saved_plan_path),
            "environment_attestation_sha256": sha256(environment_public_path),
            "probe_pack_sha256": expected_pack_sha256,
        },
        "bindings": {
            "plan_reproduced_from_raw_snapshot": True,
            "plan_digest": plan["result_digest"],
            "scenario_id": plan["scenario_id"],
            "turn": plan["turn"],
            "assignment_id": plan["source_assignment_id"],
            "query_count": plan["query_count"],
            "observed_query_count": observed_count,
            "unavailable_query_count": unavailable_count,
            "packet_end_line": end.line_number,
        },
        "nonpromotions": [
            "A true reachability result does not establish route geometry, zone-of-control safety, interception safety, movement/attack legality, acknowledgement, execution, or outcome.",
            "A faction centroid remains a reference point and never becomes a character, settlement, or attack target.",
            "No query result grants application authority.",
        ],
        "orders_emitted": False,
        "save_values_written": False,
    }
    verification["result_digest"] = digest(verification)
    return {
        "plan": plan,
        "observation": packet,
        "adjudication": adjudication,
        "verification": verification,
        "environment": environment,
    }


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _deterministic_zip(paths: list[Path], destination: Path) -> None:
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(paths, key=lambda p: p.name):
            info = zipfile.ZipInfo(path.name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())


def main() -> int:
    parser = argparse.ArgumentParser(description="Build and verify a public-safe v0.2I campaign feasibility live observation export.")
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--environment", type=Path, required=True)
    parser.add_argument("--expected-pack-sha256", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--zip", type=Path, required=True)
    args = parser.parse_args()

    artifacts = build_live_artifacts(
        log_path=args.log,
        saved_plan_path=args.plan,
        environment_public_path=args.environment,
        expected_pack_sha256=args.expected_pack_sha256,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    members: list[Path] = []
    for key, filename in (
        ("plan", "campaign_feasibility_plan.json"),
        ("observation", "campaign_feasibility_observation.json"),
        ("adjudication", "campaign_feasibility_adjudication.json"),
        ("verification", "campaign_feasibility_verification.json"),
        ("environment", "sfo_environment_attestation.json"),
    ):
        path = args.output_dir / filename
        _write_json(path, artifacts[key])
        members.append(path)
    manifest = {
        "schema_version": 1,
        "contract": "CAMPAIGN_STRATEGIC_FEASIBILITY_PUBLIC_EXPORT_V1",
        "members": [
            {"name": path.name, "size_bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in sorted(members, key=lambda p: p.name)
        ],
        "raw_log_included": False,
        "private_paths_included": False,
        "orders_emitted": False,
        "save_values_written": False,
    }
    manifest["result_digest"] = digest(manifest)
    manifest_path = args.output_dir / "manifest.json"
    _write_json(manifest_path, manifest)
    members.append(manifest_path)
    args.zip.parent.mkdir(parents=True, exist_ok=True)
    _deterministic_zip(members, args.zip)
    print(json.dumps({
        "status": artifacts["verification"]["status"],
        "zip": str(args.zip),
        "zip_sha256": sha256(args.zip),
        "plan_digest": artifacts["plan"]["result_digest"],
        "observation_digest": artifacts["observation"]["result_digest"],
        "adjudication_digest": artifacts["adjudication"]["result_digest"],
        "verification_digest": artifacts["verification"]["result_digest"],
        "observed_query_count": artifacts["verification"]["bindings"]["observed_query_count"],
        "query_count": artifacts["verification"]["bindings"]["query_count"],
    }, indent=2, sort_keys=True))
    return 0 if artifacts["verification"]["status"] == "OBSERVED_READ_ONLY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
