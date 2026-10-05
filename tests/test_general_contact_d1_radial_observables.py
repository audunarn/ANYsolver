"""Independent geometric/polynomial observable checks; no coupling execution."""

import math

import numpy as np
import pytest

from docs.d1_review_support.d1_radial_reference_observables import (
    DIAGNOSTIC_BIN_EDGES, PRINCIPAL_BIN_EDGES, SOURCE_RECTANGLE,
    disk_rectangle_area, disk_rectangle_area_moments,
    q1_reference_pressure_observables, uniform_disk_pressure_observables,
)


def _quarter_cumulative(a, b, radius):
    """Closed-form quarter-disk area in [0,a]x[0,b], independent oracle."""
    a, b = min(a,radius), min(b,radius)
    if a <= 0 or b <= 0:
        return 0.
    if a*a+b*b <= radius*radius:
        return a*b
    return .5*(a*math.sqrt(max(0.,radius*radius-a*a))
        + b*math.sqrt(max(0.,radius*radius-b*b))
        + radius*radius*(math.asin(a/radius)+math.asin(b/radius)-math.pi/2))


@pytest.mark.parametrize("edges", [PRINCIPAL_BIN_EDGES, DIAGNOSTIC_BIN_EDGES])
def test_disk_partition_total_force_centroid_and_world_moments(edges):
    p, r = .016, .35
    result = uniform_disk_pressure_observables(p, x_bin_edges=edges, y_bin_edges=edges,
                                               moment_origin_xy=(0.,0.))
    bins = [b for row in result.bins for b in row]
    assert math.fsum(b.force_n for b in bins) == pytest.approx(p*math.pi*r*r, rel=3.e-14)
    assert result.total.force_n == pytest.approx(p*math.pi*r*r, rel=2.e-15)
    np.testing.assert_allclose(result.total.resultant_xy_m, (.6,.6), atol=2.e-16)
    np.testing.assert_allclose(result.total.moment_nm,
                               (.6*result.total.force_n,-.6*result.total.force_n,0), atol=1.e-18)
    for k in range(3):
        assert math.fsum(b.moment_nm[k] for b in bins) == pytest.approx(
            result.total.moment_nm[k], abs=5.e-17)
    assert "reference area" in result.integration_measure


def test_quadrant_force_centroid_and_independent_polar_tensor_gauss():
    r, p = .35, .016
    result = uniform_disk_pressure_observables(p)
    roots, weights = np.polynomial.legendre.leggauss(16)
    rho, wr = .5*r*(roots+1), .5*r*weights
    theta, wt = .25*math.pi*(roots+1), .25*math.pi*weights
    polar_weights = wr[:,None]*wt[None,:]*rho[:,None]
    xs = .6+rho[:,None]*np.cos(theta)[None,:]
    ys = .6+rho[:,None]*np.sin(theta)[None,:]
    bin_result = result.bins[1][1]
    analytic_centroid = .6+4*r/(3*math.pi)
    np.testing.assert_allclose(bin_result.resultant_xy_m,
                               (analytic_centroid,analytic_centroid), atol=4.e-16)
    assert bin_result.force_n == pytest.approx(p*math.pi*r*r/4, rel=3.e-15)
    np.testing.assert_allclose((bin_result.force_n,bin_result.first_x_nm,bin_result.first_y_nm),
        p*np.array((np.sum(polar_weights),np.sum(xs*polar_weights),np.sum(ys*polar_weights))),
        rtol=4.e-15)
    assert bin_result.moment_nm[0] > 0 > bin_result.moment_nm[1]


@pytest.mark.parametrize("rect", [(.62,.92,.65,.88), (.61,.94,.61,.94),
                                  (.8,1.1,.62,.7), (.61,.7,.61,.7)])
def test_asymmetric_clipping_against_closed_form_quarter_cdf(rect):
    x0,x1,y0,y1 = rect
    expected = (_quarter_cumulative(x1-.6,y1-.6,.35)
        -_quarter_cumulative(x0-.6,y1-.6,.35)
        -_quarter_cumulative(x1-.6,y0-.6,.35)
        +_quarter_cumulative(x0-.6,y0-.6,.35))
    actual = disk_rectangle_area_moments(rect)
    assert abs(actual.area_m2-expected) <= actual.estimated_absolute_error[0]+2.e-16


@pytest.mark.parametrize("rect", [(1.,1.1,.5,.7), (.95,1.1,.6,.6),
                                  (.1,.1,.1,1.1), (.95,1.1,.6,.7)])
def test_outside_degenerate_and_tangent_intersections(rect):
    value = disk_rectangle_area_moments(rect)
    assert value.area_m2 == 0.
    assert value.first_x_m3 == value.first_y_m3 == 0.


def test_thin_rectangle_and_thin_circular_cap():
    rect = (.6,.6+1.e-10,.57,.63)
    area = (rect[1]-rect[0])*(rect[3]-rect[2])
    assert disk_rectangle_area(rect) == pytest.approx(area, rel=2.e-15)
    # Unit disk at origin avoids unrelated center subtraction at a tangent.
    d = 1.-1.e-8
    theta = math.acos(d)
    expected = theta**3*(2/3+theta**2*(-2/15+theta**2*(4/315-2*theta**2/2835)))
    cap = disk_rectangle_area_moments((d,1.,-1.,1.), center=(0.,0.), radius_m=1.)
    assert cap.area_m2 > 0.
    assert abs(cap.area_m2-expected) < cap.estimated_absolute_error[0]
    assert cap.first_x_m3/cap.area_m2 == pytest.approx(1., abs=1.e-8)
    assert abs(cap.first_y_m3) <= cap.estimated_absolute_error[2]


def _polynomial_integrals(rect):
    """p=2+3*x+5*y+7*x*y integrated term-by-term, including x*p/y*p."""
    xa,xb,ya,yb = rect
    def power(lo,hi,n):
        return (hi**(n+1)-lo**(n+1))/(n+1)
    coefficients = {(0,0):2., (1,0):3., (0,1):5., (1,1):7.}
    return tuple(sum(c*power(xa,xb,i+dx)*power(ya,yb,j+dy)
                     for (i,j),c in coefficients.items()) for dx,dy in ((0,0),(1,0),(0,1)))


def test_q1_global_polynomial_witness_total_and_non_grid_bin_boundaries():
    xs, ys = np.array((.1,.27,.66,1.1)), np.array((.1,.3,.51,.92,1.1))
    x,y = np.meshgrid(xs,ys)
    result = q1_reference_pressure_observables(xs,ys,2+3*x+5*y+7*x*y,
        x_bin_edges=DIAGNOSTIC_BIN_EDGES,y_bin_edges=DIAGNOSTIC_BIN_EDGES,
        moment_origin_xy=(.2,.3))
    np.testing.assert_allclose((result.total.force_n,result.total.first_x_nm,result.total.first_y_nm),
                               _polynomial_integrals(SOURCE_RECTANGLE), rtol=3.e-15)
    for j,(ya,yb) in enumerate(zip(DIAGNOSTIC_BIN_EDGES[:-1],DIAGNOSTIC_BIN_EDGES[1:])):
        for i,(xa,xb) in enumerate(zip(DIAGNOSTIC_BIN_EDGES[:-1],DIAGNOSTIC_BIN_EDGES[1:])):
            b = result.bins[j][i]
            np.testing.assert_allclose((b.force_n,b.first_x_nm,b.first_y_nm),
                                       _polynomial_integrals((xa,xb,ya,yb)),rtol=4.e-15)
    assert "numerical Q1 reference-pressure" in result.integration_measure
    fx,fy = result.total.first_x_nm,result.total.first_y_nm
    np.testing.assert_allclose(result.total.moment_nm,
        (fy-.3*result.total.force_n,.2*result.total.force_n-fx,0.),atol=1.e-15)


def _independent_tensor_gauss_q1(xs,ys,pressure,rect):
    roots,weights = np.polynomial.legendre.leggauss(3)
    terms = []
    for j,(ya,yb) in enumerate(zip(ys[:-1],ys[1:])):
        yl,yh=max(ya,rect[2]),min(yb,rect[3])
        if yl>=yh:
            continue
        for i,(xa,xb) in enumerate(zip(xs[:-1],xs[1:])):
            xl,xh=max(xa,rect[0]),min(xb,rect[1])
            if xl>=xh:
                continue
            x=.5*(xl+xh)+.5*(xh-xl)*roots[:,None]
            y=.5*(yl+yh)+.5*(yh-yl)*roots[None,:]
            sx,sy=(x-xa)/(xb-xa),(y-ya)/(yb-ya)
            value=((1-sx)*(1-sy)*pressure[j,i]+sx*(1-sy)*pressure[j,i+1]
                   +(1-sx)*sy*pressure[j+1,i]+sx*sy*pressure[j+1,i+1])
            w=np.outer(weights,weights)*.25*(xh-xl)*(yh-yl)
            terms.append([np.sum(w*value),np.sum(w*x*value),np.sum(w*y*value)])
    return np.sum(terms,axis=0)


def test_arbitrary_signed_q1_coefficients_against_independent_tensor_gauss():
    xs,ys=np.array((.1,.16,.53,.71,1.1)),np.array((.1,.4,.48,.95,1.1))
    p=np.random.default_rng(812).normal(size=(len(ys),len(xs)))
    result=q1_reference_pressure_observables(xs,ys,p)
    targets=[(result.total,SOURCE_RECTANGLE)]
    for j,(ya,yb) in enumerate(zip(PRINCIPAL_BIN_EDGES[:-1],PRINCIPAL_BIN_EDGES[1:])):
        for i,(xa,xb) in enumerate(zip(PRINCIPAL_BIN_EDGES[:-1],PRINCIPAL_BIN_EDGES[1:])):
            targets.append((result.bins[j][i],(xa,xb,ya,yb)))
    for measured,rect in targets:
        actual=np.array((measured.force_n,measured.first_x_nm,measured.first_y_nm))
        expected=_independent_tensor_gauss_q1(xs,ys,p,rect)
        assert np.all(np.abs(actual-expected)<=np.array(measured.estimated_absolute_error)+2.e-16)


def test_opening_and_material_force_threshold_keep_absolute_values():
    disk=uniform_disk_pressure_observables(0.)
    assert disk.total.force_n == 0 and disk.total.resultant_xy_m is None
    assert disk.total.moment_nm == (0.,0.,0.)
    xs=(.1,.6,1.1)
    q1=q1_reference_pressure_observables(xs,xs,np.zeros((3,3)))
    assert q1.total.resultant_xy_m is None
    low=uniform_disk_pressure_observables(1.e-10,material_force_threshold_n=1.e-9)
    assert low.total.force_n > 0 and low.total.resultant_xy_m is None
    assert all(b.resultant_xy_m is None for row in low.bins for b in row)
    negative=q1_reference_pressure_observables(xs,xs,-np.ones((3,3)))
    assert negative.total.force_n == pytest.approx(-1.)
    np.testing.assert_allclose(negative.total.resultant_xy_m,(.6,.6),atol=2.e-16)


@pytest.mark.parametrize("kind", ["bins", "shape", "nan", "threshold", "radius"])
def test_invalid_inputs_fail_closed(kind):
    with pytest.raises(ValueError):
        if kind=="bins":
            uniform_disk_pressure_observables(1.,x_bin_edges=(.1,.5,1.))
        elif kind=="shape":
            q1_reference_pressure_observables((.1,1.1),(.1,1.1),np.ones((3,2)))
        elif kind=="nan":
            q1_reference_pressure_observables((.1,1.1),(.1,1.1),np.full((2,2),np.nan))
        elif kind=="threshold":
            uniform_disk_pressure_observables(1.,material_force_threshold_n=-1.)
        else:
            disk_rectangle_area(SOURCE_RECTANGLE,radius_m=-1.)
