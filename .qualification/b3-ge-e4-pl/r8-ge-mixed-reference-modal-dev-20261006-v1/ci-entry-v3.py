"""One bounded development suite; process-tree limits belong to launch job."""
from pathlib import Path
from hashlib import sha256
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

RAW = Path(__file__).resolve().parent
REPO = RAW.parents[2]
SITE = REPO/'.qualification/b3-ge-e4-pl/r8-native-s3-restart-binding-dev-20261005-v1/ci-site-network-v2'
FILES = ('src/anysolver/_stiffened_shell_ge_reference_modal.py',
    'src/anysolver/_stiffened_shell_ge_experimental.py','src/anysolver/stiffened_shell.py',
    'src/anysolver/_stiffened_shell_physical_q4_mass.py',
    'src/anysolver/_stiffened_shell_physical_s3_mass.py',
    'src/anysolver/_stiffened_shell_ge_mixed_modal_mass.py',
    'tests/test_stiffened_shell_ge_mixed_reference_modal.py',
    'tests/test_stiffened_shell_physical_s3_mass.py',
    'tests/test_stiffened_shell_ge_reference_modal.py',
    'tests/test_stiffened_shell_physical_q4_mass.py',
    'examples/stiffened_shell_ge_mixed_reference_modes.py')
record = dict(python=sys.executable, imports={m.__name__:m.__file__ for m in
    (numpy,scipy,numba,llvmlite,anysolver)},
    versions={m.__name__:m.__version__ for m in (numpy,scipy,numba,llvmlite)},
    threadpools=threadpool_info(),affinity=psutil.Process().cpu_affinity(),
    jit_disabled=bool(numba.config.DISABLE_JIT),numba_threads=numba.get_num_threads(),
    environment={k:os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS',
        'OMP_NUM_THREADS','NUMEXPR_NUM_THREADS','NUMBA_NUM_THREADS','NUMBA_DISABLE_JIT')},
    unforced_backend={k:os.environ.get(k) for k in ('OPENBLAS_CORETYPE','NPY_DISABLE_CPU_FEATURES')},
    source_bindings={name:sha256((REPO/name).read_bytes()).hexdigest() for name in FILES})
(RAW/'effective-runtime-v3.json').write_text(json.dumps(record,indent=2)+'\n')
for module,version in ((numpy,'2.5.3'),(scipy,'1.18.1'),(numba,'0.68.0'),(llvmlite,'0.50.0')):
    assert module.__version__ == version,record
    assert Path(module.__file__).resolve().is_relative_to(SITE.resolve()),record
assert Path(anysolver.__file__).resolve().is_relative_to((REPO/'src').resolve()),record
assert record['affinity'] == [0] and record['jit_disabled'],record
assert record['numba_threads'] == 1,record
assert all(item['num_threads'] == 1 for item in record['threadpools']),record
assert all(value == '1' for value in record['environment'].values()),record
assert not any(record['unforced_backend'].values()),record
SNAPSHOT = RAW/'source-snapshot-v3'
for name in FILES:
    target=SNAPSHOT/name
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes((REPO/name).read_bytes())
import pytest
raise SystemExit(pytest.main(['-q','-p','no:cacheprovider',
    '--basetemp',str(RAW/'pytest-temp-v3'),'--junitxml='+str(RAW/'junit-v3.xml'),
    '-k','independent_dense_qz_on_actual_full_mixed_pencil or independent_curved_centered_lift_kinetic_work',
    str(REPO/'tests/test_stiffened_shell_ge_mixed_reference_modal.py'),
    str(REPO/'tests/test_stiffened_shell_physical_s3_mass.py'),
    str(REPO/'tests/test_stiffened_shell_ge_reference_modal.py'),
    str(REPO/'tests/test_stiffened_shell_physical_q4_mass.py')]))
