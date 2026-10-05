"""One bounded eight-interval native mixed diagnostic; not F03 acceptance."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
from pathlib import Path
from time import monotonic

import numpy as np
from scipy import linalg
from threadpoolctl import threadpool_info

from scripts._b3_e4_f03_native_fixture import build
from scripts.b3_e4_f03_c1_native_mixed_metric import (
    T, _beam_metric, _case, _drilling_metric, _line_metric,
)
from scripts.b3_e4_f03_distributed_surface_finite import FiniteSurfaceTopFaceLine
from scripts.b3_e4_f03_plate_patch_work import local_grid, raw_e4_tangent
from scripts.b3_e4_f03_square_section_control import square_torsion_constant
from scripts.b3_e4_f03_top_face_common_trace import _supported_scale


PREVIOUS = Path(
    "docs/agent_plans/B3_GE_E4_PL_F03_TOP_FACE_X8_MIXED_METRIC_20260927.json")
INTERVALS = 8


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluate() -> dict:
    started = monotonic()
    deadline = started + 120.
    xs, ys = local_grid(8, transverse_cells=4)
    shell, physical = raw_e4_tangent(xs, ys, thickness=T)
    beam = build(12, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um")
    ns = len(shell)
    shell_free = np.array([i for i in range(ns)
                           if (i//6) % len(xs) != 0])
    beam_free = np.asarray(beam.context.free)
    free = np.r_[shell_free, ns + beam_free]

    drill = _drilling_metric(xs, ys)
    R_shell = physical.copy()
    drill_ids = 6*np.arange(len(xs)*len(ys)) + 5
    R_shell[np.ix_(drill_ids, drill_ids)] += drill
    R_beam, R_resultant, layout = _beam_metric(beam)
    R_primal = linalg.block_diag(
        R_shell[np.ix_(shell_free, shell_free)],
        R_beam[np.ix_(beam_free, beam_free)])
    primal_chol = linalg.cholesky((R_primal+R_primal.T)/2, lower=True)
    K = linalg.block_diag(
        shell[np.ix_(shell_free, shell_free)],
        beam.tangent.toarray()[np.ix_(beam_free, beam_free)])
    if monotonic() > deadline:
        raise TimeoutError("bounded native setup deadline")

    knots = np.linspace(.9, 1., INTERVALS+1)
    patches = [FiniteSurfaceTopFaceLine(
        xs, ys, beam, thickness=T,
        x_interval=(float(low), float(high)))
        for low, high in zip(knots[:-1], knots[1:])]
    masses = np.asarray([patch.basis_integral_m for patch in patches])
    gap = max(float(np.max(np.abs(patch.evaluate_e4_total(
        np.zeros(patch.shell_size),
        beam.context.initial.mechanical)[:, 0]))) for patch in patches)
    if gap > 1e-12:
        raise ArithmeticError("top-face reference line opened")
    C = np.vstack([patch.reference_trace() for patch in patches])[:, free]
    if len(C) != 6*INTERVALS:
        raise ArithmeticError("native six-channel row inventory changed")
    R_line, line_info = _line_metric("piecewise_constant", INTERVALS, masses)
    line_chol = linalg.cholesky(R_line, lower=True)
    normalized_C = linalg.solve_triangular(line_chol, C, lower=True)
    normalized_C = linalg.solve_triangular(
        primal_chol, normalized_C.T, lower=True).T
    norm_sv = linalg.svdvals(normalized_C, check_finite=True)
    rank = int(np.linalg.matrix_rank(normalized_C))
    same_free, scales = _supported_scale(xs, ys, beam)
    if not np.array_equal(same_free, free):
        raise ArithmeticError("physical coordinate scales changed their layout")
    scaled_rows = C*scales[free]
    row_norm = np.linalg.norm(scaled_rows, axis=1)
    if np.any(row_norm == 0):
        raise ArithmeticError("an eight-interval work row vanished")
    unit_rows = scaled_rows/row_norm[:, None]
    physical_u, physical_sv, _ = linalg.svd(
        unit_rows, full_matrices=False, check_finite=True)
    physical_rank = int(np.count_nonzero(physical_sv > 1e-10*physical_sv[0]))
    row_diagnostic = {
        "rank_in_inherited_mixed_norm": rank,
        "inherited_norm_tail_relative": (norm_sv[-8:]/norm_sv[0]).tolist(),
        "physical_coordinate_rank_1e_10": physical_rank,
        "physical_row_tail_relative": (physical_sv[-8:]/physical_sv[0]).tolist(),
        "physical_weak_left_mode_by_interval": physical_u[:, -1].reshape(
            INTERVALS, 6).tolist(),
        "physical_weak_left_mode_residual": float(np.linalg.norm(
            physical_u[:, -1]@unit_rows)),
    }

    A = np.block([[K, C.T], [C, np.zeros((len(C), len(C)))]])
    R = linalg.block_diag(R_primal, R_line)
    shell_n, beam_n = len(shell_free), len(beam_free)
    beam_resultant = R_resultant[np.ix_(beam_free, beam_free)]
    pieces = {"C": C, "blocks": [
        ("shell_physical", slice(0, shell_n),
         physical[np.ix_(shell_free, shell_free)]),
        ("shell_drilling_chart", slice(0, shell_n),
         R_shell[np.ix_(shell_free, shell_free)]-
         physical[np.ix_(shell_free, shell_free)]),
        ("beam_kinematic", slice(shell_n, shell_n+beam_n),
         R_beam[np.ix_(beam_free, beam_free)]-beam_resultant),
        ("beam_complementary", slice(shell_n, shell_n+beam_n),
         beam_resultant),
        ("line_dual", slice(shell_n+beam_n, None), R_line),
    ]}
    if rank == len(C):
        report = _case(A, R, pieces, len(C), deadline)
    else:
        report = {
            "rows": len(A), "constraint_rows": len(C),
            "status": "rank_deficient_before_mixed_svd",
            "reason": "A mixed singular value cannot establish stability when the proposed constraint rows are dependent in the inherited norm.",
        }
    report["normalized_constraint_rank"] = rank
    report["row_diagnostic"] = row_diagnostic
    report["max_reference_gap_m_rad"] = gap
    report["line_norm"] = line_info

    old = json.loads(PREVIOUS.read_text())
    if old["shell_rows"] != shell_n or old["beam_rows"] != beam_n:
        raise ArithmeticError("saved comparison has a different primal model")
    return {
        "classification": "bounded eight-interval native retained mixed diagnostic; not F03/G0B acceptance",
        "question": "Does P0 growth on the same native primal expose a weak mixed mode?",
        "model": "saved x8/y4 C1 Q4/B3-12, 35 mm shell, 2 um tangent beam, fixed left roots",
        "operator": "actual virgin E4 and full native B3 retained tangents; exact weak top-face rows",
        "norm": "unchanged diagnostic physical/chart primal and P0 H^-1/2 dual norm",
        "previous_sha256": _sha(PREVIOUS),
        "previous_beta": {key: old["cases"][key]["beta_min"]
                          for key in ("p0_m2", "p0_m4")},
        "layout": layout,
        "shell_rows": shell_n,
        "beam_rows": beam_n,
        "case": report,
        "elapsed_s_not_benchmark": monotonic()-started,
        "limitations": ["one primal mesh and ratio; no mesh-uniform stability claim",
                        "diagnostic norm is not an independently established physical norm",
                        "no loaded physical-transfer or locking comparison"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = evaluate()
    if result["elapsed_s_not_benchmark"] > 120.:
        raise TimeoutError("bounded native diagnostic exceeded 120 s")
    sources = [Path(__file__),
               Path("scripts/b3_e4_f03_top_face_native_mixed_metric.py"),
               Path("scripts/b3_e4_f03_c1_native_mixed_metric.py"),
               Path("scripts/b3_e4_f03_distributed_surface_finite.py"),
               Path("scripts/_b3_e4_f03_native_fixture.py")]
    result["source_git"] = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True).strip()
    result["source_sha256"] = {str(path): _sha(path) for path in sources}
    result["python"] = platform.python_version()
    result["numpy"] = np.__version__
    result["threadpool_info"] = threadpool_info()
    result["thread_env"] = {key: os.environ.get(key) for key in
                            ("NUMBA_DISABLE_JIT", "OPENBLAS_NUM_THREADS",
                             "MKL_NUM_THREADS", "OMP_NUM_THREADS")}
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
    print(json.dumps({"elapsed_s": result["elapsed_s_not_benchmark"],
                      "rows": result["case"]["rows"],
                      "rank": result["case"]["normalized_constraint_rank"],
                      "beta": result["case"].get("beta_min"),
                      "prior": result["previous_beta"],
                      "physical_rank": result["case"]["row_diagnostic"]["physical_coordinate_rank_1e_10"],
                      "tail": result["case"]["row_diagnostic"]["physical_row_tail_relative"],
                      "shares": result["case"].get("near_null_metric_share")},
                     sort_keys=True))


if __name__ == "__main__":
    main()
