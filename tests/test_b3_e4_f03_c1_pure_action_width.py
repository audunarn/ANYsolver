"""Check physical director and thickness-warp extraction independently."""

import numpy as np

from scripts.b3_e4_f03_c1_pure_action_width import _width_metrics


def test_rigid_torsion_is_exact_and_mid_thickness_warp_is_separate():
    x = .9
    ys = np.array((-.05, 0., .05, .5))
    thickness = .035
    angle = .002
    coordinates = {}
    field = []
    shell_nodes = []
    nodal = []
    for y in ys:
        shell_nodes.append((x, y, 0.))
        nodal.append((0., 0., angle*y, angle, 0., 0.))
        for z in (-thickness/2, 0., thickness/2):
            node = len(field)
            coordinates[node] = (x, y, z)
            field.append((0., -angle*z, angle*y))
    node_index = {node: node for node in coordinates}
    arguments = (np.asarray(field), np.asarray(nodal), coordinates,
                 set(coordinates), node_index, np.asarray(shell_nodes),
                 ys, x, "torsion_Mx")
    rigid = _width_metrics(*arguments)
    assert rigid["width_samples"] == 4
    assert rigid["regions"]["under_0p1m_stiffener"]["count"] == 3
    assert rigid["regions"]["outside_stiffener"]["count"] == 1
    assert rigid["native_minus_solid_primary_max"] < 1e-15
    assert rigid["solid_mid_thickness_linear_director_residual_max_m"] < 1e-15

    warped = np.asarray(field).copy()
    warped[4, 0] = 1e-5  # y=0, z=0; top and bottom remain rigid.
    changed = _width_metrics(warped, *arguments[1:])
    np.testing.assert_allclose(changed["solid_mid_thickness_linear_director_residual_max_m"],
                               1e-5, rtol=0., atol=1e-15)
    assert changed["native_minus_solid_primary_max"] < 1e-15
