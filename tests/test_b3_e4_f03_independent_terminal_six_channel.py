"""Physical contracts for the bounded independent six-channel comparator."""

from functools import lru_cache

import numpy as np
import pytest

from scripts.b3_e4_f03_independent_terminal_six_channel import Model, PATCH
from scripts._b3_e4_f03_shell_strip_pose_candidate import reference_spatial_trace_strip
from scripts._b3_e4_f03_shell_trace import make_shell


@lru_cache(None)
def _model(resolution):
    return Model(resolution)


@pytest.mark.parametrize("resolution", (2, 4))
def test_patch_recovers_exact_affine_in_plane_motion_and_yaw(resolution):
    model = _model(resolution)
    q = np.zeros(model.k.shape[0])
    membrane = q[:model.panel.dof_count].reshape(-1, 2)
    x, y = model.panel.nodes.T
    translation = np.array((.002, -.003))
    yaw = .007
    membrane[:, 0] = translation[0]-yaw*y
    membrane[:, 1] = translation[1]+yaw*(x-.95)
    pose = model.shell_patch_pose()@q
    assert pose[[0, 1, 5]] == pytest.approx((*translation, yaw), abs=2e-14)
    assert pose[[2, 3, 4]] == pytest.approx((0., 0., 0.), abs=2e-14)


def test_independent_patch_mean_curl_matches_native_reference_rows():
    model = _model(4)
    actual = model.shell_patch_pose()
    native = reference_spatial_trace_strip(
        make_shell(4, "Q4", n_y=4), .95,
        half_length=.05, half_width=.05)
    assert actual[5, :model.panel.dof_count:2] == pytest.approx(
        native[5, 0::6], abs=1e-12)
    assert actual[5, 1:model.panel.dof_count:2] == pytest.approx(
        native[5, 1::6], abs=1e-12)


def test_rigid_corner_rotation_is_conjugate_to_actual_eccentric_geometry():
    model = _model(2)
    c = model.constraint("rigid")
    beam = model.beam_tip_pose()
    rx = beam[3]
    q = rx/float(rx@rx)
    assert (beam@q)[3] == pytest.approx(1.)
    # With zero shell motion and unit beam twist, the z gap at each corner
    # is -y; the y gap contains the negative 0.085 m eccentric lever arm.
    gap = (c@q).reshape(4, 3)
    assert gap[:, 2] == pytest.approx([-y for _, y in PATCH], abs=2e-14)
    assert gap[:, 1] == pytest.approx([-.085]*4, abs=2e-14)


@pytest.mark.parametrize("law", ("rigid", "distributing"))
@pytest.mark.parametrize("load", ("tip_mx", "tip_fz"))
def test_independent_terminal_solve_satisfies_work_and_constraint(law, load):
    result = _model(2).solve(law, load)
    assert result["rows"] == result["rank"]
    assert result["free_equilibrium_ratio"] < 1e-10
    assert result["constraint_gap_norm"] < 1e-12
    assert abs(result["work_error_j"]) < 1e-10
    assert result["tip_work_coordinate"] > 0.
