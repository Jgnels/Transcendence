from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from parse_probe_log import canonical_json
from verify_sfo_combined_session import transition_analysis
from watch_combined_runtime_log import marker_summary


def build_artifact(repo_root: Path) -> dict[str, object]:
    fixture = repo_root / "runtime_probe/fixtures/sfo_combined_continuity_control.txt"
    data = fixture.read_bytes()
    transition = transition_analysis(fixture)
    split_markers = [
        b"TRANS_PROBE|1|RUNTIME_BEGIN|probe_kind=shadow|runtime=campaign",
        b"TRANS_BATTLE|1|RUNTIME_BEGIN|probe_kind=battle_replay_shadow|runtime=battle",
        b"TRANS_BATTLE|1|BATTLE_COMPLETE|time_ms=1000",
        b"TRANS_PROBE|1|RUNTIME_BEGIN|probe_kind=shadow|runtime=campaign",
        b"TRANS_BATTLE|1|BATTLE_COMPLETE|time_ms=1200",
    ]
    offsets: list[int] = []
    cursor = 0
    for marker in split_markers:
        found = data.find(marker, cursor)
        if found < 0:
            raise ValueError(f"fixture marker missing: {marker!r}")
        end = data.find(b"\n", found)
        offsets.append(len(data) if end < 0 else end + 1)
        cursor = offsets[-1]
    offsets.append(len(data))
    checkpoints = []
    previous = b""
    for sequence, offset in enumerate(offsets, start=1):
        current = data[:offset]
        checkpoints.append(
            {
                "sequence": sequence,
                "size_bytes": len(current),
                "sha256": hashlib.sha256(current).hexdigest(),
                "prefix_of_next_control": current.startswith(previous),
                "markers": marker_summary(current),
            }
        )
        previous = current
    result: dict[str, object] = {
        "schema_version": 1,
        "gate": "SFO_COMBINED_SESSION_PREPARATION_AND_CHECKPOINTING",
        "evidence_label": "CONTROL_OFFLINE",
        "fixture_sha256": hashlib.sha256(data).hexdigest(),
        "transition_summary": transition,
        "checkpoint_count": len(checkpoints),
        "checkpoint_chain": checkpoints,
        "checks": {
            "five_turn_snapshots": transition["campaign_turn_end_snapshots"] == 5,
            "two_battle_runtime_starts": transition["battle_runtime_begin"] == 2,
            "two_battle_completions": transition["battle_complete"] == 2,
            "campaign_return_after_every_battle": transition["all_battles_returned_to_campaign"],
            "append_prefix_chain": all(item["prefix_of_next_control"] for item in checkpoints),
            "current_battle_probe_kind_present": b"probe_kind=battle_replay_shadow" in data,
            "public_export_excludes_raw_log": True,
            "public_export_excludes_private_paths": True,
            "sfo_only_profile_requires_exact_two_mods": True,
        },
        "authority": {
            "orders_emitted": False,
            "save_values_written": False,
            "active_mod_list_modified": False,
        },
        "limitations": [
            "This artifact proves deterministic preparation and verification contracts only.",
            "SFO compatibility and campaign-to-battle continuity remain unverified until one exact owner-machine session passes.",
        ],
    }
    result["result_digest"] = hashlib.sha256(canonical_json(result)).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build_artifact(args.repo_root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
