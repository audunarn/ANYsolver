"""Matched 8x4x2 weak-P0 Mx C3D20 CalculiX development deck.

The row reduction is only an *EQUATION representation. The five physical
constraint rows per material support and the independently solved body are
unchanged. This is not a BL5/F03 qualification deck.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from scripts import r8_bl5_mx_matched_refinement_dev as matched
from scripts import r8_bl5_mx_coupled_shell_refinement_dev as shell_ref
from scripts import r8_bl5_mx_torsion_refinement_dev as beam_ref
from scripts import r8_bl5_weak_continuum_reference as continuum
from scripts import r8_bl5_released_director_reference as solid


LEVEL = (8, 4, 2)
INDEPENDENT_SHA256 = "69ac74e73dcc63e306aecdfb3d21b32088350905dcefddb4f9f0122e78a4feb3"
TORQUE_NM = 10.
ROW_FLOOR = 1e-14


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _node_at(model: dict, coordinate: tuple[float, float, float]) -> int:
    choices = [node for node in model["beam_nodes"]
               if max(abs(a-b) for a, b in zip(model["physical_nodes"][node], coordinate)) < 1e-14]
    if len(choices) != 1:
        raise ValueError("unique beam-side station node required")
    return choices[0]


def _rows_for_ccx(model: dict, c: np.ndarray, measure: np.ndarray) -> tuple[np.ndarray, np.ndarray, dict]:
    order, index, fixed, _, _ = continuum.layout(model)
    nx = LEVEL[0]
    dependent = np.array([
        index[_node_at(model, (edge/nx, 0., z))]+axis
        for edge in range(nx)
        for z, axes in ((.01, range(3)), (.07, range(2)))
        for axis in axes], dtype=int)
    if (c.shape != (5*nx, 3*len(order)) or measure.shape != (5*nx,) or
            len(set(dependent)) != 5*nx or any(slot in fixed for slot in dependent)):
        raise ValueError("complete unique non-SPC physical pivot set required")
    a = c[:, dependent]
    condition = float(np.linalg.cond(a))
    if not np.isfinite(condition) or condition > 1e10:
        raise ValueError("unresolved physical pivot conditioning")
    reduced = np.linalg.solve(a, c)
    reduced[:, dependent] = np.eye(5*nx)
    reduced[np.abs(reduced) < ROW_FLOOR] = 0.
    serialized = np.array([[float(f"{value:.17g}") for value in row]
                           for row in reduced])
    row_error = float(np.linalg.norm(a@serialized-c, ord=np.inf)/
                      max(np.linalg.norm(c, ord=np.inf), 1e-30))
    pivot_error = float(np.max(np.abs(serialized[:, dependent]-np.eye(5*nx))))
    if row_error > 1e-11 or pivot_error != 0.:
        raise ValueError("serialized CalculiX rows change the physical weak space")
    return serialized, dependent, {"physical_rows": 5*nx,
        "row_measures_m": measure.tolist(), "pivot_condition": condition,
        "row_relative_error": row_error, "pivot_error": pivot_error,
        "dependent_slots": dependent.tolist(),
        "physical_pivot_matrix": a.tolist(),
        "multiplier_transform": "lambda_physical=A^{-T} lambda_equation"}


def deck(independent: Path) -> tuple[bytes, dict]:
    if _sha(independent) != INDEPENDENT_SHA256:
        raise ValueError("exact matched independent 8x4x2 result required")
    prior = json.loads(independent.read_text(encoding="utf-8"))
    if (prior["status"] != "DEVELOPMENT_MATCHED_REFINEMENT_NOT_QUALIFIED" or
            tuple(prior["level"]) != LEVEL or prior["multiplier_rows"] != 40):
        raise ValueError("complete matched independent case required")
    shell_nodes, shell_elements = shell_ref._shell_mesh(*LEVEL)
    beam_nodes, beam_elements = beam_ref._mesh(*LEVEL)
    model = shell_ref._combined(shell_nodes, shell_elements, beam_nodes, beam_elements)
    c_sparse, measure = matched._weak_rows(model, LEVEL[0])
    c = c_sparse.toarray()
    equations, dependent, audit = _rows_for_ccx(model, c, measure)
    tip, tip_meta = beam_ref._port(beam_nodes, beam_elements, 1., LEVEL)
    order, index, fixed, _, _ = continuum.layout(model)
    load = np.zeros(3*len(order))
    load[-3*len(beam_nodes):] = tip.T @ np.array((0., 0., 0., TORQUE_NM, 0., 0.))
    load[np.abs(load) < 1e-12] = 0.
    positions = np.array([model["physical_nodes"][node] for node in order])
    from scripts.r8_bl5_mx_section_port_dev import _wrench
    wrench = _wrench(positions, load)
    if np.max(np.abs(wrench-np.array((0., 0., 0., TORQUE_NM, 0., 0.)))) > 1e-9:
        raise ValueError("serialized section-dual tip load changed physical wrench")
    lines = ["*HEADING", "R8_BL5_CCX_MATCHED_MX_8X4X2_DEV; not qualified", "*NODE"]
    lines += [str(node)+","+",".join(format(v, ".17g") for v in xyz)
              for node, xyz in model["physical_nodes"].items()]
    lines += ["*ELEMENT,TYPE=C3D20,ELSET=BODY"]
    for eid, ids in model["elements"].items():
        lines += [str(eid)+","+",".join(map(str, ids[:15])),
                  ",".join(map(str, ids[15:]))]
    for name, nodes in (("ALL", tuple(sorted(model["physical_nodes"]))),
                        ("ROOT", model["root_nodes"])):
        lines.append("*NSET,NSET="+name)
        lines += [",".join(map(str, nodes[j:j+16])) for j in range(0, len(nodes), 16)]
    lines += ["*MATERIAL,NAME=ELASTIC", "*ELASTIC", f"{solid.E:.17g},{solid.NU:.17g}",
              "*SOLID SECTION,ELSET=BODY,MATERIAL=ELASTIC",
              "*BOUNDARY", "ROOT,1,3,0."]
    for row, pivot in zip(equations, dependent):
        slots = [int(pivot)]+[j for j, value in enumerate(row)
                              if j != pivot and value != 0.]
        terms = [f"{order[slot//3]},{slot%3+1},{row[slot]:.17g}"
                 for slot in slots]
        lines += ["*EQUATION", str(len(terms))]
        lines += [",".join(terms[j:j+3]) for j in range(0, len(terms), 3)]
    lines += ["*STEP", "*STATIC", "1.,1.", "*CLOAD"]
    lines += [f"{order[slot//3]},{slot%3+1},{value:.17g}"
              for slot, value in enumerate(load) if value != 0.]
    lines += ["*NODE OUTPUT,DOUBLE,NSET=ALL", "U",
              "*NODE OUTPUT,DOUBLE,NSET=ROOT", "RF", "*END STEP"]
    payload = ("\n".join(lines)+"\n").encode("ascii")
    metadata = {"identity": "R8_BL5_CCX_MATCHED_MX_8X4X2_DEV_V1",
        "status": "PREPARED_NOT_EXECUTED", "level": LEVEL,
        "source_sha256": _sha(Path(__file__)),
        "independent_sha256": INDEPENDENT_SHA256,
        "physical_nodes": model["physical_nodes"], "elements": model["elements"],
        "root_nodes": model["root_nodes"], "shell_nodes": model["shell_nodes"],
        "beam_nodes": model["beam_nodes"], "shell_elements": model["shell_elements"],
        "beam_elements": model["beam_elements"],
        "tip_port": tip_meta, "tip_wrench_about_origin": wrench.tolist(),
        "physical_tip_load_N": load.tolist(),
        "equation_check": audit,
        "dependent_pivots": [(int(order[slot//3]), int(slot%3+1)) for slot in dependent],
        "deck_sha256": sha256(payload).hexdigest(),
        "interpretation": "exact five-channel P0 row space at 40 growing supports; work-conjugate section torque; development not F03"}
    return payload, metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--independent", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists():
        raise FileExistsError("preserve prior external preparation")
    payload, metadata = deck(args.independent)
    args.output_dir.mkdir(parents=True)
    (args.output_dir/"weak.inp").write_bytes(payload)
    (args.output_dir/"metadata.json").write_text(json.dumps(metadata, indent=2,
                                                  allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps({"status": metadata["status"], "nodes": len(metadata["physical_nodes"]),
                      "elements": len(metadata["elements"]),
                      "weak_rows": metadata["equation_check"]["physical_rows"],
                      "pivot_condition": metadata["equation_check"]["pivot_condition"],
                      "row_relative_error": metadata["equation_check"]["row_relative_error"],
                      "deck_sha256": metadata["deck_sha256"]}))


if __name__ == "__main__":
    main()
