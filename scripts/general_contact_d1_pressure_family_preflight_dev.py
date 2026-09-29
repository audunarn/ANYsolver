"""Cheap contact-free screen for an interior multi-mode pressure fixture.

This selects a fixture for later coupled testing. It is not stability evidence.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
from dataclasses import replace

import numpy as np
from scipy import linalg

from anysolver import ContactPathNodalForce
from anysolver.assembly import build_constraint_transformation
from anysolver.general_contact.s3_patch_static import GeneralS3PatchManager
from anysolver.matrix_assembly import assemble_stiffness_matrix
from scripts.general_contact_d1_interior_press_dev import build_interior_press


def screen(columns: int, rows: int, slope: float,
           load_shape: str) -> dict:
    model, definition, settings, program = build_interior_press(
        force_n=0.04, reference_slope=slope, source_support="perimeter",
        source_columns=columns, source_rows=rows, target_columns=1,
        load_shape="interior_uniform", slide_body="target",
    )
    if load_shape == "four_lobe_dev":
        raw = {}
        stride = columns+1
        for row in range(1, rows):
            for column in range(1, columns):
                node = 1+row*stride+column
                x, y = column/columns, row/rows
                raw[node] = sum(np.exp(-((x-cx)**2+(y-cy)**2)
                                       /(2.0*0.11**2))
                                for cx in (0.25, 0.75)
                                for cy in (0.25, 0.75))
        total = float(sum(raw.values()))
        program = replace(program, nodal_forces=tuple(
            ContactPathNodalForce(node, "uz", (0.0, -0.04*weight/total))
            for node, weight in raw.items()
        ))
    elif load_shape != "interior_uniform":
        raise ValueError("unknown contact-free screen load shape")
    model.apply_boundary_conditions()
    stiffness, _ = assemble_stiffness_matrix(model)
    n_dof = model.mesh.dof_manager.total_dofs
    _, _, transform, offset, _, _ = build_constraint_transformation(
        stiffness, np.zeros(n_dof), model,
    )
    if np.max(np.abs(offset)) > 1.0e-12:
        raise ValueError("contact-free screen expects homogeneous supports")
    dof_manager = model.mesh.dof_manager
    force = np.zeros(n_dof)
    for term, value in zip(program.nodal_forces,
                           program.force_values_at(program.total_steps)):
        force[dof_manager.get_node_dofs(term.node_id)[2]] += value
    control = np.zeros((len(program.controls), n_dof))
    for row, item in enumerate(program.controls):
        for node, name, weight in item.terms:
            control[row, dof_manager.get_node_dofs(node)[0 if name == "ux" else 2]] += weight
    free_basis = linalg.null_space(np.asarray(control @ transform))
    admissible = transform @ free_basis
    reduced = np.asarray(admissible.T @ stiffness @ admissible)
    rhs = np.asarray(admissible.T @ force).reshape(-1)
    displacement = np.asarray(admissible @ linalg.solve(
        0.5*(reduced+reduced.T), rhs, assume_a="pos",
    )).reshape(-1)
    manager = GeneralS3PatchManager(model, definition, settings)
    source, target = manager._positions(displacement)
    geometry = manager.law.geometry.evaluate(source, target)
    node_ids = manager.law.source_node_ids
    stride = columns + 1
    interior = tuple(1 + row*stride + column
                     for row in range(1, rows) for column in range(1, columns))
    gaps = np.asarray(geometry.normalized_gap)
    selected = np.array([node_ids.index(node) for node in interior])
    interior_gaps = gaps[selected]
    min_gap = float(np.min(interior_gaps))
    # Counts ask whether the unconstrained shape presents several comparable
    # interior candidates; no positive-pressure or equilibrium claim is made.
    return {
        "source_q4_faces": columns*rows,
        "target_s3_faces": 2,
        "source_columns": columns, "source_rows": rows,
        "reference_slope": slope,
        "load_shape": load_shape,
        "interior_pressure_modes": len(selected),
        "contact_free_minimum_interior_weighted_gap_m": min_gap,
        "interior_gap_spread_m": float(np.max(interior_gaps)-min_gap),
        "interior_nodes_within_5um_of_minimum": int(np.count_nonzero(
            interior_gaps <= min_gap+5.0e-6)),
        "interior_nodes_within_20um_of_minimum": int(np.count_nonzero(
            interior_gaps <= min_gap+20.0e-6)),
        "interior_node_gaps_m": {str(node): float(gap) for node, gap in zip(
            interior, interior_gaps)},
        "maximum_absolute_structural_displacement_m": float(np.max(np.abs(displacement))),
    }


def main(output: Path) -> None:
    if output.exists():
        raise FileExistsError(output)
    cases = [screen(columns, rows, slope, load_shape)
             for columns, rows, slope, load_shape in (
                 (4, 4, 1.0e-4, "four_lobe_dev"),
                 (8, 4, 1.0e-4, "four_lobe_dev"),
                 (8, 8, 1.0e-4, "four_lobe_dev"),
             )]
    output.write_text(json.dumps({"cases": cases}, indent=2)+"\n",
                      encoding="utf-8")
    print(json.dumps([{
        "faces": item["source_q4_faces"], "slope": item["reference_slope"],
        "load_shape": item["load_shape"],
        "min_gap_um": item["contact_free_minimum_interior_weighted_gap_m"]*1e6,
        "spread_um": item["interior_gap_spread_m"]*1e6,
        "within_5um": item["interior_nodes_within_5um_of_minimum"],
        "within_20um": item["interior_nodes_within_20um_of_minimum"],
    } for item in cases]))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
