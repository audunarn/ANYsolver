from __future__ import annotations

import anysolver
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
        "StatusCallback",
        "apply_mode_shape_imperfections",
        "build_generated_geometry",
        "dnv_c208_steel_properties",
        "full_backend_api",
        "full_backend_available",
        "run_lightweight_fem",
        "run_production_fem",
        "runtime_imperfection_preview_offsets",
        "warm_fe_solver_kernels",
    }

    assert set(runtime.__all__) == expected
    assert all(hasattr(runtime, name) for name in runtime.__all__)


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
