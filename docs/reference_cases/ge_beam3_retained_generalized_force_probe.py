"""One-macro retained generalized force research probe, never native commit."""
from time import monotonic
import numpy as np
from anysolver._ge_beam3_retained_generalized import RetainedGeneralizedOperator
from anysolver._ge_beam3_fibre_line_work import evaluate as line_work
from anysolver._ge_beam3_generalized_static_boundary import cell_couple_load,spatial_jacobian
from anysolver._ge_beam3_p5.compensated_coordinates import split_sum
from anysolver._ge_beam3_p5.algebra import rotation
from anysolver._ge_beam3_p5_seeded.core import canonical

def virgin(operator):
    return dict(positions=operator.reference.coordinates.copy(),position_low=np.zeros((3,3)),
        nodal_frames=operator.reference.nodal_triads.copy(),cell_rotations=np.tile(np.eye(3),(2,1,1)),
        resultants=np.zeros(18))

def assemble(operator,state,origin,force,couple,parameter,check=lambda:None):
    check()
    e=operator.evaluate(state['positions'],state['position_low'],state['nodal_frames'],
        state['cell_rotations'],state['resultants'],origin=origin,check=check)
    w=line_work(operator.reference,state['positions'],state['position_low'],
        state['cell_rotations'],parameter*force,order=operator.order)
    rc=e.residual-w.gradient
    jac=spatial_jacobian(rc,e.hessian+e.hessian_low-w.hessian)
    net=rc-cell_couple_load(operator,parameter*couple)
    return net,jac,e,w

def advance(state,step):
    if np.shape(step)!=(42,) or not np.isfinite(step).all():raise ValueError('finite retained step required')
    angular=[step[6*i+3:6*i+6] for i in range(3)]+[step[18+3*i:21+3*i] for i in range(2)]
    if max(np.linalg.norm(v) for v in angular)>=.9*np.pi:raise ValueError('retained step requires cutback')
    s={k:v.copy() for k,v in state.items()}
    for i in range(3):
        for axis in range(3):
            s['positions'][i,axis],s['position_low'][i,axis]=split_sum((
                float(state['positions'][i,axis]),float(state['position_low'][i,axis]),float(step[6*i+axis])))
        s['nodal_frames'][i]=rotation(step[6*i+3:6*i+6])@state['nodal_frames'][i]
    for i in range(2):s['cell_rotations'][i]=rotation(step[18+3*i:21+3*i])@state['cell_rotations'][i]
    s['resultants']+=step[24:]
    return s

def solve(operator,force,couple,*,progress=lambda value:None):
    if type(operator) is not RetainedGeneralizedOperator:raise ValueError('exact generalized operator required')
    force=np.array(force,dtype=float,copy=True);couple=np.array(couple,dtype=float,copy=True)
    if force.shape!=(3,) or couple.shape!=(3,) or not np.isfinite(np.r_[force,couple]).all():
        raise ValueError('finite force and couple required')
    start=monotonic();identity=operator.identity;origin=operator.cell.virgin();origin_bytes=canonical(origin)
    state=virgin(operator);accepted=virgin(operator);records=[];last_trial=None
    length=float(np.linalg.norm(operator.reference.coordinates[-1]-operator.reference.coordinates[0]))
    if not np.isfinite(length) or length<=0:raise ValueError('positive characteristic length')
    scale=np.ones(42)
    for i in range(3):scale[6*i+3:6*i+6]=length
    scale[18:30]=length
    free=np.arange(6,42)
    def safe():
        operator.guard()
        if operator.identity!=identity or canonical(origin)!=origin_bytes:raise ValueError('frozen probe input changed')
        if monotonic()-start>120:raise RuntimeError('retained generalized diagnostic deadline')
    def metric(r):return (float(np.linalg.norm((r/scale)[6:24])),float(np.linalg.norm((r/scale)[24:])))
    try:
        for parameter in (.5,1.):
            for iteration in range(25):
                safe();r,j,e,w=assemble(operator,state,origin,force,couple,parameter,safe);errors=metric(r)
                progress(dict(stage='iteration',parameter=parameter,iteration=iteration,equilibrium=errors[0],compatibility=errors[1]))
                if max(errors)<=1e-11:
                    if canonical(e.history)!=origin_bytes:raise ValueError('elastic-only probe cannot commit plastic history')
                    records.append(dict(parameter=parameter,iterations=iteration,equilibrium=errors[0],compatibility=errors[1],
                        state={k:v.copy() for k,v in state.items()},reaction=r[:6].copy(),work=w.value))
                    accepted={k:v.copy() for k,v in state.items()};break
                if iteration==24:raise RuntimeError('retained generalized Newton limit')
                step=np.zeros(42);step[free]=np.linalg.solve(j[np.ix_(free,free)],-r[free])
                if not np.isfinite(step).all():raise ValueError('nonfinite retained Newton step')
                angle=max(np.linalg.norm(step[s:s+3]) for s in (3,9,15,18,21))
                fraction=min(1.,.45*np.pi/max(float(angle),np.finfo(float).tiny))
                for cut in range(9):
                    trial=advance(state,step*(fraction*.5**cut));last_trial=trial
                    changed,_,_,_=assemble(operator,trial,origin,force,couple,parameter,safe)
                    if max(metric(changed))<max(errors):state=trial;break
                else:raise RuntimeError('retained generalized line search limit')
        safe()
        return dict(status='COMPLETED',state=state,records=records,
            recovery=operator.recover(state['cell_rotations'],state['resultants'],origin=origin,check=safe),
            production_qualified=False,native_state_committed=False)
    except Exception as exc:
        progress(dict(stage='failure',error=type(exc).__name__,message=str(exc),
            accepted_state=accepted,current_state=state,last_trial=last_trial,records=records))
        raise
