from __future__ import annotations

import argparse
import json
from pathlib import Path

from adjudicate_action_authority_export import adjudicate_action_authority_documents

SOURCE_EXPORT_SHA256 = "a1c03ec12a4c2b70945311fc57b54f978fcca892a37b12d46a5daa6f22ebf579"


def build(evidence_dir: Path) -> dict[str, object]:
    summary = json.loads(
        (evidence_dir / "action_authority_summary.json").read_text(encoding="utf-8-sig")
    )
    verification = json.loads(
        (evidence_dir / "action_authority_verification.json").read_text(encoding="utf-8-sig")
    )
    manifest = json.loads(
        (evidence_dir / "public_capture_manifest.json").read_text(encoding="utf-8-sig")
    )
    return adjudicate_action_authority_documents(
        summary=summary,
        verification=verification,
        manifest=manifest,
        source_export_sha256=SOURCE_EXPORT_SHA256,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the frozen v0.1S live action-authority adjudication")
    parser.add_argument("evidence_dir", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = build(args.evidence_dir)
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
