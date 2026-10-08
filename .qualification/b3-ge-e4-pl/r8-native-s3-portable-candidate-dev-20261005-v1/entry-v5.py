from pathlib import Path
import hashlib, json, os
import numpy, scipy.linalg, numba, llvmlite, psutil, anysolver
from threadpoolctl import threadpool_info
ROOT = Path(__file__).resolve().parent;REPO = ROOT.parents[2]
SITE = ROOT.parent/'r8-native-s3-restart-binding-dev-20261005-v1/ci-site-network-v2'
modules = (numpy, scipy, numba, llvmlite, anysolver)
record = dict(imports={m.__name__:m.__file__ for m in modules},
    versions={m.__name__:getattr(m, '__version__', None) for m in modules}, pools=threadpool_info(),
    affinity=psutil.Process().cpu_affinity(), jit_off=bool(numba.config.DISABLE_JIT),
    environment={k:os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'OMP_NUM_THREADS',
        'NUMEXPR_NUM_THREADS', 'NUMBA_NUM_THREADS', 'NUMBA_DISABLE_JIT', 'OPENBLAS_CORETYPE')})
(ROOT/'runtime-v5.json').write_text(json.dumps(record, indent=2)+'\n')
for module, version in ((numpy, '2.5.3'), (scipy, '1.18.1'), (numba, '0.68.0'), (llvmlite, '0.50.0')):
    assert module.__version__ == version and Path(module.__file__).resolve().is_relative_to(SITE.resolve()), record
assert len(record['affinity']) == 1 and record['jit_off']
assert all(p['num_threads'] == 1 and p['architecture'] == 'Haswell' for p in record['pools']), record
assert all(v == '1' for k, v in record['environment'].items() if k != 'OPENBLAS_CORETYPE'), record
expected = json.loads((ROOT/'binding-v5.json').read_text())['files']
assert expected == {name:hashlib.sha256((REPO/name).read_bytes()).hexdigest() for name in expected}
import pytest
raise SystemExit(pytest.main(['-q', '-p', 'no:cacheprovider', '--basetemp', str(ROOT/'pytest-temp-v5'),
    '--junitxml='+str(ROOT/'junit-v5.xml'), str(REPO/'tests/test_stiffened_shell_s3_portable_restart.py')+'::test_portable_old_seed_preserves_bytes_and_reports_margin', str(REPO/'tests/test_stiffened_shell_s3_portable_restart.py')+'::test_portable_checksum_valid_changed_physical_association_is_atomic[predecessor]']))



