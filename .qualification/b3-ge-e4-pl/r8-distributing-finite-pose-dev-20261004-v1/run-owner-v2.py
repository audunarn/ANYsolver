"""One serial local-map check; no external solver or formal F03 execution."""
from pathlib import Path
import hashlib
import importlib.util
import os
import sys

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
supervisor = Path(os.environ['TEMP'])/'r8-bl5-affine-flexible-v1/run.py'
if hashlib.sha256(supervisor.read_bytes()).hexdigest() != 'ad9947c9268774a980041112004364d4daba6ce884fe339fab9f0d90b265d3ec':
    raise ValueError('recorded bounded supervisor required')
spec = importlib.util.spec_from_file_location('bounded', supervisor)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.ROOT = ROOT
module.ENV = os.environ.copy()
module.ENV.pop('PYTHONOPTIMIZE', None)
module.ENV.update(OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1',
    MKL_NUM_THREADS='1', NUMBA_NUM_THREADS='1', NUMBA_DISABLE_JIT='1',
    BLIS_NUM_THREADS='1', VECLIB_MAXIMUM_THREADS='1', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
module.ENV['PYTHONPATH'] = os.pathsep.join((str(REPO/'src'),str(REPO),
    str(REPO/'.qualification/b3-ge-e4-pl/r8-distributing-multihost-dev-20261004-v1/site')))
module.supervise([sys.executable, '-u', str(ROOT/'probe-owner-v2.py')],
    'checks-owner-v2', 2*1024**3)
