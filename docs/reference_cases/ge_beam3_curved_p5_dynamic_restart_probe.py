"""Strict research dynamic restart; integrity is not history authenticity."""

from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import sys
import tempfile

import numpy as np

from docs.reference_cases import ge_beam3_curved_p5_dynamic_assembly_probe as dynamic
from docs.reference_cases.ge_beam3_curved_p5_history_path_probe import digest


SCHEMA = 'GE_BEAM3_P5_RESEARCH_DYNAMIC_ASSEMBLY_RESTART_V1'
MAX_BYTES = 4*1024*1024


class RestartError(ValueError):
    """Rejected before returning any restored mutable model."""


def canonical(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False,
                       ensure_ascii=True,default=lambda a:a.tolist())+'\n').encode('ascii')


def _sha(value): return hashlib.sha256(canonical(value)).hexdigest()


def _keys(value,names):
    if type(value) is not dict or set(value)!=set(names): raise RestartError('exact dynamic restart fields required')


def _pairs(pairs):
    record={}
    for key,value in pairs:
        if key in record: raise RestartError('duplicate restart key')
        record[key]=value
    return record


def _constant(value): raise RestartError('nonfinite restart number')


def _parse(payload):
    if type(payload) is not bytes or not 0<len(payload)<=MAX_BYTES: raise RestartError('bounded restart bytes required')
    quoted=escaped=False;depth=0
    for byte in payload:
        if quoted:
            if escaped: escaped=False
            elif byte==92: escaped=True
            elif byte==34: quoted=False
        elif byte==34: quoted=True
        elif byte in (91,123):
            depth+=1
            if depth>32: raise RestartError('restart nesting bound')
        elif byte in (93,125): depth-=1
    record=json.loads(payload.decode('ascii'),object_pairs_hook=_pairs,parse_constant=_constant)
    if canonical(record)!=payload: raise RestartError('strict canonical dynamic JSON required')
    _keys(record,('schema','identity','state','accepted','payload_sha256'))
    body={k:v for k,v in record.items() if k!='payload_sha256'}
    if record['schema']!=SCHEMA or record['payload_sha256']!=_sha(body):
        raise RestartError('dynamic restart schema/hash mismatch')
    return record


def _identity(model):
    if type(model) is not dynamic.DynamicAssemblyProbe: raise RestartError('exact expected dynamic assembly required')
    model._check_state(model.committed)
    names=['anysolver.ge_beam3_curved_reference','anysolver._ge_beam3_mixed_ad']
    names+=['docs.reference_cases.ge_beam3_curved_p5_'+suffix for suffix in (
        'algebra_probe','finite_probe','history_path_probe','finite_inertia_probe',
        'implicit_dynamics_probe','midpoint_dynamics_probe','dynamic_assembly_probe','dynamic_restart_probe')]
    sources={name:hashlib.sha256(Path(sys.modules[name].__file__).read_bytes()).hexdigest() for name in names}
    return {'candidate':'CANDIDATE_GE_BEAM3_DC_CURVED_OBJECTIVE_LIFT_V1','production_qualified':False,
        'scope':'ELASTIC_SHARED_RETAINED_SPIN_MIDPOINT_RESEARCH','state_schema':dynamic.SCHEMA,
        'model_sha256':model._identity(),'connectivity':[r.tolist() for r in model._maps],
        'fixed_nodes':list(model._fixed),'update':'SHARED_SPATIAL_V_ELEMENT_Q_EQUALS_V_R0',
        'cell_inertia':'RETAINED_NO_TRACE_MASS',
        'elements':[{'coordinates':e._reference.coordinates.tolist(),'frames':e._reference.nodal_triads.tolist(),
                     'section':e._elastic.section.tolist(),'inertia':e._kinetic.section_mass.tolist(),'order':e._order}
                    for e in model._elements],
        'implementation_sources':sources,'runtime':{'python':platform.python_version(),'numpy':np.__version__,
            'platform':sys.platform,'machine':platform.machine(),
            'threads':{key:os.environ.get(key) for key in
                       ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')}}}


def _fresh(expected):
    if type(expected) is not dynamic.DynamicAssemblyProbe or expected._pending is not None:
        raise RestartError('expected model must be exact and have no pending trial')
    expected._check_state(expected.committed)
    elements=expected._elements;order=elements[0]._order
    if any(e._order!=order for e in elements): raise RestartError('registered shared quadrature order required')
    made=dynamic.DynamicAssemblyProbe([e._reference for e in elements],[r.tolist() for r in expected._maps],
        [e._elastic.section for e in elements],[e._kinetic.section_mass for e in elements],
        fixed_nodes=expected._fixed,order=order)
    if made._identity()!=expected._identity(): raise RestartError('expected graph caches/layout differ from clean construction')
    return made


def _decode(value,schema):
    if schema is float:
        if type(value) is not float or not math.isfinite(value): raise RestartError('finite JSON float required without coercion')
        return value
    kind,spec=schema
    if kind=='constant':
        if type(value) is not type(spec) or value!=spec: raise RestartError('exact schema/model constant required')
        return value
    if kind=='integer':
        if type(value) is not int or not 0<=value<=spec: raise RestartError('bounded integer required')
        return value
    if kind=='array':
        def nested(item,shape):
            if not shape: return _decode(item,float)
            if type(item) is not list or len(item)!=shape[0]: raise RestartError('exact dynamic array shape required')
            return [nested(x,shape[1:]) for x in item]
        result=np.array(nested(value,spec),dtype=float);result.setflags(write=False);return result
    if kind=='sequence':
        count,item=spec
        if type(value) is not list or len(value)!=count: raise RestartError('exact element count required')
        return tuple(_decode(v,item) for v in value)
    _keys(value,spec)
    made=kind(**{key:_decode(value[key],field) for key,field in spec.items()})
    if kind is dynamic.ChainState and ((made.epoch==0 and made.time!=0.) or (made.epoch>0 and made.time<=0.)):
        raise RestartError('dynamic epoch/time consistency required')
    return made


def _schemas(model):
    array=lambda *shape:('array',shape)
    integer=lambda maximum:('integer',maximum)
    count,nodes,size=model._count,model._nodes,model._size
    parts=('sequence',(count,array(24)))
    state=(dynamic.ChainState,{'schema':('constant',dynamic.SCHEMA),'model_sha256':('constant',model._identity()),
        'epoch':integer(2147483647),'time':float,'positions':array(nodes,3),'rotations':array(nodes,3,3),
        'cell_rotations':array(count,2,3,3),'nodal_velocity':array(nodes,3),'cell_angular_velocity':array(count,2,3)})
    stage=(dynamic.ChainStage,{'endpoint_guess':state,'residual':array(size),'tangent':array(size,size),
        'elastic_force':array(size),'inertia':array(size),'element_forces':parts,'element_inertia':parts})
    response=(dynamic.ChainResponse,{'state':state,'stage':stage,'elastic_energy':float,'kinetic_energy':float,
        'endpoint_force':array(size),'endpoint_element_forces':parts,'trace_iterations':integer(8),
        'trace_evaluations':integer(64),'trace_residual_norm':float})
    trial=(dynamic.ChainTrial,{'origin':state,'increment':array(size),'step':float,'forces':array(nodes,3),
        'response':response,'residual_norm':float,'iterations':integer(16),'evaluations':integer(128)})
    return state,trial


def loads(payload,expected):
    """Restore to a fresh model. The caller's expected model is never modified."""
    try:
        record=_parse(payload)
        if canonical(record['identity'])!=canonical(_identity(expected)):
            raise RestartError('expected model/source/runtime identity mismatch')
        staged=_fresh(expected);state_schema,trial_schema=_schemas(staged)
        state=_decode(record['state'],state_schema);staged._check_state(state)
        if state.epoch==0:
            if record['accepted'] is not None or digest(state)!=digest(staged.committed):
                raise RestartError('initial restart must be the exact reference/rest state')
            return staged
        trial=_decode(record['accepted'],trial_schema)
        if state.epoch!=trial.origin.epoch+1 or digest(state)!=digest(trial.response.state):
            raise RestartError('accepted/committed epoch or state mismatch')
        staged._check_state(trial.origin)
        if trial.origin.epoch==0 and digest(trial.origin)!=digest(staged.committed):
            raise RestartError('first accepted origin must be the exact initial state')
        # Verify the saved origin; never silently repair its algebraic traces.
        guard=dynamic._watchdog()
        origin=staged._endpoint(trial.origin,trial.origin.rotations,guard)
        if np.linalg.norm(origin[1][staged._traces])/staged._length>1e-11:
            raise RestartError('saved origin algebraic equilibrium mismatch')
        staged._reconstruct(trial)
        staged._checkpoint=(deepcopy(state),deepcopy(trial))
        return staged
    except RestartError: raise
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError,RecursionError,UnicodeError,
            dynamic.DynamicStepError,dynamic.DynamicTransactionError,np.linalg.LinAlgError) as error:
        raise RestartError('invalid dynamic research restart') from error


def dumps(model):
    try:
        identity=_identity(model)
        if model._pending is not None: raise RestartError('commit/discard pending graph trial before export')
        state,trial=model._checkpoint
        if trial is not None: model.replay()
        body={'schema':SCHEMA,'identity':identity,'state':asdict(state),'accepted':None if trial is None else asdict(trial)}
        payload=canonical({**body,'payload_sha256':_sha(body)})
        loads(payload,model)
        return payload
    except RestartError: raise
    except (ValueError,TypeError,AttributeError,OverflowError,RecursionError,
            dynamic.DynamicStepError,dynamic.DynamicTransactionError) as error:
        raise RestartError('invalid dynamic research export') from error


def write_exclusive(path,model):
    """Same-directory exclusive publication; not power-loss durability."""
    payload=dumps(model);target=Path(path)
    descriptor,temporary=tempfile.mkstemp(prefix='.ge-b3-dynamic-restart-',dir=target.parent)
    try:
        with os.fdopen(descriptor,'wb') as stream:
            stream.write(payload);stream.flush();os.fsync(stream.fileno())
        os.link(temporary,target)
    finally:
        os.unlink(temporary)
    return hashlib.sha256(payload).hexdigest()
