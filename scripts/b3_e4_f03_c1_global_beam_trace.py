"""Fit supported solid bar faces to actual retained B3 open-half-cell traces.

The fit shares native nodal positions but retains independent one-sided cell
rotations. Q8-interpolated solid fields and physical six-channel action
densities are integrated on open faces, so no shared solid node is assigned
to an arbitrary internal B3 side. This is a one-grid diagnostic only.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path

import numpy as np

from scripts._b3_e4_f03_native_fixture import build
from scripts._b3_e4_f03_native_spatial_port import NativeHalfCellSpatialPort
from scripts.b3_e4_f03_c1_solid_trace_residual import (
    EVIDENCE, RECON, SCALES, SOURCE, _bound_field,
)
from scripts.b3_e4_f03_ccx_six_channel_compliance import _source
from scripts.b3_e4_f03_ccx_six_channel_preflight import _element_domain_nodes
from scripts.b3_e4_f03_ccx_solid_bond_screen import _quad8_shape, digest
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


def _skew(v):
    x, y, z = v
    return np.array(((0., -z, y), (z, 0., -x), (-y, x, 0.)))


def _surface_samples(coords, bar_nodes, beam):
    """One physical quadrature and actual native port map per face point."""
    lookup = defaultdict(list)
    for node in bar_nodes:
        lookup[tuple(np.round(coords[node], 9))].append(node)

    def face_node(x, y, z):
        found = lookup[tuple(np.round((x, y, z), 9))]
        if len(found) != 1:
            raise ValueError("missing or ambiguous solid bar face node")
        return found[0]

    roots, gauss = np.polynomial.legendre.leggauss(3)
    xs = np.linspace(.9, 1., 5)
    ys = np.linspace(-.05, .05, 9)
    reference = beam.context.initial.mechanical
    rows = []
    records = []
    for x0, x1 in zip(xs[:-1], xs[1:]):
        for y0, y1 in zip(ys[:-1], ys[1:]):
            xm, ym = (x0+x1)/2, (y0+y1)/2
            for z, z_rel, side in ((.0175, -.05, "bottom"),
                                   (.1175, .05, "top")):
                ids = (face_node(x0, y0, z), face_node(x1, y0, z),
                       face_node(x1, y1, z), face_node(x0, y1, z),
                       face_node(xm, y0, z), face_node(x1, ym, z),
                       face_node(xm, y1, z), face_node(x0, ym, z))
                for xi, wx in zip(roots, gauss):
                    x = xm+(x1-x0)*float(xi)/2
                    element, cell, fraction, _ = beam._locate(x)
                    port = NativeHalfCellSpatialPort(
                        beam.context, element, cell, fraction)
                    high, low, frame = port.pose_pair(reference)
                    axis = high+low
                    if (np.linalg.norm(axis-np.array((x, 0., .0675))) > 2e-9 or
                            np.linalg.norm(frame-np.eye(3)) > 2e-7):
                        raise ValueError("solid and native beam reference axes differ")
                    tangent = port.tangent(reference)
                    for eta, wy in zip(roots, gauss):
                        y = ym+(y1-y0)*float(eta)/2
                        shape = _quad8_shape(float(xi), float(eta))
                        area = (x1-x0)*(y1-y0)*float(wx*wy)/4
                        offset = np.array((0., y, z_rel))
                        row = tangent[:3]-_skew(offset)@tangent[3:]
                        rows.append(row)
                        records.append((ids, shape, area, y, side))
    matrix = np.vstack(rows)
    active = np.flatnonzero(np.linalg.norm(matrix, axis=0) > 1e-12)
    if not len(active):
        raise ArithmeticError("native terminal trace has no active coordinates")
    return matrix[:, active], active, records


def _action_density(records, dual):
    if dual.shape != (6,):
        raise ValueError("six physical work duals required")
    density = []
    area_total = 0.
    second_moment_y = .1**2/12
    for _, _, area, y, side in records:
        area_total += area
        if side == "bottom":
            value = (dual[0]-dual[5]*y/second_moment_y-dual[4]/.1,
                     dual[1], dual[2]+dual[3]*y/second_moment_y)
        else:
            value = (dual[4]/.1, 0., 0.)
        density.extend(np.asarray(value)*area/.01)
    if abs(area_total-.02) > 1e-12:
        raise ArithmeticError("two solid bar faces lost area")
    return np.asarray(density)


def _fit_case(matrix, records, state, dual):
    target = []
    weights = []
    for ids, shape, area, _, _ in records:
        target.extend(shape@np.array([state[node] for node in ids]))
        weights.extend((area,)*3)
    target = np.asarray(target)
    weights = np.asarray(weights)
    density = _action_density(records, dual)
    root = np.sqrt(weights)
    solution, _, rank, singular = np.linalg.lstsq(
        matrix*root[:, None], target*root, rcond=None)
    if rank != matrix.shape[1]:
        raise ArithmeticError("retained B3 terminal trace fit lost rank")
    fitted = matrix@solution
    rms = np.sqrt(np.sum(weights*(target-fitted)**2) /
                  (np.sum(weights)/3))
    actual_work = float(density@target)
    fitted_work = float(density@fitted)
    return {
        "trace_coordinate_count": matrix.shape[1],
        "trace_fit_rank": int(rank),
        "trace_fit_condition": float(singular[0]/singular[-1]),
        "face_quadrature_point_count": len(records),
        "face_rms_difference_m": float(rms),
        "actual_bar_interface_work_J": actual_work,
        "retained_b3_trace_interface_work_J": fitted_work,
        "outside_retained_b3_trace_work_J": actual_work-fitted_work,
    }


def evaluate() -> dict:
    recon = json.loads(RECON.read_text())
    if recon["status"] != "EXPLORATORY_COMPLETE":
        raise ValueError("completed solid reconstruction required")
    deck, _, coords, _, _, _ = _source(SOURCE / "tip_mx")
    _, bar_nodes = _element_domain_nodes(deck)
    beam = build(12, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um", assemble=False)
    matrix, active, records = _surface_samples(coords, bar_nodes, beam)
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
        result = _fit_case(matrix, records, state, dual)
        np.testing.assert_allclose(
            result["actual_bar_interface_work_J"],
            recon["cases"][label]["bar_interface_work_J"],
            rtol=2e-12, atol=1e-12)
        cases[label] = result
    return {
        "classification": "native retained B3 open-half-cell fit to supported solid bar faces; development diagnostic",
        "status": "EXPLORATORY_COMPLETE", "cases": cases,
        "active_native_coordinate_indices": active.tolist(),
        "inputs_sha256": {str(RECON): digest(RECON)},
        "source_sha256": digest(Path(__file__)),
        "limitations": ["bounded one-grid C1 linear no-contact solid reference",
                        "physical L2 face fit, not a coupled B3 equilibrium solve",
                        "signed work pairing is not an energy fraction or lower bound",
                        "no line-space selection or F03/G0B acceptance"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("preserve existing beam-fit result")
    report = evaluate()
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True,
                                      allow_nan=False) + "\n")
    print(json.dumps({key: value["outside_retained_b3_trace_work_J"]
                      for key, value in report["cases"].items()}, sort_keys=True))


if __name__ == "__main__":
    main()
