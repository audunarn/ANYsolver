"""Fresh-process public-module compatibility for the ordinary Beam import route."""
import os
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.parametrize("access", ("attribute", "from_import", "submodule"))
def test_stiffened_shell_lazy_public_identity(access):
    # Use the actual already-selected installed/source artifact in a clean child.
    # A repository test must not fall back to a historical checkout.
    import anysolver
    source = str(Path(anysolver.__file__).resolve().parent.parent)
    code = '''
import importlib, sys, types
sys.path.insert(0, SOURCE)
import anysolver
assert 'stiffened_shell' in anysolver.__all__
assert 'stiffened_shell' in dir(anysolver)
assert 'stiffened_shell' not in vars(anysolver)
assert 'anysolver.stiffened_shell' not in sys.modules
assert 'scipy.spatial.transform' not in sys.modules
try:
    anysolver._not_a_public_export
except AttributeError:
    pass
else:
    raise AssertionError('unknown export accepted')
if ACCESS == 'attribute':
    module = anysolver.stiffened_shell
elif ACCESS == 'from_import':
    from anysolver import stiffened_shell as module
else:
    module = importlib.import_module('anysolver.stiffened_shell')
assert isinstance(module, types.ModuleType)
assert module is anysolver.stiffened_shell
assert module is sys.modules['anysolver.stiffened_shell']
from anysolver import stiffened_shell
assert stiffened_shell is module
assert importlib.import_module('anysolver.stiffened_shell') is module
assert vars(anysolver)['stiffened_shell'] is module
assert 'stiffened_shell' in dir(anysolver)
assert module.GEBeamLineAction is importlib.import_module('anysolver._stiffened_shell_ge_distributed_load').GEBeamLineAction
'''
    code = 'SOURCE = ' + repr(source) + '\nACCESS = ' + repr(access) + '\n' + code
    env = os.environ.copy()
    env['PYTHONPATH'] = ''
    completed = subprocess.run([sys.executable, '-c', code], env=env,
                               capture_output=True, text=True, timeout=20)
    assert completed.returncode == 0, completed.stdout + completed.stderr
