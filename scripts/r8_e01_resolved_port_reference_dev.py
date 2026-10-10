"""Inert E01 resolved plate/stiffener port reference; never launches CalculiX.

Separate C3D20R constituents retain observable plate and beam-side actions.
Finite rigid port patches are an explicit approximation to native point ties;
this deck alone cannot establish response accuracy or E01 qualification.
"""
from __future__ import annotations

from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path

import numpy as np


E = 210e9
NU = .3
PLATE_THICKNESS_M = .07
BEAM_SIDE_M = .1
OFFSET_M = .1
STATIONS_MM = (0, 1000, 2000)
X_MM = (0, 25, 250, 500, 750, 975, 1000, 1025,
        1250, 1500, 1750, 1975, 2000)
PLATE_Y_MM = (-500, -450, -250, 0, 250, 500)
PLATE_Z_MM = (-35, 0, 35)
BEAM_Y_MM = (-550, -500, -450)
EDGES = ((0, 1), (1, 2), (2, 3), (3, 0),
         (4, 5), (5, 6), (6, 7), (7, 4),
         (0, 4), (1, 5), (2, 6), (3, 7))


def _lines(values):
    ordered = sorted(values)
    return [",".join(map(str, ordered[i:i+12])) for i in range(0, len(ordered), 12)]


def _volume(first_id, ys, zs):
    """One owned structured Q20 volume, without cross-domain node merging."""
    points = {}
    elements = []
    next_id = first_id

    def node(point):
        nonlocal next_id
        if point not in points:
            points[point] = next_id
            next_id += 1
        return points[point]

    for iz in range(len(zs)-1):
        for iy in range(len(ys)-1):
            for ix in range(len(X_MM)-1):
                x0, x1 = X_MM[ix:ix+2]
                y0, y1 = ys[iy:iy+2]
                z0, z1 = zs[iz:iz+2]
                corners = ((x0, y0, z0), (x1, y0, z0),
                           (x1, y1, z0), (x0, y1, z0),
                           (x0, y0, z1), (x1, y0, z1),
                           (x1, y1, z1), (x0, y1, z1))
                mids = tuple(tuple((Fraction(a)+Fraction(b))/2
                                   for a, b in zip(corners[i], corners[j]))
                             for i, j in EDGES)
                elements.append((ix, tuple(node(p) for p in corners+mids)))
    return points, elements, next_id


def _noncollinear(points, ids):
    coordinates = np.array([tuple(float(v) for v in p)
                            for p, number in points.items() if number in ids])
    if len(coordinates) < 3:
        return False
    return np.linalg.matrix_rank(coordinates-coordinates.mean(axis=0),
                                 tol=1e-9) >= 2


def build(sign: int, load: str) -> tuple[str, dict]:
    """Emit one reference model and its exact geometry/work inventory."""
    if type(sign) is not int or sign not in (-1, 1):
        raise ValueError("E01 reference requires explicit offset sign")
    if load not in ("fy", "mx"):
        raise ValueError("E01 reference admits only Fy or Mx controls")
    beam_z = (50, 100, 150) if sign == 1 else (-150, -100, -50)
    plate, plate_cells, beam_start = _volume(1, PLATE_Y_MM, PLATE_Z_MM)
    beam, beam_cells, end = _volume(beam_start, BEAM_Y_MM, beam_z)
    if set(plate.values()) & set(beam.values()):
        raise AssertionError("plate/beam solid node ownership overlaps")
    points = {number: tuple(float(v)/1000. for v in position)
              for domain in (plate, beam)
              for position, number in domain.items()}

    root = {number for point, number in plate.items() if point[0] == 0}
    patches = []
    for station in STATIONS_MM:
        lo, hi = ((0, 25) if station == 0 else
                  (975, 1000) if station == 1000 else (1975, 2000))
        shell_patch = {number for (x, y, _), number in plate.items()
                       if y == -500 and lo <= x <= hi}
        beam_patch = {number for (x, _, _), number in beam.items()
                      if x == station}
        if not _noncollinear(plate, shell_patch) or not _noncollinear(beam, beam_patch):
            raise AssertionError("finite two-dimensional port support required")
        patches.append((shell_patch, beam_patch))
    for domain in (0, 1):
        if any(patches[i][domain] & patches[j][domain]
               for i in range(3) for j in range(i+1, 3)):
            raise AssertionError("station rigid patches overlap")

    port_nodes = {}
    for i, station in enumerate(STATIONS_MM):
        x = station/1000.
        for side, z in (("shell", 0.), ("beam", sign*OFFSET_M)):
            base = end+4*i+(0 if side == "shell" else 2)
            port_nodes[(side, station)] = (base, base+1)
            points[base] = (x, -.5, z)
            points[base+1] = (x, -.5, z)

    lines = ["*HEADING", "E01 inert resolved eccentric plate/stiffener port reference",
             "*NODE"]
    for number, xyz in sorted(points.items()):
        lines.append(f"{number},"+",".join(f"{float(v):.17g}" for v in xyz))
    for name, cells, first in (("Plate", plate_cells, 1),
                               ("BeamSolid", beam_cells, len(plate_cells)+1)):
        lines.append(f"*ELEMENT,TYPE=C3D20R,ELSET={name}")
        for number, (_, cell) in enumerate(cells, first):
            lines.append(f"{number},"+",".join(map(str, cell[:15])))
            lines.append(",".join(map(str, cell[15:])))
    lines.extend(("*MATERIAL,NAME=Isotropic", "*ELASTIC",
                  f"{E:.17g},{NU:.17g}",
                  "*SOLID SECTION,ELSET=Plate,MATERIAL=Isotropic",
                  "*SOLID SECTION,ELSET=BeamSolid,MATERIAL=Isotropic"))
    # CalculiX rigid-body slave nodes must not also receive direct SPCs.
    root_free = root-patches[0][0]
    lines.append("*NSET,NSET=PlateRootFree")
    lines.extend(_lines(root_free))
    all_ports = []
    equations = []
    for i, station in enumerate(STATIONS_MM):
        shell_ref, shell_rot = port_nodes[("shell", station)]
        beam_ref, beam_rot = port_nodes[("beam", station)]
        all_ports.extend((shell_ref, shell_rot, beam_ref, beam_rot))
        for side, patch, ref, rot in (("Shell", patches[i][0], shell_ref, shell_rot),
                                      ("Beam", patches[i][1], beam_ref, beam_rot)):
            name = f"{side}Port{station}"
            lines.append(f"*NSET,NSET={name}")
            lines.extend(_lines(patch))
            lines.append(f"*RIGID BODY,NSET={name},REF NODE={ref},ROT NODE={rot}")
        e = sign*OFFSET_M
        equations.extend((
            ((beam_ref, 1, 1.), (shell_ref, 1, -1.), (shell_rot, 2, -e)),
            ((beam_ref, 2, 1.), (shell_ref, 2, -1.), (shell_rot, 1, e)),
            ((beam_ref, 3, 1.), (shell_ref, 3, -1.)),
        ))
        equations.extend(tuple(((beam_rot, d, 1.), (shell_rot, d, -1.))
                               for d in (1, 2, 3)))
    lines.append("*NSET,NSET=AllPorts")
    lines.extend(_lines(all_ports))
    for row in equations:
        lines.extend(("*EQUATION", str(len(row)),
                      ",".join(f"{node},{dof},{coef:.17g}"
                               for node, dof, coef in row)))

    cuts = {}
    for side, cells, first in (("Plate", plate_cells, 1),
                               ("Beam", beam_cells, len(plate_cells)+1)):
        for station, direction in ((0, "Right"), (1000, "Left"),
                                   (1000, "Right"), (2000, "Left")):
            # S4 is x+ and S6 is x- for the declared C3D20R ordering.
            target = X_MM.index(station)-(direction == "Left")
            face = "S4" if direction == "Left" else "S6"
            name = f"{side}{station}{direction}Cut"
            faces = [first+i for i, (ix, _) in enumerate(cells) if ix == target]
            cuts[name] = (face, len(faces))
            lines.append(f"*SURFACE,NAME={name},TYPE=ELEMENT")
            lines.extend(f"{number},{face}" for number in faces)
    shell_root_ref, shell_root_rot = port_nodes[("shell", 0)]
    lines.extend(("*BOUNDARY", "PlateRootFree,1,3",
                  f"{shell_root_ref},1,3", f"{shell_root_rot},1,3",
                  "*STEP", "*STATIC", "*CLOAD"))
    tip_ref, tip_rot = port_nodes[("beam", 2000)]
    force_n = (0., 1000., 0.) if load == "fy" else (0., 0., 0.)
    moment_nm = (100., 0., 0.) if load == "mx" else (0., 0., 0.)
    lines.append(f"{tip_ref},2,1000" if load == "fy" else f"{tip_rot},1,100")
    for name in cuts:
        lines.extend((f"*SECTION PRINT,SURFACE={name},NAME={name}", "SOF"))
    lines.extend(("*NODE PRINT,NSET=AllPorts", "U", "RF",
                  "*NODE PRINT,NSET=PlateRootFree", "RF",
                  "*NODE FILE,OUTPUT=3D", "U", "*END STEP"))
    if len(equations) != 18 or len(points) != end-1+12:
        raise AssertionError("complete three-station six-row port inventory required")
    pullback = np.cross((0., 0., sign*OFFSET_M), force_n)+moment_nm
    meta = dict(identity="R8_E01_RESOLVED_PORT_INERT_V1", sign=sign,
                load=load, classification="development deck, not executed or qualified",
                plate_thickness_m=PLATE_THICKNESS_M,
                beam_side_m=BEAM_SIDE_M, beam_centroid_offset_m=sign*OFFSET_M,
                plate_nodes=len(plate), beam_nodes=len(beam),
                plate_elements=len(plate_cells), beam_elements=len(beam_cells),
                port_patch_sizes=[(len(a), len(b)) for a, b in patches],
                port_reference_nodes={f"{side}_{station}": pair for
                                      (side, station), pair in port_nodes.items()},
                equation_count=len(equations), applied_force_n=force_n,
                applied_moment_nm=moment_nm,
                shell_tip_wrench_from_beam=(tuple(force_n), tuple(pullback)),
                root_free_nodes=len(root_free),
                cut_surfaces={name: dict(face=face, count=count)
                              for name, (face, count) in cuts.items()},
                limitations=("rigid finite port patches differ from native point ties",
                             "native torsion/shear section laws require physical matching",
                             "face-stress cuts near rigid ports require weak residual cross-check",
                             "root and sided cut work must be verified after execution"))
    return "\n".join(lines)+"\n", meta


def generate(output: Path) -> dict:
    if output.exists():
        raise FileExistsError("preserve existing E01 reference deck evidence")
    output.mkdir(parents=True)
    cases = []
    for sign, load in ((1, "fy"), (1, "mx"), (-1, "fy"), (-1, "mx")):
        deck, meta = build(sign, load)
        path = output/f"e01-resolved-{'plus' if sign > 0 else 'minus'}-{load}.inp"
        path.write_text(deck, encoding="ascii", newline="\n")
        cases.append(dict(deck=path.name, sha256=sha256(path.read_bytes()).hexdigest(),
                          model=meta))
    manifest = dict(identity="R8_E01_RESOLVED_PORT_INERT_V1", cases=cases,
                    status="NOT_EXECUTED_NOT_QUALIFIED")
    (output/"manifest.json").write_text(json.dumps(manifest, indent=2)+"\n",
                                        encoding="utf-8")
    return manifest
