"""Installed B2 boundary: frozen public tests, explicit helpers, example."""
from pathlib import Path
from hashlib import sha256
import importlib.metadata
import json,os,sys,shutil
import numpy,scipy,scipy.linalg,numba,llvmlite,psutil,anysolver
from anysolver import _b2_physical_flexibility_linear,_b2_physical_linear_definition
from anysolver import _stiffened_shell_b2_physical_rigid_footprint,_stiffened_shell_b2_reference_buckling
from threadpoolctl import threadpool_info
RAW=Path(__file__).resolve().parent;REPO=RAW.parents[2]
TARGET=RAW/'installed-host-v1'
CI=REPO/'.qualification/b3-ge-e4-pl/r8-native-s3-restart-binding-dev-20261005-v1/ci-site-network-v2'
ARTIFACT=json.loads((RAW/'artifact-provenance-v1.json').read_text())
FROZEN=json.loads((RAW/'check-input-binding-v1.json').read_text())
CHECKS=RAW/'test-stage-v1'
assert CHECKS.is_dir() and not any(CHECKS.iterdir())
assert ARTIFACT['commit']=='b6ef85cff28513bdbdb078054decd9d80842dc8e'
assert sha256(Path(ARTIFACT['wheel']).read_bytes()).hexdigest()==ARTIFACT['wheel_sha256']
for name,digest in FROZEN['files'].items():
    assert sha256((REPO/name).read_bytes()).hexdigest()==digest,name
    target=CHECKS/name;target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(REPO/name,target)
    assert sha256(target.read_bytes()).hexdigest()==digest,name
sys.path.insert(0,str(CHECKS))
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

dependency_baseline={}
distribution_baseline={name:importlib.metadata.version(name) for name in ('ANYmaterial','ANYmesher','ANYfileio')}
previous_path=REPO/'.qualification/b3-ge-e4-pl/r8-b2-physical-rigid-footprint-installed-dev-20261006-v1/installed-imports-after-tests-v1.json'
previous=json.loads(previous_path.read_text())['dependency_origins']

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
            dependencies[name]=dict(path=str(path),version=getattr(module,'__version__',None),sha256=sha256(path.read_bytes()).hexdigest())
    dependency_modules={}
    for name,module in sys.modules.copy().items():
        if module is None or not any(name==p or name.startswith(p+'.') for p in ('anymaterial','anymesh','anymesher','anyfileio')):
            continue
        filename=getattr(module,'__file__',None)
        if filename is None: continue
        path=Path(filename).resolve()
        identity=dict(path=str(path),sha256=sha256(path.read_bytes()).hexdigest())
        if name in dependency_baseline: assert identity==dependency_baseline[name],(phase,name,'dependency identity drift')
        else: dependency_baseline[name]=identity
        dependency_modules[name]=identity
    distributions={name:importlib.metadata.version(name) for name in distribution_baseline}
    assert distributions==distribution_baseline,(phase,'dependency distribution drift')
    prior_comparison={name:dict(previous=previous.get(name),current=identity,
        unchanged=previous.get(name)==identity) for name,identity in dependencies.items()}
    result=dict(phase=phase,module_import_count=len(imports),all_anysolver_imports_installed=True,imports=imports,dependency_origins=dependencies,
        threadpools=threadpool_info(),affinity=psutil.Process().cpu_affinity(),numba_threads=numba.get_num_threads(),jit_disabled=bool(numba.config.DISABLE_JIT),sys_path=sys.path,
        dependency_modules=dependency_modules,dependency_distributions=distributions,
        prior_dependency_comparison=prior_comparison,prior_record_sha256=sha256(previous_path.read_bytes()).hexdigest())
    assert result['affinity']==[0] and result['numba_threads']==1 and result['jit_disabled']
    assert all(pool['num_threads']==1 for pool in result['threadpools'])
    assert str(REPO/'src') not in sys.path
    (RAW/('installed-imports-'+phase+'-v1.json')).write_text(json.dumps(result,indent=2)+'\n')
    return result

inspect_imports('before')
os.environ['B2_BATCH_EXAMPLE_RECORD']=str(RAW/'installed-batch-example-test-v1.json')
import pytest
arguments=['-q','-p','no:cacheprovider','-c',str(CHECKS/'pyproject.toml'),'-o','pythonpath=',
    '--basetemp',str(RAW/'pytest-temp-v1'),'--junitxml='+str(RAW/'installed-junit-v1.xml'),
    str(CHECKS/'tests/test_stiffened_shell_b2_physical_footprint_batch.py'),
    str(CHECKS/'tests/test_stiffened_shell_b2_physical_rigid_footprint.py')+'::test_explicit_refusals_and_legacy_request',
    str(CHECKS/'tests/test_stiffened_shell_b2_nodal_rigid_footprint.py')+'::test_selected_batches_one_factor_and_no_unselected_recovery',
    str(CHECKS/'tests/test_stiffened_shell_b2_nodal_rigid_footprint.py')+'::test_batch_complete_prefix_and_callback_lifetime']
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
from examples.stiffened_shell_b2_physical_rigid_footprint import batch_workflow,workflow
batch=batch_workflow(10)
(RAW/'installed-batch-example-v1.json').write_text(json.dumps(batch,indent=2)+'\n')
assert batch['status']=='completed' and batch['case_count']==10 and batch['factorization_count']==1 and batch['solve_count']==10 and batch['maximum_rhs_chunk']==1 and batch['production_qualified'] is False,batch
assert batch['footprint_law_id']=='B2_PHYSICAL_RIGID_FOOTPRINT_DIRECTOR_REFERENCE_V1_EXPERIMENTAL',batch
pad=workflow()
(RAW/'installed-footprint-example-v1.json').write_text(json.dumps(pad,indent=2)+'\n')
assert pad['status']=='ok' and pad['static_status']=='completed' and pad['production_qualified'] is False,pad
assert abs(pad['load_factors'][0]-.16324601652203263)<=1e-8*.16324601652203263,pad
final=inspect_imports('after-examples')
print(json.dumps(dict(batch_example=batch,physical_footprint_example=pad,installed_module_import_count=final['module_import_count'],all_anysolver_imports_installed=True,source_stage_wheel_site_bytes_equal=True,consumed_input_count=len(FROZEN['files'])),indent=2))
