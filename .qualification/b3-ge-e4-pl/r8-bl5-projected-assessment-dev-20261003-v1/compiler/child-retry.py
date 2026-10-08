from pathlib import Path
import json, os, sys
import numpy, scipy, numba, anysolver
from threadpoolctl import threadpool_info
import pytest
ROOT = Path(__file__).resolve().parent
REPO = Path('C:/Github/ANYsolver/.perf2-worktrees/stiffened-main-reconcile-20261001')
pools = threadpool_info()
record = dict(executable=sys.executable, solver=anysolver.__file__, pools=pools,
    numba_threads=numba.config.NUMBA_NUM_THREADS, numba_jit_disabled=numba.config.DISABLE_JIT)
(ROOT/'effective-runtime-retry.json').write_text(json.dumps(record, indent=2)+'\n')
assert pools and all(p['num_threads'] == 1 for p in pools)
assert numba.config.NUMBA_NUM_THREADS == 1 and numba.config.DISABLE_JIT == 1
assert Path(anysolver.__file__).resolve().is_relative_to(REPO/'src')
assert os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] == '1'
args = ['-v', '-c', str(ROOT/'pytest.ini'), '--basetemp', str(ROOT/'pytest-retry-temp'), '-p', 'no:cacheprovider',
    str(REPO/'tests/test_stiffened_shell_bl5_projected_density.py')+'::test_finite_density_checkpoint_identity_and_same_candidate_restart']
(ROOT/'pytest-retry-args.json').write_text(json.dumps(args, indent=2)+'\n')
raise SystemExit(pytest.main(args))
