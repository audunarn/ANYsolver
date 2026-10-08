"""Preparation checks for an Nm128 classical comparator, without a solve."""

import argparse
from fractions import Fraction
from pathlib import Path
import sys

import numpy as np
import pytest
from scipy import sparse

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import _b3_e4_f03_independent_beam as beam
import _b3_e4_f03_gap_enclosure as enclosure
import _b3_e4_f03_independent_line as line
import _b3_e4_f03_independent_shell as shell
import _b3_e4_f03_kkt_scaling as scaling
import b3_e4_f03_resource_preflight as runner


@pytest.mark.parametrize('topology',('Q4','CST-CB'))
def test_nm128_full_reference_overlay_and_diagnostic_admission(topology):
    mesh=runner._mesh('128,64,512,128')
    model=shell.panel(mesh.n_s,mesh.n_y,topology)
    knots=line.overlay(model,mesh.n_beam,mesh.n_mortar)
    exact=enclosure.exact_overlay(model,mesh.n_beam,mesh.n_mortar)
    assert knots[0]==0 and knots[-1]==1 and np.all(np.diff(knots)>0)
    assert exact[0]==0 and exact[-1]==1
    assert all(Fraction(i,128) in exact for i in range(129))
    assert all(Fraction(i,512) in exact for i in range(513))
    assert len(exact)>=len(knots)
    for a,b in zip(knots[:-1],knots[1:]):
        left=a+(b-a)/4; right=a+3*(b-a)/4
        assert int(left*128)==int(right*128)
        assert int(left*512)==int(right*512)
        for dx,dy in shell.OFFSETS:
            assert shell.sample(model,left+dx,dy)[0]==shell.sample(
                model,right+dx,dy)[0]


@pytest.mark.parametrize('topology',('Q4','CST-CB'))
def test_nm128_p1_patch_and_adjoint_on_both_shell_hosts(topology):
    model=shell.panel(32,64,topology)
    nb=512; nm=128
    cs,cb,knots=line.coupling(model,nb,nm,'P1')
    assert cs.shape==(387,model.dof_count)
    assert cb.shape==(387,beam.dof_count(nb))
    assert len(knots)>nb and sparse.isspmatrix_csr(cs)
    assert sparse.isspmatrix_csr(cb)
    q=np.zeros(beam.dof_count(nb))
    q[:2*nb+1]=np.arange(2*nb+1)/(2*nb)
    h=1/nm
    expected=np.r_[h*h/6,np.arange(1,nm)*h*h,h/2-h*h/6]
    np.testing.assert_allclose((cb@q)[0::3],expected,rtol=1e-11,atol=1e-14)
    rng=np.random.default_rng(128)
    qs=rng.standard_normal(model.dof_count)
    qb=rng.standard_normal(beam.dof_count(nb))
    ps=rng.standard_normal(model.dof_count)
    pb=rng.standard_normal(beam.dof_count(nb))
    lam=rng.standard_normal(387)
    np.testing.assert_allclose(lam@(cb@pb-cs@ps),
                               (-cs.T@lam)@ps+(cb.T@lam)@pb,
                               rtol=1e-13,atol=1e-13)
    measure=np.full(nm+1,1/nm)
    measure[[0,-1]]*=.5
    assert np.all(measure>0)
    # A beam-only full-row-rank witness suffices for the assembled C rank.
    # This is a finite algebraic check, not a uniform inf-sup claim.
    free=np.setdiff1d(np.arange(cb.shape[1]),beam.root_dofs(nb))
    normalized=sparse.diags(1/np.repeat(measure,3))@cb[:,free]
    gram=(normalized@normalized.T).tocsc()
    assert gram.shape==(387,387) and gram.nnz<387**2
    smallest=sparse.linalg.eigsh(gram,k=1,which='SA',return_eigenvectors=False,
                                  tol=1e-9,maxiter=20000)[0]
    largest=sparse.linalg.eigsh(gram,k=1,which='LA',return_eigenvectors=False,
                                 tol=1e-9,maxiter=20000)[0]
    assert np.isfinite(smallest) and np.isfinite(largest)
    assert smallest>1e-12*largest


def test_nm128_exact_gap_and_dimensionless_kkt_layout():
    with pytest.raises(argparse.ArgumentTypeError,match='resource envelope'):
        runner._mesh('128,64,512,129')
    model=shell.panel(3,6,'Q4')
    nb=4; nm=128
    cs,cb,_=line.coupling(model,nb,nm,'P1')
    c=sparse.hstack((-cs,cb),format='csr')
    physical=model.dof_count+beam.dof_count(nb)
    free=np.setdiff1d(np.arange(physical),
                      np.r_[model.supported,model.dof_count+beam.root_dofs(nb)])
    prepared=scaling.build(sparse.eye(physical,format='csr'),c,
                           np.zeros(physical),free,model.dof_count,nb,nm,'P1')
    assert prepared.matrix.shape==(len(free)+387,)*2
    assert np.all(np.isfinite(prepared.matrix.data))
    qs=np.zeros(model.dof_count)
    qb=np.zeros(beam.dof_count(nb))
    qb[:2*nb+1]=.125
    bounds=enclosure.gap_bounds(model,nb,nm,qs,qb,depth=0)
    assert bounds[0][0]<=.125<=bounds[0][1]
    assert all(0<=lo<=hi and np.isfinite(hi) for lo,hi in bounds)
