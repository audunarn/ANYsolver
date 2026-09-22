"""Small independent polynomial/pad/variational unit checks; no gate runs."""

import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import _b3_e4_f03_primal_ritz as ritz


def test_supported_legendre_basis_and_closed_form_derivatives():
    n=3
    for x in (-.5,1.5):
        phi,*_=ritz.basis(n,x,np.array((-.37,0.,.41)))
        np.testing.assert_allclose(phi,0.,atol=0.)
    x,y=.17,.23
    p,dx,dy,dxx=ritz.basis(n,x,y)
    X=x-.5; Y=2*y
    assert p[0]==pytest.approx(1-X*X)
    assert dx[0]==pytest.approx(-2*X)
    assert dy[0]==pytest.approx(0.)
    assert dxx[0]==pytest.approx(-2.)
    assert p[1]==pytest.approx((1-X*X)*Y)
    assert dy[1]==pytest.approx(2*(1-X*X))
    h=1e-5
    p_plus=ritz.basis(n,x+h,y)[0]
    p_minus=ritz.basis(n,x-h,y)[0]
    np.testing.assert_allclose((p_plus-p_minus)/(2*h),dx,rtol=2e-9,atol=2e-10)


@pytest.mark.parametrize('s',(0.,.137,.5,.913,1.))
def test_exact_rectangular_moments_station_derivatives_and_rigid_lifts(s):
    n=2; m=n*n-1
    a,a1,a2=ritz.pose_operators(n,s)
    sigma_x2=.2**2+ritz.HALFWIDTH**2/3
    X=s-.5
    mean=1-X*X-sigma_x2
    assert a[0,0]==pytest.approx(mean,abs=5e-15)
    assert a1[0,0]==pytest.approx(-2*X,abs=5e-15)
    assert a2[0,0]==pytest.approx(-2.,abs=5e-15)
    assert a[1,m]==pytest.approx(mean,abs=5e-15)
    assert a[2,m]==pytest.approx(-2*X*sigma_x2/ritz.J,abs=5e-15)
    assert a1[2,m]==pytest.approx(-2*sigma_x2/ritz.J,abs=5e-15)
    assert a2[2,m]==pytest.approx(0.,abs=5e-15)
    for channel,expected,dexpected in (
            (0,(1.,0.,0.),(0.,0.,0.)),
            (1,(0.,1.,0.),(0.,0.,0.)),
            (2,(0.,s,1.),(0.,1.,0.))):
        left,dl=ritz._lift_pose(0,channel,s)
        right,dr=ritz._lift_pose(1,channel,s)
        np.testing.assert_allclose(left+right,expected,rtol=0,atol=2e-14)
        np.testing.assert_allclose(dl+dr,dexpected,rtol=0,atol=2e-14)


@pytest.mark.parametrize('n',(2,3))
def test_exact_quadrature_shell_energy_root_rank_and_free_slope(n):
    operators=ritz.assemble(n)
    increased=ritz.assemble(n,polynomial_order=n+3,load_order=64)
    assert operators.shell_stiffness.shape==(2*(n*n-1),)*2
    assert operators.quadrature.polynomial_order==n+1
    assert operators.quadrature.polynomial_degree_bound==2*n
    assert operators.quadrature.load_order==48
    assert operators.quadrature.comparison_load_order==64
    assert operators.quadrature.load_difference_inf_scaled<1e-12
    np.testing.assert_allclose(operators.shell_stiffness,
                               increased.shell_stiffness,rtol=2e-12,atol=1e-4)
    np.testing.assert_allclose(operators.beam_stiffness,
                               increased.beam_stiffness,rtol=2e-12,atol=1e-4)
    np.testing.assert_allclose(operators.load,increased.load,rtol=2e-12,atol=1e-8)
    assert np.linalg.matrix_rank(operators.root_constraint)==3
    m=n*n-1
    if n==2:
        expected=ritz.THICKNESS*ritz.PLANE[0,0]*8/3
        assert operators.shell_stiffness[0,0]==pytest.approx(expected,rel=2e-14)
    root_slope=ritz.pose_operators(n,0.)[1][1]
    fit=np.linalg.lstsq(operators.root_constraint.T,root_slope,rcond=None)[0]
    mismatch=np.linalg.norm(root_slope-operators.root_constraint.T@fit)
    rank=ritz.root_rank_diagnostics(operators)
    if n==2:
        assert mismatch<1e-12
        assert rank['root_slope_independence_ratio']<1e-12
    else:
        assert mismatch>1e-3
        assert rank['root_slope_independence_ratio']>1e-10
    assert np.all(np.linalg.eigvalsh(operators.shell_stiffness)>0)


def test_tiny_manufactured_kkt_energy_and_origin_reaction_balance():
    operators=ritz.assemble(2)
    metrics,state=ritz.solve(operators)
    assert metrics['equilibrium_scaled']<1e-10
    assert metrics['root_compatibility_scaled']<1e-10
    assert metrics['energy_identity_scaled']<1e-10
    assert metrics['augmented_energy_identity_scaled']<1e-10
    assert metrics['scaled_kkt_condition_2']<1e5
    q,eta=state['q'],state['eta']
    np.testing.assert_allclose(metrics['tip_pose_physical'],
                               operators.tip_pose@q,rtol=0,atol=0)
    np.testing.assert_allclose(metrics['tip_pose_scaled_m'],
                               np.diag((1.,1.,ritz.YAW_LENGTH))@
                               operators.tip_pose@q,rtol=0,atol=0)
    assert 'tip_pose_m' not in metrics
    assert q.shape==(operators.dof_count,) and eta.shape==(3,)
    edges=ritz.recover_support_wrenches(operators,q,eta)
    assert edges.shape==(2,3)
    global_balance=(edges.sum(axis=0)-eta+
                    np.array((0.,ritz.F0,.5*ritz.F0)))
    np.testing.assert_allclose(global_balance,0.,rtol=0,atol=2e-7)


def test_scaled_asymmetry_rejected_before_kkt_solve():
    import dataclasses
    operators=ritz.assemble(2)
    shell=operators.shell_stiffness.copy()
    shell[0,1]+=1e6
    with pytest.raises(ValueError,match='asymmetric scaled Ritz shell'):
        ritz.solve(dataclasses.replace(operators,shell_stiffness=shell))


def test_density_and_endpoint_atoms_match_variational_work():
    n=3; nd=2*(n*n-1)
    rng=np.random.default_rng(36)
    q=rng.normal(size=nd)*2e-6
    eta=np.array((340.,-130.,27.))
    roots,weights=np.polynomial.legendre.leggauss(48)
    stations=(roots+1)/2
    recovered=ritz.recover_interface(n,q,eta,stations)
    def virtual(s):
        return np.array((s*s,s*(1-s),1+s)),np.array((2*s,1-2*s,1.))
    lhs=0.;rhs=0.
    for s,w,density in zip(stations,weights/2,recovered['density']):
        test,dtest=virtual(s)
        lhs+=w*density@test
        a,a1,_=ritz.pose_operators(n,float(s))
        b=a@q;db=a1@q
        nqm=np.array((ritz.E*ritz.AREA*db[0],
                      ritz.G*ritz.SHEAR_AREA*(db[1]-b[2]),
                      ritz.E*ritz.INERTIA*db[2]))
        rhs+=w*(ritz.F0*(1+.25*math.cos(2*math.pi*s))*test[1]-
                nqm[0]*dtest[0]-nqm[1]*(dtest[1]-test[2])-
                nqm[2]*dtest[2])
    w0,_=virtual(0.); w1,_=virtual(1.)
    lhs+=recovered['root_atom']@w0+recovered['tip_atom']@w1
    rhs-=eta@w0
    assert lhs==pytest.approx(rhs,rel=2e-12,abs=1e-7)
    np.testing.assert_array_equal(recovered['root_reaction'],-eta)
    np.testing.assert_allclose(recovered['root_elastic']+
                               recovered['root_atom'],recovered['root_reaction'],
                               rtol=0,atol=1e-10)
    np.testing.assert_allclose(recovered['tip_elastic']+
                               recovered['tip_atom'],0.,rtol=0,atol=1e-10)
    np.testing.assert_allclose(recovered['root_section_resultant'],
                               -recovered['root_elastic'],rtol=0,atol=0)


@pytest.mark.parametrize('invalid',(1,25,True))
def test_bound_and_physical_pad_rejections(invalid):
    with pytest.raises(ValueError,match='bounded'):
        ritz.assemble(invalid)
    with pytest.raises(ValueError,match='one fixed'):
        ritz.pose_operators(2,.5,halfwidth=.04)
