"""Bounded ASCII FRD reader for the four expanded B31 tip work coordinates."""

from __future__ import annotations

import math
import re

import numpy as np


_NUMBER=re.compile(r"[+-]?\d\.\d{5}E[+-]\d{2,3}",re.I)
_TIP_CORNERS={(1.,y,z) for y in (-.05,.05) for z in (.05,.15)}


def _values(line:str)->tuple[int,tuple[float,float,float]]:
    if not line.startswith(" -1"):
        raise ValueError("not an ASCII FRD node row")
    node=int(line[3:13])
    matches=_NUMBER.findall(line[13:])
    if len(matches)!=3:
        raise ValueError("malformed FRD node vector")
    xyz=tuple(float(x) for x in matches)
    if not all(math.isfinite(x) for x in xyz):
        raise ValueError("nonfinite FRD node vector")
    return node,xyz


def parse_tip_corner_displacements(frd:str)->dict:
    """Find four geometric tip corners and their only 3D DISP block."""
    lines=frd.splitlines()
    mesh=[i for i,line in enumerate(lines) if line.startswith("    2C")]
    disp=[i for i,line in enumerate(lines) if line.startswith(" -4  DISP")]
    if len(mesh)!=1 or len(disp)!=1 or mesh[0]>=disp[0]:
        raise ValueError("one coordinate and one later DISP block required")
    coords={}
    for line in lines[mesh[0]+1:]:
        if line.startswith(" -3"):
            break
        node,xyz=_values(line)
        if node in coords:
            raise ValueError("duplicate FRD coordinate")
        coords[node]=xyz
    if len(coords)<4:
        raise ValueError("incomplete FRD mesh")
    corners={}
    for node,xyz in coords.items():
        matched=[p for p in _TIP_CORNERS if max(abs(x-y) for x,y in zip(xyz,p))<1e-7]
        if matched:
            if len(matched)!=1 or matched[0] in corners.values():
                raise ValueError("ambiguous expanded beam tip corner")
            corners[node]=matched[0]
    if len(corners)!=4 or set(corners.values())!=_TIP_CORNERS:
        raise ValueError("missing expanded beam tip corners")
    vectors={}
    inside=False
    for line in lines[disp[0]+1:]:
        if line.startswith(" -3"):
            break
        if line.startswith(" -5"):
            if inside:
                raise ValueError("late FRD DISP field label")
            continue
        inside=True
        node,xyz=_values(line)
        if node in vectors:
            raise ValueError("duplicate FRD displacement")
        vectors[node]=xyz
    if not set(corners).issubset(vectors):
        raise ValueError("missing expanded tip displacement")
    result=[dict(node=node,coordinate_m=list(corners[node]),
                 displacement_m=list(vectors[node])) for node in sorted(corners)]
    return dict(corners=result,mean_tip_y_m=sum(
        item["displacement_m"][1] for item in result)/4)


def recover_tip_section_motion(frd: str) -> dict:
    """Fit six candidate small-motion coordinates of the expanded B31 tip.

    Four geometric corners determine a least-squares rigid motion. A nonzero
    residual exposes section deformation or an incompatible result field.
    Neither the fitted rotation nor printed MPC forces are established as
    work-conjugate quantities by this kinematic recovery alone.
    """
    corners = parse_tip_corner_displacements(frd)["corners"]
    points = np.array([item["coordinate_m"] for item in corners], dtype=float)
    displacement = np.array([item["displacement_m"] for item in corners],
                            dtype=float)
    center = points.mean(axis=0)
    if np.max(np.abs(center-np.array([1., 0., .1]))) > 1e-7:
        raise ValueError("expanded tip section center changed")
    relative = points-center
    design = np.zeros((12, 6))
    for i, (x, y, z) in enumerate(relative):
        design[3*i:3*i+3, :3] = np.eye(3)
        # omega cross relative_position = -skew(relative_position) omega.
        design[3*i:3*i+3, 3:] = ((0., z, -y),
                                 (-z, 0., x),
                                 (y, -x, 0.))
    motion, _, rank, _ = np.linalg.lstsq(design, displacement.ravel(),
                                        rcond=None)
    if rank != 6 or not np.isfinite(motion).all():
        raise ValueError("expanded tip corners do not define six motions")
    error = (design@motion-displacement.ravel()).reshape(4, 3)
    return {
        "center_m": center.tolist(),
        "translation_m": motion[:3].tolist(),
        "rotation_rad": motion[3:].tolist(),
        "rms_fit_residual_m": float(np.sqrt(np.mean(error**2))),
        "max_corner_fit_residual_m": float(np.max(np.linalg.norm(error, axis=1))),
        "scope": "four-corner small-motion fit; torque work conjugacy unverified",
    }
