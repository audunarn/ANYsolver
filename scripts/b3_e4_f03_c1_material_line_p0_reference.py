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

from scripts._b3_e4_f03_weak_line_candidate import LineMultiplierSpace
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


def integrated_selective_yaw_rows(coords, plate, bar):
    """P0 and exact yaw P1/dual rows in one common solid-face node order."""
    nodes, p0, ports = integrated_rows(coords, plate, bar)
    index = {node: k for k, node in enumerate(nodes)}
    candidates = {}
    for kind in ("continuous_linear", "dual_linear"):
        space = LineMultiplierSpace(kind, (0., .5, 1.))
        yaw = np.zeros((space.count, p0.shape[1]))
        for interval in ports:
            for weight, port in interval:
                station = (port.station_x_m-X_EDGES[0])/(X_EDGES[-1]-X_EDGES[0])
                values = space.values(station)
                for k, node in enumerate(port.node_ids):
                    yaw[:, 3*index[node]:3*index[node]+3] += (
                        weight*values[:, None]*port.gap_jacobian[5, 3*k:3*k+3])
        candidates[kind] = yaw
    return nodes, p0, candidates


def evaluate_selective_yaw_span() -> dict:
    """Count the extra solid action directions needed beyond saved P0 columns."""
    reconstruction = json.loads(RECON.read_text())
    if reconstruction["status"] != "EXPLORATORY_COMPLETE":
        raise ValueError("completed detached F4 reconstruction required")
    deck, meta, coords, _, _, _ = _source(SOURCE / "tip_mx")
    if digest(deck) != reconstruction["cases"]["tip_mx"]["source_deck_sha256"]:
        raise ValueError("detached source deck changed")
    plate, bar = _element_domain_nodes(deck)
    nodes, p0, candidates = integrated_selective_yaw_rows(coords, plate, bar)
    if set(nodes) & set(meta["boundary_node_ids"]):
        raise ValueError("material-line action overlaps saved supports")

    def rank(matrix):
        norms = np.linalg.norm(matrix, axis=1)
        if np.any(norms <= 0.):
            raise ArithmeticError("zero solid action row")
        normalized = matrix/norms[:, None]
        singular = np.linalg.svd(normalized, compute_uv=False)
        return int(np.sum(singular > 1e-10)), float(singular[-1])

    base_rank, _ = rank(p0)
    if base_rank != 24:
        raise ArithmeticError("saved P0 action rank changed")
    p1 = candidates["continuous_linear"]
    dual = candidates["dual_linear"]
    proposed = np.vstack((p0, p1[[0, 2]]))
    proposed_rank, _ = rank(proposed)
    combined = np.vstack((p0, p1, dual))
    combined_rank, _ = rank(combined)
    if proposed_rank != 26 or combined_rank != 26:
        raise ArithmeticError("two P1 endpoint actions do not span both yaw spaces")
    _, _, vt = np.linalg.svd(proposed, full_matrices=False)
    basis = vt[:proposed_rank]
    row_span_defects = {}
    for kind, rows in candidates.items():
        defects = np.linalg.norm(rows-(rows@basis.T)@basis, axis=1)
        row_span_defects[kind] = (defects/np.linalg.norm(rows, axis=1)).tolist()
    if max(max(values) for values in row_span_defects.values()) > 1e-10:
        raise ArithmeticError("proposed extra actions do not span yaw candidates")

    origin = np.array((.95, 0., .0175))
    node_coordinates = np.array([coords[node] for node in nodes])
    sample = np.array([[.01*np.sin(node), .02*np.cos(node),
                        .005*np.sin(2*node)] for node in nodes])
    actions = []
    for yaw_index in (0, 2):
        row = p1[yaw_index]
        nodal = row.reshape(-1, 3)
        force = np.sum(nodal, axis=0)
        moment = np.sum(np.cross(node_coordinates-origin, nodal), axis=0)
        plate_force = np.sum([nodal[i] for i, node in enumerate(nodes)
                              if node in plate], axis=0)
        bar_force = np.sum([nodal[i] for i, node in enumerate(nodes)
                            if node in bar], axis=0)
        work_defect = abs(float(row@sample.ravel()-np.sum(nodal*sample)))
        result = {
            "p1_yaw_index": yaw_index,
            "row_norm": float(np.linalg.norm(row)),
            "global_force_norm_n_per_unit_dual": float(np.linalg.norm(force)),
            "global_moment_norm_nm_per_unit_dual": float(np.linalg.norm(moment)),
            "side_force_norm_n_per_unit_dual": float(np.linalg.norm(plate_force+bar_force)),
            "transpose_work_defect_j_per_unit_dual": work_defect,
        }
        if max(result[key] for key in (
                "global_force_norm_n_per_unit_dual",
                "global_moment_norm_nm_per_unit_dual",
                "side_force_norm_n_per_unit_dual",
                "transpose_work_defect_j_per_unit_dual")) > 1e-10:
            raise ArithmeticError("extra solid action loses balance or work")
        actions.append(result)
    return {
        "status": "DEVELOPMENT_SPAN_PREFLIGHT_PASSED",
        "classification": "same detached solid geometry; exact selective-yaw action span only",
        "source_deck_sha256": digest(deck),
        "reference_reconstruction_sha256": digest(RECON),
        "p0_row_count": len(p0),
        "p0_rank": base_rank,
        "p1_yaw_row_count": len(p1),
        "dual_yaw_row_count": len(dual),
        "p0_plus_p1_rank": rank(np.vstack((p0, p1)))[0],
        "p0_plus_dual_rank": rank(np.vstack((p0, dual)))[0],
        "combined_rank": combined_rank,
        "proposed_extra_p1_yaw_indices": [0, 2],
        "proposed_basis_rank": proposed_rank,
        "candidate_row_relative_span_defects": row_span_defects,
        "proposed_extra_actions": actions,
        "active_face_nodes": len(nodes),
        "limitations": [
            "fixed solid face grid only; no growing-space or mesh-ratio claim",
            "span does not supply unexecuted external displacement fields",
            "no loaded P1/dual reference, F03/G0B acceptance, or multiplier selection",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--selective-yaw-span", action="store_true")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("preserve prior action preflight")
    result = (evaluate_selective_yaw_span() if args.selective_yaw_span
              else evaluate())
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True,
                                      allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps({"status": result["status"],
                      "rows": result.get("row_count", result.get("proposed_basis_rank")),
                      "rank": result.get("row_rank", result.get("combined_rank")),
                      "output": str(args.output)}))


if __name__ == "__main__":
    main()
