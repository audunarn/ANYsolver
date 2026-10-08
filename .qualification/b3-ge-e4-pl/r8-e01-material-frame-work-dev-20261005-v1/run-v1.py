from pathlib import Path
import hashlib, importlib.util, json, os, sys
ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
BASE = Path(os.environ['TEMP'])/'r8-bl5-affine-flexible-v1/run.py'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(BASE) == 'ad9947c9268774a980041112004364d4daba6ce884fe339fab9f0d90b265d3ec'
spec = importlib.util.spec_from_file_location('bounded', BASE)
s = importlib.util.module_from_spec(spec); spec.loader.exec_module(s)
s.ROOT = ROOT; s.ENV.pop('PYTHONOPTIMIZE', None)
s.ENV.update(NUMEXPR_NUM_THREADS='1', NUMBER_OF_CPUS='1')
s.ENV['PYTHONPATH'] = os.pathsep.join((str(REPO/'scripts'), str(REPO/'src'), str(REPO)))
s.ENV['ANYSOLVER_DEVELOPMENT_SOURCE'] = str(REPO/'src')
s.ENV['ANYSOLVER_DEVELOPMENT_RECORD'] = str(ROOT/'runtime-v1.json')
source = [REPO/'scripts/r8_e01_material_frame_work.py', REPO/'tests/test_r8_e01_material_frame_work.py', REPO/'docs/reference_cases/stiffened_shell_e01_material_frame_work.md']
inputs = [Path('C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling/.qualification/b3-ge-e4-pl/r8-e01-pure-torque-dev-20260929-v4')/name for name in ('native-shell-action.json', 'external-shell-action.json')]
expected = ['2411b64903ed16a5cd7ac5f788b21497975d14df038a3563e9e85e45f5db42bd', 'b599bba7822f98e6bcac80785bf694eb833aa10cb6c77aa457cb0e4ee28b331c']
assert [sha(p) for p in inputs] == expected
(ROOT/'binding-v1.json').write_text(json.dumps(dict(source={str(p.relative_to(REPO)):sha(p) for p in source}, inputs={str(p):h for p,h in zip(inputs,expected)}, supervisor_sha256=sha(BASE), runner_sha256=sha(__file__), scope='Source-only linear port-map feasibility; no product/external solve or qualification'), indent=2)+'\n')
child = '''import json, sys, pathlib, pytest
from threadpoolctl import threadpool_info
from scripts import r8_e01_material_frame_work as work
root = pathlib.Path(sys.argv[1]); repo = root.parents[2]
code = pytest.main(['-q', '-p', 'no:cacheprovider', '-p', 'development_test_runtime', '--basetemp', str(root/'pytest-temp-v1'), '--junitxml='+str(root/'junit-v1.xml'), str(repo/'tests/test_r8_e01_material_frame_work.py')])
if code: sys.exit(code)
args = json.loads(sys.argv[2])
record = work.main(args)
pools = threadpool_info()
assert all(p['num_threads'] == 1 for p in pools), pools
(root/'diagnostic-runtime-v1.json').write_text(json.dumps(dict(effective_pools=pools, imported_map=work.__file__, source_sha256=record['source_sha256'], qualified=False), indent=2)+'\\n')
print(json.dumps(dict(captures=len(record['captures']), samples=[len(c['diagnostic']['samples']) for c in record['captures']], qualified=False, effective_pool_threads=[p['num_threads'] for p in pools])))
'''
args = []
for p,h in zip(inputs,expected): args += ['--capture', str(p), '--expected-sha256', h]
args += ['--output', str(ROOT/'saved-fields-v1.json')]
s.supervise(['C:/Python/Python314/python.exe', '-c', child, str(ROOT), json.dumps(args)], 'focused-v1', 2*1024**3)
result = json.loads((ROOT/'focused-v1/execution.json').read_text())
sys.exit(0 if result['status']=='completed' and result['exit_code']==0 else 1)
