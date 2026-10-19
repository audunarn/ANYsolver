"""Locate one declared material event on the saved Newton ray; no commits."""
import argparse,copy,hashlib,json,pickle,sys,time
from pathlib import Path
import numpy as np
from scipy import sparse
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'tests'))
from test_nonlinear_beam_shell_slice3_continuation import _build_ep_model,_add_tip_load
from anysolver.corotational import build_nonlinear_rotating_mpc_map
from anysolver.nonlinear_static import _assemble_nonlinear_system
from anysolver.plasticity import plane_stress_elastic_matrix
from assessment_support import identical


def main():
    p=argparse.ArgumentParser(); p.add_argument('capture'); p.add_argument('output'); a=p.parse_args()
    out=Path(a.output); out.mkdir(parents=True,exist_ok=False); started=time.perf_counter()
    c=pickle.loads(Path(a.capture).read_bytes()); before=pickle.dumps(c)
    model,load,probe,grid=_build_ep_model('direct'); _add_tip_load(model,load,grid)
    m=build_nonlinear_rotating_mpc_map(model,c['T']); material=model.get_material('steel')
    E=material.elastic_modulus; C=plane_stress_elastic_matrix(E,material.poisson_ratio); curve=material.hardening_curve
    cache={}; raw={}; records=[]; eps=np.finfo(float).eps
    def evaluate(alpha,tangent=False):
        if (alpha,tangent) in cache: return cache[alpha,tangent]
        q=c['q']+alpha*c['delta'][:-1]; lam=c['lam']+alpha*c['delta'][-1]
        u=m.apply_kinematics(np.asarray(c['T']@q+c['u0']).reshape(-1))
        H=copy.deepcopy(c['states']); frozen=copy.deepcopy(H); u_before=u.copy()
        fint,K,trial=_assemble_nonlinear_system(model,u,H,5,tangent=tangent,kinematics='corotational',corotational_tangent='work_conjugate')
        assert identical(H,frozen) and np.array_equal(u,u_before)
        ext=c['F_const']+lam*c['F']; r=m.reduce_force(u,ext-fint); control=float(c['row']@u)
        merit=np.linalg.norm(r)/(c['tolerance']*c['reference'])+abs(c['target']-control)/(c['tolerance']*c['target_scale'])
        indicators=[]; labels=[]; strains=[]
        for eid,state in sorted(trial.items()):
            if not isinstance(state,dict) or 'alpha' not in state: continue
            old=c['states'][eid]; alpha_old=np.asarray(old['alpha']); flow=curve.flow_stress(alpha_old)
            if 'fiber_strain' in state:
                strain=np.asarray(state['fiber_strain']); sigma=E*(strain-np.asarray(old['plastic_strain']))
                value=(abs(sigma)-flow)/np.maximum(flow,1.)-1e-9
            elif 'layer_strain' in state:
                strain=np.asarray(state['layer_strain']); sigma=(strain-np.asarray(old['plastic_strain']))@C.T
                sx,sy,tau=sigma.T; phi2=(sx*sx-sx*sy+sy*sy)/3.+tau*tau
                value=(phi2-flow*flow/3.)/np.maximum(flow*flow,1.)-1e-10
            else: raise ValueError('unobserved material strain path')
            strains.extend(strain.reshape(-1))
            for j,v in enumerate(value.reshape(-1)): labels.append((eid,'loading',j)); indicators.append(v)
            for name,boundary in [('hardening1',curve.eps_p_y1),('hardening2',curve.eps_p_y2)]:
                for j,v in enumerate((np.asarray(state['alpha'])/boundary-1.).reshape(-1)):
                    labels.append((eid,name,j)); indicators.append(v)
        indicators=np.asarray(indicators); signature=indicators>0.
        result=dict(alpha=float(alpha),q=q,u=u,r=r,control=control,merit=float(merit),indicators=indicators,labels=labels,strains=np.asarray(strains),signature=signature,states=copy.deepcopy(dict(trial)),K=None)
        if tangent: result['K']=m.reduce_tangent(u,K,fint-ext)
        result['force_scale']=max(np.linalg.norm(m.reduce_force(u,fint)),np.linalg.norm(m.reduce_force(u,ext)),1.)
        cache[alpha,tangent]=result
        records.append(dict(alpha=float(alpha),tangent=tangent,residual=float(np.linalg.norm(r)),merit=float(merit),control=control,branch=hashlib.sha256(signature.tobytes()).hexdigest()))
        return result
    base=evaluate(0.,True); upper=evaluate(1e-7); lower=evaluate(1e-8)
    if not np.array_equal(lower['signature'],base['signature']): raise ValueError('measured lower bracket already crossed a material event')
    changes=np.flatnonzero(upper['signature']!=base['signature'])
    report=dict(diagnostic_only=True,committed_probe_history=False,base_residual=float(np.linalg.norm(base['r'])),captured_rhs_error=float(np.linalg.norm(base['r']-c['rhs'][:-1])),upper_changed_equations=len(changes))
    if not len(changes):
        report['outcome']='no_declared_event_in_measured_bracket'
    else:
        lo=1e-8; hi=1e-7
        # Locate the first observed departure from the base fingerprint within
        # the already measured tiny bracket, not an alpha grid or load sweep.
        for iteration in range(48):
            mid=.5*(lo+hi); ev=evaluate(mid)
            if np.array_equal(ev['signature'],base['signature']): lo=mid
            else: hi=mid
            if hi-lo<=64*np.spacing(hi): break
        pre=evaluate(lo); post=evaluate(hi); event=.5*(lo+hi)
        changed=np.flatnonzero(post['signature']!=pre['signature'])
        if not len(changed): raise ValueError('localized event has no actual fingerprint change')
        slopes=(upper['indicators']-base['indicators'])/1e-7
        equation_offset=max(64*eps/max(abs(slopes[j]),np.finfo(float).tiny) for j in changed)
        state_offset=64*np.max(np.abs(np.spacing(c['q'])))/max(np.max(abs(c['delta'][:-1])),np.finfo(float).tiny)
        strain_slope=np.max(abs((upper['strains']-base['strains'])/1e-7))
        strain_offset=64*np.max(abs(np.spacing(base['strains'])))/max(strain_slope,np.finfo(float).tiny)
        offset=max(equation_offset,state_offset,strain_offset,64*np.spacing(event))
        if not 0.<event-offset<event+offset<=1e-7: raise ValueError('machine-resolved event neighborhood leaves the measured bracket')
        left=evaluate(event-offset); center=evaluate(event); right=evaluate(event+offset,True)
        decrease=float(np.linalg.norm(base['r'])-np.linalg.norm(right['r']))
        noise_bound=float(128*eps*max(base['force_scale'],right['force_scale']))
        armijo=right['merit']<=(1.-1e-4*right['alpha'])*base['merit']
        crossed=not np.array_equal(left['signature'],right['signature'])
        info=[]
        for j in changed:
            info.append(dict(label=base['labels'][j],base=float(base['indicators'][j]),upper=float(upper['indicators'][j]),left=float(left['indicators'][j]),at_event=float(center['indicators'][j]),right=float(right['indicators'][j])))
        report.update(outcome='resolved_post_event_descent' if crossed and armijo and decrease>noise_bound else 'no_useful_resolved_post_event_descent',
                      event_alpha=event,offset=offset,event_bracket=[lo,hi],bisection_iterations=iteration+1,
                      equation_offset=equation_offset,state_offset=state_offset,strain_offset=strain_offset,event_equations=info,
                      post_event_armijo=bool(armijo),event_crossed=bool(crossed),physical_residual_decrease=decrease,roundoff_noise_bound=noise_bound,
                      post_tangent_relative_change=float(np.linalg.norm((right['K']-base['K']).data)/max(np.linalg.norm(base['K'].data),1.)),
                      pre_event_residual=float(np.linalg.norm(left['r'])),at_event_residual=float(np.linalg.norm(center['r'])),post_event_residual=float(np.linalg.norm(right['r'])))
        raw.update(left=left,center=center,right=right,pre=pre,post=post)
    assert pickle.dumps(c)==before
    raw.update(base=base,lower=lower,upper=upper)
    report.update(inputs_unchanged=True,records=records,evaluations=len(records),elapsed=time.perf_counter()-started)
    (out/'raw.pkl').write_bytes(pickle.dumps(raw)); (out/'result.json').write_text(json.dumps(report,indent=2)); print(json.dumps(report))


if __name__=='__main__': main()
