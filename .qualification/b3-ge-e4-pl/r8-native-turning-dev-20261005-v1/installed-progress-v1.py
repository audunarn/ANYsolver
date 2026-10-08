from pathlib import Path
import hashlib,json,os,sys
import pytest
from threadpoolctl import threadpool_info
from anysolver import stiffened_shell as ss
import anyfem.solve.stiffened_shell as consumer
raw=Path(__file__).resolve().parent;repo=raw.parents[2];site=raw/'site-progress-v1'
assert Path(ss.__file__).resolve().is_relative_to(site)
assert Path(consumer.__file__).resolve().is_relative_to(site)
assert os.environ['NUMBA_DISABLE_JIT']=='1' and not sys.flags.optimize
assert threadpool_info() and all(p['num_threads']==1 for p in threadpool_info())
artifacts=json.loads((raw/'artifact-progress-v1.json').read_bytes())['artifacts']
previous=json.loads((raw.parent/'r8-native-displacement-chart-dev-20261005-v1/installed-result-v3.json').read_bytes())
fem=Path('C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer')
sources={}
for name in previous['sources']:
    checkout=repo if name.startswith('anysolver/') else fem
    digest=hashlib.sha256((checkout/'src'/name).read_bytes()).hexdigest()
    assert hashlib.sha256((site/name).read_bytes()).hexdigest()==digest,name
    sources[name]=digest
for item in artifacts.values():assert hashlib.sha256(Path(item['wheel']).read_bytes()).hexdigest()==item['sha256']
record=dict(status='IN_PROGRESS',artifacts=artifacts,sources=sources,pools=threadpool_info())
def save():(raw/'installed-progress-result-v1.json').write_bytes((json.dumps(record,indent=2)+'\n').encode('ascii'))
save()
status=pytest.main(['-q','-p','no:cacheprovider',str(repo/'tests/test_stiffened_shell_native_arc_progress.py'),
    str(repo/'tests/test_stiffened_shell_native_arc.py'),'--junitxml='+str(raw/'installed-progress-junit-v1.xml')])
record.update(pytest_exit=status,status='FAILED_TESTS' if status else 'PASSED_INSTALLED_PROGRESS_DEVELOPMENT_NOT_QUALIFIED');save()
raise SystemExit(status)
