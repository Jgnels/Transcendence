from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import struct
from collections import defaultdict
from pathlib import Path

# This decoder is intentionally narrow and fail-closed. Every listed layout was
# accepted only after consuming the complete owner-exported vanilla/mod files
# with zero trailing bytes. Unknown tables remain inventory-only.

def parse_header(data: bytes) -> dict:
    o = 0
    guid = None
    version = 0
    if data[:4] == b"\xfd\xfe\xfc\xff":
        n = struct.unpack_from("<H", data, 4)[0]
        guid = data[6:6 + 2*n].decode("utf-16le")
        o = 6 + 2*n
    if data[o:o+4] == b"\xfc\xfd\xfe\xff":
        version = struct.unpack_from("<i", data, o+4)[0]
        o += 8
    mysterious = bool(data[o]); o += 1
    rows = struct.unpack_from("<I", data, o)[0]; o += 4
    return {"guid": guid, "version": version, "mysterious": mysterious, "rows": rows, "data_offset": o}

def s8(data: bytes, o: int):
    n = struct.unpack_from("<H", data, o)[0]; o += 2
    return data[o:o+n].decode("utf-8"), o+n

def optional_s8(data: bytes, o: int):
    flag = data[o]; o += 1
    if flag == 0: return None, o
    if flag != 1: raise ValueError(f"invalid OptionalStringU8 flag={flag} at offset={o-1}")
    return s8(data, o)

def f32(data: bytes, o: int): return struct.unpack_from("<f", data, o)[0], o+4

def cai_variables(d,o):
    key,o=s8(d,o); value,o=f32(d,o); description,o=s8(d,o)
    return {"key":key,"value":value,"description":description},o

def tms_variables(d,o):
    value,o=f32(d,o); key,o=s8(d,o)
    return {"key":key,"value":value},o

def tms_variable_group(d,o):
    group,o=s8(d,o); value,o=f32(d,o); variable,o=s8(d,o)
    return {"group":group,"variable":variable,"value":value},o

def tg_variables(d,o):
    value,o=s8(d,o); key,o=s8(d,o)
    return {"key":key,"value":value},o

def tg_variable_group(d,o):
    value,o=s8(d,o); variable,o=s8(d,o); group,o=s8(d,o)
    return {"group":group,"variable":variable,"value":value},o

def tg_group(d,o):
    priority,o=f32(d,o); group,o=s8(d,o); generator,o=s8(d,o); variable_group,o=optional_s8(d,o)
    return {"group":group,"generator":generator,"variable_group":variable_group,"priority":priority},o

def variable_overrides(d,o):
    key,o=s8(d,o); campaign,o=s8(d,o); campaign_type,o=optional_s8(d,o); difficulty,o=optional_s8(d,o); value,o=f32(d,o)
    return {"key":key,"campaign":campaign,"campaign_type":campaign_type,"difficulty":difficulty,"value":value},o

def personality_variable_set(d,o):
    variable,o=s8(d,o); set_name,o=s8(d,o); value,o=s8(d,o)
    return {"set":set_name,"variable":variable,"value":value},o

def manager_behaviour(d,o):
    manager,o=s8(d,o); behaviour,o=s8(d,o); priority,o=f32(d,o)
    return {"manager":manager,"behaviour":behaviour,"priority":priority},o

LAYOUTS = {
    "cai_variables_tables": (cai_variables, ("key",), "FULL_BINARY_LAYOUT_VERIFIED"),
    "cai_task_management_system_variables_tables": (tms_variables, ("key",), "FULL_BINARY_LAYOUT_VERIFIED"),
    "cai_task_management_system_variable_group_junctions_tables": (tms_variable_group, ("group","variable"), "FULL_BINARY_LAYOUT_VERIFIED"),
    "cai_task_management_system_task_generator_variables_tables": (tg_variables, ("key",), "FULL_BINARY_LAYOUT_VERIFIED"),
    "cai_task_management_system_task_generator_variable_group_junctions_tables": (tg_variable_group, ("group","variable"), "FULL_BINARY_LAYOUT_VERIFIED"),
    "cai_task_management_system_task_generator_groups_generators_junctions_tables": (tg_group, ("group","generator","variable_group"), "PROVISIONAL_COMPOSITE_KEY_SCHEMA_CERTIFICATION_PENDING"),
    "cai_variables_overides_tables": (variable_overrides, ("key","campaign","campaign_type","difficulty"), "FULL_BINARY_LAYOUT_VERIFIED"),
    "cai_personality_variable_set_junctions_tables": (personality_variable_set, ("set","variable"), "FULL_BINARY_LAYOUT_VERIFIED"),
    "campaign_ai_manager_behaviour_junctions_tables": (manager_behaviour, ("manager","behaviour"), "FULL_BINARY_LAYOUT_VERIFIED"),
}

def norm(value):
    if isinstance(value,float):
        if math.isclose(value, round(value), abs_tol=1e-7): return int(round(value))
        return round(value,8)
    return value

def canon(row): return {k:norm(v) for k,v in row.items()}
def kt(row, fields): return tuple(row.get(x) for x in fields)

def table_name(path: Path, root: Path) -> str | None:
    try: rel=path.relative_to(root)
    except ValueError: return None
    parts=rel.parts
    if "db" not in parts: return None
    i=parts.index("db")
    return parts[i+1] if i+1 < len(parts) else None

def decode(path: Path, decoder):
    data=path.read_bytes(); h=parse_header(data); o=h["data_offset"]; rows=[]
    for _ in range(h["rows"]):
        row,o=decoder(data,o); rows.append(row)
    if o != len(data): raise ValueError(f"layout did not consume file: ended={o} bytes={len(data)} trailing={len(data)-o}")
    return h,rows

def sha256(path: Path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> int:
    ap=argparse.ArgumentParser(description="Fail-closed row diff for exact binary DB payloads extracted by RPFM.")
    ap.add_argument("--root",type=Path,required=True,help="exports/<source>/db/... root")
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--csv",type=Path,default=None)
    args=ap.parse_args()

    sources={}
    inventory=[]
    for source_dir in sorted(p for p in args.root.iterdir() if p.is_dir()):
        tables=defaultdict(list)
        for path in sorted(p for p in source_dir.rglob("*") if p.is_file()):
            table=table_name(path,args.root)
            if not table: continue
            h=parse_header(path.read_bytes())
            inventory.append({"source":source_dir.name,"table":table,"file":str(path.relative_to(args.root)).replace("\\","/"),"bytes":path.stat().st_size,"sha256":sha256(path),**h})
            if table in LAYOUTS: tables[table].append(path)
        sources[source_dir.name]={}
        for table,paths in tables.items():
            decoder,keys,key_status=LAYOUTS[table]
            rows=[]; files=[]
            try:
                for path in paths:
                    h,part=decode(path,decoder);rows.extend(part);files.append({"path":str(path.relative_to(args.root)).replace("\\","/"),**h})
            except Exception as exc:
                sources[source_dir.name][table]={"status":"DECODE_FAILED_CLOSED","error":str(exc)}
                continue
            key_values=[kt(r,keys) for r in rows]
            duplicate_count=len(key_values)-len(set(key_values))
            sources[source_dir.name][table]={"status":"DECODED","rows":rows,"row_count":len(rows),"files":files,"key_fields":list(keys),"key_status":key_status,"duplicate_keys_under_spec":duplicate_count}

    report={"schema_version":1,"authority":"OFFLINE_RESEARCH_ONLY","format":"RPFM_EXTRACTED_BINARY_DB","inventory":inventory,"sources":{},"diffs":[],"limitations":["Exact pinned schema key metadata was not present in the 2026-08-02 owner bundle; the task-generator junction composite key remains provisional."]}
    for source,tables in sources.items():
        report["sources"][source]={table:{k:v for k,v in record.items() if k!="rows"} for table,record in tables.items()}
    vanilla=sources.get("vanilla",{})
    for source,tables in sources.items():
        if source=="vanilla": continue
        for table,mod in tables.items():
            if mod.get("status")!="DECODED": continue
            base=vanilla.get(table)
            if not base or base.get("status")!="DECODED":
                report["diffs"].append({"source":source,"table":table,"status":"TABLE_NOT_DECODED_IN_VANILLA"});continue
            keys=tuple(base["key_fields"])
            if base["duplicate_keys_under_spec"] or mod["duplicate_keys_under_spec"]:
                report["diffs"].append({"source":source,"table":table,"status":"KEY_NOT_UNIQUE_FAIL_CLOSED","keys":list(keys)});continue
            bi={kt(r,keys):r for r in base["rows"]}; mi={kt(r,keys):r for r in mod["rows"]}
            entries=[]
            for key,mrow in sorted(mi.items(),key=lambda x:str(x[0])):
                brow=bi.get(key)
                if brow is None:
                    entries.append({"status":"MOD_ONLY_ROW","key":list(key),"mod":canon(mrow)});continue
                changes={c:{"vanilla":norm(brow.get(c)),"mod":norm(mrow.get(c))} for c in sorted(set(brow)|set(mrow)) if norm(brow.get(c))!=norm(mrow.get(c))}
                if changes: entries.append({"status":"OVERRIDE_CHANGED","key":list(key),"changes":changes,"vanilla":canon(brow),"mod":canon(mrow)})
                else: entries.append({"status":"OVERRIDE_SAME_AS_VANILLA","key":list(key),"vanilla":canon(brow)})
            counts=defaultdict(int)
            for x in entries: counts[x["status"]]+=1
            report["diffs"].append({"source":source,"table":table,"status":"DIFFED","key_fields":list(keys),"key_status":base["key_status"],"vanilla_rows":base["row_count"],"mod_rows":mod["row_count"],"counts":dict(counts),"entries":entries})
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    if args.csv:
        args.csv.parent.mkdir(parents=True,exist_ok=True)
        with args.csv.open("w",newline="",encoding="utf-8") as f:
            w=csv.writer(f);w.writerow(["table","source","status","key","changes","vanilla","mod"])
            for d in report["diffs"]:
                if d.get("status")!="DIFFED":continue
                for e in d["entries"]:
                    w.writerow([d["table"],d["source"],e["status"],json.dumps(e["key"],ensure_ascii=False),json.dumps(e.get("changes",{}),ensure_ascii=False),json.dumps(e.get("vanilla"),ensure_ascii=False),json.dumps(e.get("mod"),ensure_ascii=False)])
    print(f"PASS binary inventory={len(inventory)} diff_records={sum(1 for d in report['diffs'] if d.get('status')=='DIFFED')}")
    return 0

if __name__=="__main__": raise SystemExit(main())
