"""Saved-state free-row derivative localization; no formulation assessment."""
from pathlib import Path
import hashlib,json,os,sys
import numpy as np
from scipy import sparse
from threadpoolctl import threadpool_info
from anysolver import stiffened_shell as ss
import anysolver._stiffened_shell_ge_finite_experimental as finite
from anysolver._stiffened_shell_ge_distributing_finite import PreparedFiniteDistributingAttachment
# Diagnostic-only isolated dispatch. No shared source or registered graph changed.
from anysolver import _ge_beam3_variational_shell as value_map
from anysolver import _stiffened_shell_algorithmic_pullback as pullback
from anysolver import _ge_beam3_g3c_so3_numerics as stable
from anysolver._ge_beam3_g3c_stable.joint import _exp_terms as stable_exp_terms
value_map.so3_exp=stable.so3_exp
value_map.so3_log=stable.so3_log
pullback._exp_terms=stable_exp_terms

from test_stiffened_shell_ge_distributing_material import definition
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2];SITE=ROOT/'site'
assert Path(finite.__file__).resolve().is_relative_to(SITE)
assert not sys.flags.optimize and os.environ['NUMBA_DISABLE_JIT']=='1'
pools=threadpool_info();assert pools and all(p['num_threads']==1 for p in pools)
owner=ss.create_analysis(definition=definition())
try:
    prefix=(ROOT/'failed-prefix-v9.bin').read_bytes();owner.restore(prefix)
    driver=owner._finite_driver
    with np.load(ROOT/'failed-base-v9.npz') as data:
        state=finite._State(*(data[name].copy() for name in ('q','frames','cells','resultants','multipliers')))
        direction=data['direction'].copy();pattern=data['pattern'].copy()
    count=owner._K.shape[0];size=count+len(state.multipliers)
    weights=np.r_[owner._coordinate_scale,np.ones(size-count)]
    free=owner._free;constraint=np.arange(count,size)
    shell_slots={id(element):slots for _,element,slots,_ in owner._shell_parts}
    assert len(owner._beam_parts)==1 and not owner._connections
    beam,beam_slots,_=owner._beam_parts[0]
    capture={}
    def record(label,slots,force,matrix):
        slots=np.asarray(slots,dtype=int)
        if label not in capture:capture[label]=[np.zeros(size),sparse.csc_matrix((size,size))]
        np.add.at(capture[label][0],slots,force)
        entries=sparse.coo_matrix(matrix)
        capture[label][1]+=sparse.coo_matrix((entries.data,(slots[entries.row],slots[entries.col])),shape=(size,size)).tocsc()
    shell_original=finite.q4_algorithmic_response
    beam_type=type(beam.operator);beam_original=beam_type.evaluate
    attachment_original=PreparedFiniteDistributingAttachment.evaluate
    def shell_response(model,element,*args,**kwargs):
        response=shell_original(model,element,*args,**kwargs)
        record('shell',shell_slots[id(element)],response[0],response[1]);return response
    def beam_response(operator,*args,**kwargs):
        assert operator is beam.operator
        response=beam_original(operator,*args,**kwargs)
        matrix=finite.spatial_jacobian(response.residual,response.hessian+response.hessian_low)
        record('beam',beam_slots+owner._shell_count,response.residual,matrix);return response
    def attachment_response(adapter,*args,**kwargs):
        block=attachment_original(adapter,*args,**kwargs)
        record('attachment',block.slots,block.residual,block.tangent);return block
    def evaluate(actual):
        capture.clear()
        full=driver._assemble(actual,1.01,driver._shell_origins,driver._beam_origins,pattern=pattern)
        return full,{name:(force.copy(),matrix.copy()) for name,(force,matrix) in capture.items()}
    finite.q4_algorithmic_response=shell_response;beam_type.evaluate=beam_response
    PreparedFiniteDistributingAttachment.evaluate=attachment_response
    try:
        base,parts=evaluate(state)
        reconstructed=sum((part[0] for part in parts.values()),np.zeros(size));reconstructed[:count]-=1.01*pattern
        matrix=sum((part[1] for part in parts.values()),sparse.csc_matrix((size,size)))
        force_error=float(np.linalg.norm((reconstructed-base[0])*weights)/max(np.linalg.norm(base[0]*weights),1.))
        matrix_error=float(sparse.linalg.norm(matrix-base[1])/max(sparse.linalg.norm(base[1]),1.))
        assert force_error<=1e-10 and matrix_error<=1e-10,(force_error,matrix_error)
        derivatives={name:[] for name in parts}
        for h in (1e-4,1e-5,4e-6,1e-6,1e-7):
            _,plus=evaluate(driver._advance(state,direction,h))
            _,minus=evaluate(driver._advance(state,direction,-h))
            for name,(force,matrix) in parts.items():
                predicted=matrix@direction
                observed=(plus[name][0]-minus[name][0])/(2*h)
                errors={}
                for label,rows in (('free',free),('constraint',constraint)):
                    expected=predicted[rows]*weights[rows];difference=(observed-predicted)[rows]*weights[rows]
                    errors[label]=dict(predicted_norm=float(np.linalg.norm(expected)),
                        absolute_error=float(np.linalg.norm(difference)),
                        relative_error=(float(np.linalg.norm(difference)/np.linalg.norm(expected)) if np.linalg.norm(expected)>0 else None))
                derivatives[name].append(dict(h=h,**errors))
        result=dict(scope='development localization, not qualification or convergence acceptance',
            model=owner._identity,anchor_sha256=hashlib.sha256((ROOT/'failed-base-v9.npz').read_bytes()).hexdigest(),
            prefix_sha256=hashlib.sha256(prefix).hexdigest(),pools=pools,
            actual_imports={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in
              (Path(finite.__file__),Path(ss.__file__))},
            fixture_sha256=hashlib.sha256((REPO/'tests/test_stiffened_shell_ge_distributing_material.py').read_bytes()).hexdigest(),
            reconstruction=dict(force_relative=force_error,matrix_relative=matrix_error),derivatives=derivatives)
        assert owner.checkpoint()==prefix
        (ROOT/'stable-components-v21.json').open('x',encoding='utf-8').write(json.dumps(result,indent=2,allow_nan=False)+'\n')
        print(json.dumps(dict(reconstruction=result['reconstruction'],free_errors={name:[v['free']['relative_error'] for v in values] for name,values in derivatives.items()})))
    finally:
        finite.q4_algorithmic_response=shell_original;beam_type.evaluate=beam_original
        PreparedFiniteDistributingAttachment.evaluate=attachment_original
finally:owner.close()
