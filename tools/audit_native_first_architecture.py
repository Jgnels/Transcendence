from __future__ import annotations

import argparse
import json
from pathlib import Path


CHECKS = (
    ("README.md", "## Current implementation — v0.2I", False, "paused v0.2I must not be labeled current"),
    ("README.md", "## Current implementation — v0.2G", False, "v0.2G must not be labeled a current implementation controller"),
    ("research/CURRENT_STATE.md", "v0.2Q SFO benchmark adjudication / staged replication — AUTHORITATIVE CURRENT", True, "current-state must lead with v0.2Q"),
    ("research/CURRENT_STATE.md", "NO_NATIVE_ROW_ABLATION_EARNED", True, "current-state must preserve no-ablation decision"),
    ("research/CURRENT_STATE.md", "zero decoded allocator-variable overrides", True, "current-state must block false SFO allocator attribution"),
    ("research/ARCHITECTURE.md", "Historical-boundary rule", True, "architecture must explicitly bound superseded controller descriptions"),
    ("research/ARCHITECTURE.md", "The current campaign reasoning chain is:", False, "superseded v0.2G/v0.2H chains must not be called current"),
    ("research/KNOWN_RISKS.md", "next gate must add portfolio-to-army assignment", False, "stale allocator-next-step mitigation must be retired"),
    ("research/KNOWN_RISKS.md", "privileged artifacts are explicitly `application_eligible=false`", True, "privileged research/application firewall must remain explicit"),
    ("research/CLAIM_REGISTER.md", "Native reserve preservation, recovering-army protection, assignment exclusivity, temporal commitment and reassignment hysteresis are proven absent", True, "absence claim must remain explicitly registered and rejected"),
    ("research/CLAIM_REGISTER.md", "No captured SFO allocator-variable override", True, "false allocator attribution correction must remain registered"),
    ("research/CLAIM_REGISTER.md", "Grey Point Scuttlers", True, "special-force causal review must remain registered"),
)


def run(root: Path) -> dict:
    results=[]
    for relative, needle, should_exist, rationale in CHECKS:
        path=root/relative
        text=path.read_text(encoding="utf-8")
        present=needle in text
        passed=present if should_exist else not present
        results.append({
            "file": relative,
            "needle": needle,
            "expectation": "PRESENT" if should_exist else "ABSENT",
            "passed": passed,
            "rationale": rationale,
        })
    return {
        "contract":"NATIVE_FIRST_ACTIVE_DOCUMENT_AUDIT_V1",
        "authority":"NO_ORDERS",
        "application_authority":"PROHIBITED",
        "status":"PASS" if all(x["passed"] for x in results) else "FAIL_CLOSED",
        "checks":results,
    }


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1])
    ap.add_argument("--out",type=Path)
    args=ap.parse_args()
    report=run(args.root.resolve())
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2,sort_keys=True))
    return 0 if report["status"]=="PASS" else 2

if __name__=="__main__": raise SystemExit(main())
