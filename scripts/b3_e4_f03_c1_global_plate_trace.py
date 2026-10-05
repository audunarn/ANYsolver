"""Project one supported solid joint field into a compatible Q4 patch trace.

The equal-node fit uses both physical plate faces over the bonded patch and
shared E4 nodal translations/directors. It is a bounded representation
diagnostic, not a solution of the native coupled model or an F03 acceptance.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path

import numpy as np

from scripts.b3_e4_f03_c1_solid_trace_residual import (
    EVIDENCE, RECON, SCALES, SOURCE, _bound_field, _side_work,
)
from scripts.b3_e4_f03_ccx_six_channel_compliance import _source
from scripts.b3_e4_f03_ccx_six_channel_preflight import _element_domain_nodes
from scripts.b3_e4_f03_ccx_solid_bond_screen import digest
from scripts.b3_e4_f03_local_footprint_work import structured_q4_point_shape


def _fit_e4_patch(coords, displacement, action_nodes):
    """Return one C0 Q4/director displacement field on the x4/y4 patch."""
    xs = np.linspace(.9, 1., 5)
    ys = np.linspace(-.05, .05, 5)
    sx = sorted({round(float(coords[node][0]), 9) for node in action_nodes})
    sy = sorted({round(float(coords[node][1]), 9) for node in action_nodes})
    if (len(sx) != 9 or len(sy) != 17 or
            not np.allclose(sx, np.linspace(.9, 1., 9), rtol=0, atol=1e-9) or
            not np.allclose(sy, np.linspace(-.05, .05, 17), rtol=0, atol=1e-9) or
            len(action_nodes) != 242):
        raise ValueError("solid face nodes do not match bounded Q8 patch")
    nodes = sorted(action_nodes)
    matrix = np.zeros((3*len(nodes), 5*len(xs)*len(ys)))
    observed = np.array([displacement[node] for node in nodes]).ravel()
    for k, node in enumerate(nodes):
        x, y, z = coords[node]
        if abs(abs(z)-.0175) > 1e-10:
            raise ValueError("action lies outside plate face pair")
        host, shape = structured_q4_point_shape(xs, ys, float(x), float(y))
        for index, value in zip(host, shape):
            base = 5*index
            matrix[3*k, base] += value
            matrix[3*k, base+4] += value*z
            matrix[3*k+1, base+1] += value
            matrix[3*k+1, base+3] -= value*z
            matrix[3*k+2, base+2] += value
    solution, _, rank, singular = np.linalg.lstsq(matrix, observed,
                                                   rcond=None)
    if rank != matrix.shape[1]:
        raise ArithmeticError("bounded Q4 trace fit lost rank")
    fitted_array = (matrix@solution).reshape(-1, 3)
    residual = fitted_array-observed.reshape(-1, 3)
    rms = np.sqrt(np.mean(np.sum(residual**2, axis=1)))
    return dict(zip(nodes, fitted_array)), {
        "patch_shell_node_count": len(xs)*len(ys),
        "solid_face_node_count": len(nodes),
        "fit_rank": int(rank),
        "fit_condition": float(singular[0]/singular[-1]),
        "q8_node_rms_difference_m": float(rms),
    }


def evaluate() -> dict:
    recon = json.loads(RECON.read_text())
    if recon["status"] != "EXPLORATORY_COMPLETE":
        raise ValueError("completed solid reconstruction required")
    deck, _, coords, rows, _, _ = _source(SOURCE / "tip_mx")
    plate_nodes, bar_nodes = _element_domain_nodes(deck)
    unit = [_bound_field(EVIDENCE / f"channel-{j}",
                         recon["unit_records"][j]["frd_sha256"])
            for j in range(6)]
    if any(set(field) != set(coords) for field in unit):
        raise ValueError("unit-action field topology changed")
    cases = {}
    for label in ("tip_mx", "tip_fz"):
        decks = list((SOURCE / label).glob("*.inp"))
        if (len(decks) != 1 or digest(decks[0]) !=
                recon["cases"][label]["source_deck_sha256"]):
            raise ValueError("source deck identity changed")
        base = _bound_field(SOURCE / label,
                            recon["cases"][label]["source_frd_sha256"])
        if set(base) != set(coords):
            raise ValueError("loaded field topology changed")
        dual = np.asarray(recon["cases"][label]["dual_physical"])
        multiplier = dual/SCALES
        state = {node: base[node]-sum(multiplier[j]*unit[j][node]
                                      for j in range(6))
                 for node in coords}
        forces = defaultdict(lambda: np.zeros(3))
        for j, row in enumerate(rows):
            for (node, axis), value in row.items():
                forces[node][axis] -= dual[j]*value
        plate_force = {node: force for node, force in forces.items()
                       if node in plate_nodes}
        if len(plate_force)+sum(node in bar_nodes for node in forces) != len(forces):
            raise ValueError("unowned interface action")
        fit, details = _fit_e4_patch(coords, state, set(plate_force))
        actual = _side_work(plate_force, state)
        fitted = _side_work(plate_force, fit)
        np.testing.assert_allclose(actual,
                                   recon["cases"][label]["plate_interface_work_J"],
                                   rtol=2e-12, atol=1e-12)
        cases[label] = {**details, "actual_plate_interface_work_J": actual,
                        "q4_compatible_plate_interface_work_J": fitted,
                        "outside_q4_trace_work_J": actual-fitted}
    return {
        "classification": "globally C0 Q4 plate-patch fit to supported solid field; development diagnostic",
        "status": "EXPLORATORY_COMPLETE", "cases": cases,
        "inputs_sha256": {str(RECON): digest(RECON)},
        "source_sha256": digest(Path(__file__)),
        "limitations": ["bounded x4/y4 plate patch, not a full coupled E4/B3 projection",
                        "equal-Q8-node least-squares fit is a diagnostic choice, not a physical L2 projection",
                        "one linear no-contact solid grid; no F03/G0B acceptance"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("preserve existing plate-fit result")
    report = evaluate()
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True,
                                      allow_nan=False) + "\n")
    print(json.dumps({key: value["outside_q4_trace_work_J"]
                      for key, value in report["cases"].items()}, sort_keys=True))


if __name__ == "__main__":
    main()
