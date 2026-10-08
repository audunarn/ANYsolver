"""Build an inert E01 matching-point B31/S4 feasibility screen.

The geometry, support and station pairs match the experimental GE panel in
tests/test_stiffened_shell_ge_experimental.py. B31/S4 section and shell laws
still need physical matching and refinement before an E01 comparison.
This generator never launches CalculiX.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path


E = 210e9
NU = .3
THICKNESS = .07
OFFSET = .1
SHELL = {
    1: (0., -.5, 0.), 2: (1., -.5, 0.), 3: (2., -.5, 0.),
    4: (0., .5, 0.), 5: (1., .5, 0.), 6: (2., .5, 0.),
}
STATIONS = ((1, 101), (2, 103), (3, 105))


def _beam_nodes(sign: int):
    if sign not in (-1, 1):
        raise ValueError("signed eccentricity required")
    return {101+i: (.5*i, -.5, sign*OFFSET) for i in range(5)}


def _cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2],
            a[0]*b[1]-a[1]*b[0])


def bond_rows(sign: int):
    """Linearized six-row pose work; first entry is a unique beam pivot."""
    e = sign*OFFSET
    rows = []
    for shell, beam in STATIONS:
        rows.extend((
            ((beam, 1, 1.), (shell, 1, -1.), (shell, 5, -e)),
            ((beam, 2, 1.), (shell, 2, -1.), (shell, 4, e)),
            ((beam, 3, 1.), (shell, 3, -1.)),
        ))
        rows.extend(((beam, d, 1.), (shell, d, -1.))
                    for d in (4, 5, 6))
    return tuple(rows)


def _rigid_values(nodes):
    translation = (.31, -.22, .17)
    rotation = (.13, -.09, .05)
    return {node: tuple(translation[d]+_cross(rotation, position)[d]
                        for d in range(3))+rotation
            for node, position in nodes.items()}


def validate_work(sign: int):
    nodes = SHELL | _beam_nodes(sign)
    rows = bond_rows(sign)
    if len(rows) != 18 or len({row[0][:2] for row in rows}) != 18:
        raise ValueError("independent beam pivot inventory required")
    for shell, beam in STATIONS:
        displacement = tuple(nodes[beam][i]-nodes[shell][i]
                             for i in range(3))
        if displacement != (0., 0., sign*OFFSET):
            raise ValueError("matching reference station offset changed")
    rigid = _rigid_values(nodes)
    rigid_error = max(abs(sum(coefficient*rigid[node][dof-1]
                              for node, dof, coefficient in row))
                      for row in rows)
    if rigid_error > 2e-15:
        raise ValueError("rigid-motion pose work defect")
    multipliers = tuple((i-8.)/13. for i in range(len(rows)))
    generalized = {(node, d): 0. for node in nodes for d in range(1, 7)}
    for lam, row in zip(multipliers, rows):
        for node, dof, coefficient in row:
            generalized[node, dof] += lam*coefficient
    force = [sum(generalized[node, d] for node in nodes) for d in (1, 2, 3)]
    moment = [sum(generalized[node, d+4]+_cross(
        nodes[node], tuple(generalized[node, axis] for axis in (1, 2, 3)))[d]
        for node in nodes) for d in range(3)]
    balance = max(abs(v) for v in force+moment)
    if balance > 1e-13:
        raise ValueError("point connection force/moment work does not balance")
    return {"rows": len(rows), "distinct_beam_pivots": 18,
            "maximum_rigid_gap": rigid_error,
            "maximum_connection_wrench_imbalance": balance}


def build_deck(sign: int):
    validate_work(sign)
    nodes = SHELL | _beam_nodes(sign)
    lines = ["*HEADING", "M1 matching-point B31/S4 development canary",
             "*NODE,NSET=AllNodes"]
    for node, xyz in nodes.items():
        lines.append(",".join((str(node), *(f"{v:.17g}" for v in xyz))))
    lines += ["*ELEMENT,TYPE=S4,ELSET=Panel", "1,1,2,5,4",
              "2,2,3,6,5", "*ELEMENT,TYPE=B31,ELSET=Beam"]
    lines += [f"{3+i},{101+i},{102+i}" for i in range(4)]
    lines += ["*NSET,NSET=ShellRoot", "1,4", "*BOUNDARY",
              "ShellRoot,1,6", "*MATERIAL,NAME=Isotropic", "*ELASTIC",
              f"{E:.17g},{NU:.17g}",
              "*SHELL SECTION,ELSET=Panel,MATERIAL=Isotropic",
              f"{THICKNESS:.17g}",
              "*BEAM SECTION,ELSET=Beam,MATERIAL=Isotropic,SECTION=RECT",
              "0.1,0.1", "0,1,0"]
    for row in bond_rows(sign):
        lines += ["*EQUATION", str(len(row)),
                  ",".join(f"{node},{dof},{coefficient:.17g}"
                           for node, dof, coefficient in row)]
    lines += ["*STEP", "*STATIC", "*CLOAD", "105,1,1000",
              "*NODE PRINT,NSET=AllNodes", "U", "RF", "*END STEP"]
    return "\n".join(lines)+"\n"


def generate(out_dir: Path):
    if out_dir.exists():
        raise FileExistsError("preserve earlier E01 development decks")
    out_dir.mkdir(parents=True)
    records = []
    for sign, label in ((-1, "minus"), (1, "plus")):
        deck = build_deck(sign)
        path = out_dir/f"point-{label}.inp"
        path.write_text(deck, encoding="ascii", newline="\n")
        records.append({"sign": sign, "deck": path.name,
                        "sha256": sha256(path.read_bytes()).hexdigest(),
                        "work": validate_work(sign)})
    manifest = {
        "classification": "inert external feasibility screen; not E01 acceptance",
        "native_fixture": "tests/test_stiffened_shell_ge_experimental.py::_panel",
        "shell": "two Q4 on 0..2 by -0.5..0.5 m; t=0.07 m",
        "beam": "B31 along shell lower edge with five nodes and z=+/-0.1 m",
        "section_limit": "B31 rectangular section approximates native A/I; shear and torsion matching unverified",
        "joint": "three matching stations; six linearized pose equations each",
        "supports": "shell root nodes 1,4 fixed in six coordinates; beam root tied only",
        "load": "beam tip node 105, global +x, 1000 N",
        "cases": records,
    }
    (out_dir/"manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    result = generate(args.out_dir)
    print(json.dumps({"status": result["classification"],
                      "cases": [v["deck"] for v in result["cases"]]}))
