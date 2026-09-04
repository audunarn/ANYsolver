from __future__ import annotations

from types import SimpleNamespace

import anysolver
import numpy as np
import pytest
from anysolver import runtime
from anysolver import anystructure_fem_mode
from anysolver import arc_length


def _flat_geometry() -> dict[str, object]:
    return {
        "domain": "flat",
        "is_cylinder": False,
        "length": 2.0,
        "width": 1.0,
        "plate_thickness": 0.012,
        "stiffener_spacing": 0.5,
        "girder_spacing": 1.0,
        "stiffener_section": {
            "area": 0.002,
            "Iy": 1.0e-6,
            "Iz": 2.0e-7,
            "J": 1.0e-8,
        },
        "girder_section": {
            "area": 0.004,
            "Iy": 4.0e-6,
            "Iz": 8.0e-7,
            "J": 4.0e-8,
        },
    }


def test_runtime_contract_is_headless_and_builds_geometry() -> None:
    config = runtime.LightweightFEMConfig(
        mesh_fidelity="coarse",
        include_stiffeners=True,
        include_girders=True,
    )

    generated = runtime.build_generated_geometry(_flat_geometry(), config)

    assert runtime.full_backend_available()
    assert generated["nodes"]
    assert generated["shells"]
    assert "beams" in generated


def test_runtime_public_api_is_explicit_and_complete() -> None:
    expected = {
        "GeneratedGeometry",
        "LightweightFEMConfig",
        "LightweightFEMResult",
        "NormalizedGeometry",
        "RuntimeAnalysisSelection",
        "StatusCallback",
        "apply_mode_shape_imperfections",
        "build_generated_geometry",
        "dnv_c208_steel_properties",
        "full_backend_api",
        "full_backend_available",
        "run_lightweight_fem",
        "run_production_fem",
        "resolve_runtime_analysis",
        "runtime_imperfection_preview_offsets",
        "warm_fe_solver_kernels",
    }

    assert set(runtime.__all__) == expected
    assert all(hasattr(runtime, name) for name in runtime.__all__)


def test_runtime_forwards_optional_nonlinear_static_warmup(monkeypatch) -> None:
    observed = {}

    def warm(shell_orders, **options):
        observed["shell_orders"] = shell_orders
        observed.update(options)
        return {"status": "completed"}

    monkeypatch.setattr(runtime, "_backend_warm_fe_solver_kernels", warm)

    result = runtime.warm_fe_solver_kernels(
        ("S4",),
        include_nonlinear_static=True,
    )

    assert result == {"status": "completed"}
    assert observed == {
        "shell_orders": ("S4",),
        "include_nonlinear_impact": False,
        "include_nonlinear_static": True,
    }


def test_runtime_analysis_selection_is_public_and_normalized() -> None:
    selection = runtime.resolve_runtime_analysis(
        runtime.LightweightFEMConfig(
            analysis_type="geom. + material nonlinear static",
            nonlinear_solution_control="arc length",
            nonlinear_static_kinematics="Corotational",
        )
    )

    assert selection == runtime.RuntimeAnalysisSelection(
        static_nonlinear=True,
        material_nonlinear=True,
        solution_control="arc length",
        kinematics="corotational",
    )


def test_root_exports_arc_length_and_generic_generated_geometry_api() -> None:
    expected_root_names = {
        "ArcLengthControl",
        "ArcLengthResult",
        "ArcLengthStep",
        "solve_static_arc_length",
        "GeneratedGeometryFEMConfig",
        "GeneratedGeometryFEMResult",
        "run_generated_geometry_fem",
    }

    assert expected_root_names <= set(anysolver.__all__)
    assert anysolver.ArcLengthControl is arc_length.ArcLengthControl
    assert anysolver.ArcLengthResult is arc_length.ArcLengthResult
    assert anysolver.ArcLengthStep is arc_length.ArcLengthStep
    assert anysolver.solve_static_arc_length is arc_length.solve_static_arc_length


def test_generic_generated_geometry_aliases_match_historical_api() -> None:
    generic_names = {
        "GeneratedGeometryFEMConfig",
        "GeneratedGeometryFEMResult",
        "run_generated_geometry_fem",
    }

    assert generic_names <= set(anystructure_fem_mode.__all__)
    assert anysolver.GeneratedGeometryFEMConfig is anysolver.AnyStructureFEMConfig
    assert anysolver.GeneratedGeometryFEMResult is anysolver.AnyStructureFEMResult
    assert anysolver.run_generated_geometry_fem is anysolver.run_anystructure_fem_mode

    assert (
        anystructure_fem_mode.GeneratedGeometryFEMConfig
        is anystructure_fem_mode.AnyStructureFEMConfig
    )
    assert (
        anystructure_fem_mode.GeneratedGeometryFEMResult
        is anystructure_fem_mode.AnyStructureFEMResult
    )
    assert (
        anystructure_fem_mode.run_generated_geometry_fem
        is anystructure_fem_mode.run_anystructure_fem_mode
    )


def test_runtime_rejects_curved_b3_ring_girders() -> None:
    geometry = {
        "geometry": "cylinder",
        "radius_m": 1.0,
        "length_m": 2.0,
        "thickness_m": 0.012,
        "has_stiffener": False,
        "has_girder": True,
        "girder_spacing_m": 1.0,
    }

    with pytest.raises(ValueError, match="B3 ring girders are not supported"):
        runtime.build_generated_geometry(
            geometry,
            runtime.LightweightFEMConfig(beam_element_order="B3"),
        )


def test_runtime_cylinder_adaptive_refinement_preserves_b3_midnodes() -> None:
    geometry = {
        "geometry": "cylinder",
        "radius_m": 1.0,
        "length_m": 2.0,
        "thickness_m": 0.012,
        "has_stiffener": True,
        "stiffener_spacing_m": 1.0,
        "has_girder": False,
        "stiffener_section": {
            "area": 0.002,
            "Iy": 1.0e-6,
            "Iz": 2.0e-7,
            "J": 1.0e-8,
        },
    }
    config = runtime.LightweightFEMConfig(
        mesh_fidelity="coarse",
        beam_element_order="B3",
        include_stiffeners=True,
        include_girders=False,
        point_refinement_enabled=True,
        point_refinement_x_m=0.6,
        point_refinement_y_m=0.3,
        point_refinement_fine_factor=0.3,
        point_refinement_extent_m=0.35,
    )

    generated = runtime.build_generated_geometry(geometry, config)
    coordinates = {
        int(node["id"]): [float(value) for value in node["coords"]]
        for node in generated["nodes"]
    }
    b3_beams = [beam for beam in generated["beams"] if len(beam["node_ids"]) == 3]

    assert generated["adaptive_mesh"]["enabled"]
    assert b3_beams
    for beam in b3_beams:
        start, middle, end = (coordinates[int(node_id)] for node_id in beam["node_ids"])
        expected_middle = [0.5 * (a + b) for a, b in zip(start, end)]
        assert middle == pytest.approx(expected_middle, abs=1.0e-12)


def test_runtime_lightweight_smoke() -> None:
    result = runtime.run_lightweight_fem(
        _flat_geometry(),
        runtime.LightweightFEMConfig(mesh_fidelity="coarse", pressure_pa=10_000.0),
    )

    assert result.status == "ok"
    assert result.mesh_info["nodes"] > 0
    assert result.mesh_info["shells"] > 0


def test_runtime_cylinder_smoke() -> None:
    geometry = {
        "geometry": "cylinder",
        "length_m": 2.0,
        "radius_m": 1.0,
        "thickness_m": 0.012,
        "has_stiffener": False,
        "has_girder": False,
    }

    result = runtime.run_lightweight_fem(
        geometry,
        runtime.LightweightFEMConfig(mesh_fidelity="coarse", pressure_pa=10_000.0),
    )

    assert result.status == "ok"
    assert result.mesh_info["nodes"] > 0
    assert result.mesh_info["shells"] > 0


def test_runtime_rejects_follower_pressure_outside_nonlinear_static() -> None:
    result = runtime.run_production_fem(
        _flat_geometry(),
        runtime.LightweightFEMConfig(
            mesh_fidelity="coarse",
            runtime_solver="static only",
            pressure_pa=1_000.0,
            follower_pressure=True,
        ),
    )

    assert result.status == "invalid_follower_pressure"
    assert any(
        "requires a nonlinear static or arc-length" in message
        for message in result.diagnostics
    )


def test_runtime_rejects_follower_pressure_with_stepwise_eigen_buckling() -> None:
    reason = runtime._invalid_follower_pressure_reason(
        runtime.LightweightFEMConfig(
            runtime_solver="stepwise",
            analysis_type="geometric nonlinear static",
            follower_pressure=True,
        )
    )

    assert "stability pencil" in reason
    assert "'static only' or 'nonlinear static'" in reason


def test_runtime_reuses_one_bounded_session_for_linear_prestress_and_buckling(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    generated = {
        "plot_type": "flat",
        "plot_grid": [],
        "nodes": [
            {"id": 1, "coords": [0.0, 0.0, 0.0]},
            {"id": 2, "coords": [1.0, 0.0, 0.0]},
            {"id": 3, "coords": [1.0, 1.0, 0.0]},
            {"id": 4, "coords": [0.0, 1.0, 0.0]},
        ],
        "shells": [
            {
                "id": 1,
                "node_ids": [1, 2, 3, 4],
                "thickness": 0.01,
                "role": "skin",
            }
        ],
        "beams": [],
    }
    model = anystructure_fem_mode.build_fe_model_from_generated_geometry(generated)
    captured: dict[str, object] = {}

    class RecordingSession:
        def __init__(self, owned_model):
            captured["owned_model"] = owned_model
            self.closed = False

        def diagnostics(self):
            return {"plan_reused": True, "stiffness_builds": 1}

        def close(self):
            self.closed = True
            captured["closed"] = True

    def fake_linear(model_arg, _load_case, **kwargs):
        captured["linear_session"] = kwargs.get("session")
        return np.zeros(model_arg.mesh.dof_manager.total_dofs), {
            "convergence_info": {
                "status": "converged",
                "backend": {"backend": "test_double"},
            },
            "constraint_method": "test_double",
            "constraint_mode": "test_double",
        }

    def fake_buckling(_model_arg, _states, **kwargs):
        captured["buckling_session"] = kwargs.get("session")
        return SimpleNamespace(
            modes=(),
            failed=False,
            status="completed",
            diagnostics={},
        )

    monkeypatch.setattr(runtime, "_backend_AnalysisSession", RecordingSession)
    monkeypatch.setattr(runtime, "_backend_solve_linear", fake_linear)
    monkeypatch.setattr(runtime, "_backend_solve_buckling", fake_buckling)

    result = runtime.run_production_fem(
        _flat_geometry(),
        runtime.LightweightFEMConfig(
            runtime_solver="stepwise",
            analysis_type="linear eigenvalue",
            num_buckling_modes=1,
        ),
        imported_fem_model=model,
        precomputed_generated_geometry=generated,
    )

    assert result.status == "ok"
    assert captured["owned_model"] is model
    assert captured["linear_session"] is captured["buckling_session"]
    assert captured["closed"] is True
    assert result.prestress_summary["analysis_session"]["plan_reused"] is True
    assert any("Reused one analysis session" in item for item in result.diagnostics)


def test_runtime_session_reuse_excludes_state_changing_paths() -> None:
    assert runtime._can_reuse_linear_buckling_session(
        runtime.LightweightFEMConfig(
            runtime_solver="stepwise",
            analysis_type="linear eigenvalue",
        )
    )
    assert not runtime._can_reuse_linear_buckling_session(
        runtime.LightweightFEMConfig(
            runtime_solver="nonlinear static",
            analysis_type="geometric nonlinear static",
        )
    )
    assert not runtime._can_reuse_linear_buckling_session(
        runtime.LightweightFEMConfig(collision_enabled=True)
    )


def test_geometric_nonlinear_elastic_runtime_does_not_claim_plastic_history() -> None:
    result = runtime.run_production_fem(
        {
            "geometry": "flat panel",
            "length_m": 0.6,
            "width_m": 0.3,
            "thickness_m": 0.01,
            "has_stiffener": False,
            "has_girder": False,
        },
        runtime.LightweightFEMConfig(
            mesh_fidelity="coarse",
            runtime_solver="nonlinear static",
            analysis_type="geometric nonlinear static",
            material_model="linear elastic",
            pressure_pa=1_000.0,
            nonlinear_steps=2,
            num_buckling_modes=1,
        ),
    )

    assert result.status == "ok"
    assert not any(
        "elastoplastic states" in message for message in result.diagnostics
    )
    assert (
        result.prestress_summary["stress_recovery"]["mode"]
        == "material_history"
    )
    assert "mixed_reconstruction_peak_von_mises_pa" not in result.prestress_summary


def test_runtime_bridges_generated_loads_and_corotational_arc_length(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    generated = {
        "plot_type": "flat",
        "plot_grid": [],
        "nodes": [
            {"id": 1, "coords": [0.0, 0.0, 0.0]},
            {"id": 2, "coords": [2.0, 0.0, 0.0]},
            {"id": 3, "coords": [2.0, 1.0, 0.0]},
            {"id": 4, "coords": [0.0, 1.0, 0.0]},
        ],
        "shells": [
            {
                "id": 1,
                "node_ids": [1, 2, 3, 4],
                "thickness": 0.02,
                "role": "skin",
            }
        ],
        "beams": [],
    }
    model = anystructure_fem_mode.build_fe_model_from_generated_geometry(generated)
    captured: dict[str, object] = {}

    def fake_linear(model_arg, load_case, **_kwargs):
        captured["linear_load_case"] = load_case
        return np.zeros(model_arg.mesh.dof_manager.total_dofs), {
            "convergence_info": {
                "status": "converged",
                "backend": {"backend": "test_double"},
            },
            "constraint_method": "test_double",
            "constraint_mode": "test_double",
        }

    def fake_arc_length(model_arg, load_case, **kwargs):
        captured["arc_load_case"] = load_case
        captured["arc_kwargs"] = kwargs
        displacements = np.zeros(model_arg.mesh.dof_manager.total_dofs)
        return SimpleNamespace(
            status="completed",
            converged=True,
            capacity_estimate=0.5,
            displacements=displacements,
            element_states={},
            steps=(),
            info={"kinematics": kwargs["kinematics"], "num_layers": 5},
            peak_load_factor=0.5,
            peak_step_index=None,
        )

    monkeypatch.setattr(runtime, "_backend_solve_linear", fake_linear)
    monkeypatch.setattr(
        runtime,
        "_backend_solve_static_arc_length",
        fake_arc_length,
    )
    config = runtime.LightweightFEMConfig(
        runtime_solver="static only",
        analysis_type="geometric nonlinear static",
        nonlinear_solution_control="arc length",
        nonlinear_static_kinematics="corotational",
        pressure_pa=1_000.0,
        follower_pressure=True,
        shear_force_n=321.0,
        torsional_moment_nm=654.0,
    )

    result = runtime.run_production_fem(
        _flat_geometry(),
        config,
        imported_fem_model=model,
        precomputed_generated_geometry=generated,
    )

    assert result.status == "ok"
    load_case = captured["arc_load_case"]
    assert load_case is captured["linear_load_case"]
    assert load_case.follower_pressure is True
    nodal_loads = np.vstack(list(load_case.nodal_loads.values()))
    assert np.max(np.abs(nodal_loads[:, 1])) > 0.0
    assert np.max(np.abs(nodal_loads[:, 3])) > 0.0
    assert captured["arc_kwargs"]["kinematics"] == "corotational"
    assert (
        result.prestress_summary["nonlinear_static_kinematics"]
        == "corotational"
    )
