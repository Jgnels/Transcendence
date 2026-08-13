from __future__ import annotations

import argparse, hashlib, json, zipfile
from pathlib import Path

REPO_ROOT=Path(__file__).resolve().parents[2]
FILES=(
 "runtime_probe/tools/Prepare-NativeDiagnosticCapture.ps1",
 "runtime_probe/tools/Collect-NativeDiagnosticCapture.ps1",
 "runtime_probe/tools/prepare_native_diagnostic_capture.py",
 "runtime_probe/tools/collect_native_diagnostic_capture.py",
 "runtime_probe/tools/verify_native_diagnostic_profile.py",
 "runtime_probe/tools/run_native_diagnostic_telemetry.py",
 "runtime_probe/tools/build_probe_packs.py",
 "runtime_probe/manifests/native_diagnostic_pack.json",
 "runtime_probe/source/script/campaign/mod/transcendence_native_diagnostic_probe.lua",
 "synthetic_lab/transcendence_lab/__init__.py",
 "synthetic_lab/transcendence_lab/canonical.py",
 "synthetic_lab/transcendence_lab/native_diagnostic.py",
)

def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()

def build(root:Path,out:Path)->dict:
 rows=[]; blobs=[]
 for rel in FILES:
  b=(root/rel).read_bytes(); blobs.append((rel,b)); rows.append({'path':rel,'size_bytes':len(b),'sha256':sha(b)})
 readme=(root/'intake/NATIVE_DIAGNOSTIC_OWNER_HANDOFF_v0.2M.md').read_bytes(); blobs.append(('README_FIRST.md',readme)); rows.append({'path':'README_FIRST.md','size_bytes':len(readme),'sha256':sha(readme)})
 manifest={'contract':'NATIVE_CAI_DIAGNOSTIC_OWNER_KIT_V1','authority':'NO_ORDERS','application_authority':'PROHIBITED','research_visibility':'PRIVILEGED_OMNISCIENT_DIAGNOSTIC','application_eligible':False,'contains_private_machine_paths':False,'contains_raw_game_or_workshop_pack_bytes':False,'files':sorted(rows,key=lambda x:x['path'])}
 manifest['manifest_digest']=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 blobs.append(('OWNER_KIT_MANIFEST.json',(json.dumps(manifest,indent=2,sort_keys=True)+'\n').encode()))
 out.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for name,b in sorted(blobs):
   i=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0));i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o100644<<16;z.writestr(i,b)
 if zipfile.ZipFile(out).testzip() is not None: raise ValueError('owner kit ZIP integrity failed')
 return {'output':str(out),'size_bytes':out.stat().st_size,'sha256':sha(out.read_bytes()),'entry_count':len(blobs),'manifest_digest':manifest['manifest_digest']}

def main()->int:
 p=argparse.ArgumentParser();p.add_argument('--repo-root',type=Path,default=REPO_ROOT);p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(build(a.repo_root.resolve(),a.output.resolve()),indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
