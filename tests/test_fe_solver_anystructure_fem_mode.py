import numpy as np
import pytest

from anysolver import (
    AnyStructureFEMConfig,
    build_fe_model_from_generated_geometry,
    build_symmetric_load_case,
    idealize_generated_geometry_members,
    load_case_resultant,
    recover_prestress_from_static_result,
    run_anystructure_fem_mode,
)
from anysolver.assembly import solve_linear
from anysolver.elements import BeamElement, ShellElement
from anysolver.matrix_assembly import assemble_geometric_stiffness_matrix


class _Part:
    span = 1.0
    spacing = 1.0
    t = 0.01
    sigma_x1 = 5.0
    sigma_x2 = 5.0
    sigma_y1 = 0.0
    sigma_y2 = 0.0
    tau_xy = 0.0
    pressure = 0.0


class _Calc:
    Plate = _Part()
    Stiffener = None


def _square_shell_geometry():
    return {
        "nodes": [
            {"id": 1, "coords": [0.0, 0.0, 0.0]},
            {"id": 2, "coords": [2.0, 0.0, 0.0]},
            {"id": 3, "coords": [2.0, 1.0, 0.0]},
            {"id": 4, "coords": [0.0, 1.0, 0.0]},
        ],
        "shells": [{"id": 1, "node_ids": [1, 2, 3, 4], "thickness": 0.02}],
    }


def _cylinder_geometry(num_circ=8):
    radius = 1.0
    height = 1.0
    nodes = []
    for iz, z in enumerate([0.0, height]):
        for itheta in range(num_circ):
            theta = 2.0 * np.pi * itheta / num_circ
            nodes.append({"id": iz * num_circ + itheta + 1, "coords": [radius * np.cos(theta), radius * np.sin(theta), z]})
    shells = []
    for itheta in range(num_circ):
        next_theta = (itheta + 1) % num_circ
        shells.append(
            {
                "id": itheta + 1,
                "node_ids": [itheta + 1, next_theta + 1, num_circ + next_theta + 1, num_circ + itheta + 1],
                "thickness": 0.02,
            }
        )
    return {
        "nodes": nodes,
        "shells": shells,
        "supports": [
            {
                "name": "bottom_fixed",
                "node_ids": list(range(1, num_circ + 1)),
                "dof_constraints": {"ux": 0.0, "uy": 0.0, "uz": 0.0, "rx": 0.0, "ry": 0.0, "rz": 0.0},
            }
        ],
    }


def test_generated_shell_geometry_converts_to_fe_model():
    model = build_fe_model_from_generated_geometry(_square_shell_geometry())

    assert model.mesh.num_nodes == 4
    assert model.mesh.num_elements == 1
    assert isinstance(model.mesh.get_element(1), ShellElement)


def test_generated_beam_shell_coupling_metadata_is_preserved():
    geometry = _square_shell_geometry()
    geometry["nodes"].extend(
        [
            {"id": 100, "coords": [0.5, 0.5, 0.2]},
            {"id": 101, "coords": [1.5, 0.5, 0.2]},
        ]
    )
    geometry["beams"] = [{"id": 20, "node_ids": [100, 101], "cross_section": {"area": 0.01, "Iy": 1e-6, "Iz": 1e-6, "J": 1e-6}}]
    geometry["couplings"] = [
        {"id": 30, "beam_node_id": 100, "shell_node_ids": [1, 2, 3, 4], "shape_weights": [0.25, 0.25, 0.25, 0.25], "eccentricity": [0.0, 0.0, 0.2]}
    ]

    model = build_fe_model_from_generated_geometry(geometry)
    coupling = model.mesh.get_element(30)

    assert model.mesh.num_elements == 3
    assert coupling is not None
    assert len(coupling.get_mpc_constraints(model.mesh)) == 6


def test_generated_stiffeners_and_girders_are_created_as_beams():
    geometry = _square_shell_geometry()
    geometry["nodes"].extend(
        [
            {"id": 100, "coords": [0.0, 0.5, 0.2]},
            {"id": 101, "coords": [2.0, 0.5, 0.2]},
            {"id": 200, "coords": [1.0, 0.0, 0.3]},
            {"id": 201, "coords": [1.0, 1.0, 0.3]},
        ]
    )
    section = {"area": 0.01, "Iy": 1e-6, "Iz": 1e-6, "J": 1e-6}
    geometry["stiffeners"] = [{"id": 20, "node_ids": [100, 101], "cross_section": section}]
    geometry["girders"] = [{"id": 21, "node_ids": [200, 201], "cross_section": section}]

    model = build_fe_model_from_generated_geometry(geometry)
    beams = [element for element in model.mesh.elements.values() if isinstance(element, BeamElement)]

    assert len(beams) == 2
    assert {getattr(beam, "structural_role", None) for beam in beams} == {"stiffener", "girder"}


def test_generated_beam_collections_are_additive_not_first_alias_only():
    geometry = _square_shell_geometry()
    geometry["nodes"].extend(
        [
            {"id": 100, "coords": [0.0, 0.25, 0.2]},
            {"id": 101, "coords": [2.0, 0.25, 0.2]},
            {"id": 110, "coords": [0.0, 0.75, 0.2]},
            {"id": 111, "coords": [2.0, 0.75, 0.2]},
        ]
    )
    section = {"area": 0.01, "Iy": 1e-6, "Iz": 1e-6, "J": 1e-6}
    geometry["beams"] = [{"id": 20, "node_ids": [100, 101], "cross_section": section}]
    geometry["stiffeners"] = [{"id": 21, "node_ids": [110, 111], "cross_section": section}]

    model = build_fe_model_from_generated_geometry(geometry)
    beam_ids = {element.element_id for element in model.mesh.elements.values() if isinstance(element, BeamElement)}

    assert beam_ids == {20, 21}


def _square_shell_with_tagged_member_plate(role="stiffener_web"):
    geometry = _square_shell_geometry()
    geometry["nodes"].extend(
        [
            {"id": 100, "coords": [0.0, 0.5, 0.0]},
            {"id": 101, "coords": [2.0, 0.5, 0.0]},
            {"id": 102, "coords": [2.0, 0.5, 0.2]},
            {"id": 103, "coords": [0.0, 0.5, 0.2]},
        ]
    )
    geometry["plates"] = [{"id": 2, "node_ids": [100, 101, 102, 103], "thickness": 0.01, "role": role, "member_id": "S1"}]
    return geometry


@pytest.mark.parametrize(("tag", "expected_role"), [("stiffener_web", "stiffener"), ("girder_web", "girder")])
def test_tagged_member_plates_are_auto_idealized_as_beams_by_default(tag, expected_role):
    idealized = idealize_generated_geometry_members(_square_shell_with_tagged_member_plate(tag))

    assert len(idealized["shells"]) == 1
    assert len(idealized["beams"]) == 1
    assert idealized["beams"][0]["role"] == expected_role
    np.testing.assert_allclose(idealized["beams"][0]["cross_section"]["area"], 0.002)

    model = build_fe_model_from_generated_geometry(_square_shell_with_tagged_member_plate(tag))
    beams = [element for element in model.mesh.elements.values() if isinstance(element, BeamElement)]

    assert model.mesh.num_elements == 2
    assert len(beams) == 1
    assert getattr(beams[0], "structural_role", None) == expected_role


def test_tagged_stiffener_or_girder_plates_fail_closed_when_auto_idealization_is_disabled():
    config = AnyStructureFEMConfig(auto_idealize_member_plates_as_beams=False)

    with pytest.raises(ValueError, match="idealized-member-plates-require-beam-members-stiffener"):
        build_fe_model_from_generated_geometry(_square_shell_with_tagged_member_plate(), config)


def test_symmetric_pressure_load_resultant_matches_generated_area():
    model = build_fe_model_from_generated_geometry(_square_shell_geometry())
    load_case = build_symmetric_load_case(_Calc(), model, AnyStructureFEMConfig(pressure_pa=5.0, add_inplane_edge_loads=False))

    resultant = load_case_resultant(model, load_case)

    np.testing.assert_allclose(resultant.force, [0.0, 0.0, 10.0], atol=1.0e-12)


def test_symmetric_pressure_load_sign_controls_normal_direction():
    model = build_fe_model_from_generated_geometry(_square_shell_geometry())
    positive = build_symmetric_load_case(
        _Calc(),
        model,
        AnyStructureFEMConfig(pressure_pa=5.0, pressure_sign=1.0, add_inplane_edge_loads=False),
    )
    negative = build_symmetric_load_case(
        _Calc(),
        model,
        AnyStructureFEMConfig(pressure_pa=5.0, pressure_sign=-1.0, add_inplane_edge_loads=False),
    )

    positive_resultant = load_case_resultant(model, positive)
    negative_resultant = load_case_resultant(model, negative)

    np.testing.assert_allclose(positive_resultant.force, [0.0, 0.0, 10.0], atol=1.0e-12)
    np.testing.assert_allclose(negative_resultant.force, [0.0, 0.0, -10.0], atol=1.0e-12)
    np.testing.assert_allclose(positive_resultant.force, -negative_resultant.force, atol=1.0e-12)


def test_shell_geometric_stiffness_from_membrane_compression_is_symmetric_and_scales():
    model = build_fe_model_from_generated_geometry(_square_shell_geometry())
    KG_1, _ = assemble_geometric_stiffness_matrix(model, {1: {"membrane_compression_x": 10.0, "membrane_compression_y": 4.0}})
    KG_3, _ = assemble_geometric_stiffness_matrix(model, {1: {"membrane_compression_x": 30.0, "membrane_compression_y": 12.0}})

    assert KG_1.nnz > 0
    np.testing.assert_allclose(KG_1.toarray(), KG_1.toarray().T, atol=1.0e-12)
    np.testing.assert_allclose(KG_3.toarray(), 3.0 * KG_1.toarray(), rtol=1.0e-12, atol=1.0e-12)


def test_recovered_static_prestress_drives_buckling_workflow_for_full_generated_cylinder():
    config = AnyStructureFEMConfig(pressure_pa=2_000.0, pressure_sign=-1.0, add_inplane_edge_loads=False, num_buckling_modes=2)

    result = run_anystructure_fem_mode(_Calc(), _cylinder_geometry(), config)

    assert result.static_solver_status == "converged"
    assert result.valid, result.to_dict()
    assert result.critical_load_factor is not None
    assert result.critical_load_factor > 0.0
    assert result.buckling_load_factors == sorted(result.buckling_load_factors)
    assert result.prestress_summary["shell_elements"] > 0
    assert result.stress_max > 0.0


def test_prestress_recovery_returns_shell_states_from_static_result():
    geometry = _square_shell_geometry()
    geometry["supports"] = [
        {"node_ids": [1, 4], "dof_constraints": {"ux": 0.0, "uy": 0.0, "uz": 0.0, "rx": 0.0, "ry": 0.0, "rz": 0.0}},
        {"node_ids": [2, 3], "dof_constraints": {"uy": 0.0, "uz": 0.0, "rx": 0.0, "ry": 0.0, "rz": 0.0}},
    ]
    model = build_fe_model_from_generated_geometry(geometry)
    load_case = build_symmetric_load_case(_Calc(), model, AnyStructureFEMConfig(pressure_pa=0.0))

    displacements, solver_info = solve_linear(model, load_case)
    states, summary = recover_prestress_from_static_result(model, displacements)

    assert solver_info["convergence_info"]["status"] == "converged"
    assert 1 in states
    assert summary["shell_elements"] == 1
