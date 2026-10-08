"""Record effective runtime for the single supervised changed-route check."""
from pathlib import Path
import json
import os
import sys


def pytest_sessionstart(session):
    import numpy
    import scipy.linalg
    import numba
    import psutil
    import anysolver
    from threadpoolctl import threadpool_info
    pools = threadpool_info()
    affinity = psutil.Process().cpu_affinity()
    record = dict(python=sys.executable, imports={m.__name__: m.__file__ for m in
        (numpy, scipy, numba, anysolver)}, threadpools=pools, affinity=affinity,
        numba_disable_jit_effective=bool(numba.config.DISABLE_JIT),
        environment={key: os.environ.get(key) for key in ('OMP_NUM_THREADS',
            'OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','NUMBA_NUM_THREADS','NUMBA_DISABLE_JIT')})
    (Path(__file__).parent/'focused-effective-runtime-v1.json').write_text(json.dumps(record, indent=2)+'\n')
    assert len(affinity) == 1
    assert numba.config.DISABLE_JIT
    assert pools and all(row['num_threads'] == 1 for row in pools)
    assert all(value == '1' for value in record['environment'].values())
