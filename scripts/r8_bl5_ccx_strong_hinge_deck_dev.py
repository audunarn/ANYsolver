"""Pinned 8x4x2 C3D20 sampled five-channel line-hinge Fy/Mx decks.

This is a development continuum proxy. Station constraints are not an exact
native E4-PL material-director trace or an F03 acceptance result.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from scripts import r8_bl5_strong_hinge_pair_dev as pair
from scripts import r8_bl5_mx_coupled_shell_refinement_dev as shell_ref
from scripts import r8_bl5_mx_torsion_refinement_dev as beam_ref
from scripts import r8_bl5_weak_continuum_reference as continuum
from scripts import r8_bl5_released_director_reference as solid
from scripts.r8_bl5_mx_section_port_dev import _wrench


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _node_at(model: dict, xyz: tuple[float, float, float]) -> int:
    found = [n for n in model["beam_nodes"]
             if max(abs(a-b) for a, b in zip(model["physical_nodes"][n], xyz)) < 1e-14]
    if len(found) != 1:
        raise ValueError("one beam-side station pivot required")
    return found[0]


def _equations(model: dict, c: np.ndarray) -> tuple[np.ndarray, np.ndarray, dict]:
    order, index, fixed, _, _ = continuum.layout(model)
    stations = pair.LEVEL[0] + 1
    # Physical constraints are channel-major; choose matching channel-major
    # beam-side pivots, with all three bottom translations and two top shifts.
    pivot = np.array([
        index[_node_at(model, (j/(stations-1), 0., .01 if channel < 3 else .07))]
        + (channel if channel < 3 else channel-3)
        for channel in range(5) for j in range(stations)], dtype=int)
    if (c.shape != (5*stations, 3*len(order)) or len(set(pivot)) != len(pivot)
            or any(slot in fixed for slot in pivot)):
        raise ValueError("complete unique non-SPC physical pivots required")
    a = c[:, pivot]
    condition = float(np.linalg.cond(a))
    if not np.isfinite(condition) or condition > 1e10:
        raise ValueError("unresolved strong-row pivot conditioning")
    rows = np.linalg.solve(a, c)
    rows[:, pivot] = np.eye(len(pivot))
    rows[np.abs(rows) < 1e-14] = 0.
    encoded = np.array([[float(f"{v:.17g}") for v in row] for row in rows])
    error = float(np.linalg.norm(a@encoded-c, ord=np.inf)
                  / max(np.linalg.norm(c, ord=np.inf), 1e-30))
    if error > 1e-11 or np.max(abs(encoded[:, pivot]-np.eye(len(pivot)))) != 0.:
        raise ValueError("serialized equations change physical strong row space")
    return encoded, pivot, {"physical_rows": len(pivot),
        "pivot_condition": condition, "row_relative_error": error,
        "dependent_slots": pivot.tolist(), "physical_pivot_matrix": a.tolist(),
        "multiplier_transform": "lambda_physical=A^{-T} lambda_equation"}


def decks(independent: Path) -> tuple[dict[str, bytes], dict]:
    source = json.loads(independent.read_text(encoding="utf-8"))
    if (source["status"] != "DEVELOPMENT_REFERENCE_DESIGN_NOT_QUALIFIED"
            or tuple(source["level"]) != pair.LEVEL):
        raise ValueError("exact complete same-body design result required")
    shell_nodes, shell_elements = shell_ref._shell_mesh(*pair.LEVEL)
    beam_nodes, beam_elements = beam_ref._mesh(*pair.LEVEL)
    model = shell_ref._combined(shell_nodes, shell_elements, beam_nodes, beam_elements)
    c = pair._strong_rows(model, pair.LEVEL[0]+1).toarray()
    equations, dependent, audit = _equations(model, c)
    tip, tip_meta = beam_ref._port(beam_nodes, beam_elements, 1., pair.LEVEL)
    order, _, _, _, _ = continuum.layout(model)
    position = np.array([model["physical_nodes"][n] for n in order])
    common = ["*HEADING", "R8_BL5_CCX_STRONG_HINGE_8X4X2_DEV; not qualified", "*NODE"]
    common += [str(n)+","+",".join(f"{v:.17g}" for v in xyz)
               for n, xyz in model["physical_nodes"].items()]
    common += ["*ELEMENT,TYPE=C3D20,ELSET=BODY"]
    for eid, ids in model["elements"].items():
        common += [str(eid)+","+",".join(map(str,ids[:15])), ",".join(map(str,ids[15:]))]
    for name, nodes in (("ALL", tuple(sorted(model["physical_nodes"]))),
                        ("ROOT", model["root_nodes"])):
        common.append("*NSET,NSET="+name)
        common += [",".join(map(str,nodes[j:j+16])) for j in range(0,len(nodes),16)]
    common += ["*MATERIAL,NAME=ELASTIC", "*ELASTIC", f"{solid.E:.17g},{solid.NU:.17g}",
               "*SOLID SECTION,ELSET=BODY,MATERIAL=ELASTIC", "*BOUNDARY", "ROOT,1,3,0."]
    for row, pivot in zip(equations, dependent):
        slots = [int(pivot)] + [j for j,v in enumerate(row) if j != pivot and v != 0.]
        terms = [f"{order[s//3]},{s%3+1},{row[s]:.17g}" for s in slots]
        common += ["*EQUATION", str(len(terms))]
        common += [",".join(terms[j:j+3]) for j in range(0,len(terms),3)]
    payloads = {}
    cases = {}
    for name, action in (("fy", np.array((0.,100.,0.,0.,0.,0.))),
                         ("mx", np.array((0.,0.,0.,10.,0.,0.)))):
        load = np.zeros(3*len(order))
        load[-3*len(beam_nodes):] = tip.T @ action
        load[np.abs(load) < 1e-12] = 0.
        wrench = _wrench(position,load)
        if np.max(abs(wrench-action-np.array((0.,0.,0.,-4.,0.,100.))*(name=="fy"))) > 1e-9:
            raise ValueError("section-dual load wrench changed")
        lines = common + ["*STEP", "*STATIC", "1.,1.", "*CLOAD"]
        lines += [f"{order[s//3]},{s%3+1},{v:.17g}" for s,v in enumerate(load) if v != 0.]
        lines += ["*NODE OUTPUT,DOUBLE,NSET=ALL", "U", "*NODE OUTPUT,DOUBLE,NSET=ROOT", "RF", "*END STEP"]
        payload = ("\n".join(lines)+"\n").encode("ascii")
        payloads[name] = payload
        cases[name] = {"deck_sha256": sha256(payload).hexdigest(),
                       "physical_tip_load_N": load.tolist(),
                       "tip_wrench_about_origin": wrench.tolist()}
    metadata = {"identity":"R8_BL5_CCX_STRONG_HINGE_8X4X2_FY_MX_DEV_V1",
        "status":"PREPARED_NOT_EXECUTED", "source_sha256":digest(Path(__file__)),
        "independent_sha256":digest(independent), "level":pair.LEVEL,
        "physical_nodes":model["physical_nodes"],"elements":model["elements"],
        "root_nodes":model["root_nodes"],"shell_nodes":model["shell_nodes"],
        "beam_nodes":model["beam_nodes"],"shell_elements":model["shell_elements"],
        "beam_elements":model["beam_elements"],"tip_port":tip_meta,
        "equation_check":audit, "cases":cases,
        "interpretation":"sampled five-channel material thickness-secant hinge; no spin row; single-level development reference"}
    return payloads, metadata


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--independent", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists():
        raise FileExistsError("preserve prepared evidence")
    payloads, metadata = decks(args.independent)
    args.output_dir.mkdir(parents=True)
    for name,payload in payloads.items():
        (args.output_dir/f"{name}.inp").write_bytes(payload)
    (args.output_dir/"metadata.json").write_text(json.dumps(metadata,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":metadata["status"],"rows":metadata["equation_check"]["physical_rows"],
                      "pivot_condition":metadata["equation_check"]["pivot_condition"],
                      "row_relative_error":metadata["equation_check"]["row_relative_error"],
                      "decks":{name:value["deck_sha256"] for name,value in metadata["cases"].items()}}))


if __name__ == "__main__":
    main()
