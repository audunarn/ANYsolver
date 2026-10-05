"""One orthogonal solid-reference sensitivity, not convergence or acceptance.

The new fixed40x16/nz4 geometry keeps the previously declared functional,
physical pad, material, clamp and load measures. Historical nz2 donors/guards
are not modified or called with out-of-scope arguments. This module never runs
a solver and exposes no general refinement campaign.
"""
from .r8_e02_rigid_tip_reference import _OFFSETS,ReferenceParseError
from .r8_e02_distributing_feasibility import (
    LOADS,_hash,_build_geometry_case,_parse_observed,
)

SCHEMA="R8_E02_DISTRIBUTING_THICKNESS_SENSITIVITY_V1"


def build_case(name):
    if type(name) is not str or name not in ('Mx','Fy'):
        raise ValueError('one declared Mx/Fy thickness discriminator required')
    nx,ny,nz=40,16,4
    lattice=[];used=set()
    for ix in range(nx):
        for iy in range(ny):
            for iz in range(nz):
                cell=tuple((2*ix+dx,2*iy+dy,2*iz+dz) for dx,dy,dz in _OFFSETS)
                lattice.append(cell);used.update(cell)
    ids={point:i+1 for i,point in enumerate(sorted(used))}
    nodes={node:(ix/(2*nx),(iy-ny)/(10*ny),(iz-nz)/(100*nz))
           for (ix,iy,iz),node in ids.items()}
    elements={i+1:tuple(ids[p] for p in cell) for i,cell in enumerate(lattice)}
    root=sorted(node for (ix,iy,iz),node in ids.items() if ix==0)
    if len(elements)!=2560 or 3*len(nodes)>100000:
        raise ValueError('fixed thickness diagnostic resource inventory mismatch')
    return _build_geometry_case(name,nodes,elements,root,nx,ny,nz,SCHEMA,
        'fixed in-plane40x16; nz4 versus saved nz2; reference sensitivity only, no acceptance')


def parse_result(dat,stdout,metadata):
    try:
        _,expected,area=build_case(metadata['case'])
        if _hash(metadata)!=_hash(expected):
            raise ReferenceParseError('changed thickness diagnostic metadata')
    except (KeyError,TypeError,ValueError) as error:
        raise ReferenceParseError('invalid thickness diagnostic metadata') from error
    return _parse_observed(dat,stdout,expected,area)
