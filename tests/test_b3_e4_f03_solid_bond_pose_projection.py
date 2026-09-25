"""Reference and objectivity controls for the bounded solid pose diagnostic."""

import numpy as np
from scipy.spatial.transform import Rotation

from scripts.b3_e4_f03_ccx_solid_bond_screen import build
from scripts.b3_e4_f03_solid_bond_pose_projection import (
    _read_deck_nodes, project,
)


def test_solid_bond_pose_projection_has_zero_reference_and_common_motion(tmp_path):
    deck, _ = build(
        4,"tip_mx",boundary_policy="left_root",bond_policy="terminal",
        element_family="C3D20R",tip_mx_gap_audit=True,
        bar_clearance_um=2,plate_thickness_mm=35)
    path = tmp_path / "solid.inp"
    path.write_text(deck)
    coords = _read_deck_nodes(path)
    zero = project(coords,{node:np.zeros(3) for node in coords})
    assert np.max(np.abs(zero["distributing_translation_gap_m"])) < 1e-12
    assert np.max(np.abs(zero["distributing_rotation_gap_rad"])) < 1e-12
    assert zero["rigid_corner_gap_max_norm_m"] < 1e-12

    rotation = Rotation.from_rotvec((4e-5,-3e-5,2e-5)).as_matrix()
    shift = np.array((1e-4,-2e-4,3e-4))
    displacement = {node:rotation@xyz+shift-xyz
                    for node,xyz in coords.items()}
    moved = project(coords,displacement)
    assert np.max(np.abs(moved["distributing_translation_gap_m"])) < 1e-10
    assert np.max(np.abs(moved["distributing_rotation_gap_rad"])) < 1e-9
    assert moved["rigid_corner_gap_max_norm_m"] < 1e-10
