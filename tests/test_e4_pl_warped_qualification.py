from __future__ import annotations

import numpy as np
import pytest

from anysolver.e4_pl_element import QualifiedE4PLShellElement
from anysolver.elements import ShellElement
from anysolver.fe_core import FEMesh, Material
from anysolver.materials import OrthotropicMaterial
from anysolver.shell_sections import GeneralizedShellSection


OPERATIONS = (
    (0, 1, 2, 3),
    (1, 2, 3, 0),
    (2, 3, 0, 1),
    (3, 0, 1, 2),
    (1, 0, 3, 2),
    (3, 2, 1, 0),
    (0, 3, 2, 1),
    (2, 1, 0, 3),
)

WARPED_GEOMETRIES = (
    np.asarray(((0.0, 0.0, 0.0), (1.0, 0.0, 0.08), (1.0, 1.0, -0.04), (0.0, 1.0, 0.03))),
    np.asarray(((0.0, 0.0, 0.0), (1.4, -0.1, -0.06), (1.1, 0.9, 0.11), (-0.2, 0.7, -0.03))),
    np.asarray(((-0.7, -0.4, 0.12), (0.9, -0.5, -0.08), (0.6, 0.8, 0.16), (-0.8, 0.6, -0.11))),
)


def _mesh(nodes: np.ndarray) -> FEMesh:
    mesh = FEMesh()
    for identifier, coordinates in enumerate(nodes, start=1):
        mesh.add_node(identifier, *coordinates)
    return mesh


def _material() -> Material:
    return Material("warped", 210.0e9, 0.29, density=7850.0)


def _element(identifier: int = 1) -> QualifiedE4PLShellElement:
    return QualifiedE4PLShellElement(
        identifier,
        [1, 2, 3, 4],
        "warped",
        thickness=0.025,
        warped_formulation="varying_frame",
    )


def _relative_residual(left: np.ndarray, right: np.ndarray) -> float:
    scale = max(float(np.linalg.norm(right, ord=np.inf)), 1.0)
    return float(np.linalg.norm(left - right, ord=np.inf) / scale)


@pytest.mark.parametrize("nodes", WARPED_GEOMETRIES)
def test_warped_varying_frame_has_exactly_six_rigid_modes_and_positive_quotient(
    nodes: np.ndarray,
) -> None:
    mesh = _mesh(nodes)
    element = _element()
    components = element.compute_stiffness_components(mesh, _material())
    stiffness = np.asarray(components["total"])
    assert components["warped_direct"] is True
    assert components["legacy_fallback"] is False
    assert components["warped_formulation"] == "varying_frame"
    assert np.linalg.norm(stiffness - stiffness.T, ord=np.inf) <= 2.0e-12 * max(
        np.linalg.norm(stiffness, ord=np.inf), 1.0
    )

    rigid = element._rigid_body_mode_matrix(nodes)
    assert rigid.shape == (24, 6)
    scale = max(float(np.linalg.norm(stiffness, ord=2)), 1.0)
    assert np.linalg.norm(stiffness @ rigid, ord=np.inf) <= 2.0e-12 * scale
    basis, _ = np.linalg.qr(rigid, mode="complete")
    quotient = basis[:, 6:].T @ stiffness @ basis[:, 6:]
    quotient = 0.5 * (quotient + quotient.T)
    eigenvalues = np.linalg.eigvalsh(quotient)
    assert eigenvalues[0] > 1.0e-9 * max(float(eigenvalues[-1]), 1.0)


@pytest.mark.parametrize("nodes", WARPED_GEOMETRIES)
def test_warped_d4_numberings_are_operator_congruent(nodes: np.ndarray) -> None:
    material = _material()
    base = _element().compute_stiffness_matrix(_mesh(nodes), material)
    for operation in OPERATIONS:
        numbered = nodes[list(operation)]
        actual = _element().compute_stiffness_matrix(_mesh(numbered), material)
        dofs = [6 * node + component for node in operation for component in range(6)]
        expected = base[np.ix_(dofs, dofs)]
        assert _relative_residual(actual, expected) < 5.0e-13


@pytest.mark.parametrize("nodes", WARPED_GEOMETRIES)
def test_warped_proper_global_rotation_is_covariant(nodes: np.ndarray) -> None:
    angle = 0.71
    axis = np.asarray((0.3, -0.4, 0.7), dtype=float)
    axis /= np.linalg.norm(axis)
    cross = np.asarray(
        ((0.0, -axis[2], axis[1]), (axis[2], 0.0, -axis[0]), (-axis[1], axis[0], 0.0))
    )
    rotation = (
        np.eye(3) * np.cos(angle)
        + (1.0 - np.cos(angle)) * np.outer(axis, axis)
        + np.sin(angle) * cross
    )
    material = _material()
    base = _element().compute_stiffness_matrix(_mesh(nodes), material)
    transformed_nodes = nodes @ rotation.T + np.asarray((2.3, -1.1, 0.8))
    actual = _element().compute_stiffness_matrix(_mesh(transformed_nodes), material)
    transform = np.zeros((24, 24))
    for node in range(4):
        transform[6 * node : 6 * node + 3, 6 * node : 6 * node + 3] = rotation
        transform[6 * node + 3 : 6 * node + 6, 6 * node + 3 : 6 * node + 6] = rotation
    expected = transform @ base @ transform.T
    assert _relative_residual(actual, expected) < 2.0e-12


@pytest.mark.parametrize("nodes", WARPED_GEOMETRIES)
def test_warped_direct_kernel_retains_established_shell_response(nodes: np.ndarray) -> None:
    mesh = _mesh(nodes)
    material = _material()
    candidate = _element()
    established = ShellElement(2, [1, 2, 3, 4], "warped", thickness=0.025)
    candidate_stiffness = candidate.compute_stiffness_matrix(mesh, material)
    established_stiffness = established.compute_stiffness_matrix(mesh, material)
    assert np.array_equal(candidate_stiffness, established_stiffness)

    displacement = np.linspace(-3.0e-4, 2.0e-4, 24)
    candidate_force, candidate_tangent, _ = candidate.compute_nonlinear_response(
        mesh, material, displacement, tangent=True
    )
    established_force, established_tangent, _ = established.compute_nonlinear_response(
        mesh, material, displacement, tangent=True
    )
    np.testing.assert_array_equal(candidate_force, established_force)
    np.testing.assert_array_equal(candidate_tangent, established_tangent)


def test_warped_direct_kernel_covers_orthotropic_and_generalized_sections() -> None:
    nodes = WARPED_GEOMETRIES[1]
    mesh = _mesh(nodes)
    orthotropic = OrthotropicMaterial(
        name="orthotropic",
        elastic_modulus_1=150.0e9,
        elastic_modulus_2=10.0e9,
        elastic_modulus_3=8.0e9,
        poisson_ratio_12=0.25,
        poisson_ratio_13=0.20,
        poisson_ratio_23=0.30,
        shear_modulus_12=5.0e9,
        shear_modulus_13=4.0e9,
        shear_modulus_23=3.0e9,
        density=1600.0,
    )
    direction = np.asarray((1.0, 0.3, -0.1))
    candidate = QualifiedE4PLShellElement(
        1,
        [1, 2, 3, 4],
        "orthotropic",
        thickness=0.018,
        material_direction=direction,
    )
    established = ShellElement(
        2,
        [1, 2, 3, 4],
        "orthotropic",
        thickness=0.018,
        material_direction=direction,
    )
    np.testing.assert_array_equal(
        candidate.compute_stiffness_matrix(mesh, orthotropic),
        established.compute_stiffness_matrix(mesh, orthotropic),
    )

    section = GeneralizedShellSection(
        A=np.asarray(((120.0, 12.0, 4.0), (12.0, 95.0, -3.0), (4.0, -3.0, 42.0))),
        B=np.asarray(((1.2, 0.1, 0.0), (0.05, -0.8, 0.1), (0.0, 0.05, 0.3))),
        D=np.asarray(((15.0, 1.0, 0.2), (1.0, 11.0, -0.1), (0.2, -0.1, 5.0))),
        As=np.diag((25.0, 20.0)),
        mass_per_area=8.0,
        rotary_inertia_per_area=0.02,
    )
    candidate_section = QualifiedE4PLShellElement(
        3, [1, 2, 3, 4], "warped", shell_section=section
    )
    established_section = ShellElement(
        4, [1, 2, 3, 4], "warped", shell_section=section
    )
    material = _material()
    np.testing.assert_array_equal(
        candidate_section.compute_stiffness_matrix(mesh, material),
        established_section.compute_stiffness_matrix(mesh, material),
    )
    np.testing.assert_array_equal(
        candidate_section.compute_mass_matrix(mesh, material),
        established_section.compute_mass_matrix(mesh, material),
    )
