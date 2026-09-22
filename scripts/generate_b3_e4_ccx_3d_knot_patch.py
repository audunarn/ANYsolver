"""Inert rigid-x patch deck for a *new* B31/S4 knot-based comparator.

This changes the failed comparator's two beam section orientations while
retaining a square physical section. It does not execute or qualify the deck.
"""

from __future__ import annotations

import generate_b3_e4_ccx_3d_footprint_feasibility as base
import generate_b3_e4_ccx_3d_reciprocity_influences as old


def build_knot_rigid_deck(component: int, signed_delta: float) -> str:
    """Prescribe a reference rigid translation or rotation at all supports."""
    if type(component) is not int or not 0 <= component < 6:
        raise ValueError("invalid global rigid mode")
    if signed_delta not in (-old.DELTA,old.DELTA):
        raise ValueError("only the frozen signed amplitude is admitted")
    original = base.build_deck(1, "force_y")
    base.validate_deck(original, 1, "force_y")
    lines = original.splitlines()
    beam_element = ["*ELEMENT,TYPE=B31,ELSET=Beam", "33,46,47", "34,47,48"]
    beam_sections = ["*BEAM SECTION,ELSET=Beam,MATERIAL=Isotropic,SECTION=RECT",
                     base._number(base.BEAM_WIDTH)+","+base._number(base.BEAM_WIDTH),
                     "0,1,0"]
    if lines.count(beam_element[0]) != 1 or lines.count(beam_sections[0]) != 1:
        raise ValueError("original beam-section inventory changed")
    i = lines.index(beam_element[0])
    if lines[i:i+3] != beam_element:
        raise ValueError("original beam connectivity changed")
    lines[i:i+3] = ["*ELEMENT,TYPE=B31,ELSET=BeamA", "33,46,47",
                    "*ELEMENT,TYPE=B31,ELSET=BeamB", "34,47,48"]
    i = lines.index(beam_sections[0])
    if lines[i:i+3] != beam_sections:
        raise ValueError("original section geometry changed")
    lines[i:i+3] = ["*BEAM SECTION,ELSET=BeamA,MATERIAL=Isotropic,SECTION=RECT",
                    beam_sections[1],"0,1,0",
                    "*BEAM SECTION,ELSET=BeamB,MATERIAL=Isotropic,SECTION=RECT",
                    beam_sections[1],"0,0,1"]
    i = lines.index("*BOUNDARY")
    if lines[i+1:i+3] != ["PanelEnds,1,3", "BeamRoot,1,6"]:
        raise ValueError("original supports changed")
    del lines[i:i+3]
    i = lines.index("*CLOAD")
    if lines[i:i+2] != ["*CLOAD", "48,2,1000"]:
        raise ValueError("original applied load changed")
    del lines[i:i+2]
    motion = old.support_motion("shell",component,signed_delta)
    root = old.support_coordinates()[old.BEAM_ROOT]
    if component < 3:
        motion[(old.BEAM_ROOT,component+1)] = signed_delta
    else:
        axis = tuple(float(i == component-3) for i in range(3))
        field = old._cross(axis,root)
        for direction in range(3):
            motion[(old.BEAM_ROOT,direction+1)] = signed_delta*field[direction]
        motion[(old.BEAM_ROOT,component+1)] = signed_delta
    rows = [f"{node},{dof},{dof},{old.checked_boundary_token(f'{value:.12g}')}"
            for (node,dof),value in sorted(motion.items())]
    i = lines.index("*STATIC")
    lines[i+1:i+1] = ["*BOUNDARY",*rows]
    deck = "\n".join(lines)+"\n"
    if (len(rows) != 36 or deck.count("*STEP\n") != 1 or
            deck.count("*BOUNDARY\n") != 1 or deck.count("*EQUATION\n") != 12 or
            "*CLOAD" in deck or deck.index("*BOUNDARY\n") < deck.index("*STEP\n")):
        raise ValueError("knot patch deck inventory changed")
    return deck


def build_knot_rigid_x_deck() -> str:
    """Preserve the exact first registered positive x-rotation deck."""
    return build_knot_rigid_deck(3,old.DELTA)
