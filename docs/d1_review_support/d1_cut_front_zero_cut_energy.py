"""Check reduced contact-free shell energy at the zero-width cut limit."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess

import numpy as np

import anysolver
from anysolver.assembly import build_constraint_transformation
from anysolver.matrix_assembly import assemble_stiffness_matrix
from docs.d1_review_support.d1_cut_front_shell_work import build_patch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output exists")
    model, _definition, _settings = build_patch(0.0, touching=True)
    stiffness = assemble_stiffness_matrix(model)[0]
    zero = np.zeros(model.mesh.dof_manager.total_dofs)
    _r, _f, transform, offset, _fixed, _info = (
        build_constraint_transformation(stiffness, zero, model)
    )
    reduced = (transform.T@stiffness@transform).toarray()
    symmetric = 0.5*(reduced+reduced.T)
    eigen = np.linalg.eigvalsh(symmetric)
    if eigen[0] <= 0.0 or np.linalg.norm(offset) != 0.0:
        raise AssertionError("zero-cut structural energy is not coercive")
    result = {
        "status": "development_zero_cut_structural_energy",
        "source_commit": subprocess.check_output(
            ("git", "rev-parse", "HEAD"), text=True).strip(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "model_builder_sha256": hashlib.sha256(
            Path(build_patch.__code__.co_filename).read_bytes()).hexdigest(),
        "anysolver_module": str(Path(anysolver.__file__).resolve()),
        "python": platform.python_version(),
        "free_coordinates": int(transform.shape[1]),
        "minimum_eigenvalue": float(eigen[0]),
        "maximum_eigenvalue": float(eigen[-1]),
        "symmetry_relative": float(np.linalg.norm(reduced-reduced.T)/
                                   np.linalg.norm(reduced)),
        "diagonal_minimum": float(np.min(np.diag(reduced))),
    }
    args.output.write_text(json.dumps(result, indent=2)+"\n",
                           encoding="utf-8")
    print(json.dumps({k: result[k] for k in (
        "status", "free_coordinates", "minimum_eigenvalue",
        "maximum_eigenvalue", "symmetry_relative",
    )}))


if __name__ == "__main__":
    main()
