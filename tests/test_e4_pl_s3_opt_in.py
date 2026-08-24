from __future__ import annotations

import itertools
import json

import numpy as np
import pytest

from anysolver import (
    DEFAULT_Q4_FORMULATION,
    DEFAULT_S3_FORMULATION,
    FEModel,
    ImperfectionField,
    LegacyShellElement,
    QualifiedE4PLS3ShellElement,
    QualifiedE4PLShellElement,
    apply_imperfection,
    create_element,
    create_shell_element,
    shell_element_from_dict,
)
from anysolver.e4_pl_s3_element import (
    BUBBLE_OFFSET_D,
    CAPABILITY_GAPS,
    FORMULATION_ID,
    MITC3_PLUS_SOURCE_BYTES,
    MITC3_PLUS_SOURCE_SHA256,
    PHYSICAL_EXTERNAL_INDICES,
    TRIANGLE_QUADRATURE,
    TYING_POINTS,
    invariant_drilling_scale,
)
from anysolver.fe_core import FEMesh, Material
from anysolver.shell_sections import GeneralizedShellSection


def _mesh(nodes: np.ndarray) -> FEMesh:
    mesh = FEMesh()
    for identifier, coordinate in enumerate(nodes, start=1):
        mesh.add_node(identifier, *coordinate)
    return mesh


def _material() -> Material:
    return Material("steel", 210.0e9, 0.3, density=7850.0)


OWNER_NORMAL = np.asarray((0.0, 0.0, 1.0))


def _rigid_modes(nodes: np.ndarray) -> np.ndarray:
    modes = np.zeros((18, 6), dtype=float)
    centre = np.mean(nodes, axis=0)
    for node, coordinate in enumerate(nodes):
        base = 6 * node
        modes[base : base + 3, :3] = np.eye(3)
        for axis in range(3):
            modes[base : base + 3, 3 + axis] = np.cross(
                np.eye(3)[axis], coordinate - centre
            )
            modes[base + 3 : base + 6, 3 + axis] = np.eye(3)[axis]
    return modes


def _relative(left: np.ndarray, right: np.ndarray) -> float:
    return float(
        np.linalg.norm(left - right, ord=np.inf)
        / max(np.linalg.norm(right, ord=np.inf), 1.0)
    )


def test_published_identity_and_seven_point_rule_are_frozen() -> None:
    assert MITC3_PLUS_SOURCE_BYTES == 1_146_142
    assert MITC3_PLUS_SOURCE_SHA256 == (
        "182F52217277B55E17627B8C41A3A4626ED91ED5378399088E0EA1748AD93EF0"
    )
    assert BUBBLE_OFFSET_D == 1.0e-4
    assert set(TYING_POINTS) == {"A", "B", "C", "D", "E", "F"}
    assert len(TRIANGLE_QUADRATURE) == 7
    assert sum(weight for _r, _s, weight in TRIANGLE_QUADRATURE) == pytest.approx(0.5)


def test_opt_in_dispatch_keeps_all_existing_defaults_unchanged() -> None:
    assert DEFAULT_Q4_FORMULATION == "e4-pl"
    assert DEFAULT_S3_FORMULATION == "legacy-s3"
    assert type(create_shell_element(1, [1, 2, 3], "steel")) is LegacyShellElement
    assert type(create_element("s3", 2, [1, 2, 3], "steel")) is LegacyShellElement
    assert type(create_element("tria3", 3, [1, 2, 3], "steel")) is LegacyShellElement
    assert type(
        create_element(
            "tria3",
            31,
            [1, 2, 3],
            "steel",
            formulation="qualified-s3",
            reference_normal=OWNER_NORMAL,
        )
    ) is QualifiedE4PLS3ShellElement
    assert type(create_shell_element(4, [1, 2, 3, 4], "steel")) is QualifiedE4PLShellElement
    assert type(
        create_shell_element(
            5,
            [1, 2, 3],
            "steel",
            formulation="e4-pl-s3",
            reference_normal=OWNER_NORMAL,
        )
    ) is QualifiedE4PLS3ShellElement
    assert type(
        create_element(
            "qualified-s3", 6, [1, 2, 3], "steel", reference_normal=OWNER_NORMAL
        )
    ) is QualifiedE4PLS3ShellElement
    with pytest.raises(ValueError, match="only for three-node"):
        create_element("legacy-s3", 7, [1, 2, 3, 4], "steel")
    with pytest.raises(ValueError, match="only for three-node"):
        create_element("e4-pl-s3", 8, [1, 2, 3, 4], "steel")


def test_local_condensation_pl_completion_and_rigid_kernel() -> None:
    nodes = np.asarray(
        ((0.1, 0.2, 0.3), (1.2, 0.1, 0.5), (0.3, 1.0, 0.4)), dtype=float
    )
    mesh = _mesh(nodes)
    element = QualifiedE4PLS3ShellElement(
        1, [1, 2, 3], "steel", thickness=0.2, reference_normal=np.cross(
            nodes[1] - nodes[0], nodes[2] - nodes[0]
        )
    )
    components = element.compute_stiffness_components(mesh, _material())
    assert components["ranks"] == {
        "uncondensed_physical_rank": 11,
        "bubble_rank": 2,
        "condensed_physical_rank": 9,
        "embedded_physical_rank": 9,
        "pl_rank": 3,
        "total_rank": 12,
        "saddle_rank": 17,
        "saddle_inertia": (14, 3, 6),
    }
    assert np.linalg.eigvalsh(components["bubble_block"])[0] > 0.0
    assert np.array_equal(components["hourglass"], np.zeros((18, 18)))
    assert np.array_equal(components["numerical"], components["pl"])
    stiffness = components["total"]
    rigid = _rigid_modes(nodes)
    scale = max(np.linalg.norm(stiffness, ord=np.inf), 1.0)
    assert np.linalg.norm(stiffness @ rigid, ord=np.inf) / scale < 2.0e-14
    assert np.linalg.norm(components["pl"] @ rigid, ord=np.inf) / scale < 2.0e-14

    constraint = components["pl_constraint"]
    gram = components["pl_multiplier_gram"]
    expected = components["k_d"] * constraint.T @ gram @ constraint
    transform = element._local_dof_transform(components["frame"])
    assert _relative(components["pl"], transform.T @ expected @ transform) < 2.0e-15


def test_structural_rank_certificate_is_unit_and_thickness_scaled() -> None:
    material = _material()
    expected = {
        "uncondensed_physical_rank": 11,
        "bubble_rank": 2,
        "condensed_physical_rank": 9,
        "embedded_physical_rank": 9,
        "pl_rank": 3,
        "total_rank": 12,
        "saddle_rank": 17,
        "saddle_inertia": (14, 3, 6),
    }
    shape = np.asarray(((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.2, 0.9, 0.0)))
    for length in (1.0e-6, 1.0, 1.0e6):
        element = QualifiedE4PLS3ShellElement(
            1,
            [1, 2, 3],
            "steel",
            thickness=length * 1.0e-6,
            reference_normal=OWNER_NORMAL,
        )
        components = element.compute_stiffness_components(_mesh(length * shape), material)
        assert components["rank_certificate"] == "DIMENSIONLESS_KINEMATIC_SUBSPACE_V1"
        assert components["ranks"] == expected


def test_all_d3_numberings_are_operator_covariant() -> None:
    nodes = np.asarray(
        ((0.1, 0.2, 0.3), (1.2, 0.1, 0.5), (0.3, 1.0, 0.4)), dtype=float
    )
    material = _material()

    def stiffness(numbered: np.ndarray) -> np.ndarray:
        element = QualifiedE4PLS3ShellElement(
            1, [1, 2, 3], "steel", thickness=0.2, reference_normal=np.cross(
                nodes[1] - nodes[0], nodes[2] - nodes[0]
            )
        )
        return element._compute_stiffness_components(
            _mesh(numbered), material, enforce_positive_winding=False
        )["total"]

    baseline = stiffness(nodes)
    for permutation in itertools.permutations(range(3)):
        actual = stiffness(nodes[list(permutation)])
        dofs = [6 * node + component for node in permutation for component in range(6)]
        expected = baseline[np.ix_(dofs, dofs)]
        assert _relative(actual, expected) < 2.0e-14, permutation


def test_all_d3_numberings_transport_uncondensed_bubble_pl_and_saddle_blocks() -> None:
    nodes = np.asarray(
        ((0.1, 0.2, 0.3), (1.2, 0.1, 0.5), (0.3, 1.0, 0.4)), dtype=float
    )
    owner = np.cross(nodes[1] - nodes[0], nodes[2] - nodes[0])
    material = _material()

    def components(numbered: np.ndarray):
        element = QualifiedE4PLS3ShellElement(
            1,
            [1, 2, 3],
            "steel",
            thickness=0.2,
            reference_normal=owner,
        )
        made = element._compute_stiffness_components(
            _mesh(numbered), material, enforce_positive_winding=False
        )
        return element, made

    baseline_element, baseline = components(nodes)
    baseline_transform = baseline_element._local_dof_transform(baseline["frame"])
    physical = PHYSICAL_EXTERNAL_INDICES
    for permutation in itertools.permutations(range(3)):
        numbered_element, numbered = components(nodes[list(permutation)])
        numbered_transform = numbered_element._local_dof_transform(numbered["frame"])
        node_map = np.zeros((18, 18), dtype=float)
        multiplier_map = np.zeros((3, 3), dtype=float)
        for new_node, old_node in enumerate(permutation):
            node_map[6 * new_node : 6 * new_node + 6, 6 * old_node : 6 * old_node + 6] = np.eye(6)
            multiplier_map[new_node, old_node] = 1.0
        local_external_map = numbered_transform @ node_map @ baseline_transform.T
        physical_map = local_external_map[np.ix_(physical, physical)]
        bubble_map = numbered["frame"][:, :2].T @ baseline["frame"][:, :2]

        transport_17 = np.zeros((17, 17), dtype=float)
        transport_17[:15, :15] = physical_map
        transport_17[15:, 15:] = bubble_map
        assert _relative(
            transport_17.T @ numbered["uncondensed_physical"] @ transport_17,
            baseline["uncondensed_physical"],
        ) < 2.0e-14
        assert np.linalg.norm(
            numbered["bubble_map"] @ physical_map
            - bubble_map @ baseline["bubble_map"],
            ord=np.inf,
        ) < 1.0e-13
        assert np.linalg.norm(
            numbered["pl_constraint"] @ local_external_map
            - multiplier_map @ baseline["pl_constraint"],
            ord=np.inf,
        ) < 2.0e-14

        transport_20 = np.zeros((20, 20), dtype=float)
        transport_20[:18, :18] = local_external_map
        transport_20[18:, 18:] = bubble_map
        transport_23 = np.zeros((23, 23), dtype=float)
        transport_23[:20, :20] = transport_20
        transport_23[20:, 20:] = multiplier_map
        assert _relative(
            transport_23.T @ numbered["full_saddle"] @ transport_23,
            baseline["full_saddle"],
        ) < 2.0e-14


def test_b_coupled_section_requires_and_uses_authoritative_normal() -> None:
    nodes = np.asarray(
        ((0.1, 0.2, 0.3), (1.2, 0.1, 0.5), (0.3, 1.0, 0.4)), dtype=float
    )
    normal = np.cross(nodes[1] - nodes[0], nodes[2] - nodes[0])
    normal /= np.linalg.norm(normal)
    section = GeneralizedShellSection(
        A=np.asarray(((120.0, 12.0, 4.0), (12.0, 95.0, -3.0), (4.0, -3.0, 42.0))),
        B=np.asarray(((1.2, 0.1, 0.0), (0.1, -0.8, 0.1), (0.0, 0.1, 0.3))),
        D=np.asarray(((15.0, 1.0, 0.2), (1.0, 11.0, -0.1), (0.2, -0.1, 5.0))),
        As=np.asarray(((25.0, 2.0), (2.0, 20.0))),
    )
    with pytest.raises(ValueError, match="authoritative reference_normal"):
        QualifiedE4PLS3ShellElement(1, [1, 2, 3], "steel", shell_section=section)

    def stiffness(numbered: np.ndarray) -> np.ndarray:
        element = QualifiedE4PLS3ShellElement(
            1,
            [1, 2, 3],
            "steel",
            shell_section=section,
            material_direction=np.asarray((1.0, 0.2, 0.1)),
            reference_normal=normal,
        )
        return element._compute_stiffness_components(
            _mesh(numbered), _material(), enforce_positive_winding=False
        )["total"]

    baseline = stiffness(nodes)
    for permutation in itertools.permutations(range(3)):
        actual = stiffness(nodes[list(permutation)])
        dofs = [6 * node + component for node in permutation for component in range(6)]
        assert _relative(actual, baseline[np.ix_(dofs, dofs)]) < 2.0e-14


def test_invariant_drilling_scale_matches_isotropy_and_rotated_section() -> None:
    young = 210.0
    poisson = 0.3
    thickness = 0.4
    q11 = young / (1.0 - poisson * poisson)
    q66 = young / (2.0 * (1.0 + poisson))
    membrane = thickness * np.asarray(
        ((q11, poisson * q11, 0.0), (poisson * q11, q11, 0.0), (0.0, 0.0, q66))
    )
    assert invariant_drilling_scale(membrane) == pytest.approx(thickness * q66)

    section = GeneralizedShellSection(
        A=np.asarray(((120.0, 12.0, 4.0), (12.0, 95.0, -3.0), (4.0, -3.0, 42.0))),
        B=np.zeros((3, 3)),
        D=np.diag((15.0, 11.0, 5.0)),
        As=np.diag((25.0, 20.0)),
    )
    baseline = invariant_drilling_scale(section.A)
    for angle in (0.1, 0.37, 1.1):
        assert invariant_drilling_scale(section.rotated(angle).A) == pytest.approx(
            baseline, rel=2.0e-14
        )


def test_native_linear_recovery_excludes_pl_fields() -> None:
    nodes = np.asarray(((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.2, 0.9, 0.0)))
    mesh = _mesh(nodes)
    element = QualifiedE4PLS3ShellElement(
        1, [1, 2, 3], "steel", thickness=0.1, reference_normal=OWNER_NORMAL
    )
    displacement = np.linspace(-1.0e-4, 2.0e-4, 18)
    recovery = element.compute_stresses(mesh, displacement, _material())
    assert recovery["recovery_scope"] == "qualified_s3_local_physical_only"
    assert recovery["numerical_fields_excluded"] is True
    assert recovery["membrane_strain"].shape == (7, 3)
    assert recovery["curvature"].shape == (7, 3)
    assert recovery["transverse_shear_strain"].shape == (7, 2)
    top = np.column_stack(
        (
            recovery["membrane_xx"] + recovery["bending_xx"],
            recovery["membrane_yy"] + recovery["bending_yy"],
            recovery["membrane_xy"] + recovery["bending_xy"],
        )
    )
    bottom = np.column_stack(
        (
            recovery["membrane_xx"] - recovery["bending_xx"],
            recovery["membrane_yy"] - recovery["bending_yy"],
            recovery["membrane_xy"] - recovery["bending_xy"],
        )
    )
    shear_squared = recovery["shear_xz"] ** 2 + recovery["shear_yz"] ** 2
    expected_top = np.sqrt(
        top[:, 0] ** 2
        - top[:, 0] * top[:, 1]
        + top[:, 1] ** 2
        + 3.0 * (top[:, 2] ** 2 + shear_squared)
    )
    expected_bottom = np.sqrt(
        bottom[:, 0] ** 2
        - bottom[:, 0] * bottom[:, 1]
        + bottom[:, 1] ** 2
        + 3.0 * (bottom[:, 2] ** 2 + shear_squared)
    )
    assert np.allclose(
        recovery["equivalent_stress"], np.maximum(expected_top, expected_bottom)
    )
    numerical = element.numerical_internal_force(displacement)
    assert np.array_equal(numerical["hourglass"], np.zeros(18))
    assert np.array_equal(numerical["numerical"], numerical["pl"])
    with pytest.raises(NotImplementedError, match="global recovery"):
        element.compute_stresses(mesh, displacement, _material(), return_global=True)


def test_serialization_is_identity_bound_and_legacy_missing_id_stays_legacy() -> None:
    original = QualifiedE4PLS3ShellElement(
        7,
        [1, 2, 3],
        "steel",
        thickness=0.07,
        material_direction=np.asarray((1.0, 0.2, 0.0)),
        material_angle_deg=11.0,
        reference_normal=np.asarray((0.0, 0.0, 1.0)),
    )
    payload = json.loads(json.dumps(original.to_dict()))
    assert payload["formulation_id"] == FORMULATION_ID
    rebuilt = shell_element_from_dict(payload)
    assert type(rebuilt) is QualifiedE4PLS3ShellElement
    assert rebuilt.to_dict() == payload

    historical = dict(payload)
    for key in (
        "formulation_id",
        "formulation_schema",
        "bubble_convention",
        "quadrature_id",
        "dynamic_reduction_policy",
        "algebraic_coordinate_policy",
        "mass_moment_id",
        "state_layout_id",
    ):
        historical.pop(key)
    historical["type"] = "ShellElement"
    assert type(shell_element_from_dict(historical)) is LegacyShellElement

    mutated = dict(payload, formulation_id="E4_PL_QUALIFIED_S3_UNKNOWN")
    with pytest.raises(ValueError, match="unknown serialized"):
        shell_element_from_dict(mutated)
    missing = dict(payload)
    missing.pop("formulation_id")
    with pytest.raises(ValueError, match="missing formulation_id"):
        shell_element_from_dict(missing)
    missing_mass_identity = dict(payload)
    missing_mass_identity.pop("mass_moment_id")
    with pytest.raises(ValueError, match="mass moment identity"):
        shell_element_from_dict(missing_mass_identity)
    mutated_descriptor = dict(payload, algebraic_coordinate_policy="INVENTED_DRILL_MASS")
    with pytest.raises(ValueError, match="algebraic coordinate policy"):
        shell_element_from_dict(mutated_descriptor)
    mutated_mass = dict(payload, mass_moment_id="UNDERINTEGRATED_DEGREE5")
    with pytest.raises(ValueError, match="mass moment identity"):
        shell_element_from_dict(mutated_mass)


def test_legacy_controls_quality_and_unqualified_capabilities_fail_closed() -> None:
    with pytest.raises(ValueError, match="physical material_direction"):
        QualifiedE4PLS3ShellElement(
            1, [1, 2, 3], "steel", material_angle_deg=15.0
        )
    with pytest.raises(ValueError, match="no user drilling coefficient"):
        QualifiedE4PLS3ShellElement(
            1, [1, 2, 3], "steel", drilling_stabilization=1.0e-3
        )
    with pytest.raises(ValueError, match="no hourglass coefficient"):
        QualifiedE4PLS3ShellElement(
            1, [1, 2, 3], "steel", hourglass_stabilization=1.0e-8
        )
    with pytest.raises(ValueError, match="seven-point"):
        QualifiedE4PLS3ShellElement(
            1, [1, 2, 3], "steel", reduced_integration=True
        )

    bad_nodes = np.asarray(((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.99, 0.01, 0.0)))
    bad = QualifiedE4PLS3ShellElement(
        1, [1, 2, 3], "steel", reference_normal=OWNER_NORMAL
    )
    with pytest.raises(ValueError, match="quality admission failed"):
        bad.compute_stiffness_matrix(_mesh(bad_nodes), _material())

    reversed_nodes = np.asarray(
        ((0.0, 0.0, 0.0), (0.2, 0.9, 0.0), (1.0, 0.0, 0.0))
    )
    with pytest.raises(ValueError, match="connectivity winding opposes"):
        QualifiedE4PLS3ShellElement(
            2, [1, 2, 3], "steel", reference_normal=OWNER_NORMAL
        ).compute_stiffness_matrix(_mesh(reversed_nodes), _material())

    nodes = np.asarray(((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.2, 0.9, 0.0)))
    element = QualifiedE4PLS3ShellElement(
        1, [1, 2, 3], "steel", reference_normal=OWNER_NORMAL
    )
    assert element.capability_gaps == CAPABILITY_GAPS
    assert all(
        element.capability_matrix()[name] == "PARITY_GAP"
        for name in CAPABILITY_GAPS
    )
    mass = element.compute_mass_matrix(_mesh(nodes), _material())
    assert mass.shape == (18, 18)
    assert np.all(np.isfinite(mass))
    with pytest.raises(NotImplementedError, match="geometric_stiffness"):
        element.compute_geometric_stiffness_matrix(_mesh(nodes), _material())
    with pytest.raises(NotImplementedError, match="nonlinear_geometry"):
        element.compute_nonlinear_response(_mesh(nodes), _material(), np.zeros(18))


def test_direct_solver_imperfection_cannot_bypass_initial_field_parity_gap() -> None:
    model = FEModel("qualified-s3-imperfection")
    for node_id, coordinate in enumerate(
        ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.2, 0.9, 0.0)), start=1
    ):
        model.add_node(node_id, *coordinate)
    model.add_element(
        1,
        QualifiedE4PLS3ShellElement(
            1, [1, 2, 3], "default", reference_normal=OWNER_NORMAL
        ),
    )
    before = model.mesh.get_node(3).coords().copy()

    with pytest.raises(NotImplementedError, match="initial_fields PARITY_GAP"):
        apply_imperfection(
            model,
            ImperfectionField({3: (0.0, 0.0, 0.1)}),
            copy_model=False,
        )

    np.testing.assert_array_equal(model.mesh.get_node(3).coords(), before)
