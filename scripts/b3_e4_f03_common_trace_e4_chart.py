"""Pull common top-face rows through E4 additive total rotations at finite state."""

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
from scripts.b3_e4_f03_distributed_surface_finite import FiniteSurfaceLineHybrid
from scripts.b3_e4_f03_plate_patch_work import local_grid
from scripts.b3_e4_f03_square_section_control import square_torsion_constant
from scripts.b3_e4_f03_top_face_common_trace import _raw_rows


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _case(patch: _CommonRawWork, seed: int) -> dict:
    beam = patch.beam
    rng = np.random.default_rng(seed)
    count = patch.shell_count
    shell_total = rng.normal(size=(count, 6))*np.array(
        (.001, .001, .001, .025, .025, .025))
    beam_base = np.zeros(beam.context.count)
    beam_base[6:beam.context.nodal_count] = rng.normal(
        size=beam.context.nodal_count-6)*.001
    for element in range(len(beam.context.elements)):
        begin = beam.context.nodal_count+24*element
        beam_base[begin:begin+6] = rng.normal(size=6)*.02
    state = beam.context.advance(beam.context.initial.mechanical, beam_base)
    shell_u = rng.normal(size=(count, 6))*np.array(
        (.002, .002, .002, .04, .04, .04))
    shell_v = rng.normal(size=(count, 6))*np.array(
        (.002, .002, .002, .04, .04, .04))
    beam_u = rng.normal(size=beam.context.count)*.001
    beam_v = rng.normal(size=beam.context.count)*.001
    beam_u[:6] = 0.
    beam_v[:6] = 0.
    for element in range(len(beam.context.elements)):
        begin = beam.context.nodal_count+24*element
        beam_u[begin:begin+6] *= 30
        beam_v[begin:begin+6] *= 30

    def evaluate(total, trial_state, first=None, second=None):
        return FiniteSurfaceLineHybrid.evaluate_e4_total(
            patch, total.ravel(), trial_state, first, second)

    directions = ((shell_u, beam_u), (shell_v, beam_v))
    derivatives = evaluate(shell_total, state, *directions)
    dual = np.array((18., -23., 31., 7., -100., 13.))

    def formal_pairing(a: float, b: float) -> float:
        trial_total = shell_total+a*shell_u+b*shell_v
        trial_state = beam.context.advance(state, a*beam_u+b*beam_v)
        return float(dual@evaluate(trial_total, trial_state)[:, 0])

    h1, h2 = 1e-5, 2e-3
    first_ad = np.array((dual@derivatives[:, 1],
                         dual@derivatives[:, 2]))
    first_fd = np.array(((formal_pairing(h1, 0.)-
                          formal_pairing(-h1, 0.))/(2*h1),
                         (formal_pairing(0., h1)-
                          formal_pairing(0., -h1))/(2*h1)))
    mixed_ad = float(dual@derivatives[:, 3])
    mixed_fd = ((formal_pairing(h2, h2)-formal_pairing(h2, -h2)-
                 formal_pairing(-h2, h2)+formal_pairing(-h2, -h2))
                /(4*h2*h2))
    zero_shell = np.zeros_like(shell_total)
    zero_state = beam.context.initial.mechanical
    _, _, frame = patch.center.pose_pair(zero_state)
    reference_direction = np.r_[shell_u.ravel(), beam_u]
    reference_first = evaluate(zero_shell, zero_state, *directions)[:, 1]
    reference_row_error = float(np.max(np.abs(
        reference_first-_raw_rows(patch, frame)@reference_direction)))
    return {
        "nonzero_total_rotation_norm": float(np.linalg.norm(
            shell_total[:, 3:])),
        "nonzero_gap_norm": float(np.linalg.norm(derivatives[:, 0])),
        "reference_directional_error": reference_row_error,
        "first_ad_formal_pairing": first_ad.tolist(),
        "first_fd_formal_pairing": first_fd.tolist(),
        "first_max_formal_error": float(np.max(np.abs(first_ad-first_fd))),
        "mixed_ad_formal_pairing": mixed_ad,
        "mixed_fd_formal_pairing": float(mixed_fd),
        "mixed_formal_error": float(abs(mixed_ad-mixed_fd)),
        "signed_weight_min": float(min(p.weight for p in patch.points)),
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
        case = _case(patch, 1729)
        if (case["nonzero_total_rotation_norm"] <= 1e-3 or
                case["nonzero_gap_norm"] <= 1e-12 or
                case["reference_directional_error"] > 1e-10 or
                case["first_max_formal_error"] > 1e-7 or
                case["mixed_formal_error"] > 1e-6):
            raise ArithmeticError(f"actual E4 chart pullback failed for {kind}")
        if kind == "dual_linear" and case["signed_weight_min"] >= 0.:
            raise ArithmeticError("dual case did not exercise signed weights")
        cases[kind] = case
    return {
        "classification": "bounded actual E4 total-rotation chart pullback; no F03 acceptance",
        "question": "Do selected P0/P1/signed-dual common rows have correct first and mixed formal-work derivatives through E4 additive total coordinates at nonzero rotation?",
        "model": "Q4 x4/y4 35mm, C1 B3-12, fixed reference arm and co-moving x=.95 beam frame",
        "derivative_steps": {"first": 1e-5, "mixed": 2e-3},
        "development_limits": {"reference_directional": 1e-10,
                               "first_formal": 1e-7,
                               "mixed_formal": 1e-6},
        "cases": cases,
        "elapsed_s_not_benchmark": monotonic()-started,
        "limitations": ["selected basis rows and one finite chart only",
                        "formal multipliers have no physical dual units yet",
                        "interface stability and physical transfer remain open"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = evaluate()
    if result["elapsed_s_not_benchmark"] > 120.:
        raise TimeoutError("bounded E4 chart check exceeded 120 s")
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
        "first_max_formal_error": value["first_max_formal_error"],
        "mixed_formal_error": value["mixed_formal_error"],
        "reference_directional_error": value["reference_directional_error"]}
        for key, value in result["cases"].items()},
        "elapsed_s": result["elapsed_s_not_benchmark"]}, sort_keys=True))


if __name__ == "__main__":
    main()
