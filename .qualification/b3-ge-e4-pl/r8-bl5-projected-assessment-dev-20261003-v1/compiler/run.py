from pathlib import Path
import importlib.util, json, os, sys
ROOT = Path(__file__).resolve().parent
REPO = Path('C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001')
spec = importlib.util.spec_from_file_location('owned_supervisor', ROOT.parent/'r8-bl5-affine-flexible-v1/run.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
m.ROOT = ROOT
m.ENV['PYTHONPATH'] = os.pathsep.join(map(str, (REPO/'src', REPO, REPO/'tests')))
for key in ('NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'BLIS_NUM_THREADS'):
    m.ENV[key] = '1'
command = [sys.executable, '-u', str(ROOT/'child.py')]
(ROOT/'command.json').write_text(json.dumps(dict(command=command, repository=str(REPO),
    environment={k: m.ENV[k] for k in ('PYTHONPATH','OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS',
        'NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS','BLIS_NUM_THREADS','NUMBA_NUM_THREADS',
        'NUMBA_DISABLE_JIT','PYTEST_DISABLE_PLUGIN_AUTOLOAD')},
    limits=dict(seconds=600, sampled_tree_rss_bytes=1024**3)), indent=2)+'\n')
m.supervise(command, 'focused-run', 1024**3)
