from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def marker_summary(data: bytes) -> dict[str, Any]:
    text = data.decode("utf-8", errors="replace")
    lines = text.splitlines()
    events: list[str] = []
    counts = {
        "campaign_runtime_begin": 0,
        "campaign_turn_end_snapshots": 0,
        "battle_runtime_begin": 0,
        "battle_complete": 0,
    }
    for line in lines:
        if line.startswith("TRANS_PROBE|1|RUNTIME_BEGIN|") and "runtime=campaign" in line:
            counts["campaign_runtime_begin"] += 1
            events.append("CAMPAIGN_RUNTIME_BEGIN")
        elif line.startswith("TRANS_PROBE|1|SNAPSHOT_END|") and "reason=LOCAL_FACTION_TURN_START" in line:
            counts["campaign_turn_end_snapshots"] += 1
        elif (
            line.startswith("TRANS_BATTLE|1|RUNTIME_BEGIN|")
            or line.startswith("TRANS_BATTLE|2|RUNTIME_BEGIN|")
        ) and "runtime=battle" in line:
            counts["battle_runtime_begin"] += 1
            events.append("BATTLE_RUNTIME_BEGIN")
        elif line.startswith("TRANS_BATTLE|1|BATTLE_COMPLETE|") or line.startswith(
            "TRANS_BATTLE|2|BATTLE_COMPLETE|"
        ):
            counts["battle_complete"] += 1
            events.append("BATTLE_COMPLETE")
    return {**counts, "transition_events": events}


def write_json(path: Path, payload: object) -> None:
    """Durably replace one JSON control file and verify the exact bytes.

    A unique temporary name prevents two rapid publications from sharing one
    staging file.  Flush+fsync and a post-replace byte comparison make a
    zero-filled or truncated control file an immediate watcher error instead of
    silently poisoning later collection.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    blob = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f".{path.name}.{os.getpid()}.",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(blob)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        temporary = None
        persisted = path.read_bytes()
        if persisted != blob:
            raise OSError(
                f"atomic JSON verification failed for {path.name}: "
                f"expected {len(blob)} bytes, found {len(persisted)}"
            )
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def take_checkpoint(
    *,
    data: bytes,
    checkpoint_root: Path,
    sequence: int,
    reason: str,
) -> dict[str, Any]:
    checkpoint_root.mkdir(parents=True, exist_ok=True)
    filename = f"checkpoint_{sequence:04d}_{len(data):012d}.txt"
    path = checkpoint_root / filename
    path.write_bytes(data)
    return {
        "sequence": sequence,
        "created_at_utc": utc_now(),
        "reason": reason,
        "filename": filename,
        "private_path": str(path.resolve()),
        "size_bytes": len(data),
        "sha256": sha256_bytes(data),
        "markers": marker_summary(data),
    }


def run_watcher(
    *,
    log_path: Path,
    checkpoint_root: Path,
    stop_file: Path,
    status_path: Path,
    manifest_path: Path,
    poll_seconds: float,
    interval_seconds: float,
    growth_bytes: int,
    handshake_token: str,
) -> int:
    checkpoint_root.mkdir(parents=True, exist_ok=True)
    checkpoints: list[dict[str, Any]] = []
    violations: list[str] = []
    previous_data = b""
    previous_markers: dict[str, Any] | None = None
    last_checkpoint_monotonic = 0.0
    sequence = 0
    started = utc_now()

    def publish(state: str) -> None:
        write_json(
            manifest_path,
            {
                "schema_version": 2,
                "handshake_token": handshake_token,
                "pid": os.getpid(),
                "started_at_utc": started,
                "updated_at_utc": utc_now(),
                "state": state,
                "log_private_path": str(log_path.resolve()),
                "checkpoint_root_private_path": str(checkpoint_root.resolve()),
                "checkpoint_count": len(checkpoints),
                "checkpoints": checkpoints,
                "violations": violations,
            },
        )
        write_json(
            status_path,
            {
                "schema_version": 2,
                "handshake_token": handshake_token,
                "pid": os.getpid(),
                "state": state,
                "started_at_utc": started,
                "updated_at_utc": utc_now(),
                "checkpoint_count": len(checkpoints),
                "last_size_bytes": len(previous_data),
                "violations": violations,
            },
        )

    publish("WAITING_FOR_LOG")
    while True:
        stop_requested = stop_file.exists()
        data: bytes | None = None
        if log_path.is_file():
            for attempt in range(5):
                try:
                    data = log_path.read_bytes()
                    break
                except OSError:
                    if attempt == 4:
                        raise
                    time.sleep(0.2)

        if data is not None:
            if previous_data and not data.startswith(previous_data):
                violations.append("APPEND_ONLY_PREFIX_VIOLATION")
                publish("FAILED")
                return 3
            markers = marker_summary(data)
            now = time.monotonic()
            reasons: list[str] = []
            if not checkpoints:
                reasons.append("FIRST_LOG_OBSERVATION")
            if previous_markers is not None and markers != previous_markers:
                reasons.append("RUNTIME_MARKER_CHANGE")
            if checkpoints and len(data) - checkpoints[-1]["size_bytes"] >= growth_bytes:
                reasons.append("GROWTH_THRESHOLD")
            if checkpoints and now - last_checkpoint_monotonic >= interval_seconds and len(data) > checkpoints[-1]["size_bytes"]:
                reasons.append("TIME_INTERVAL")
            if stop_requested:
                reasons.append("STOP_REQUESTED")
            if reasons and (not checkpoints or data != previous_data or stop_requested):
                sequence += 1
                checkpoint = take_checkpoint(
                    data=data,
                    checkpoint_root=checkpoint_root,
                    sequence=sequence,
                    reason="+".join(dict.fromkeys(reasons)),
                )
                checkpoints.append(checkpoint)
                last_checkpoint_monotonic = now
            previous_data = data
            previous_markers = markers
            publish("STOPPED" if stop_requested else "WATCHING")

        if stop_requested:
            if data is None:
                violations.append("STOP_REQUESTED_BEFORE_LOG_CREATED")
                publish("FAILED")
                return 4
            return 0
        time.sleep(poll_seconds)


def main() -> int:
    parser = argparse.ArgumentParser(description="Checkpoint the append-only WH3 Transcendence runtime log.")
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--checkpoint-root", type=Path, required=True)
    parser.add_argument("--stop-file", type=Path, required=True)
    parser.add_argument("--status", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--poll-seconds", type=float, default=2.0)
    parser.add_argument("--interval-seconds", type=float, default=15.0)
    parser.add_argument("--growth-bytes", type=int, default=1_000_000)
    parser.add_argument("--handshake-token", required=True)
    args = parser.parse_args()
    return run_watcher(
        log_path=args.log,
        checkpoint_root=args.checkpoint_root,
        stop_file=args.stop_file,
        status_path=args.status,
        manifest_path=args.manifest,
        poll_seconds=args.poll_seconds,
        interval_seconds=args.interval_seconds,
        growth_bytes=args.growth_bytes,
        handshake_token=args.handshake_token,
    )


if __name__ == "__main__":
    raise SystemExit(main())
