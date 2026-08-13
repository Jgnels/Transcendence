from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _parse_utc(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _classification(segment: dict[str, Any]) -> str:
    source = str(segment.get("source_filename", ""))
    source_kind = str(segment.get("source_kind", ""))
    lower = source.lower()

    # ZIP-member notation and canonical fixture suffixes are generated test data,
    # not owner gameplay evidence.
    if "::" in source or lower.endswith(("_valid.txt", "_invalid.txt")):
        return "PROJECT_FIXTURE"
    if source_kind == "project_runtime_probe" and lower.startswith("segment_"):
        return "RECOVERY_REEXPORT"
    if lower == "probe_build_manifest.json":
        return "BUILD_METADATA"
    if lower in {"modified.log", "used_mods.txt"}:
        return "LOADER_DIAGNOSTIC"
    if lower.startswith("lua_mod_log") or "script_log" in lower or lower == "transcendence_runtime_log.txt":
        return "LIVE_LOG_CANDIDATE"
    return "OTHER"


def adjudicate_inventory(
    data: dict[str, Any],
    *,
    session_start_utc: datetime | None = None,
) -> dict[str, Any]:
    segments = data.get("segments")
    if not isinstance(segments, list):
        raise ValueError("recovery inventory has no segments list")

    if session_start_utc is not None:
        if session_start_utc.tzinfo is None:
            session_start_utc = session_start_utc.replace(tzinfo=timezone.utc)
        session_start_utc = session_start_utc.astimezone(timezone.utc)

    classified: list[dict[str, Any]] = []
    unique_live: dict[str, dict[str, Any]] = {}
    for raw in segments:
        if not isinstance(raw, dict):
            continue
        classification = _classification(raw)
        modified = _parse_utc(raw.get("source_last_write_utc"))
        current_session = bool(
            classification == "LIVE_LOG_CANDIDATE"
            and session_start_utc is not None
            and modified is not None
            and modified >= session_start_utc
        )
        record = {
            "segment": raw.get("segment"),
            "source_filename": raw.get("source_filename"),
            "source_kind": raw.get("source_kind"),
            "source_sha256": raw.get("source_sha256"),
            "source_last_write_utc": (
                modified.isoformat().replace("+00:00", "Z") if modified else None
            ),
            "classification": classification,
            "current_session_candidate": current_session,
            "trans_probe_record_count": int(raw.get("trans_probe_record_count", 0) or 0),
            "trans_battle_record_count": int(raw.get("trans_battle_record_count", 0) or 0),
            "battle_pack_loaded_count": int(raw.get("battle_pack_loaded_count", 0) or 0),
            "battle_complete_count": int(raw.get("battle_complete_count", 0) or 0),
            "canonical_snapshot_turns": sorted(
                {int(turn) for turn in raw.get("canonical_snapshot_turns", [])}
            ),
        }
        classified.append(record)
        digest = record["source_sha256"]
        if classification == "LIVE_LOG_CANDIDATE" and isinstance(digest, str):
            # Prefer an original game-install/private-log source over a recovery
            # derivative when the same bytes are represented more than once.
            existing = unique_live.get(digest)
            if existing is None:
                unique_live[digest] = record
            else:
                priority = {"game_install": 0, "project_private_logs": 1}
                old_priority = priority.get(str(existing.get("source_kind")), 9)
                new_priority = priority.get(str(record.get("source_kind")), 9)
                if new_priority < old_priority:
                    unique_live[digest] = record

    live_records = sorted(
        unique_live.values(),
        key=lambda item: (
            str(item.get("source_last_write_utc") or ""),
            str(item.get("source_filename") or ""),
        ),
    )
    current_records = [record for record in live_records if record["current_session_candidate"]]
    historical_records = [record for record in live_records if not record["current_session_candidate"]]

    def _turns(records: list[dict[str, Any]]) -> list[int]:
        return sorted(
            {
                turn
                for record in records
                for turn in record["canonical_snapshot_turns"]
            }
        )

    def _sum(records: list[dict[str, Any]], key: str) -> int:
        return sum(int(record[key]) for record in records)

    current_turns = _turns(current_records)
    historical_turns = _turns(historical_records)
    current_battle_records = _sum(current_records, "trans_battle_record_count")
    current_battle_completions = _sum(current_records, "battle_complete_count")
    fixture_battle_records = sum(
        int(record["trans_battle_record_count"])
        for record in classified
        if record["classification"] == "PROJECT_FIXTURE"
    )
    fixture_battle_completions = sum(
        int(record["battle_complete_count"])
        for record in classified
        if record["classification"] == "PROJECT_FIXTURE"
    )

    session_label = (
        session_start_utc.isoformat().replace("+00:00", "Z")
        if session_start_utc is not None
        else None
    )
    result: dict[str, Any] = {
        "schema_version": 2,
        "evidence_label": "LIMITING_RESULT",
        "session_start_utc": session_label,
        "live_unique_log_count": len(live_records),
        "current_session_live_log_count": len(current_records),
        "historical_live_log_count": len(historical_records),
        "current_session_campaign_turns_recovered": current_turns,
        "current_session_early_turns_recovered": [turn for turn in current_turns if turn <= 3],
        "current_session_trans_battle_record_count": current_battle_records,
        "current_session_completed_battle_count": current_battle_completions,
        "historical_campaign_turns_recovered": historical_turns,
        "historical_trans_battle_record_count": _sum(historical_records, "trans_battle_record_count"),
        "fixture_trans_battle_record_count_excluded": fixture_battle_records,
        "fixture_completed_battle_count_excluded": fixture_battle_completions,
        "class_counts": {},
        "current_session_live_sources": current_records,
        "historical_live_sources": historical_records,
        "segments": classified,
        "conclusion": (
            "No live battle telemetry or early-turn snapshots from the current combined "
            "session were recovered; fixture battle records were excluded."
            if current_battle_records == 0 and not [turn for turn in current_turns if turn <= 3]
            else "At least one current-session early-turn or battle telemetry record was recovered."
        ),
        "warnings": [
            "A project fixture proves parser behavior, not owner gameplay.",
            "A re-exported recovery segment is not an independent runtime source.",
            "Historical observer or persistence logs are not part of the current combined session.",
            "Missing current-session battle records do not prove no battle occurred; they prove the telemetry did not survive in recovered sources.",
        ],
    }
    counts: dict[str, int] = {}
    for record in classified:
        key = str(record["classification"])
        counts[key] = counts.get(key, 0) + 1
    result["class_counts"] = dict(sorted(counts.items()))

    digest_payload = dict(result)
    digest_payload.pop("result_digest", None)
    result["result_digest"] = hashlib.sha256(
        json.dumps(digest_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Separate current live WH3 recovery evidence from historical logs, fixtures, and re-exports."
    )
    parser.add_argument("inventory", type=Path)
    parser.add_argument("--session-start-utc")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    session_start = _parse_utc(args.session_start_utc)
    if args.session_start_utc and session_start is None:
        raise SystemExit("--session-start-utc must be an ISO-8601 timestamp")

    data = json.loads(args.inventory.read_text(encoding="utf-8-sig"))
    result = adjudicate_inventory(data, session_start_utc=session_start)
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
