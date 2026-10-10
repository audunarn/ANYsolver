"""Complete outcome cases execute only inside the explicitly bounded harness."""
import os,traceback
from pathlib import Path
import pytest
from scripts.r8_f07_block_descriptor_dev import (CONTROLS,run_control,run_saved,run_installed,write,
    STRUCTURAL_CONTROLS,run_structural_control,run_structural_saved,
    FINITE_CONTROLS,run_finite_control,run_finite_saved)
pytestmark=pytest.mark.skipif('F07_BLOCK_OUTPUT' not in os.environ or 'F07_BLOCK_SUPERVISED' not in os.environ,
    reason='Requires explicitly supervised bounded block-F07 harness')


def attempt(name,call):
    out=Path(os.environ['F07_BLOCK_OUTPUT'])/name;out.mkdir()
    try:call(out)
    except BaseException as exc:
        write(out/'failure.json',dict(exception=repr(exc),traceback=traceback.format_exc()));raise


@pytest.mark.parametrize('name',CONTROLS)
def test_independent_block_controls(name):
    attempt(name,lambda out:run_control(name,out))


def test_saved_current_public():
    attempt('saved-current-public',run_saved)


@pytest.mark.skipif(os.environ.get('F07_BLOCK_STAGE')!='installed',reason='installed-stage caller only')
def test_installed_public_bridge():
    attempt('installed-current-public',run_installed)


@pytest.mark.parametrize('name',STRUCTURAL_CONTROLS)
def test_structural_role_controls(name):
    attempt('structural-'+name,lambda out:run_structural_control(name,out))


def test_structural_saved_current_public():
    attempt('structural-saved-current-public',run_structural_saved)


@pytest.mark.parametrize('name',FINITE_CONTROLS)
def test_finite_supplement_controls(name):
    attempt('finite-'+name,lambda out:run_finite_control(name,out))


def test_finite_supplement_saved_current_public():
    attempt('finite-supplement-saved-current-public',run_finite_saved)
