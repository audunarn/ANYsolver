"""Public import and retained-step seams shared by the two development routes."""
import os
from pathlib import Path
import subprocess
import sys

import pytest


def _fresh(code):
    root = Path(__file__).resolve().parents[1]
    expected = Path(os.environ.get('ANYSOLVER_INTEGRATION_EXPECT_SITE', root / 'src')).resolve()
    environment = os.environ.copy()
    environment['PYTHONPATH'] = os.pathsep.join((str(expected), str(root)))
    prefix = f"from pathlib import Path; expected = Path({str(expected)!r})\n"
    run = subprocess.run([sys.executable, '-c', prefix + code], env=environment,
                         cwd=root, capture_output=True, text=True, timeout=30)
    assert run.returncode == 0, run.stdout + run.stderr


def test_fresh_public_facades_share_one_package_and_keep_contact_lazy():
    _fresh("""
import sys
import anysolver
assert Path(anysolver.__file__).resolve().is_relative_to(expected)
assert 'anysolver.general_contact' not in sys.modules
assert anysolver.stiffened_shell.create_analysis is not None
public = anysolver.ContactDefinition
from anysolver.general_contact import ContactDefinition
assert public is ContactDefinition
from anysolver import stiffened_shell
assert stiffened_shell is anysolver.stiffened_shell
""")


@pytest.mark.parametrize('name', ('__annotate__', '__annotate_func__'))
def test_preimport_abc_callback_is_rejected_without_execution(name):
    _fresh(f"""
from abc import ABC
calls = []
def callback(*args, **kwargs):
    calls.append(1)
    raise AssertionError('callback must never execute')
setattr(ABC, {name!r}, callback)
try:
    import anysolver
except RuntimeError as error:
    assert 'ABC annotation callback' in str(error)
else:
    raise AssertionError('preinstalled callback admitted')
assert not calls
""")


def test_generalized_context_step_matches_constrained_rank_one_inverse():
    from types import SimpleNamespace
    import numpy as np
    from anysolver._ge_beam3_retained_generalized_state import Context
    count = 42
    free = np.arange(6, count)
    diagonal = np.linspace(2., 4., count)
    direction = np.cos(np.arange(count) + .3)
    tangent = np.diag(diagonal) + np.outer(direction, direction)
    residual = np.sin(np.arange(count) + .7)
    d, u, rhs = diagonal[free], direction[free], -residual[free]
    expected = rhs / d - (u / d) * (u @ (rhs / d)) / (1. + u @ (u / d))
    context = SimpleNamespace(count=count, free=free, nodal_count=18,
                              length=2., elements=(object(),))
    state = SimpleNamespace(resultants=np.ones((1, 18)))
    step, correction = Context.step(context, state, residual, tangent)
    np.testing.assert_allclose(step[free], expected, rtol=2e-14, atol=2e-15)
    np.testing.assert_array_equal(step[:6], np.zeros(6))
    assert np.isfinite(correction) and correction > 0
