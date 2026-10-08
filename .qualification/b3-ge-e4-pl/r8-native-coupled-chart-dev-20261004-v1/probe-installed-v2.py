from pathlib import Path
import hashlib, importlib.metadata, json, os, subprocess, sys, time
import pytest
from threadpoolctl import threadpool_info
from anysolver import stiffened_shell as ss

root = Path(__file__).resolve().parent
repo = root.parents[2]
previous = root.parent/'r8-distributing-native-material-dev-20261004-v1'
site = previous/'site-v1'
assert Path(ss.__file__).resolve().is_relative_to(site)
assert not sys.flags.optimize and os.environ['NUMBA_DISABLE_JIT'] == '1'
import numpy, scipy.linalg
pools = threadpool_info()
assert pools and all(p['num_threads'] == 1 for p in pools)
original = json.loads((previous/'installed-runtime-v1.json').read_text())
for package_path, digest in original['sources'].items():
    assert hashlib.sha256((site/package_path).read_bytes()).hexdigest() == digest
    owner = repo if package_path.startswith('anysolver/') else Path(
        'C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer')
    assert hashlib.sha256((owner/'src'/package_path).read_bytes()).hexdigest() == digest
for artifact in original['artifacts'].values():
    assert hashlib.sha256(Path(artifact['wheel']).read_bytes()).hexdigest() == artifact['sha256']
test = repo/'tests/test_stiffened_shell_native_plastic_chart.py'
binding = dict(scope='simultaneous shell J2 fibre chart transport development check, not aggregate qualification',
    solver_source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip(),
    wheel=original['artifacts']['solver'], inherited_import_identity=str(previous/'installed-runtime-v1.json'),
    verified_source_files=len(original['sources']), pools=pools,
    test_sha256=hashlib.sha256(test.read_bytes()).hexdigest(),
    dependencies={name:importlib.metadata.version(name) for name in ('ANYsolver','ANYmaterial','numpy','scipy','pytest')})
out = root/'installed-runtime-v2.json'
out.open('x').write(json.dumps(binding,indent=2)+'\n')
started = time.monotonic()
status = pytest.main(['-q',str(test)+'::test_loaded_coupled_j2_fibre_cyclic_chart_transport','-p','no:cacheprovider','--basetemp',str(root/'pytest-v2'),
                     '-o','junit_family=legacy','--junitxml',str(root/'native-coupled-chart-v2.xml')])
binding.update(exit_code=int(status), elapsed_seconds=time.monotonic()-started,
    imports={name:module.__file__ for name,module in sys.modules.items()
             if (name == 'anysolver' or name.startswith('anysolver.')) and getattr(module,'__file__',None)})
assert all(Path(path).resolve().is_relative_to(site) for path in binding['imports'].values())
assert hashlib.sha256(test.read_bytes()).hexdigest() == binding['test_sha256']
out.write_text(json.dumps(binding,indent=2)+'\n')
raise SystemExit(status)
