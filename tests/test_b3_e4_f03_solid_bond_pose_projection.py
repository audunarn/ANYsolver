"""Reference and objectivity controls for the bounded solid pose diagnostic."""

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from scripts.b3_e4_f03_ccx_solid_bond_screen import build
from scripts.b3_e4_f03_solid_bond_pose_projection import (
    _read_deck_nodes, bound_c1_unbonded_vertical_gap, project,
    project_surface_position_moments,
)


@pytest.mark.parametrize("factor,faces,seam_faces", ((2,32,4),(4,128,8),(5,250,10)))
def test_c1_saved_field_gap_bound_distinguishes_open_and_overlapping_faces(
        tmp_path, factor, faces, seam_faces):
    deck, meta = build(
        factor, "tip_fz", boundary_policy="left_root", bond_policy="terminal",
        element_family="C3D20R", reverse_tip_fz=True,
        bar_clearance_um=2, bar_reference_profile="c1_tangent",
        plate_thickness_mm=35, tip_load_map="quadratic_face",
        full_displacement_output=True)
    path = tmp_path / "c1.inp"
    path.write_text(deck)
    coords = _read_deck_nodes(path)
    bar_only = {int(j) for face in meta["unbonded_face_pairs"]
                for i, j in face if i != j}
    assert bar_only
    upward = {node: np.array((0., 0., 1e-4 if node in bar_only else 0.))
              for node in coords}
    positive = bound_c1_unbonded_vertical_gap(
        coords, upward, meta["unbonded_face_pairs"])
    assert positive["status"] == "POSITIVE_SAVED_FIELD_FACE_GAP_BOUND"
    assert positive["face_count"] == faces
    assert positive["seam_face_count"] == seam_faces
    assert positive["minimum_seam_factored_gap_bound_m"] > 0.
    downward = {node: -value for node, value in upward.items()}
    negative = bound_c1_unbonded_vertical_gap(
        coords, downward, meta["unbonded_face_pairs"])
    assert negative["status"] == "INCONCLUSIVE_FACE_GAP_BOUND"
    assert negative["minimum_nonseam_gap_bound_m"] < 0.
    with pytest.raises(ValueError, match="complete 250-face"):
        bound_c1_unbonded_vertical_gap(
            coords, upward, meta["unbonded_face_pairs"][:-1])


def test_solid_bond_pose_projection_has_zero_reference_and_common_motion(tmp_path):
    deck, _ = build(
        4,"tip_mx",boundary_policy="left_root",bond_policy="terminal",
        element_family="C3D20R",tip_mx_gap_audit=True,
        bar_clearance_um=2,plate_thickness_mm=35)
    path = tmp_path / "solid.inp"
    path.write_text(deck)
    coords = _read_deck_nodes(path)
    rotation = Rotation.from_rotvec((4e-5,-3e-5,2e-5)).as_matrix()
    shift = np.array((1e-4,-2e-4,3e-4))
    displacement = {node:rotation@xyz+shift-xyz
                    for node,xyz in coords.items()}
    for kwargs in ({}, {"section_x":.95,"patch_x0":.925,"patch_x1":.975}):
        zero = project(coords,{node:np.zeros(3) for node in coords},**kwargs)
        assert np.max(np.abs(zero["distributing_translation_gap_m"])) < 1e-12
        assert np.max(np.abs(zero["distributing_rotation_gap_rad"])) < 1e-12
        assert zero["rigid_corner_gap_max_norm_m"] < 1e-12
        moved = project(coords,displacement,**kwargs)
        assert np.max(np.abs(moved["distributing_translation_gap_m"])) < 1e-10
        assert np.max(np.abs(moved["distributing_rotation_gap_rad"])) < 1e-9
        assert moved["rigid_corner_gap_max_norm_m"] < 1e-10


def test_factor_five_station_projection_uses_its_actual_quadratic_grid(tmp_path):
    deck, _ = build(
        5, "tip_fz", boundary_policy="left_root", bond_policy="terminal",
        element_family="C3D20R", reverse_tip_fz=True,
        bar_clearance_um=2, bar_reference_profile="c1_tangent",
        plate_thickness_mm=35, tip_load_map="quadratic_face",
        full_displacement_output=True)
    path = tmp_path / "factor5.inp"
    path.write_text(deck)
    coords = _read_deck_nodes(path)
    options = dict(patch_grid=tuple(np.linspace(.9, 1., 6)),
                   transverse_cells=10)
    zero = project(coords, {node: np.zeros(3) for node in coords},
                   **options)
    assert zero["patch_grid_x_m"] == pytest.approx(
        (.9, .92, .94, .96, .98, 1.))
    assert np.max(np.abs(zero["distributing_translation_gap_m"])) < 1e-12
    rotation = Rotation.from_rotvec((4e-5, -3e-5, 2e-5)).as_matrix()
    shift = np.array((1e-4, -2e-4, 3e-4))
    moved = project(coords, {node: rotation@xyz+shift-xyz
                             for node, xyz in coords.items()}, **options)
    assert np.max(np.abs(moved["distributing_translation_gap_m"])) < 1e-10
    assert np.max(np.abs(moved["distributing_rotation_gap_rad"])) < 1e-9


def test_full_bond_interior_patch_is_objective_on_its_actual_grid(tmp_path):
    deck, _ = build(
        4, "tip_mx", boundary_policy="left_root", bond_policy="full",
        element_family="C3D20R", plate_thickness_mm=35,
        tip_load_map="quadratic_face")
    path = tmp_path / "full.inp"
    path.write_text(deck)
    coords = _read_deck_nodes(path)
    options = dict(section_x=.9375, patch_x0=.875, patch_x1=1.,
                   patch_grid=(.875, .9375, 1.))
    zero = project(coords, {node:np.zeros(3) for node in coords}, **options)
    assert zero["patch_grid_x_m"] == [.875, .9375, 1.]
    assert np.max(np.abs(zero["distributing_translation_gap_m"])) < 1e-12
    assert np.max(np.abs(zero["distributing_rotation_gap_rad"])) < 1e-12
    rotation = Rotation.from_rotvec((4e-5, -3e-5, 2e-5)).as_matrix()
    shift = np.array((1e-4, -2e-4, 3e-4))
    moved = project(coords, {node:rotation@xyz+shift-xyz
                             for node,xyz in coords.items()}, **options)
    assert np.max(np.abs(moved["distributing_translation_gap_m"])) < 1e-10
    assert np.max(np.abs(moved["distributing_rotation_gap_rad"])) < 1e-9
    assert moved["rigid_corner_gap_max_norm_m"] < 1e-10


def test_solid_surface_moment_projection_separates_reference_and_section_fit(
        tmp_path):
    deck, _ = build(
        4, "tip_mx", boundary_policy="left_root", bond_policy="terminal",
        element_family="C3D20R", tip_mx_gap_audit=True,
        bar_clearance_um=2, plate_thickness_mm=35,
        tip_load_map="quadratic_face")
    path = tmp_path / "terminal.inp"
    path.write_text(deck)
    coords = _read_deck_nodes(path)
    zero = {node: np.zeros(3) for node in coords}
    reference = project_surface_position_moments(coords, zero)
    assert np.max(np.abs(reference["surface_position_moment_gap_m_rad"])) < 1e-12
    assert reference["reduced_section_gap_rms_m"] < 1e-12
    np.testing.assert_allclose(reference["inertia_eigenvalues_m2"],
                               (.1**2/12, .1**2/12, .1**2/6),
                               rtol=0., atol=1e-12)
    rotation = Rotation.from_rotvec((4e-5, -3e-5, 2e-5)).as_matrix()
    shift = np.array((1e-4, -2e-4, 3e-4))
    moved = project_surface_position_moments(
        coords, {node: rotation@xyz+shift-xyz
                 for node, xyz in coords.items()})
    assert moved["reduced_section_gap_rms_m"] < 1e-9
    assert np.max(np.abs(moved["surface_position_moment_gap_m_rad"])) < 1e-8


def test_full_bond_interior_surface_moment_projection_is_objective(tmp_path):
    deck, _ = build(
        4, "tip_mx", boundary_policy="left_root", bond_policy="full",
        element_family="C3D20R", plate_thickness_mm=35,
        tip_load_map="quadratic_face")
    path = tmp_path / "full.inp"
    path.write_text(deck)
    coords = _read_deck_nodes(path)
    stations = (.5, .5625, .625)
    zero = {node: np.zeros(3) for node in coords}
    reference = project_surface_position_moments(
        coords, zero, stations=stations)
    assert reference["patch_interval_x_m"] == [.5, .625]
    assert np.max(np.abs(reference["surface_position_moment_gap_m_rad"])) < 1e-12
    assert reference["reduced_section_gap_rms_m"] < 1e-12
    rotation = Rotation.from_rotvec((4e-5, -3e-5, 2e-5)).as_matrix()
    shift = np.array((1e-4, -2e-4, 3e-4))
    moved = project_surface_position_moments(
        coords, {node: rotation@xyz+shift-xyz
                 for node, xyz in coords.items()}, stations=stations)
    assert moved["reduced_section_gap_rms_m"] < 1e-9
    assert np.max(np.abs(moved["surface_position_moment_gap_m_rad"])) < 1e-8
