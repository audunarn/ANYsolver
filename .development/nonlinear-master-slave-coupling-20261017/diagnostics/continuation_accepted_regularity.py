"""Copied accepted-state regularity replay; no nonlinear solver/root steps."""
import argparse,copy,hashlib,json,pickle,sys,time
from collections.abc import Mapping
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'tests'))
from test_nonlinear_beam_shell_slice3_continuation import _build_ep_model,_add_tip_load,L,NY,TIP_LOAD_PER_NODE
from anysolver.assembly import build_constraint_transformation
from anysolver.matrix_assembly import assemble_stiffness_matrix,assemble_load_vector
from anysolver.corotational import build_nonlinear_rotating_mpc_map
from anysolver.nonlinear_static import _assemble_nonlinear_system
from anysolver._nonlinear_events import material_events
from anysolver.constraint_audit import constraint_residual_summary
from assessment_support import identical


def main():
    p=argparse.ArgumentParser(); p.add_argument('accepted_folder'); p.add_argument('output'); a=p.parse_args()
    out=Path(a.output); out.mkdir(parents=True,exist_ok=False); started=time.perf_counter(); eps=np.finfo(float).eps
    folder=Path(a.accepted_folder); paths=[folder/f'accepted-{i:04d}.pkl' for i in (10,11)]
    prev,cur=[pickle.loads(path.read_bytes()) for path in paths]; original=pickle.dumps((prev,cur))
    model,load,probe,grid=_build_ep_model('direct'); _add_tip_load(model,load,grid)
    K0,_=assemble_stiffness_matrix(model); F,_=assemble_load_vector(model,load)
    _,_,T,u0,independent,_=build_constraint_transformation(K0,F,model)
    independent=np.asarray(independent,dtype=int); n=T.shape[1]
    assert np.array_equal(T[independent,:].toarray(),np.eye(n))
    mapping=build_nonlinear_rotating_mpc_map(model,T)
    qp,qc=[(mapping.to_linear_displacement(s['displacements'])-u0)[independent] for s in (prev,cur)]
    qdir=qc-qp; lam=float(cur['lam']); row=np.zeros(T.shape[0]); row[model.mesh.dof_manager.get_node_dofs(probe)[2]]=1.
    L0=float(L); theta0=1.; F0=abs(TIP_LOAD_PER_NODE)*(NY+1); W0=F0*L0
    kind={int(d):j<3 for node in model.mesh.nodes.values() for j,d in enumerate(node.dofs)}
    S=np.asarray([L0 if kind[int(d)] else theta0 for d in independent]); secant=np.r_[qdir/S,lam-float(prev['lam'])]
    cache={}; raw={}; logs=[]
    def evaluate(label,q,history,tangent=True):
        H=copy.deepcopy(history); before=copy.deepcopy(H)
        u=mapping.apply_kinematics(np.asarray(T@q+u0).reshape(-1)); ubefore=u.copy()
        fint,K,trial=_assemble_nonlinear_system(model,u,H,5,tangent=tangent,kinematics='corotational',corotational_tangent='work_conjugate')
        assert identical(H,before) and np.array_equal(u,ubefore)
        ext=lam*F; r=mapping.reduce_force(u,fint-ext); fred=mapping.reduce_force(u,F)
        events=material_events(model,H,trial)
        if events is None: raise ValueError('unsupported material event layout')
        g=np.asarray(row@mapping.jacobian(u)).reshape(-1)*S/L0
        khat=None
        if tangent:
            kr=mapping.reduce_tangent(u,K,fint-ext).toarray(); khat=S[:,None]*kr*S[None,:]/W0
        data=dict(label=label,q=q.copy(),u=u.copy(),history=copy.deepcopy(H),trial=copy.deepcopy(dict(trial)),r=r*S/W0,
                  physical_r=r,fred=fred*S/W0,khat=khat,g=g,events=events,control=float(row@u),
                  force_scale=float((np.linalg.norm(S*mapping.reduce_force(u,fint))+np.linalg.norm(S*mapping.reduce_force(u,ext)))/W0))
        raw[label]=data
        logs.append(dict(label=label,elapsed=time.perf_counter()-started,residual=float(np.linalg.norm(r)),control=data['control'],branch=hashlib.sha256(events.signature.tobytes()).hexdigest()))
        with (out/'evaluations.jsonl').open('a') as stream: stream.write(json.dumps(logs[-1])+'\n')
        return data
    arriving=evaluate('arriving_H10_at_accepted_u11',qc,prev['element_states'])
    committed=evaluate('committed_H11_zero_increment_at_accepted_u11',qc,cur['element_states'])
    report=dict(diagnostic_only=True,no_nonlinear_solver_or_root_steps=True,accepted_controls=[prev['control'],cur['control']],accepted_loads=[prev['lam'],cur['lam']],
                input_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
                fixed_scales=dict(length_m=L0,rotation_rad=theta0,unit_load_resultant_N=F0,energy_Nm=W0,lambda_scale=1.),
                retained_translation_coordinates=int(sum(kind[int(d)] for d in independent)),retained_rotation_coordinates=int(sum(not kind[int(d)] for d in independent)),
                accepted_reconstruction_error=float(np.linalg.norm(committed['u']-cur['displacements'])),constraint_summary=constraint_residual_summary(model,mapping.to_linear_displacement(committed['u'])),
                limitations='Local loading regularity only. Probes are unaccepted. Histories are distinct equations; no root reachability, physical fold, collapse or rigorous operator uncertainty bound follows.')
    def fingerprint(data): return data['events'].signature
    def sensitivity(data):
        E=np.column_stack((data['khat'],-data['fred'])); A=np.vstack((E,np.r_[data['g'],0.]))
        U,se,V=np.linalg.svd(E,full_matrices=True); t=V[-1]
        if t@secant<0: t=-t
        sa=np.linalg.svd(A,compute_uv=False); rhs=np.r_[np.zeros(n),1.]
        result=dict(label=data['label'],equilibrium_singular_values=se.tolist(),bordered_singular_values=sa.tolist(),
                    equilibrium_float_rank=int(np.count_nonzero(se>max(E.shape)*eps*se[0])),
                    bordered_float_rank=int(np.count_nonzero(sa>max(A.shape)*eps*sa[0])),
                    t_control=float(data['g']@t[:-1]),t_lambda=float(t[-1]),
                    tangent_orientation_secant_dot=float(t@secant),null_backward_error=float(np.linalg.norm(E@t)/max(np.linalg.norm(E),1e-300)))
        try:
            v=np.linalg.solve(A,rhs)
            result.update(control_tangent_norm=float(np.linalg.norm(v)),control_lambda_sensitivity=float(v[-1]),
                          bordered_backward_error=float(np.linalg.norm(A@v-rhs)/(np.linalg.norm(A)*np.linalg.norm(v)+np.linalg.norm(rhs))))
        except np.linalg.LinAlgError: result['bordered_solve']='singular'
        raw[data['label']+'_linear_sensitivity']=dict(E=E,A=A,t=t)
        return result,t
    def derivative(data,t):
        # One fixed machine-balance kinematic probe determines a branch-safe
        # four-point forward stencil. No after-result scale fitting or sweep.
        direction=S*t[:-1]; dn=np.linalg.norm(t[:-1],np.inf)
        if dn==0: return dict(status='no_displacement_direction')
        h0=np.sqrt(eps)*max(1.,np.linalg.norm(data['q']/S,np.inf))/dn
        first=evaluate(data['label']+'_direction_machine',data['q']+h0*direction,data['history'],False)
        if not np.array_equal(fingerprint(data),fingerprint(first)):
            return dict(status='branch_ambiguous_at_fixed_machine_direction',machine_scale=float(h0))
        rates=(first['events'].values-data['events'].values)/h0; values=data['events'].values
        mask=values*rates<0.; cap=float(np.min(-values[mask]/rates[mask])) if np.any(mask) else float('inf')
        h=min(eps**.2*max(1.,np.linalg.norm(data['q']/S,np.inf))/dn,cap/8.)
        min_h=64*np.max(np.abs(np.spacing(data['q'])))/max(np.max(abs(direction)),np.finfo(float).tiny)
        if not np.isfinite(h) or h<=min_h: return dict(status='no_representable_branch_safe_stencil',candidate_scale=float(h))
        points=[]
        for j in range(1,5):
            value=evaluate(data['label']+f'_forward{j}',data['q']+j*h*direction,data['history'],False)
            points.append(value)
            if not np.array_equal(fingerprint(data),fingerprint(value)):
                return dict(status='branch_ambiguous_in_declared_forward_stencil',stencil_scale=float(h),point=j)
        weights=[4.,-3.,4./3.,-.25]
        fd=sum(w*(v['r']-data['r']) for w,v in zip(weights,points))/h
        predicted=data['khat']@t[:-1]; error=float(np.linalg.norm(fd-predicted)); magnitude=float(np.linalg.norm(predicted))
        control_fd=sum(w*(v['control']-data['control'])/L0 for w,v in zip(weights,points))/h
        bound=float(64*eps*(data['force_scale']+sum(abs(w)*v['force_scale'] for w,v in zip(weights,points)))/h)
        relative=error/max(magnitude,1e-300)
        control_predicted=float(data['g']@t[:-1]); control_error=float(abs(control_fd-control_predicted))
        control_bound=float(64*eps*(abs(data['control'])+sum(abs(w)*abs(v['control']) for w,v in zip(weights,points)))/(h*L0))
        force_pass=relative<=1e-7 and bound<=1e-7*max(magnitude,1e-300)
        control_pass=max(control_error,control_bound)<=1e-7*max(abs(control_predicted),1e-300)
        return dict(status='passed_existing_1e-7_oracle' if force_pass and control_pass else 'derivative_uncertain_or_oracle_failed',
                    machine_scale=float(h0),stencil_scale=float(h),relative_force_error=relative,absolute_dimensionless_force_error=error,
                    force_direction_scale=magnitude,estimated_roundoff_bound=bound,force_derivative_pass=bool(force_pass),control_derivative_pass=bool(control_pass),control_direction=control_predicted,
                    finite_control_direction=float(control_fd),control_direction_error=control_error,control_roundoff_bound=control_bound,
                    empirically_resolved_nonzero_control=bool(abs(control_predicted)>control_error+control_bound))
    analyses=[]
    for value in (arriving,committed):
        result,t=sensitivity(value); result['directional_check']=derivative(value,t); analyses.append(result)
    hkin=np.sqrt(eps)*max(1.,np.linalg.norm(qc/S,np.inf))/max(np.linalg.norm(qdir/S,np.inf),np.finfo(float).tiny)
    kinematic=evaluate('committed_H11_fixed_machine_secant_probe',qc+hkin*qdir,cur['element_states'],False)
    values=committed['events'].values; rates=(kinematic['events'].values-values)/hkin
    flowed=np.zeros(len(values),dtype=bool); cursor=0
    for eid,state in sorted(committed['trial'].items()):
        if not isinstance(state,Mapping) or 'alpha' not in state: continue
        count=np.asarray(state['alpha']).size
        flowed[cursor:cursor+count]=(np.asarray(cur['element_states'][eid]['alpha'])>np.asarray(prev['element_states'][eid]['alpha'])).reshape(-1)
        cursor+=3*count
    assert cursor==len(values)
    selected=flowed & (rates!=0.)
    # Globally forward loading includes local unloading. A prior-flowed point
    # already elastic on that side needs zero re-entry distance. If literal
    # committed overstress still selects plasticity, resolve its exit first;
    # never force such an unloading point to reload or change its history.
    rate_uncertainty=64*eps*np.maximum(1.,np.maximum(abs(values),abs(kinematic['events'].values)))/hkin
    unresolved=flowed & (abs(rates)<=rate_uncertainty)
    buffer=64*eps*np.maximum(1.,abs(values))
    required=np.zeros(len(values)); required[selected]=np.maximum((np.sign(rates[selected])*buffer[selected]-values[selected])/rates[selected],0.)
    min_state=64*np.max(abs(np.spacing(qc)))/max(np.max(abs(qdir)),np.finfo(float).tiny)
    hload=float(np.nextafter(max(float(np.max(required)),float(min_state)),np.inf))
    other=(~selected)&(values*rates<0.)
    cap=float(np.min(-values[other]/rates[other])) if np.any(other) else float('inf')
    selection=dict(machine_kinematic_scale=float(hkin),loading_probe_scale=hload,unrelated_event_cap=None if not np.isfinite(cap) else cap,flowed_directional_points=int(np.count_nonzero(selected)),
                   further_loading_points=int(np.count_nonzero(flowed & (rates>0.))),local_unloading_points=int(np.count_nonzero(flowed & (rates<0.))),unresolved_flowed_directional_points=int(np.count_nonzero(unresolved)))
    if np.any(unresolved):
        selection['status']='loading_direction_rates_unresolved_no_scale_refit'
    elif not np.any(selected) or not np.isfinite(hload) or hload>=cap:
        selection['status']='no_common_branch_safe_loading_interval'
    else:
        loading=evaluate('committed_H11_shared_loading_probe_UNACCEPTED',qc+hload*qdir,cur['element_states'])
        desired=committed['events'].signature.copy(); desired[selected]=rates[selected]>0.
        if not np.array_equal(desired,fingerprint(loading)):
            selection['status']='actual_loading_fingerprint_not_predicted_no_scale_refit'
        else:
            selection['status']='branch_selected_once'
            result,t=sensitivity(loading); result['directional_check']=derivative(loading,t); analyses.append(result)
    assert pickle.dumps((prev,cur))==original
    report.update(loading_selection=selection,analyses=analyses,evaluations=logs,input_histories_and_displacements_unchanged=True,elapsed=time.perf_counter()-started,
                  interpretation='Read numerical regularity witnesses with branch/derivative uncertainty; no automatic physical-fold or reachability classification.')
    (out/'raw.pkl').write_bytes(pickle.dumps(raw)); (out/'result.json').write_text(json.dumps(report,indent=2,allow_nan=False)); print(json.dumps(report))


if __name__=='__main__': main()
