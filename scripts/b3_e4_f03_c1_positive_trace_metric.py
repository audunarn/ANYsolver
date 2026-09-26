"""Bounded C1 positive trace-metric experiments; no G0B qualification.

The native retained B3 tangent is indefinite.  This experiment instead tests
the six-channel line rows on the quotient of *observable* B3 bottom-surface
traces, paired with the left-supported, drilling-free physical E4 energy.
It is a finite-grid representability diagnostic, not an inf-sup bound or a
replacement for the native mixed operator.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
from pathlib import Path

import numpy as np
from scipy import linalg

from scripts._b3_e4_f03_dual_linear_norm import dual_linear_gram
from scripts._b3_e4_f03_native_fixture import (
    G, SECTION_DIAGONAL, _c1_offset_slope, build,
)
from scripts._b3_e4_f03_native_spatial_port import NativeHalfCellSpatialPort
from scripts._b3_e4_f03_p0_dual_norm import p0_dual_gram
from scripts._b3_e4_f03_p1_dual_norm import p1_dual_gram
from scripts.b3_e4_f03_distributed_surface_finite import c1_hybrid_line_space
from scripts.b3_e4_f03_local_footprint_work import skew
from scripts.b3_e4_f03_plate_patch_work import local_grid, raw_e4_tangent
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


BOND = (.9, 1.)
LENGTH_M = .1
WIDTH_M = .1
GRID_CELLS = 4
BEAM_HALF_CELLS = 12
RATIO_EXTREMES = (("fine_shell_coarse_beam", 16, 4, 12),
                  ("coarse_shell_fine_beam", 2, 4, 26))
GAUSS_ORDER = 3
MAX_SQUARE = 1900
KINDS = ("piecewise_constant", "continuous_linear", "dual_linear")
REFERENCE_STIFFNESS_N_PER_M = 210e9 * .035


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _active_beam_trace(beam) -> tuple[np.ndarray, np.ndarray, dict]:
    """Return a section-weighted broken H1-like bond trace feature matrix.

    On each native half-cell the three Gauss samples define a quadratic
    interpolant in x; its derivative is taken *only within that half-cell*.
    The transverse integral is three-point Gauss across the physical width.
    The metric is positive on the observable trace quotient, not on retained
    resultants or B3 nodal rotations which the port does not observe.
    """
    nodes = beam.abscissae
    cuts = [(i, float(a), float(b)) for i, (a, b) in enumerate(
        zip(nodes[:-1], nodes[1:])) if a >= BOND[0] - 1e-12 and
        b <= BOND[1] + 1e-12]
    expected = {12: 2, 26: 16}.get(beam.n_half_cells)
    if (expected is None or len(cuts) != expected or
            abs(cuts[0][1]-BOND[0]) > 1e-12 or
            abs(cuts[-1][2]-BOND[1]) > 1e-12 or
            any(abs(a[2]-b[1]) > 1e-12 for a, b in zip(cuts[:-1], cuts[1:])) or
            any(right <= left for _, left, right in cuts) or
            not np.any(np.isclose(nodes, .95, atol=1e-12))):
        raise ValueError("unsupported or incomplete C1 retained bond half-cell partition")
    roots, weights = np.polynomial.legendre.leggauss(GAUSS_ORDER)
    # Differentiation at the Gauss nodes of their quadratic interpolant.
    vandermonde = np.vander(roots, N=GAUSS_ORDER, increasing=True)
    derivative = np.column_stack((np.zeros_like(roots),
                                  np.ones_like(roots), 2 * roots))
    differentiation = derivative @ np.linalg.inv(vandermonde)
    section_weights = SECTION_DIAGONAL.copy()
    # The C1 fixture replaces the default polar torsion proxy by the same
    # physical square-section constant used to assemble its retained beam.
    section_weights[3] = G * square_torsion_constant()
    section_root = np.sqrt(section_weights)
    n = beam.context.count
    features = []
    samples = []
    state = beam.context.initial.mechanical
    for half, left, right in cuts:
        element, cell = divmod(half, 2)
        midpoint, half_length = (left + right) / 2, (right - left) / 2
        for eta, wy in zip(roots, weights):
            y = WIDTH_M * float(eta) / 2
            transverse_weight = float(wy) / 2
            trace = []
            for xi in roots:
                x = midpoint + half_length * float(xi)
                port = NativeHalfCellSpatialPort(
                    beam.context, element, cell, (x-left)/(right-left))
                pose = port.tangent(state)
                lift = np.block([[np.eye(3), -skew(np.array((0., y, -.05)))],
                                 [np.zeros((3, 3)), np.eye(3)]])
                trace.append(lift @ pose)
            trace = np.stack(trace)
            trace_x = np.einsum("ij,jkn->ikn", differentiation, trace) / half_length
            for i, (xi, wx) in enumerate(zip(roots, weights)):
                weight = half_length * float(wx) * transverse_weight
                root = np.sqrt(weight) * section_root[:, None]
                features.append(root * trace[i] / LENGTH_M)
                features.append(root * trace_x[i])
                samples.append((half, midpoint + half_length*float(xi), y,
                                weight, trace[i]))
    feature = np.vstack(features)
    active = np.flatnonzero(np.max(np.abs(feature), axis=0) > 1e-13)
    if not len(active) or len(active) >= n:
        raise ArithmeticError("unexpected B3 observable trace inventory")
    scale = np.array([LENGTH_M if i < beam.context.nodal_count and
                      i % 6 < 3 else 1. for i in active])
    feature_scaled = feature[:, active] * scale
    _, singular, vt = linalg.svd(feature_scaled, full_matrices=True,
                                 check_finite=True)
    threshold = singular[0] * max(feature_scaled.shape) * np.finfo(float).eps * 10
    rank = int(np.count_nonzero(singular > threshold))
    if rank < 1:
        raise ArithmeticError("B3 broken trace has zero observable rank")
    report = {"half_cells": [[left, right] for _, left, right in cuts],
              "section_weights_N_and_Nm2": section_weights.tolist(),
              "active_coordinates": int(len(active)), "trace_rank": rank,
              "smallest_positive_singular": float(singular[rank-1]),
              "largest_singular": float(singular[0]),
              "relative_rank_threshold": float(threshold/singular[0]),
              "samples": samples, "scale": scale,
              "right_vectors": vt, "singular_values": singular}
    return active, feature_scaled, report


def _shell_metric(xs: np.ndarray, ys: np.ndarray) -> tuple[np.ndarray, np.ndarray, dict]:
    tangent, physical = raw_e4_tangent(xs, ys, thickness=.035)
    if max(tangent.shape) > MAX_SQUARE:
        raise ValueError("shell resource cap exceeded")
    left = {6*(j*len(xs))+axis for j in range(len(ys)) for axis in range(6)}
    free = np.array([i for i in range(len(tangent))
                     if i not in left and i % 6 != 5], dtype=int)
    block = physical[np.ix_(free, free)]
    scale = np.where(free % 6 < 3, LENGTH_M, 1.)
    metric = scale[:, None] * block * scale[None, :]
    asymmetry = float(np.linalg.norm(metric-metric.T) /
                      max(np.linalg.norm(metric), 1e-30))
    if asymmetry > 1e-10:
        raise ArithmeticError("physical E4 metric is asymmetric")
    metric = (metric+metric.T)/2
    eig = linalg.eigvalsh(metric, check_finite=True)
    if eig[0] <= max(eig[-1], 1.) * 1e-12:
        raise ArithmeticError("left-supported drilling-free physical E4 metric is not robustly positive")
    factor = linalg.cho_factor(metric, lower=True, check_finite=True)
    return free, scale, {"factor": factor, "min_eigenvalue": float(eig[0]),
                         "max_eigenvalue": float(eig[-1]),
                         "relative_min_eigenvalue": float(eig[0]/eig[-1]),
                         "relative_asymmetry": asymmetry,
                         "free_coordinates": len(free),
                         "drilling_columns_max": float(np.max(np.abs(
                             physical[:, 5::6])))}


def _beam_action(rows: np.ndarray, active: np.ndarray,
                 feature: np.ndarray, trace: dict) -> tuple[np.ndarray, np.ndarray, float]:
    outside = np.ones(rows.shape[1], dtype=bool)
    outside[active] = False
    outside_max = float(np.max(np.abs(rows[:, outside]))) if np.any(outside) else 0.
    if outside_max > 1e-12:
        raise ArithmeticError("line row observes coordinates outside broken B3 trace")
    scaled_rows = rows[:, active] * trace["scale"]
    vt = trace["right_vectors"]
    rank = trace["trace_rank"]
    kernel_error = float(np.linalg.norm(scaled_rows @ vt[rank:].T) /
                         max(np.linalg.norm(scaled_rows), 1e-30))
    if kernel_error > 1e-10:
        raise ArithmeticError("line row does not annihilate B3 trace kernel")
    right = vt[:rank].T
    dual = (scaled_rows @ right) / trace["singular_values"][:rank]
    gram = dual @ dual.T
    return gram, dual, kernel_error


def _space(kind: str, xs: np.ndarray, ys: np.ndarray, beam,
           shell_free: np.ndarray, shell_scale: np.ndarray,
           shell: dict, beam_active: np.ndarray,
           beam_feature: np.ndarray, beam_trace: dict) -> dict:
    rows, masses, patches = c1_hybrid_line_space(xs, ys, beam, kind=kind)
    shell_size = len(xs)*len(ys)*6
    if len(rows) not in (12, 18) or rows.shape[1] != shell_size+beam.context.count:
        raise ArithmeticError("unexpected six-channel row inventory")
    drilling_max = float(np.max(np.abs(rows[:, 5:shell_size:6])))
    if drilling_max > 1e-14:
        raise ArithmeticError("six-channel line row uses drilling")
    shell_rows = rows[:, shell_free]*shell_scale
    shell_solution = linalg.cho_solve(shell["factor"], shell_rows.T,
                                      check_finite=True)
    shell_gram = shell_rows @ shell_solution
    beam_gram, beam_dual, kernel_error = _beam_action(
        rows[:, shell_size:], beam_active, beam_feature, beam_trace)
    density_to_integrated = (np.tile(
        np.r_[np.ones(3), np.full(3, LENGTH_M)], len(patches)) *
        np.repeat(masses, 6))
    gram_fn = {"piecewise_constant": p0_dual_gram,
               "continuous_linear": p1_dual_gram,
               "dual_linear": dual_linear_gram}[kind]
    lower, upper = gram_fn(2, LENGTH_M, 4095)
    lower, upper = np.kron(lower, np.eye(6)), np.kron(upper, np.eye(6))
    numerator = REFERENCE_STIFFNESS_N_PER_M * (
        density_to_integrated[:, None]*(shell_gram+beam_gram)*
        density_to_integrated[None, :])
    numerator = (numerator+numerator.T)/2
    if np.min(linalg.eigvalsh(numerator, check_finite=True)) <= 0:
        raise ArithmeticError("positive trace quotient has a dependent line row")

    def mode(indices: np.ndarray) -> dict:
        numerator_i = numerator[np.ix_(indices, indices)]
        upper_i, lower_i = upper[np.ix_(indices, indices)], lower[np.ix_(indices, indices)]
        values, vectors = linalg.eigh(numerator_i, upper_i, check_finite=True)
        upper_value = float(linalg.eigh(numerator_i, lower_i,
                                       eigvals_only=True, check_finite=True)[0])
        density = np.zeros(len(rows))
        density[indices] = vectors[:, 0]
        # No canonical sign exists; orient by the largest density component.
        pivot = int(np.argmax(np.abs(density)))
        if density[pivot] < 0:
            density *= -1
        integrated = density_to_integrated*density
        shell_primal = shell_solution @ integrated
        beam_active_scaled = (beam_trace["right_vectors"][:beam_trace["trace_rank"]].T @
                              ((beam_dual.T @ integrated) /
                               beam_trace["singular_values"][:beam_trace["trace_rank"]]))
        beam_primal = np.zeros(beam.context.count)
        beam_primal[beam_active] = beam_trace["scale"]*beam_active_scaled
        shell_gap, beam_gap = rows[:, shell_free] @ (shell_scale*shell_primal), (
            rows[:, shell_size:] @ beam_primal)
        shell_work = float(REFERENCE_STIFFNESS_N_PER_M*integrated @ shell_gap)
        beam_work = float(REFERENCE_STIFFNESS_N_PER_M*integrated @ beam_gap)
        if abs(shell_work+beam_work-values[0]) > 2e-8*max(1., abs(values[0])):
            raise ArithmeticError("positive trace mode split failed")
        samples = beam_trace["samples"]
        segment_rms = []
        for half in sorted({item[0] for item in samples}):
            selected = [item for item in samples if item[0] == half]
            mass = sum(item[3] for item in selected)
            mean = sum(item[3]*np.square(item[4] @ beam_primal)
                       for item in selected) / mass
            segment_rms.append({"half_cell": int(half),
                                "position_rms_m": float(np.sqrt(sum(mean[:3]))),
                                "rotation_rms_rad": float(np.sqrt(sum(mean[3:]))),
                                "weight_m": float(mass)})
        return {"quotient_lower_bound_from_upper_dual_gram": float(values[0]),
                "quotient_upper_bound_from_lower_dual_gram": upper_value,
                "density_mode_force_equivalent_N_per_m": density.tolist(),
                "moment_density_conversion_m": LENGTH_M,
                "shell_positive_action": shell_work,
                "beam_positive_action": beam_work,
                "shell_weighted_gap_rows": shell_gap.tolist(),
                "beam_weighted_gap_rows": beam_gap.tolist(),
                "beam_broken_trace": segment_rms}

    full = mode(np.arange(len(rows)))
    nonaxial = mode(np.array([i for i in range(len(rows)) if i % 6 != 0]))
    return {"space": kind, "rows": len(rows),
            "basis_integrals_m": masses.tolist(),
            "reference_gap_max": max(float(np.max(np.abs(p.evaluate(
                p.reference_nodes, np.broadcast_to(np.eye(3),
                (p.shell_count, 3, 3)), beam.context.initial.mechanical)[:, 0])))
                for p in patches),
            "supported_row_rank": int(np.linalg.matrix_rank(rows[:, np.r_[
                shell_free, shell_size+beam_active]])),
            "shell_drilling_column_max": drilling_max,
            "beam_trace_kernel_relative_action": kernel_error,
            "dual_gram_upper_lower_ratio": float(np.max(linalg.eigvalsh(
                upper, lower, check_finite=True))),
            "full": full, "nonaxial": nonaxial}


def _fixture_contract(xs: np.ndarray, ys: np.ndarray, beam) -> dict:
    """Verify the supported C1 geometry, boundary and actual port chart."""
    shell_size = 6*len(xs)*len(ys)
    if (shell_size > 1800 or beam.context.count > MAX_SQUARE or
            abs(xs[0]+.5) > 1e-12 or abs(xs[-1]-1.5) > 1e-12 or
            abs(ys[0]+.5) > 1e-12 or abs(ys[-1]-.5) > 1e-12 or
            any(not np.any(np.isclose(xs, x, atol=1e-12))
                for x in (BOND[0], .95, BOND[1])) or
            any(not np.any(np.isclose(ys, y, atol=1e-12))
                for y in (-.05, 0., .05)) or
            set(beam.context.fixed) != set(range(6))):
        raise ValueError("C1 shell/beam geometry, support or resource contract changed")
    maximum_node_error = 0.
    for node, x in enumerate(beam.abscissae, 1):
        offset, _ = _c1_offset_slope(float(x))
        actual = np.asarray(beam.model.mesh.nodes[node].coords(), dtype=float)
        expected = np.array((x, 0., .0675+offset))
        maximum_node_error = max(maximum_node_error,
                                 float(np.max(np.abs(actual-expected))))
    if maximum_node_error > 1e-12:
        raise ArithmeticError("native B3 nodes changed C1 tapered reference")
    state = beam.context.initial.mechanical
    maximum_port_position_error = 0.
    maximum_port_frame_error = 0.
    bond_cells = 0
    for half, (left, right) in enumerate(zip(beam.abscissae[:-1],
                                            beam.abscissae[1:])):
        if left < BOND[0]-1e-12 or right > BOND[1]+1e-12:
            continue
        bond_cells += 1
        element, cell = divmod(half, 2)
        for fraction in (0., .5, 1.):
            port = NativeHalfCellSpatialPort(beam.context, element, cell,
                                             fraction)
            high, low, frame = port.pose_pair(state)
            x = (1.-fraction)*left+fraction*right
            bottom = high+low+frame@np.array((0., 0., -.05))
            maximum_port_position_error = max(maximum_port_position_error,
                float(np.max(np.abs(bottom-np.array((x, 0., .0175))))))
            maximum_port_frame_error = max(maximum_port_frame_error,
                float(np.max(np.abs(frame-np.eye(3)))))
    expected_cells = {12: 2, 26: 16}.get(beam.n_half_cells)
    if (bond_cells != expected_cells or maximum_port_position_error > 1e-12 or
            maximum_port_frame_error > 1e-12):
        raise ArithmeticError("C1 bond bottom pose/reference frame changed")
    return {"beam_root_fixed_dofs": sorted(beam.context.fixed),
            "shell_fixed_edge_x_m": float(xs[0]),
            "shell_top_reference_z_m": .0175,
            "beam_axis_reference_z_m": .0675,
            "beam_bond_half_cells": bond_cells,
            "maximum_beam_node_geometry_error_m": maximum_node_error,
            "maximum_bond_bottom_reference_error_m": maximum_port_position_error,
            "maximum_bond_frame_reference_error": maximum_port_frame_error,
            "largest_dense_square_rows": max(shell_size, beam.context.count)}


def _evaluate_case(name: str, shell_x_cells: int,
                   shell_y_cells: int, beam_half_cells: int) -> dict:
    xs, ys = local_grid(shell_x_cells, transverse_cells=shell_y_cells)
    beam = build(beam_half_cells, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um")
    fixture = _fixture_contract(xs, ys, beam)
    shell_free, shell_scale, shell = _shell_metric(xs, ys)
    beam_active, beam_feature, beam_trace = _active_beam_trace(beam)
    cases = [_space(kind, xs, ys, beam, shell_free, shell_scale, shell,
                    beam_active, beam_feature, beam_trace) for kind in KINDS]
    return {"classification": "one finite-grid positive trace-quotient development diagnostic; not inf-sup or G0B acceptance",
            "name": name,
            "model": (f"C1 35 mm Q4 x{shell_x_cells}/y{shell_y_cells}, "
                      f"native retained B3-{beam_half_cells}, two line intervals"),
            "metric": {"shell": "left-supported drilling-free physical E4 strain energy",
                       "beam": "section-weighted broken half-cell H1-like bottom-position/spatial-rotation trace quotient",
                       "bond_length_m": LENGTH_M,
                       "bond_width_m": WIDTH_M,
                       "multiplier": "basis-specific Neumann H^-1/2 density Gram; moment characteristic length 0.1 m",
                       "reference_stiffness_n_per_m": REFERENCE_STIFFNESS_N_PER_M},
            "grid": {"xs_m": xs.tolist(), "ys_m": ys.tolist(),
                     "beam_half_stations_m": beam.abscissae.tolist()},
            "fixture_contract": fixture,
            "shell_metric": {k:v for k,v in shell.items() if k != "factor"},
            "beam_trace_metric": {k:v for k,v in beam_trace.items() if k not in (
                "samples", "scale", "right_vectors", "singular_values")},
            "cases": cases,
            "limitations": ["positive quotient is on the observable B3 bond-trace quotient, not all retained mixed coordinates",
                            "broken trace does not impose continuity of retained half-cell rotations",
                            "one finite grid and fixed metric do not establish a mesh-uniform inf-sup bound or select a multiplier space",
                            "no external physical solve or loaded accuracy comparison"]}


def evaluate() -> dict:
    """Preserve the original fixed x4/y4, B3-12 experiment."""
    return _evaluate_case("fixed_mid_ratio", GRID_CELLS, GRID_CELLS,
                          BEAM_HALF_CELLS)


def evaluate_ratio_extremes() -> dict:
    """Only the two predeclared 1:8 and 8:1 C1 ratio endpoints."""
    results = [_evaluate_case(*case) for case in RATIO_EXTREMES]
    return {"classification": "two frozen-metric C1 extreme-ratio operator diagnostics; not inf-sup or G0B acceptance",
            "metric_identity": "same shell physical and B3 broken-half-cell trace formula, square-section weights, 0.1 m bond/width/characteristic length, and H^-1/2 multiplier Gram as fixed-mid-ratio v4",
            "ratios": results,
            "limitations": ["two finite endpoints do not establish a mesh-uniform bound or select P0/P1/dual",
                            "positive B3 metric acts on its observable trace quotient, not all retained mixed coordinates",
                            "no external or loaded solve"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--ratio-extremes", action="store_true",
                        help="evaluate only the two registered C1 ratio endpoints")
    args = parser.parse_args()
    root = args.evidence_root.resolve()
    if root.exists():
        raise FileExistsError("development evidence root already exists")
    script = Path(__file__).resolve()
    repo = script.parents[1]
    sources = [script, repo/"scripts/_b3_e4_f03_native_fixture.py",
               repo/"scripts/_b3_e4_f03_native_spatial_port.py",
               repo/"scripts/b3_e4_f03_distributed_surface_finite.py",
               repo/"scripts/b3_e4_f03_local_footprint_work.py",
               repo/"scripts/b3_e4_f03_plate_patch_work.py",
               repo/"scripts/b3_e4_f03_square_section_control.py",
               repo/"scripts/_b3_e4_f03_p0_dual_norm.py",
               repo/"scripts/_b3_e4_f03_p1_dual_norm.py",
               repo/"scripts/_b3_e4_f03_dual_linear_norm.py"]
    identity = {str(path.relative_to(repo)): _sha(path) for path in sources}
    head = subprocess.check_output(["git", "rev-parse", "HEAD"],
                                   cwd=repo, text=True).strip()
    manifest = {"git_head": head, "source_sha256": identity,
                "python": platform.python_version(), "numpy": np.__version__,
                "scipy": __import__("scipy").__version__,
                "parameters": {"mode": ("ratio_extremes" if args.ratio_extremes
                                        else "fixed_mid_ratio"),
                               "cases": ([list(case) for case in RATIO_EXTREMES]
                                         if args.ratio_extremes else
                                         [["fixed_mid_ratio", GRID_CELLS,
                                           GRID_CELLS, BEAM_HALF_CELLS]]),
                               "quadrature_order": GAUSS_ORDER,
                               "bond_length_m": LENGTH_M,
                               "moment_characteristic_length_m": LENGTH_M}}
    root.mkdir(parents=True, exist_ok=False)
    (root/"manifest.json").write_text(json.dumps(manifest, indent=2,
                                                 sort_keys=True)+"\n")
    try:
        result = (evaluate_ratio_extremes() if args.ratio_extremes
                  else evaluate())
    except Exception as error:
        (root/"failure.json").write_text(json.dumps({
            "status": "FAILED_CLOSED", "error_type": type(error).__name__,
            "message": str(error)}, indent=2, sort_keys=True)+"\n")
        raise
    (root/"result.json").write_text(json.dumps(result, indent=2,
                                               sort_keys=True)+"\n")
    reports = result["ratios"] if args.ratio_extremes else [result]
    print(json.dumps({"status": "COMPLETED_FINITE_GRID_DIAGNOSTIC",
                      "root": str(root),
                      "ratios": [{"name": report["name"],
                                  "shell_relative_min": report[
                                      "shell_metric"]["relative_min_eigenvalue"],
                                  "beam_trace_rank": report[
                                      "beam_trace_metric"]["trace_rank"],
                                  "spaces": [{"space": c["space"],
                                              "full_lower_bound": c["full"][
                                                  "quotient_lower_bound_from_upper_dual_gram"],
                                              "nonaxial_lower_bound": c[
                                                  "nonaxial"][
                                                      "quotient_lower_bound_from_upper_dual_gram"]}
                                             for c in report["cases"]]}
                                 for report in reports]}, sort_keys=True))


if __name__ == "__main__":
    main()
