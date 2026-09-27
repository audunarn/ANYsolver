"""Bounded checks of the global Q4 displacement-fit diagnostic."""

import numpy as np

from types import SimpleNamespace

from scripts.b3_e4_f03_c1_global_q4_fit import (
    THICKNESS, constrained_trace_fit, fit_field, fit_matrix,
)


def test_clamped_global_q4_face_fit_recovers_representable_field():
    xs = np.array((-.5, 0., 1.))
    ys = np.array((-.5, 0., .5))
    locations = [(x, y, z) for z in (-THICKNESS/2, THICKNESS/2)
                 for x in (-.5, -.25, 0., .5, 1.)
                 for y in (-.5, -.25, 0., .25, .5)]
    coords = {i: np.asarray(point) for i, point in enumerate(locations)}
    nodes = tuple(coords)
    matrix, free = fit_matrix(coords, nodes, xs, ys)
    rng = np.random.default_rng(421)
    q = rng.normal(scale=1e-4, size=(len(xs)*len(ys), 6))
    q[[j*len(xs) for j in range(len(ys))]] = 0.
    q[:, 5] = 0.
    coefficients = np.array([q[node, component]*(
        THICKNESS if component >= 3 else 1.)
        for (node, component), _ in sorted(free.items(), key=lambda item: item[1])])
    target = matrix@coefficients
    recovered, report = fit_field(matrix, free, target.reshape(-1, 3), len(q))
    np.testing.assert_allclose(recovered.reshape(-1, 6), q, rtol=0., atol=1e-10)
    assert report["fit_component_max_abs_m"] < 1e-11
    station_matrix = rng.normal(size=(72, matrix.shape[1]))
    stations = [SimpleNamespace(weight=.025/3) for _ in range(12)]
    integrated = np.zeros((4, 6, matrix.shape[1]))
    for j in range(12):
        integrated[j//3] += stations[j].weight*station_matrix.reshape(
            12, 6, -1)[j]
    solid_points = (station_matrix@coefficients).reshape(12, 6)
    constrained = constrained_trace_fit(
        matrix, free, recovered, solid_points, stations,
        station_matrix, integrated.reshape(24, -1), target.reshape(-1, 3))
    assert constrained["scaled_weak_row_max_defect_m"] < 1e-10
    assert constrained["weak_row_constrained_face_rms_m"] < 1e-10
    assert constrained["minimum_scaled_station_component_rms_m"] < 1e-10
