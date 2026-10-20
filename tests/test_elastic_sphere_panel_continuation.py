"""Focused continuation tests for the elastic sphere panel probe example.

One session-scoped fixture runs the complete continuation workflow exactly
once (the single existing panel-only gravity solve through
``prepare_case_models``, the probe load leg, the unload leg, the fresh
uninterrupted gravity-then-probe oracle, the actual-load acceptance and the
skin recovery) and every assertion inspects that one payload; no test
repeats a solve.  Backstop checks cover the fixed probe case data, the
unsupported contact/impact labels, the not-a-checkpoint note, exact
nonmutation and the public CLI ``--output`` wiring (exercised against the
shared payload, so the CLI test adds no second solve).
"""
from __future__ import annotations

import json
import copy
import os
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

import examples.elastic_sphere_panel_continuation as continuation_module
from examples.elastic_sphere_panel_continuation import (
    COMPARISON_ATOL,
    COMPARISON_RTOL,
    POSTCHECK_TOLERANCE,
    PROBE_LOAD_N,
    PROBE_NUM_STEPS,
    SCHEMA,
    SKIN_RECONSTRUCTION_TOLERANCE,
    SOLVE_SETTINGS,
    STATUS,
    TARGET_PANEL_MASS,
    GRAVITY,
    main,
    prepare_continuation,
)


@pytest.fixture(scope="session")
def continuation() -> dict:
    """The one verified continuation payload (single shared workflow run)."""
    payload = prepare_continuation()
    if output := os.environ.get("PANEL_CONTINUATION_EVIDENCE"):
        Path(output).write_text(json.dumps(payload, indent=2, allow_nan=False), encoding="utf-8")
    return payload


def test_continuation_document_metadata(continuation) -> None:
    """Status, unsupported labels and the fixed probe case data are exact."""
    assert continuation["schema"] == SCHEMA
    assert continuation["status"] == STATUS == "gravity_probe_completed"
    assert continuation["contact_response"] == "unsupported"
    assert continuation["impact_status"] == "unsupported"
    assert "no admitted contact solve" in continuation["unsupported_note"]
    assert "not a checkpoint" in continuation["not_a_checkpoint"]
    assert "cannot be used to resume" in continuation["not_a_checkpoint"]
    case = continuation["case"]
    assert case["gravity_m_s2"] == GRAVITY == 9.81
    probe = case["probe"]
    assert probe["load_N"] == [0.0, 0.0, -PROBE_LOAD_N]
    assert probe["magnitude_N"] == PROBE_LOAD_N == 1000.0
    assert probe["dof"] == "uz"
    assert probe["increments_per_leg"] == PROBE_NUM_STEPS == 2
    # The exact centre structural node: a plate shell node at x=y=z=0.
    assert probe["node_reference_position_m"] == [0.0, 0.0, 0.0]
    assert int(probe["node_id"]) < 10000
    legs = case["legs"]
    assert "gravity" in legs["load"]["constant_load"]
    assert legs["load"]["proportional_load"] == "centre probe 0 -> 1000 N"
    assert "gravity + full centre probe" in legs["unload"]["constant_load"]
    assert legs["unload"]["proportional_load"] == "negated centre probe 0 -> 1000 N"
    settings = case["settings"]
    assert settings["gravity_solve"] == {
        "kinematics": "corotational",
        "corotational_tangent": "work_conjugate",
        "num_layers": 5,
        "num_steps": 4,
        "max_iterations": 20,
        "tolerance": 1.0e-8,
        "max_load_factor": 1.0,
    }
    probe_settings = settings["probe_legs"]
    assert probe_settings["kinematics"] == "corotational"
    assert probe_settings["corotational_tangent"] == "work_conjugate"
    assert probe_settings["num_steps"] == 2
    assert probe_settings["tolerance"] == 1.0e-8
    assert probe_settings["equilibrate_initial_state"] is False
    assert probe_settings["control"] == "force"
    fresh = settings["fresh_program"]
    assert fresh["kinematics"] == "corotational"
    assert fresh["corotational_tangent"] == "work_conjugate"
    assert fresh["tolerance"] == 1.0e-8
    assert [(s["name"], s["target_factor"]) for s in fresh["stages"]] == [
        ("gravity", 1.0),
        ("probe", 1.0),
    ]


def test_all_solves_completed_with_work_conjugate_postcheck(continuation) -> None:
    """Every solve completed, work-conjugate, with a passing postcheck."""
    for key in ("gravity_solve", "load_leg", "unload_leg", "fresh_program"):
        assert continuation[key]["status"] == "completed", key
    for key in ("load_leg", "unload_leg", "fresh_program"):
        record = continuation[key]
        assert record["corotational_tangent"] == "work_conjugate", key
        postcheck = record["constraint_postcheck"]
        assert postcheck["status"] == "passed", key
        assert postcheck["max_absolute_residual"] <= POSTCHECK_TOLERANCE, key
        assert postcheck["max_relative_residual"] <= POSTCHECK_TOLERANCE, key
        assert postcheck["equation_count"] > 0, key
    # Two accepted increments per probe leg, ramping to the full probe.
    for key in ("load_leg", "unload_leg"):
        steps = continuation[key]["steps"]
        assert len(steps) == PROBE_NUM_STEPS, key
        assert [step["load_factor"] for step in steps] == [0.5, 1.0], key
        assert continuation[key]["final_load_factor"] == pytest.approx(1.0), key
        for step in steps:
            assert 1 <= step["iterations"] <= SOLVE_SETTINGS["max_iterations"]
            assert np.isfinite(step["residual_norm"])
            assert step["residual_norm"] >= 0.0
    # The fresh program reaches both full stage factors.
    fresh = continuation["fresh_program"]
    assert fresh["final_load_factor"] == pytest.approx(2.0)
    assert fresh["stage_factors"] == {"gravity": 1.0, "probe": 1.0}
    assert fresh["steps"][0]["load_factor"] < fresh["steps"][-1]["load_factor"]


def test_comparisons_within_split_restart_bound(continuation) -> None:
    """Peak matches the fresh program and unload matches original gravity."""
    comparisons = continuation["comparisons"]
    peak = comparisons["peak_vs_fresh_program"]
    unload = comparisons["unloaded_vs_original_gravity"]
    for record in (peak, unload):
        assert record["rtol"] == COMPARISON_RTOL == 1.0e-8
        assert record["atol"] == COMPARISON_ATOL == 1.0e-10
        assert record["passed"] is True
        assert np.isfinite(record["max_absolute_difference"])
        assert record["max_absolute_difference"] >= 0.0
    assert "fresh uninterrupted" in peak["label"]
    assert "original accepted gravity" in unload["label"]


def test_centre_displacement_history(continuation) -> None:
    """The centre node moves down under the probe and back on unload."""
    centre = continuation["centre_displacements"]
    for state in ("gravity", "peak", "unloaded"):
        fields = centre[state]
        assert fields["node_id"] == continuation["case"]["probe"]["node_id"]
        assert fields["reference_position_m"] == [0.0, 0.0, 0.0]
        assert len(fields["displacement"]) == 6
    gravity_uz = centre["gravity"]["displacement"][2]
    peak_uz = centre["peak"]["displacement"][2]
    unloaded_uz = centre["unloaded"]["displacement"][2]
    # Gravity self-weight sag at the centre (S6 measured -0.598 mm).
    assert -0.002 < gravity_uz < 0.0
    # The probe pushes the centre further down; the leg is a real response.
    assert peak_uz < gravity_uz
    assert peak_uz - gravity_uz < -1.0e-5
    # Unload returns to the original gravity state within the fixed bound.
    assert abs(unloaded_uz - gravity_uz) <= COMPARISON_ATOL + COMPARISON_RTOL * abs(
        gravity_uz
    )
    # Plate top stays below its undeformed level at every accepted state.
    for state in ("gravity", "peak", "unloaded"):
        assert centre[state]["plate_top_z_m"] == pytest.approx(
            0.005 + centre[state]["displacement"][2]
        )
        assert centre[state]["plate_top_z_m"] < 0.005


def test_acceptance_accounts_for_actual_loads(continuation) -> None:
    """Masses, support resultants and global balance hold at both states."""
    for label, applied_z in (
        ("peak_state", -(TARGET_PANEL_MASS * GRAVITY + PROBE_LOAD_N)),
        ("unloaded_state", -(TARGET_PANEL_MASS * GRAVITY)),
    ):
        acceptance = continuation["acceptance"][label]
        assert acceptance["applied_force_N"][2] == pytest.approx(
            applied_z, rel=1.0e-9
        )
        assert acceptance["applied_force_N"][0] == pytest.approx(
            0.0, abs=acceptance["force_balance_tolerance_N"]
        )
        assert acceptance["applied_force_N"][1] == pytest.approx(
            0.0, abs=acceptance["force_balance_tolerance_N"]
        )
        assert acceptance["force_balance_norm_N"] <= acceptance[
            "force_balance_tolerance_N"
        ]
        assert acceptance["moment_balance_norm_Nm"] <= acceptance[
            "moment_balance_tolerance_Nm"
        ]
        assert acceptance["max_support_resultant_relative_deviation"] <= acceptance[
            "reaction_agreement_tolerance"
        ]
        assert set(acceptance["recovered_named_resultants"]) == set(
            acceptance["solver_recorded_named_resultants"]
        )
        for mass in acceptance["panel_masses_kg"]:
            assert mass == pytest.approx(
                TARGET_PANEL_MASS, rel=acceptance["relative_mass_tolerance"]
            )
    # The probe carries no moment about the case origin.
    peak = continuation["acceptance"]["peak_state"]
    for component in peak["applied_moment_Nm"]:
        assert component == pytest.approx(
            0.0, abs=peak["moment_balance_tolerance_Nm"]
        )
    # The translational support carries the full actual load upward.
    translations = peak["recovered_named_resultants"]["Integrated_edge_translations"]
    assert translations[2] == pytest.approx(
        TARGET_PANEL_MASS * GRAVITY + PROBE_LOAD_N, rel=1.0e-6
    )


def test_nonmutation_of_supplied_state_and_case(continuation) -> None:
    """Every supplied input and both case models are exactly unmutated."""
    nonmutation = continuation["nonmutation"]
    for key in (
        "supplied_state_preserved", "accepted_gravity_state_preserved",
        "panel_model_coordinates_supports_materials_preserved", "sphere_model_preserved",
    ):
        assert nonmutation[key] is True, key
    assert nonmutation["sphere_solved"] is False
    assert nonmutation["gravity_duplicated"] is False
    document = json.dumps(continuation)
    assert "impact_history" not in document
    assert "restart_checkpoint" not in document


def test_skins_recovered_and_independently_reconstructed(continuation) -> None:
    """Panel skins at three accepted states; sphere at rest; 1e-13 check."""
    skins = continuation["skins"]
    panel = skins["panel"]
    assert panel["face_count"] == 100
    states = {}
    for state in ("gravity", "peak", "unloaded"):
        record = panel[state]
        assert record["corner_count"] == 400
        assert (
            record["independent_reconstruction_max_deviation_m"]
            <= SKIN_RECONSTRUCTION_TOLERANCE
        )
        assert len(record["recovered_positions_m"]) == 400
        states[state] = np.asarray(record["recovered_positions_m"], dtype=float)
    assert "accepted gravity-preloaded" in panel["gravity"]["label"]
    assert "peak" in panel["peak"]["label"]
    assert "unloaded" in panel["unloaded"]["label"]
    # The recovered skins are genuinely different accepted states.
    gravity_to_peak = float(
        np.max(np.linalg.norm(states["peak"] - states["gravity"], axis=1))
    )
    peak_to_unloaded = float(
        np.max(np.linalg.norm(states["unloaded"] - states["peak"], axis=1))
    )
    assert gravity_to_peak > 1.0e-6
    assert peak_to_unloaded > 1.0e-6
    sphere = skins["sphere"]
    assert sphere["face_count"] == 320
    assert sphere["reference"]["corner_count"] == 960
    assert (
        sphere["reference"]["independent_reconstruction_max_deviation_m"]
        <= SKIN_RECONSTRUCTION_TOLERANCE
    )
    assert "never solved" in sphere["note"]
    assert "zero-pose reference" in sphere["reference"]["label"]


def test_cli_output_writes_shared_document(
    continuation, tmp_path, capsys, monkeypatch
) -> None:
    """The public CLI --output path writes the payload and prints a summary.

    The CLI wiring is exercised against the shared session payload (the
    workflow itself is verified by the fixture); no second solve runs here.
    """
    monkeypatch.setattr(
        continuation_module, "prepare_continuation",
        lambda: continuation, raising=True,
    )
    output = tmp_path / "nested" / "continuation.json"
    code = main(["--output", str(output)])
    assert code == 0
    written = json.loads(output.read_text(encoding="utf-8"))
    assert written == continuation
    summary = json.loads(capsys.readouterr().out)
    assert summary == {
        "status": continuation["status"],
        "contact_response": "unsupported",
        "impact_status": "unsupported",
        "output": str(output),
    }
    # Without --output the full document goes to stdout.
    code = main([])
    assert code == 0
    printed = json.loads(capsys.readouterr().out)
    assert printed == continuation


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_report_is_refused(continuation, value):
    bad = copy.deepcopy(continuation)
    bad["acceptance"]["peak_state"]["force_balance_norm_N"] = value
    with pytest.raises(RuntimeError, match="nonfinite"):
        continuation_module._verify_continuation(bad)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), 1.0e-10])
def test_invalid_constraint_result_is_refused(value):
    result = SimpleNamespace(status="completed", info={
        "corotational_tangent": "work_conjugate",
        "constraint_postcheck": {"status": "passed",
            "max_absolute_residual": value, "max_relative_residual": 0.0},
    })
    with pytest.raises(RuntimeError, match="postcheck"):
        continuation_module._require_leg_result(result, "invalid leg")


@pytest.mark.parametrize("left,right", [
    ([float("nan")], [0.0]), ([0.0], [float("inf")]),
    ([[0.0]], [[0.0]]), ([0.0], [0.0, 0.0]), ([1.0], [0.0]),
])
def test_invalid_displacement_comparison_is_refused(left, right):
    with pytest.raises(RuntimeError):
        continuation_module.displacement_agreement(left, right, "invalid comparison")


def test_support_value_mutation_changes_model_snapshot():
    model = continuation_module.build_panel_model()
    before = continuation_module._model_snapshot(model)
    model.boundary_conditions[0].dof_constraints["uz"] = 0.01
    assert continuation_module._model_snapshot(model) != before
