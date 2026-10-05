"""One bounded changed-certificate source slice; not a qualification run."""
from pathlib import Path
import hashlib, importlib.util, json, os, sys
ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
BASE = Path(os.environ['TEMP'])/'r8-bl5-affine-flexible-v1/run.py'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(BASE) == 'ad9947c9268774a980041112004364d4daba6ce884fe339fab9f0d90b265d3ec'
spec = importlib.util.spec_from_file_location('bounded', BASE)
s = importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
s.ROOT = ROOT;s.ENV.pop('PYTHONOPTIMIZE', None)
SITE = ROOT.parent/'r8-native-s3-restart-binding-dev-20261005-v1/ci-site-network-v2'
s.ENV.update(NUMEXPR_NUM_THREADS='1', NUMBER_OF_CPUS='1', OPENBLAS_CORETYPE='Haswell')
s.ENV['PYTHONPATH'] = os.pathsep.join((str(SITE), str(REPO/'src'), str(REPO)))
files = ('src/anysolver/_stiffened_shell_s3_restart_certificate.py',
    'src/anysolver/_stiffened_shell_ge_finite_experimental.py',
    'src/anysolver/_stiffened_shell_ge_experimental.py',
    'src/anysolver/_stiffened_shell_affine_endpoint.py',
    'src/anysolver/_stiffened_shell_displacement_control.py',
    'src/anysolver/_stiffened_shell_arc_publication.py',
    'tests/test_stiffened_shell_s3_portable_restart.py',
    'tests/data/native_s3_fibre_history/unloaded-v1.bin')
OLD = SITE.parent
(ROOT/'binding-v1.json').write_text(json.dumps(dict(files={name:sha(REPO/name) for name in files},
    runner_sha256=sha(__file__), entry_sha256=sha(ROOT/'entry-v1.py'), supervisor_sha256=sha(BASE),
    wheels={folder+'/'+p.name:sha(p) for folder in ('ci-wheels-network-v2', 'ci-wheels-network-v3')
            for p in sorted((OLD/folder).glob('*.whl'))}), indent=2)+'\n')
s.supervise([sys.executable, str(ROOT/'entry-v1.py')], 'focused-v1', 2*1024**3)
