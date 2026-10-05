"""Verify the exact isolated CI numerical dependencies before six selected tests."""
from pathlib import Path
import json, os, sys
import numpy
import scipy.linalg
import numba
import llvmlite
import psutil
import anysolver
from threadpoolctl import threadpool_info
ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
SITE = ROOT/'ci-site-network-v2'
modules = (numpy, scipy, numba, llvmlite, anysolver)
record = dict(python=sys.executable, imports={m.__name__:m.__file__ for m in modules},
    versions={m.__name__:getattr(m,'__version__',None) for m in modules},
    threadpools=threadpool_info(), affinity=psutil.Process().cpu_affinity(),
    jit_disabled=bool(numba.config.DISABLE_JIT), environment={key:os.environ.get(key) for key in
        ('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS','NUMEXPR_NUM_THREADS','NUMBA_NUM_THREADS','NUMBA_DISABLE_JIT')})
(ROOT/'ci-effective-runtime-v2.json').write_text(json.dumps(record, indent=2)+'\n')
for module, version in ((numpy,'2.5.3'), (scipy,'1.18.1'), (numba,'0.68.0'), (llvmlite,'0.50.0')):
    assert module.__version__ == version, record
    assert Path(module.__file__).resolve().is_relative_to(SITE.resolve()), record
assert len(record['affinity']) == 1 and record['jit_disabled']
assert all(row['num_threads'] == 1 for row in record['threadpools'])
assert all(value == '1' for value in record['environment'].values())
from hashlib import sha256
expected = json.loads((ROOT/'backend-ci-binding-v2.json').read_text())['files']
actual = {name:sha256((REPO/name).read_bytes()).hexdigest() for name in expected}
assert actual == expected, (actual, expected)
record['source_bindings'] = actual
(ROOT/'ci-effective-runtime-v2.json').write_text(json.dumps(record, indent=2)+'\n')
import pytest
raise SystemExit(pytest.main(['-q','-p','no:cacheprovider',
    '--basetemp',str(ROOT/'pytest-temp-backend-ci-v2'),
    '--junitxml='+str(ROOT/'backend-ci-junit-v2.xml'),
    str(REPO/'tests/test_stiffened_shell_native_arc.py'),
    str(REPO/'tests/test_stiffened_shell_native_s3_displacement.py'),
    '-k','s3-fibre or elastic_s3_displacement']))
