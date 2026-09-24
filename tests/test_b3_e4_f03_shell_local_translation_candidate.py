"""Finite rigid-motion check for the alternate local shell pose origin."""

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from scripts._b3_e4_f03_shell_finite_pose_candidate import (
    pose_from_e4_total, reference_nodes)
from scripts._b3_e4_f03_shell_local_translation_candidate import (
    pose_from_e4_total_local_translation)
from scripts._b3_e4_f03_shell_trace import make_shell


@pytest.mark.parametrize("topology", ("Q4", "S3-V2D"))
@pytest.mark.parametrize("n_s", (1, 2, 4))
def test_local_shell_pose_follows_common_finite_rigid_motion(topology, n_s):
    panel = make_shell(n_s, topology)
    nodes = reference_nodes(panel)
    angle = np.array((.13, -.21, .18))
    frame = Rotation.from_rotvec(angle).as_matrix()
    shift = np.array((.31, -.27, .19))
    total = np.zeros((panel.node_count, 6))
    total[:, :3] = nodes@frame.T+shift-nodes
    total[:, 3:] = angle
    for station in (0., .125, .375, .5, .875, 1.):
        position, current_frame = pose_from_e4_total_local_translation(
            panel, station, total.ravel())
        np.testing.assert_allclose(
            position, frame@np.array((station, 0., 0.))+shift,
            rtol=0., atol=2e-12)
        np.testing.assert_allclose(current_frame, frame, rtol=0., atol=2e-12)


@pytest.mark.parametrize("topology", ("Q4", "S3-V2D"))
def test_local_origin_follows_declared_center_material_point(topology):
    panel = make_shell(8, topology, n_y=8)
    nodes = reference_nodes(panel)
    total = np.zeros((panel.node_count, 6))
    total[:, 0] = 1e-3*nodes[:, 0]**2
    station = .5  # A shell node, so the center material value is exact.
    local = pose_from_e4_total_local_translation(
        panel, station, total.ravel())[0]
    rail = pose_from_e4_total(panel, station, total.ravel())[0]
    np.testing.assert_allclose(local[0], station+1e-3*station**2,
                               atol=1e-14)
    assert rail[0]-local[0] > 3e-5
