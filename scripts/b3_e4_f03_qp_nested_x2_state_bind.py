"""Bind the preparatory Q6 h screen to its saved physical states.

The band oracle reconstructs cell polynomials independently of the trace
adjoint. Functional regeneration still shares the candidate conversion code;
that limitation is explicit in the result and does not close F03/G0B.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from scripts._b3_e4_f03_conforming_qp_trace import FinitePadQpTrace
from scripts._b3_e4_f03_primal_ritz import F0, U0, YAW_LENGTH, SECTION
from scripts._b3_e4_f03_qp_functional_conversion import NORMALIZATION
from scripts._b3_e4_f03_qp_piecewise_functional import comparison, norm_squared
from scripts._b3_e4_f03_qp_piecewise_moment_oracle import PiecewisePadMomentOracle
from scripts._b3_e4_f03_qp_precise_functional import from_qp_recovery_precise
from scripts._b3_e4_f03_qp_subulp_density import exact_endpoint_resultant
from scripts.b3_e4_f03_qp_nested_x_pilot import BANDS, refined_x, refined_x2
from scripts.b3_e4_f03_qp_nested_x_band_oracle import _density


WRENCH_SCALE = np.array((F0, F0, F0 * YAW_LENGTH))
POSE_SCALE = np.array((U0, U0, U0 / YAW_LENGTH))


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _max_scaled(actual, expected, scale):
    return float(np.max(np.abs(np.asarray(actual)-np.asarray(expected))/scale))


def _atom_wrench(atom, station, trace):
    mx = sum(x for x, _ in trace.offsets)/len(trace.offsets)
    my = sum(y for _, y in trace.offsets)/len(trace.offsets)
    geometric_j = sum(x*x+y*y+2*trace.a**2/3 for x, y in
                      trace.offsets)/len(trace.offsets)
    gamma = geometric_j/trace.j
    return np.array((atom[0], atom[1],
        (station+mx)*atom[1]-my*atom[0]+gamma*atom[2]))


def _all_bands(oracle, coefficients, trace, atoms):
    """Integrate the union partition once per rule; add each terminal atom once."""
    events = set(trace.station_breakpoints())
    for a, b in BANDS:
        events.update((a, b))
    intervals = sorted(events)
    mx = sum(x for x, _ in trace.offsets)/len(trace.offsets)
    my = sum(y for _, y in trace.offsets)/len(trace.offsets)
    geometric_j = sum(x*x+y*y+2*trace.a**2/3 for x, y in
                      trace.offsets)/len(trace.offsets)
    gamma = geometric_j/trace.j
    rules = {}
    for order in (48, 64):
        roots, weights = np.polynomial.legendre.leggauss(order)
        pieces = []
        for a, b in zip(intervals, intervals[1:]):
            if b <= a:
                raise ArithmeticError("nonpositive station interval")
            stations = (a+b)/2+(b-a)*roots/2
            density = np.array([_density(oracle, coefficients, s)
                                for s in stations])
            w = weights*(b-a)/2
            pieces.append(np.array((w@density[:, 0], w@density[:, 1],
                w@(stations*density[:, 1]+mx*density[:, 1]
                   -my*density[:, 0]+gamma*density[:, 2]))))
        rules[order] = np.array(pieces)
    rows = []
    for a, b in BANDS:
        i, j = intervals.index(a), intervals.index(b)
        line48 = np.sum(rules[48][i:j], axis=0)
        line64 = np.sum(rules[64][i:j], axis=0)
        total = line64.copy()
        if a == 0:
            total += _atom_wrench(atoms[0], 0., trace)
        if b == 1:
            total += _atom_wrench(atoms[1], 1., trace)
        rows.append({"left": a, "right": b,
                     "line_only": line64.tolist(), "total": total.tolist(),
                     "quadrature_gap_scaled":
                         _max_scaled(line48, line64, WRENCH_SCALE)})
    return rows


def _case(trace, q, eta, signed, source, record=None):
    if q.shape != (2*trace.n,) or eta.shape != (3,) or not (
            np.isfinite(q).all() and np.isfinite(eta).all()):
        raise ValueError("invalid saved state")
    if not np.all(q[np.setdiff1d(np.arange(len(q)), trace.free_columns)] == 0):
        raise ValueError("fixed coordinates changed")
    if _max_scaled(eta, signed["eta"], WRENCH_SCALE) != 0:
        raise ValueError("stored multiplier and signed output differ")
    oracle = PiecewisePadMomentOracle(trace.p, x=trace.x, y=trace.y,
        offsets=trace.offsets, halfwidth=trace.a, j=trace.j)
    coefficients = oracle.coefficients(q)
    root = np.array((SECTION[0,0]*oracle.evaluate(coefficients, 0.)[1][0],
        0., 0.))
    for station, side, vector in ((0., "right", root),):
        pose, first, _ = oracle.evaluate(coefficients, station, side=side)
        vector[1] = SECTION[2,2]*(first[1]-pose[2])
        vector[2] = SECTION[1,1]*first[2]
    pose_tip, first_tip, _ = oracle.evaluate(coefficients, 1., side="left")
    tip = np.array((SECTION[0,0]*first_tip[0],
        SECTION[2,2]*(first_tip[1]-pose_tip[2]),
        SECTION[1,1]*first_tip[2]))
    atoms = (root-eta, -tip)
    exact_root = exact_endpoint_resultant(oracle, coefficients, 0.)
    exact_tip = exact_endpoint_resultant(oracle, coefficients, 1.)
    checks = {
        "root_section_scaled": _max_scaled(root, signed["root_section"], WRENCH_SCALE),
        "tip_section_scaled": _max_scaled(tip, signed["tip_section"], WRENCH_SCALE),
        "root_atom_scaled": _max_scaled(atoms[0], signed["root_atom"], WRENCH_SCALE),
        "tip_atom_scaled": _max_scaled(atoms[1], signed["tip_atom"], WRENCH_SCALE),
        "exact_root_scaled": _max_scaled(exact_root, root, WRENCH_SCALE),
        "exact_tip_scaled": _max_scaled(exact_tip, tip, WRENCH_SCALE),
        "tip_pose_scaled": _max_scaled(pose_tip, signed["tip_pose"], POSE_SCALE),
    }
    bands = _all_bands(oracle, coefficients, trace, atoms)
    for i, band in enumerate(bands):
        band["saved_total_gap_scaled"] = _max_scaled(
            band["total"], signed["bands"][i], WRENCH_SCALE)
    checks["band_total_scaled"] = max(r["saved_total_gap_scaled"] for r in bands)
    checks["band_48_64_scaled"] = max(r["quadrature_gap_scaled"] for r in bands)
    checks["quarter_partition_scaled"] = _max_scaled(
        np.sum([r["total"] for r in bands[:4]], axis=0),
        signed["line_wrench"], WRENCH_SCALE)
    checks["global_wrench_scaled"] = _max_scaled(
        np.sum([r["total"] for r in bands[:4]], axis=0),
        np.array((0., F0, F0/2))-eta, WRENCH_SCALE)
    precise = from_qp_recovery_precise(trace, q, eta)
    functional = precise.functional
    # Binary64 Gauss points cannot enter a one-ulp station interval. Bound
    # its entire physical wrench from the independently nodal-checked Decimal
    # coefficient row instead of treating 48/64 agreement as an interior test.
    mx = sum(x for x, _ in trace.offsets)/len(trace.offsets)
    my = sum(y for _, y in trace.offsets)/len(trace.offsets)
    geometric_j = sum(x*x+y*y+2*trace.a**2/3 for x, y in
                      trace.offsets)/len(trace.offsets)
    gamma = geometric_j/trace.j
    subulp_bound = np.zeros(3)
    for i in precise.repaired_indices:
        left, right = functional.breaks[i:i+2]
        width = right-left
        amplitude = np.sum(np.abs(functional.coefficients[i]), axis=0)+\
            np.abs(functional.cosine)
        subulp_bound += width*np.array((amplitude[0], amplitude[1],
            (1+abs(mx))*amplitude[1]+abs(my)*amplitude[0]
            +abs(gamma)*amplitude[2]))
    checks["subulp_total_wrench_bound_scaled"] = float(np.max(
        subulp_bound/WRENCH_SCALE))
    if record is not None:
        stored = record["functional"]
        checks["functional_coefficients_scaled"] = _max_scaled(
            functional.coefficients, stored["coefficients"], NORMALIZATION)
        checks["functional_atoms_scaled"] = _max_scaled(
            functional.atoms, stored["atoms"], NORMALIZATION)
        checks["functional_cosine_scaled"] = _max_scaled(
            functional.cosine, stored["cosine"], NORMALIZATION)
        if functional.breaks.tolist() != stored["breaks"]:
            raise ArithmeticError("functional breakpoints differ")
    norm = norm_squared(functional)
    checks["functional_norm_scaled"] = abs(np.sqrt(norm.squared_total)-(
        record["functional_norm_n"] if record is not None else
        np.sqrt(norm.squared_total)))/F0
    if max(checks.values()) > 2e-10:
        raise ArithmeticError(f"state binding failed: {checks}")
    return {"source_sha256": _sha(source),
            "q_sha256": hashlib.sha256(q.tobytes()).hexdigest(),
            "eta_sha256": hashlib.sha256(eta.tobytes()).hexdigest(),
            "x_hex": [x.hex() for x in trace.x],
            "station_intervals": len(trace.station_intervals()),
            "physical_coordinates": len(q),
            "free_coordinates": len(trace.free_columns),
            "checks": checks, "bands": bands,
            "functional_norm_n": float(np.sqrt(norm.squared_total))}, functional


def run(default_state, default_scalars, x1_path, x2_path, adjudication):
    scalars = json.loads(Path(default_scalars).read_text(encoding="utf-8"))
    x1 = json.loads(Path(x1_path).read_text(encoding="utf-8"))
    x2 = json.loads(Path(x2_path).read_text(encoding="utf-8"))
    target = json.loads(Path(adjudication).read_text(encoding="utf-8"))
    traces = (FinitePadQpTrace(6), FinitePadQpTrace(6, x=refined_x()),
              FinitePadQpTrace(6, x=refined_x2()))
    with np.load(default_state) as state:
        q0, eta0 = state["q"].copy(), state["eta"].copy()
    rows, functionals = [], []
    for trace, q, eta, signed, source, record in (
        (traces[0], q0, eta0, scalars["cases"]["6"], default_state, None),
        *((trace, None, np.asarray(rec["root_multiplier"]), rec["signed"],
           path, rec) for trace, rec, path in
          ((traces[1], x1, x1_path), (traces[2], x2, x2_path)))):
        if record is not None:
            if (record["x_hex"] != [v.hex() for v in trace.x] or
                    record["y_hex"] != [v.hex() for v in trace.y]):
                raise ValueError("saved grid differs")
            free = np.asarray(record["free_state"], dtype=float)
            if hashlib.sha256(free.tobytes()).hexdigest() != record["free_state_sha256"]:
                raise ValueError("saved state hash differs")
            q = np.zeros(2*trace.n)
            q[trace.free_columns] = free
        row, functional = _case(trace, q, eta, signed, source, record)
        rows.append(row)
        functionals.append(functional)
    pairs = [comparison(functionals[i], functionals[i+1]) for i in (0, 1)]
    distances = [float(np.sqrt(pair[2].squared_total)) for pair in pairs]
    expected = target["functional"]["differences_n"]
    gap = _max_scaled(distances, expected, F0)
    if gap > 2e-10:
        raise ArithmeticError("regenerated Green pair distances differ")
    return {"status": "UNREGISTERED_Q6_X0_X1_X2_STATE_BINDING",
            "qualification_status": "F03_G0B_OPEN",
            "method_limit": "Functional conversion shares candidate code; all band wrenches use independent cell-polynomial quadrature.",
            "inputs": {str(path): _sha(path) for path in
                       (default_state, default_scalars, x1_path,
                        x2_path, adjudication)},
            "cases": rows, "green_distances_n": distances,
            "green_distance_gap_scaled": gap}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("default_state", "default_scalars", "x1_state", "x2_state",
                 "adjudication", "output"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    result = run(args.default_state, args.default_scalars, args.x1_state,
                 args.x2_state, args.adjudication)
    args.output.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"green_distances_n": result["green_distances_n"],
        "maximum_case_defects": [max(case["checks"].values()) for case in
                                 result["cases"]]}))


if __name__ == "__main__":
    main()
