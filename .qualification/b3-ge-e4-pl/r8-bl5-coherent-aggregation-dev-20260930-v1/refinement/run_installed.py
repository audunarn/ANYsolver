from pathlib import Path
import hashlib,json,runpy,sys
r=Path.cwd();m=json.loads((r/'manifest.json').read_text())
w=Path(r'C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling')
source=json.loads((r/'source-manifest.json').read_text())
assert all(hashlib.sha256((w/p).read_bytes()).hexdigest()==h for p,h in source.items())
assert all(hashlib.sha256((Path(m['site'])/p.replace('src/','',1)).read_bytes()).hexdigest()==h for p,h in source.items())
assert all(hashlib.sha256((r/'fixtures'/p).read_bytes()).hexdigest()==h for p,h in m['fixtures_sha256'].items())
sys.argv=[str(r/'run_case.py'),'--output',str(r/'result.json'),'--refine-from',str(r/'predecessor.json')]
runpy.run_path(str(r/'run_case.py'),run_name='__main__')
v=json.loads((r/'result.json').read_text());print(json.dumps({'status':v['status'],'operator_constructions':v['operator_constructions'],'assignments':len(v['cases'])}),flush=True)
