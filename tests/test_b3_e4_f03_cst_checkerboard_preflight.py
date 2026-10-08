"""Mechanical and host-map oracles for the separate classical CST-CB candidate."""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import _b3_e4_f03_gap_enclosure as enclosure
import _b3_e4_f03_independent_beam as beam
import _b3_e4_f03_independent_line as line
import _b3_e4_f03_independent_shell as shell
import _b3_e4_f03_loaded_preflight as loaded


def _reflect(model,axis):
    nx=2*model.n_s
    mapped=[]; signs=[]
    for j in range(model.n_y+1):
        for i in range(nx+1):
            target=((model.n_y-j)*(nx+1)+i if axis=='y' else
                    j*(nx+1)+nx-i)
            mapped.append(target)
    for _ in mapped:
        signs.extend((1,-1) if axis=='y' else (-1,1))
    permutation=np.zeros((model.dof_count,model.dof_count))
    for source,target in enumerate(mapped):
        permutation[2*target,2*source]=signs[2*source]
        permutation[2*target+1,2*source+1]=signs[2*source+1]
    return mapped,permutation


def test_checkerboard_is_ccw_and_reflection_symmetric():
    model=shell.panel(3,4,'CST-CB')
    assert len(model.elements)==4*model.n_s*model.n_y
    assert all(np.linalg.det(np.column_stack((
        np.ones(3),model.nodes[list(element)])))>0
        for element in model.elements)
    incidence={frozenset(element) for element in model.elements}
    k=shell.stiffness(model).toarray()
    for axis in ('x','y'):
        mapped,p=_reflect(model,axis)
        assert {frozenset(mapped[index] for index in element)
                for element in model.elements}==incidence
        assert np.linalg.norm(p.T@k@p-k)/np.linalg.norm(k)<1e-13


def test_checkerboard_affine_patch_and_pose_work():
    model=shell.panel(2,4,'CST-CB')
    gradient=np.array(((.0007,.0003),(-.0002,-.0004)))
    q=(model.nodes@gradient.T).ravel()
    eps=np.array((gradient[0,0],gradient[1,1],
                  gradient[0,1]+gradient[1,0]))
    expected=2*shell.THICKNESS*(eps@shell.CONSTITUTIVE@eps)
    k=shell.stiffness(model)
    np.testing.assert_allclose(q@(k@q),expected,rtol=2e-11)
    for s in (0.,.19,.5,.83,1.):
        p=shell.pose(model,s)
        offsets=np.asarray(shell.OFFSETS)
        displaced=offsets@gradient.T
        yaw=(offsets[:,0]@displaced[:,1]-offsets[:,1]@displaced[:,0])/\
            shell.YAW_DENOMINATOR
        np.testing.assert_allclose(p@q,(gradient[0,0]*s,
                                         gradient[1,0]*s,yaw),
                                   rtol=1e-11,atol=1e-14)
        wrench=np.array((125.,-930.,72.))
        dq=np.cos(np.arange(model.dof_count)*.3)*.0001
        np.testing.assert_allclose(dq@(p.T@wrench),wrench@(p@dq),
                                   rtol=1e-12,atol=1e-13)


def test_both_diagonal_hosts_and_overlay_branches():
    model=shell.panel(4,4,'CST-CB')
    y=.1; j=2; frac=.4; delta=1e-9
    axes=enclosure._axes(model)
    for i in (2,3):
        x0=-.5+i/model.n_s
        crossing=x0+(frac if (i+j)%2==0 else 1-frac)/model.n_s
        bl=j*(2*model.n_s+1)+i; br=bl+1
        tl=bl+2*model.n_s+1; tr=tl+1
        expected=((bl,tr,tl),(bl,br,tr)) if (i+j)%2==0 else (
            (bl,br,tl),(br,tr,tl))
        for x,want in zip((crossing-delta,crossing+delta),expected):
            actual=shell.sample(model,x,y)[0]
            exact=enclosure._host(model,Fraction.from_float(x),(0.,y),axes)
            assert actual==exact==want
        for x in (crossing-delta,crossing,crossing+delta):
            ids,w=shell.sample(model,x,y)
            assert len(ids)==3
            np.testing.assert_allclose(np.sum(w),1.,rtol=0,atol=1e-12)
    floating=line.overlay(model,4,2)
    exact=enclosure.exact_overlay(model,4,2)
    # Every exact rational host transition belongs to the floating overlay
    # within its stated rounding tolerance, including falling diagonals.
    for knot in exact:
        assert np.min(np.abs(floating-float(knot)))<2e-12


def test_reflected_four_sample_pose_with_nonaffine_field():
    model=shell.panel(3,6,'CST-CB')
    _,p=_reflect(model,'y')
    q=np.cos(np.arange(model.dof_count)*.41)*1e-5
    assert abs((shell.pose(model,.39)@q)[2])>1e-9
    for s in (.11,.39,.77):
        original=shell.pose(model,s)@q
        mirrored=shell.pose(model,s)@(p@q)
        np.testing.assert_allclose(mirrored,original*np.array((1,-1,-1)),
                                   rtol=1e-11,atol=1e-12)


@pytest.mark.parametrize('law',('P0','P1'))
@pytest.mark.parametrize('loading',('smooth','sine'))
def test_checkerboard_small_loaded_balance_and_gap(law,loading):
    result=loaded.evaluate(2,4,4,2,'CST-CB',law,loading,depth=5)
    assert result.free_force_scaled_max<1e-8
    assert result.weak_gap_scaled_max<1e-9
    assert max(map(abs,result.global_balance_scaled))<1e-8
    assert abs(result.energy_identity_joule)/loaded.scaling.E0<1e-8
    assert np.isfinite(result.fixed_scale_gap)
    assert np.isfinite(result.motion_scale_gap)


def test_checkerboard_exact_field_bounds_cover_station_values():
    model=shell.panel(2,4,'CST-CB'); nb=4
    rng=np.random.default_rng(44)
    qs=rng.normal(size=model.dof_count)*1e-5
    qb=rng.normal(size=beam.dof_count(nb))*1e-5
    bounds=enclosure.gap_bounds(model,nb,2,qs,qb,depth=6)
    for s in np.linspace(0,1,121):
        gap=beam.trace(nb,float(s))@qb-shell.pose(model,float(s))@qs
        gap[2]*=line.YAW_LENGTH
        assert all(abs(value)<=upper+1e-12
                   for value,(_,upper) in zip(gap,bounds))


def test_checkerboard_gap_and_motion_quadrature_parity():
    model=shell.panel(2,4,'CST-CB'); nb=4
    rng=np.random.default_rng(91)
    qs=rng.normal(size=model.dof_count)*1e-5
    qb=rng.normal(size=beam.dof_count(nb))*1e-5
    assert abs((shell.pose(model,.37)@qs)[2])>1e-9
    low=loaded._motion_integrals(model,nb,2,qs,qb,order=4)
    high=loaded._motion_integrals(model,nb,2,qs,qb,order=6)
    np.testing.assert_allclose(low,high,rtol=1e-12,atol=1e-18)
    np.testing.assert_allclose(np.sqrt(low[0]),
                               line.integrated_gap(model,nb,2,qs,qb,order=6),
                               rtol=1e-12,atol=1e-14)


def test_checkerboard_rejects_odd_panel_rows():
    with pytest.raises(ValueError,match='unsupported bounded classical panel'):
        shell.panel(2,3,'CST-CB')
