"""Exact S3 restart and displacement failure reproduction under existing limits."""
from pathlib import Path
import ast, hashlib, importlib.util, json, os, sys
ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
BASE = Path(os.environ['TEMP'])/'r8-bl5-affine-flexible-v1/run.py'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(BASE) == 'ad9947c9268774a980041112004364d4daba6ce884fe339fab9f0d90b265d3ec'
spec = importlib.util.spec_from_file_location('bounded', BASE)
s = importlib.util.module_from_spec(spec); spec.loader.exec_module(s)
s.ROOT = ROOT; s.ENV.pop('PYTHONOPTIMIZE', None)
s.ENV.update(NUMEXPR_NUM_THREADS='1', NUMBER_OF_CPUS='1')
s.ENV['PYTHONPATH'] = os.pathsep.join((str(ROOT), str(REPO/'src'), str(REPO)))
files = ['src/anysolver/_stiffened_shell_ge_finite_experimental.py',
    'src/anysolver/_stiffened_shell_s3_algorithmic_pullback.py',
    'tests/test_stiffened_shell_native_arc.py', 'tests/test_stiffened_shell_native_s3_displacement.py']
for name in files: ast.parse((REPO/name).read_text(encoding='utf-8-sig'), filename=name)
(ROOT/'rebase-binding-v3.json').write_text(json.dumps(dict(
    files={name:sha(REPO/name) for name in files}, supervisor_sha256=sha(BASE),
    parent='888be00b', runner_sha256=sha(__file__), scope='Two affected elastic S3 chart-event test repairs'), indent=2)+'\n')
s.supervise([sys.executable,'-m','pytest','-q','-p','no:cacheprovider',
    '-p','restart_runtime_probe_v3','--basetemp',str(ROOT/'pytest-temp-rebase-v3'),
    '--junitxml='+str(ROOT/'rebase-junit-v3.xml'),
    str(REPO/'tests/test_stiffened_shell_native_arc.py'),
    str(REPO/'tests/test_stiffened_shell_native_s3_displacement.py'),
    '-k','elastic_s3_displacement'], 'rebase-v3', 2*1024**3)
