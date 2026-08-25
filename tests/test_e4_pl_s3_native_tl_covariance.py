"""Independent covariance checks for the private native S3 TL update.

These tests derive rigid rotations, the published Eq. (11) director gauge,
and the D3 numbering action directly.  They intentionally target private
formulation kernels without establishing a supported public API.
"""

from __future__ import annotations

import itertools
import math

import numpy as np

import anysolver.e4_pl_s3_element as s3
from anysolver.e4_pl_s3_state import reconstruct_director_triad


def _normalized(vector: np.ndarray) -> np.ndarray:
    made = np.asarray(vector, dtype=float)
    return made / np.linalg.norm(made)


def _independent_rodrigues(rotation_vector: np.ndarray) -> np.ndarray:
    """Evaluate ``exp(skew(rotation_vector))`` independently."""

    vector = np.asarray(rotation_vector, dtype=float).reshape(3)
    angle = float(np.linalg.norm(vector))
    skew = np.asarray(
        (
            (0.0, -vector[2], vector[1]),
            (vector[2], 0.0, -vector[0]),
            (-vector[1], vector[0], 0.0),
        ),
        dtype=float,
    )
    if angle == 0.0:
        return np.eye(3)
    return (
        np.eye(3)
        + (math.sin(angle) / angle) * skew
        + ((1.0 - math.cos(angle)) / (angle * angle)) * (skew @ skew)
    )


def _independent_eq11_gauge(normal: np.ndarray) -> np.ndarray:
    """Reconstruct the global-e_y/Eq. (11) chart without production code."""

    unit = _normalized(normal)
    first = np.cross(np.asarray((0.0, 1.0, 0.0)), unit)
    if np.linalg.norm(first) <= 1.0e-12:
        first = np.cross(np.asarray((0.0, 0.0, 1.0)), unit)
    first = _normalized(first)
    second = _normalized(np.cross(unit, first))
    return np.column_stack((first, second, unit))


def _four_distinct_gauges() -> np.ndarray:
    normals = np.asarray(
        (
            (0.11, 0.24, 0.964),
            (0.32, -0.17, 0.932),
            (-0.21, 0.31, 0.927),
            (0.16, 0.43, 0.888),
        ),
        dtype=float,
    )
    triads = np.asarray([_independent_eq11_gauge(item) for item in normals])
    assert all(
        not np.allclose(triads[left], triads[right])
        for left in range(4)
        for right in range(left)
    )
    return triads


def _mixed_rigid_increment(
    nodes: np.ndarray,
    axis: np.ndarray,
    angle: float,
) -> np.ndarray:
    rotation_vector = float(angle) * _normalized(axis)
    rigid_rotation = _independent_rodrigues(rotation_vector)
    increment = np.zeros(20, dtype=float)
    for node, coordinate in enumerate(nodes):
        base = 6 * node
        increment[base : base + 3] = (
            rigid_rotation - np.eye(3)
        ) @ coordinate
        increment[base + 3 : base + 6] = rotation_vector
    return increment


def test_mixed_axis_exact_rigid_q_residual_is_third_order() -> None:
    """The retained quadratic director update leaves only O(theta^3)."""

    nodes = np.asarray(
        ((0.0, 0.0, 0.0), (2.3, 0.1, 0.0), (0.37, 1.41, 0.0)),
        dtype=float,
    )
    triads = np.broadcast_to(np.eye(3), (4, 3, 3)).copy()
    axis = np.asarray((0.31, -0.47, 0.826), dtype=float)
    residuals = []
    for angle in (0.01, 0.02, 0.04):
        values, _jacobian, _hessian = s3._native_incremental_strain_jets(
            nodes,
            triads,
            0.23,
            0.31,
            _mixed_rigid_increment(nodes, axis, angle),
            reference_nodes=nodes,
            reference_frame=np.eye(3),
        )
        # Exact Q nodal transport cancels the membrane terms.  A uniform
        # director field also cancels curvature, leaving only the cubic
        # remainder of the quadratic assumed-shear director expansion.
        np.testing.assert_allclose(values[:6], 0.0, atol=1.0e-14)
        residuals.append(float(np.linalg.norm(values, ord=np.inf)))

    observed_orders = [
        math.log(residuals[index + 1] / residuals[index], 2.0)
        for index in range(2)
    ]
    assert all(2.98 < order < 3.03 for order in observed_orders)
    assert residuals[0] > 1.0e-8


def test_eq11_commit_reconstructs_gauge_instead_of_transporting_it() -> None:
    """Eq. (11) resets tangent gauge after committing the new normal."""

    triads = np.broadcast_to(np.eye(3), (4, 3, 3)).copy()
    triads[0] = _independent_eq11_gauge(
        np.asarray((0.17, -0.29, 0.941), dtype=float)
    )
    rotation = np.asarray((0.08, -0.06, 0.12), dtype=float)
    increment = np.zeros(20, dtype=float)
    increment[3:6] = rotation

    updated = s3._update_native_director_triads(triads, increment)[0]

    first = float(rotation @ triads[0, :, 0])
    second = float(rotation @ triads[0, :, 1])
    drill = float(rotation @ triads[0, :, 2])
    corrected_first = first - 0.5 * drill * second
    corrected_second = second + 0.5 * drill * first
    minimal_rotation = (
        corrected_first * triads[0, :, 0]
        + corrected_second * triads[0, :, 1]
    )
    expected_normal = (
        _independent_rodrigues(minimal_rotation) @ triads[0, :, 2]
    )
    expected = _independent_eq11_gauge(expected_normal)
    q_transported = _independent_rodrigues(rotation) @ triads[0]

    np.testing.assert_allclose(updated, expected, rtol=0.0, atol=2.0e-15)
    np.testing.assert_allclose(updated.T @ updated, np.eye(3), atol=2.0e-15)
    assert np.linalg.det(updated) > 0.999999999999998
    assert np.linalg.norm(updated[:, :2] - q_transported[:, :2]) > 0.1
    # Even the normal differs at the expected third-order truncation scale;
    # this guards against silently replacing the Eq. (14) minimal update by
    # a full global rotation-vector transport.
    assert np.linalg.norm(updated[:, 2] - q_transported[:, 2]) > 1.0e-5


def test_exact_global_ey_normal_uses_global_ez_fallback() -> None:
    for sign in (-1.0, 1.0):
        normal = np.asarray((0.0, sign, 0.0), dtype=float)
        actual = reconstruct_director_triad(normal)
        expected = _independent_eq11_gauge(normal)

        np.testing.assert_array_equal(actual, expected)
        np.testing.assert_array_equal(actual[:, 2], normal)
        np.testing.assert_allclose(actual.T @ actual, np.eye(3), atol=0.0)
        assert np.linalg.det(actual) == 1.0


def test_source_node_four_mapping_uses_hierarchical_values_and_own_gauge() -> None:
    triads = _four_distinct_gauges()
    increment = np.asarray(
        (
            0.0,
            0.0,
            0.0,
            0.07,
            -0.04,
            0.09,
            0.0,
            0.0,
            0.0,
            -0.08,
            0.06,
            0.04,
            0.0,
            0.0,
            0.0,
            0.05,
            0.09,
            -0.07,
            0.031,
            -0.022,
        ),
        dtype=float,
    )
    rotations = increment[:18].reshape(3, 6)[:, 3:]
    tangent_first = np.einsum("ij,ij->i", rotations, triads[:3, :, 0])
    tangent_second = np.einsum("ij,ij->i", rotations, triads[:3, :, 1])
    drill = np.einsum("ij,ij->i", rotations, triads[:3, :, 2])
    corner_first = tangent_first - 0.5 * drill * tangent_second
    corner_second = tangent_second + 0.5 * drill * tangent_first
    expected_first = np.concatenate(
        (corner_first, (float(np.mean(corner_first) + increment[18]),))
    )
    expected_second = np.concatenate(
        (corner_second, (float(np.mean(corner_second) + increment[19]),))
    )

    actual_first, actual_second = s3._native_source_rotation_values(
        triads,
        increment,
    )
    np.testing.assert_allclose(
        actual_first, expected_first, rtol=0.0, atol=2.0e-17
    )
    np.testing.assert_allclose(
        actual_second, expected_second, rtol=0.0, atol=2.0e-17
    )
    np.testing.assert_allclose(
        actual_first[3] - np.mean(actual_first[:3]),
        increment[18],
        rtol=0.0,
        atol=4.0e-18,
    )
    np.testing.assert_allclose(
        actual_second[3] - np.mean(actual_second[:3]),
        increment[19],
        rtol=0.0,
        atol=4.0e-18,
    )

    # The hierarchical values are components of the fourth source rotation
    # in its own, distinct Eq. (11) gauge.
    expected_source_rotation = (
        expected_first[3] * triads[3, :, 0]
        + expected_second[3] * triads[3, :, 1]
    )
    expected_source_normal = (
        _independent_rodrigues(expected_source_rotation) @ triads[3, :, 2]
    )
    expected_source_triad = _independent_eq11_gauge(expected_source_normal)
    updated = s3._update_native_director_triads(triads, increment)
    np.testing.assert_allclose(updated[3], expected_source_triad, atol=2.0e-15)


def test_deformed_current_covariants_use_explicit_reference_basis() -> None:
    reference_nodes = np.asarray(
        ((0.0, 0.0, 0.0), (2.3, 0.1, 0.0), (0.37, 1.41, 0.0)),
        dtype=float,
    )
    current_gradient = np.asarray(
        ((1.16, 0.21, 0.0), (-0.13, 0.91, 0.0), (0.0, 0.0, 1.0)),
        dtype=float,
    )
    increment_gradient = np.asarray(
        ((0.07, -0.11, 0.0), (0.04, 0.055, 0.0), (0.0, 0.0, 0.0)),
        dtype=float,
    )
    current_nodes = reference_nodes @ current_gradient.T
    translation = reference_nodes @ increment_gradient.T
    increment = np.zeros(20, dtype=float)
    for node in range(3):
        increment[6 * node : 6 * node + 3] = translation[node]
    triads = np.broadcast_to(np.eye(3), (4, 3, 3)).copy()

    actual, _jacobian, _hessian = s3._native_incremental_strain_jets(
        current_nodes,
        triads,
        0.29,
        0.22,
        increment,
        reference_nodes=reference_nodes,
        reference_frame=np.eye(3),
    )
    twice_green_lagrange_increment = (
        current_gradient.T @ increment_gradient
        + increment_gradient.T @ current_gradient
        + increment_gradient.T @ increment_gradient
    )
    expected = np.asarray(
        (
            0.5 * twice_green_lagrange_increment[0, 0],
            0.5 * twice_green_lagrange_increment[1, 1],
            twice_green_lagrange_increment[0, 1],
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
        )
    )
    np.testing.assert_allclose(actual, expected, rtol=2.0e-14, atol=2.0e-14)

    deformed_basis_result, _bad_jacobian, _bad_hessian = (
        s3._native_incremental_strain_jets(
            current_nodes,
            triads,
            0.29,
            0.22,
            increment,
            reference_nodes=current_nodes,
            reference_frame=np.eye(3),
        )
    )
    assert np.linalg.norm(deformed_basis_result[:3] - actual[:3]) > 0.04


def test_all_six_d3_numberings_commute_with_director_commit_update() -> None:
    triads = _four_distinct_gauges()
    increment = np.asarray(
        (
            0.01,
            -0.02,
            0.03,
            0.07,
            -0.04,
            0.09,
            -0.02,
            0.03,
            0.01,
            -0.08,
            0.06,
            0.04,
            0.04,
            -0.01,
            -0.03,
            0.05,
            0.09,
            -0.07,
            0.031,
            -0.022,
        ),
        dtype=float,
    )
    baseline = s3._update_native_director_triads(triads, increment)
    external_by_node = increment[:18].reshape(3, 6)

    for permutation in itertools.permutations(range(3)):
        numbered_triads = np.concatenate(
            (triads[:3][list(permutation)], triads[3:]),
            axis=0,
        )
        numbered_increment = np.concatenate(
            (
                external_by_node[list(permutation)].reshape(18),
                increment[18:],
            )
        )
        actual = s3._update_native_director_triads(
            numbered_triads,
            numbered_increment,
        )
        expected = np.concatenate(
            (baseline[:3][list(permutation)], baseline[3:]),
            axis=0,
        )
        np.testing.assert_allclose(
            actual,
            expected,
            rtol=0.0,
            atol=3.0e-15,
            err_msg=f"D3 numbering {permutation}",
        )
