"""Private, bounded C1 retained-KKT norm diagnostic; never a G0B result.

The auxiliary Riesz norm is not assembled into the mechanics tangent. Its shell
drilling term controls a coordinate absent from physical shell energy; its beam
kinematic term controls every independent nodal and half-cell rotation; the
resultant term is the *native* complementary Hessian. No Schur condensation is
used. See the emitted manifest for the exact model and limitations.
"""

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
from threadpoolctl import threadpool_info, threadpool_limits

from scripts._b3_e4_f03_native_fixture import G, SECTION_DIAGONAL, build
from scripts._b3_e4_f03_dual_linear_norm import dual_linear_gram
from scripts._b3_e4_f03_p0_dual_norm import p0_dual_gram
from scripts._b3_e4_f03_p1_dual_norm import p1_dual_gram
from scripts.b3_e4_f03_distributed_surface_finite import c1_hybrid_line_space
from scripts.b3_e4_f03_plate_patch_work import local_grid, raw_e4_tangent
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


E = 210e9
NU = .3
T = .035
L_LINE = .1
L_BEAM = 1.
K_REF = E*T  # N/m; force-norm squared / K_REF is joules.
MAX_ROWS = 1900
KINDS = ("piecewise_constant", "continuous_linear", "dual_linear")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _scalar_h1(nodes: np.ndarray, derivative: float, zeroth: float) -> np.ndarray:
    """Exact auxiliary piecewise-linear H1 Gram; coefficients yield joules."""
    gram = np.zeros((len(nodes), len(nodes)))
    for i, h in enumerate(np.diff(nodes)):
        if h <= 0:
            raise ValueError("unordered physical stations")
        gram[i:i+2, i:i+2] += (
            derivative/h*np.array(((1., -1.), (-1., 1.))) +
            zeroth*h/6*np.array(((2., 1.), (1., 2.))))
    return gram


def _drilling_metric(xs: np.ndarray, ys: np.ndarray) -> np.ndarray:
    """Plate-bending-scale H1 chart norm for the E4 drilling coordinate only.

    D=Et^3/[12(1-nu^2)] is the physical isotropic bending rigidity (Nm).
    The 1/L_LINE^2 zeroth term fixes the norm's constant drill direction.
    Neither this matrix nor D is added to the actual E4 tangent.
    """
    rigidity = E*T**3/(12*(1-NU**2))
    n = len(xs)*len(ys)
    metric = np.zeros((n, n))
    roots = (-1/np.sqrt(3), 1/np.sqrt(3))
    for j in range(len(ys)-1):
        hy = ys[j+1]-ys[j]
        for i in range(len(xs)-1):
            hx = xs[i+1]-xs[i]
            ids = np.array((j*len(xs)+i, j*len(xs)+i+1,
                            (j+1)*len(xs)+i+1, (j+1)*len(xs)+i))
            local = np.zeros((4, 4))
            for xi in roots:
                for eta in roots:
                    nfun = np.array(((1-xi)*(1-eta), (1+xi)*(1-eta),
                                     (1+xi)*(1+eta), (1-xi)*(1+eta)))/4
                    dx = np.array((-(1-eta), 1-eta, 1+eta, -(1+eta)))/(2*hx)
                    dy = np.array((-(1-xi), -(1+xi), 1+xi, 1-xi))/(2*hy)
                    local += hx*hy/4*rigidity*(np.outer(dx, dx) +
                        np.outer(dy, dy) + np.outer(nfun, nfun)/L_LINE**2)
            metric[np.ix_(ids, ids)] += local
    return metric


def _beam_metric(beam) -> tuple[np.ndarray, np.ndarray, dict]:
    """Complete native B3 coordinate metric: nodal, cell rotations, resultants.

    The kinematic H1 fields are auxiliary nodal piecewise-linear coordinate
    fields, not a replacement for the native physical half-cell trace. The
    exact supported retained tangent remains the tested operator.
    """
    context = beam.context
    half = beam.n_half_cells
    ne = half//2
    if context.nodal_count != 6*(half+1) or context.count != context.nodal_count+24*ne:
        raise ArithmeticError("native retained 6-nodal/6-cell-rotation/18-resultant layout changed")
    active = np.asarray(context.free, dtype=int)
    if len(active) != context.count-6 or not np.array_equal(active[:6], np.arange(6, 12)):
        raise ArithmeticError("native root support or free-coordinate layout changed")
    D = SECTION_DIAGONAL.copy()
    D[3] = G*square_torsion_constant()
    kinetic = np.zeros((context.count, context.count))
    for channel in range(6):
        modulus = D[channel]
        indices = 6*np.arange(half+1)+(channel if channel < 3 else channel)
        kinetic[np.ix_(indices, indices)] += _scalar_h1(
            beam.abscissae, modulus, modulus/L_BEAM**2)
    for element in range(ne):
        for cell in (0, 1):
            h = beam.abscissae[2*element+cell+1]-beam.abscissae[2*element+cell]
            ids = context.nodal_count+24*element+3*cell+np.arange(3)
            kinetic[ids, ids] += D[3:]*h/L_BEAM**2
    resultant = np.zeros_like(kinetic)
    tangent = beam.tangent.toarray()
    for element in range(ne):
        ids = context.nodal_count+24*element+6+np.arange(18)
        block = -tangent[np.ix_(ids, ids)]
        # Native operator: K_pp=-d²W*(p)/dp², including its six force-constraint
        # variables and twelve half-cell moment variables. These are not 3x6
        # pointwise physical resultants.
        if not np.allclose(block, block.T, rtol=1e-10, atol=1e-12):
            raise ArithmeticError("native complementary Hessian is asymmetric")
        linalg.cholesky((block+block.T)/2, lower=True, check_finite=True)
        resultant[np.ix_(ids, ids)] = (block+block.T)/2
    metric = kinetic+resultant
    conditioned = metric[np.ix_(active, active)]
    scales = np.ones(len(active))
    scales[active % 6 < 3] = L_BEAM
    # The modulo rule is only for nodal entries; reset all internal coordinates.
    scales[active >= context.nodal_count] = 1.
    tested = scales[:, None]*conditioned*scales[None, :]
    linalg.cholesky((tested+tested.T)/2, lower=True, check_finite=True)
    return metric, resultant, {"free": len(active), "nodal": context.nodal_count,
        "cell_rotations": 6*ne, "resultants": 18*ne,
        "complementary_min_diagonal_J_per_resultant_squared": float(
            np.min(np.diag(resultant)[np.diag(resultant)>0]))}


def _line_metric(kind: str, intervals: int, masses: np.ndarray) -> tuple[np.ndarray, dict]:
    fn = {"piecewise_constant": p0_dual_gram,
          "continuous_linear": p1_dual_gram,
          "dual_linear": dual_linear_gram}[kind]
    low, high = fn(intervals, L_LINE, 4095)
    # Floating tail enclosures are diagnostic approximations. P1/dual may
    # invert at ~1e-11; record the defect rather than calling them bounds.
    gram = (low+high)/2
    scales = np.tile(np.r_[np.ones(3), np.full(3, 1/L_LINE)], len(masses))
    density_from_action = scales/np.repeat(masses, 6)
    metric = (density_from_action[:, None]*np.kron(gram, np.eye(6))*
              density_from_action[None, :])/K_REF
    linalg.cholesky((metric+metric.T)/2, lower=True, check_finite=True)
    return metric, {"density_gram_ordering_defect": float(np.min(
        linalg.eigvalsh((high-low+high.T-low.T)/2))),
        "basis_integrals_m": masses.tolist(),
        "physical_density_units": ["N/m"]*3+["Nm/m"]*3,
        "moment_to_force_equivalent_length_m": L_LINE}


def _case(A: np.ndarray, R: np.ndarray, pieces: dict,
          row_count: int, deadline: float) -> dict:
    if len(A) > MAX_ROWS or len(A) != len(R):
        raise ValueError("bounded mixed KKT row cap exceeded")
    if monotonic() > deadline:
        raise TimeoutError("bounded native mixed diagnostic deadline")
    chol = linalg.cholesky((R+R.T)/2, lower=True, check_finite=True)
    # B=L^-1 A L^-T. Keep the actual possibly indefinite A, without
    # replacing it by |A|, a Schur complement, or a positive trace Gram.
    B = linalg.solve_triangular(chol, A, lower=True, check_finite=True)
    B = linalg.solve_triangular(chol, B.T, lower=True, check_finite=True).T
    u, singular, vh = linalg.svd(B, full_matrices=False, check_finite=True)
    y = vh[-1]
    x = linalg.solve_triangular(chol.T, y, lower=False, check_finite=True)
    r = A@x
    scaled_residual = linalg.solve_triangular(chol, r, lower=True)
    near_null = {}
    for label, slc, block in pieces["blocks"]:
        vec = x[slc]
        near_null[label] = float(vec @ block @ vec)
    primal = x[:-row_count]
    dual = x[-row_count:]
    C = pieces["C"]
    work_left = float(dual @ (C@primal))
    work_right = float(primal @ (C.T@dual))
    if abs(work_left-work_right) > 1e-10*max(1., abs(work_left), abs(work_right)):
        raise ArithmeticError("coupled interface transpose work failed")
    return {"rows": len(A), "constraint_rows": row_count,
        "beta_min": float(singular[-1]), "operator_max": float(singular[0]),
        "normed_condition": float(singular[0]/singular[-1]),
        "weak_vector_metric_norm_sq": float(x@R@x),
        "near_null_metric_share": near_null,
        "scaled_weak_residual_norm": float(np.linalg.norm(scaled_residual)),
        "svd_residual_defect": float(np.linalg.norm(scaled_residual)-singular[-1]),
        "work_left_J": work_left, "work_right_J": work_right,
        "weak_constraint_euclidean": float(np.linalg.norm(C@primal)),
        "left_right_svd_defect": float(np.linalg.norm(B@y-singular[-1]*u[:, -1])),
        "assembly_asymmetry_relative": float(np.linalg.norm(A-A.T)/max(1., np.linalg.norm(A)))}


def evaluate() -> dict:
    started = monotonic()
    deadline = started+120.
    xs, ys = local_grid(8, transverse_cells=4)
    shell, physical = raw_e4_tangent(xs, ys, thickness=T)
    beam = build(12, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um")
    ns = len(shell)
    nb = beam.context.count
    shell_free = np.array([i for i in range(ns) if (i//6) % len(xs) != 0])
    beam_free = np.asarray(beam.context.free)
    free = np.r_[shell_free, ns+beam_free]
    drill = _drilling_metric(xs, ys)
    R_shell = physical.copy()
    drill_ids = 6*np.arange(len(xs)*len(ys))+5
    R_shell[np.ix_(drill_ids, drill_ids)] += drill
    R_beam, R_resultant, layout = _beam_metric(beam)
    R_primal = linalg.block_diag(R_shell[np.ix_(shell_free, shell_free)],
                                  R_beam[np.ix_(beam_free, beam_free)])
    primal_scale = np.ones(len(free))
    primal_scale[:len(shell_free)][shell_free % 6 < 3] = L_LINE
    primal_scale[len(shell_free):len(shell_free)+len(beam_free)] = 1.
    normalized = primal_scale[:, None]*R_primal*primal_scale[None, :]
    linalg.cholesky((normalized+normalized.T)/2, lower=True)
    K = linalg.block_diag(shell[np.ix_(shell_free, shell_free)],
                            beam.tangent.toarray()[np.ix_(beam_free, beam_free)])
    if monotonic() > deadline:
        raise TimeoutError("bounded native assembly deadline")
    reports = {}
    for intervals in (4, 8):
        for kind in KINDS:
            if monotonic() > deadline:
                raise TimeoutError("bounded native mixed diagnostic deadline")
            rows, masses, _ = c1_hybrid_line_space(xs, ys, beam, kind=kind,
                                                     intervals=intervals)
            C = rows[:, free]
            if len(C) != 6*len(masses):
                raise ArithmeticError("native six-channel row inventory changed")
            R_line, line_info = _line_metric(kind, intervals, masses)
            # A rank check in the same work-based norms avoids a threshold on
            # a mixed N/Nm/m/rad raw C matrix.
            line_chol = linalg.cholesky(R_line, lower=True)
            primal_chol = linalg.cholesky(R_primal, lower=True)
            normalized_C = linalg.solve_triangular(line_chol, C, lower=True)
            normalized_C = linalg.solve_triangular(primal_chol,
                normalized_C.T, lower=True).T
            line_info["normalized_constraint_rank"] = int(np.linalg.matrix_rank(
                normalized_C))
            if line_info["normalized_constraint_rank"] != len(C):
                raise ArithmeticError("norm-scaled native line rows lost rank")
            A = np.block([[K, C.T], [C, np.zeros((len(C), len(C)))]])
            R = linalg.block_diag(R_primal, R_line)
            shell_n = len(shell_free)
            beam_n = len(beam_free)
            beam_resultant = R_resultant[np.ix_(beam_free, beam_free)]
            pieces = {"C": C, "blocks": [
                ("shell_physical", slice(0, shell_n), physical[np.ix_(shell_free, shell_free)]),
                ("shell_drilling_chart", slice(0, shell_n),
                 R_shell[np.ix_(shell_free, shell_free)]-physical[np.ix_(shell_free, shell_free)]),
                ("beam_kinematic", slice(shell_n, shell_n+beam_n),
                 R_beam[np.ix_(beam_free, beam_free)]-beam_resultant),
                ("beam_complementary", slice(shell_n, shell_n+beam_n), beam_resultant),
                ("line_dual", slice(shell_n+beam_n, None), R_line)]}
            report = _case(A, R, pieces, len(C), deadline)
            report["line_norm"] = line_info
            reports[f"{kind}_m{intervals}"] = report
    return {"classification": "bounded private G0 native retained mixed KKT diagnostic",
        "elapsed_s": monotonic()-started,
        "model": "C1 Q4 x8/y4 35 mm E4; B3-12, 2 um tangent profile; left shell/root beam fixed",
        "line": "0.1 m six-channel weighted strip line, P0/P1/dual m4/m8",
        "operator": "actual virgin E4 trial tangent plus full native retained B3 tangent plus exact weak C1 rows",
        "metric": "E4 physical energy + separate plate-bending H1 drill chart; B3 section-weighted auxiliary nodal H1 plus both half-cell rotation L2 plus exact native complementarity Hessian; H^-1/2 physical density / Et",
        "layout": layout, "primal_rows": len(K), "shell_rows": len(shell_free),
        "beam_rows": len(beam_free), "cases": reports,
        "limitations": ["finite fixed-shell two-level screen; not mesh-uniform inf-sup or G0B acceptance",
            "auxiliary drilling chart norm is a diagnostic choice, not physical drilling stiffness",
            "auxiliary B3 nodal H1 interpolation is a norm only, not the native half-cell trace",
            "positive broken-trace quotient remains separate and has a smaller observable space",
            "floating H^-1/2 Gram is not an interval certificate; independent review required",
            "physical connection law, loaded fidelity, locking and registered-ratio sequence remain open"]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    sources = [Path(__file__), Path("scripts/_b3_e4_f03_native_fixture.py"),
        Path("scripts/b3_e4_f03_distributed_surface_finite.py"),
        Path("scripts/b3_e4_f03_plate_patch_work.py"),
        Path("scripts/_b3_e4_f03_p0_dual_norm.py"),
        Path("scripts/_b3_e4_f03_p1_dual_norm.py"),
        Path("scripts/_b3_e4_f03_dual_linear_norm.py")]
    manifest = {"source_git": subprocess.check_output(["git", "rev-parse", "HEAD"],
        text=True).strip(), "sha256": {str(p): _sha(p) for p in sources},
        "python": platform.python_version(), "numpy": np.__version__,
        "resource": {"max_dense_rows": MAX_ROWS, "wall_deadline_s": 120,
            "one_blas_thread": True}, "env": {key: os.environ.get(key) for key in
            ("NUMBA_DISABLE_JIT", "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS")}}
    (args.output/"manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
    with threadpool_limits(limits=1):
        manifest["effective_threadpools"] = threadpool_info()
        (args.output/"manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
        try:
            result = evaluate()
        except Exception as exc:
            (args.output/"failure.json").write_text(json.dumps({
                "type": type(exc).__name__, "detail": str(exc)}, indent=2)+"\n")
            raise
    (args.output/"result.json").write_text(json.dumps(result, indent=2,
        allow_nan=False)+"\n")
    print(json.dumps({"elapsed_s": result["elapsed_s"],
        "beta": {key: value["beta_min"] for key, value in result["cases"].items()}}))


if __name__ == "__main__":
    main()
