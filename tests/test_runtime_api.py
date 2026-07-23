from __future__ import annotations

from anysolver import runtime


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
