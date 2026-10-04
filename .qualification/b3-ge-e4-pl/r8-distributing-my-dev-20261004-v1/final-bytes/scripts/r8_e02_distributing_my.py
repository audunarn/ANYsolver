"""One new unitMy direction at unchanged finest geometry; no refinement gate.

Same reduced mean/director/curl pose and support, not a pointwise welded face.
Old Mx/Fy entry points continue to reject My. Native retained coordinates and
all free-stub, equilibrium and physical work controls use the existing fixture.
"""
import hashlib
from .r8_e02_distributing_thickness import build_case as thickness_case
from .r8_e02_distributing_feasibility import _hash,_parse_observed,_native_load_cases
from .r8_e02_rigid_tip_reference import ReferenceParseError

WRENCH=(0.,0.,0.,0.,1.,0.)
SCHEMA='R8_E02_DISTRIBUTING_MY_DIRECTION_V1'


def build_case():
    text,metadata,area=thickness_case('Mx')
    action=area.action(WRENCH[:3],WRENCH[3:])
    before,tail=text.split('*CLOAD\n',1)
    _,after=tail.split('*NODE PRINT',1)
    loads=[f'{n},{j},{v:.13e}' for n,f in zip(action.node_ids,action.forces_n)
           for j,v in enumerate(f,1) if v]
    if any(len(line.split(',')[2])>20 for line in loads):
        raise ValueError('My CLOAD numeric field exceeds20characters')
    text=before+'*CLOAD\n'+'\n'.join(loads)+'\n*NODE PRINT'+after
    metadata.update(schema=SCHEMA,case='My',applied_wrench=WRENCH,
        scope='ONE independent My direction; fixed40x16/nz4; no convergence/acceptance',
        deck_sha256=hashlib.sha256(text.encode('ascii')).hexdigest())
    return text,metadata,area


def parse_result(dat,stdout,metadata):
    _,expected,area=build_case()
    try:
        same=_hash(metadata)==_hash(expected)
    except (ValueError,TypeError) as error:
        raise ReferenceParseError('invalid My diagnostic metadata') from error
    if not same:raise ReferenceParseError('changed My diagnostic metadata')
    return _parse_observed(dat,stdout,expected,area)


def native_case():
    return _native_load_cases(40,16,{'My':WRENCH})
