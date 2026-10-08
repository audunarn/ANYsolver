"""Bounded representability witnesses for the compatible E4 patch fit."""

import numpy as np

from scripts.b3_e4_f03_c1_global_plate_trace import _fit_e4_patch
from scripts.b3_e4_f03_local_footprint_work import structured_q4_point_shape


def test_q4_patch_fit_recovers_one_shared_nodal_field(f03_q8_sided_faces):
    coords, action, _ = f03_q8_sided_faces
    xs = np.linspace(.9, 1., 5)
    ys = np.linspace(-.05, .05, 5)
    rng = np.random.default_rng(31)
    nodal = rng.normal(size=(25, 5))*1e-6
    field = {}
    for node in action:
        x, y, z = coords[node]
        host, shape = structured_q4_point_shape(xs, ys, float(x), float(y))
        u = shape@nodal[host]
        field[node] = np.array((u[0]+z*u[4], u[1]-z*u[3], u[2]))
    fitted, data = _fit_e4_patch(coords, field, action)
    assert data["fit_rank"] == 125
    assert data["q8_node_rms_difference_m"] < 1e-18
    assert max(np.linalg.norm(fitted[node]-field[node])
               for node in action) < 1e-17


def test_q4_patch_fit_detects_nonrepresentable_single_face_motion(f03_q8_sided_faces):
    coords, action, _ = f03_q8_sided_faces
    field = {node: np.zeros(3) for node in action}
    node = next(node for node in action if
                abs(coords[node][0]-.95) < 1e-10 and
                abs(coords[node][1]) < 1e-10 and
                coords[node][2] > 0)
    field[node] = np.array((0., 0., 1e-6))
    _, data = _fit_e4_patch(coords, field, action)
    assert data["q8_node_rms_difference_m"] > 1e-9
