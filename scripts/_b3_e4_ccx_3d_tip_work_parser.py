"""Bounded ASCII FRD reader for the four expanded B31 tip work coordinates."""

from __future__ import annotations

import math
import re


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
