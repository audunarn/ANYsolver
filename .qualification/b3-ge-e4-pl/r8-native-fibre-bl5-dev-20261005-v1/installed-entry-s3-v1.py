from pathlib import Path
import hashlib,json,os,runpy
import anysolver,numpy,scipy.linalg,numba,llvmlite,psutil
from threadpoolctl import threadpool_info
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2];SITE=ROOT/'installed-s3-v1'
CI=ROOT.parent/'r8-native-s3-restart-binding-dev-20261005-v1/ci-site-network-v2'
record=dict(imports={m.__name__:m.__file__ for m in (anysolver,numpy,scipy,numba,llvmlite)},
 versions={m.__name__:getattr(m,'__version__',None) for m in (anysolver,numpy,scipy,numba,llvmlite)},
 environment={k:os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS','NUMEXPR_NUM_THREADS','NUMBA_NUM_THREADS','NUMBA_DISABLE_JIT','OPENBLAS_CORETYPE')},pools=threadpool_info(),affinity=psutil.Process().cpu_affinity(),jit_off=bool(numba.config.DISABLE_JIT))
(ROOT/'installed-runtime-s3-v1.json').write_text(json.dumps(record,indent=2)+'\n')
assert Path(anysolver.__file__).resolve().is_relative_to(SITE.resolve()),record
for module,version in ((numpy,'2.5.3'),(scipy,'1.18.1'),(numba,'0.68.0'),(llvmlite,'0.50.0')):
 assert module.__version__==version and Path(module.__file__).resolve().is_relative_to(CI.resolve()),record
assert len(record['affinity'])==1 and record['jit_off'] and all(p['num_threads']==1 for p in record['pools'])
binding=json.loads((ROOT/'binding-s3-v1.json').read_text())
for name,expected in binding['files'].items():
 assert hashlib.sha256((REPO/name).read_bytes()).hexdigest()==expected,name
 if name.startswith('src/anysolver/'):
  assert hashlib.sha256((SITE/name.removeprefix('src/')).read_bytes()).hexdigest()==expected,name
source={str(path.relative_to(REPO/'src')):hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (REPO/'src/anysolver').rglob('*.py')}
installed={str(path.relative_to(SITE)):hashlib.sha256(path.read_bytes()).hexdigest()
           for path in (SITE/'anysolver').rglob('*.py')}
assert source==json.loads((ROOT/'source-package-modules-s3-v1.json').read_text())
assert record['environment']['OPENBLAS_CORETYPE'] is None,record
assert all(v=='1' for k,v in record['environment'].items() if k!='OPENBLAS_CORETYPE'),record
assert source==installed,'entire installed package module bytes differ from source'
(ROOT/'installed-package-modules-s3-v1.json').write_text(json.dumps(source,indent=2)+'\n')
import pytest,sys
code=pytest.main(['-q','-p','no:cacheprovider','--basetemp',str(ROOT/'installed-pytest-temp-s3-v1'),
 '--junitxml='+str(ROOT/'installed-junit-s3-v1.xml'),str(REPO/'tests/test_stiffened_shell_native_fibre_bl5_s3.py'),str(REPO/'tests/test_stiffened_shell_native_fibre_bl5.py'),
 str(REPO/'tests/test_stiffened_shell_ge_point_buckling.py')+'::test_explicit_admission_and_legacy_namespace_are_preserved',
 str(REPO/'tests/test_stiffened_shell_bl5_finite.py')+'::test_nonmatching_finite_history_physical_recovery_rebase_restart[3-p0]'])
loaded={name:module.__file__ for name,module in sys.modules.items()
        if name=='anysolver' or name.startswith('anysolver.') if getattr(module,'__file__',None)}
assert all(Path(path).resolve().is_relative_to(SITE.resolve()) for path in loaded.values()),loaded
(ROOT/'installed-loaded-modules-s3-v1.json').write_text(json.dumps(loaded,indent=2)+'\n')
assert code==0,'installed focused regressions failed'
example=runpy.run_path(str(REPO/'examples/stiffened_shell_native_fibre_bl5.py'))
results={}
for shell in ('s3','mixed'):
 result=example['workflow'](count=2,shell=shell)
 (ROOT/('installed-example-'+shell+'-v1.json')).write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
 assert result['status']=='completed',result
 assert result['fresh_restore_bytes_equal'] and result['continued_bytes_equal'] and result['accepted_checkpoint_unchanged']
 assert result['free_equilibrium_ratio']<=1e-8 and result['constraint_max']<=1e-9,result
 assert max(result['equation_residuals'])<=1e-8 and max(result['constraint_residuals'])<=1e-8
 results[shell]=result
print(json.dumps(dict(package_module_count=len(source),loaded_module_count=len(loaded),examples=results),indent=2,allow_nan=False))
