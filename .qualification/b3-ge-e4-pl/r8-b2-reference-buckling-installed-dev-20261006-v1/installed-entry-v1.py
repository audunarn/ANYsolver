"""Installed B2 boundary: frozen public tests, explicit helpers, example."""
from pathlib import Path
from hashlib import sha256
import importlib.metadata
import json,os,sys,shutil
import numpy,scipy,scipy.linalg,numba,llvmlite,psutil,anysolver
from anysolver import _b2_physical_flexibility_linear,_b2_physical_linear_definition
from threadpoolctl import threadpool_info
RAW=Path(__file__).resolve().parent;REPO=RAW.parents[2]
TARGET=RAW/'installed-host-v1'
CI=REPO/'.qualification/b3-ge-e4-pl/r8-native-s3-restart-binding-dev-20261005-v1/ci-site-network-v2'
ARTIFACT=json.loads((RAW/'artifact-provenance-v1.json').read_text())
FROZEN=json.loads((RAW/'check-input-binding-v1.json').read_text())
CHECKS=RAW/'check-inputs-v1'
assert not CHECKS.exists()
assert ARTIFACT['commit']=='71dfeddbcc2d4328b251220ffeb8779ee5f93408'
assert sha256(Path(ARTIFACT['wheel']).read_bytes()).hexdigest()==ARTIFACT['wheel_sha256']
for name,digest in FROZEN['files'].items():
    assert sha256((REPO/name).read_bytes()).hexdigest()==digest,name
    target=CHECKS/name;target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(REPO/name,target)
    assert sha256(target.read_bytes()).hexdigest()==digest,name
record=dict(python=sys.executable,commit=ARTIFACT['commit'],wheel_sha256=ARTIFACT['wheel_sha256'],installed_version=importlib.metadata.version('ANYsolver'),
    imports={m.__name__:m.__file__ for m in (numpy,scipy,numba,llvmlite,anysolver)},versions={m.__name__:m.__version__ for m in (numpy,scipy,numba,llvmlite)},
    affinity=psutil.Process().cpu_affinity(),threadpools=threadpool_info(),numba_threads=numba.get_num_threads(),jit_disabled=bool(numba.config.DISABLE_JIT),sys_path=sys.path,
    environment={k:os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS','NUMEXPR_NUM_THREADS','NUMBA_NUM_THREADS','NUMBA_DISABLE_JIT','PYTHONDONTWRITEBYTECODE')},
    unforced_backend={k:os.environ.get(k) for k in ('OPENBLAS_CORETYPE','NPY_DISABLE_CPU_FEATURES')},consumed_bindings=FROZEN['files'],pytest_override='-o pythonpath=',staged_explicit_inputs=True)
(RAW/'effective-installed-runtime-v1.json').write_text(json.dumps(record,indent=2)+'\n')
for module,version in ((numpy,'2.5.3'),(scipy,'1.18.1'),(numba,'0.68.0'),(llvmlite,'0.50.0')):
    assert module.__version__==version and Path(module.__file__).resolve().is_relative_to(CI.resolve()),record
assert record['installed_version']=='0.4.7'
assert record['affinity']==[0] and record['numba_threads']==1 and record['jit_disabled']
assert all(pool['num_threads']==1 for pool in record['threadpools'])
assert all(value=='1' for value in record['environment'].values()) and not any(record['unforced_backend'].values())
assert str(REPO/'src') not in sys.path and not (CHECKS/'src').exists()

def inspect_imports(phase):
    imports={}
    for name,module in sys.modules.copy().items():
        if (name=='anysolver' or name.startswith('anysolver.')) and module is not None:
            path=Path(module.__file__).resolve()
            assert path.is_relative_to(TARGET.resolve()),(phase,name,str(path))
            relative=path.relative_to(TARGET.resolve()).as_posix();digest=sha256(path.read_bytes()).hexdigest()
            assert ARTIFACT['payload'][relative]==digest,(phase,name,relative)
            imports[name]=dict(path=str(path),sha256=digest)
    dependencies={}
    for name in ('anymaterial','anymesh','anymesher','anyfileio'):
        module=sys.modules.get(name)
        if module is not None:
            path=Path(module.__file__).resolve()
            assert path.is_relative_to(CI.resolve()),(phase,name,str(path))
            dependencies[name]=dict(path=str(path),version=getattr(module,'__version__',None),sha256=sha256(path.read_bytes()).hexdigest())
    result=dict(phase=phase,module_import_count=len(imports),all_anysolver_imports_installed=True,imports=imports,dependency_origins=dependencies,
        threadpools=threadpool_info(),affinity=psutil.Process().cpu_affinity(),numba_threads=numba.get_num_threads(),jit_disabled=bool(numba.config.DISABLE_JIT),sys_path=sys.path)
    assert result['affinity']==[0] and result['numba_threads']==1 and result['jit_disabled']
    assert all(pool['num_threads']==1 for pool in result['threadpools'])
    assert str(REPO/'src') not in sys.path
    (RAW/('installed-imports-'+phase+'-v1.json')).write_text(json.dumps(result,indent=2)+'\n')
    return result

inspect_imports('before')
os.environ['B2_BUCKLING_EXAMPLE_RECORD']=str(RAW/'installed-example-v1.json')
import pytest
arguments=['-q','-p','no:cacheprovider','-c',str(CHECKS/'pyproject.toml'),'-o','pythonpath=',
    '--basetemp',str(RAW/'pytest-temp-v1'),'--junitxml='+str(RAW/'installed-junit-v1.xml'),
    str(CHECKS/'tests/test_stiffened_shell_b2_reference_buckling.py'),
    str(CHECKS/'tests/test_stiffened_shell_b2_q4_panel_experimental.py')+'::test_multi_q4_multi_b2_panel_matches_bounded_dense_oracle']
(RAW/'installed-pytest-command-v1.json').write_text(json.dumps(arguments,indent=2)+'\n')
code=pytest.main(arguments)
final=inspect_imports('after-tests')
for name,digest in ARTIFACT['payload'].items():
    assert sha256((TARGET/name).read_bytes()).hexdigest()==digest,name
    assert sha256((REPO/'src'/name).read_bytes()).hexdigest()==digest,name
for name,digest in FROZEN['files'].items():
    assert sha256((CHECKS/name).read_bytes()).hexdigest()==digest,name
    assert sha256((REPO/name).read_bytes()).hexdigest()==digest,name
if code: raise SystemExit(code)
example=json.loads((RAW/'installed-example-v1.json').read_text())
assert example['status']=='ok' and example['production_qualified'] is False,example
assert len(example['load_factors'])==1 and abs(example['load_factors'][0]-24.60872920125391)<=1e-8*24.60872920125391,example
print(json.dumps(dict(example=example,installed_module_import_count=final['module_import_count'],all_anysolver_imports_installed=True,source_stage_wheel_site_bytes_equal=True,consumed_input_count=len(FROZEN['files'])),indent=2))
