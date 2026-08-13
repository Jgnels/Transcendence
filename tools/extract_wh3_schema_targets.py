from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

TARGETS=[
'cai_gds_task_generators_tables','cai_task_management_system_task_generator_groups_generators_junctions_tables',
'cai_task_management_system_task_generator_variable_group_junctions_tables','cai_task_management_system_task_generator_variables_tables',
'cai_task_management_system_variable_group_junctions_tables','cai_task_management_system_variables_tables','cai_variables_tables',
'cai_variables_overides_tables','cai_personalities_tables','cai_personality_strategic_components_tables','cai_personality_variables_tables',
'cai_personality_variable_set_junctions_tables','cai_personalities_budget_allocations_tables','cai_personalities_income_allocations_tables',
'cai_personality_faction_potential_modifiers_tables','cai_query_variable_set_junctions_tables','campaign_ai_manager_behaviour_junctions_tables',
'cdir_military_generator_template_ratios_tables','cdir_military_generator_unit_qualities_tables']
EXPECTED_BLOB='232216808ff5d38edd9e056c7828afdc1700d297'

def git_blob(data:bytes):
    return hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('schema',type=Path); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--radius',type=int,default=12000)
    a=ap.parse_args(); data=a.schema.read_bytes(); text=data.decode('utf-8',errors='replace')
    a.out.mkdir(parents=True,exist_ok=True)
    manifest={'schema_path':str(a.schema),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'git_blob_sha1':git_blob(data),'expected_git_blob_sha1':EXPECTED_BLOB,'exact_patch_8_1':git_blob(data)==EXPECTED_BLOB,'targets':{}}
    dynamic=[]
    # Discover cai_decision table names from nearby schema text.
    import re
    dynamic=sorted(set(re.findall(r'cai_decision_[A-Za-z0-9_]*_tables',text)))
    for target in TARGETS+dynamic:
        locs=[]; start=0
        while True:
            i=text.find(target,start)
            if i<0: break
            locs.append(i); start=i+len(target)
        manifest['targets'][target]={'occurrences':len(locs),'offsets':locs}
        if locs:
            chunks=[]
            for n,i in enumerate(locs[:5],1):
                lo=max(0,i-a.radius); hi=min(len(text),i+len(target)+a.radius)
                chunks.append(f'===== occurrence {n} offset {i} =====\n'+text[lo:hi])
            (a.out/(target+'.txt')).write_text('\n\n'.join(chunks),encoding='utf-8')
    (a.out/'schema_target_manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True),encoding='utf-8')
    print(f"schema git_blob={manifest['git_blob_sha1']} exact_patch_8_1={manifest['exact_patch_8_1']} targets_found={sum(1 for v in manifest['targets'].values() if v['occurrences'])}/{len(manifest['targets'])}")
if __name__=='__main__': main()
