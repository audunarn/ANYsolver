"""Small compensated-coordinate algebra and native-potential checks."""

from fractions import Fraction as F

import numpy as np
import pytest

from docs.reference_cases.ge_beam3_curved_p5_compensated_coordinates import split_sum, advance, validate_pair
from docs.reference_cases.ge_beam3_curved_p5_compensated_mixed import CompensatedMixedBeamProbe
from docs.reference_cases.ge_beam3_curved_p5_centered_chord import CenteredChordMixedProbe
from docs.reference_cases.ge_beam3_curved_p5_nonlinear_mixed_probe import LocalForceAccuracy, NonlinearLocalError
from docs.reference_cases.ge_beam3_curved_p5_section_probe import DirectedHardeningSectionProbe, SectionHistory
from docs.reference_cases.ge_beam3_curved_p5_algebra_probe import rotation, T3, T6
from docs.reference_cases.ge_beam3_curved_p5_history_path_probe import digest
from test_ge_beam3_curved_p5_algebra_probe import reference, perturbed, section
from test_ge_beam3_curved_p5_nonlinear_mixed_probe import law, A


@pytest.mark.parametrize('values', [(1., 1e-18), (1., 1e-18, -1.), (1e10, -1e10, 1e-18),
    (1., 2e-18, -1., 3e-18), (0.03125, -0.015625, 1e-20), (1e-200, -1e-200, 1e-220)])
def test_two_part_sum_against_exact_fractions(values):
    high, low = split_sum(values)
    assert validate_pair(high, low) == (high, low)
    exact = sum(map(F.from_float, values))
    error = abs(F.from_float(high)+F.from_float(low)-exact)
    assert error <= F('1e-32')*max(abs(exact), max(map(abs, map(F.from_float, values))))


def test_sub_ulp_increments_survive_and_cancel_exactly():
    high, low = 1., 0.
    tiny = 2.**-60
    assert high+tiny == high
    for _ in range(7): high, low = advance(high, low, tiny)
    assert F.from_float(high)+F.from_float(low) == F(1)+7*F.from_float(tiny)
    for _ in range(7): high, low = advance(high, low, -tiny)
    assert (high, low) == (1., 0.)


@pytest.mark.parametrize('values', [(), (1,), (True,), (float('nan'),), (float('inf'),), (1e308, 1e308)])
def test_nonfinite_wrong_type_and_overflow_fail_closed(values):
    with pytest.raises(ValueError): split_sum(values)


def test_noncanonical_pair_rejected():
    with pytest.raises(ValueError, match='normalized'): validate_pair(1., 1e-12)


def test_sub_ulp_coordinate_produces_native_force_instead_of_disappearing():
    ref = reference(0.);low = np.zeros((3,3));low[2,0] = 2.**-60
    section = DirectedHardeningSectionProbe(np.diag([1000.,400.,400.,.02,.01,.02]),[1.,0.,0.,0.,0.,0.],1e6,1.)
    old = CenteredChordMixedProbe(ref, section, order=8)
    new = CompensatedMixedBeamProbe(ref, section, order=8, position_low=low)
    args = (ref.coordinates, ref.nodal_triads, np.tile(np.eye(3),(2,1,1)), np.zeros((2,2,3)))
    a,b = old.evaluate(*args),new.evaluate(*args)
    assert ref.coordinates[2,0]+low[2,0] == ref.coordinates[2,0]
    assert a.residual[12] == 0.
    assert b.residual[12] == pytest.approx(1000*low[2,0], rel=1e-14, abs=0.)
    assert b.potential == pytest.approx(500*low[2,0]**2, rel=1e-14, abs=0.)
    assert abs(b.residual[6]+b.residual[12]) < 1e-30
    for station in b.stations:
        expected = 1000*low[2,0] if station.cell == 1 else 0.
        assert station.response.resultants[0] == pytest.approx(expected,rel=1e-14,abs=0.)


def transformed_pair(high, low, turn, shift):
    """Test-only exact Fraction action on stored binary64 coordinate inputs."""
    a,b=np.zeros_like(high),np.zeros_like(low)
    for node in range(3):
        for i in range(3):
            exact=F.from_float(float(shift[i]))+sum(F.from_float(float(turn[i,k]))*(
                F.from_float(float(high[node,k]))+F.from_float(float(low[node,k]))) for k in range(3))
            a[node,i]=float(exact);b[node,i]=float(exact-F.from_float(float(a[node,i])))
    return a,b


def test_arbitrary_common_rigid_motion_preserves_native_variations():
    ref=reference(.4);x,q,u=perturbed(ref);mom=np.cos(np.arange(12)).reshape(2,2,3)/7
    low=np.zeros((3,3));low[2,0]=2.**-65
    g,shift=rotation([1.8,-1.7,2.1]),np.array([2.,-3.,4.])
    moved_high,moved_low=transformed_pair(x,low,g,shift)
    base=CompensatedMixedBeamProbe(ref,law(),order=8,position_low=low).evaluate(x,q,u,mom)
    other=CompensatedMixedBeamProbe(ref,law(),order=8,position_low=moved_low).evaluate(
        moved_high,np.einsum('ij,njk->nik',g,q),np.einsum('ij,njk->nik',g,u),mom)
    transform=np.eye(36);transform[:24,:24]=np.kron(np.eye(8),g)
    assert abs(other.potential-base.potential) < 1e-11
    assert np.linalg.norm(other.residual-transform@base.residual) < 1e-11
    assert np.linalg.norm(other.hessian-transform@base.hessian@transform.T) < 1e-11*np.linalg.norm(base.hessian)


def test_fresh_local_reconstruction_and_missing_low_part_detection():
    ref=reference(0.);low=np.zeros((3,3));low[2,0]=2.**-60
    elastic=DirectedHardeningSectionProbe(np.diag([1000.,400.,400.,.02,.01,.02]),[1.,0.,0.,0.,0.,0.],1e6,1.)
    one=CompensatedMixedBeamProbe(ref,elastic,order=8,position_low=low)
    result=one.solve(ref.coordinates,ref.nodal_triads,force_accuracy=LocalForceAccuracy(1e-12,2.))
    two=CompensatedMixedBeamProbe(ref,elastic,order=8,origins=one.origins,position_low=low)
    replay=two.evaluate(ref.coordinates,ref.nodal_triads,result.local_rotations,result.moments)
    assert replay.potential==result.potential
    np.testing.assert_array_equal(replay.residual[:18],result.residual)
    assert [digest(s) for s in replay.stations]==[digest(s) for s in result.stations]
    dropped=CompensatedMixedBeamProbe(ref,elastic,order=8,origins=one.origins,position_low=np.zeros((3,3))).evaluate(
        ref.coordinates,ref.nodal_triads,result.local_rotations,result.moments)
    assert digest(replay)!=digest(dropped)


@pytest.mark.parametrize('height,yield_force,load', [(0.,1000.,None),(.4,1000.,None),(.4,.02,None),(.4,.02,[.1,-.2,.3])])
def test_full_mixed_potential_matches_historical_expression(height, yield_force, load):
    ref = reference(height);x,q,u = perturbed(ref);m = np.cos(np.arange(12)).reshape(2,2,3)/7
    old = CenteredChordMixedProbe(ref, law(yield_force), order=8, line_force=load)
    new = CompensatedMixedBeamProbe(ref, law(yield_force), order=8, line_force=load, position_low=np.zeros((3,3)))
    delta = np.sin(np.arange(36)+.4)/300
    a,b = old.evaluate(x,q,u,m,increment=delta),new.evaluate(x,q,u,m,increment=delta)
    assert abs(a.potential-b.potential) < 1e-11
    assert np.linalg.norm(a.residual-b.residual) < 1e-11
    assert np.linalg.norm(a.hessian-b.hessian) < 1e-11*max(1.,np.linalg.norm(a.hessian))
    assert [s.response.plastic_active for s in a.stations] == [s.response.plastic_active for s in b.stations]


@pytest.mark.parametrize('yield_force', [1000.,.02])
def test_condensed_derivatives_include_coordinate_low_parts(yield_force):
    ref=reference(.4);x,q,_=perturbed(ref)
    low=np.full((3,3),2.**-70);low[x==0]=0.
    probe=CompensatedMixedBeamProbe(ref,law(yield_force),order=8,position_low=low)
    policy=LocalForceAccuracy(1e-12,2.);base=probe.solve(x,q,force_accuracy=policy)
    direction=np.sin(np.arange(18)+.2)/8;step=1e-6;responses=[]
    for sign in (1.,-1.):
        d=sign*step*direction.reshape(3,6)
        solved=probe.solve(x+d[:,:3],np.array([rotation(d[n,3:])@q[n] for n in range(3)]),force_accuracy=policy)
        responses.append(probe.evaluate(x,q,solved.local_rotations,solved.moments,increment=np.r_[d.ravel(),np.zeros(18)]))
    plus,minus=responses
    assert abs((plus.potential-minus.potential)/(2*step)-base.residual@direction) < 1e-7
    assert np.linalg.norm((plus.residual[:18]-minus.residual[:18])/(2*step)-base.tangent@direction) < 1e-7
    assert np.linalg.norm(base.tangent-base.tangent.T) < 1e-11


def test_load_work_contains_low_coordinate_and_native_force_derivative():
    ref=reference(0.);low=np.zeros((3,3));low[2,0]=2.**-60
    args=(ref.coordinates,ref.nodal_triads,np.tile(np.eye(3),(2,1,1)),np.zeros((2,2,3)))
    unloaded=CompensatedMixedBeamProbe(ref,law(1000.),order=8,position_low=low).evaluate(*args)
    loaded=CompensatedMixedBeamProbe(ref,law(1000.),order=8,position_low=low,line_force=[1.,0.,0.]).evaluate(*args)
    assert loaded.potential-unloaded.potential == pytest.approx(-low[2,0]/2,rel=1e-14,abs=0.)
    assert loaded.residual[12]-unloaded.residual[12] == pytest.approx(-.5,rel=1e-14,abs=0.)


def test_low_parts_are_copied_and_cannot_alias_constructor_input():
    ref=reference(0.);low=np.zeros((3,3))
    model=CompensatedMixedBeamProbe(ref,law(),order=8,position_low=low)
    low[2,0]=1.
    exported=model.position_low;exported[2,0]=2.
    assert np.array_equal(model.position_low,np.zeros((3,3)))
    bad=CompensatedMixedBeamProbe(ref,law(),order=8,position_low=np.ones((3,3)))
    with pytest.raises(ValueError,match='normalized'):
        bad.evaluate(ref.coordinates,ref.nodal_triads,np.tile(np.eye(3),(2,1,1)),np.zeros((2,2,3)))
    with pytest.raises(NonlinearLocalError): model.solve(ref.coordinates,ref.nodal_triads,max_evaluations=0)


def test_reversal_and_fixed_material_origins():
    ref=reference(.4);x,q,u=perturbed(ref);mom=np.cos(np.arange(12)).reshape(2,2,3)/7
    low=np.zeros((3,3));low[2,0]=2.**-65
    origins=tuple(SectionHistory(.0001*i,.0002*i) for i in range(16))
    base=CompensatedMixedBeamProbe(ref,law(),order=8,origins=origins,position_low=low).evaluate(x,q,u,mom)
    reversed_law=DirectedHardeningSectionProbe(T6@section()@T6.T,T6@A,.02,.4)
    flip=np.diag([-1.,1.,-1.])
    other=CompensatedMixedBeamProbe(ref.reversed(),reversed_law,order=8,origins=origins[::-1],position_low=low[::-1]).evaluate(
        x[::-1],q[::-1]@flip,u[::-1],mom[::-1,::-1]@T3.T)
    assert abs(base.potential-other.potential) < 1e-11
    for a,b in zip(other.stations,base.stations[::-1]):
        assert a.response.origin==b.response.origin
        assert np.linalg.norm(a.response.resultants-T6@b.response.resultants) < 1e-11
