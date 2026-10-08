"""One changed mixed-route source check; historical full runner stays unexecuted."""
from pathlib import Path
import ast
import hashlib
import importlib.util
import json
import os
import sys

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
BASE = Path(os.environ['TEMP'])/'r8-bl5-affine-flexible-v1/run.py'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(BASE) == 'ad9947c9268774a980041112004364d4daba6ce884fe339fab9f0d90b265d3ec'
spec = importlib.util.spec_from_file_location('bounded', BASE)
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)
s.ROOT = ROOT
s.ENV.pop('PYTHONOPTIMIZE', None)
s.ENV.update(NUMEXPR_NUM_THREADS='1', NUMBER_OF_CPUS='1')
s.ENV['PYTHONPATH'] = os.pathsep.join((str(ROOT), str(REPO/'src'), str(REPO)))
files = ['src/anysolver/_stiffened_shell_ge_point_buckling.py',
    'src/anysolver/_stiffened_shell_ge_experimental.py', 'src/anysolver/stiffened_shell.py',
    'src/anysolver/_stiffened_shell_s3_conservative_buckling.py',
    'tests/test_stiffened_shell_ge_mixed_buckling.py',
    'examples/stiffened_shell_ge_mixed_buckling.py', 'scripts/r8_ge_mixed_buckling_dev.py',
    'docs/reference_cases/stiffened_shell_ge_mixed_buckling.md']
for name in files:
    if name.endswith('.py'):
        ast.parse((REPO/name).read_text(encoding='utf-8-sig'), filename=name)
(ROOT/'focused-binding-v1.json').write_text(json.dumps(dict(
    files={name: sha(REPO/name) for name in files}, runner_sha256=sha(__file__),
    supervisor_sha256=sha(BASE), scope='Changed mixed-route development checks only; no qualification'), indent=2)+'\n')
s.supervise([sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
    '-p', 'mixed_runtime_probe_v1', '--basetemp', str(ROOT/'pytest-temp-focused-v1'),
    '--junitxml='+str(ROOT/'focused-junit-v1.xml'),
    str(REPO/'tests/test_stiffened_shell_ge_mixed_buckling.py')], 'focused-source-v1', 2*1024**3)
