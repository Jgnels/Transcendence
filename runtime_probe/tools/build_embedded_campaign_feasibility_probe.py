from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "runtime_probe" / "tools"))
sys.path.insert(0, str(REPO_ROOT / "synthetic_lab"))

from build_probe_packs import write_pfh5_pack
from watch_campaign_feasibility import _request_text, MAX_QUERIES

PACK_NAME = "transcendence_campaign_feasibility_probe.pack"
INTERNAL_PATH = "script/campaign/mod/transcendence_campaign_feasibility_probe.lua"
SOURCE_PATH = REPO_ROOT / "runtime_probe" / "source" / "script" / "campaign" / "mod" / "transcendence_campaign_feasibility_probe.lua"
READER_PREFIX = 'local function trans_feas_read_request()\n    local opened, handle = pcall(io.open, TRANS_FEAS_REQUEST_FILE, "r")\n    if not opened or not handle then\n        return nil\n    end\n    local lines = {}\n    for line in handle:lines() do\n        lines[#lines + 1] = line\n    end\n    handle:close()\n    if #lines < 2 then\n        return nil\n    end\n'
QUERY_WHITELIST = {
    "MODEL_HAS_CHARACTER_CQI",
    "MODEL_CHARACTER_FROM_CQI",
    "MODEL_HAS_FORCE_CQI",
    "MODEL_FORCE_FROM_CQI",
    "FORCE_ACTIVE_STANCE",
    "POSITION_REACHABLE_THIS_TURN",
    "POSITION_REACHABLE_THIS_TURN_IN_STANCE",
    "POSITION_EVER_REACHABLE",
    "REGION_SETTLEMENT_INTERFACE",
    "SETTLEMENT_REACHABLE_THIS_TURN",
    "SETTLEMENT_REACHABLE_THIS_TURN_IN_STANCE",
    "SETTLEMENT_EVER_REACHABLE",
    "GARRISON_UNDER_SIEGE",
}


class EmbeddedProbeBuildError(ValueError):
    pass


def sha256_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def sha256_path(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _lua_quote_ascii(value: str) -> str:
    if any(ord(ch) > 127 for ch in value):
        raise EmbeddedProbeBuildError("request must remain ASCII for deterministic Lua embedding")
    replacements = {
        "\\": "\\\\",
        '"': '\\"',
        "\n": "\\n",
        "\r": "\\r",
        "\t": "\\t",
    }
    return '"' + "".join(replacements.get(ch, ch) for ch in value) + '"'


def validate_plan(plan: dict[str, Any]) -> None:
    if plan.get("authority") != "NO_ORDERS":
        raise EmbeddedProbeBuildError("plan authority must be NO_ORDERS")
    if plan.get("application_authority") != "PROHIBITED":
        raise EmbeddedProbeBuildError("plan application authority must be PROHIBITED")
    queries = plan.get("queries")
    if not isinstance(queries, list) or not 1 <= len(queries) <= MAX_QUERIES:
        raise EmbeddedProbeBuildError("plan query count is out of bounds")
    if plan.get("query_count") != len(queries):
        raise EmbeddedProbeBuildError("plan query_count does not match queries")
    seen: set[str] = set()
    for query in queries:
        key = query.get("query_key")
        qid = query.get("query_id")
        if key not in QUERY_WHITELIST:
            raise EmbeddedProbeBuildError(f"query key is not whitelisted: {key!r}")
        if not isinstance(qid, str) or len(qid) != 64 or any(ch not in "0123456789abcdef" for ch in qid):
            raise EmbeddedProbeBuildError("query id is not a lowercase sha256 hex digest")
        if qid in seen:
            raise EmbeddedProbeBuildError("duplicate query id")
        seen.add(qid)


def _decode(value: str) -> str:
    out = value
    for encoded, plain in (("%0A", "\n"), ("%0D", "\r"), ("%3D", "="), ("%7C", "|"), ("%25", "%")):
        out = out.replace(encoded, plain)
    return out


def _fields(parts: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in parts:
        if "=" not in item:
            raise EmbeddedProbeBuildError("request field is malformed")
        key, value = item.split("=", 1)
        key = _decode(key); value = _decode(value)
        if key in result:
            raise EmbeddedProbeBuildError("request contains a duplicate field")
        result[key] = value
    return result


def validate_request_against_plan(text: str, plan: dict[str, Any]) -> None:
    lines = text.replace("\r\n", "\n").rstrip("\n").split("\n")
    if len(lines) != 1 + int(plan["query_count"]):
        raise EmbeddedProbeBuildError("request line count does not match the saved plan")
    head = lines[0].split("|")
    if head[:3] != ["TRANS_FEAS_REQ", "1", "REQUEST"]:
        raise EmbeddedProbeBuildError("request header is malformed")
    header = _fields(head[3:])
    expected_header = {
        "plan_digest": str(plan["result_digest"]),
        "scenario_id": str(plan["scenario_id"]),
        "turn": str(plan["turn"]),
        "assignment_id": str(plan["source_assignment_id"]),
        "query_count": str(plan["query_count"]),
        "authority": "NO_ORDERS",
        "application_authority": "PROHIBITED",
    }
    if header != expected_header:
        raise EmbeddedProbeBuildError("request header differs semantically from the saved plan")
    expected_queries = {str(q["query_id"]): q for q in plan["queries"]}
    seen: set[str] = set()
    for raw in lines[1:]:
        parts = raw.split("|")
        if parts[:3] != ["TRANS_FEAS_REQ", "1", "QUERY"]:
            raise EmbeddedProbeBuildError("request query record is malformed")
        values = _fields(parts[3:])
        qid = values.get("query_id")
        if qid not in expected_queries or qid in seen:
            raise EmbeddedProbeBuildError("request query identity is foreign or duplicated")
        seen.add(qid)
        query = expected_queries[qid]
        expected = {
            "plan_digest": str(plan["result_digest"]),
            "query_id": qid,
            "query_key": str(query["query_key"]),
            **{str(k): str(v).lower() if isinstance(v, bool) else str(v) for k, v in query["parameters"].items()},
        }
        if values != expected:
            raise EmbeddedProbeBuildError("request query differs semantically from the saved plan")
    if seen != set(expected_queries):
        raise EmbeddedProbeBuildError("request does not cover the exact saved-plan query set")


def build_embedded_probe(*, plan_path: Path, request_path: Path | None, output_dir: Path) -> dict[str, Any]:
    plan = json.loads(plan_path.read_text(encoding="utf-8-sig"))
    validate_plan(plan)
    canonical_request = _request_text(plan)
    if request_path is not None:
        if not request_path.is_file():
            raise EmbeddedProbeBuildError(f"request file not found: {request_path}")
        supplied = request_path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
        validate_request_against_plan(supplied, plan)
        canonical_request = supplied if supplied.endswith("\n") else supplied + "\n"
    else:
        validate_request_against_plan(canonical_request, plan)

    source = SOURCE_PATH.read_text(encoding="utf-8")
    if source.count(READER_PREFIX) != 1:
        raise EmbeddedProbeBuildError("canonical Lua request reader does not match the exact audited prefix")
    request_lines = canonical_request.rstrip("\n").split("\n")
    embedded_table = "local TRANS_FEAS_EMBEDDED_REQUEST_LINES = {\n" + "\n".join(
        f"    {_lua_quote_ascii(line)}," for line in request_lines
    ) + "\n}\n"
    embedded_reader = embedded_table + 'local function trans_feas_read_request()\n    local lines = {}\n    for index = 1, #TRANS_FEAS_EMBEDDED_REQUEST_LINES do\n        lines[#lines + 1] = TRANS_FEAS_EMBEDDED_REQUEST_LINES[index]\n    end\n    if #lines < 2 then\n        return nil\n    end\n'
    generated_source = source.replace(READER_PREFIX, embedded_reader, 1)
    generated_source = generated_source.replace(
        '{"request_file", "RELATIVE_GAME_ROOT_REQUEST_FILE"},',
        '{"request_file", "NOT_USED_EMBEDDED_REQUEST"},',
        1,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    generated_lua = output_dir / "transcendence_campaign_feasibility_probe.generated.lua"
    generated_lua.write_text(generated_source, encoding="utf-8", newline="\n")
    pack_path = output_dir / PACK_NAME
    pack_record = write_pfh5_pack([(INTERNAL_PATH, generated_source.encode("utf-8"))], pack_path, pack_type=3, timestamp=0)
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "contract": "CAMPAIGN_FEASIBILITY_EMBEDDED_REQUEST_PROBE_V1",
        "probe_kind": "campaign_feasibility",
        "pack_name": PACK_NAME,
        "pack_sha256": pack_record["pack_sha256"],
        "pack_size_bytes": pack_record["pack_size"],
        "generated_lua_sha256": sha256_path(generated_lua),
        "canonical_template_sha256": sha256_path(SOURCE_PATH),
        "saved_plan_sha256": sha256_path(plan_path),
        "plan_digest": plan["result_digest"],
        "scenario_id": plan["scenario_id"],
        "turn": plan["turn"],
        "assignment_id": plan["source_assignment_id"],
        "query_count": plan["query_count"],
        "request_sha256": sha256_bytes(canonical_request.encode("utf-8")),
        "request_source": "EMBEDDED_GENERATED",
        "query_keys": [item["query_key"] for item in plan["queries"]],
        "policy_authority": "NO_ORDERS",
        "application_authority": "PROHIBITED",
        "orders_emitted": False,
        "save_values_written": False,
        "gameplay_mutation": False,
        "save_mutation": False,
    }
    manifest_blob = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    (output_dir / "embedded_probe_manifest.json").write_text(manifest_blob, encoding="utf-8", newline="\n")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a one-session read-only WH3 feasibility probe with an exact saved request embedded in its Lua payload.")
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--request", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = build_embedded_probe(plan_path=args.plan, request_path=args.request, output_dir=args.output_dir)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
