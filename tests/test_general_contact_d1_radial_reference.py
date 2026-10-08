"""Independent PDE, force, geometry and trace-bound checks; no coupled solve."""

from fractions import Fraction
import math

import numpy as np
import pytest

from docs.d1_review_support.d1_radial_two_body_reference import (
    RadialTwoBodyReference, continuum_displacement_trace_error_bound,
)


@pytest.mark.parametrize("target_ratio", [.02, 1., 5.])
def test_finite_difference_poisson_equations_on_both_sides_of_front(target_ratio):
    reference = RadialTwoBodyReference(1600., 1600.*target_ratio)
    points = np.array(((.6, .6), (.7, .65), (.85, .7),
                       (1.05, .65), (1.2, .8), (.1, .2)))
    step = 2.e-4
    field = reference.fields_xy(points)
    laplacian = {body: np.zeros(len(points)) for body in ("source_w", "target_w")}
    for axis in range(2):
        direction = np.eye(2)[axis]*step
        first = reference.fields_xy(points+direction)
        last = reference.fields_xy(points-direction)
        farther_first = reference.fields_xy(points+2*direction)
        farther_last = reference.fields_xy(points-2*direction)
        for body in laplacian:
            laplacian[body] += (-farther_first[body]+16*first[body]-30*field[body]
                               +16*last[body]-farther_last[body])/(12*step**2)
    # Independent Cartesian differences test the equations, not derivatives
    # coded into the reference. Fourth-order differences remove the O(h²)
    # log-field Laplacian truncation; points remain clear of the front.
    np.testing.assert_allclose(reference.ds*laplacian["source_w"],
                               reference.load_pa-field["pressure"],
                               rtol=4.e-6, atol=2.e-9)
    np.testing.assert_allclose(reference.dt*laplacian["target_w"],
                               field["pressure"], rtol=4.e-6, atol=2.e-9)


def test_contact_signs_continuity_smooth_fit_and_outer_zero_trace():
    reference = RadialTwoBodyReference(1600., 400.)
    a = reference.contact_radius_m
    radii = np.array((0., .1, .3, a, .4, .6, .8, 1.))
    fields = reference.fields_xy(np.stack((.6+radii, .6+0*radii), axis=-1))
    assert reference.gap_m > 0.
    assert np.all(fields["gap"] >= 0.)
    assert np.all(fields["pressure"] >= 0.)
    np.testing.assert_array_equal(fields["gap"]*fields["pressure"], 0.)
    np.testing.assert_allclose(fields["source_w"]-fields["target_w"],
                               fields["gap"]-reference.gap_m, atol=2.e-21)
    assert fields["source_w"][-1] == pytest.approx(0., abs=3.e-21)
    assert fields["target_w"][-1] == pytest.approx(0., abs=3.e-21)
    assert np.all(fields["source_w"][:-1] < 0.)
    assert np.all(fields["target_w"][:-1] < 0.)

    def at(radius, body):
        return float(reference.fields_xy((.6+radius, .6))[body])

    h = 1.e-5
    expected_derivative = reference.load_pa*a/(2*(reference.ds+reference.dt))
    for body in ("source_w", "target_w"):
        value = at(a, body)
        left = (3*value-4*at(a-h, body)+at(a-2*h, body))/(2*h)
        right = (-3*value+4*at(a+h, body)-at(a+2*h, body))/(2*h)
        assert left == pytest.approx(expected_derivative, rel=2.e-7)
        assert right == pytest.approx(expected_derivative, rel=2.e-7)
        assert abs(at(a+h, body)-at(a-h, body)) < 3*h*expected_derivative


def test_independent_disk_quadrature_force_and_contact_moments():
    reference = RadialTwoBodyReference(1600., 400.)
    roots, weights = np.polynomial.legendre.leggauss(8)
    radius = .5*reference.contact_radius_m*(roots+1)
    radial_weight = .5*reference.contact_radius_m*weights*radius
    theta = np.arange(32)*(2*math.pi/32)
    offsets = radius[:, None, None]*np.stack((np.cos(theta), np.sin(theta)), axis=-1)
    points = offsets+np.array((.6, .6))
    pressure = reference.fields_xy(points)["pressure"]
    area_weight = radial_weight[:, None]*(2*math.pi/32)
    force = float(np.sum(pressure*area_weight))
    moments = (np.sum(offsets[..., 1]*pressure*area_weight),
               -np.sum(offsets[..., 0]*pressure*area_weight), 0.)
    assert force == pytest.approx(reference.force_n, rel=4.e-15)
    np.testing.assert_allclose(moments, reference.contact_moments_nm, atol=1.e-18)


@pytest.mark.parametrize("body", ["source", "target"])
def test_edge_bound_encloses_trace_interpolation_and_exact_rational_bound(body):
    reference = RadialTwoBodyReference(1600., 400.)
    first, last = (.1, .6), (.1, .7)
    bound = reference.edge_trace_error_bound(first, last, body)
    f, ds, dt, a = map(Fraction, (.08, 1600., 400., .35))
    radius_squared = (Fraction(.1)-Fraction(.6))**2
    h_squared = (Fraction(.7)-Fraction(.6))**2
    if body == "source":
        hessian = f/(2*ds)+f*a*a*dt/(2*ds*(ds+dt)*radius_squared)
    else:
        hessian = f*a*a/(2*(ds+dt)*radius_squared)
    assert Fraction(bound.max_error_m) >= h_squared*hessian/8
    assert Fraction(bound.hessian_upper_per_m) >= hessian

    fraction = np.linspace(0., 1., 101)
    points = ((1-fraction[:, None])*np.array(first)
              +fraction[:, None]*np.array(last))
    values = reference.fields_xy(points)[body+"_w"]
    endpoint = reference.fields_xy((first, last))[body+"_w"]
    interpolated = (1-fraction)*endpoint[0]+fraction*endpoint[1]
    assert np.max(np.abs(values-interpolated)) <= bound.max_error_m


def test_frozen_rectangles_have_admissible_geometry_and_strict_trace_budgets():
    reference = RadialTwoBodyReference(1600., 400.)
    source = reference.rectangle_trace_error_bound((.1, 1.1), (.1, 1.1), 12, 12, "source")
    target = reference.rectangle_trace_error_bound((0., 1.3), (-.1, 1.2), 12, 12, "target")
    assert source["edge_count"] == target["edge_count"] == 48
    assert source["minimum_boundary_radius_m"] == pytest.approx(.5)
    assert target["minimum_boundary_radius_m"] == pytest.approx(.6)
    assert source["minimum_boundary_radius_m"] > reference.contact_radius_m
    assert target["minimum_boundary_radius_m"] > reference.contact_radius_m
    for bounds in (((.1, 1.1), (.1, 1.1)), ((0., 1.3), (-.1, 1.2))):
        corners = [(x, y) for x in bounds[0] for y in bounds[1]]
        assert np.max(np.linalg.norm(np.asarray(corners)-(.6, .6), axis=1)) < 1.
    epsilon = continuum_displacement_trace_error_bound(source, target)
    assert epsilon == max(source["max_error_m"], target["max_error_m"])


def test_common_shift_brackets_are_sharp_and_preserve_contact_equations():
    reference = RadialTwoBodyReference(1600., 400.)
    points = np.array(((.6, .6), (.8, .7), (1.1, .8)))
    exact = reference.fields_xy(points)
    epsilon = 1.e-7
    shifted_source = exact["source_w"]+epsilon
    shifted_target = exact["target_w"]+epsilon
    np.testing.assert_allclose(reference.gap_m+shifted_source-shifted_target,
                               exact["gap"], atol=2.e-21)
    np.testing.assert_allclose(shifted_source-exact["source_w"], epsilon, atol=2.e-21)
    # Constant common shifts change neither Cartesian derivatives nor pressure;
    # no smaller universal displacement factor follows from boundary error alone.


@pytest.mark.parametrize("kwargs", [{"ds": 0.}, {"dt": -1.}, {"load_pa": math.nan},
                                    {"contact_radius_m": 1.}, {"radius_m": math.inf}])
def test_invalid_scalar_reference_is_rejected(kwargs):
    values = {"ds": 1600., "dt": 400.}
    values.update(kwargs)
    with pytest.raises(ValueError):
        RadialTwoBodyReference(**values)


def test_invalid_trace_domain_is_rejected():
    reference = RadialTwoBodyReference(1600., 400.)
    with pytest.raises(ValueError, match="outside contact"):
        reference.edge_trace_error_bound((.1, .6), (1.1, .6), "source")
    with pytest.raises(ValueError, match="inside R"):
        reference.edge_trace_error_bound((1.6, .6), (1.6, .7), "target")
    with pytest.raises(ValueError, match="positive length"):
        reference.edge_trace_error_bound((.1, .1), (.1, .1), "source")
