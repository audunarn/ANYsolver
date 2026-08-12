"""Focused public-contract probe for supported ANYmesher endpoints."""

from __future__ import annotations

import argparse
import json
import os
import re
import tomllib
from importlib import metadata
from pathlib import Path
from typing import Any


EXPECTED_REQUIREMENT = "ANYmesher>=0.1,<0.3"


def _compact_requirement(requirement: str) -> str:
    return re.sub(r"\s+", "", requirement)


def _installed_anymesher_requirements() -> list[str]:
    requirements = metadata.requires("ANYsolver") or []
    return [
        requirement
        for requirement in requirements
        if re.match(r"(?i)^anymesher(?:\s|[<>=!~])", requirement)
    ]


def probe_anymesher_public_contract(
    *, require_installed_metadata: bool = False
) -> dict[str, Any]:
    """Exercise the exact neutral-meshing surface consumed by ANYsolver."""

    import anymesher
    import anysolver

    expected_version = os.environ.get("EXPECTED_ANYMESHER_VERSION")
    if expected_version is not None:
        assert anymesher.__version__ == expected_version

    required_names = (
        "Mesh",
        "PanelMeshConfig",
        "StiffenedPanel",
        "StiffenerCrossSection",
        "panel_edge_nodes",
        "stiffened_panel_mesh",
        "verify_mesh_quality",
    )
    assert all(hasattr(anymesher, name) for name in required_names)
    assert anysolver.StiffenerCrossSection is anymesher.StiffenerCrossSection

    panel = anymesher.StiffenedPanel(
        length=2.4,
        width=1.8,
        plate_thickness=0.012,
        stiffener_type="T-bar",
        stiffener_spacing=0.55,
        stiffener_height=0.18,
        stiffener_web_thickness=0.008,
        stiffener_flange_width=0.10,
        stiffener_flange_thickness=0.012,
        num_stiffeners=2,
    )
    config = anymesher.PanelMeshConfig(
        shell_num_divisions_x=5,
        shell_num_divisions_y=4,
        beam_num_divisions=3,
        use_coupling_elements=True,
        tolerance=1.0e-9,
        use_8node_shells=True,
        align_mesh_to_stiffeners=True,
    )
    mesh = anymesher.stiffened_panel_mesh(panel, config)
    edge_nodes = anymesher.panel_edge_nodes(mesh)
    quality = anymesher.verify_mesh_quality(mesh)

    assert isinstance(mesh, anymesher.Mesh)
    assert mesh.nodes
    assert mesh.quads
    assert mesh.beams
    assert mesh.couplings
    assert edge_nodes["all"]
    assert isinstance(quality, anymesher.MeshQuality)
    shell_element_count = len(mesh.quads) + len(mesh.tris)
    assert shell_element_count > 0

    installed_requirements = _installed_anymesher_requirements()
    if require_installed_metadata:
        assert len(installed_requirements) == 1
        assert _compact_requirement(installed_requirements[0]) == EXPECTED_REQUIREMENT

    return {
        "anymesher_version": anymesher.__version__,
        "anymesher_origin": str(Path(anymesher.__file__).resolve()),
        "anysolver_version": anysolver.__version__,
        "anysolver_origin": str(Path(anysolver.__file__).resolve()),
        "requirement": (
            installed_requirements[0] if installed_requirements else None
        ),
        "node_count": len(mesh.nodes),
        "quad_count": len(mesh.quads),
        "beam_count": len(mesh.beams),
        "coupling_count": len(mesh.couplings),
        "edge_node_count": len(edge_nodes["all"]),
        "quality_element_count": shell_element_count,
    }


def test_source_declares_exact_anymesher_compatibility_range() -> None:
    root = Path(__file__).resolve().parents[1]
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    requirements = [
        requirement
        for requirement in project["project"]["dependencies"]
        if requirement.lower().startswith("anymesher")
    ]
    assert requirements == [EXPECTED_REQUIREMENT]


def test_anymesher_public_contract_used_by_anysolver() -> None:
    result = probe_anymesher_public_contract()
    assert result["node_count"] > 0
    assert result["quality_element_count"] > 0


def _main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe", action="store_true")
    arguments = parser.parse_args()
    if not arguments.probe:
        parser.error("the standalone entry point requires --probe")
    print(
        json.dumps(
            probe_anymesher_public_contract(require_installed_metadata=True),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
