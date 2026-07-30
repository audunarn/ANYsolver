"""Qualification tests for pre-integrated generalized shell sections."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pytest

from anysolver import (
    FEModel,
    ShellElement,
    assemble_mass_matrix,
    assemble_stiffness_matrix,
    create_element,
)
from anysolver.shell_sections import (
    GeneralizedShellSection,
    GeneralizedShellSectionProtocol,
    coerce_generalized_shell_section,
)


def _isotropic_section(
    *,
    thickness: float = 0.02,
    elastic_modulus: float = 70.0e9,
    poisson_ratio: float = 0.25,
    **kwargs,
) -> GeneralizedShellSection:
    shear_modulus = elastic_modulus / (2.0 * (1.0 + poisson_ratio))
    Q = elastic_modulus / (1.0 - poisson_ratio**2) * np.array(
        [
            [1.0, poisson_ratio, 0.0],
            [poisson_ratio, 1.0, 0.0],
            [0.0, 0.0, (1.0 - poisson_ratio) / 2.0],
        ],
        dtype=float,
    )
    return GeneralizedShellSection(
        A=thickness * Q,
        B=np.zeros((3, 3)),
        D=thickness**3 / 12.0 * Q,
        As=(5.0 / 6.0) * thickness * shear_modulus * np.eye(2),
        **kwargs,
    )


def _topology_coordinates(node_count: int) -> list[tuple[float, float, float]]:
    if node_count == 3:
        return [(0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (0.0, 1.0, 0.0)]
    if node_count == 4:
        return [
            (0.0, 0.0, 0.0),
            (2.0, 0.0, 0.0),
            (2.0, 1.0, 0.0),
            (0.0, 1.0, 0.0),
        ]
    if node_count == 6:
        return [
            (0.0, 0.0, 0.0),
            (2.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (1.0, 0.0, 0.0),
            (1.0, 0.5, 0.0),
            (0.0, 0.5, 0.0),
        ]
    if node_count == 8:
        return [
            (0.0, 0.0, 0.0),
            (2.0, 0.0, 0.0),
            (2.0, 1.0, 0.0),
            (0.0, 1.0, 0.0),
            (1.0, 0.0, 0.0),
            (2.0, 0.5, 0.0),
            (1.0, 1.0, 0.0),
            (0.0, 0.5, 0.0),
        ]
    raise AssertionError(node_count)


def _model_with_shell(
    node_count: int = 4,
    *,
    section: GeneralizedShellSection | None = None,
    thickness: float = 0.02,
    material_angle_deg: float = 0.0,
) -> tuple[FEModel, ShellElement]:
    model = FEModel("generalized_shell")
    model.add_material("aluminium", 70.0e9, 0.25, density=2700.0)
    coordinates = _topology_coordinates(node_count)
    for node_id, coordinate in enumerate(coordinates, start=1):
        model.add_node(node_id, *coordinate)
    element = ShellElement(
        1,
        list(range(1, node_count + 1)),
        "aluminium",
        thickness=thickness,
        material_angle_deg=material_angle_deg,
        shell_section=section,
    )
    model.add_element(1, element)
    return model, element


def test_generalized_shell_section_validates_and_accepts_structural_objects() -> None:
    section = _isotropic_section(name="laminate")
    assert section.name == "laminate"
    assert section.ABD.shape == (6, 6)
    assert not section.A.flags.writeable

    @dataclass
    class ExternalSection:
        A: np.ndarray
        B: np.ndarray
        D: np.ndarray
        As: np.ndarray
        name: str = "external"

    external = ExternalSection(section.A, section.B, section.D, section.As)
    assert isinstance(external, GeneralizedShellSectionProtocol)
    copied = coerce_generalized_shell_section(external)
    assert isinstance(copied, GeneralizedShellSection)
    assert copied.name == "external"
    np.testing.assert_allclose(copied.ABD, section.ABD)

    with pytest.raises(ValueError, match="A must be symmetric"):
        GeneralizedShellSection(
            A=np.array([[1.0, 0.2, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]),
            B=np.zeros((3, 3)),
            D=np.eye(3),
            As=np.eye(2),
        )
    with pytest.raises(ValueError, match="ABD matrix must be positive definite"):
        GeneralizedShellSection(
            A=np.eye(3),
            B=2.0 * np.eye(3),
            D=np.eye(3),
            As=np.eye(2),
        )
    with pytest.raises(ValueError, match="As matrix must be positive definite"):
        GeneralizedShellSection(
            A=np.eye(3),
            B=np.zeros((3, 3)),
            D=np.eye(3),
            As=np.diag([1.0, 0.0]),
        )


def test_generalized_shell_section_allows_energy_symmetric_nonsymmetric_B() -> None:
    B = np.array(
        [
            [0.1, 0.03, 0.0],
            [0.0, -0.05, 0.02],
            [0.01, 0.0, 0.04],
        ]
    )
    section = GeneralizedShellSection(
        A=10.0 * np.eye(3),
        B=B,
        D=2.0 * np.eye(3),
        As=np.eye(2),
    )
    np.testing.assert_allclose(section.ABD, section.ABD.T)
    assert np.min(np.linalg.eigvalsh(section.ABD)) > 0.0


@pytest.mark.parametrize("node_count", [3, 4, 6, 8])
def test_isotropic_generalized_section_matches_legacy_shell_stiffness(
    node_count: int,
) -> None:
    thickness = 0.02
    model, legacy = _model_with_shell(node_count, thickness=thickness)
    section_element = ShellElement(
        2,
        legacy.node_ids,
        "aluminium",
        thickness=thickness,
        shell_section=_isotropic_section(thickness=thickness),
    )
    material = model.get_material("aluminium")

    legacy_stiffness = legacy.compute_stiffness_matrix(model.mesh, material)
    section_stiffness = section_element.compute_stiffness_matrix(model.mesh, material)
    np.testing.assert_allclose(
        section_stiffness,
        legacy_stiffness,
        rtol=2.0e-12,
        atol=2.0e-5,
    )


def test_generalized_shell_section_recovers_exact_strains_and_resultants() -> None:
    A = np.array(
        [[120.0, 18.0, 7.0], [18.0, 90.0, -4.0], [7.0, -4.0, 35.0]]
    )
    B = np.array(
        [[1.5, 0.2, -0.1], [0.1, -0.8, 0.15], [0.05, -0.04, 0.4]]
    )
    D = np.array(
        [[12.0, 1.0, 0.3], [1.0, 9.0, -0.2], [0.3, -0.2, 4.0]]
    )
    section = GeneralizedShellSection(A=A, B=B, D=D, As=np.diag([20.0, 15.0]))
    model, element = _model_with_shell(section=section)
    material = model.get_material("aluminium")

    strain = np.array([1.2e-3, -0.4e-3, 0.7e-3])
    curvature = np.array([1.1e-2, -0.3e-2, 0.5e-2])
    displacement = np.zeros(element.total_dofs)
    for local_index, coordinate in enumerate(element.get_node_coordinates(model.mesh)):
        x, y, _ = coordinate
        base = 6 * local_index
        displacement[base + 0] = strain[0] * x
        displacement[base + 1] = strain[1] * y + strain[2] * x
        displacement[base + 3] = -curvature[1] * y - 0.5 * curvature[2] * x
        displacement[base + 4] = curvature[0] * x + 0.5 * curvature[2] * y

    recovered = element.compute_stresses(model.mesh, displacement, material)

    expected_force = A @ strain + B @ curvature
    expected_moment = B.T @ strain + D @ curvature
    np.testing.assert_allclose(
        recovered["membrane_strain"],
        np.broadcast_to(strain, recovered["membrane_strain"].shape),
        atol=1.0e-14,
    )
    np.testing.assert_allclose(
        recovered["curvature"],
        np.broadcast_to(curvature, recovered["curvature"].shape),
        atol=1.0e-14,
    )
    np.testing.assert_allclose(
        recovered["membrane_resultants"],
        np.broadcast_to(expected_force, recovered["membrane_resultants"].shape),
        atol=1.0e-13,
    )
    np.testing.assert_allclose(
        recovered["bending_resultants"],
        np.broadcast_to(expected_moment, recovered["bending_resultants"].shape),
        atol=1.0e-13,
    )
    assert recovered["generalized_stress_scope"] == "section_resultants_only"
    assert "von_mises" not in recovered
    assert "global_xx_top" not in recovered


def test_generalized_shell_section_rotation_uses_shell_material_angle() -> None:
    section = GeneralizedShellSection(
        A=np.diag([200.0, 50.0, 25.0]),
        B=np.zeros((3, 3)),
        D=np.diag([20.0, 5.0, 2.5]),
        As=np.diag([30.0, 10.0]),
    )
    model, element = _model_with_shell(section=section, material_angle_deg=90.0)
    material = model.get_material("aluminium")
    strain_x = 2.0e-3
    displacement = np.zeros(element.total_dofs)
    for local_index, coordinate in enumerate(element.get_node_coordinates(model.mesh)):
        displacement[6 * local_index] = strain_x * coordinate[0]

    recovered = element.compute_stresses(model.mesh, displacement, material)
    expected = section.rotated(np.pi / 2.0).A @ np.array([strain_x, 0.0, 0.0])
    np.testing.assert_allclose(
        recovered["membrane_resultants"],
        np.broadcast_to(expected, recovered["membrane_resultants"].shape),
        atol=1.0e-13,
    )
    np.testing.assert_allclose(
        recovered["membrane_resultants"][:, 0],
        50.0 * strain_x,
        atol=1.0e-13,
    )


def test_generalized_shell_section_mass_metadata_overrides_homogeneous_fallback() -> None:
    section = _isotropic_section(
        mass_per_area=17.0,
        rotary_inertia_per_area=0.08,
    )
    model, element = _model_with_shell(section=section)
    mass = element.compute_mass_matrix(model.mesh, model.get_material("aluminium"))
    assembled_mass, _ = assemble_mass_matrix(model)
    np.testing.assert_allclose(assembled_mass.toarray(), mass, rtol=1.0e-12, atol=1.0e-14)
    area = 2.0

    rigid_translation = np.zeros(element.total_dofs)
    rigid_translation[0::6] = 1.0
    rigid_rotation = np.zeros(element.total_dofs)
    rigid_rotation[3::6] = 1.0
    assert float(rigid_translation @ mass @ rigid_translation) == pytest.approx(
        17.0 * area,
        rel=1.0e-12,
    )
    assert float(rigid_rotation @ mass @ rigid_rotation) == pytest.approx(
        0.08 * area,
        rel=1.0e-12,
    )


def test_generalized_shell_section_routes_assembly_through_general_path() -> None:
    model, element = _model_with_shell(section=_isotropic_section())
    expected = element.compute_stiffness_matrix(
        model.mesh,
        model.get_material(element.material_name),
    )
    assembled, info = assemble_stiffness_matrix(model)

    np.testing.assert_allclose(assembled.toarray(), expected, rtol=1.0e-12, atol=1.0e-5)
    assert info["diagnostics"]["generalized_shell_section_fallback"] == {
        "path": "general_element",
        "reason": "preintegrated_generalized_shell_section",
        "element_ids": [1],
    }


def test_generalized_shell_section_nonlinear_tangent_matches_difference() -> None:
    section = GeneralizedShellSection(
        A=np.array([[110.0, 12.0, 3.0], [12.0, 85.0, -2.0], [3.0, -2.0, 30.0]]),
        B=np.array([[0.9, 0.2, 0.0], [0.0, -0.5, 0.1], [0.05, 0.0, 0.3]]),
        D=np.array([[10.0, 0.8, 0.2], [0.8, 8.0, -0.1], [0.2, -0.1, 3.0]]),
        As=np.diag([18.0, 14.0]),
    )
    model, element = _model_with_shell(section=section)
    material = model.get_material("aluminium")
    displacement = np.linspace(-2.0e-3, 2.0e-3, element.total_dofs)
    force, tangent, _state = element.compute_nonlinear_response(
        model.mesh,
        material,
        displacement,
        tangent=True,
    )
    assert tangent is not None
    assert np.all(np.isfinite(force))
    np.testing.assert_allclose(tangent, tangent.T, rtol=1.0e-10, atol=1.0e-10)

    direction = np.cos(np.arange(element.total_dofs, dtype=float))
    step = 1.0e-7
    force_plus, _, _ = element.compute_nonlinear_response(
        model.mesh,
        material,
        displacement + step * direction,
        tangent=False,
    )
    force_minus, _, _ = element.compute_nonlinear_response(
        model.mesh,
        material,
        displacement - step * direction,
        tangent=False,
    )
    numerical = (force_plus - force_minus) / (2.0 * step)
    np.testing.assert_allclose(tangent @ direction, numerical, rtol=2.0e-6, atol=2.0e-6)


def test_shell_element_serialization_round_trips_inline_section() -> None:
    section = _isotropic_section(name="serialized", mass_per_area=5.0)
    element = ShellElement(7, [1, 2, 3, 4], "aluminium", shell_section=section)
    payload = element.to_dict()
    payload.pop("type")
    rebuilt = create_element(
        "shell",
        payload.pop("element_id"),
        payload.pop("node_ids"),
        payload.pop("material_name"),
        **payload,
    )
    assert isinstance(rebuilt.shell_section, GeneralizedShellSection)
    assert rebuilt.shell_section.name == "serialized"
    assert rebuilt.shell_section.mass_per_area == pytest.approx(5.0)
    np.testing.assert_allclose(rebuilt.shell_section.ABD, section.ABD)
