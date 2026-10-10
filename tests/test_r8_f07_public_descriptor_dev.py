"""Heavy complete-pencil cases are explicitly harness opt-in."""
import os
from pathlib import Path
import traceback
import pytest
from scripts.r8_f07_public_descriptor_dev import run_fixture,run_control,write

pytestmark=pytest.mark.skipif('F07_OUTPUT' not in os.environ,reason='Requires explicitly invoked bounded F07 harness')


def attempt(name,call):
    out=Path(os.environ['F07_OUTPUT'])/name;out.mkdir()
    try:call(out)
    except BaseException as exc:
        write(out/'failure.json',dict(exception=repr(exc),traceback=traceback.format_exc()));raise


@pytest.mark.parametrize('name',('baseline','seventh','ambiguous','indeterminate','negative-rigid-mass','defective-zero'))
def test_independent_classification_controls(name):
    attempt(name,lambda out:run_control(name,out))


def test_current_public_complete_pencil():
    attempt('current-public-mixed-point',run_fixture)
