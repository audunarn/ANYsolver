"""Narrow old/new control for the Qp trace quadrature preparation.

The hoisted local node incidence and vectorized basis evaluation in
_area_rows/_edge_rows must reproduce the previous pointwise preparation
exactly, with unchanged geometry admission, one-sided selection, crossing
limits, and error semantics. The frozen pointwise _shape is the comparator.
"""

import numpy as np
import pytest

from scripts._b3_e4_f03_conforming_qp_trace import FinitePadQpTrace


X = (-.5, -.12, .29, .81, 1.5)
Y = (-.5, -.08, .18, .5)


def _reference_matrices(trace, station, *, side="right"):
    """The previous pointwise organization, rebuilt on the frozen _shape."""
    pose, first, second = (np.zeros((3, 2*trace.n)) for _ in range(3))
    for ox, oy in trace.offsets:
        l, r = ox-trace.a, ox+trace.a
        bottom, top = oy-trace.a, oy+trace.a
        low = trace._crossing_limit(station+l, station, l)
        high = trace._crossing_limit(station+r, station, r)
        pad_pose = np.zeros((3, 2*trace.n))
        for i, xl, xr in trace._intervals(trace.x, low, high):
            for k, yl, yr in trace._intervals(trace.y, bottom, top):
                jac = (xr-xl)*(yr-yl)/4
                for gx, wx in zip(trace._roots, trace._weights):
                    xx = (xl+xr+(xr-xl)*gx)/2
                    for gy, wy in zip(trace._roots, trace._weights):
                        yy = (yl+yr+(yr-yl)*gy)/2
                        ids, shape, _ = trace._shape(xx, yy, cell=(i, k))
                        weight = jac*wx*wy
                        pad_pose[0, ids] += weight*shape
                        pad_pose[1, trace.n+ids] += weight*shape
                        pad_pose[2, ids] -= weight*yy*shape/trace.j
                        pad_pose[2, trace.n+ids] += weight*(xx-station)*shape/trace.j
        pose += pad_pose
        edges = []
        for x_edge in (low, high):
            rows = np.zeros((6, 2*trace.n))
            for _, yl, yr in trace._intervals(trace.y, bottom, top):
                for gy, wy in zip(trace._roots, trace._weights):
                    yy = (yl+yr+(yr-yl)*gy)/2
                    ids, shape, dx = trace._shape(x_edge, yy, side=side)
                    weight = (yr-yl)*wy/2
                    rows[0, ids] += weight*shape
                    rows[1, trace.n+ids] += weight*shape
                    rows[2, ids] += weight*dx
                    rows[3, trace.n+ids] += weight*dx
                    rows[4, ids] += weight*yy*shape
                    rows[5, ids] += weight*yy*dx
            edges.append(rows)
        left, right = edges
        first[0] += right[0]-left[0]
        first[1] += right[1]-left[1]
        first[2] += (r*right[1]-l*left[1]-pad_pose[1]
            -right[4]+left[4])/trace.j
        second[0] += right[2]-left[2]
        second[1] += right[3]-left[3]
        second[2] += (r*right[3]-l*left[3]-right[1]+left[1]
            -right[5]+left[5])/trace.j
    return tuple(row/trace.area for row in (pose, first, second))


def _control_stations(trace, *, midpoints=True):
    stations = [0., 1.]
    for event in trace.station_breakpoints():
        for value in (event, np.nextafter(event, 0.), np.nextafter(event, 1.)):
            if 0. <= value <= 1.:
                stations.append(float(value))
    if midpoints:
        for lo, hi in trace.station_intervals():
            stations.append((lo+hi)/2)
    return sorted(set(stations))


@pytest.mark.parametrize("p", (1, 2, 3, 4, 5, 6))
def test_hoisted_matrices_match_pointwise_reference(p):
    trace = FinitePadQpTrace(p, x=X, y=Y)
    for side in ("left", "right"):
        for station in _control_stations(trace):
            new = trace.matrices(station, side=side)
            old = _reference_matrices(trace, station, side=side)
            for new_rows, old_rows in zip(new, old):
                np.testing.assert_array_equal(new_rows, old_rows)


def test_default_geometry_near_duplicate_events_match_reference():
    # The default edges carry near-duplicate crossings; the hoisted
    # organization must keep their one-sided limits and measures.
    trace = FinitePadQpTrace(2)
    for side in ("left", "right"):
        for station in _control_stations(trace, midpoints=False):
            new = trace.matrices(station, side=side)
            old = _reference_matrices(trace, station, side=side)
            for new_rows, old_rows in zip(new, old):
                np.testing.assert_array_equal(new_rows, old_rows)


def test_returned_matrices_are_fresh_and_unaliased():
    trace = FinitePadQpTrace(3, x=X, y=Y)
    first = trace.matrices(.3)
    mutated = trace.matrices(.3)
    for rows in mutated:
        rows[:] = 1.
    again = trace.matrices(.3)
    for fresh, original in zip(again, first):
        np.testing.assert_array_equal(fresh, original)


def test_admission_and_error_semantics_unchanged():
    trace = FinitePadQpTrace(3, x=X, y=Y)
    with pytest.raises(ValueError):
        trace.matrices(1.5)
    with pytest.raises(ValueError):
        trace.matrices(-.1)
    with pytest.raises(ValueError):
        trace.matrices(float("nan"))
    with pytest.raises(ValueError):
        trace.matrices(.5, side="both")
    # An empty edge span never admitted its host point before either.
    empty = trace._edge_rows(9., .6, .7, "right")
    np.testing.assert_array_equal(empty, np.zeros((6, 2*trace.n)))
    empty = trace._edge_rows(9., .6, .7, "both")
    np.testing.assert_array_equal(empty, np.zeros((6, 2*trace.n)))
    with pytest.raises(ValueError):
        trace._edge_rows(9., -.1, .1, "right")
    with pytest.raises(ValueError):
        trace._edge_rows(.3, -.1, .1, "both")
    with pytest.raises(ValueError):
        FinitePadQpTrace(0)
    with pytest.raises(ValueError):
        FinitePadQpTrace(True)
    with pytest.raises(ValueError):
        FinitePadQpTrace(7)
    with pytest.raises(ValueError):
        FinitePadQpTrace(2, x=(1., 0.))
    with pytest.raises(ValueError):
        FinitePadQpTrace(2, halfwidth=-.05)
