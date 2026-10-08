"""Serial bounded source/build/install checks for the existing owner boundary."""
from pathlib import Path
import hashlib, importlib.util, os, sys

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
p = Path(os.environ['TEMP'])/'r8-bl5-affine-flexible-v1/run.py'
if hashlib.sha256(p.read_bytes()).hexdigest() != 'ad9947c9268774a980041112004364d4daba6ce884fe339fab9f0d90b265d3ec':
    raise ValueError('pinned bounded supervisor required')
s = importlib.util.spec_from_file_location('bounded', p)
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)
m.ROOT = ROOT
m.ENV = os.environ.copy()
m.ENV.pop('PYTHONOPTIMIZE', None)
for key, value in {'OPENBLAS_NUM_THREADS':'1', 'OMP_NUM_THREADS':'1',
    'MKL_NUM_THREADS':'1', 'NUMBA_NUM_THREADS':'1', 'NUMBA_DISABLE_JIT':'1',
    'VECLIB_MAXIMUM_THREADS':'1', 'BLIS_NUM_THREADS':'1',
    'PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1'}.items():
    m.ENV[key] = value
action = sys.argv[1] if len(sys.argv) == 2 else None
if action in ('source', 'installed', 'example'):
    m.ENV['PYTHONPATH'] = str(REPO/'src') if action == 'source' else str(ROOT/'site')
    m.ENV['R8_DISTRIBUTING_OWNER_KIND'] = action
    m.supervise([sys.executable, '-u', str(ROOT/'probe-v1.py')], action+'-v1', 2*1024**3)
elif action == 'consumer':
    m.ENV['PYTHONPATH'] = os.pathsep.join((str(ROOT/'site'),
        'C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer/src'))
    m.supervise([sys.executable, '-u', str(ROOT/'consumer-probe-v1.py')], 'consumer-v1', 2*1024**3)
elif action == 'build':
    m.ENV.pop('PYTHONPATH', None)
    m.supervise([sys.executable, '-m', 'build', '--wheel', '--no-isolation',
        '--outdir', str(ROOT/'dist'), str(REPO)], 'build-v1', 2*1024**3)
elif action == 'install':
    m.ENV.pop('PYTHONPATH', None)
    wheels = list((ROOT/'dist').glob('*.whl'))
    if len(wheels) != 1 or (ROOT/'site').exists():
        raise ValueError('one fresh wheel/site required')
    m.supervise([sys.executable, '-m', 'pip', 'install', '--no-deps', '--no-index',
        '--target', str(ROOT/'site'), str(wheels[0])], 'install-v1', 2*1024**3)
else:
    raise ValueError('source/build/install/installed/example/consumer action required')
