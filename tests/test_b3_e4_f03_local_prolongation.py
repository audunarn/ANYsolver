"""Exact nested-space and sparse energy/work preservation on manufactured data."""
from fractions import Fraction as F
from dataclasses import replace

import numpy as np
import pytest

from scripts import _b3_e4_f03_local_grid as topology
from scripts import _b3_e4_f03_local_prolongation as transfer
from scripts import _b3_e4_f03_local_primal_assembly as assembly


XS=(F(-1,2),F(0),F(1,2),F(1),F(3,2));YS=(F(-1,2),F(0),F(1,2))
FINE_XS=tuple(sorted((*XS,F(1,4))))
LIMITS=dict(max_entries=100000,max_integer_bits=8_000_000,max_work_bytes=128*1024**2)
BUDGET=assembly.AssemblyBudget(512,2_000_000,512*1024**2,8_000_000)


def field(grid):
    nx=len(grid.x_nodes);ny=len(grid.y_nodes);result=[]
    for full in grid.free_to_full:
        component,node=divmod(int(full),nx*ny);j,i=divmod(node,nx)
        x=grid.x_nodes[i];y=grid.y_nodes[j]
        result.append((1+component)*(x+F(1,2))*(F(3,2)-x)*(1+y*y))
    return tuple(result)


@pytest.mark.parametrize('source_p,target_p',[(2,2),(2,3),(3,3)])
def test_nested_polynomial_field_and_owned_sparse_matrix(source_p,target_p):
    source=topology.compile_grid(XS,YS,source_p)
    target=topology.compile_grid(FINE_XS,YS,target_p)
    operator=transfer.prolongation(source,target,**LIMITS)
    assert operator.apply_exact(field(source))==field(target)
    matrix=operator.matrix()
    np.testing.assert_allclose(matrix@np.array(field(source),dtype=float),np.array(field(target),dtype=float),rtol=1e-14,atol=1e-14)
    matrix.data[:]=0
    assert operator.matrix().nnz>0 and np.any(operator.matrix().data!=0)
    with pytest.raises(ValueError): operator.rows.setflags(write=True)
    with pytest.raises(TypeError): replace(operator,source_dofs=1)


def test_complete_nonpolynomial_nodal_field_preserves_trace_derivatives():
    source=topology.compile_grid(XS,YS,2);target=topology.compile_grid(FINE_XS,YS,3)
    operator=transfer.prolongation(source,target,**LIMITS)
    q=tuple(F((i*17)%31-15,31) for i in range(source.free_dofs));fine_q=operator.apply_exact(q)
    def action(model,values,s,order):
        index=next((i for i,(a,b) in enumerate(zip(model.station_cuts,model.station_cuts[1:])) if a<=s<b),len(model.station_cuts)-2)
        trace=assembly.trace_interval(model,index,BUDGET)
        rows=trace.evaluate_exact((s-trace.left)/(trace.right-trace.left),order)
        return tuple(sum((coefficient*values[j] for coefficient,j in zip(row,trace.indices)),F(0)) for row in rows)
    for station in (F(0),F(2,7),F(1)):
        for order in (0,1,2):
            assert action(source,q,station,order)==action(target,fine_q,station,order)


def test_nested_energy_root_compatibility_and_physical_load_work():
    source=topology.compile_grid(XS,YS,2);target=topology.compile_grid(FINE_XS,YS,3)
    P=transfer.prolongation(source,target,**LIMITS).matrix()
    coarse=assembly.assemble(source,BUDGET)
    fine=assembly.assemble(target,BUDGET,extra_beam_order=True,load_order=64)
    q=np.array([((i*17)%31-15)/31 for i in range(source.free_dofs)]);z=P@q
    for a,b in ((coarse.shell,fine.shell),(coarse.beam,fine.beam)):
        left=q@(a@q);right=z@(b@z)
        assert abs(left-right)/max(abs(left),abs(right),1)<3e-13
        # Sparse complete-space identity, independent of the sampled q.
        discrepancy=P.T@b@P-a
        assert np.linalg.norm(discrepancy.data)/max(np.linalg.norm(a.data),1)<3e-13
    root_difference=fine.root@P-coarse.root
    assert np.linalg.norm(root_difference.data)/max(np.linalg.norm(coarse.root.data),1)<3e-13
    np.testing.assert_allclose(P.T@fine.load,coarse.load,rtol=3e-13,atol=1e-9)
    np.testing.assert_allclose(coarse.root@q,fine.root@z,rtol=3e-13,atol=1e-14)
    assert abs(coarse.load@q-fine.load@z)/max(abs(coarse.load@q),1)<3e-13


def test_rejects_nonnested_spaces_and_enforces_preallocation_limits():
    q3=topology.compile_grid(XS,YS,3);fine_q2=topology.compile_grid(FINE_XS,YS,2)
    with pytest.raises(ValueError,match='not nested'):
        transfer.prolongation(q3,fine_q2,**LIMITS)
    unrelated=topology.compile_grid((F(-1,2),F(1,2),F(3,2)),YS,3)
    with pytest.raises(ValueError,match='not nested'):
        transfer.prolongation(q3,unrelated,**LIMITS)
    with pytest.raises(ValueError,match='entry envelope'):
        transfer.prolongation(q3,q3,**(LIMITS|{'max_entries':1}))
    with pytest.raises(ValueError,match='workspace'):
        transfer.prolongation(q3,q3,**(LIMITS|{'max_work_bytes':1}))
    with pytest.raises(ValueError,match='aggregate'):
        transfer.prolongation(q3,q3,**(LIMITS|{'max_integer_bits':1}))
