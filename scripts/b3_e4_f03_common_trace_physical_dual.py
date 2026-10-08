"""Reference physical wrench and work dual of the common top-face rows."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
from time import monotonic

import numpy as np
from threadpoolctl import threadpool_info

from scripts._b3_e4_f03_native_fixture import build
from scripts.b3_e4_f03_common_trace_finite_work import _CommonRawWork
from scripts.b3_e4_f03_plate_patch_work import local_grid
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


WIDTH_M = .1
LAMBDA_FORCE_N_PER_M = np.array((80., -120., 160.))
LAMBDA_MOMENT_N_PER_M2 = np.array((900., -1100., 700.))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rigid_direction(patch, *, translation: np.ndarray,
                     rotation: np.ndarray):
    shell = np.zeros((patch.shell_count, 6))
    shell[:, :3] = translation+np.cross(rotation, patch.reference_nodes)
    shell[:, 3:] = rotation
    beam = patch.beam
    state = beam.context.initial.mechanical
    beam_direction = np.zeros(beam.context.count)
    for node in range(1, beam.context.nodal_count//6):
        start = 6*node
        position = state.positions[node]+state.position_low[node]
        beam_direction[start:start+3] = (
            translation+np.cross(rotation, position))
        beam_direction[start+3:start+6] = rotation
    for element in range(len(beam.context.elements)):
        begin = beam.context.nodal_count+24*element
        beam_direction[begin:begin+6] = np.tile(rotation, 2)
    return shell, beam_direction


def _case(patch: _CommonRawWork) -> dict:
    shell0 = patch.reference_nodes.copy()
    frames0 = np.broadcast_to(np.eye(3),
                              (patch.shell_count, 3, 3)).copy()
    beam0 = patch.beam.context.initial.mechanical
    _, _, frame = patch.center.pose_pair(beam0)
    if np.max(np.abs(frame-np.eye(3))) > 1e-13:
        raise ValueError("bounded physical dual assumes identity initial frame")
    dual = np.r_[LAMBDA_FORCE_N_PER_M, LAMBDA_MOMENT_N_PER_M2]
    physical_force = np.zeros(3)
    physical_moment = np.zeros(3)
    for point in patch.points:
        arm_material = np.array((point.x-.95, point.y, 0.))
        point_force = point.weight*frame@(
            LAMBDA_FORCE_N_PER_M+
            np.cross(LAMBDA_MOMENT_N_PER_M2, arm_material))
        top_position = np.array((point.x, point.y, patch.top))
        physical_force += point_force
        physical_moment += np.cross(top_position, point_force)
    expected = np.r_[physical_force, physical_moment]
    shell_virtual = np.zeros(6)
    beam_virtual = np.zeros(6)
    for index in range(6):
        translation = np.zeros(3)
        rotation = np.zeros(3)
        if index < 3:
            translation[index] = 1.
        else:
            rotation[index-3] = 1.
        su, bu = _rigid_direction(
            patch, translation=translation, rotation=rotation)
        zero_shell = np.zeros_like(su)
        zero_beam = np.zeros_like(bu)
        shell_virtual[index] = dual@patch.evaluate(
            shell0, frames0, beam0, (su, zero_beam),
            (su, zero_beam))[:, 1]
        beam_virtual[index] = dual@patch.evaluate(
            shell0, frames0, beam0, (zero_shell, bu),
            (zero_shell, bu))[:, 1]
    physical_scale = np.maximum(np.abs(expected), np.r_[
        np.full(3, .01), np.full(3, .01)])
    shell_error = float(np.max(np.abs(shell_virtual-expected)/physical_scale))
    beam_error = float(np.max(np.abs(beam_virtual+expected)/physical_scale))
    balance_error = float(np.max(np.abs(shell_virtual+beam_virtual)/physical_scale))
    return {
        "reference_gap_max_m2_m3": float(np.max(np.abs(
            patch.evaluate(shell0, frames0, beam0)[:, 0]))),
        "physical_force_N": physical_force.tolist(),
        "physical_moment_about_origin_Nm": physical_moment.tolist(),
        "shell_virtual_force_moment": shell_virtual.tolist(),
        "beam_virtual_force_moment": beam_virtual.tolist(),
        "shell_relative_wrench_error": shell_error,
        "beam_relative_wrench_error": beam_error,
        "action_reaction_relative_error": balance_error,
        "minimum_signed_integration_weight_m": float(min(
            point.weight for point in patch.points)),
        "quadrature_points": len(patch.points),
    }


def evaluate() -> dict:
    started = monotonic()
    xs, ys = local_grid(4, transverse_cells=4)
    beam = build(12, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um")
    cases = {}
    for kind, index in (("piecewise_constant", 1),
                        ("continuous_linear", 2),
                        ("dual_linear", 0)):
        patch = _CommonRawWork(xs, ys, beam, kind=kind, index=index)
        case = _case(patch)
        if (case["reference_gap_max_m2_m3"] > 1e-11 or
                max(case["shell_relative_wrench_error"],
                    case["beam_relative_wrench_error"],
                    case["action_reaction_relative_error"]) > 1e-8):
            raise ArithmeticError(f"physical dual work failed for {kind}")
        if (kind == "dual_linear" and
                case["minimum_signed_integration_weight_m"] >= 0.):
            raise ArithmeticError("dual physical work lacks negative weight")
        cases[kind] = case
    return {
        "classification": "bounded reference physical-dual work check; no F03 acceptance",
        "question": "Do N/m mean-gap and N/m² first-moment duals recover the same physical force/moment and equal-opposite shell/beam virtual work?",
        "law": "q_F=integral(phi * transverse_average(g) dx), q_M=integral(phi * transverse_average(a cross g) dx); traction=R*(lambda_F+lambda_M cross a)/width",
        "width_m": WIDTH_M,
        "lambda_force_N_per_m": LAMBDA_FORCE_N_PER_M.tolist(),
        "lambda_moment_N_per_m2": LAMBDA_MOMENT_N_PER_M2.tolist(),
        "model": "Q4 x4/y4 35mm, C1 B3-12, selected P0/P1/signed-dual rows",
        "development_relative_wrench_limit": 1e-8,
        "cases": cases,
        "elapsed_s_not_benchmark": monotonic()-started,
        "limitations": ["reference state and selected basis rows only",
                        "finite-chart recovered display wrenches and full external transfer remain open"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = evaluate()
    if result["elapsed_s_not_benchmark"] > 120.:
        raise TimeoutError("bounded physical dual check exceeded 120 s")
    result["source_sha256"] = {str(path): _sha(path) for path in (
        Path(__file__), Path("scripts/b3_e4_f03_common_trace_finite_work.py"),
        Path("scripts/b3_e4_f03_distributed_surface_finite.py"))}
    result["python"] = platform.python_version()
    result["numpy"] = np.__version__
    result["threadpool_info"] = threadpool_info()
    result["thread_env"] = {key: os.environ.get(key) for key in
                            ("NUMBA_DISABLE_JIT", "OPENBLAS_NUM_THREADS",
                             "MKL_NUM_THREADS", "OMP_NUM_THREADS")}
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
    print(json.dumps({"cases": {key: {
        "shell_relative_wrench_error": value["shell_relative_wrench_error"],
        "beam_relative_wrench_error": value["beam_relative_wrench_error"],
        "action_reaction_relative_error": value["action_reaction_relative_error"]}
        for key, value in result["cases"].items()},
        "elapsed_s": result["elapsed_s_not_benchmark"]}, sort_keys=True))


if __name__ == "__main__":
    main()
