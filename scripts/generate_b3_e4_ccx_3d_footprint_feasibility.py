"""Generate inert B31/S4 elastic footprint decks; never invoke CalculiX.

This is a *rigid footprint* external comparator, not an exact weak line bond,
native B3-GE/E4-PL discretization, or a registered E01/E02 reference.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


E = 210e9
NU = .3
PANEL_THICKNESS = .07
BEAM_WIDTH = .1
ECCENTRICITY = .1
BEAM_NODE = 47  # shell grid has 9 * 5 = 45 nodes; beam nodes are 46..48
SAMPLES = ((.25, -.25), (.75, -.25), (.75, .25), (.25, .25))
LOADS = {"force_y": (2, 1000.), "force_z": (3, 1000.),
         "torque_normal_z": (6, 1000.),
         "torque_longitudinal_x": (4, 1000.)}


def _number(value: float) -> str:
    return f"{value:.17g}"


def _shell_id(x: float, y: float) -> int:
    ix, iy = round((x + .5) * 4), round((y + .5) * 4)
    if not (0 <= ix <= 8 and 0 <= iy <= 4):
        raise ValueError("footprint sample outside shell grid")
    return 1 + iy * 9 + ix


def footprint_rows(offset_sign: int):
    """Each row: u_shell - u_beam - theta_beam cross (X_shell-X_beam)=0.

    The first term is a unique dependent shell translation for CalculiX MPCs.
    No shell drilling coordinate is used to transmit a physical moment.
    """
    if offset_sign not in (-1, 1):
        raise ValueError("offset sign must be -1 or +1")
    rows = []
    for x, y in SAMPLES:
        r = (x - .5, y, -offset_sign * ECCENTRICITY)
        sid = _shell_id(x, y)
        rows.extend((
            ((sid, 1, 1.), (BEAM_NODE, 1, -1.), (BEAM_NODE, 5, -r[2]),
             (BEAM_NODE, 6, r[1])),
            ((sid, 2, 1.), (BEAM_NODE, 2, -1.), (BEAM_NODE, 4, r[2]),
             (BEAM_NODE, 6, -r[0])),
            ((sid, 3, 1.), (BEAM_NODE, 3, -1.), (BEAM_NODE, 4, -r[1]),
             (BEAM_NODE, 5, r[0])),
        ))
    return tuple(rows)


def _cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2],
            a[0]*b[1]-a[1]*b[0])


def _dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def _add(a, b):
    return tuple(x+y for x, y in zip(a, b))


def torque_couple(axis: int):
    """Shell nodal force couple with unit torque about x (0) or z (2)."""
    if axis == 0:
        denominator = sum(y*y for _, y in SAMPLES)
        return tuple((0., 0., y/denominator) for _, y in SAMPLES)
    if axis == 2:
        denominator = sum((x-.5)**2+y*y for x, y in SAMPLES)
        return tuple((-y/denominator, (x-.5)/denominator, 0.)
                     for x, y in SAMPLES)
    raise ValueError("only longitudinal x and panel-normal z couples are defined")


def applied_wrench(offset_sign: int, load_kind: str):
    """Applied tip wrench and required *total* support balance about origin.

    This is load inventory bookkeeping, not a predicted reaction partition.
    """
    dof, value = LOADS[load_kind]
    force = tuple(value if i == dof-1 else 0. for i in range(3)) if dof <= 3 else (0.,)*3
    moment = tuple(value if i == dof-4 else 0. for i in range(3)) if dof >= 4 else (0.,)*3
    moment = _add(moment, _cross((1., 0., offset_sign*ECCENTRICITY), force))
    return {"applied_force":force, "applied_moment_about_origin":moment,
            "required_total_support_force":tuple(-v for v in force),
            "required_total_support_moment_about_origin":tuple(-v for v in moment)}


def audit_virtual_work(offset_sign: int, forces, beam_translation, beam_rotation,
                       shell_displacements):
    """Return the shell/beam wrench and their virtual works from C^T lambda.

    Forces are the shell-side Lagrange forces. Opposite beam moment includes
    the signed eccentric lever arm; all moments use the beam-center origin.
    """
    if len(forces) != 4 or len(shell_displacements) != 4:
        raise ValueError("four force and displacement triples required")
    beam_force, beam_moment = (0., 0., 0.), (0., 0., 0.)
    shell_work = 0.
    for (x, y), force, displacement in zip(SAMPLES, forces, shell_displacements):
        r = (x-.5, y, -offset_sign*ECCENTRICITY)
        beam_force = _add(beam_force, tuple(-v for v in force))
        beam_moment = _add(beam_moment, tuple(-v for v in _cross(r, force)))
        shell_work += _dot(force, displacement)
    beam_work = _dot(beam_force, beam_translation) + _dot(beam_moment, beam_rotation)
    return {"beam_force": beam_force, "beam_moment": beam_moment,
            "shell_work": shell_work, "beam_work": beam_work,
            "interface_work": shell_work + beam_work}


def build_deck(offset_sign: int, load_kind: str) -> str:
    if load_kind not in LOADS:
        raise ValueError("unknown load case")
    if offset_sign not in (-1, 1):
        raise ValueError("invalid offset sign")
    lines = ["** INERT 3D B31/S4 rigid-footprint external comparator; no qualification",
             f"** beam z offset sign={offset_sign:+d}; e={_number(ECCENTRICITY)} m",
             "*NODE,NSET=AllNodes"]
    for iy in range(5):
        for ix in range(9):
            node = 1 + iy*9 + ix
            lines.append(f"{node},{_number(-.5+ix*.25)},{_number(-.5+iy*.25)},0")
    for i, x in enumerate((0., .5, 1.), start=46):
        lines.append(f"{i},{_number(x)},0,{_number(offset_sign*ECCENTRICITY)}")
    lines.append("*ELEMENT,TYPE=S4,ELSET=Panel")
    for iy in range(4):
        for ix in range(8):
            n = 1 + iy*9 + ix
            lines.append(f"{1+iy*8+ix},{n},{n+1},{n+10},{n+9}")
    lines += ["*ELEMENT,TYPE=B31,ELSET=Beam", "33,46,47", "34,47,48",
              "*NSET,NSET=PanelEnds"]
    lines.append(",".join(str(1+iy*9+ix) for iy in range(5) for ix in (0, 8)))
    lines += ["*NSET,NSET=BeamRoot", "46", "*BOUNDARY", "PanelEnds,1,3",
              "BeamRoot,1,6", "*MATERIAL,NAME=Isotropic", "*ELASTIC",
              f"{_number(E)},{_number(NU)}",
              "*SHELL SECTION,ELSET=Panel,MATERIAL=Isotropic",
              _number(PANEL_THICKNESS),
              "*BEAM SECTION,ELSET=Beam,MATERIAL=Isotropic,SECTION=RECT",
              f"{_number(BEAM_WIDTH)},{_number(BEAM_WIDTH)}",
              "0,1,0"]
    for row in footprint_rows(offset_sign):
        lines += ["*EQUATION", str(len(row)),
                  ",".join(f"{node},{dof},{_number(coefficient)}"
                           for node, dof, coefficient in row)]
    dof, value = LOADS[load_kind]
    lines += ["*STEP", "*STATIC", "*CLOAD", f"48,{dof},{_number(value)}",
              "*NODE PRINT,NSET=AllNodes", "U", "RF", "*END STEP"]
    return "\n".join(lines) + "\n"


def validate_deck(content: str, offset_sign: int, load_kind: str) -> dict:
    """Independently parse the generated element/equation/load inventory."""
    rows, nodes, shells, beams = [], {}, [], []
    lines = content.splitlines()
    section = None
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("**"):
            i += 1
            continue
        if line == "*EQUATION":
            count = int(lines[i+1])
            values = [v.strip() for v in lines[i+2].split(",")]
            if count != 4 or len(values) != 3*count:
                raise ValueError("invalid equation cardinality")
            rows.append(tuple((int(values[j]), int(values[j+1]), float(values[j+2]))
                              for j in range(0, len(values), 3)))
            i += 3
            continue
        if line.startswith("*"):
            section = line
            i += 1
            continue
        if section == "*NODE,NSET=AllNodes":
            parts = line.split(",")
            nodes[int(parts[0])] = tuple(float(v) for v in parts[1:])
        elif section == "*ELEMENT,TYPE=S4,ELSET=Panel":
            shells.append(tuple(int(v) for v in line.split(",")))
        elif section == "*ELEMENT,TYPE=B31,ELSET=Beam":
            beams.append(tuple(int(v) for v in line.split(",")))
        i += 1
    if len(nodes) != 48 or len(shells) != 32 or beams != [(33,46,47),(34,47,48)]:
        raise ValueError("node/element inventory changed")
    if any(nodes[1+iy*9+ix] != (-.5+ix*.25, -.5+iy*.25, 0.)
           for iy in range(5) for ix in range(9)):
        raise ValueError("shell grid coordinate changed")
    expected_shells = [(1+iy*8+ix, n, n+1, n+10, n+9)
                       for iy in range(4) for ix in range(8)
                       for n in (1+iy*9+ix,)]
    if shells != expected_shells:
        raise ValueError("shell topology or orientation changed")
    if nodes[46] != (0., 0., offset_sign*ECCENTRICITY) or nodes[48] != (
            1., 0., offset_sign*ECCENTRICITY):
        raise ValueError("beam end coordinates changed")
    if nodes[47] != (.5, 0., offset_sign*ECCENTRICITY):
        raise ValueError("beam center offset incorrect")
    for x, y in SAMPLES:
        if nodes[_shell_id(x, y)] != (x, y, 0.):
            raise ValueError("shell footprint correspondence changed")
    expected = footprint_rows(offset_sign)
    if len(rows) != len(expected) or len({row[0][:2] for row in rows}) != 12:
        raise ValueError("dependent footprint pivots missing or repeated")
    for row, original in zip(rows, expected):
        if any((a[:2] != b[:2] or abs(a[2]-b[2]) > 1e-14)
               for a, b in zip(row, original)):
            raise ValueError("footprint lever-arm equation mismatch")
    if f"48,{LOADS[load_kind][0]},{_number(LOADS[load_kind][1])}" not in lines:
        raise ValueError("tip loading changed")
    required = ("*SHELL SECTION,ELSET=Panel,MATERIAL=Isotropic",
                "*BEAM SECTION,ELSET=Beam,MATERIAL=Isotropic,SECTION=RECT",
                f"{_number(E)},{_number(NU)}",
                _number(PANEL_THICKNESS),
                f"{_number(BEAM_WIDTH)},{_number(BEAM_WIDTH)}",
                "0,1,0", "PanelEnds,1,3", "BeamRoot,1,6")
    if any(lines.count(value) != 1 for value in required):
        raise ValueError("section/frame/support idealization changed")
    if (lines[lines.index("*NSET,NSET=PanelEnds")+1] !=
            ",".join(str(1+iy*9+ix) for iy in range(5) for ix in (0,8)) or
            lines[lines.index("*NSET,NSET=BeamRoot")+1] != "46"):
        raise ValueError("support node membership changed")
    if any("TYPE=U1" in line or "TYPE=CPS" in line for line in lines):
        raise ValueError("unsupported mixed-element route")
    # Rigid-motion patch, including both offset signs and all rotations.
    for translation, rotation in (((1.,2.,3.),(0.,0.,0.)),
                                  ((0.,0.,0.),(1.,-2.,3.))):
        beam_xyz = nodes[BEAM_NODE]
        beam_u = _add(translation, _cross(rotation, beam_xyz))
        shell_u = {sid: _add(translation, _cross(rotation, xyz))
                   for sid, xyz in nodes.items() if sid <= 45}
        for row in rows:
            residual = sum(c*(shell_u[n][d-1] if n <= 45 and d <= 3
                              else beam_u[d-1] if d <= 3 else rotation[d-4])
                           for n, d, c in row)
            if abs(residual) > 1e-12:
                raise ValueError("rigid-motion patch failed")
    for axis in (0, 2):
        forces = torque_couple(axis)
        audit = audit_virtual_work(offset_sign, forces, (0.,0.,0.), (0.,0.,0.),
                                   ((0.,0.,0.),)*4)
        shell_force = tuple(-v for v in audit["beam_force"])
        if max(abs(v) for v in shell_force) > 1e-12:
            raise ValueError("torque force couple has a nonzero resultant")
        if max(abs(v + (1. if i == axis else 0.))
               for i, v in enumerate(audit["beam_moment"])) > 1e-12:
            raise ValueError("torque moment is not the unit shell-side couple")
    return {"shell_nodes":45, "beam_nodes":3, "shell_elements":32,
            "beam_elements":2, "equations":12, "offset_sign":offset_sign,
            "load_kind":load_kind, "dependent_shell_translations":12,
            "rigid_patch":True, "unit_torque_couples_x_z":True,
            "global_wrench_inventory":applied_wrench(offset_sign, load_kind)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path,
                        help="Create a fresh directory with eight inert .inp decks and manifest")
    args = parser.parse_args()
    cases = {}
    for sign in (-1, 1):
        for load in LOADS:
            name = f"footprint_{'minus' if sign < 0 else 'plus'}_{load}"
            deck = build_deck(sign, load)
            record = validate_deck(deck, sign, load)
            record["deck_sha256"] = hashlib.sha256(deck.encode("ascii")).hexdigest()
            cases[name] = (deck, record)
    if args.out_dir is not None:
        args.out_dir.mkdir(parents=True, exist_ok=False)
        for name, (deck, _) in cases.items():
            (args.out_dir / f"{name}.inp").write_bytes(deck.encode("ascii"))
        (args.out_dir / "manifest.json").write_bytes(
            (json.dumps({"purpose":"INERT_UNREGISTERED_3D_RIGID_FOOTPRINT_FEASIBILITY",
                         "solver_executed":False,
                         "cases":{name: record for name, (_, record) in cases.items()}},
                        sort_keys=True, indent=2)+"\n").encode("ascii"))
    print(json.dumps({name: record for name, (_, record) in cases.items()}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
