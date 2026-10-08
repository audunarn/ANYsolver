"""Bounded work and rank checks for a new finite-pad mortar line."""

import sys
from pathlib import Path

import numpy as np
import pytest
from scipy import sparse

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import _b3_e4_f03_area_line as area
import _b3_e4_f03_independent_beam as beam
import _b3_e4_f03_independent_line as original
import _b3_e4_f03_independent_shell as shell


def _rigid_fields(model,cells,tx,ty,omega):
    qs=np.array([v for x,y in model.nodes
                 for v in (tx-omega*y,ty+omega*x)])
    qb=np.zeros(beam.dof_count(cells))
    u=2*cells+1
    theta=u+2*(cells+1)
    qb[:u]=tx
    qb[theta:]=omega
    for node in range(cells+1):
        qb[u+2*node]=ty+omega*node/cells
        qb[u+2*node+1]=omega
    return qs,qb


@pytest.mark.parametrize("topology",("Q4","CST-CB"))
@pytest.mark.parametrize("law",("P0","P1"))
def test_rigid_weak_gap_adjoint_work_and_pad_wrench(topology,law):
    model=shell.panel(2,4,topology)
    cells,mortar,halfwidth=(4,2,.04)
    cs,cb,knots=area.coupling(model,cells,mortar,law,halfwidth)
    assert knots[0]==0 and knots[-1]==1 and np.all(np.diff(knots)>0)
    qs,qb=_rigid_fields(model,cells,1e-4,-2e-4,3e-4)
    np.testing.assert_allclose(cb@qb-cs@qs,0.,atol=2e-13)
    density=np.array((123.,-456.,789.))
    lam=np.tile(density,mortar+(law=="P1"))
    shell_force=-(cs.T@lam)
    beam_force=cb.T@lam
    assert lam@(cb@qb-cs@qs)==pytest.approx(
        shell_force@qs+beam_force@qb,rel=1e-12,abs=1e-9)
    np.testing.assert_allclose((shell_force[0::2].sum(),
                                shell_force[1::2].sum()),-density[:2],
                               rtol=2e-10,atol=2e-8)
    moment=np.sum(model.nodes[:,0]*shell_force[1::2]-
                  model.nodes[:,1]*shell_force[0::2])
    expected=-(density[1]/2+original.YAW_LENGTH*density[2])
    assert moment==pytest.approx(expected,rel=2e-10,abs=2e-8)
    fixed=np.r_[model.supported,model.dof_count+beam.root_dofs(cells)]
    c=sparse.hstack((-cs,cb),format="csr")
    free=np.setdiff1d(np.arange(c.shape[1]),fixed)
    singular=np.linalg.svd(c[:,free].toarray(),compute_uv=False)
    assert singular[-1]>1e-7*singular[0]


@pytest.mark.parametrize("topology",("Q4","CST-CB"))
@pytest.mark.parametrize("law",("P0","P1"))
def test_segmented_pad_mortar_quadrature_parity(topology,law):
    model=shell.panel(2,4,topology)
    a,b,_=area.coupling(model,4,2,law,.037,order=6)
    x,y,_=area.coupling(model,4,2,law,.037,order=8)
    for low,high in ((a,x),(b,y)):
        difference=(low-high).toarray()
        assert np.max(np.abs(difference))<1e-10


def test_moving_pad_overlay_contains_shell_and_mortar_events():
    model=shell.panel(2,4,"CST-CB")
    halfwidth=.037
    knots=area.overlay(model,4,2,halfwidth)
    assert len(knots)>len(original.overlay(model,4,2))
    assert .5 in knots
    # Independently locate moving x-edge crossings of both orientations
    # of a checkerboard diagonal at the fixed upper pad y-edge.
    yedge=-.23+halfwidth
    fraction=(yedge-(-.5+1/4))*4
    q=np.random.default_rng(17).normal(scale=1e-5,size=model.dof_count)
    from _b3_e4_f03_area_port import pose
    for i,diagonal_fraction in ((0,1-fraction),(1,fraction)):
        diagonal=-.5+(i+diagonal_fraction)/2
        expected=diagonal-(-.2+halfwidth)
        assert np.min(np.abs(knots-expected))<1e-12
        # The moving finite-area field is continuous across either branch.
        left=pose(model,expected-1e-8,halfwidth)@q
        right=pose(model,expected+1e-8,halfwidth)@q
        assert np.max(np.abs(left-right))<2e-9
    with pytest.raises(ValueError):
        area.overlay(model,4,2,0.)


def test_axis_diagnostic_envelope_has_distinct_mortar_and_beam_knots():
    model=shell.panel(8,16,"Q4")
    knots=area.overlay(model,32,16,.05)
    assert knots[0]==0 and knots[-1]==1
    assert np.all(np.diff(knots)>0)
    for value in (1/32,1/16,15/16):
        assert np.min(np.abs(knots-value))<1e-12
    with pytest.raises(ValueError,match='mortar count'):
        area.overlay(model,32,17,.05)


def test_independent_nonconstant_multiplier_moments():
    model=shell.panel(3,6,"Q4")
    halfwidth=.04
    mortar=2
    cs,_,_=area.coupling(model,4,mortar,"P1",halfwidth)
    q=np.array([v for x,y in model.nodes for v in (x*y,0.)])
    x2=.2**2+halfwidth**2/3
    y2=.23**2+halfwidth**2/3
    inertia=x2+y2
    lam=np.zeros(3*(mortar+1))
    lam[2::3]=np.arange(mortar+1)/mortar
    # Analytic Q4 field: yaw(s)=-s*E[y²]/J, hence ∫s*Lc*yaw(s)ds.
    assert lam@(cs@q)==pytest.approx(
        -original.YAW_LENGTH*y2/(3*inertia),rel=2e-10,abs=1e-10)
    lam[1::3]=np.arange(mortar+1)/mortar
    shell_force=-(cs.T@lam)
    assert shell_force[0::2].sum()==pytest.approx(0.,abs=1e-9)
    assert shell_force[1::2].sum()==pytest.approx(-.5,abs=1e-9)
    moment=np.sum(model.nodes[:,0]*shell_force[1::2]-
                  model.nodes[:,1]*shell_force[0::2])
    assert moment==pytest.approx(-1/3-original.YAW_LENGTH/2,
                                 rel=2e-10,abs=1e-9)
