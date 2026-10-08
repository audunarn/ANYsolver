"""Manufactured sparse-assembly proofs; no physical reference equilibrium."""
from dataclasses import replace
from fractions import Fraction as F
import math

import numpy as np
import pytest
from scipy import sparse

from scripts import _b3_e4_f03_local_primal_assembly as assembly
from scripts import _b3_e4_f03_local_grid as topology
from scripts import _b3_e4_f03_spatial_contract as c


BUDGET=assembly.AssemblyBudget(512,2_000_000,512*1024**2,8_000_000)


def grid(p=1):
    return topology.compile_grid((F(-1,2),F(0),F(1,2),F(1),F(3,2)),
                                 (F(-1,2),F(0),F(1,2)),p)


def dot_exact(row,values): return sum((a*b for a,b in zip(row,values)),F(0))


def coefficient_action(trace,values,order):
    coefficients=trace.derivative_coefficients(order)
    return tuple(tuple(sum((values[j]*poly[k] for j,poly in enumerate(channel)),F(0))
        for k in range(len(channel[0]))) for channel in coefficients)


def integral_product(a,b):
    return sum((x*y/F(i+j+1) for i,x in enumerate(a) for j,y in enumerate(b)),F(0))


def exact_beam_bilinear(trace,first,second):
    def strains(q):
        b=coefficient_action(trace,q,0);d=coefficient_action(trace,q,1)
        shear=tuple((d[1][i] if i<len(d[1]) else F(0))-b[2][i] for i in range(len(b[2])))
        return d[0],shear,d[2]
    return (trace.right-trace.left)*sum((modulus*integral_product(a,b)
        for modulus,a,b in zip((c.Q_EA,c.Q_GAS,c.Q_EI),strains(first),strains(second))),F(0))


@pytest.mark.parametrize('p',[1,2,3])
def test_interval_quadrature_against_exact_polynomial_bilinear_and_work(p):
    model=grid(p)
    whole_q=tuple(F((i%11)-5,11) for i in range(model.free_dofs))
    whole_z=tuple(F((i%7)-3,13) for i in range(model.free_dofs))
    energy=F(0);numeric=0.;cross=F(0);numeric_cross=0.
    for index in range(len(model.trace_incidence)):
        trace=assembly.trace_interval(model,index,BUDGET)
        q=tuple(whole_q[i] for i in trace.indices);z=tuple(whole_z[i] for i in trace.indices)
        k=assembly.beam_interval(trace);alternate=assembly.beam_interval(trace,extra_order=True)
        assert np.linalg.norm(k-alternate)/max(np.linalg.norm(k),1)<3e-14
        assert np.linalg.norm(k-k.T)/max(np.linalg.norm(k),1)<2e-15
        e=exact_beam_bilinear(trace,q,q);b=exact_beam_bilinear(trace,z,q)
        energy+=e;cross+=b
        numeric+=np.array(q,dtype=float)@k@np.array(q,dtype=float)
        numeric_cross+=np.array(z,dtype=float)@k@np.array(q,dtype=float)
        assert e>=0
        f48=assembly.load_interval(trace,48);f64=assembly.load_interval(trace,64)
        assert np.linalg.norm(f48-f64)/max(np.linalg.norm(f64),1)<2e-13
    assert numeric==pytest.approx(float(energy),rel=3e-14)
    assert numeric_cross==pytest.approx(float(cross),rel=3e-13)


@pytest.mark.parametrize('p',[1,2])
def test_sparse_global_scatter_matches_bounded_dense_exact_beam_oracle(p):
    model=grid(p)
    result=assembly.assemble(model,BUDGET)
    assert model.free_dofs<=128
    n=model.free_dofs;oracle=np.zeros((n,n));force=np.zeros(n)
    # Independently integrate the full coefficient pairs, without the beam
    # Gauss implementation or its matrix contraction. Dense scope is bounded.
    for index in range(len(model.trace_incidence)):
        trace=assembly.trace_interval(model,index,BUDGET)
        b=trace.derivative_coefficients(0);d=trace.derivative_coefficients(1)
        strain=[]
        for j in range(len(trace.indices)):
            shear=tuple((d[1][j][k] if k<len(d[1][j]) else F(0))-b[2][j][k]
                         for k in range(len(b[2][j])))
            strain.append((d[0][j],shear,d[2][j]))
        for j,global_j in enumerate(trace.indices):
            for k,global_k in enumerate(trace.indices):
                exact=(trace.right-trace.left)*sum((modulus*integral_product(a,b)
                    for modulus,a,b in zip((c.Q_EA,c.Q_GAS,c.Q_EI),strain[j],strain[k])),F(0))
                oracle[global_j,global_k]+=float(exact)
        force[trace.indices]+=assembly.load_interval(trace,64)
    np.testing.assert_allclose(result.beam.toarray(),oracle,rtol=3e-14,atol=1e-6)
    np.testing.assert_allclose(result.load,force,rtol=3e-13,atol=1e-9)
    assert sparse.isspmatrix_csr(result.shell) and sparse.isspmatrix_csr(result.beam)
    kkt=result.kkt()
    assert sparse.isspmatrix_csc(kkt) and kkt.shape==(n+3,n+3)
    assert kkt[-3:,-3:].nnz==0
    assert result.root.shape==(3,n)
    assert result.diagnostics['factorization_count']==result.diagnostics['equilibrium_count']==0
    assert result.diagnostics['beam_nnz']==result.beam.nnz


def test_global_energy_and_residual_directional_derivative():
    model=grid(2);result=assembly.assemble(model,BUDGET)
    q=np.array([((i%7)-3)/7 for i in range(model.free_dofs)])
    z=np.array([((i%11)-5)/11 for i in range(model.free_dofs)])
    eta=np.array([.2,-.3,.5]);deta=np.array([.4,.6,-.2])
    k=result.stiffness();C=result.root
    def potential(x,multiplier): return .5*x@(k@x)-result.load@x+multiplier@(C@x)
    action=z@(k@q-result.load+C.T@eta)+deta@(C@q)
    h=2**-12
    difference=(potential(q+h*z,eta+h*deta)-potential(q-h*z,eta-h*deta))/(2*h)
    assert abs(difference-action)/max(abs(action),1)<1e-11
    # The primal block stays physical; multipliers are not assigned energy
    # stiffness or fictitious inertia to complete the block matrix.
    assert np.linalg.norm((k-k.T).data)/max(np.linalg.norm(k.data),1)<2e-15


def test_interval_ownership_collapsed_events_and_invalid_root_space():
    model=grid(2);trace=assembly.trace_interval(model,0,BUDGET)
    with pytest.raises(TypeError): assembly.ExactTrace()
    with pytest.raises(TypeError): replace(trace,left=F(1,10))
    with pytest.raises(ValueError): trace.indices.setflags(write=True)
    a=trace.evaluate(.25);a[:]=0
    assert np.any(trace.evaluate(.25)!=0)
    narrow_model=topology.compile_grid(c.X_CUTS,c.Y_CUTS,1)
    idx=next(i for i,(a,b) in enumerate(zip(narrow_model.station_cuts,narrow_model.station_cuts[1:])) if float(a)==float(b))
    narrow=assembly.trace_interval(narrow_model,idx,BUDGET)
    assert narrow.right>narrow.left
    assert np.isfinite(assembly.beam_interval(narrow)).all()
    coarse=topology.compile_grid((F(-1,2),F(1,2),F(3,2)),(F(-1,2),F(0),F(1,2)),1)
    with pytest.raises(ValueError,match='rank3.*rank4'):
        assembly.assemble(coarse,BUDGET)


def test_assembled_result_factory_and_mutation_isolation():
    result=assembly.assemble(grid(1),BUDGET)
    with pytest.raises(TypeError): assembly.AssembledPrimal()
    with pytest.raises(TypeError): replace(result,_root=sparse.csr_matrix((4,1)))
    original=result.kkt().copy();load=result.load.copy()
    for matrix in (result.shell,result.beam,result.root,result.stiffness(),result.kkt()):
        matrix.data[:]=0
    exposed_load=result.load;exposed_load[:]=0
    assert (original-result.kkt()).nnz==0
    np.testing.assert_array_equal(result.load,load)
    with pytest.raises(TypeError): result.diagnostics['equilibrium_count']=1


def test_nonzero_unrepresentable_exact_trace_coefficient_is_not_dropped(monkeypatch):
    trace=assembly.trace_interval(grid(1),0,BUDGET)
    original=assembly.ExactTrace.derivative_coefficients
    def tiny(self,order=0):
        rows=[[list(poly) for poly in row] for row in original(self,order)]
        rows[0][0][0]=F(1,10**400)
        return tuple(tuple(tuple(poly) for poly in row) for row in rows)
    monkeypatch.setattr(assembly.ExactTrace,'derivative_coefficients',tiny)
    with pytest.raises(ValueError,match='unrepresentable assembled trace'):
        trace.evaluate(.5)


def test_preflight_fails_before_local_evaluation_and_no_factorization(monkeypatch):
    model=grid(1)
    def forbidden(*args,**kwargs): raise AssertionError('unexpected operator/solver invocation')
    monkeypatch.setattr(assembly.moments,'trace_segment',forbidden)
    with pytest.raises(ValueError,match='triplets'):
        assembly.assemble(model,replace(BUDGET,max_triplets=1))
    with pytest.raises(ValueError,match='workspace'):
        assembly.assemble(model,replace(BUDGET,max_work_bytes=1))
    with pytest.raises(ValueError,match='active trace'):
        assembly.assemble(model,replace(BUDGET,max_trace_dofs=1))
    with pytest.raises(ValueError,match='initial trace'):
        assembly.trace_interval(model,0,replace(BUDGET,max_trace_integer_bits=1))
    with pytest.raises(ValueError): assembly.AssemblyBudget(True,1,1,1)
