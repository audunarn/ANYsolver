"""Bounded target-only S3 compliance discriminator for the D1 two-body case.

This uses the actual target structural stiffness and three identical physical
unit-total affine traction fields on each target mesh. It does not evaluate
contact or establish a continuum reference.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

import numpy as np
from scipy.sparse.linalg import splu

import anysolver
from anysolver.matrix_assembly import assemble_stiffness_matrix
from docs.d1_review_support.d1_two_body_reference_oracle import (
    _clip, _source_shape, _target_shape, _triangle_quadrature,
)
from docs.d1_review_support.d1_two_body_refined_target_route import build_refined_case


AFFINE_PROFILES = ("uniform", "free_edge_x", "upper_rim_y")


def force_and_moments(model, target_nodes, rhs):
    target_z = np.asarray([model.mesh.dof_manager.get_node_dofs(node)[2]
                           for node in target_nodes], dtype=int)
    points = np.asarray([(model.mesh.nodes[node].x,
                          model.mesh.nodes[node].y) for node in target_nodes])
    totals = np.sum(rhs[target_z], axis=0)
    moments = np.stack((points[:, 0] @ rhs[target_z],
                        points[:, 1] @ rhs[target_z]), axis=1)
    return totals, moments


def load_fields(model, target_ids, target_nodes):
    rhs = np.zeros((model.mesh.dof_manager.total_dofs, len(AFFINE_PROFILES)))
    exact_shape_mass = np.eye(3)+np.ones((3, 3))
    for element_id in target_ids:
        element = model.mesh.elements[element_id]
        nodes = element.node_ids
        xy = np.asarray([(model.mesh.nodes[node].x,
                          model.mesh.nodes[node].y) for node in nodes])
        area = 0.5*abs(float(np.linalg.det(np.stack((xy[1]-xy[0],
                                                    xy[2]-xy[0])))))
        if area <= 0:
            raise AssertionError("invalid target S3 area")
        values = np.column_stack((np.ones(3),
                                  2.0*xy[:, 0]/1.3,
                                  2.0*xy[:, 1]))
        nodal_forces = (area/12.0)*exact_shape_mass @ values
        for local, node in enumerate(nodes):
            rhs[model.mesh.dof_manager.get_node_dofs(node)[2]] += (
                nodal_forces[local]
            )
    totals, _moments = force_and_moments(model, target_nodes, rhs)
    if np.any(totals <= 0.0):
        raise AssertionError("nonpositive physical traction resultant")
    rhs /= totals[None, :]
    return rhs


def contact_shaped_load(model, definition, target_nodes, pressure_by_node):
    """Map one fixed reference-XY source Q1 pressure into target P1 work."""
    rhs = np.zeros((model.mesh.dof_manager.total_dofs, 1))
    for source_id in definition.surfaces[0].element_ids:
        source_element = model.mesh.elements[source_id]
        source_xy = np.asarray([(model.mesh.nodes[node].x,
                                 model.mesh.nodes[node].y)
                                for node in source_element.node_ids])
        source_pressure = np.asarray([pressure_by_node[node]
                                      for node in source_element.node_ids])
        for target_id in definition.surfaces[1].element_ids:
            target_element = model.mesh.elements[target_id]
            target_xy = np.asarray([(model.mesh.nodes[node].x,
                                     model.mesh.nodes[node].y)
                                    for node in target_element.node_ids])
            polygon = _clip(source_xy, target_xy)
            for fan in range(1, len(polygon)-1):
                triangle = polygon[[0, fan, fan+1]]
                for point, weight in _triangle_quadrature(triangle):
                    pressure = float(_source_shape(point, source_xy)
                                     @ source_pressure)
                    if pressure < -1e-13:
                        raise AssertionError("negative reconstructed pressure")
                    target_shape = _target_shape(point, target_xy)
                    for local, node in enumerate(target_element.node_ids):
                        rhs[model.mesh.dof_manager.get_node_dofs(node)[2], 0] += (
                            weight*pressure*target_shape[local]
                        )
    totals, _moments = force_and_moments(model, target_nodes, rhs)
    if totals[0] <= 0.0:
        raise AssertionError("nonpositive contact-shaped resultant")
    raw_resultant = float(totals[0])
    rhs /= raw_resultant
    return rhs, raw_resultant


def one_mesh(x_cells, y_cells, pressure_by_node=None):
    started = time.perf_counter()
    model, definition, _settings, _program, x_knots, y_knots = (
        build_refined_case(4, x_cells, y_cells)
    )
    model.apply_boundary_conditions()
    stiffness, _info = assemble_stiffness_matrix(model)
    target_ids = definition.surfaces[1].element_ids
    target_nodes = sorted({node for eid in target_ids
                           for node in model.mesh.elements[eid].node_ids})
    source_nodes = sorted({node for eid in definition.surfaces[0].element_ids
                           for node in model.mesh.elements[eid].node_ids})
    source_dofs = [dof for node in source_nodes
                   for dof in model.mesh.dof_manager.get_node_dofs(node)]
    target_dofs = [dof for node in target_nodes
                   for dof in model.mesh.dof_manager.get_node_dofs(node)]
    if stiffness[source_dofs, :][:, target_dofs].nnz:
        raise AssertionError("target-only structural stiffness couples to source")
    free = np.asarray([dof for node in target_nodes
                       if abs(model.mesh.nodes[node].x) > 1e-14
                       for dof in model.mesh.dof_manager.get_node_dofs(node)],
                      dtype=int)
    matrix = stiffness[free, :][:, free].tocsc()
    asymmetry = matrix-matrix.T
    asymmetry_relative = float(np.linalg.norm(asymmetry.data)
                               /max(np.linalg.norm(matrix.data), 1e-30))
    factor = splu(matrix)
    names = list(AFFINE_PROFILES)
    rhs = load_fields(model, target_ids, target_nodes)
    raw_contact_resultant = None
    if pressure_by_node is not None:
        contact_rhs, raw_contact_resultant = contact_shaped_load(
            model, definition, target_nodes, pressure_by_node,
        )
        rhs = np.column_stack((rhs, contact_rhs))
        names.append("saved_contact_q1")
    totals, moments = force_and_moments(model, target_nodes, rhs)
    displacements = factor.solve(rhs[free])
    residuals = matrix @ displacements-rhs[free]
    compliance = np.sum(rhs[free]*displacements, axis=0)
    if np.any(compliance <= 0.0):
        raise AssertionError("target-only compliance is not positive")
    residual_relative = np.linalg.norm(residuals, axis=0) / np.maximum(
        np.linalg.norm(rhs[free], axis=0), 1e-30,
    )
    return {
        "target_cells": [x_cells, y_cells],
        "target_s3_faces": len(target_ids),
        "x_knots_m": x_knots.tolist(),
        "y_knots_m": y_knots.tolist(),
        "free_target_dofs": len(free),
        "target_stiffness_asymmetry_relative": asymmetry_relative,
        "total_force_n": dict(zip(names, totals.tolist(), strict=True)),
        "first_moment_x_nm": dict(zip(names, moments[:, 0].tolist(),
                                       strict=True)),
        "first_moment_y_nm": dict(zip(names, moments[:, 1].tolist(),
                                       strict=True)),
        "compliance_m_per_n": dict(zip(names, compliance.tolist(),
                                        strict=True)),
        "linear_solve_relative_residual": dict(zip(
            names, residual_relative.tolist(), strict=True,
        )),
        "raw_contact_shaped_resultant_n": raw_contact_resultant,
        "elapsed_seconds": time.perf_counter()-started,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pressure-record", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output exists")
    pressure_by_node = None
    pressure_sha = None
    if args.pressure_record is not None:
        pressure_bytes = args.pressure_record.read_bytes()
        saved = json.loads(pressure_bytes)
        assert saved["status"] == "completed"
        assert saved["source_q4_faces"] == 4
        pressure_step = saved["steps"][-1]
        pressure_by_node = dict(zip(
            pressure_step["source_pressure_node_ids"],
            pressure_step["numerical_pressure_pa"], strict=True,
        ))
        assert len(pressure_by_node) == 10
        assert sum(value > 0.0 for value in pressure_by_node.values()) == 2
        pressure_sha = hashlib.sha256(pressure_bytes).hexdigest()
    cases = [one_mesh(x_cells, y_cells, pressure_by_node)
             for x_cells, y_cells in ((2, 4), (4, 4), (8, 8), (16, 16))]
    names = list(AFFINE_PROFILES)
    if pressure_by_node is not None:
        names.append("saved_contact_q1")
    for name in names:
        totals = np.asarray([case["total_force_n"][name] for case in cases])
        first_x = np.asarray([case["first_moment_x_nm"][name]
                              for case in cases])
        first_y = np.asarray([case["first_moment_y_nm"][name]
                              for case in cases])
        assert np.max(abs(totals-1.0)) < 1e-12
        assert np.ptp(first_x) < 1e-12 and np.ptp(first_y) < 1e-12
    record = {
        "status": "development_target_only_structural_compliance",
        "source_commit": subprocess.check_output(
            ("git", "rev-parse", "HEAD"), text=True,
        ).strip(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "anysolver_module": str(Path(anysolver.__file__).resolve()),
        "profiles": names,
        "pressure_record_sha256": pressure_sha,
        "source_pressure_pa_by_node": pressure_by_node,
        "cases": cases,
    }
    args.output.write_text(json.dumps(record, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"status": record["status"],
                      "elapsed_seconds": [case["elapsed_seconds"]
                                          for case in cases]}, indent=2))


if __name__ == "__main__":
    main()
