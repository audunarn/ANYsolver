"""Actual active assembled updates at the same physical pose across rebase."""
import os,traceback
from pathlib import Path
import pytest
from scripts.r8_f06_active_chart_dev import run_case,write

pytestmark=pytest.mark.skipif('F06_OUTPUT' not in os.environ,
    reason='Requires the explicitly invoked bounded F06 harness')

@pytest.mark.parametrize('family',('q4','s3'))
def test_active_same_physical_chart_seam(family,tmp_path):
    out=Path(os.environ.get('F06_OUTPUT',str(tmp_path)))/family;out.mkdir()
    try:
        result=run_case(family,out)
        write(out/'result.json',result)
        assert result['status']=='PASS'
    except BaseException as exc:
        write(out/'failure.json',dict(exception=repr(exc),traceback=traceback.format_exc()));raise
