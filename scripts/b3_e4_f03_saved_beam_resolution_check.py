"""One beam-only resolution check under the already-saved Fz force modes.

The shell, physical load profiles and line rows are fixed. Beam spline8 is
reproduced exactly before comparing spline16 with the native retained B3.
No line-space or coupled-solve refinement is performed.
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from pathlib import Path

import numpy as np
import scipy
from scipy import linalg
from threadpoolctl import threadpool_info, threadpool_limits

from scripts.b3_e4_f03_independent_transverse_reference import (
    BEAM_I, BEAM_J, BEAM_SHEAR_AREA, E, G, _quadrature, _spline,
    beam_basis, beam_strain_rows,
)


def beam_only(nb: int, intervals: int, mode: np.ndarray) -> dict:
    """Integrate the independent Timoshenko beam and P0 force work."""
    if nb not in (8, 16) or intervals not in (4, 8):
        raise ValueError("only the frozen two beam resolutions and force rows")
    n = len(beam_basis(nb, 0., basis="spline")[0])
    stiffness = np.zeros((3 * n, 3 * n))
    section = np.array((G * BEAM_J, E * BEAM_I, G * BEAM_SHEAR_AREA))
    beam_edges = _spline(nb, 0., 1.)[2]
    for station, weight in _quadrature(5, beam_edges):
        strain = beam_strain_rows(nb, float(station), basis="spline")
        stiffness += weight * ((strain.T * section) @ strain)
    trace = np.zeros((intervals, 3 * n))
    for cell in range(intervals):
        a, b = cell / intervals, (cell + 1) / intervals
        edges = np.r_[a, beam_edges[(a < beam_edges) & (beam_edges < b)], b]
        for station, weight in _quadrature(5, edges):
            value, _ = beam_basis(nb, float(station), basis="spline")
            trace[cell, :n] += weight * value
    solution = linalg.solve(stiffness, trace.T @ mode, assume_a="pos")
    action = float(solution @ stiffness @ solution)
    components = np.zeros(3)
    for station, weight in _quadrature(5, beam_edges):
        strain = beam_strain_rows(nb, float(station), basis="spline") @ solution
        components += weight * section * strain**2
    if (action <= 0 or abs(float(components.sum()) - action) >
            2e-9 * action):
        raise ArithmeticError("independent beam section/work closure failed")
    return {
        "beam_spline_elements": nb,
        "beam_columns": len(stiffness),
        "force_row_rank": int(np.linalg.matrix_rank(trace)),
        "action": action,
        "torsion_bending_shear_shares": (components / action).tolist(),
        "strain_work_closure_relative": float((components.sum() - action) / action),
    }


def run(output_dir: Path) -> None:
    source = subprocess.check_output(["git", "rev-parse", "HEAD"],
                                     text=True).strip()
    if subprocess.check_output(["git", "status", "--porcelain"],
                               text=True).strip():
        raise RuntimeError("run requires clean source")
    saved_file = (output_dir.parent / "f03-finite-strip-dual-norm-dev-20260925-v1" /
                  "results.jsonl")
    independent_file = (output_dir.parent / "f03-saved-fz-beam-energy-dev-20260925-v1" /
                        "results.jsonl")
    native_file = (output_dir.parent / "f03-native-saved-fz-energy-dev-20260925-v1" /
                   "results.jsonl")
    files = (saved_file, independent_file, native_file)
    sources = [[json.loads(line) for line in path.read_text().splitlines()]
               for path in files]
    if any([item["intervals"] for item in rows] != [4, 8] for rows in sources):
        raise ValueError("saved case identities changed")
    output_dir.mkdir(parents=True, exist_ok=False)
    manifest = {
        "question": "Does beam-only spline8→16 resolution account for its eight-row compliance gap against native B3 under the same saved Fz density?",
        "decision": "Movement toward native action identifies independent trial underresolution; lack of movement points to a beam-operator/trace difference. One refinement is not a convergence claim.",
        "source_sha": source, "python": platform.python_version(),
        "numpy": np.__version__, "scipy": scipy.__version__, "threads": 1,
        "inputs": [{"path": str(path),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                   for path in files],
        "scope": "beam-only spline8 and spline16 under fixed saved physical four/eight-row Fz densities; no shell or line resolution change",
    }
    with threadpool_limits(limits=1):
        manifest["effective_threadpools"] = threadpool_info()
        (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        with (output_dir / "results.jsonl").open("w") as stream:
            for saved, independent, native in zip(*sources):
                intervals = saved["intervals"]
                row = {"intervals": intervals}
                for norm in ("HminusHalf", "HminusOne"):
                    mode = np.asarray(saved[norm]["mode"], dtype=float)
                    coarse = beam_only(8, intervals, mode)
                    fine = beam_only(16, intervals, mode)
                    target = independent[norm]["beam_action"]
                    if abs(coarse["action"] - target) > 2e-9 * max(target, 1e-20):
                        raise ArithmeticError("beam8 fails saved-action parity")
                    native_action = native[norm]["algebraic_action_j"] / 1e10
                    row[norm] = {
                        "spline8": coarse, "spline16": fine,
                        "native_b3_action_under_same_density": native_action,
                        "spline16_to_native_action_ratio": fine["action"] / native_action,
                    }
                stream.write(json.dumps(row, allow_nan=False) + "\n")
                stream.flush()
                print(intervals,
                      row["HminusOne"]["spline16_to_native_action_ratio"],
                      flush=True)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)
    run(parser.parse_args().output_dir)
