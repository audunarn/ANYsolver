"""Bounded saved interface and signed band admission for classical F03.

This component recomputes one manufactured Recovery from owned q/eta, binds
an independently owned saved Functional, and certifies saved band values.
It performs no equilibrium solve and makes no full-recovery acceptance claim.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F
import hashlib
import math
from types import MappingProxyType

import numpy as np

from scripts import _b3_e4_f03_action_enclosure as enclosure
from scripts import _b3_e4_f03_local_functional as functional
from scripts import _b3_e4_f03_local_grid as topology
from scripts import _b3_e4_f03_local_recovery as rec
from scripts import _b3_e4_f03_spatial_contract as c


Z=F(0);O=F(1)
BANDS=((Z,F(1,4)),(F(1,4),F(1,2)),(F(1,2),F(3,4)),(F(3,4),O),
       (Z,F(1,32)),(F(1,32),F(1,16)),(F(15,16),F(31,32)),(F(31,32),O))
INTERFACE_LIMIT=F.from_float(1e-10)
PARTITION_LIMIT=F.from_float(1e-11)
SCOPE='CLASSICAL_SAVED_INTERFACE_AND_FIXED_BANDS_ONLY'


def _owned(value,shape,name):
    if (type(value) is not np.ndarray or value.dtype!=np.float64 or
            value.shape!=shape):
        raise ValueError(f'{name} must be finite float64 with exact shape {shape}')
    owned=np.frombuffer(value.tobytes(),dtype=np.float64).reshape(shape)
    if not np.isfinite(owned).all():
        raise ValueError(f'{name} owned snapshot must be finite float64')
    return owned


@dataclass(frozen=True,slots=True,init=False)
class SavedInterface:
    cuts:tuple
    density:np.ndarray
    cosine:np.ndarray
    atoms:np.ndarray
    band_analytic:np.ndarray
    band48:np.ndarray
    band64:np.ndarray
    line_band_analytic:np.ndarray

    def __init__(self,cuts,density,cosine,atoms,band_analytic,band48,band64,
                 line_band_analytic):
        if type(cuts) not in (tuple,list) or not 2<=len(cuts)<=rec.MAX_TERMS+1:
            raise ValueError('bounded exact saved interface cuts required')
        cc=tuple(rec._coordinate(value) for value in cuts)
        if cc[0]!=Z or cc[-1]!=O or any(a>=b for a,b in zip(cc,cc[1:])):
            raise ValueError('strict exact saved interface partition 0..1 required')
        ni=len(cc)-1
        values=dict(cuts=cc,density=_owned(density,(ni,3,6),'density'),
            cosine=_owned(cosine,(3,),'cosine'),atoms=_owned(atoms,(2,3),'atoms'),
            band_analytic=_owned(band_analytic,(8,3),'band_analytic'),
            band48=_owned(band48,(8,3),'band48'),
            band64=_owned(band64,(8,3),'band64'),
            line_band_analytic=_owned(line_band_analytic,(8,3),'line_band_analytic'))
        for name,value in values.items():object.__setattr__(self,name,value)


@dataclass(frozen=True,slots=True)
class InterfaceBudget:
    recovery_budget:rec.RecoveryBudget
    action_budget:enclosure.ActionBudget
    max_intervals:int
    max_comparisons:int
    max_aggregate_operations:int
    max_aggregate_bits:int
    max_work_bytes:int

    def __post_init__(self):
        if (type(self.recovery_budget) is not rec.RecoveryBudget or
                type(self.action_budget) is not enclosure.ActionBudget or any(
                type(getattr(self,key)) is not int or getattr(self,key)<=0 for key in
                ('max_intervals','max_comparisons','max_aggregate_operations',
                 'max_aggregate_bits','max_work_bytes'))):
            raise ValueError('explicit bounded saved-interface budgets required')


@dataclass(frozen=True,slots=True,init=False)
class InterfaceResult:
    recovery:rec.Recovery
    saved_functional:functional.Functional
    metrics:object
    comparisons:tuple
    input_sha256:object
    diagnostics:object
    status:str
    failures:tuple

    def __init__(self,*args,**kwargs):
        raise TypeError('InterfaceResult requires verified factory')


def _freeze(value):
    if isinstance(value,dict):return MappingProxyType({key:_freeze(item) for key,item in value.items()})
    if isinstance(value,list):return tuple(_freeze(item) for item in value)
    if isinstance(value,tuple):return tuple(_freeze(item) for item in value)
    return value


def _hash_fraction(digest,value):
    digest.update(b'-' if value<0 else b'+')
    for integer in (abs(value.numerator),value.denominator):
        raw=integer.to_bytes(max(1,(integer.bit_length()+7)//8),'little')
        digest.update(len(raw).to_bytes(8,'little'));digest.update(raw)


def _hash_saved(saved):
    digest=hashlib.sha256(b'F03_SAVED_INTERFACE_V1\0')
    for value in saved.cuts:_hash_fraction(digest,value)
    for name in ('density','cosine','atoms','band_analytic','band48','band64',
                 'line_band_analytic'):
        value=getattr(saved,name);digest.update(name.encode()+b'\0')
        digest.update(np.asarray(value.shape,dtype='<i8').tobytes())
        digest.update(np.asarray(value,dtype='<f8').tobytes())
    return digest.hexdigest()


def _hash_state(grid,q,eta):
    digest=hashlib.sha256(b'F03_INTERFACE_STATE_GRID_V1\0')
    digest.update(int(grid.p).to_bytes(1,'little'))
    for values in (grid.x_cuts,grid.y_cuts,grid.station_cuts,q,eta):
        digest.update(len(values).to_bytes(8,'little'))
        for value in values:_hash_fraction(digest,value)
    for array in (grid.full_gathers,grid.free_gathers,grid.free_to_full):
        digest.update(np.asarray(array.shape,dtype='<i8').tobytes())
        digest.update(np.asarray(array,dtype='<i8').tobytes())
    return digest.hexdigest()


def _saved_functional(saved):
    coefficients=tuple(tuple(tuple(F.from_float(float(v)) for v in polynomial)
                       for polynomial in interval) for interval in saved.density)
    cosine=tuple(F.from_float(float(v)) for v in saved.cosine)
    atoms=tuple(tuple(F.from_float(float(v)) for v in row) for row in saved.atoms)
    return functional.Functional(saved.cuts,coefficients,cosine,atoms)


def _band(value,left,right):
    """Pure Functional signed wrench, with each external atom included once."""
    rational=[Z]*3;terms=[[],[],[]]
    for (a,b),density in zip(zip(value.cuts,value.cuts[1:]),value.coefficients):
        lo=max(a,left);hi=min(b,right)
        if lo>=hi:continue
        rows=tuple(rec._restrict(poly,(lo-a)/(b-a),(hi-lo)/(b-a)) for poly in density)
        for channel in (0,1):
            rational[channel]+=(hi-lo)*rec._product_integral(rows[channel],(O,))
            terms[channel].append((lo,hi,(value.cosine[channel],)))
        rational[2]+=(hi-lo)*(rec._product_integral(rows[1],(lo,hi-lo))+
                               rec._product_integral(rows[2],(O,)))
        terms[2].append((lo,hi,(value.cosine[2]+lo*value.cosine[1],
                                (hi-lo)*value.cosine[1])))
    for station,atom,include in ((Z,value.atoms[0],left==Z),
                                 (O,value.atoms[1],right==O)):
        if include:
            rational[0]+=atom[0];rational[1]+=atom[1]
            rational[2]+=station*atom[1]+atom[2]
    return tuple(rec.Action(v,tuple(t)) for v,t in zip(rational,terms))


def _atom_action(value,left,right):
    result=[Z,Z,Z]
    for station,atom,include in ((Z,value.atoms[0],left==Z),
                                 (O,value.atoms[1],right==O)):
        if include:
            result[0]+=atom[0];result[1]+=atom[1]
            result[2]+=station*atom[1]+atom[2]
    return tuple(rec.Action(v) for v in result)


def _compare_actions(actions,saved,name,budget,work,comparisons):
    for index,(action,target) in enumerate(zip(actions,saved.flat)):
        result=enclosure.compare_saved(action,float(target),c.F0,1e-10,
                                        budget=budget.action_budget)
        work['comparisons']+=1
        work['operations']+=result['comparison_work']['exact_operations']
        work['bits']+=result['comparison_work']['cumulative_integer_bits']
        if (work['comparisons']>budget.max_comparisons or
                work['operations']>budget.max_aggregate_operations or
                work['bits']>budget.max_aggregate_bits):
            raise ValueError('saved-interface aggregate Action budget exceeded')
        comparisons.append(_freeze({'name':name,'index':index,**result}))


def verify_interface(grid,q,eta,saved,*,budget):
    """Recompute and bind one exact interface plus eight fixed signed bands."""
    if (type(grid) is not topology.CompiledGrid or type(saved) is not SavedInterface or
            type(budget) is not InterfaceBudget):
        raise ValueError('factory grid, saved interface and explicit budget required')
    ni=len(grid.station_cuts)-1
    if (ni>budget.max_intervals or saved.cuts!=grid.station_cuts or
            ni!=len(saved.density)):
        raise ValueError('saved interface exact station partition mismatch')
    if (grid.free_dofs>budget.recovery_budget.max_free_dofs or
            ni>budget.recovery_budget.max_intervals):
        raise ValueError('saved interface state exceeds nested recovery inventory')
    q0=rec._vector(q,grid.free_dofs,budget.recovery_budget.max_integer_bits)
    eta0=rec._vector(eta,3,budget.recovery_budget.max_integer_bits-
                     sum(rec._bits(v) for v in q0))
    planned=192
    if planned>budget.max_comparisons:
        raise ValueError('saved-interface comparison inventory exceeds budget')
    if (planned*budget.action_budget.max_operations>budget.max_aggregate_operations or
            planned*budget.action_budget.max_total_bits>budget.max_aggregate_bits):
        raise ValueError('saved-interface worst-case aggregate Action budget exceeded')
    saved_bytes=sum(getattr(saved,name).nbytes for name in
        ('density','cosine','atoms','band_analytic','band48','band64','line_band_analytic'))
    fraction_slot=512+(2*budget.action_budget.max_fraction_bits+7)//8
    # Each retained comparison contains scalar operands/bounds, two hashes,
    # status/scope strings and nested work metadata. Thirty-two maximum-size
    # fraction/hash slots plus fixed Python-object overhead intentionally
    # over-count that record. Saved Functional coefficients are charged too.
    comparison_records=planned*(32*fraction_slot+4096)
    saved_functional_storage=(ni*3*6+3+6)*fraction_slot
    # Four retained lists contain 96 Actions. During construction the total,
    # line and endpoint 3-tuples coexist (102), and one unary subtraction plus
    # its result raises the evaluated peak to at least 104. A 128-slot bound
    # also charges loop/local references and fixed-band temporaries. Each slot
    # admits one rational plus ni*(two endpoints+six coefficients). Fraction
    # storage converts the numerator+denominator bit cap to bytes explicitly
    # and adds conservative Python integer/Fraction object overhead.
    recovery_fraction_slot=512+(2*rec.BITS+7)//8
    live_action_storage=128*(1+8*ni)*recovery_fraction_slot
    workspace=(saved_bytes+budget.recovery_budget.max_work_bytes+
               budget.action_budget.max_work_bytes+comparison_records+
               saved_functional_storage+live_action_storage+ni*3*6*256)
    if workspace>budget.max_work_bytes:
        raise ValueError('saved-interface workspace estimate exceeds budget')
    recovered=rec.recover(grid,q0,eta0,budget.recovery_budget)
    owned_saved=_saved_functional(saved)
    scale=F.from_float(c.F0)
    density_error=max(abs(F.from_float(float(a))-b)/scale for a,b in
        zip(saved.density.flat,(v for interval in recovered.interface.coefficients
                                for row in interval for v in row)))
    cosine_error=max(abs(F.from_float(float(a))-b)/scale
                     for a,b in zip(saved.cosine,recovered.interface.cosine))
    atom_error=max(abs(F.from_float(float(a))-b)/scale for a,b in
        zip(saved.atoms.flat,(v for row in recovered.interface.atoms for v in row)))
    root_expected=tuple(v-e for v,e in zip(recovered.root_resultants,recovered.eta))
    tip_expected=tuple(-v for v in recovered.tip_resultants)
    root_partition=max(abs(F.from_float(float(a))-b)/scale
                       for a,b in zip(saved.atoms[0],root_expected))
    tip_partition=max(abs(F.from_float(float(a))-b)/scale
                      for a,b in zip(saved.atoms[1],tip_expected))
    recovered_total=[];recovered_line=[];saved_total=[];saved_line=[]
    for left,right in BANDS:
        total=rec.band(recovered,left,right)
        atom=_atom_action(recovered.interface,left,right)
        recovered_total.extend(total);recovered_line.extend(a-b for a,b in zip(total,atom))
        stotal=_band(owned_saved,left,right)
        satom=_atom_action(owned_saved,left,right)
        saved_total.extend(stotal);saved_line.extend(a-b for a,b in zip(stotal,satom))
    arrays=(('recovered_band_analytic',recovered_total,saved.band_analytic),
            ('recovered_band48',recovered_total,saved.band48),
            ('recovered_band64',recovered_total,saved.band64),
            ('recovered_line_band_analytic',recovered_line,saved.line_band_analytic),
            ('saved_functional_band_analytic',saved_total,saved.band_analytic),
            ('saved_functional_band48',saved_total,saved.band48),
            ('saved_functional_band64',saved_total,saved.band64),
            ('saved_functional_line_band_analytic',saved_line,saved.line_band_analytic))
    comparisons=[];work={'comparisons':0,'operations':0,'bits':0}
    for name,actions,targets in arrays:
        _compare_actions(actions,targets,name,budget,work,comparisons)
    failed=[item for item in comparisons if item['status']=='FAILED']
    held=[item for item in comparisons if item['status']=='HOLD_UNRESOLVED']
    failures=[]
    for name,value,limit in (('density',density_error,INTERFACE_LIMIT),
        ('cosine',cosine_error,INTERFACE_LIMIT),('atoms',atom_error,INTERFACE_LIMIT),
        ('root_partition',root_partition,PARTITION_LIMIT),
        ('tip_partition',tip_partition,PARTITION_LIMIT)):
        if value>limit:failures.append(f'{name} saved interface mismatch')
    if failed:failures.append('one or more certified saved band comparisons failed')
    status=('FAILED' if failures else 'HOLD_UNRESOLVED' if held else 'PASSED')
    reasons=tuple(failures+(['one or more certified saved band comparisons unresolved']
                            if held else []))
    result=object.__new__(InterfaceResult)
    values=dict(recovery=recovered,saved_functional=owned_saved,
        metrics=_freeze(dict(density_scaled=density_error,cosine_scaled=cosine_error,
            atoms_scaled=atom_error,root_partition_scaled=root_partition,
            tip_partition_scaled=tip_partition,failed_comparisons=len(failed),
            unresolved_comparisons=len(held))),comparisons=tuple(comparisons),
        input_sha256=MappingProxyType({'saved_interface':_hash_saved(saved),
            'grid_q_eta':_hash_state(grid,q0,eta0)}),
        diagnostics=MappingProxyType(dict(comparisons=work['comparisons'],
            aggregate_action_operations=work['operations'],aggregate_action_bits=work['bits'],
            workspace_estimate_bytes=workspace,
            retained_comparison_estimate_bytes=comparison_records,
            saved_functional_estimate_bytes=saved_functional_storage,
            live_action_estimate_bytes=live_action_storage,
            recovery_recomputations=1,
            equilibrium_solves=0,endpoint_atoms_per_band='once',
            origin_moment='s*Fy+intrinsic',scope=SCOPE)),status=status,
        failures=reasons)
    for name,value in values.items():object.__setattr__(result,name,value)
    return result
