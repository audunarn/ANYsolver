"""Production model guardrail tests."""

from __future__ import annotations

from anysolver import (
    BoundaryCondition,
    CoupledBeamShellElement,
    FEModel,
    FixedSupport,
    LoadCase,
    ShellElement,
    validate_production_model,
)


def _issue_codes(report):
    return {issue.code for issue in report.issues}


def test_validate_production_model_rejects_invalid_material_and_thickness() -> None:
    model = FEModel("invalid_shell")
    model.add_material("bad", -1.0, 0.8, density=-5.0)
    for node_id, coords in {
        1: (0.0, 0.0, 0.0),
        2: (1.0, 0.0, 0.0),
        3: (1.0, 1.0, 0.0),
        4: (0.0, 1.0, 0.0),
    }.items():
        model.add_node(node_id, *coords)
    model.add_element(1, ShellElement(1, [1, 2, 3, 4], "bad", thickness=0.0))

    report = validate_production_model(model)

    assert report.status == "invalid"
    assert {"MAT001", "MAT002", "MAT003", "SHELL001"} <= _issue_codes(report)
    assert report.to_dict()["error_count"] >= 4


def test_validate_production_model_reports_q8_midside_and_warp_warnings() -> None:
    model = FEModel("distorted_q8")
    model.add_material("steel", 210e9, 0.3)
    coords = {
        1: (0.0, 0.0, 0.0),
        2: (1.0, 0.0, 0.0),
        3: (1.0, 1.0, 0.0),
        4: (0.0, 1.0, 0.2),
        5: (0.8, 0.0, 0.0),
        6: (1.0, 0.5, 0.0),
        7: (0.5, 1.0, 0.0),
        8: (0.0, 0.5, 0.0),
    }
    for node_id, xyz in coords.items():
        model.add_node(node_id, *xyz)
    model.add_element(1, ShellElement(1, list(range(1, 9)), "steel", thickness=0.01))

    report = validate_production_model(model, allow_free_mechanisms=True)

    assert report.status == "warning"
    assert {"MESH003", "MESH004"} <= _issue_codes(report)
    assert report.mesh_quality["max_q8_midside_deviation"] > 0.20


def test_validate_production_model_rejects_duplicate_mpc_slave_owner() -> None:
    model = FEModel("duplicate_mpc")
    model.add_material("steel", 210e9, 0.3)
    model.add_node(1, 0.0, 0.0, 0.0)
    model.add_node(2, 0.1, 0.0, 0.0)
    model.add_node(3, 0.2, 0.0, 0.0)
    model.add_element(1, CoupledBeamShellElement(1, beam_node_id=2, shell_node_id=1, material_name="steel"))
    model.add_element(2, CoupledBeamShellElement(2, beam_node_id=2, shell_node_id=3, material_name="steel"))

    report = validate_production_model(model, allow_free_mechanisms=True)

    assert report.status == "invalid"
    assert "MPC001" in _issue_codes(report)


def test_validate_production_model_rejects_follower_pressure_and_missing_pressure_element() -> None:
    model = FEModel("follower_pressure")
    model.add_material("steel", 210e9, 0.3)
    load = LoadCase("pressure")
    load.add_pressure_load(99, 1000.0)
    load.follower_pressure = True

    report = validate_production_model(model, [load], allow_free_mechanisms=True)

    assert report.status == "invalid"
    assert {"LOAD001", "LOAD002"} <= _issue_codes(report)


def test_validate_production_model_rejects_free_mechanism_by_default() -> None:
    model = FEModel("free_shell")
    model.add_material("steel", 210e9, 0.3)
    for node_id, coords in {
        1: (0.0, 0.0, 0.0),
        2: (1.0, 0.0, 0.0),
        3: (1.0, 1.0, 0.0),
        4: (0.0, 1.0, 0.0),
    }.items():
        model.add_node(node_id, *coords)
    model.add_element(1, ShellElement(1, [1, 2, 3, 4], "steel", thickness=0.01))

    free_report = validate_production_model(model)
    allowed_report = validate_production_model(model, allow_free_mechanisms=True)

    assert free_report.status == "invalid"
    assert "MECH001" in _issue_codes(free_report)
    assert allowed_report.status == "ok"


def test_validate_production_model_accepts_supported_plate() -> None:
    model = FEModel("supported_shell")
    model.add_material("steel", 210e9, 0.3)
    for node_id, coords in {
        1: (0.0, 0.0, 0.0),
        2: (1.0, 0.0, 0.0),
        3: (1.0, 1.0, 0.0),
        4: (0.0, 1.0, 0.0),
    }.items():
        model.add_node(node_id, *coords)
    model.add_element(1, ShellElement(1, [1, 2, 3, 4], "steel", thickness=0.01))
    model.add_boundary_condition(FixedSupport("fixed", [1]))
    model.add_boundary_condition(BoundaryCondition("edge_w", [2, 3, 4], {"uz": 0.0}))

    report = validate_production_model(model, allow_free_mechanisms=True)

    assert report.status == "ok"
    assert report.mesh_quality["shell_count"] == 1
