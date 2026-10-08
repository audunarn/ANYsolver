"""One supervised six-selector screen on the isolated exact CI numerical site."""
from pathlib import Path
import hashlib, importlib.util, json, os, sys
ROOT = Path(__file__).resolve().parent; REPO = ROOT.parents[2]
BASE = Path(os.environ['TEMP'])/'r8-bl5-affine-flexible-v1/run.py'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(BASE) == 'ad9947c9268774a980041112004364d4daba6ce884fe339fab9f0d90b265d3ec'
spec = importlib.util.spec_from_file_location('bounded', BASE)
s = importlib.util.module_from_spec(spec); spec.loader.exec_module(s)
s.ROOT = ROOT; s.ENV.pop('PYTHONOPTIMIZE', None)
s.ENV.update(NUMEXPR_NUM_THREADS='1', NUMBER_OF_CPUS='1')
s.ENV['PYTHONPATH'] = os.pathsep.join((str(ROOT/'ci-site-network-v2'), str(REPO/'src'), str(REPO)))
files = ['src/anysolver/_stiffened_shell_ge_finite_experimental.py',
    'src/anysolver/_stiffened_shell_s3_algorithmic_pullback.py',
    'src/anysolver/_ge_beam3_variational_shell.py',
    'tests/test_stiffened_shell_native_arc.py', 'tests/test_stiffened_shell_native_s3_displacement.py',
    'tests/data/native_s3_fibre_history/unloaded-v1.bin',
    'examples/stiffened_shell_coupled_s3_adaptive_history.py']
(ROOT/'backend-ci-binding-v1.json').write_text(json.dumps(dict(
    files={name:sha(REPO/name) for name in files}, runner_sha256=sha(__file__),
    entry_sha256=sha(ROOT/'ci-entry-v1.py'), supervisor_sha256=sha(BASE),
    wheels={folder+'/'+p.name:sha(p) for folder in ('ci-wheels-network-v2','ci-wheels-network-v3')
            for p in sorted((ROOT/folder).glob('*.whl'))},
    scope='Six changed/failed selectors under exact CI dependency versions; no binding changes'),indent=2)+'\n')
s.supervise([sys.executable,str(ROOT/'ci-entry-v1.py')], 'backend-ci-v1', 2*1024**3)
