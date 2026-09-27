"""Preflight an exact weak P0 material-line action on saved detached solid faces.

This prepares a law-matched external action basis, not a loaded solve or a
production multiplier selection. The four intervals are the current bounded
native comparison grid; each row is an exact three-point Gauss integral of
the independently constructed flat solid-side six-channel pose.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from scripts.b3_e4_f03_c1_material_line_solid_port import build_flat_solid_line_port
from scripts.b3_e4_f03_ccx_six_channel_compliance import _source
from scripts.b3_e4_f03_ccx_six_channel_preflight import _element_domain_nodes
from scripts.b3_e4_f03_ccx_solid_bond_screen import digest
from scripts.b3_e4_f03_c1_solid_trace_residual import RECON, SOURCE


X_EDGES = (.9, .925, .95, .975, 1.)


def integrated_rows(coords, plate, bar):
    roots, weights = np.polynomial.legendre.leggauss(3)
    point_ports = []
    for a, b in zip(X_EDGES[:-1], X_EDGES[1:]):
        point_ports.append(tuple(
            (float(weight)*(b-a)/2., build_flat_solid_line_port(
                coords, plate, bar, (a+b)/2.+float(root)*(b-a)/2.))
            for root, weight in zip(roots, weights)))
    nodes = tuple(sorted({node for interval in point_ports
                          for _, port in interval for node in port.node_ids}))
    index = {node: k for k, node in enumerate(nodes)}
    result = np.zeros((6*len(point_ports), 3*len(nodes)))
    for i, interval in enumerate(point_ports):
        for weight, port in interval:
            for k, node in enumerate(port.node_ids):
                result[6*i:6*i+6, 3*index[node]:3*index[node]+3] += (
                    weight*port.gap_jacobian[:, 3*k:3*k+3])
    result.setflags(write=False)
    return nodes, result, point_ports


def evaluate() -> dict:
    reconstruction = json.loads(RECON.read_text())
    if reconstruction["status"] != "EXPLORATORY_COMPLETE":
        raise ValueError("completed detached F4 reconstruction required")
    deck, meta, coords, _, _, _ = _source(SOURCE / "tip_mx")
    if digest(deck) != reconstruction["cases"]["tip_mx"]["source_deck_sha256"]:
        raise ValueError("detached source deck changed")
    plate, bar = _element_domain_nodes(deck)
    nodes, rows, ports = integrated_rows(coords, plate, bar)
    if set(nodes) & set(meta["boundary_node_ids"]):
        raise ValueError("material-line action overlaps saved supports")
    row_scale = np.linalg.norm(rows, axis=1)
    if np.any(row_scale <= 0.):
        raise ArithmeticError("zero material-line row")
    normalized = rows/row_scale[:, None]
    singular = np.linalg.svd(normalized, compute_uv=False)
    rank = int(np.sum(singular > 1e-10))
    if rank != rows.shape[0]:
        raise ArithmeticError("dependent P0 solid material-line action rows")
    center = np.array((.95, 0., .0175))
    maximum_rigid_gap = 0.
    for direction in np.eye(6):
        field = np.array([direction[:3]+np.cross(direction[3:], coords[node])
                          for node in nodes]).ravel()
        maximum_rigid_gap = max(maximum_rigid_gap,
                                float(np.max(np.abs(rows@field))))
    dual = np.arange(1., 1.+len(rows))
    force = (rows.T@dual).reshape(-1, 3)
    sample = np.array([[.01*np.sin(node), .02*np.cos(node),
                        .005*np.sin(2*node)] for node in nodes])
    work_defect = abs(float(np.sum(force*sample)-dual@(rows@sample.ravel())))
    total_force = np.sum(force, axis=0)
    total_moment = np.sum(np.cross(
        np.array([coords[node]-center for node in nodes]), force), axis=0)
    plate_force = sum((force[i] for i, node in enumerate(nodes) if node in plate),
                      np.zeros(3))
    bar_force = sum((force[i] for i, node in enumerate(nodes) if node in bar),
                    np.zeros(3))
    if (maximum_rigid_gap > 1e-10 or work_defect > 1e-10 or
            np.linalg.norm(total_force) > 1e-9 or
            np.linalg.norm(total_moment) > 1e-9 or
            np.linalg.norm(plate_force+bar_force) > 1e-9):
        raise ArithmeticError("integrated solid line work or balance failed")
    return {
        "status": "DEVELOPMENT_PREFLIGHT_PASSED",
        "classification": "bounded detached-solid exact weak P0 material-line action",
        "source_deck_sha256": digest(deck),
        "reference_reconstruction_sha256": digest(RECON),
        "x_edges_m": X_EDGES,
        "gauss_order": 3,
        "integrated_interval_lengths_m": [sum(weight for weight, _ in interval)
                                         for interval in ports],
        "active_face_nodes": len(nodes),
        "row_count": rows.shape[0],
        "row_rank": rank,
        "minimum_row_normalized_singular": float(singular[-1]),
        "maximum_integrated_common_rigid_gap": maximum_rigid_gap,
        "transpose_work_defect_j": work_defect,
        "global_force_imbalance_n": float(np.linalg.norm(total_force)),
        "global_moment_imbalance_nm": float(np.linalg.norm(total_moment)),
        "side_force_imbalance_n": float(np.linalg.norm(plate_force+bar_force)),
        "limitations": [
            "row-normalized singular values are algebraic rank diagnostics, not physical inf-sup measures",
            "P0 m4 is a bounded comparator, not a selected native multiplier policy",
            "no external action solve, loaded comparison, or contact qualification",
            "not F03 or G0B acceptance",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("preserve prior action preflight")
    result = evaluate()
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True,
                                      allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "rows": result["row_count"],
                      "rank": result["row_rank"], "output": str(args.output)}))


if __name__ == "__main__":
    main()
