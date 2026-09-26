"""Owned physical B2 definition and objective reference-frame oracles."""

import numpy as np
import pytest

from anysolver._b2_physical_flexibility_linear import LinearSection
from anysolver._b2_physical_linear_definition import (
    GeometricMetadata, MassMetadata, PhysicalB2Member, PROFILE_ID,
)


def section():
    return LinearSection.isotropic(E=200., nu=.25, area=.4,
                                   Iy=.03, Iz=.03, J=.06, ky=.8, kz=.8)


def member(p0=(0., 0., 0.), p1=(2., 0., 0.), y=(0., 1., 0.), **metadata):
    return PhysicalB2Member("beam-A", "geometry/beam-A", (11, 27),
                            (p0, p1), y, "section-A", section(), **metadata)


def global_response(beam, displacement):
    transform=beam.local_dof_map()
    local=beam.local_operator().evaluate(transform@displacement)
    return local.energy, transform.T@local.force, transform.T@local.tangent@transform


def test_owned_reference_and_separate_mass_geometry_metadata():
    points=np.array([[0.,0.,0.],[2.,0.,0.]])
    y=np.array([0.,1.,0.])
    inertia=np.diag([.8,.8,.8,.02,.03,.04])
    mass=MassMetadata("mass-source",(0.,0.,0.),inertia)
    geometric=GeometricMetadata("shape-source",(0.,0.,0.),
                                (0.,.1,0.),(0.,-.1,0.),.2)
    beam=member(points[0],points[1],y,mass=mass,geometric=geometric)
    points[1,0]=9.;y[1]=4.;inertia[0,0]=99.
    assert beam.reference_points_m == ((0.,0.,0.),(2.,0.,0.))
    assert beam.local_y_global == (0.,1.,0.)
    assert mass.matrix_per_m[0][0] == .8
    assert beam.length_m == 2.
    assert beam.mass.source_id == "mass-source"
    assert beam.geometric.centroid_local_m == (0.,.1,0.)
    assert member().mass is None and member().geometric is None
    assert beam.profile_id == PROFILE_ID
    assert beam.unit_system == "SI"
    frame=beam.local_frame_rows();frame[0,0]=99.
    assert beam.local_frame_rows()[0,0] == 1.
    assert GeometricMetadata("no-Wagner",(0.,0.,0.),
                             (0.,.1,0.),(0.,-.1,0.)).geometric_polar_radius_squared_m2 is None


def test_mass_origin_pullback_matches_independent_particle_kinetic_work():
    points=np.array([(0.,.25+y,-.125+z) for y in (-.3,.3)
                     for z in (-.4,.4)])
    velocity=np.array([.13,-.21,.31,-.17,.29,.11])
    def kinetic_matrix(origin):
        matrix=np.zeros((6,6))
        for point in points:
            x,y,z=point-origin
            map_velocity=np.array([[1.,0.,0.,0.,z,-y],
                                   [0.,1.,0.,-z,0.,x],
                                   [0.,0.,1.,y,-x,0.]])
            matrix+=2.*map_velocity.T@map_velocity
        return matrix
    direct=kinetic_matrix(np.zeros(3))
    direct_energy=sum(np.linalg.norm(velocity[:3]+
                     np.cross(velocity[3:],point))**2 for point in points)
    assert .5*velocity@direct@velocity == pytest.approx(direct_energy,rel=1e-14)
    for origin in (np.array([0.,.1,.05]),np.array([0.,-.2,.3])):
        metadata=MassMetadata("particle-inertia",tuple(origin),
                              kinetic_matrix(origin))
        pulled=metadata.matrix_at_reference_axis()
        np.testing.assert_allclose(pulled,direct,rtol=2e-15,atol=2e-15)
        assert .5*velocity@pulled@velocity == pytest.approx(direct_energy,rel=1e-14)
        pulled[0,0]=0.
        assert metadata.matrix_at_reference_axis()[0,0] == 8.


def test_admitted_roundoff_is_canonical_orthonormal_frame():
    beam=member(y=(5e-11,1.,0.))
    frame=beam.local_frame_rows()
    np.testing.assert_allclose(frame@frame.T,np.eye(3),rtol=0.,atol=1e-15)
    assert abs(beam.local_y_global[0]) < 1e-15


def test_reference_axis_rotation_and_reversed_connectivity_work():
    baseline=member()
    u=np.array([.1,-.2,.3,.04,-.02,.01,
                -.05,.07,-.08,.03,.02,-.04])
    energy,force,tangent=global_response(baseline,u)
    angle=np.array([[0.,-1.,0.],[1.,0.,0.],[0.,0.,1.]])
    rotate=np.kron(np.eye(4),angle)
    rotated=member((0.,0.,0.),(0.,2.,0.),(-1.,0.,0.))
    energy_rot,force_rot,tangent_rot=global_response(rotated,rotate@u)
    assert energy_rot == pytest.approx(energy,rel=1e-14)
    np.testing.assert_allclose(force_rot,rotate@force,rtol=1e-13,atol=1e-13)
    np.testing.assert_allclose(tangent_rot,rotate@tangent@rotate.T,
                               rtol=1e-13,atol=1e-13)

    swap=np.block([[np.zeros((6,6)),np.eye(6)],
                   [np.eye(6),np.zeros((6,6))]])
    reversed_beam=member((2.,0.,0.),(0.,0.,0.),(0.,1.,0.))
    energy_rev,force_rev,_=global_response(reversed_beam,swap@u)
    assert energy_rev == pytest.approx(energy,rel=1e-13)
    np.testing.assert_allclose(force_rev,swap@force,rtol=1e-12,atol=1e-12)


def test_generalized_reversal_requires_explicit_section_axis_transform():
    stiffness=np.diag([20.,11.,13.,7.,5.,9.])
    stiffness[0,1]=stiffness[1,0]=.8
    stiffness[2,4]=stiffness[4,2]=.3
    forward_section=LinearSection.generalized(stiffness)
    sign=np.diag([1.,-1.,1.,1.,-1.,1.])
    reversed_section=LinearSection.generalized(sign@stiffness@sign)
    common=("beam-A","source-A",(11,27))
    forward=PhysicalB2Member(*common,((0.,0.,0.),(2.,0.,0.)),
                              (0.,1.,0.),"section-A",forward_section)
    reverse=PhysicalB2Member(*common,((2.,0.,0.),(0.,0.,0.)),
                              (0.,1.,0.),"section-A/reoriented",reversed_section)
    unchanged=PhysicalB2Member(*common,((2.,0.,0.),(0.,0.,0.)),
                                (0.,1.,0.),"section-A",forward_section)
    u=np.array([.1,-.2,.3,.04,-.02,.01,
                -.05,.07,-.08,.03,.02,-.04])
    swap=np.block([[np.zeros((6,6)),np.eye(6)],
                   [np.eye(6),np.zeros((6,6))]])
    energy,force,_=global_response(forward,u)
    reversed_energy,reversed_force,_=global_response(reverse,swap@u)
    assert reversed_energy == pytest.approx(energy,rel=2e-14)
    np.testing.assert_allclose(reversed_force,swap@force,rtol=2e-13,atol=2e-13)
    assert abs(global_response(unchanged,swap@u)[0]-energy) > 1e-4


def test_precise_definition_negatives():
    with pytest.raises(ValueError,match="node IDs"):
        PhysicalB2Member("b","source",None,((0.,0.,0.),(1.,0.,0.)),
                         (0.,1.,0.),"s",section())
    with pytest.raises(ValueError,match="reference positions"):
        PhysicalB2Member("b","source",(1,2),None,
                         (0.,1.,0.),"s",section())
    with pytest.raises(ValueError,match="SI unit"):
        member(unit_system="inch-pound")
    with pytest.raises(ValueError,match="two distinct"):
        PhysicalB2Member("b","source",(1,1),((0.,0.,0.),(1.,0.,0.)),
                         (0.,1.,0.),"s",section())
    with pytest.raises(ValueError,match="perpendicular"):
        member(y=(1.,0.,0.))
    with pytest.raises(ValueError,match="nondegenerate"):
        member(p1=(0.,0.,0.))
    with pytest.raises(ValueError,match="profile/schema"):
        member(profile_id="historical-b2")
    with pytest.raises(ValueError,match="positive-semidefinite"):
        MassMetadata("m",(0.,0.,0.),np.diag([1.,1.,1.,1.,1.,-1.]))
    coupled=np.eye(6);coupled[0,1]=coupled[1,0]=2.
    with pytest.raises(ValueError,match="positive-semidefinite"):
        MassMetadata("m",(0.,0.,0.),coupled)
    massless_rotations=MassMetadata("translational",(0.,0.,0.),
                                    np.diag([1.,1.,1.,0.,0.,0.]))
    assert massless_rotations.matrix_per_m[5][5] == 0.
    with pytest.raises(ValueError,match="polar radius"):
        GeometricMetadata("g",(0.,0.,0.),(0.,0.,0.),(0.,0.,0.),0.)
