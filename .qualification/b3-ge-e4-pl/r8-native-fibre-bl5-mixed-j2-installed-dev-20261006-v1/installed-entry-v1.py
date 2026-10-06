from pathlib import Path
from hashlib import sha256
import importlib.metadata,json,os,sys,time,traceback
import numpy,scipy,numba,llvmlite,psutil,anysolver
from threadpoolctl import threadpool_info
RAW=Path(__file__).resolve().parent;REPO=RAW.parents[2];TARGET=RAW/'installed-host-v1';CHECKS=RAW/'check-stage-v1'
CI=REPO/'.qualification/b3-ge-e4-pl/r8-native-s3-restart-binding-dev-20261005-v1/ci-site-network-v2'
ART=json.loads((RAW/'artifact-provenance-v1.json').read_text());INPUT=json.loads((RAW/'check-input-binding-v1.json').read_text())
STARTED=time.monotonic();CAP=float(os.environ['INSTALLED_PROCESS_CAP']);SYS_PATH_INITIAL=list(sys.path)
sys.path.insert(0,str(CHECKS))
for n,d in INPUT['files'].items():assert sha256((CHECKS/n).read_bytes()).hexdigest()==sha256((REPO/n).read_bytes()).hexdigest()==d,n
assert sha256((RAW/ART['wheel']).read_bytes()).hexdigest()==ART['wheel_sha256']
assert importlib.metadata.version('ANYsolver')=='0.4.7'
assert str(REPO/'src') not in sys.path and not (CHECKS/'src').exists()
for m,v in ((numpy,'2.5.3'),(scipy,'1.18.1'),(numba,'0.68.0'),(llvmlite,'0.50.0')):
    assert m.__version__==v and Path(m.__file__).resolve().is_relative_to(CI.resolve())
distributions={n:importlib.metadata.version(n) for n in ('ANYmaterial','ANYmesher','ANYfileio')}
sibling_baseline={};sibling_roots=('anymaterial','anymesh','anymesher','anyfileio')
def inspect(phase):
    pools=threadpool_info();affinity=psutil.Process().cpu_affinity()
    assert affinity==[0] and numba.get_num_threads()==1 and numba.config.DISABLE_JIT
    assert all(p['num_threads']==1 for p in pools)
    env={n:os.environ.get(n) for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','NUMBA_NUM_THREADS','NUMBA_DISABLE_JIT','PYTHONDONTWRITEBYTECODE')}
    forced={n:os.environ.get(n) for n in ('OPENBLAS_CORETYPE','NPY_DISABLE_CPU_FEATURES')}
    assert all(v=='1' for v in env.values()) and not any(forced.values())
    imports={};siblings={}
    for name,module in list(sys.modules.items()):
        filename=getattr(module,'__file__',None)
        if filename is None:continue
        path=Path(filename).resolve()
        if name=='anysolver' or name.startswith('anysolver.'):
            assert path.is_relative_to(TARGET.resolve()),(phase,name,str(path))
            relative=path.relative_to(TARGET.resolve()).as_posix();digest=sha256(path.read_bytes()).hexdigest()
            assert ART['payload'][relative]==digest,(phase,name,relative)
            imports[name]=dict(path=str(path),sha256=digest,payload_key=relative)
        elif any(name==p or name.startswith(p+'.') for p in sibling_roots):
            item=dict(path=str(path),sha256=sha256(path.read_bytes()).hexdigest())
            if name in sibling_baseline:assert item==sibling_baseline[name],(phase,name,'readonly sibling changed')
            else:sibling_baseline[name]=item
            siblings[name]=item
    assert {n:importlib.metadata.version(n) for n in distributions}==distributions
    record=dict(phase=phase,commit=ART['commit'],wheel_sha256=ART['wheel_sha256'],installed_version='0.4.7',actual_installed_import_count=len(imports),all_anysolver_imports_installed=True,imports=imports,readonly_sibling_modules=siblings,dependency_distributions=distributions,pins={m.__name__:dict(path=str(Path(m.__file__).resolve()),version=m.__version__) for m in (numpy,scipy,numba,llvmlite)},affinity=affinity,pools=pools,numba_threads=numba.get_num_threads(),jit_disabled=bool(numba.config.DISABLE_JIT),unforced_backend=forced,environment=env,sys_path=list(sys.path),cwd=str(Path.cwd()))
    (RAW/('installed-imports-'+phase+'-v1.json')).write_text(json.dumps(record,indent=2)+'\n')
    return record
inspect('before')
try:
    import pytest
    arguments=['-q','-p','no:cacheprovider','-c',str(CHECKS/'pyproject.toml'),'-o','pythonpath=','--basetemp',str(RAW/'pytest-temp-v1'),'--junitxml='+str(RAW/'installed-junit-v1.xml'),str(CHECKS/'tests/test_native_fibre_bl5_mixed_j2_displacement.py')]
    (RAW/'installed-pytest-command-v1.json').write_text(json.dumps(arguments,indent=2)+'\n')
    status=pytest.main(arguments);after_tests=inspect('after-tests')
    (RAW/'installed-result-v1.json').write_text(json.dumps(dict(pytest_exit_code=int(status),fresh_test_case_count=8,actual_installed_import_count=after_tests['actual_installed_import_count']),indent=2)+'\n')
    if status:raise SystemExit(status)
    remaining=CAP-(time.monotonic()-STARTED)
    example=dict(executed=False,remaining_process_seconds=remaining,minimum_remaining_seconds=90,reason='remaining process budget below registered example margin')
    if remaining>=90:
        from examples.stiffened_shell_native_fibre_bl5_mixed_j2_displacement import workflow
        begun=time.monotonic();value=workflow();elapsed=time.monotonic()-begun
        assert value['status']=='completed' and value['shell_alpha_max']>0 and value['fibre_alpha_max']>0 and value['fresh_restore_bytes_equal'] and value['continued_bytes_equal'] and not value['production_qualified']
        example=dict(executed=True,elapsed_seconds=elapsed,result=value,remaining_before_seconds=remaining,scope='public new mixed-J2 example only; no historical workflows')
    (RAW/'installed-public-example-v1.json').write_text(json.dumps(example,indent=2)+'\n')
    final=inspect('after-example')
    for n,d in ART['payload'].items():assert sha256((TARGET/n).read_bytes()).hexdigest()==sha256((REPO/'src'/n).read_bytes()).hexdigest()==d
    for n,d in INPUT['files'].items():assert sha256((CHECKS/n).read_bytes()).hexdigest()==sha256((REPO/n).read_bytes()).hexdigest()==d
    print(json.dumps(dict(status='completed',fresh_cases=8,actual_installed_imports=final['actual_installed_import_count'],payload_count=len(ART['payload']),example_executed=example['executed'])))
except BaseException:
    (RAW/'installed-failure-v1.txt').write_text(traceback.format_exc());raise
finally:
    inspect('terminal')
