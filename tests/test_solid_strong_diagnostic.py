"""Strong control algebra only; no connector/locking acceptance claim."""
import importlib.util
from pathlib import Path
import numpy as np
import pytest
from anysolver.solids import SolidModel, SolidModelError, SolidAnalysisNotSupported


def load(name,path):
    spec = importlib.util.spec_from_file_location(name,path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_strong_diagnostic_matches_rigid_fields_and_transpose_work():
    here = Path(__file__).resolve()
    fixture = load("_strong_fixture",here.with_name("test_solid_coupling.py"))
    helper = load("_strong_control",here.parents[2] / "ANYsolid/tools/strong_diagnostic.py")
    native,prepared,left,right,clamp,tip = fixture.specimen(nshell=1,nsolid=2)
    for trace,group in ((left,"left"),(right,"right")):
        control = helper.build_strong_point_control(trace,prepared,group)
        assert control.metadata["diagnostic_only"]
        assert control.formulation == "strong_point_diagnostic_v1"
        ordinary = SolidModel(native)
        ordinary.add_region("solid",prepared=prepared)
        with pytest.raises(SolidAnalysisNotSupported):
            ordinary.add_interface("solid",control,diagnostic_strong_tying=True)
        model = SolidModel(native,research_coupling=True)
        model.add_region("solid",prepared=prepared)
        with pytest.raises(SolidModelError,match="strong tying requires"):
            model.add_interface("solid",control)
        with pytest.raises(SolidModelError,match="boolean"):
            model.add_interface("solid",control,diagnostic_strong_tying="yes")
        model.add_interface("solid",control,diagnostic_strong_tying=True)
        weak = fixture.build_weak_connector(trace,prepared,group,multiplier_breakpoints=[0.,trace.length])
        with pytest.raises(SolidModelError,match="do not mix"):
            model.add_interface("solid",weak)
        for axis in np.eye(3):
            for rotation in (False,True):
                shell = fixture.native_rigid(native,np.zeros(3) if rotation else axis,
                                             axis if rotation else np.zeros(3))
                xyz = prepared.coefficient_coordinates
                vector = np.cross(axis,xyz) if rotation else np.broadcast_to(axis,xyz.shape)
                solid = vector[np.arange(prepared.ndof),prepared.coefficient_components]
                np.testing.assert_allclose(control.C_shell@shell,control.C_solid@solid,atol=1e-13)
        lam = np.linspace(-1.,1.,control.C_shell.shape[0])
        a = np.linspace(-.03,.02,prepared.ndof)
        q = np.linspace(-.02,.04,trace.ndof)
        fs,fv = control.interface_forces(lam)
        np.testing.assert_allclose(q@fs+a@fv,lam@(control.C_shell@q-control.C_solid@a),atol=1e-13)
