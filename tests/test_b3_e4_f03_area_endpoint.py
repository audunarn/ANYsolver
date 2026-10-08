"""Bounded finite-pad endpoint derivative and first-hat diagnostics."""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import _b3_e4_f03_area_endpoint as endpoint
import _b3_e4_f03_area_line as line
import _b3_e4_f03_area_port as port
import _b3_e4_f03_independent_beam as beam
import _b3_e4_f03_independent_line as original
import _b3_e4_f03_independent_shell as shell


@pytest.mark.parametrize('topology',('Q4','CST','CST-CB'))
def test_affine_and_rigid_pad_derivative(topology):
    model=shell.panel(3,6,topology)
    s,a=.371,.037
    ex,ey,gamma,delta=(.014,-.021,.032,-.025)
    q=np.array([v for x,y in model.nodes
                for v in (ex*x+gamma*y,delta*x+ey*y)])
    np.testing.assert_allclose(endpoint.shell_pose_derivative(model,s,a,q),
                               (ex,delta,0.),rtol=1e-12,atol=3e-14)
    tx,ty,omega=(.00013,-.00008,.00021)
    rigid=np.array([v for x,y in model.nodes
                    for v in (tx-omega*y,ty+omega*x)])
    np.testing.assert_allclose(endpoint.shell_pose_derivative(model,s,a,rigid),
                               (0.,omega,0.),rtol=1e-11,atol=3e-15)


@pytest.mark.parametrize('topology',('Q4','CST-CB'))
@pytest.mark.parametrize('station',(.091,.371,.723))
def test_nonaffine_boundary_flux_matches_pose_directional_difference(
        topology,station):
    model=shell.panel(3,6,topology)
    q=np.random.default_rng(218).normal(scale=1e-5,size=model.dof_count)
    a=.037
    step=1e-6
    difference=((port.pose(model,station+step,a)@q)-
                (port.pose(model,station-step,a)@q))/(2*step)
    actual=endpoint.shell_pose_derivative(model,station,a,q)
    np.testing.assert_allclose(actual,difference,rtol=3e-6,atol=2e-10)


@pytest.mark.parametrize('i', (0,1))
def test_checkerboard_both_diagonal_orientations_near_edge_event(i):
    model=shell.panel(2,4,'CST-CB')
    a=.037
    yedge=-.23+a
    fraction=(yedge-(-.5+1/4))*4
    diagonal=-.5+(i+(1-fraction if i==0 else fraction))/2
    event=diagonal-(-.2+a)
    q=np.random.default_rng(71).normal(scale=1e-5,size=model.dof_count)
    for station in (event-1e-4,event+1e-4):
        step=1e-6
        difference=((port.pose(model,station+step,a)@q)-
                    (port.pose(model,station-step,a)@q))/(2*step)
        np.testing.assert_allclose(
            endpoint.shell_pose_derivative(model,station,a,q),difference,
            rtol=4e-6,atol=3e-10)


def test_analytic_quadratic_hermite_beam_derivative():
    n=4
    qb=np.zeros(beam.dof_count(n))
    u=2*n+1
    theta=u+2*(n+1)
    for k in range(2*n+1):
        s=k/(2*n)
        qb[k]=s*s
        qb[theta+k]=2*s*s
    for k in range(n+1):
        s=k/n
        qb[u+2*k]=s**3
        qb[u+2*k+1]=3*s*s
    for s in (.03,.37,.91):
        np.testing.assert_allclose(endpoint.beam_pose_derivative(n,s,qb),
                                   (2*s,3*s*s,4*s),rtol=3e-13,atol=3e-13)


def test_first_hat_identity_for_independent_polynomial_gap():
    h=.125
    norm,weighted=endpoint.first_hat_moments(
        np.array((0.,h/3,h)),h,
        lambda s: np.array((2*s,0.,0.)))
    np.testing.assert_allclose(weighted,(h*h/6,0.,0.),atol=2e-17)
    assert -h*h/6+weighted[0]==pytest.approx(0.,abs=2e-17)
    assert norm==pytest.approx(2*h**1.5/np.sqrt(3),rel=2e-14)
    assert abs(-h*h/6)<=np.sqrt(h/5)*norm


def test_matched_rigid_beam_shell_has_zero_first_cell_gap():
    model=shell.panel(2,4,'CST-CB')
    n=4
    tx,ty,omega=(.00013,-.00008,.00021)
    qs=np.array([v for x,y in model.nodes
                 for v in (tx-omega*y,ty+omega*x)])
    qb=np.zeros(beam.dof_count(n))
    u=2*n+1
    theta=u+2*(n+1)
    qb[:u]=tx
    qb[theta:]=omega
    for k in range(n+1):
        qb[u+2*k]=ty+omega*k/n
        qb[u+2*k+1]=omega
    result=endpoint.first_cell_gap_diagnostic(model,n,2,.04,qs,qb)
    np.testing.assert_allclose(result.endpoint_gap_m,0.,atol=2e-15)
    np.testing.assert_allclose(result.first_hat_identity_residual_m,0.,
                               atol=3e-14)
    assert result.gap_derivative_l2<3e-13
    assert result.endpoint_bound_m<3e-13


def test_constant_gap_bound_includes_nonzero_first_hat_residual():
    model=shell.panel(2,4,'Q4')
    qs=np.zeros(model.dof_count)
    qs[0::2]=-1e-11  # Constant shell translation; beam remains rooted.
    qb=np.zeros(beam.dof_count(4))
    result=endpoint.first_cell_gap_diagnostic(model,4,2,.04,qs,qb)
    assert result.endpoint_gap_m[0]==pytest.approx(1e-11,abs=1e-20)
    assert result.gap_derivative_l2<1e-18
    assert result.first_hat_identity_residual_m[0]==pytest.approx(
        1e-11,abs=1e-20)
    assert result.endpoint_bound_m>=abs(result.endpoint_gap_m[0])-1e-19


@pytest.mark.parametrize('topology',('Q4','CST-CB'))
def test_first_hat_residual_equals_independently_integrated_weak_gap(topology):
    model=shell.panel(2,4,topology)
    n_beam,n_mortar,a=(4,2,.04)
    rng=np.random.default_rng(832)
    qs=rng.normal(scale=1e-5,size=model.dof_count)
    qb=rng.normal(scale=1e-5,size=beam.dof_count(n_beam))
    result=endpoint.first_cell_gap_diagnostic(
        model,n_beam,n_mortar,a,qs,qb)
    h=1/n_mortar
    knots=line.overlay(model,n_beam,n_mortar,a)
    first=np.r_[knots[knots<h-1e-12],h]
    roots,weights=np.polynomial.legendre.leggauss(10)
    weak=np.zeros(3)
    for left,right in zip(first[:-1],first[1:]):
        for root,weight in zip(roots,weights):
            s=(left+right)/2+(right-left)*root/2
            gap=beam.trace(n_beam,s)@qb-port.pose(model,s,a)@qs
            gap[2]*=original.YAW_LENGTH
            weak+=(right-left)*weight/2*(1-s/h)*gap
    np.testing.assert_allclose(result.first_hat_identity_residual_m,
                               2*weak/h,rtol=2e-8,atol=2e-11)


@pytest.mark.parametrize('station',(0.,1.))
def test_nonaffine_one_sided_endpoint_derivative(station):
    model=shell.panel(3,6,'CST-CB')
    q=np.random.default_rng(91).normal(scale=1e-5,size=model.dof_count)
    step=1e-6
    direction=1 if station==0 else -1
    values=[port.pose(model,station+direction*k*step,.037)@q
            for k in (0,1,2)]
    difference=direction*(-3*values[0]+4*values[1]-values[2])/(2*step)
    np.testing.assert_allclose(
        endpoint.shell_pose_derivative(model,station,.037,q),difference,
        rtol=4e-6,atol=3e-10)


def test_invalid_gap_fields_rejected():
    model=shell.panel(2,4,'Q4')
    with pytest.raises(ValueError):
        endpoint.first_cell_gap_diagnostic(model,4,2,.04,
                                           np.zeros(model.dof_count-1),
                                           np.zeros(beam.dof_count(4)))
