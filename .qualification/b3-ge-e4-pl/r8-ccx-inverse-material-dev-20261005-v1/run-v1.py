"""Serial, bounded development execution; no qualification or force-case repair."""
from pathlib import Path
import hashlib, importlib.util, json, os, shutil, sys

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
PYTHON = 'C:/Python/Python314/python.exe'
BASE = Path(os.environ['TEMP'])/'r8-bl5-affine-flexible-v1/run.py'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(BASE) == 'ad9947c9268774a980041112004364d4daba6ce884fe339fab9f0d90b265d3ec'
spec = importlib.util.spec_from_file_location('bounded_supervisor', BASE)
supervisor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(supervisor)
supervisor.ROOT = ROOT
supervisor.ENV.update(NUMEXPR_NUM_THREADS='1', CCX_NPROC_RESULTS='1',
    CCX_NPROC_EQUATION_SOLVER='1', NUMBER_OF_CPUS='1', PYTHONPATH=str(REPO/'src'))
OLD = ROOT.parent/'r8-ccx-restricted-nonlinear-dev-20261005-v1'
NATIVE = ROOT.parent/'r8-restricted-nonlinear-reference-dev-20261005-v1/native-screen-v3/native.json'
EXE = Path('C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/calculix-223/CalculiX-2.23.0-win-x64/bin/ccx.exe')
binding = json.loads((ROOT/'binding.json').read_text())
for name, path in (
    ('native_json_sha256', NATIVE), ('native_status_sha256', NATIVE.parent/'status.json'),
    ('spring_control_sha256', OLD/'spring-control-v3/status.json'),
    ('shell_control_sha256', OLD/'shell-control-v3/status.json')):
    assert sha(path) == binding[name].lower(), name
assert sha(EXE) == '27a9426a1ee2f72c38fbe892e0ffaf38e14867628ffd0235770261b6f3ec9c5f'
SCRIPT = REPO/'scripts/r8_e04_ccx_restricted_membrane.py'
TEST = REPO/'tests/test_stiffened_shell_e04_ccx_restricted_membrane.py'
mode = sys.argv[1]
if mode == 'tests':
    for source, name in ((SCRIPT, 'executed-script-v1.py'), (TEST, 'executed-tests-v1.py')):
        assert not (ROOT/name).exists()
        shutil.copyfile(source, ROOT/name)
    (ROOT/'execution-binding-v1.json').write_text(json.dumps(dict(
        script_sha256=sha(SCRIPT), test_sha256=sha(TEST), supervisor_sha256=sha(BASE),
        runner_sha256=sha(__file__), executable_sha256=sha(EXE),
        scope='Development inverse discriminator; original force failure and E04/G4D remain open'), indent=2)+'\n')
    command = [PYTHON, '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
               '--basetemp', str(ROOT/'pytest-temp-v1'), str(TEST)]
else:
    frozen = json.loads((ROOT/'execution-binding-v1.json').read_text())
    assert sha(SCRIPT) == frozen['script_sha256']
    assert sha(TEST) == frozen['test_sha256']
    assert json.loads((ROOT/'tests-v1/execution.json').read_text())['status'] == 'completed'
    command = [PYTHON, str(SCRIPT), '--mode', 'full', '--exe', str(EXE),
        '--spring-control-json', str(OLD/'spring-control-v3/status.json'),
        '--shell-control-json', str(OLD/'shell-control-v3/status.json')]
    if mode == 'control':
        command += ['--inverse-elastic-control', '--output', str(ROOT/'inverse-control-v1')]
    elif mode == 'full':
        control = ROOT/'inverse-control-v1/status.json'
        assert json.loads(control.read_text())['status'] == 'COMPLETED_INVERSE_CONTROL'
        command += ['--inverse-response', '--native-input', str(NATIVE),
            '--inverse-control-json', str(control), '--output', str(ROOT/'inverse-response-v1')]
    else:
        raise ValueError('tests/control/full only')
supervisor.supervise(command, mode+'-v1', 2*1024**3)
