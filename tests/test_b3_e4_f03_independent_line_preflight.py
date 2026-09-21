"""Bounded mechanics checks for the independent F03 weak-line comparator."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pytest
from scipy import sparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import _b3_e4_f03_independent_beam as beam
import _b3_e4_f03_independent_line as line
import _b3_e4_f03_independent_coupled as coupled
import _b3_e4_f03_independent_shell as shell


@pytest.mark.parametrize('topology', ['Q4', 'CST'])
def test_overlay_splits_every_host_and_interpolation_boundary(topology):
    model=shell.panel(5, 10, topology)
    knots=line.overlay(model, 8, 4)
    assert knots[0]==0 and knots[-1]==1
    assert np.all(np.diff(knots)>1e-12)
    # The first x-cell crossing for the sample at dx=-.2 is s=.1.
    assert np.min(abs(knots-.1))<1e-12
    if topology=='CST':
        # dy=-.23 lies .7 of the way up its cell, so the first diagonal
        # crossing for this same sample is s=.1+.7/5=.24.
        assert np.min(abs(knots-.24))<1e-12
    for a,b in zip(knots[:-1],knots[1:]):
        left=a+(b-a)/4
        right=a+3*(b-a)/4
        near_left=a+(b-a)*1e-7
        near_right=b-(b-a)*1e-7
        for dx,dy in shell.OFFSETS:
            hosts=[shell.sample(model,s+dx,dy)[0]
                   for s in (near_left,left,right,near_right)]
            assert all(host==hosts[0] for host in hosts)
        assert min(int(left*8),7)==min(int(right*8),7)
        assert min(int(left*4),3)==min(int(right*4),3)


def _rigid_fields(model, n_beam, tx, ty, omega):
    qs=np.empty(model.dof_count)
    qs[0::2]=tx-omega*model.nodes[:,1]
    qs[1::2]=ty+omega*model.nodes[:,0]
    qb=np.zeros(beam.dof_count(n_beam))
    u=2*n_beam+1
    v=2*(n_beam+1)
    qb[:u]=tx
    qb[u:u+v:2]=ty+omega*np.arange(n_beam+1)/n_beam
    qb[u+1:u+v:2]=omega
    qb[u+v:]=omega
    return qs,qb


@pytest.mark.parametrize('topology', ['Q4', 'CST'])
@pytest.mark.parametrize('law', ['P0', 'P1'])
def test_segmented_weak_work_quadrature_rigid_patch_and_row_rank(topology,law):
    model=shell.panel(5,10,topology)
    cs,cb,knots=line.coupling(model,8,4,law,order=4)
    cs6,cb6,knots6=line.coupling(model,8,4,law,order=6)
    assert cs.shape==(3*(4+(law=='P1')),model.dof_count)
    assert cb.shape==(cs.shape[0],beam.dof_count(8))
    assert sparse.isspmatrix_csr(cs) and sparse.isspmatrix_csr(cb)
    np.testing.assert_array_equal(knots,knots6)
    for low,high in ((cs,cs6),(cb,cb6)):
        diff=low-high
        assert sparse.linalg.norm(diff)/sparse.linalg.norm(high)<1e-12

    for tx,ty,omega in ((1.,0.,0.),(0.,1.,0.),(0.,0.,1.),(.37,-.21,.04)):
        qs,qb=_rigid_fields(model,8,tx,ty,omega)
        assert np.linalg.norm(cb@qb-cs@qs)<1e-12
        assert line.integrated_gap(model,8,4,qs,qb)<1e-12

    qs=np.zeros(model.dof_count)
    qb=np.zeros(beam.dof_count(8))
    qb[:2*8+1]=.123
    np.testing.assert_allclose(line.integrated_gap(model,8,4,qs,qb),.123,
                               rtol=1e-12,atol=1e-14)

    # The dual forces are the exact transpose of the work functional;
    # a finite directional perturbation must agree with their virtual work.
    rng=np.random.default_rng(617)
    qs=rng.standard_normal(model.dof_count)
    qb=rng.standard_normal(beam.dof_count(8))
    ps=rng.standard_normal(qs.size)
    pb=rng.standard_normal(qb.size)
    lam=rng.standard_normal(cs.shape[0])
    derivative=lam@(cb@pb-cs@ps)
    dual=(-cs.T@lam)@ps+(cb.T@lam)@pb
    np.testing.assert_allclose(derivative,dual,rtol=1e-13,atol=1e-13)

    # Integrate the physical non-rigid gap directly, independently of the
    # assembled COO entries. Each segmented integrand is polynomial degree
    # at most four, so eight-point integration supplies a separate oracle.
    roots,weights=np.polynomial.legendre.leggauss(8)
    scalar=0.
    for a,b in zip(knots[:-1],knots[1:]):
        for root,weight in zip(roots,weights):
            s=(a+b)/2+(b-a)*root/2
            gap=(beam.trace(8,s)@qb-shell.pose(model,s)@qs)
            gap[2]*=line.YAW_LENGTH
            tests=line.mortar_tests(4,law,s)
            multiplier=sum(value*lam[3*index:3*index+3]
                           for index,value in tests)
            scalar+=(b-a)*weight/2*float(multiplier@gap)
    np.testing.assert_allclose(lam@(cb@qb-cs@qs),scalar,rtol=1e-12,atol=1e-12)

    # Hand-integrated axial patch u(s)=s with a stationary shell. This
    # checks every P0/P1 mortar row without calling mortar_tests as oracle.
    qb[:]=0; qs[:]=0
    qb[:17]=np.arange(17)/16
    axial=(cb@qb-cs@qs)[0::3]
    h=1/4
    if law=='P0':
        expected=np.array([(i+.5)*h*h for i in range(4)])
    else:
        expected=np.r_[h*h/6, np.arange(1,4)*h*h,h/2-h*h/6]
    np.testing.assert_allclose(axial,expected,rtol=1e-12,atol=1e-14)

    free_shell=np.setdiff1d(np.arange(model.dof_count),model.supported)
    free_beam=np.setdiff1d(np.arange(beam.dof_count(8)),beam.root_dofs(8))
    rows=sparse.hstack((-cs[:,free_shell],cb[:,free_beam])).toarray()
    singular=np.linalg.svd(rows,compute_uv=False)
    assert singular[-1]/singular[0]>1e-9


def test_invalid_mortar_definitions_reject_explicitly():
    model=shell.panel(3,6,'Q4')
    for count in (0,65):
        with pytest.raises(ValueError,match='mortar'):
            line.overlay(model,4,count)
    with pytest.raises(ValueError,match='mortar'):
        line.coupling(model,4,2,'P2')


@pytest.mark.parametrize('topology', ['Q4', 'CST'])
@pytest.mark.parametrize('law', ['P0', 'P1'])
@pytest.mark.parametrize('loading', ['smooth', 'sine'])
def test_small_loaded_saddle_equilibrium_work_and_global_balance(topology,law,loading):
    model=shell.panel(3,6,topology)
    result=coupled.solve(model,6,3,law,loading)
    assert result.algebraic_residual_ratio<1e-8
    assert result.weak_compatibility_ratio<1e-8
    assert np.linalg.norm(result.weak_gap)<1e-8
    gap=line.integrated_gap(model,6,3,result.shell,result.beam)
    gap6=line.integrated_gap(model,6,3,result.shell,result.beam,order=6)
    assert gap>0
    np.testing.assert_allclose(gap,gap6,rtol=1e-11)
    assert result.shell_energy>0 and result.beam_energy>0
    np.testing.assert_allclose(2*(result.shell_energy+result.beam_energy),
                               result.external_work,rtol=1e-8)
    force=1e6 if loading=='smooth' else 0.
    moment=5e5 if loading=='smooth' else -1e6/(2*np.pi)
    r_shell=result.shell_reactions.reshape(-1,2)
    r_beam=result.beam_reactions
    n=6; u=2*n+1; v=2*(n+1)
    unsupported_shell=np.setdiff1d(np.arange(model.dof_count),model.supported)
    unsupported_beam=np.setdiff1d(np.arange(r_beam.size),beam.root_dofs(n))
    np.testing.assert_array_equal(result.shell_reactions[unsupported_shell],0)
    np.testing.assert_array_equal(r_beam[unsupported_beam],0)
    np.testing.assert_allclose(np.sum(r_shell[:,0])+np.sum(r_beam[:u]),0,
                               rtol=0,atol=2e-5)
    total_y=np.sum(r_shell[:,1])+np.sum(r_beam[u:u+v:2])
    total_moment=(model.nodes[:,0]@r_shell[:,1]-
                  model.nodes[:,1]@r_shell[:,0]+
                  np.arange(n+1)/n@r_beam[u:u+v:2]+
                  np.sum(r_beam[u+1:u+v:2])+np.sum(r_beam[u+v:]))
    np.testing.assert_allclose(total_y+force,0,rtol=0,atol=2e-5)
    np.testing.assert_allclose(total_moment+moment,0,rtol=0,atol=2e-5)
