"""Independent geometric controls for the internal C1 common-refinement kernel."""

import numpy as np
import pytest

from anysolver import create_shell_element
from anysolver.fe_core import FEModel
from anysolver.general_contact.overlap import (
    PlanarFace,
    current_planar_shell_face,
    planar_projected_overlap,
    reference_shell_face,
)


def _face(feature, xy, z=0.0):
    return PlanarFace(feature, np.asarray([(x, y, z) for x, y in xy], dtype=float))


def test_opposed_q4_faces_preserve_their_original_interpolation():
    integration = _face((1, 1), ((0, 0), (1, 0), (1, 1), (0, 1)))
    target = _face((2, 1), ((0.5, 0), (0.5, 1), (1.5, 1), (1.5, 0)), z=0.1)
    overlap = planar_projected_overlap(integration, target)
    assert overlap is not None
    assert overlap.area == pytest.approx(0.5)
    assert len(overlap.polygon) == 4
    point = np.array((0.75, 0.5, 0.0))
    for face in (integration, target):
        shape = overlap.shape_values(face, point)
        assert min(shape) >= 0.0
        np.testing.assert_allclose((shape @ face.corners)[:2], point[:2], atol=1e-12)
    assert (overlap.shape_values(target, point) @ target.corners)[2] == pytest.approx(0.1)


def test_q4_s3_partial_overlap_has_the_analytical_area():
    square = _face((1, 1), ((0, 0), (1, 0), (1, 1), (0, 1)))
    triangle = _face((2, 1), ((0.5, 0), (1.5, 0), (0.5, 1)), z=0.2)
    overlap = planar_projected_overlap(square, triangle)
    assert overlap is not None
    assert overlap.area == pytest.approx(0.375)
    centroid = np.mean(overlap.polygon, axis=0)
    assert sum(overlap.shape_values(square, centroid)) == pytest.approx(1.0)
    assert sum(overlap.shape_values(triangle, centroid)) == pytest.approx(1.0)


def test_s3_s3_partial_overlap_has_the_analytical_area():
    first = _face((1, 1), ((0, 0), (1, 0), (0, 1)))
    second = _face((2, 1), ((0.5, 0), (1.5, 0), (0.5, 1)), z=-0.1)
    overlap = planar_projected_overlap(first, second)
    assert overlap is not None
    assert overlap.area == pytest.approx(0.125)


def test_crossed_faces_are_found_when_no_vertex_is_inside_the_other_face():
    horizontal = _face((1, 1), ((-1, -0.1), (1, -0.1),
                                (1, 0.1), (-1, 0.1)))
    vertical = _face((2, 1), ((-0.1, -1), (0.1, -1),
                              (0.1, 1), (-0.1, 1)), z=0.01)
    overlap = planar_projected_overlap(horizontal, vertical)
    assert overlap is not None
    assert overlap.area == pytest.approx(0.04)


def test_projected_area_and_shape_values_are_rigid_frame_invariant():
    square = _face((1, 1), ((0, 0), (1, 0), (1, 1), (0, 1)))
    triangle = _face((2, 1), ((0.5, 0), (1.5, 0), (0.5, 1)), z=0.2)
    reference = planar_projected_overlap(square, triangle)
    rotation = np.array(((0.0, -1.0, 0.0),
                         (0.0, 0.0, -1.0),
                         (1.0, 0.0, 0.0)))
    shift = np.array((1.0, -2.0, 3.0))
    rotated_square = PlanarFace((1, 1), square.corners @ rotation.T + shift)
    rotated_triangle = PlanarFace((2, 1), triangle.corners @ rotation.T + shift)
    rotated = planar_projected_overlap(rotated_square, rotated_triangle)
    assert rotated is not None
    assert rotated.area == pytest.approx(reference.area)
    point = np.mean(reference.polygon, axis=0)
    rotated_point = rotation @ point + shift
    np.testing.assert_allclose(rotated.shape_values(rotated_square, rotated_point),
                               reference.shape_values(square, point), atol=1e-12)
    np.testing.assert_allclose(rotated.shape_values(rotated_triangle, rotated_point),
                               reference.shape_values(triangle, point), atol=1e-12)


def test_overlap_uses_face_scale_for_micrometre_geometry():
    scale = 1.0e-6
    first = _face((1, 1), tuple((scale * x, scale * y)
                                 for x, y in ((0, 0), (1, 0), (1, 1), (0, 1))))
    second = _face((2, 1), tuple((scale * x, scale * y)
                                  for x, y in ((0.5, 0), (1.5, 0),
                                               (1.5, 1), (0.5, 1))))
    overlap = planar_projected_overlap(first, second)
    assert overlap is not None
    assert overlap.area == pytest.approx(0.5 * scale * scale, rel=1e-9)
    point = np.array((0.75 * scale, 0.5 * scale, 0.0))
    np.testing.assert_allclose(overlap.shape_values(first, point),
                               (0.125, 0.375, 0.375, 0.125), atol=1e-10)


def test_warped_and_crossed_q4_are_rejected():
    with pytest.raises(ValueError, match="planar"):
        PlanarFace((1, 1), np.array(((0, 0, 0), (1, 0, 0),
                                    (1, 1, 0.1), (0, 1, 0))))
    with pytest.raises(ValueError, match="strictly convex"):
        _face((1, 1), ((0, 0), (1, 1), (0, 1), (1, 0)))


def test_reference_shell_adapter_uses_s3_material_offset_and_physical_director():
    model = FEModel("reference_shell_skins")
    model.add_material("elastic", 1.0e5, 0.3)
    for node_id, xyz in enumerate(((0, 0, 0), (1, 0, 0),
                                   (0, 1, 0), (1, 1, 0)), 1):
        model.add_node(node_id, *xyz)
    model.add_element(1, create_shell_element(
        1, [1, 2, 3], "elastic", formulation="e4-pl-s3-v2d",
        thickness=0.2, reference_normal=(0, 0, 1),
        reference_surface_offset=0.03,
    ))
    model.add_element(2, create_shell_element(
        2, [1, 2, 4, 3], "elastic", thickness=0.2,
    ))
    assert reference_shell_face(model, 7, 1, "top").corners[:, 2] == pytest.approx(
        (0.07,) * 3
    )
    assert reference_shell_face(model, 7, 1, "midsurface").corners[:, 2] == pytest.approx(
        (-0.03,) * 3
    )
    assert reference_shell_face(model, 7, 1, "bottom").corners[:, 2] == pytest.approx(
        (-0.13,) * 3
    )
    assert reference_shell_face(model, 8, 2, "top").corners[:, 2] == pytest.approx(
        (0.1,) * 4
    )


def test_current_physical_faces_track_relative_sliding_and_recontact():
    model = FEModel("trial_shell_overlap")
    model.add_material("elastic", 1.0e5, 0.3)
    square = ((0, 0), (1, 0), (1, 1), (0, 1))
    for node_id, (x, y, z) in enumerate(
        (*((x, y, 0.0) for x, y in square),
         *((x, y, 0.05) for x, y in square)), 1
    ):
        model.add_node(node_id, x, y, z)
    model.add_element(1, create_shell_element(
        1, (1, 2, 3, 4), "elastic", thickness=0.05,
    ))
    model.add_element(2, create_shell_element(
        2, (5, 6, 7, 8), "elastic", thickness=0.05,
    ))
    displacement = np.zeros(model.mesh.dof_manager.total_dofs)
    target = current_planar_shell_face(model, 2, 1, "top", displacement)
    for shift, expected_area in ((0.0, 1.0), (0.5, 0.5), (1.1, None),
                                 (0.25, 0.75)):
        for node_id in (5, 6, 7, 8):
            displacement[model.mesh.dof_manager.get_node_dofs(node_id)[0]] = shift
        integration = current_planar_shell_face(
            model, 1, 2, "bottom", displacement
        )
        overlap = planar_projected_overlap(integration, target)
        if expected_area is None:
            assert overlap is None
        else:
            assert overlap is not None
            assert overlap.area == pytest.approx(expected_area)
    displacement[:] = 0.0
    displacement[model.mesh.dof_manager.get_node_dofs(8)[2]] = 0.01
    with pytest.raises(ValueError, match="planar"):
        current_planar_shell_face(model, 1, 2, "bottom", displacement)


def test_current_s3_skin_uses_rotated_material_offset():
    model = FEModel("trial_s3_skin")
    model.add_material("elastic", 1.0e5, 0.3)
    for node_id, (x, y) in enumerate(((0, 0), (1, 0), (0, 1)), 1):
        model.add_node(node_id, x, y, 0.0)
    model.add_element(1, create_shell_element(
        1, (1, 2, 3), "elastic", formulation="e4-pl-s3-v2d",
        thickness=0.2, reference_normal=(0, 0, 1),
        reference_surface_offset=0.03,
    ))
    displacement = np.zeros(model.mesh.dof_manager.total_dofs)
    for node_id in (1, 2, 3):
        dofs = model.mesh.dof_manager.get_node_dofs(node_id)
        displacement[dofs[2]] = 0.02
        displacement[dofs[4]] = 0.1
    face = current_planar_shell_face(model, 1, 1, "top", displacement)
    assert face.corners[:, 0] == pytest.approx((0.007, 1.007, 0.007))
    assert face.corners[:, 2] == pytest.approx((0.09, 0.09, 0.09))
