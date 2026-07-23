"""Plasticity return-map and nonlinear tangent qualification checks."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from anysolver import (
    element_tangent_metrics,
    generate_plasticity_qualification_report,
    material_point_path_metrics,
    reference_plastic_curve,
    yield_function_residual,
)
from anysolver.plasticity import plane_stress_return_map

import numpy as np


def test_material_point_paths_have_small_yield_residuals() -> None:
    metrics = material_point_path_metrics()

    assert metrics["elastic"]["stress_relative_error"] < 1.0e-14
    assert metrics["elastic"]["tangent_relative_error"] < 1.0e-14
    assert metrics["max_abs_yield_residual"] < 1.0e-8
    assert metrics["plastic_paths"]["uniaxial"]["alpha"] > 0.0
    assert metrics["plastic_paths"]["pure_shear"]["alpha"] > 0.0
    assert metrics["plastic_paths"]["unload_from_plastic"]["alpha_change"] == 0.0


def test_yield_function_residual_matches_returned_state() -> None:
    curve = reference_plastic_curve()
    strain = np.array([[0.003, 0.001, 0.0005]], dtype=float)
    stress, _tangent, _plastic, alpha = plane_stress_return_map(
        strain,
        np.zeros_like(strain),
        np.zeros(1),
        210.0e9,
        0.3,
        curve,
    )

    assert abs(yield_function_residual(stress[0], float(alpha[0]), curve)) < 1.0e-8


def test_element_tangent_metrics_are_algorithmic_and_finite_difference_tight() -> None:
    metrics = element_tangent_metrics()

    assert metrics["beam_elastic"]["tangent_fd_relative_error"] < 1.0e-8
    assert metrics["beam_fiber_plastic"]["tangent_fd_relative_error"] < 1.0e-8
    assert metrics["shell_elastic"]["tangent_fd_relative_error"] < 1.0e-8
    assert metrics["shell_layered_plastic"]["state_summary"]["alpha_max"] > 0.0
    assert metrics["shell_layered_plastic"]["tangent_status"] == "tight"
    assert metrics["shell_layered_plastic"]["tangent_fd_relative_error"] < 1.0e-4
    assert metrics["max_algorithmic_tangent_error"] < 1.0e-4


def test_plasticity_qualification_report_exposes_limits_and_dnv_curves() -> None:
    report = generate_plasticity_qualification_report()

    assert report["status"] == "passed"
    assert "S355_0.01" in report["dnv_curves"]
    assert report["material_point"]["max_abs_yield_residual"] < 1.0e-8
    assert report["element_tangents"]["max_algorithmic_tangent_error"] < 1.0e-4
    assert any("numerical tangent" in item for item in report["known_limitations"])


def test_plasticity_qualification_cli_writes_json_and_markdown() -> None:
    output_dir = Path(".pytest_tmp_plasticity_qualification") / str(os.getpid())
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        json_path = output_dir / "plasticity_qualification.json"
        md_path = output_dir / "plasticity_qualification.md"
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/run_plasticity_qualification.py",
                "--output",
                str(json_path),
                "--markdown",
                str(md_path),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr + completed.stdout
        report = json.loads(json_path.read_text(encoding="utf-8"))
        assert report["status"] == "passed"
        assert md_path.exists()
    finally:
        if output_dir.exists():
            shutil.rmtree(output_dir, ignore_errors=True)
