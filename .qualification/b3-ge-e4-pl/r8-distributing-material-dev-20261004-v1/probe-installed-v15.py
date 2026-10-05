from pathlib import Path
import hashlib,importlib.metadata,json,os,runpy,sys,time
import numpy as np,pytest
from threadpoolctl import threadpool_info
from anysolver import stiffened_shell as ss
import anyfem.solve.stiffened_shell as consumer
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]
FEM=Path('C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer')
SITE=ROOT/'site'
assert Path(ss.__file__).resolve().is_relative_to(SITE)
assert Path(consumer.__file__).resolve().is_relative_to(SITE)
assert not sys.flags.optimize and os.environ['NUMBA_DISABLE_JIT']=='1'
pools=threadpool_info();assert pools and all(p['num_threads']==1 for p in pools)
sources={}
for package,repo in (('anysolver',REPO),('anyfem',FEM)):
    for path in (SITE/package).rglob('*.py'):
        relative=path.relative_to(SITE)
        assert path.read_bytes()==(repo/'src'/relative).read_bytes(),relative
        sources[str(relative).replace('\\','/')]=hashlib.sha256(path.read_bytes()).hexdigest()
solver_tests=[
 'tests/test_stiffened_shell_ge_distributing_material.py',
 'tests/test_stiffened_shell_ge_distributing_finite_public.py',
 'tests/test_stiffened_shell_ge_distributing_reference.py',
 'tests/test_stiffened_shell_curved_material_checkpoint.py::test_restored_fixed_predecessor_residual_and_tangent',
 'tests/test_stiffened_shell_curved_material_checkpoint.py::test_predecessor_checkpoint_requires_matching_policy_and_material',
 'tests/test_stiffened_shell_bl5_coupled_material.py::test_coupled_bl5_monotonic_lifecycle']
consumer_tests=[
 'tests/test_stiffened_shell_ge_finite_distributing_consumer.py',
 'tests/test_stiffened_shell_ge_distributing_consumer.py',
 'tests/test_stiffened_shell_ge_reference_modal_consumer.py::test_save_reopen_owns_exact_modal_definition_without_owner_assembly']
# Keep exact node selection discoverable before execution; missing nodes fail.
tests=[str(REPO/path) for path in solver_tests]+[str(FEM/path) for path in consumer_tests]
record=dict(scope='installed development integration, not qualification',
    sources=sources,pools=pools,tests=tests,
    wheels={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in
      (ROOT/'dist/anysolver-0.4.7-py3-none-any.whl',FEM/'.qualification/stiffened-shell/r8-ge-material-compatibility-dev-20261004-v1/dist/anyfem-0.4.1-py3-none-any.whl')},
    dependencies={name:importlib.metadata.version(name) for name in ('ANYsolver','ANYfem','ANYmaterial','numpy','scipy','pytest')})
out=ROOT/'installed-runtime-v15.json';out.open('x',encoding='utf-8').write(json.dumps(record,indent=2)+'\n')
start=time.monotonic()
status=pytest.main(['-q',*tests,'-p','no:cacheprovider','--basetemp',str(ROOT/'pytest-v15')])
record.update(exit_code=int(status),checks_seconds=time.monotonic()-start)
out.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
if status:raise SystemExit(status)
sys.path.insert(0,str(REPO/'examples'))
runpy.run_path(str(REPO/'examples/stiffened_shell_ge_distributing_material.py'),run_name='__main__')
record['example']='PASS';record['imported_paths']={name:module.__file__ for name,module in sys.modules.items()
    if (name=='anysolver' or name.startswith('anysolver.') or name=='anyfem' or name.startswith('anyfem.')) and getattr(module,'__file__',None)}
assert all(Path(path).resolve().is_relative_to(SITE) for path in record['imported_paths'].values())
out.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')


