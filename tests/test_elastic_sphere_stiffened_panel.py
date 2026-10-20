"""Focused initial-state tests for the elastic sphere stiffened-panel example.

One session-scoped fixture performs the single panel-only gravity solve and
reuses the verified payload across the equilibrium, mass, metadata and pose
checks; the fixed sphere case data and the impact refusal are checked without
any solve.  These tests are the appended focused coverage for candidate
0.4.7+contact.candidate.20261020.s6 and deliberately avoid duplicating the
historical static-contact campaign.
"""
from __future__ import annotations

import json

import numpy as np
import pytest

from examples.elastic_sphere_stiffened_panel import (
    BAR_AREA,
    BAR_HEIGHT,
    BAR_J,
    BAR_Y_POSITIONS,
    DENSITY,
    DROP_CLEARANCE,
    ELASTIC_MODULUS,
    FORCE_BALANCE_TOLERANCE,
    GRAVITY,
    IMPACT_REFUSAL,
    IMPACT_STATUS,
    ImpactUnsupportedError,
    MOMENT_BALANCE_TOLERANCE,
    PANEL_LENGTH,
    PANEL_WIDTH,
    PLATE_THICKNESS,
    POISSON_RATIO,
    REACTION_AGREEMENT_TOLERANCE,
    RELATIVE_MASS_TOLERANCE,
    RADIUS_TOLERANCE,
    SCHEMA,
    STATUS,
    TARGET_PANEL_MASS,
    main,
    prepare_initial_state,
    request_impact,
    _sphere_geometry,
)
from examples.elastic_sphere_stiffened_panel_mesh import (
    SPHERE_MIDSURFACE_RADIUS,
    SPHERE_NODES,
    SPHERE_THICKNESS,
    SPHERE_TRIANGLES,
)


@pytest.fixture(scope="session")
def initial_state():
    """The one verified initial-state payload (single panel gravity solve)."""
    return prepare_initial_state()


def test_fixed_sphere_case_data_topology() -> None:
    """The fixed case data is a closed, outward, exact-radius icosphere."""
    geometry = _sphere_geometry()
    assert geometry["node_count"] == 162
    assert geometry["triangle_count"] == 320
    assert geometry["edge_count"] == 480
    assert geometry["edges_with_two_faces"] == geometry["edge_count"]
    assert geometry["closed"] is True
    assert geometry["outward_winding"] is True
    assert geometry["min_outward_cosine"] > 0.0
    assert geometry["max_radius_deviation_m"] <= RADIUS_TOLERANCE
    assert geometry["midsurface_radius_m"] == pytest.approx(SPHERE_MIDSURFACE_RADIUS)
    assert geometry["thickness_m"] == SPHERE_THICKNESS
    assert len(SPHERE_NODES) == 162
    assert len(SPHERE_TRIANGLES) == 320


def test_initial_state_document_metadata(initial_state) -> None:
    """Status, case metadata, supports and the unconstrained sphere are exact."""
    assert initial_state["schema"] == SCHEMA
    assert initial_state["status"] == STATUS == "initial_state_prepared"
    assert initial_state["impact_status"] == IMPACT_STATUS == "unsupported"
    case = initial_state["case"]
    assert case["panel"]["length_m"] == PANEL_LENGTH == 5.0
    assert case["panel"]["width_m"] == PANEL_WIDTH == 5.0
    assert case["panel"]["plate_thickness_m"] == PLATE_THICKNESS == 0.01
    assert case["panel"]["plate_midsurface_z_m"] == 0.0
    assert case["panel"]["plate_top_z_m"] == 0.005
    assert case["panel"]["shell_divisions"] == [10, 10]
    stiffeners = case["stiffeners"]
    assert stiffeners["count"] == 4
    assert stiffeners["spacing_m"] == 1.0
    assert stiffeners["height_m"] == BAR_HEIGHT == 0.15
    assert stiffeners["thickness_m"] == 0.01
    assert stiffeners["centroid_z_m"] == -0.080
    assert stiffeners["bottom_z_m"] == -0.155
    assert stiffeners["beam_segments_per_bar"] == 10
    assert "T-bar" in stiffeners["section_construction"]
    assert "zero-flange" in stiffeners["section_construction"]
    assert "-0.080" in stiffeners["placement_note"]
    assert stiffeners["section"]["area_m2"] == pytest.approx(BAR_AREA)
    assert stiffeners["section"]["J_m4"] == pytest.approx(BAR_J)
    material = case["material"]
    assert material["elastic_modulus_Pa"] == ELASTIC_MODULUS == 210.0e9
    assert material["poisson_ratio"] == POISSON_RATIO == 0.3
    assert material["density_kg_m3"] == DENSITY == 7850.0
    assert material["yield_stress_Pa"] == 0.0
    assert material["hardening_curve"] is None
    assert material["plasticity"] == "none"
    assert case["gravity_m_s2"] == GRAVITY == 9.81
    assert case["sphere"]["outside_diameter_m"] == pytest.approx(1.0)
    assert case["sphere"]["wall_thickness_m"] == 0.01
    assert case["drop_target"]["clearance_m"] == DROP_CLEARANCE == 10.0
    assert case["drop_target"]["executed"] is False
    # Clamped perimeter: all six DOFs on the four plate edges.
    supports = initial_state["panel"]["mesh"]["supports"]
    assert len(supports) == 2
    by_name = {support["name"]: support for support in supports}
    assert by_name["Integrated_edge_translations"]["components"] == ["ux", "uy", "uz"]
    assert by_name["Clamped_edge_rotations"]["components"] == ["rx", "ry", "rz"]
    for support in supports:
        assert support["node_count"] == 40
    # The released sphere carries no supports and is never solved.
    assert initial_state["sphere"]["supports"] == "none"
    assert initial_state["sphere"]["pose"]["stress_state"].startswith("stress-free")
    mesh = initial_state["panel"]["mesh"]
    assert mesh["shell_node_count"] == 121
    assert mesh["shell_element_count"] == 100
    assert mesh["beam_element_count"] == 40
    assert mesh["coupling_element_count"] == 44
    assert mesh["bar_centroid_z_values_m"] == [-0.080]
    assert mesh["bar_y_positions_m"] == list(BAR_Y_POSITIONS) == [-1.5, -0.5, 0.5, 1.5]
    assert mesh["plate_node_z_values_m"] == [0.0]


def test_exported_mesh_matches_model_geometry(initial_state) -> None:
    """The exported JSON carries real coordinates/connectivity, not claims.

    Verifies actual node coordinates and element connectivity for both
    bodies against the declared geometry: physical bars at
    y = -1.5, -0.5, 0.5, 1.5 m with beam neutral lines at z = -0.080 m,
    plate midsurface nodes at z = 0, clamped-support nodes on the plate
    edges, and the sphere skin nodes on the midsurface radius with the fixed
    case-data connectivity.
    """
    panel_mesh = initial_state["panel"]["mesh"]
    nodes = panel_mesh["nodes"]
    elements = panel_mesh["elements"]
    # Complete inventories of real reference coordinates and connectivity.
    assert len(nodes) == panel_mesh["shell_node_count"] + panel_mesh["beam_node_count"]
    assert len(elements) == (
        panel_mesh["shell_element_count"]
        + panel_mesh["beam_element_count"]
        + panel_mesh["coupling_element_count"]
    )
    for coordinates in nodes.values():
        assert len(coordinates) == 3
    beam_node_ids = {int(node_id) for node_id, (_, _, z) in nodes.items() if z == -0.080}
    assert len(beam_node_ids) == panel_mesh["beam_node_count"]
    # Physical bars: every beam element lies at a declared y position with
    # its neutral line at z = -0.080 m, spanning the full panel length.
    beam_elements = {
        element_id: entry
        for element_id, entry in elements.items()
        if entry["body"] == "stiffener_beam"
    }
    assert len(beam_elements) == 40
    for entry in beam_elements.values():
        assert entry["type"] == "Beam"
        assert len(entry["node_ids"]) == 2
        for node_id in entry["node_ids"]:
            _x, y, z = nodes[str(node_id)]
            assert y in BAR_Y_POSITIONS
            assert z == -0.080
    bar_ys = sorted({nodes[str(node_id)][1] for entry in beam_elements.values() for node_id in entry["node_ids"]})
    assert bar_ys == list(BAR_Y_POSITIONS)
    # Plate shells: Q4 connectivity on the z = 0 midsurface.
    shell_elements = {
        element_id: entry
        for element_id, entry in elements.items()
        if entry["body"] == "plate_shell"
    }
    assert len(shell_elements) == 100
    for entry in shell_elements.values():
        assert entry["type"] == "Shell"
        assert len(entry["node_ids"]) == 4
        for node_id in entry["node_ids"]:
            assert nodes[str(node_id)][2] == 0.0
    # Couplings tie one beam node to shell masters.
    coupling_elements = {
        element_id: entry
        for element_id, entry in elements.items()
        if entry["body"] == "beam_shell_coupling"
    }
    assert len(coupling_elements) == 44
    for entry in coupling_elements.values():
        assert entry["type"] == "InterpolatedBeamShellMPC"
        assert entry["node_ids"][0] in beam_node_ids
        assert all(str(node_id) in nodes for node_id in entry["node_ids"])
    # Clamped supports sit on the four plate edges.
    half_length = PANEL_LENGTH / 2.0
    half_width = PANEL_WIDTH / 2.0
    for support in panel_mesh["supports"]:
        for node_id in support["node_ids"]:
            x, y, _z = nodes[str(node_id)]
            assert abs(abs(x) - half_length) < 1.0e-12 or abs(abs(y) - half_width) < 1.0e-12
    # Sphere: local coordinates on the midsurface radius, fixed connectivity.
    sphere_mesh = initial_state["sphere"]["mesh"]
    sphere_nodes = sphere_mesh["nodes"]
    sphere_elements = sphere_mesh["elements"]
    assert len(sphere_nodes) == 162
    assert len(sphere_elements) == 320
    for node_id, coordinates in sphere_nodes.items():
        radius = sum(value ** 2 for value in coordinates) ** 0.5
        assert radius == pytest.approx(SPHERE_MIDSURFACE_RADIUS, abs=RADIUS_TOLERANCE)
    for element_id, entry in sphere_elements.items():
        assert entry["type"] == "Shell"
        assert entry["body"] == "sphere_skin"
        assert entry["node_ids"] == list(SPHERE_TRIANGLES[int(element_id) - 1])
        assert all(str(node_id) in sphere_nodes for node_id in entry["node_ids"])


def test_sphere_masses_match_faceted_reference(initial_state) -> None:
    """Raw unconstrained translation mass equals rho*t*faceted area per axis."""
    geometry = initial_state["sphere"]["geometry"]
    faceted_mass = DENSITY * SPHERE_THICKNESS * geometry["faceted_area_m2"]
    reference = initial_state["sphere"]["mass_reference_kg"]
    assert reference["faceted_rho_t_area"] == pytest.approx(faceted_mass)
    assert reference["smooth_midsurface_shell"] == pytest.approx(241.707384343)
    assert reference["hollow_solid_volume"] == pytest.approx(241.715604844)
    for axis, mass in enumerate(initial_state["sphere"]["masses_kg"]):
        assert mass == pytest.approx(faceted_mass, rel=RELATIVE_MASS_TOLERANCE)


def test_panel_masses_match_declared_target(initial_state) -> None:
    """Panel translation mass per axis equals the declared 2198 kg target."""
    reference = initial_state["panel"]["mass_reference_kg"]
    assert reference["plate"] == pytest.approx(1962.5)
    assert reference["bars"] == pytest.approx(235.5)
    assert reference["target_total"] == TARGET_PANEL_MASS == 2198.0
    for axis, mass in enumerate(initial_state["panel"]["masses_kg"]):
        assert mass == pytest.approx(TARGET_PANEL_MASS, rel=RELATIVE_MASS_TOLERANCE)


def test_panel_gravity_solve_completed(initial_state) -> None:
    """The panel-only gravity equilibrium completed under the fixed settings."""
    solve = initial_state["panel"]["gravity_solve"]
    assert solve["status"] == "completed"
    assert solve["settings"] == {
        "kinematics": "corotational",
        "corotational_tangent": "work_conjugate",
        "num_layers": 5,
        "num_steps": 4,
        "max_iterations": 20,
        "tolerance": 1.0e-8,
        "max_load_factor": 1.0,
    }
    assert solve["final_load_factor"] == pytest.approx(1.0)
    # num_steps defines the initial partition; the existing solver adapts it.
    # Its tolerance is relative to the reduced load reference, not absolute N.
    # The unchanged physical force/moment bounds are asserted separately below.
    steps = solve["steps"]
    assert steps[0]["load_factor"] == pytest.approx(0.25)
    assert steps[-1]["load_factor"] == pytest.approx(1.0)
    assert all(a["load_factor"] < b["load_factor"] for a, b in zip(steps, steps[1:]))
    for step in steps:
        assert 1 <= step["iterations"] <= 20
        assert np.isfinite(step["residual_norm"]) and step["residual_norm"] >= 0.0
    # Accepted nodal fields are present for every panel node.
    mesh = initial_state["panel"]["mesh"]
    node_count = mesh["shell_node_count"] + mesh["beam_node_count"]
    assert len(initial_state["panel"]["nodal_fields"]) == node_count
    for fields in initial_state["panel"]["nodal_fields"].values():
        assert len(fields) == 6


def test_global_equilibrium_balance_within_tolerances(initial_state) -> None:
    """Global force and moment balance meet the declared 1e-8 tolerances."""
    equilibrium = initial_state["panel"]["equilibrium"]
    assert equilibrium["force_balance_tolerance_N"] == FORCE_BALANCE_TOLERANCE
    assert equilibrium["moment_balance_tolerance_Nm"] == MOMENT_BALANCE_TOLERANCE
    assert FORCE_BALANCE_TOLERANCE == pytest.approx(1.0e-8 * max(1.0, 2198.0 * 9.81))
    assert MOMENT_BALANCE_TOLERANCE == pytest.approx(1.0e-8 * max(1.0, 2198.0 * 9.81 * 5.0))
    assert equilibrium["force_balance_norm_N"] <= FORCE_BALANCE_TOLERANCE
    assert equilibrium["moment_balance_norm_Nm"] <= MOMENT_BALANCE_TOLERANCE
    # The applied load is the panel weight alone, downward.
    assert equilibrium["applied_force_N"][2] == pytest.approx(-TARGET_PANEL_MASS * GRAVITY)
    assert equilibrium["applied_force_N"][0] == pytest.approx(0.0, abs=FORCE_BALANCE_TOLERANCE)
    assert equilibrium["applied_force_N"][1] == pytest.approx(0.0, abs=FORCE_BALANCE_TOLERANCE)
    # The recovered named resultants use the same corotational force law as
    # the solve and agree with the solver-recorded support resultants.
    reactions = initial_state["panel"]["reactions"]
    assert "corotational work-conjugate" in reactions["recovery_law"]
    assert reactions["agreement_tolerance"] == REACTION_AGREEMENT_TOLERANCE
    assert reactions["max_relative_component_deviation"] <= REACTION_AGREEMENT_TOLERANCE
    recorded = reactions["solver_recorded_named_resultants"]
    recovered = reactions["recovered_named_resultants"]
    assert set(recorded) == set(recovered)
    assert set(recorded) == {
        support["name"] for support in initial_state["panel"]["mesh"]["supports"]
    }
    for name, values in recorded.items():
        assert len(values) == 6
        assert values == pytest.approx(recovered[name], rel=REACTION_AGREEMENT_TOLERANCE, abs=1.0e-9)
    # The translational support carries the full panel weight upward; the
    # rotational support carries only the clamping moments.
    translations = recovered["Integrated_edge_translations"]
    rotations = recovered["Clamped_edge_rotations"]
    assert translations[2] == pytest.approx(TARGET_PANEL_MASS * GRAVITY, rel=1.0e-6)
    assert translations[0] == pytest.approx(0.0, abs=1.0e-6)
    assert translations[1] == pytest.approx(0.0, abs=1.0e-6)
    assert rotations[:3] == pytest.approx([0.0, 0.0, 0.0], abs=1.0e-6)


def test_sphere_pose_and_placement(initial_state) -> None:
    """The stress-free sphere's outer surface rests 10 m above the panel top."""
    placement = initial_state["placement"]
    assert placement["clearance_m"] == DROP_CLEARANCE == 10.0
    assert placement["sphere_outside_radius_m"] == pytest.approx(0.500)
    centre_top = placement["panel_top_z_at_impact_centre_m"]
    assert placement["sphere_centre_z_m"] == pytest.approx(
        centre_top + DROP_CLEARANCE + 0.500
    )
    pose = initial_state["sphere"]["pose"]
    assert pose["centre_m"][0] == pytest.approx(0.0)
    assert pose["centre_m"][1] == pytest.approx(0.0)
    assert pose["centre_m"][2] == pytest.approx(placement["sphere_centre_z_m"])
    assert pose["translational_velocity_m_s"] == [0.0, 0.0, 0.0]
    assert pose["angular_velocity_rad_s"] == [0.0, 0.0, 0.0]
    # No impact history is fabricated or implied anywhere in the document.
    assert "impact_history" not in json.dumps(initial_state)


def test_impact_request_is_refused(tmp_path, capsys) -> None:
    """Any impact request is refused clearly and writes no result document."""
    with pytest.raises(ImpactUnsupportedError, match="unsupported"):
        request_impact()
    output = tmp_path / "refused.json"
    code = main(["--impact", "--output", str(output)])
    assert code == 3
    assert not output.exists()
    captured = capsys.readouterr()
    refusal = json.loads(captured.out)
    assert refusal["status"] == "impact_refused"
    assert refusal["impact_status"] == IMPACT_STATUS
    assert "unsupported" in refusal["reason"]
    assert IMPACT_REFUSAL in captured.err
    assert "initial_state_prepared" in refusal["reason"]
