"""Small algebraic oracles for a distinct endpoint/interior-pad discretization."""

import sys
from pathlib import Path

import numpy as np
import pytest
from scipy import sparse

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import _b3_e4_f03_area_hybrid as hybrid
import _b3_e4_f03_area_line as line
import _b3_e4_f03_independent_beam as beam
import _b3_e4_f03_independent_line as original
import _b3_e4_f03_independent_shell as shell


def _rigid(model,n_beam,tx,ty,omega):
    qs=np.array([v for x,y in model.nodes
                 for v in (tx-omega*y,ty+omega*x)])
    qb=np.zeros(beam.dof_count(n_beam))
    u=2*n_beam+1
    theta=u+2*(n_beam+1)
    qb[:u]=tx
    qb[theta:]=omega
    for k in range(n_beam+1):
        qb[u+2*k]=ty+omega*k/n_beam
        qb[u+2*k+1]=omega
    return qs,qb


def test_independent_cubic_moment_null_but_endpoint_nonzero():
    h=.25
    nodes,weights=np.polynomial.legendre.leggauss(5)
    moments=np.zeros(2)
    for node,weight in zip(nodes,weights):
        t=(node+1)/2
        gap=1-9*t+18*t*t-10*t**3
        moments+=h*weight/2*np.array((1-t,t))*gap
    np.testing.assert_allclose(moments,0.,atol=2e-16)
    assert 1-9*0+18*0-10*0==1
    assert 1-9+18-10==0  # Continuous extension by zero after first cell.


@pytest.mark.parametrize('topology',('Q4','CST-CB'))
@pytest.mark.parametrize('n_mortar',(2,4,8))
def test_equal_rows_local_lift_and_physical_adjoint(topology,n_mortar):
    model=shell.panel(2,4,topology)
    n_beam=4
    raw=hybrid.assemble(model,n_beam,n_mortar,.04)
    lifted=hybrid.assemble(model,n_beam,n_mortar,.04,lifted=True)
    assert raw.interior_count==n_mortar-1
    assert raw.cs.shape==(3*(n_mortar+1),model.dof_count)
    assert raw.cb.shape==(3*(n_mortar+1),beam.dof_count(n_beam))
    np.testing.assert_allclose(raw.row_measures[:3*(n_mortar-1)],
                               1/n_mortar)
    np.testing.assert_array_equal(raw.row_measures[raw.root_rows],1.)
    np.testing.assert_array_equal(raw.row_measures[raw.tip_rows],1.)
    original_cs,original_cb,_=line.coupling(
        model,n_beam,n_mortar,'P1',.04)
    np.testing.assert_allclose(raw.cs[:3*(n_mortar-1)].toarray(),
                               original_cs[3:3*n_mortar].toarray(),atol=1e-14)
    np.testing.assert_allclose(raw.cb[:3*(n_mortar-1)].toarray(),
                               original_cb[3:3*n_mortar].toarray(),atol=1e-14)
    rng=np.random.default_rng(201+n_mortar)
    qs=rng.normal(scale=1e-5,size=model.dof_count)
    qb=rng.normal(scale=1e-5,size=beam.dof_count(n_beam))
    mu=rng.normal(scale=100.,size=raw.cs.shape[0])
    physical=hybrid.to_physical_multipliers(mu,n_mortar)
    np.testing.assert_allclose(
        hybrid.from_physical_multipliers(physical,n_mortar),mu,
        rtol=1e-14,atol=1e-14)
    raw_gap=raw.cb@qb-raw.cs@qs
    lifted_gap=lifted.cb@qb-lifted.cs@qs
    assert mu@lifted_gap==pytest.approx(physical@raw_gap,abs=1e-12)
    np.testing.assert_allclose(lifted.cs.T@mu,raw.cs.T@physical,
                               rtol=1e-12,atol=1e-12)
    np.testing.assert_allclose(lifted.cb.T@mu,raw.cb.T@physical,
                               rtol=1e-12,atol=1e-12)
    assert mu@lifted_gap==pytest.approx(
        (lifted.cb.T@mu)@qb-(lifted.cs.T@mu)@qs,abs=1e-12)
    rigid_s,rigid_b=_rigid(model,n_beam,.00013,-.00008,.00021)
    np.testing.assert_allclose(raw.cb@rigid_b-raw.cs@rigid_s,0.,atol=2e-13)
    np.testing.assert_allclose(lifted.cb@rigid_b-lifted.cs@rigid_s,
                               0.,atol=2e-13)
    # Endpoint evaluation cannot turn the beam's free Hermite root slope
    # into a support row. The exact point pose has a zero slope column.
    root_slope=2*n_beam+2
    assert raw.cb[raw.root_rows,root_slope].nnz==0
    assert lifted.cb[lifted.root_rows,root_slope].nnz==0


def test_both_lift_corrections_land_on_same_interior_row_for_nm2():
    model=shell.panel(2,4,'Q4')
    raw=hybrid.assemble(model,4,2,.04)
    lifted=hybrid.assemble(model,4,2,.04,lifted=True)
    h=1/2
    for matrix_raw,matrix_lift in ((raw.cs,lifted.cs),(raw.cb,lifted.cb)):
        expected=(matrix_raw[:3]-h/6*matrix_raw[raw.root_rows]-
                  h/6*matrix_raw[raw.tip_rows]).toarray()
        np.testing.assert_allclose(matrix_lift[:3].toarray(),expected,
                                   rtol=2e-13,atol=2e-14)
    mu=np.arange(1,10,dtype=float)
    physical=hybrid.to_physical_multipliers(mu,2)
    np.testing.assert_allclose(physical[3:6],mu[3:6]-h/6*mu[:3])
    np.testing.assert_allclose(physical[6:9],mu[6:9]-h/6*mu[:3])


def test_endpoint_atoms_are_exact_work_conjugate_wrenches():
    model=shell.panel(2,4,'CST-CB')
    n_beam,n_mortar=4,4
    op=hybrid.assemble(model,n_beam,n_mortar,.04)
    mu=np.zeros(3*(n_mortar+1))
    mu[op.root_rows]=(3.,-5.,7.)
    mu[op.tip_rows]=(11.,13.,-17.)
    fs=-(op.cs.T@mu)
    fb=op.cb.T@mu
    root=beam.root_dofs(n_beam)
    np.testing.assert_allclose(fb[root],(3.,-5.,7*original.YAW_LENGTH),
                               atol=2e-12)
    tip=np.array((2*n_beam,2*n_beam+1+2*n_beam,
                  2*n_beam+1+2*(n_beam+1)+2*n_beam))
    np.testing.assert_allclose(fb[tip],(11.,13.,-17*original.YAW_LENGTH),
                               atol=2e-12)
    np.testing.assert_allclose((fs[0::2].sum(),fs[1::2].sum()),
                               (-14.,-8.),atol=2e-10)
    moment=np.sum(model.nodes[:,0]*fs[1::2]-model.nodes[:,1]*fs[0::2])
    assert moment==pytest.approx(-(13.+(7.-17.)*original.YAW_LENGTH),
                                 abs=2e-10)


def test_reject_bad_counts_fields_and_nonfinite_multipliers():
    model=shell.panel(2,4,'Q4')
    for n in (1,17,True,2.5):
        with pytest.raises(ValueError):
            hybrid.assemble(model,4,n,.04)
    for n_beam in (0,True,513):
        with pytest.raises(ValueError):
            hybrid.assemble(model,n_beam,2,.04)
    for bad in (float('nan'),0.,.201):
        with pytest.raises(ValueError):
            hybrid.assemble(model,4,2,bad)
    with pytest.raises(ValueError):
        hybrid.assemble(model,4,2,.04,lifted=1)
    for field in (np.zeros(8),np.full(9,float('nan'))):
        with pytest.raises(ValueError):
            hybrid.to_physical_multipliers(field,2)
        with pytest.raises(ValueError):
            hybrid.from_physical_multipliers(field,2)
