from pathlib import Path
import json,hashlib,runpy,sys
r=Path(__file__).resolve().parent
m=json.loads((r/'manifest.json').read_text())
for p,h in m['inputs_sha256'].items(): assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
for case in ('mz','mx','fy'):
 sys.argv=[str(r/'run_case.py'),'--case',case,'--output',str(r/(case+'.json'))]
 runpy.run_path(str(r/'run_case.py'),run_name='__main__')
 v=json.loads((r/(case+'.json')).read_text());print(json.dumps({k:v[k] for k in ('case','status','applied_work_j','beam_line_moment_about_root_nm','beam_ground_moment_about_root_nm','normal_couple_max') if k in v}),flush=True)
