"""Independent curved material area, wrench and retained work controls."""
from math import pi
import json,os
from pathlib import Path

import numpy as np
import pytest
from scipy.spatial.transform import Rotation
from scipy.integrate import quad
from numpy.polynomial.legendre import leggauss

from anysolver.general_contact.native_curved_geometry import curved_patch_geometry_control
from anysolver.general_contact.native_curved_plane_work import NativeCurvedMaterialPlaneWork
from anysolver.general_contact.native_surface_quadrature import NativeRoundSurfaceRule
from anysolver.general_contact.native_surface_normal import StraightNormalIntegrationSettings
from test_general_contact_native_retained_station import _reference
from test_general_contact_native_surface_bounds import _independent_point


def _case(settings=None):
    ref=_reference(True)
    rule=NativeRoundSurfaceRule(7,ref,.03,xi_range=(-.9,.8),angle_range=(.2,5.8),
        axial_order=1,angular_order=1)
    settings=settings or StraightNormalIntegrationSettings(1e-10,1e-8,1e-6,64,1.)
    law=NativeCurvedMaterialPlaneWork(rule,plane_origin_m=(0.,0.,0.),
        plane_normal=(0.,0.,1.),normal_stiffness_Pa_per_m=10000.,
        integration_settings=settings)
    p=ref.coordinates.copy();p[:,2]=-.06
    p[1]+=(.003,-.002,-.001)
    U=np.stack((Rotation.from_rotvec((.025,-.015,.01)).as_matrix(),
                Rotation.from_rotvec((-.02,.01,-.015)).as_matrix()))
    return law,p,np.zeros((3,3)),U


def _reference_integral(law,p,low,U,order=64,twist=False):
    # Analytic parabola, planar frame and circular material surface; no production
    # station, area, derivative or contact integration helper.
    nodes,weights=leggauss(order)
    lo,hi=law.rule.definition['xi_range'];al,ar=law.rule.definition['angle_range']
    r=law.rule.definition['radius'];k=law.stiffness
    energy=0.;force=np.zeros(3);moment=np.zeros(3)
    for cell,left,right in ((0,lo,0.),(1,0.,hi)):
        for x,w in zip(nodes,weights):
            xi=(left+right)/2+(right-left)*x/2
            J=np.sqrt(1+.16*xi*xi)
            # r0'=(1,-.4xi,0); frame turn rate=-.4/J².
            for a,v in zip(nodes,weights):
                angle=(al+ar)/2+(ar-al)*a/2
                point=_independent_point(xi,angle,r,p,low,U,twist)
                gap=float(law.normal@(point-law.origin))
                t=xi+1 if cell==0 else xi
                roll=(1-t)*(.1,.4,-.2)[cell]+t*(.1,.4,-.2)[cell+1] if twist else 0.
                area=r*(J+.4*r*np.cos(angle+roll)/(J*J))
                factor=w*v*(right-left)*(ar-al)/4*area
                pressure=k*max(0.,-gap)
                energy+=.5*k*min(gap,0.)**2*factor
                reaction=pressure*law.normal*factor
                force+=reaction;moment+=np.cross(point,reaction)
    return energy,force,moment


def _moved(p,low,U,d,h):
    positions=p.copy()
    for i in range(3):positions[i]+=h*d[6*i:6*i+3]
    cells=np.stack([Rotation.from_rotvec(h*d[18+3*i:21+3*i]).as_matrix()@U[i] for i in range(2)])
    return positions,low,cells


def test_curved_whole_patch_orientation_plane_enclosure_and_independent_area_work():
    law,p,low,U=_case()
    value=law.evaluate(p,low,U)
    independent=_reference_integral(law,p,low,U)
    assert value.geometry.orientation_lower>0
    assert value.geometry.gap_upper_m<0
    assert value.normal_storage_j==pytest.approx(independent[0],rel=1e-9,abs=1e-10)
    np.testing.assert_allclose(value.source_force,independent[1],rtol=1e-9,atol=1e-8)
    np.testing.assert_allclose(value.source_moment,independent[2],rtol=1e-9,atol=1e-8)
    np.testing.assert_array_equal(value.source_force+value.target_force,0.)
    np.testing.assert_array_equal(value.source_moment+value.target_moment,0.)
    np.testing.assert_array_equal(value.residual[24:],0.)
    for i in (3,9,15):np.testing.assert_array_equal(value.residual[i:i+3],0.)
    for xi in np.r_[np.linspace(-.9,-1e-8,37),np.linspace(1e-8,.8,33)]:
        for angle in np.linspace(.2,5.8,13):
            point=_independent_point(xi,angle,.03,p,low,U,False)
            gap=float(law.normal@point)
            assert value.geometry.gap_lower_m<=gap<=value.geometry.gap_upper_m
    path=os.environ.get('CONTACT_APP_RESULT_RECORD')
    if path:
        Path(path+'-curved-work.json').write_text(json.dumps(dict(
            energy_error_j=abs(value.normal_storage_j-independent[0]),
            force_error_n=float(np.linalg.norm(value.source_force-independent[1])),
            moment_error_nm=float(np.linalg.norm(value.source_moment-independent[2])),
            orientation_lower=value.geometry.orientation_lower,
            gap_lower_m=value.geometry.gap_lower_m,gap_upper_m=value.geometry.gap_upper_m,
            intervals=value.intervals,evaluations=value.integrand_evaluations,
            estimated_errors=value.estimated_errors),indent=2))


def test_curved_retained_virtual_work_and_full_spatial_tangent():
    law,p,low,U=_case();value=law.evaluate(p,low,U)
    d=np.random.default_rng(14837).normal(size=42)*.003
    d[24:]=0.
    errors=[];works=[]
    for h in (1e-5,2e-6):
        plus=law.evaluate(*_moved(p,low,U,d,h));minus=law.evaluate(*_moved(p,low,U,d,-h))
        derivative=(plus.residual-minus.residual)/(2*h)
        error=np.linalg.norm(value.tangent@d-derivative)/np.linalg.norm(derivative)
        assert error<=1e-5
        work=(plus.normal_storage_j-minus.normal_storage_j)/(2*h)
        assert work==pytest.approx(value.residual@d,rel=1e-5,abs=1e-9)
        errors.append(float(error));works.append(float(abs(work-value.residual@d)))
    assert np.linalg.norm(value.residual[18:24])>0.
    path=os.environ.get('CONTACT_APP_RESULT_RECORD')
    if path:Path(path+'-curved-tangent.json').write_text(json.dumps(dict(tangent_errors=errors,
        work_errors_j=works),indent=2))


def test_curved_open_state_and_mixed_contact_rejection():
    law,p,low,U=_case()
    p[:,2]=.06
    value=law.evaluate(p,low,U)
    assert value.geometry.gap_lower_m>0 and value.normal_storage_j==0
    np.testing.assert_array_equal(value.residual,0.)
    np.testing.assert_array_equal(value.tangent,0.)
    p[:,2]=0.
    with pytest.raises(ValueError,match='mixed-contact segmentation'):
        law.evaluate(p,low,U)


def test_projected_gap_literal_origin_counterexample_and_resolution_guard():
    from anysolver.general_contact.native_curved_plane_work import _projected_gap
    n=np.array((1.,-1.,0.))/np.sqrt(2.)
    p=np.tile(np.array((1.011,.961,0.)),(3,1))
    arm=-.03*n
    first=_projected_gap(p,np.zeros_like(p),0,.5,arm,np.zeros(3),n)
    second=_projected_gap(p,np.zeros_like(p),0,.5,arm,np.array((2.**48,2.**48,0.)),n)
    assert first==second and first>0
    assert first==pytest.approx(.05/np.sqrt(2.)-.03,abs=2e-16)
    p[:]=0;p[0,2]=np.nextafter(0.,1.)
    with pytest.raises(ValueError,match='scalar projection unresolved'):
        _projected_gap(p,np.zeros_like(p),0,.75,np.zeros(3),np.zeros(3),np.array((0.,0.,1.)))


def test_curved_reference_measure_underflow_fails_explicitly():
    law,p,low,U=_case()
    tiny=NativeCurvedMaterialPlaneWork(law.rule,plane_origin_m=law.origin,
        plane_normal=law.normal,normal_stiffness_Pa_per_m=np.nextafter(0.,1.),
        integration_settings=law.settings)
    with pytest.raises(ValueError,match='reference measure/stiffness unresolved'):
        tiny.evaluate(p,low,U)


def test_whole_orientation_rejects_between_sample_inversion():
    from anysolver.general_contact.native_surface_quadrature import surface_geometry
    from anysolver.general_contact.native_retained_station import NativeRetainedRoundStation
    ref=_reference(True)
    rule=NativeRoundSurfaceRule(7,ref,1e-4,xi_range=(-.95,-.05),angle_range=(.2,5.8),
        axial_order=1,angular_order=1)
    p=ref.coordinates.copy();p[0]=(0.,0.,0.);p[1]=(.005,.01,0.)
    low=np.zeros((3,3));U=np.tile(np.eye(3),(2,1,1))
    # Sole quadrature sample stays outward. A different material station reverses.
    assert rule.evaluate(p,low,U)[0].area_jacobian>0
    hidden=NativeRetainedRoundStation(7,ref,-.25,1e-4,3.)
    with pytest.raises(ValueError,match='singular or reversed'):
        surface_geometry(hidden,p,low,U)
    with pytest.raises(ValueError,match='whole-patch orientation unresolved'):
        curved_patch_geometry_control(rule,p,low,U,np.zeros(3),np.array((0.,0.,1.)))


def test_curved_work_common_rigid_transform_and_numerical_limits():
    law,p,low,U=_case();value=law.evaluate(p,low,U)
    G=Rotation.from_rotvec((.3,-.4,.2)).as_matrix();offset=np.array((1.2,-.7,.3))
    moved=NativeCurvedMaterialPlaneWork(law.rule,plane_origin_m=offset,
        plane_normal=G@law.normal,normal_stiffness_Pa_per_m=law.stiffness,
        integration_settings=law.settings)
    transformed=moved.evaluate(p@G.T+offset,low,G@U)
    assert transformed.normal_storage_j==pytest.approx(value.normal_storage_j,rel=1e-12)
    np.testing.assert_allclose(transformed.source_force,G@value.source_force,rtol=1e-12,atol=1e-8)
    np.testing.assert_allclose(transformed.source_moment,G@value.source_moment+
        np.cross(offset,G@value.source_force),rtol=1e-11,atol=1e-8)
    too_small=StraightNormalIntegrationSettings(1e-30,1e-30,1e-30,1,1.)
    limited,_,_,_=_case(too_small)
    with pytest.raises(MemoryError,match='interval budget'):
        limited.evaluate(p,low,U)
    law.stiffness*=2
    with pytest.raises(ValueError,match='definition/settings changed'):law.evaluate(p,low,U)


def test_curved_reference_derivative_interval_bound_with_twist():
    from anysolver._ge_beam3_centered_reference import CenteredCurvedBeam3ReferenceGeometry
    from anysolver.general_contact.native_curved_geometry import _reference_norm_bounds
    base=_reference(True);frames=base.nodal_triads.copy()
    for i,roll in enumerate((.1,.4,-.2)):
        frames[i]=frames[i]@Rotation.from_rotvec((roll,0.,0.)).as_matrix()
    ref=CenteredCurvedBeam3ReferenceGeometry(base.coordinates,frames)
    for cell,(left,right) in enumerate(((-1.,0.),(0.,1.))):
        lower,upper,prime,_=_reference_norm_bounds(ref,cell)
        for xi in np.linspace(left+1e-8,right-1e-8,199):
            derivative=ref.derivative(float(xi))
            assert lower<=np.linalg.norm(derivative)<=upper
            assert np.linalg.norm(ref.frame_derivative(float(xi)),2)<=prime


def test_twisted_curved_material_reference_measure_and_work():
    from anysolver._ge_beam3_centered_reference import CenteredCurvedBeam3ReferenceGeometry
    law,p,low,U=_case()
    frames=law.reference.nodal_triads.copy()
    for i,roll in enumerate((.1,.4,-.2)):
        frames[i]=frames[i]@Rotation.from_rotvec((roll,0.,0.)).as_matrix()
    ref=CenteredCurvedBeam3ReferenceGeometry(law.reference.coordinates,frames)
    rule=NativeRoundSurfaceRule(7,ref,.03,xi_range=(-.9,.8),angle_range=(.2,5.8),
        axial_order=1,angular_order=1)
    twisted=NativeCurvedMaterialPlaneWork(rule,plane_origin_m=law.origin,
        plane_normal=law.normal,normal_stiffness_Pa_per_m=law.stiffness,
        integration_settings=law.settings)
    value=twisted.evaluate(p,low,U)
    reference=_reference_integral(twisted,p,low,U,order=64,twist=True)
    assert value.normal_storage_j==pytest.approx(reference[0],rel=1e-9,abs=1e-10)
    np.testing.assert_allclose(value.source_force,reference[1],rtol=1e-9,atol=1e-8)
    np.testing.assert_allclose(value.source_moment,reference[2],rtol=1e-9,atol=1e-8)


@pytest.mark.parametrize('open_state',(False,True))
def test_large_tangential_plane_origin_does_not_change_contact_work(open_state):
    # Same plane: n dot origin=0 exactly for both declared binary coordinates.
    law,p,low,U=_case()
    n=np.array((1.,-1.,0.))/np.sqrt(2.)
    plain=NativeCurvedMaterialPlaneWork(law.rule,plane_origin_m=(0.,0.,0.),
        plane_normal=n,normal_stiffness_Pa_per_m=law.stiffness,
        integration_settings=law.settings)
    distant=NativeCurvedMaterialPlaneWork(law.rule,plane_origin_m=(2.**48,2.**48,0.),
        plane_normal=n,normal_stiffness_Pa_per_m=law.stiffness,
        integration_settings=law.settings)
    # The complete source is placed on one side by its normal translation.
    p+= (2. if open_state else -2.)*n
    first=plain.evaluate(p,low,U);second=distant.evaluate(p,low,U)
    assert first.geometry.gap_lower_m==second.geometry.gap_lower_m
    assert first.geometry.gap_upper_m==second.geometry.gap_upper_m
    assert second.normal_storage_j==first.normal_storage_j
    np.testing.assert_array_equal(second.residual,first.residual)
    np.testing.assert_array_equal(second.tangent,first.tangent)


def test_large_tangential_origin_cannot_create_contact_on_open_curved_patch():
    ref=_reference(True);n=np.array((1.,-1.,0.))/np.sqrt(2.)
    rule=NativeRoundSurfaceRule(7,ref,.03,xi_range=(.9899,.9901),angle_range=(.2,5.8),
        axial_order=1,angular_order=1)
    G=Rotation.from_rotvec((0.,0.,np.pi/4+np.arctan(.4*.99))).as_matrix()
    chord_point=G@np.array((.99,.002,0.))
    offset=np.array((1.011,.961,0.))-chord_point
    p=ref.coordinates@G.T+offset;low=np.zeros((3,3));U=np.tile(G,(2,1,1))
    settings=StraightNormalIntegrationSettings(1e-10,1e-8,1e-6,64,1.)
    distant=NativeCurvedMaterialPlaneWork(rule,plane_origin_m=(2.**48,2.**48,0.),
        plane_normal=n,normal_stiffness_Pa_per_m=10000.,integration_settings=settings)
    # Continuous plane slab proves positive gap; no force is allowed.
    geometry=curved_patch_geometry_control(rule,p,low,U,distant.origin,n)
    assert geometry.gap_lower_m>.003
    value=distant.evaluate(p,low,U)
    assert value.normal_storage_j==0.
    np.testing.assert_array_equal(value.residual,0.)
