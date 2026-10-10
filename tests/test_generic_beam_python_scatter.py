"""Focused JIT-off generic Beam scatter/assembly compatibility checks."""
from types import SimpleNamespace

import numpy as np
import pytest

from anysolver import nonlinear_performance as performance
from anysolver.elements import BeamElement, QuadraticBeamElement


def original(values, positions, size):
    out = np.zeros(size, dtype=np.float64)
    for i in range(values.size):
        out[positions[i]] += values[i]
    return out


@pytest.mark.parametrize('values,positions,size', [
    ([1e16,1.,-1e16,2.,-2.,-0.], [0,0,0,1,1,2], 4),
    ([-0.,0.,-0.,np.inf,-np.inf,np.nan], [0,1,2,3,3,4], 6),
    ([1.,-1.,3.,-3.,1e-300,-1e-300], [2,2,0,0,1,1], 3),
    ([], [], 0),
])
def test_ordered_scatter_preserves_binary64(values, positions, size):
    values=np.asarray(values,dtype=np.float64);positions=np.asarray(positions,dtype=np.intp)
    with np.errstate(invalid='ignore'):
        expected=original(values,positions,size)
        actual=performance._scatter_sum_python_ordered(values,positions,size)
    assert np.array_equal(actual,expected,equal_nan=True)
    assert np.array_equal(np.signbit(actual),np.signbit(expected))
    assert actual.tobytes()==expected.tobytes()


def test_layout_fallback_retains_original_kernel(monkeypatch):
    calls=[]
    def fallback(*args):calls.append(args);return 'original'
    monkeypatch.setattr(performance,'_scatter_sum',fallback)
    assert performance._scatter_sum_python_ordered(np.zeros((1,2)),np.zeros(2,dtype=np.intp),2)=='original'
    assert performance._scatter_sum_python_ordered(np.zeros(2,dtype=np.float32),np.zeros(2,dtype=np.intp),2)=='original'
    assert performance._scatter_sum_python_ordered(np.zeros(2),np.zeros(1,dtype=np.intp),2)=='original'
    assert len(calls)==3


def test_selector_rechecks_jit_and_exact_family(monkeypatch):
    import numba
    beam=object.__new__(BeamElement)
    plan=SimpleNamespace(shell_batches=(),quadratic_beam_batches=(),non_shell_elements=(SimpleNamespace(element=beam),))
    monkeypatch.setattr(numba.config,'DISABLE_JIT',True)
    assert performance._generic_beam_scatter_kernel(plan) is performance._scatter_sum_python_ordered
    plan.non_shell_elements=(SimpleNamespace(element=object.__new__(QuadraticBeamElement)),)
    assert performance._generic_beam_scatter_kernel(plan) is performance._scatter_sum
    plan.non_shell_elements=(SimpleNamespace(element=beam),)
    plan.shell_batches=(object(),)
    assert performance._generic_beam_scatter_kernel(plan) is performance._scatter_sum
    plan.shell_batches=()
    from anysolver.general_contact.runtime import _ACTIVE_CONTACT, suspend_contact
    token=_ACTIVE_CONTACT.set(object())
    try:
        assert performance._generic_beam_scatter_kernel(plan) is performance._scatter_sum_python_ordered
        with suspend_contact():
            assert performance._generic_beam_scatter_kernel(plan) is performance._scatter_sum_python_ordered
    finally:
        _ACTIVE_CONTACT.reset(token)
    monkeypatch.setattr(numba.config,'DISABLE_JIT',False)
    assert performance._generic_beam_scatter_kernel(plan) is performance._scatter_sum


def test_invalid_index_retains_refusal():
    with pytest.raises(IndexError):
        performance._scatter_sum_python_ordered(np.array([1.]),np.array([3],dtype=np.intp),3)


def beam_model():
    from anysolver.fe_core import FEModel
    model=FEModel('generic-beam-scatter')
    model.add_material('steel',210e9,0.3)
    for node_id in (1,2,3):model.add_node(node_id,float(node_id-1),0.,0.)
    section=dict(area=.01,Iy=1e-5,Iz=2e-5,J=1e-5)
    for element_id in (1,2):model.add_element(element_id,BeamElement(element_id,[element_id,element_id+1],'steel',cross_section=section.copy()))
    return model


def test_actual_beam_assembly_exact_parity(monkeypatch):
    from anysolver import nonlinear_static
    import numba
    assert numba.config.DISABLE_JIT
    model=beam_model()
    nonlinear_static._ensure_nonlinear_acceleration()
    n=model.mesh.dof_manager.total_dofs
    u=np.linspace(-1e-5,1e-5,n)
    calls=[]
    actual=performance._scatter_sum_python_ordered
    def observed(*args):calls.append(True);return actual(*args)
    monkeypatch.setattr(performance,'_scatter_sum_python_ordered',observed)
    residual,no_tangent,_=nonlinear_static._assemble_nonlinear_system(model,u,{},5,tangent=False)
    assert no_tangent is None and len(calls)==1
    force,tangent,states=nonlinear_static._assemble_nonlinear_system(model,u,{},5)
    assert len(calls)==3 and residual.tobytes()==force.tobytes()
    monkeypatch.setattr(performance,'_generic_beam_scatter_kernel',lambda plan:performance._scatter_sum)
    reference,reference_tangent,reference_states=nonlinear_static._assemble_nonlinear_system(model,u,{},5)
    assert force.tobytes()==reference.tobytes()
    assert tangent.toarray().tobytes()==reference_tangent.toarray().tobytes()
    assert states.keys()==reference_states.keys()
    assert np.all(np.isfinite(force)) and np.all(np.isfinite(tangent.data))


def test_beam_plan_invalidation():
    from anysolver.nonlinear_performance_bootstrap import get_nonlinear_assembly_plan
    model=beam_model()
    first=get_nonlinear_assembly_plan(model,5)
    assert get_nonlinear_assembly_plan(model,5) is first
    node=next(iter(model.mesh.nodes.values()))
    model.mesh.set_node_coordinates(node.id,node.x,node.y,node.z+1e-6)
    second=get_nonlinear_assembly_plan(model,5)
    assert second is not first
    model.bump_revision('material')
    third=get_nonlinear_assembly_plan(model,5)
    assert third is not second
