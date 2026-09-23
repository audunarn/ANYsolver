"""Bind saved signed 48/64 Green observations to one owned physical Functional."""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction as F
import hashlib
import math
from types import MappingProxyType
import numpy as np
from scripts import _b3_e4_f03_local_functional as green

ORDERS=(48,64)
COMPONENTS=('diagonal','offdiagonal','atom_cross','atom_gram','sum_abs_terms','cancellation_ratio')
CHANNEL_FLAGS=('channel_finite','channel_nonnegative','channel_nonzero_valid')
TOTAL_FLAGS=('total_finite','total_nonnegative','admissible')
SCOPE='SAVED_SIGNED_GREEN_OBSERVATIONS_ONLY'
LIMIT=F.from_float(1e-10)
FLOOR=F(1000**2)


def _owned(array,shape,dtype):
    if type(array) is not np.ndarray or array.dtype!=dtype or array.shape!=shape:
        raise ValueError('explicit exact-shape saved norm array required')
    value=np.frombuffer(array.tobytes(order='C'),dtype=dtype).reshape(shape)
    if dtype==np.float64 and np.isinf(value).any():
        raise ValueError('undefined saved norms use NaN, not infinity')
    return value


@dataclass(frozen=True,slots=True)
class SavedNorm:
    """Fixed 48/64 inventory; NaN is allowed only as an unavailable observation."""
    channels:np.ndarray
    totals:np.ndarray
    components:np.ndarray
    channel_flags:np.ndarray
    total_flags:np.ndarray
    exact_zero:np.ndarray
    failures:tuple

    def __post_init__(self):
        for name,shape,dtype in (
            ('channels',(2,3),np.float64),('totals',(2,),np.float64),
            ('components',(2,3,6),np.float64),('channel_flags',(2,3,3),np.bool_),
            ('total_flags',(2,3),np.bool_),('exact_zero',(2,),np.bool_)):
            object.__setattr__(self,name,_owned(getattr(self,name),shape,np.dtype(dtype)))
        if type(self.failures) not in (tuple,list) or len(self.failures)!=2:
            raise ValueError('both ordered failure inventories required')
        inventories=[]
        for failures in self.failures:
            if type(failures) not in (tuple,list) or len(failures)>32:
                raise ValueError('bounded saved norm failure inventory required')
            records=[]
            for record in failures:
                if type(record) not in (tuple,list) or len(record)!=3:
                    raise ValueError('failure requires stage/channel/reason')
                stage,channel,reason=record
                if (type(stage) is not str or not 1<=len(stage)<=128 or
                        (channel is not None and (type(channel) is not int or channel not in (0,1,2))) or
                        type(reason) is not str or not 1<=len(reason)<=1024):
                    raise ValueError('invalid saved numerical failure metadata')
                records.append((stage,channel,reason))
            inventories.append(tuple(records))
        object.__setattr__(self,'failures',tuple(inventories))


@dataclass(frozen=True,slots=True)
class NormBudget:
    max_intervals:int
    max_integer_bits:int
    max_operations:int
    max_work_bytes:int

    def __post_init__(self):
        if any(type(v) is not int or v<=0 for v in (
                self.max_intervals,self.max_integer_bits,self.max_operations,self.max_work_bytes)):
            raise ValueError('explicit positive norm budgets required')


def _number(value):
    if value is None:return float('nan')
    if type(value) not in (float,np.float64):
        raise ValueError('raw norm observations require float scalars or missing values')
    if math.isinf(value):raise ValueError('raw infinite norm must be marked unavailable')
    return float(value)


def _pack(observations):
    # Internal adapter only; the verifier never produces or replaces saved evidence.
    if len(observations)!=2 or tuple(x['order'] for x in observations)!=ORDERS:
        raise ValueError('fixed ordered 48/64 observations required')
    for item in observations:
        for name in CHANNEL_FLAGS:
            if (type(item[name]) not in (tuple,list) or len(item[name])!=3 or
                    any(type(v) not in (bool,np.bool_) for v in item[name])):
                raise ValueError('raw channel validity flags must be explicit booleans')
        if any(type(item[name]) not in (bool,np.bool_) for name in (*TOTAL_FLAGS,'exact_zero')):
            raise ValueError('raw total validity flags must be explicit booleans')
    return SavedNorm(
        np.array([[_number(v) for v in x['channels']] for x in observations],dtype=np.float64),
        np.array([_number(x['squared_norm']) for x in observations],dtype=np.float64),
        np.array([[[_number(x[name][i]) for name in COMPONENTS] for i in range(3)]
                  for x in observations],dtype=np.float64),
        np.array([[list(x[name]) for name in CHANNEL_FLAGS] for x in observations],dtype=np.bool_),
        np.array([[x[name] for name in TOTAL_FLAGS] for x in observations],dtype=np.bool_),
        np.array([x['exact_zero'] for x in observations],dtype=np.bool_),
        tuple(tuple((r['stage'],r['channel'],r['reason']) for r in x['failures'])
              for x in observations))


def _numeric_parity(first,second):
    missing=np.isnan(first)
    return (np.array_equal(missing,np.isnan(second)) and
            first[~missing].tobytes()==second[~missing].tobytes())


def _same(first,second):
    numeric=('channels','totals','components')
    boolean=('channel_flags','total_flags','exact_zero')
    return (all(_numeric_parity(getattr(first,n),getattr(second,n)) for n in numeric) and
            all(np.array_equal(getattr(first,n),getattr(second,n)) for n in boolean) and
            first.failures==second.failures)


def _same_float(first,second):
    """Binary64 identity, including the sign of zero."""
    return np.float64(first).tobytes()==np.float64(second).tobytes()


def _total_consistent(channels,total):
    """Bind the reported total to the declared legacy finite-channel sum."""
    if not all(math.isfinite(float(value)) for value in channels):
        return False
    try:
        expected=math.fsum(float(value) for value in channels)
    except OverflowError:
        # A known finite-input sum overflow is unavailable and cannot pass.
        return math.isnan(float(total))
    return math.isfinite(float(total)) and _same_float(total,expected)


def _hash(value,saved):
    h=hashlib.sha256(b'F03_SAVED_SIGNED_NORM_V1\0')
    for values in (value.cuts,tuple(v for row in value.coefficients for p in row for v in p),
                   value.cosine,tuple(v for row in value.atoms for v in row)):
        h.update(len(values).to_bytes(8,'little'))
        for v in values:
            h.update(b'-' if v<0 else b'+')
            for integer in (abs(v.numerator),v.denominator):
                raw=integer.to_bytes(max(1,(integer.bit_length()+7)//8),'little')
                h.update(len(raw).to_bytes(8,'little'));h.update(raw)
    for name in ('channels','totals','components','channel_flags','total_flags','exact_zero'):
        data=getattr(saved,name);h.update(name.encode());h.update(data.tobytes())
    for records in saved.failures:
        h.update(len(records).to_bytes(4,'little'))
        for stage,channel,reason in records:
            for item in (stage,str(channel),reason):
                raw=item.encode('utf-8');h.update(len(raw).to_bytes(8,'little'));h.update(raw)
    return h.hexdigest()


def input_identity(value,saved):
    """Bind one owned Functional and saved 48/64 observation record."""
    if type(value) is not green.Functional or type(saved) is not SavedNorm:
        raise ValueError('owned Functional and SavedNorm required')
    owned_value=green.Functional(value.cuts,value.coefficients,value.cosine,value.atoms)
    owned_saved=SavedNorm(**{name:getattr(saved,name) for name in saved.__dataclass_fields__})
    return _hash(owned_value,owned_saved)


def _freeze(value):
    if isinstance(value,dict):return MappingProxyType({k:_freeze(v) for k,v in value.items()})
    if isinstance(value,(tuple,list)):return tuple(_freeze(v) for v in value)
    return value


def verify_norm(value,saved,*,budget):
    if type(value) is not green.Functional or type(saved) is not SavedNorm or type(budget) is not NormBudget:
        raise ValueError('owned Functional, SavedNorm and explicit norm budget required')
    ni=len(value.cuts)-1
    if ni>budget.max_intervals:raise ValueError('norm interval budget exceeded')
    count=len(value.cuts)+ni*18+9
    bits=sum(v.numerator.bit_length()+v.denominator.bit_length()
             for values in (value.cuts,value.cosine,*value.atoms,
                 *(p for row in value.coefficients for p in row)) for v in values)
    if bits>budget.max_integer_bits:raise ValueError('norm integer inventory budget exceeded')
    operations=2*3*ni*(64**2*96+64*96)+16384
    workspace=2*count*(512+(2*green.INPUT_INTEGER_BITS+7)//8)+64**2*8*96+ni*3*8*256+65536
    if operations>budget.max_operations or workspace>budget.max_work_bytes:
        raise ValueError('norm work or workspace budget exceeded')
    value=green.Functional(value.cuts,value.coefficients,value.cosine,value.atoms)
    saved=SavedNorm(**{name:getattr(saved,name) for name in saved.__dataclass_fields__})
    # No catches here: unexpected, geometry and input failures remain distinct.
    observations=tuple(green.norm_observation_at_order(value,order) for order in ORDERS)
    if any(type(x['intervals']) is not int or x['intervals']!=ni for x in observations):
        raise ValueError('raw norm interval identity mismatch')
    measured=_pack(observations)
    parity=_same(measured,saved)
    deltas=[]
    for channel in range(3):
        a,b=measured.channels[:,channel]
        deltas.append(abs(F.from_float(float(a))-F.from_float(float(b)))/
                      max(abs(F.from_float(float(a))),abs(F.from_float(float(b))),FLOOR)
                      if math.isfinite(a) and math.isfinite(b) else None)
    a,b=measured.totals
    deltas.append(abs(F.from_float(float(a))-F.from_float(float(b)))/
                  max(abs(F.from_float(float(a))),abs(F.from_float(float(b))),FLOOR)
                  if math.isfinite(a) and math.isfinite(b) else None)
    resolution=max(deltas) if all(x is not None for x in deltas) else None
    exact_channels=tuple(value.cosine[i]==0 and
        all(v==0 for row in value.coefficients for v in row[i]) and
        all(atom[i]==0 for atom in value.atoms) for i in range(3))
    channel_support_valid=all(
        measured.channels[k,i]==0 if exact_channels[i] else measured.channels[k,i]!=0
        for k in range(2) for i in range(3))
    exact_total_valid=(not value.exact_zero or bool((measured.totals==0).all()))
    total_consistent=all(_total_consistent(measured.channels[k],measured.totals[k])
                         for k in range(2))
    # Flags cannot waive signed value checks; failure inventory independently rejects.
    numerical=(bool(np.all(measured.channel_flags)) and bool(np.all(measured.total_flags)) and
               bool(np.isfinite(measured.channels).all()) and bool(np.isfinite(measured.totals).all()) and
               bool(np.isfinite(measured.components).all()) and
               bool((measured.channels>=0).all()) and bool((measured.totals>=0).all()) and
               channel_support_valid and exact_total_valid and total_consistent and
               all(bool(v)==value.exact_zero for v in measured.exact_zero) and
               not any(measured.failures))
    status='FAILED' if not parity or not numerical else (
           'HOLD_UNRESOLVED' if resolution is None or resolution>LIMIT else 'PASSED')
    return _freeze(dict(status=status,scope=SCOPE,input_sha256=_hash(value,saved),
        saved_bit_parity=parity,numerically_admissible=numerical,
        raw48=observations[0],raw64=observations[1],resolution=resolution,
        channel_and_total_resolution=deltas,
        diagnostics=dict(norm_orders=ORDERS,norm_evaluations=2,equilibrium_solves=0,
            operations_estimate=operations,workspace_estimate_bytes=workspace,
            input_integer_bits=bits,physical_moment_divisions_per_operand=1)))
