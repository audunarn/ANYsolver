"""Generate, but never run, a shared-knot eccentric CalculiX E01 probe.

This asks whether a shared B31/S4 node and a beam-section offset expose a
usable physical port. It is not a beam/shell accuracy reference: section shear,
torsion and E4-PL/S4 rotational equivalence remain to be established.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path


E = 210e9
NU = 0.3
SHELL_THICKNESS = 0.07
BEAM_SIDE = 0.1
ECCENTRICITY = 0.1
TIP_FORCE_X = 1000.0
SHELL_NODES = (
    (1, 0., -0.5, 0.), (2, 1., -0.5, 0.), (3, 2., -0.5, 0.),
    (4, 0., 0.5, 0.), (5, 1., 0.5, 0.), (6, 2., 0.5, 0.),
)


def _cross(a: tuple[float, ...], b: tuple[float, ...]) -> tuple[float, ...]:
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2],
            a[0]*b[1]-a[1]*b[0])


def declared_work(sign: int) -> dict:
    """Independent small-rotation load pullback at a common reference node."""
    if type(sign) is not int or sign not in (-1, 1):
        raise ValueError("signed eccentricity must be +1 or -1")
    arm = (0., 0., sign*ECCENTRICITY)
    force = (TIP_FORCE_X, 0., 0.)
    moment = _cross(arm, force)
    translation = (0.031, -0.021, 0.013)
    rotation = (0.007, -0.009, 0.005)
    beam_translation = tuple(a+b for a, b in zip(
        translation, _cross(rotation, arm), strict=True))
    beam_work = sum(a*b for a, b in zip(force, beam_translation, strict=True))
    reference_work = sum(a*b for a, b in zip(force, translation, strict=True))
    reference_work += sum(a*b for a, b in zip(moment, rotation, strict=True))
    discrepancy = abs(beam_work-reference_work)
    if discrepancy > 1e-12:
        raise ValueError("eccentric applied-load virtual work changed")
    area = BEAM_SIDE**2
    second_moment = BEAM_SIDE**4/12.
    if abs(area-0.01) > 1e-15 or abs(second_moment-8.333333333333333e-6) > 1e-18:
        raise ValueError("square beam axial/bending section no longer matches")
    return dict(sign=sign, centroid_arm_m=arm, tip_force_n=force,
                reference_tip_moment_nm=moment,
                work_discrepancy_j=discrepancy,
                area_m2=area, second_moment_m4=second_moment)


def build_deck(sign: int) -> str:
    work = declared_work(sign)
    # The beam reference line shares shell edge nodes. CalculiX OFFSET1 is
    # measured in section-side units; with local 1 = +Z, a negative offset
    # places the beam centroid on +Z. Expanded coordinates must verify this.
    offset1 = -sign*ECCENTRICITY/BEAM_SIDE
    lines = [
        "*HEADING", "E01 shared-knot eccentric B31/S4 port feasibility",
        "*NODE,NSET=PanelNodes",
    ]
    lines += [f"{number},{x:.17g},{y:.17g},{z:.17g}"
              for number, x, y, z in SHELL_NODES]
    lines += [
        "*ELEMENT,TYPE=S4,ELSET=Panel", "1,1,2,5,4", "2,2,3,6,5",
        "*ELEMENT,TYPE=B31,ELSET=Beam", "3,1,2", "4,2,3",
        "*NSET,NSET=PanelRoot", "1,4",
        "*BOUNDARY", "PanelRoot,1,6",
        "*MATERIAL,NAME=Isotropic", "*ELASTIC", f"{E:.17g},{NU:.17g}",
        "*SHELL SECTION,ELSET=Panel,MATERIAL=Isotropic",
        f"{SHELL_THICKNESS:.17g}",
        ("*BEAM SECTION,ELSET=Beam,MATERIAL=Isotropic,SECTION=RECT,"
         f"OFFSET1={offset1:.17g},OFFSET2=0"),
        f"{BEAM_SIDE:.17g},{BEAM_SIDE:.17g}", "0,0,1",
        "*STEP", "*STATIC", "*CLOAD",
        f"3,1,{work['tip_force_n'][0]:.17g}",
        f"3,5,{work['reference_tip_moment_nm'][1]:.17g}",
        "*NODE PRINT,NSET=PanelNodes", "U", "RF",
        "*NODE FILE,OUTPUT=3D", "U",
        "*END STEP",
    ]
    return "\n".join(lines)+"\n"


def generate(output: Path) -> dict:
    if output.exists():
        raise FileExistsError("preserve prior E01 shared-knot evidence")
    output.mkdir(parents=True)
    cases = []
    for sign, label in ((1, "plus"), (-1, "minus")):
        deck = output/f"shared-knot-{label}.inp"
        deck.write_text(build_deck(sign), encoding="ascii", newline="\n")
        cases.append(dict(deck=deck.name, sha256=sha256(deck.read_bytes()).hexdigest(),
                          work=declared_work(sign)))
    manifest = dict(identity="E01_SHARED_KNOT_OFFSET_PORT_20261008_V1",
                    classification="inert reference-port discriminator, not E01 accuracy",
                    shell="two S4 on 0..2 by -0.5..0.5 m, thickness 0.07 m",
                    beam="two B31 on shared lower-edge nodes, 0.1 m square section",
                    connection="automatic shared-node beam/shell knot; no separate equations",
                    section_limit="axial area and biaxial inertia match native fixture; shear, torsion and shell rotation laws unverified",
                    load="+1000 N X at shared tip plus signed eccentric My",
                    cases=cases)
    (output/"manifest.json").write_text(json.dumps(manifest, indent=2,
                                                  sort_keys=True)+"\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(json.dumps(generate(args.output)["cases"]))
