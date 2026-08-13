from __future__ import annotations
import argparse, csv, hashlib, json
from collections import defaultdict
from pathlib import Path

TARGET_TABLES = [
'cai_gds_task_generators_tables',
'cai_task_management_system_task_generator_groups_generators_junctions_tables',
'cai_task_management_system_task_generator_variable_group_junctions_tables',
'cai_task_management_system_task_generator_variables_tables',
'cai_task_management_system_variable_group_junctions_tables',
'cai_task_management_system_variables_tables',
'cai_variables_tables','cai_variables_overides_tables','cai_personalities_tables',
'cai_personality_strategic_components_tables','cai_personality_variables_tables',
'cai_personality_variable_set_junctions_tables','cai_personalities_budget_allocations_tables',
'cai_personalities_income_allocations_tables','cai_personality_faction_potential_modifiers_tables',
'cai_query_variable_set_junctions_tables','campaign_ai_manager_behaviour_junctions_tables',
'cdir_military_generator_template_ratios_tables','cdir_military_generator_unit_qualities_tables']

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
    return h.hexdigest()

def table_from_path(path: Path) -> str | None:
    parts=[p.lower() for p in path.parts]
    for t in TARGET_TABLES:
        if t.lower() in parts: return t
    for part in path.parts:
        low=part.lower()
        if low.startswith('cai_decision_') and low.endswith('_tables'): return part
    return None

def read_tsv(path: Path):
    # RPFM documentation has described both metadata-first and columns-first
    # two-header-row TSV variants across interfaces/versions. Accept both, but
    # never guess a data row into a header.
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        raw_rows = list(csv.reader(f, delimiter='\t', quoting=csv.QUOTE_NONE))
    raw_rows = [r for r in raw_rows if r and not all(x == '' for x in r)]
    if not raw_rows:
        return [], [], None
    metadata = None
    if raw_rows[0][0].startswith('#'):
        if len(raw_rows) < 2:
            return [], [], '\t'.join(raw_rows[0])
        metadata = '\t'.join(raw_rows[0])
        header = raw_rows[1]
        data_rows = raw_rows[2:]
    else:
        header = raw_rows[0]
        if len(raw_rows) > 1 and raw_rows[1][0].startswith('#'):
            metadata = '\t'.join(raw_rows[1])
            data_rows = raw_rows[2:]
        else:
            data_rows = raw_rows[1:]
    rows = []
    for raw in data_rows:
        if raw and raw[0].startswith('#'):
            raise ValueError(f'unexpected metadata/comment row inside data: {path}')
        if len(raw) < len(header):
            raw += [''] * (len(header) - len(raw))
        rows.append(dict(zip(header, raw[:len(header)])))
    return header, rows, metadata

def load_key_spec(path: Path | None):
    if path is None or not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding='utf-8'))
    # Canonical key-spec documents carry metadata at the top level and put
    # table definitions under `tables`. Also accept a direct mapping for
    # backwards-compatible one-off research fixtures.
    if isinstance(raw, dict) and isinstance(raw.get('tables'), dict):
        return raw['tables']
    return raw

def main():
    ap=argparse.ArgumentParser(description='Inventory and row-diff schema-aware RPFM TSV exports without guessing primary keys.')
    ap.add_argument('--root',type=Path,required=True,help='exports/<source>/... root')
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--key-spec',type=Path,default=None)
    args=ap.parse_args()
    spec=load_key_spec(args.key_spec)
    sources={}
    for source_dir in sorted(p for p in args.root.iterdir() if p.is_dir()):
        tables=defaultdict(list)
        for p in source_dir.rglob('*.tsv'):
            t=table_from_path(p)
            if t: tables[t].append(p)
        out_tables={}
        for table,files in sorted(tables.items()):
            headers=None; combined=[]; file_records=[]; metadata=[]
            for p in sorted(files):
                h,rows,meta=read_tsv(p)
                if headers is None: headers=h
                elif h!=headers: raise SystemExit(f'header mismatch for {table}: {p}')
                combined.extend(rows)
                file_records.append({'path':str(p.relative_to(args.root)),'sha256':sha256(p),'rows':len(rows)})
                if meta: metadata.append(meta)
            out_tables[table]={'headers':headers or [],'row_count':len(combined),'files':file_records,'metadata':metadata,'rows':combined}
        sources[source_dir.name]=out_tables

    report={'schema_version':1,'authority':'OFFLINE_RESEARCH_ONLY','sources':{},'diffs':[],'limitations':[]}
    for source,tables in sources.items():
        report['sources'][source]={t:{k:v for k,v in d.items() if k!='rows'} for t,d in tables.items()}

    if 'vanilla' not in sources:
        report['limitations'].append('No source directory named vanilla; row diffs were not produced.')
    else:
        for source,tables in sources.items():
            if source=='vanilla': continue
            for table,mod in tables.items():
                vanilla=sources['vanilla'].get(table)
                if not vanilla:
                    report['diffs'].append({'source':source,'table':table,'status':'TABLE_NOT_PRESENT_IN_VANILLA_EXPORT','mod_rows':mod['row_count']}); continue
                keys=spec.get(table,{}).get('primary_keys',[])
                if not keys:
                    report['diffs'].append({'source':source,'table':table,'status':'KEY_SPEC_REQUIRED','vanilla_rows':vanilla['row_count'],'mod_rows':mod['row_count']}); continue
                missing=[k for k in keys if k not in vanilla['headers'] or k not in mod['headers']]
                if missing:
                    report['diffs'].append({'source':source,'table':table,'status':'KEY_COLUMNS_MISSING','keys':keys,'missing':missing}); continue
                def idx(rows):
                    out={}
                    for row in rows:
                        key=tuple(row.get(k,'') for k in keys)
                        if key in out: raise SystemExit(f'duplicate primary key {table} {key} in {source}')
                        out[key]=row
                    return out
                vi=idx(vanilla['rows']); mi=idx(mod['rows'])
                added=sorted(set(mi)-set(vi)); removed=sorted(set(vi)-set(mi)); changed=[]; same=0
                for key in sorted(set(vi)&set(mi)):
                    cells=[]
                    for col in vanilla['headers']:
                        if vi[key].get(col,'') != mi[key].get(col,''):
                            cells.append({'column':col,'vanilla':vi[key].get(col,''),'mod':mi[key].get(col,'')})
                    if cells: changed.append({'key':key,'changed_cells':cells})
                    else: same+=1
                report['diffs'].append({'source':source,'table':table,'status':'DIFFED','primary_keys':keys,'added_rows':added,'removed_rows':removed,'changed_rows':changed,'same_row_count':same})
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2,sort_keys=True),encoding='utf-8')
    unresolved=sum(1 for d in report['diffs'] if d.get('status')=='KEY_SPEC_REQUIRED')
    diffed=sum(1 for d in report['diffs'] if d.get('status')=='DIFFED')
    print(f'WROTE {args.out} sources={len(sources)} diffed={diffed} key_spec_required={unresolved}')

if __name__=='__main__': main()
