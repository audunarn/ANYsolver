"""Installed artifact boundary: public suite and standalone example workflow."""
from pathlib import Path
from hashlib import sha256
import importlib.metadata
import json
import os
import sys
import numpy
import scipy
import scipy.linalg
import numba
import llvmlite
import psutil
import anysolver
from threadpoolctl import threadpool_info

RAW=Path(__file__).resolve().parent
REPO=RAW.parents[2]
TARGET=RAW/'installed-v2'
CI=REPO/'.qualification/b3-ge-e4-pl/r8-native-s3-restart-binding-dev-20261005-v1/ci-site-network-v2'
ARTIFACT=json.loads((RAW/'artifact-provenance-v2.json').read_text())
assert sha256(Path(ARTIFACT['wheel']).read_bytes()).hexdigest()==ARTIFACT['wheel_sha256']
TESTS=('tests/test_stiffened_shell_ge_mixed_reference_modal.py',
    'tests/test_stiffened_shell_physical_s3_mass.py',
    'tests/test_stiffened_shell_ge_reference_modal.py',
    'tests/test_stiffened_shell_physical_q4_mass.py')
BOUND=TESTS+('examples/stiffened_shell_ge_mixed_reference_modes.py',
    'examples/stiffened_shell_native_fibre_bl5.py')
record=dict(python=sys.executable,commit=ARTIFACT['commit'],wheel_sha256=ARTIFACT['wheel_sha256'],
    installed_version=importlib.metadata.version('ANYsolver'),
    imports={m.__name__:m.__file__ for m in (numpy,scipy,numba,llvmlite,anysolver)},
    versions={m.__name__:m.__version__ for m in (numpy,scipy,numba,llvmlite)},
    affinity=psutil.Process().cpu_affinity(),threadpools=threadpool_info(),
    numba_threads=numba.get_num_threads(),jit_disabled=bool(numba.config.DISABLE_JIT),
    sys_path=sys.path,environment={k:os.environ.get(k) for k in
        ('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS','NUMEXPR_NUM_THREADS',
         'NUMBA_NUM_THREADS','NUMBA_DISABLE_JIT','PYTHONDONTWRITEBYTECODE')},
    unforced_backend={k:os.environ.get(k) for k in ('OPENBLAS_CORETYPE','NPY_DISABLE_CPU_FEATURES')},
    consumed_bindings={name:sha256((REPO/name).read_bytes()).hexdigest() for name in BOUND},
    pytest_override='-o pythonpath=')
(RAW/'effective-installed-runtime-v2.json').write_text(json.dumps(record,indent=2)+'\n')
for module,version in ((numpy,'2.5.3'),(scipy,'1.18.1'),(numba,'0.68.0'),(llvmlite,'0.50.0')):
    assert module.__version__==version,record
    assert Path(module.__file__).resolve().is_relative_to(CI.resolve()),record
assert record['installed_version']=='0.4.7'
assert record['affinity']==[0] and record['numba_threads']==1 and record['jit_disabled']
assert all(pool['num_threads']==1 for pool in record['threadpools'])
assert all(value=='1' for value in record['environment'].values())
assert not any(record['unforced_backend'].values())
assert str(REPO/'src') not in sys.path


def inspect_imports(phase):
    imports={}
    for name,module in sys.modules.copy().items():
        if (name=='anysolver' or name.startswith('anysolver.')) and module is not None:
            path=Path(module.__file__).resolve()
            assert path.is_relative_to(TARGET.resolve()),(phase,name,str(path))
            relative=path.relative_to(TARGET.resolve()).as_posix()
            digest=sha256(path.read_bytes()).hexdigest()
            assert ARTIFACT['payload'][relative]==digest,(phase,name,relative)
            imports[name]=dict(path=str(path),sha256=digest)
    dependencies={name:str(getattr(module,'__file__',None)) for name,module in sys.modules.copy().items()
        if module is not None and name in ('anymaterial','anymesh','anymesher','anyfileio')}
    result=dict(phase=phase,module_import_count=len(imports),all_anysolver_imports_installed=True,
        imports=imports,dependency_origins=dependencies,threadpools=threadpool_info(),
        affinity=psutil.Process().cpu_affinity(),numba_threads=numba.get_num_threads())
    assert result['affinity']==[0] and result['numba_threads']==1
    assert all(pool['num_threads']==1 for pool in result['threadpools'])
    (RAW/('installed-imports-'+phase+'-v2.json')).write_text(json.dumps(result,indent=2)+'\n')
    return result


inspect_imports('before')
for name in BOUND:
    target=RAW/'consumed-source-snapshot-v2'/name
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes((REPO/name).read_bytes())
import pytest
arguments=['-q','-p','no:cacheprovider','-o','pythonpath=',
    '--basetemp',str(RAW/'pytest-temp-v2'),'--junitxml='+str(RAW/'installed-junit-v2.xml'),
    *(str(REPO/name) for name in TESTS)]
(RAW/'installed-pytest-command-v2.json').write_text(json.dumps(arguments,indent=2)+'\n')
code=pytest.main(arguments)
inspect_imports('after-tests')
if code:
    raise SystemExit(code)
from examples.stiffened_shell_ge_mixed_reference_modes import workflow
example=workflow()
(RAW/'installed-example-v2.json').write_text(json.dumps(example,indent=2)+'\n')
assert example['status']=='completed',example
assert len(example['frequencies_hz'])==2 and all(v>0. for v in example['frequencies_hz'])
assert example['production_qualified'] is False
final=inspect_imports('after-example')
for name,digest in ARTIFACT['payload'].items():
    assert sha256((TARGET/name).read_bytes()).hexdigest()==digest,name
    assert sha256((REPO/'src'/name).read_bytes()).hexdigest()==digest,name
print(json.dumps(dict(example=example,installed_module_import_count=final['module_import_count'],
    all_anysolver_imports_installed=True,source_wheel_site_bytes_equal=True),indent=2))
