"""Owned serial development checks for the conservative mixed buckling route."""
from pathlib import Path
import hashlib, importlib.util, json, os, shutil, sys

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
mode = sys.argv[1]
if mode == 'source':
    files = ['src/anysolver/_stiffened_shell_ge_point_buckling.py', 'src/anysolver/_stiffened_shell_ge_experimental.py', 'src/anysolver/stiffened_shell.py', 'src/anysolver/_stiffened_shell_q4_algorithmic_pullback.py', 'src/anysolver/_stiffened_shell_ge_finite_experimental.py', 'src/anysolver/_stiffened_shell_bl5_local_experimental.py', 'src/anysolver/_stiffened_shell_l1_local_experimental.py', 'tests/test_stiffened_shell_ge_point_buckling.py', 'tests/test_stiffened_shell_ge_line_buckling.py', 'tests/test_stiffened_shell_l1_assembly_experimental.py', 'tests/test_stiffened_shell_bl5_finite.py', 'tests/test_stiffened_shell_ge_experimental.py', 'scripts/r8_ge_line_buckling_dev.py']
    folder = ROOT/'executed-source-v1'
    folder.mkdir(exist_ok=False)
    hashes = {}
    for name in files:
        target = folder/name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO/name, target)
        hashes[name] = sha(target)
    (ROOT/'binding-v1.json').write_text(json.dumps(dict(source_parent='a4ee8a66',
        files=hashes, supervisor_sha256=sha(BASE), runner_sha256=sha(__file__),
        scope='Development only; G4B/full programme and different-family acceptance remain open'), indent=2)+'\n')
    s.ENV['PYTHONPATH'] = os.pathsep.join((str(REPO/'src'), str(REPO)))
    tests = ['tests/test_stiffened_shell_ge_point_buckling.py', 'tests/test_stiffened_shell_ge_line_buckling.py']
    command = [sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
        '--basetemp', str(ROOT/'pytest-temp-source-v1'),
        '--junitxml='+str(ROOT/'source-junit-v1.xml'), *(str(REPO/name) for name in tests)]
elif mode in ('build', 'installed'):
    binding = json.loads((ROOT/'binding-v1.json').read_text())
    assert all(sha(REPO/name) == digest for name, digest in binding['files'].items())
    assert json.loads((ROOT/'source-v1/execution.json').read_text())['status'] == 'completed'
    s.ENV['PYTHONPATH'] = os.pathsep.join((str(ROOT/'site-v1'), str(REPO)))
    command = [sys.executable, str(ROOT/(mode+'-v1.py'))]
else:
    raise ValueError('source/build/installed only')
s.supervise(command, mode+'-v1', 2*1024**3)
