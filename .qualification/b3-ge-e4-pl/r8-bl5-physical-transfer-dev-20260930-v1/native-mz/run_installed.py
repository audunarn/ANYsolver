from pathlib import Path
import json,hashlib,runpy,sys
r=Path(__file__).resolve().parent
m=json.loads((r/'manifest.json').read_text())
for p,h in m['inputs_sha256'].items(): assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
sys.argv=[str(r/'run_case.py'),'--output',str(r/'result.json')]
runpy.run_path(str(r/'run_case.py'),run_name='__main__')
print(json.dumps({k:v for k,v in json.loads((r/'result.json').read_text()).items() if k not in ('threads','station_records')}))
