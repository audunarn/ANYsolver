"""Actual-matrix consistency witness; no physical stability qualification."""
import importlib.util
from pathlib import Path
import numpy as np
from anysolid.coupling import build_weak_connector


def test_fixed_multiplier_partition_misses_refinable_quadratic_jump():
    path = Path(__file__).with_name("test_solid_coupling.py")
    spec = importlib.util.spec_from_file_location("_multiplier_witness_fixture",path)
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    native,prepared,left,right,clamp,tip = fixture.specimen(nshell=2,nsolid=2)
    coefficient_s = prepared.coefficient_coordinates[:,1]
    jump = np.where(prepared.coefficient_components == 2,
                    6*coefficient_s**2-6*coefficient_s+1,0.)
    assert np.linalg.norm(jump) > 0.
    for trace,group in ((left,"left"),(right,"right")):
        coarse = build_weak_connector(trace,prepared,group,multiplier_breakpoints=[0.,1.])
        refined = build_weak_connector(trace,prepared,group,multiplier_breakpoints=[0.,.5,1.])
        np.testing.assert_allclose(coarse.C_solid @ jump,0.,atol=1e-13)
        assert np.max(abs(refined.C_solid @ jump)) > .001
