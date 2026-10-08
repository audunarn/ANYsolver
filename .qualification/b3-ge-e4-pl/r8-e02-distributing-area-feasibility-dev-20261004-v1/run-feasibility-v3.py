from pathlib import Path
import hashlib
import importlib.util
import os
import sys

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
supervisor = Path(os.environ['TEMP'])/'r8-bl5-affine-flexible-v1/run.py'
assert hashlib.sha256(supervisor.read_bytes()).hexdigest() == 'ad9947c9268774a980041112004364d4daba6ce884fe339fab9f0d90b265d3ec'
spec = importlib.util.spec_from_file_location('bounded', supervisor)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.ROOT = ROOT
module.ENV = os.environ.copy()
module.ENV.pop('PYTHONOPTIMIZE',None)
module.ENV.update(OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
    NUMBA_NUM_THREADS='1', NUMBA_DISABLE_JIT='1', BLIS_NUM_THREADS='1',
    VECLIB_MAXIMUM_THREADS='1', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
module.ENV['PYTHONPATH'] = os.pathsep.join((str(REPO),
    str(REPO/'.qualification/b3-ge-e4-pl/r8-distributing-ge-owner-dev-20261004-v1/site')))
if sys.argv[1:] == ['native']:
    module.supervise([sys.executable,'-u',str(ROOT/'probe-feasibility-v3.py')],'native-v3',2*1024**3)
elif len(sys.argv)==2 and sys.argv[1] in ('Mx','Fy'):
    ccx = Path('C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/calculix-223/CalculiX-2.23.0-win-x64/bin/ccx.exe')
    assert hashlib.sha256(ccx.read_bytes()).hexdigest() == '27a9426a1ee2f72c38fbe892e0ffaf38e14867628ffd0235770261b6f3ec9c5f'
    module.ROOT = ROOT/('ccx-'+sys.argv[1]+'-v2')
    module.supervise([str(ccx),'-i','reference'],'execution',2*1024**3)
else:
    raise ValueError('one declared native/Mx/Fy job required')
