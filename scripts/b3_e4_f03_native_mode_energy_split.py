"""Apply saved physical Fz densities to the actual retained B3 beam operator.

This checks whether the independent bending/shear crossover survives the
native beam kinematics. It is not a shell/beam inf-sup or accuracy gate.
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

from scripts._b3_e4_f03_e4_trial_panel import FlatE4TrialPanel
from scripts._b3_e4_f03_native_fixture import build
from scripts._b3_e4_f03_shell_trace import make_shell
from scripts._b3_e4_f03_weak_line_candidate import (
    LineMultiplierSpace, assemble_reference_kkt,
)


LOAD_DENSITY_SCALE_N_PER_M = 1e5


def one_mode(beam, native_rows, mode: np.ndarray) -> dict:
    """Recover native elastic strain work after a retained linear solve."""
    load = native_rows.T @ mode * LOAD_DENSITY_SCALE_N_PER_M
    free = np.array([index for index in range(beam.context.count)
                     if index not in beam.context.fixed], dtype=int)
    tangent = beam.tangent[np.ix_(free, free)].toarray()
    increment = np.zeros(beam.context.count)
    increment[free] = linalg.solve(tangent, load[free], assume_a="sym")
    residual = beam.tangent @ increment - load
    residual_ratio = float(np.linalg.norm(residual[free]) /
                           max(np.linalg.norm(load[free]), 1.))
    if residual_ratio > 1e-10:
        raise ArithmeticError("native retained beam solve residual")
    mechanical = beam.context.advance(beam.context.initial.mechanical,
                                      increment)
    components = np.zeros(6)
    measure = 0.
    stations = 0
    for index, (_, element) in enumerate(beam.context.elements):
        rows = element.operator.recover(
            mechanical.cell_rotations[index], mechanical.resultants[index],
            origin=beam.context.initial.origins[index])
        for point in rows:
            resultants = point["resultants"] + point["resultants_low"]
            strain = point["strain"] + point["strain_low"]
            components += point["measure"] * resultants * strain
            measure += point["measure"]
            stations += 1
    algebraic_action = float(increment @ (beam.tangent @ increment))
    if (algebraic_action <= 0 or
            abs(float(components.sum()) - algebraic_action) >
            2e-9 * algebraic_action or abs(measure - 1.) > 1e-12):
        raise ArithmeticError("native recovered strain/work closure failed")
    return {
        "axial_shear_y_shear_z_torsion_bend_y_bend_z_actions_j": components.tolist(),
        "bending_shear_z_shares": [float(components[4] / algebraic_action),
                                   float(components[2] / algebraic_action)],
        "algebraic_action_j": algebraic_action,
        "strain_work_closure_relative": float(
            (components.sum() - algebraic_action) / algebraic_action),
        "equilibrium_residual_ratio": residual_ratio,
        "station_count": stations,
        "max_nodal_increment": float(np.max(np.abs(
            increment[:beam.context.nodal_count]))),
        "max_retained_increment": float(np.max(np.abs(
            increment[beam.context.nodal_count:]))),
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
    saved = [json.loads(line) for line in saved_file.read_text().splitlines()]
    independent = [json.loads(line) for line in independent_file.read_text().splitlines()]
    if [row["intervals"] for row in saved] != [4, 8] or [
            row["intervals"] for row in independent] != [4, 8]:
        raise ValueError("saved physical density identities changed")
    output_dir.mkdir(parents=True, exist_ok=False)
    manifest = {
        "question": "Does native B3 retained-section action shift from bending to transverse shear under the saved four/eight-row Fz densities?",
        "decision": "Agreement supports a physical bending/shear crossover interpretation; disagreement redirects attention to the native trace/operator. Neither outcome certifies multiplier stability.",
        "source_sha": source, "python": platform.python_version(),
        "numpy": np.__version__, "scipy": scipy.__version__, "threads": 1,
        "saved_mode_file": str(saved_file),
        "saved_mode_sha256": hashlib.sha256(saved_file.read_bytes()).hexdigest(),
        "independent_split_file": str(independent_file),
        "independent_split_sha256": hashlib.sha256(independent_file.read_bytes()).hexdigest(),
        "native_beam_half_cells": 16,
        "load_density_scale_n_per_m": LOAD_DENSITY_SCALE_N_PER_M,
        "geometry": "straight x=0..1 m native B3, Q4 shell x8/y4 only to reproduce the existing Fz trace rows",
        "scope": "beam-only native elastic response to existing physical weak densities; no new multiplier, mesh or qualification",
    }
    with threadpool_limits(limits=1):
        manifest["effective_threadpools"] = threadpool_info()
        (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        with (output_dir / "results.jsonl").open("w") as stream:
            shell = FlatE4TrialPanel(make_shell(4, "Q4", n_y=4))
            beam = build(16)
            shell_size = 6 * shell.panel.node_count
            for saved_row, independent_row in zip(saved, independent):
                intervals = saved_row["intervals"]
                space = LineMultiplierSpace(
                    "piecewise_constant",
                    tuple(np.linspace(0., 1., intervals + 1)))
                kkt = assemble_reference_kkt(
                    shell, beam, space, shell_port="physical_strip_005_005",
                    shell_support_policy="full_left_edge")
                native_rows = kkt.constraint_jacobian[2::6, shell_size:]
                row = {"intervals": intervals,
                       "native_beam_trace_row_rank": int(
                           np.linalg.matrix_rank(native_rows))}
                if row["native_beam_trace_row_rank"] != intervals:
                    raise ArithmeticError("native beam Fz trace rows dependent")
                for norm in ("HminusHalf", "HminusOne"):
                    mode = np.asarray(saved_row[norm]["mode"], dtype=float)
                    result = one_mode(beam, native_rows, mode)
                    result["independent_beam_bending_shear_shares"] = (
                        independent_row[norm]["beam_torsion_bending_shear_shares"][1:])
                    row[norm] = result
                stream.write(json.dumps(row, allow_nan=False) + "\n")
                stream.flush()
                print(intervals, row["HminusOne"]["bending_shear_z_shares"],
                      flush=True)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)
    run(parser.parse_args().output_dir)
