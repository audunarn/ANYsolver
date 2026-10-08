"""Inert unloaded boundary-motion decks for B31/S4 reciprocal wrench recovery.

Only the existing positive-offset force-y canary idealization is covered.
No deck is executed here. The influence construction assumes a conservative
linear symmetric tangent and exact work-conjugate prescribed coordinates.
"""

from __future__ import annotations

import hashlib
import math

import generate_b3_e4_ccx_3d_footprint_feasibility as base


SHELL_SUPPORTS = tuple(1 + iy*9 + ix for iy in range(5) for ix in (0, 8))
BEAM_ROOT = 46
DELTA = 1e-5


def _cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2],
            a[0]*b[1]-a[1]*b[0])


def support_coordinates() -> dict[int, tuple[float, float, float]]:
    """Reference coordinates of exactly the 11 supported physical nodes."""
    result = {}
    for node in SHELL_SUPPORTS:
        index = node-1
        result[node] = (-.5 + .25*(index % 9), -.5 + .25*(index//9), 0.)
    result[BEAM_ROOT] = (0., 0., base.ECCENTRICITY)
    return result


def support_motion(group: str, component: int, signed_delta: float) -> dict[tuple[int,int],float]:
    """Physical shell-edge wrench basis about origin or beam-root coordinate."""
    if group not in ("shell", "beam") or type(component) is not int or not 0 <= component < 6:
        raise ValueError("invalid support group or wrench component")
    if signed_delta not in (-DELTA, DELTA):
        raise ValueError("only the frozen signed influence amplitude is admitted")
    motion = {(node, dof): 0. for node in SHELL_SUPPORTS for dof in (1,2,3)}
    motion.update({(BEAM_ROOT, dof): 0. for dof in range(1,7)})
    if group == "beam":
        motion[(BEAM_ROOT, component+1)] = signed_delta
    elif component < 3:
        for node in SHELL_SUPPORTS:
            motion[(node, component+1)] = signed_delta
    else:
        axis = tuple(float(i == component-3) for i in range(3))
        for node, xyz in support_coordinates().items():
            if node != BEAM_ROOT:
                field = _cross(axis, xyz)
                for direction in range(3):
                    motion[(node,direction+1)] = signed_delta*field[direction]
    return motion


def checked_boundary_token(token: str) -> str:
    """Guard the actual 20-character numeric field parsed by CalculiX."""
    if len(token) > 20:
        raise ValueError("CalculiX prescribed value exceeds 20 characters")
    try:
        value = float(token)
    except ValueError as exc:
        raise ValueError("invalid CalculiX prescribed value") from exc
    if not math.isfinite(value):
        raise ValueError("nonfinite CalculiX prescribed value")
    return token


def build_influence_deck(group: str, component: int, signed_delta: float) -> str:
    """Replace only original supports and tip load in a validated canary deck."""
    motion = support_motion(group, component, signed_delta)
    original = base.build_deck(1, "force_y")
    base.validate_deck(original, 1, "force_y")
    lines = original.splitlines()
    location = lines.index("*BOUNDARY")
    if lines[location+1:location+3] != ["PanelEnds,1,3", "BeamRoot,1,6"]:
        raise ValueError("source support inventory changed")
    # CalculiX boundarys.f reads only textpart(4)(1:20); a .17g token such
    # as 1.0000000000000001e-05 loses its exponent and fails preprocessing.
    boundary = [f"{node},{dof},{dof},{checked_boundary_token(f'{value:.12g}')}"
                for (node,dof),value in sorted(motion.items())]
    del lines[location:location+3]
    load = ["*CLOAD", "48,2,1000"]
    if lines.count(load[0]) != 1:
        raise ValueError("source load inventory changed")
    at = lines.index(load[0])
    if lines[at:at+2] != load:
        raise ValueError("source load magnitude changed")
    del lines[at:at+2]
    step = lines.index("*STATIC")
    lines[step+1:step+1] = ["*BOUNDARY", *boundary]
    deck = "\n".join(lines)+"\n"
    if (deck.count("*STEP\n") != 1 or deck.count("*EQUATION\n") != 12 or
            deck.count("*BOUNDARY\n") != 1 or "*CLOAD" in deck or
            len(boundary) != 36 or
            any(len(row.rsplit(",",1)[1]) > 20 for row in boundary) or
            deck.index("*BOUNDARY\n") < deck.index("*STEP\n")):
        raise ValueError("influence deck inventory changed")
    return deck


def case_name(group: str, component: int, signed_delta: float) -> str:
    support_motion(group, component, signed_delta)
    label = ("fx", "fy", "fz", "mx", "my", "mz")[component]
    return f"{group}-{label}-{'plus' if signed_delta > 0 else 'minus'}"


def deck_hash(group: str, component: int, signed_delta: float) -> str:
    return hashlib.sha256(build_influence_deck(group,component,signed_delta).encode("ascii")).hexdigest()
