"""One logging-only replay of the original failed worker; never qualification."""
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT/'src'))
sys.path.insert(0, str(ROOT))
if len(sys.argv) > 1:
    os.environ.setdefault('PHYSICAL_CAPTURE_OUTPUT', sys.argv[1])
if len(sys.argv) > 2:
    os.environ.setdefault('PHYSICAL_CAPTURE_SELECTION', sys.argv[2])
OUTPUT = Path(os.environ['PHYSICAL_CAPTURE_OUTPUT'])
OUTPUT.mkdir(parents=True, exist_ok=True)
os.environ['ANYSOLVER_CI_PROGRESS_RECORD'] = str(OUTPUT/'progress.json')
os.environ.setdefault('NUMBA_CACHE_DIR', str(OUTPUT/'numba-cache'))
selection_path = Path(os.environ.get('PHYSICAL_CAPTURE_SELECTION', ROOT/'scripts/ci_physical_capture_selection.json'))
selection = json.loads(selection_path.read_text())
args = selection['command'][3:]
args = [f'--basetemp={OUTPUT / "basetemp"}' if arg.startswith('--basetemp=') else arg for arg in args]
captured = {'scope': 'LOGGING_ONLY_NOT_QUALIFICATION', 'source_base': '1e0102033b3f181e0c5dc8dfce11a493fe06302d',
            'command': [sys.executable, '-m', 'pytest', *args], 'evaluations': [], 'failures': [],
            'capture_errors': []}

def hex_array(value):
    return {'dtype': str(value.dtype), 'shape': list(value.shape), 'strides': list(value.strides),
            'alignment_mod64': value.ctypes.data % 64,
            'hex': [float(v).hex() for v in value.flat]}

def hex_tree(value):
    if isinstance(value, float):
        return {'f64': value.hex()}
    if isinstance(value, dict):
        return {str(k): hex_tree(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [hex_tree(v) for v in value]
    return value

current = None
previous = None

def trace(frame, event, arg):
    if frame.f_code.co_name != 'evaluate' or 'general_contact' not in frame.f_code.co_filename:
        return None
    frame.f_trace_lines = False
    try:
        # Python 3.14 frame locals are a proxy whose keys() may be a list.
        values = frame.f_locals
        force_name = 'shell_forces' if 'shell_forces' in values else 'sf'
        moment_name = 'shell_moment' if 'shell_moment' in values else 'sm'
        if event == 'return' and {'corners', force_name, moment_name, 'residual'} <= set(values):
            if len(captured['evaluations']) < 8:
                fields = {name: hex_array(values[key]) for name, key in
                          [('corners', 'corners'), ('shell_forces', force_name),
                           ('shell_moment', moment_name), ('residual', 'residual')]}
                captured['evaluations'].append({'node': current, 'producer': frame.f_code.co_filename, **fields})
    except Exception as error:
        # Logging must never turn the original numerical outcome into another
        # exception. Record an observer gap rather than interrupt the producer.
        captured['capture_errors'].append(type(error).__name__ + ': ' + str(error))
    return trace

class Capture:
    def pytest_runtest_logstart(self, nodeid, location):
        global current, previous
        current = nodeid
        if 'test_anchored_accepted_fixture_exact_replay[' in nodeid:
            previous = sys.gettrace()
            sys.settrace(trace)

    def pytest_runtest_logfinish(self, nodeid, location):
        if 'test_anchored_accepted_fixture_exact_replay[' in nodeid:
            sys.settrace(previous)

    def pytest_exception_interact(self, node, call, report):
        failure = {'node': report.nodeid, 'exception': str(call.excinfo.value)}
        tb = call.excinfo.value.__traceback__
        while tb is not None:
            frame = tb.tb_frame
            if frame.f_code.co_name == '_restore' and 'native_multi_s3_static.py' in frame.f_code.co_filename:
                values = frame.f_locals
                for name in ('row', 'replay'):
                    if name in values:
                        failure[name+'_contact'] = hex_tree(values[name].get('contact'))
            tb = tb.tb_next
        captured['failures'].append(failure)

import pytest
code = 3
try:
    code = pytest.main(args, plugins=[Capture()])
except BaseException as error:
    captured['driver_exception'] = type(error).__name__ + ': ' + str(error)
finally:
    sys.settrace(previous)
captured['pytest_exit_code'] = int(code)
captured['python'] = sys.version
captured['anysolver_file'] = sys.modules['anysolver'].__file__
captured['versions'] = {name: importlib.metadata.version(name) for name in
                        ('numpy', 'scipy', 'numba', 'llvmlite', 'pytest', 'threadpoolctl')}
core = sys.modules.get('numpy._core._multiarray_umath')
captured['cpu_features'] = getattr(core, '__cpu_features__', None)
captured['numerical_environment'] = {name: os.environ.get(name) for name in
    ('NUMBA_DISABLE_JIT', 'NUMBA_NUM_THREADS', 'OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS',
     'MKL_NUM_THREADS', 'NPY_DISABLE_CPU_FEATURES', 'OPENBLAS_CORETYPE')}
captured['git_head'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
captured['producer_blob'] = subprocess.check_output(
    ['git', 'rev-parse', 'HEAD:src/anysolver/general_contact/native_material_s3.py'], text=True).strip()
from threadpoolctl import threadpool_info
captured['pools'] = threadpool_info()
(OUTPUT/'physical-capture.json').write_text(json.dumps(captured, indent=2), encoding='utf-8')
print('LOGGING_ONLY', 'evaluations', len(captured['evaluations']), 'pytest_exit', code, flush=True)
raise SystemExit(code)
