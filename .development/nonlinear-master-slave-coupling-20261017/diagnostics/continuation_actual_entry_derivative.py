"""One branch-aware actual microiterate derivative audit; no global solves."""
import argparse,copy,json,pickle,time
from pathlib import Path
import numpy as np
import continuation_actual_finite_entry as entry
from anysolver._nonlinear_events import material_events
from anysolver.plasticity import _jit_hardening_modulus,lobatto_layers


def main():
    p=argparse.ArgumentParser(); p.add_argument('capture'); p.add_argument('pending'); p.add_argument('output'); a=p.parse_args()
    out=Path(a.output); out.mkdir(parents=True,exist_ok=False); started=time.perf_counter(); eps=np.finfo(float).eps
    c=pickle.loads(Path(a.capture).read_bytes()); pending=pickle.loads(Path(a.pending).read_bytes()); original=pickle.dumps((c,pending))
    model,load,probe,grid=entry._build_ep_model('direct'); entry._add_tip_load(model,load,grid)
    T,u0=c['T'],c['u0']; mapping=entry.co.build_nonlinear_rotating_mpc_map(model,T)
    q=pending['q'].copy(); lam=float(pending['lam']); H=copy.deepcopy(pending['H']); Hbefore=copy.deepcopy(H)
    row=c['row']; F=c['F']; Fc=c['F_const']; raw={}; report=dict(diagnostic_only=True,new_global_direction_solves=0,interpretation='Actual unaccepted microiterate audit only; no root/fold/reachability conclusion.')
    def local_error(u,trial):
        observer=entry.material_observer(model,mapping,u,H,trial,np.zeros(len(q)))
        cursor=0; total=0.; points=[]
        for witness in observer['witnesses']:
            eid=witness['element']; flat=witness['point']; element=model.mesh.elements[eid]; mat=model.get_material(element.material_name); E=float(mat.elastic_modulus)
            state=trial[eid]; old=H[eid]; kind=witness['kind']; size=3 if kind=='shell' else 1
            Bq=observer['strain_jacobian'][cursor:cursor+size]; cursor+=size
            active=float(state['alpha'][flat])>float(old['alpha'][flat])
            estimate=0.; residual=0.; derivative=None
            if kind=='shell':
                cache=element._nonlinear_geometry(model.mesh); gp,layer=divmod(flat,5); _z,w=lobatto_layers(5,element.thickness)
                weight=float(cache['gp'][gp]['detw']*w[layer]); curve=mat.hardening_curve
                if active:
                    C=entry.plane_stress_elastic_matrix(E,float(mat.poisson_ratio)); sigma=np.asarray(state['layer_stress'][flat]); trial_sigma=C@(np.asarray(state['layer_strain'][flat])-np.asarray(old['plastic_strain'][flat]))
                    b=np.asarray([trial_sigma[0]+trial_sigma[1],trial_sigma[0]-trial_sigma[1],trial_sigma[2]])
                    phi2=(sigma[0]**2-sigma[0]*sigma[1]+sigma[1]**2)/3+sigma[2]**2
                    g=2*np.sqrt(max(phi2/3,1e-30)); dl=(state['alpha'][flat]-old['alpha'][flat])/g
                    Y=float(curve.flow_stress(float(state['alpha'][flat]))); alpha=np.asarray([state['alpha'][flat]])
                    hard=float(_jit_hardening_modulus(alpha,float(curve.sigma_prop),float(curve.sigma_yield),float(curve.sigma_yield_2),float(curve.eps_p_y1),float(curve.eps_p_y2),float(curve.K),float(curve.n),float(curve._power_offset))[0])
                    G=E/(2*(1+mat.poisson_ratio)); ca=E/(3*(1-mat.poisson_ratio)); dA=1+ca*dl; dB=1+2*G*dl
                    dp=-2*(b[0]**2*ca/(12*dA**3)+2*G*(b[1]**2/4+b[2]**2)/dB**3)
                    dg=dp/(np.sqrt(3)*np.sqrt(max(phi2,1e-30))); derivative=abs(dp-(2/3)*Y*hard*(g+dl*dg))
                    residual=abs(phi2-Y*Y/3)
                    v=np.asarray([-.5*ca*b[0]/dA**2-G*b[1]/dB**2,-.5*ca*b[0]/dA**2+G*b[1]/dB**2,-2*G*b[2]/dB**2])
                    estimate=float(np.linalg.norm(v)*residual/derivative) if derivative>0 and np.isfinite(derivative) else float('inf')
            else:
                length,_=element._beam_frame_and_transform(element.get_node_coordinates(model.mesh)); config=element._fiber_plasticity_config(mat); _y,_z,w=element._fiber_section_grid(config)
                weight=float(length*w[flat])
                if active:
                    Y=float(config.material_curve.flow_stress(float(state['alpha'][flat])))*entry._beam_flow_scale(mat,config.material_curve)
                    residual=abs(abs(state['fiber_stress'][flat])-Y); estimate=residual
            projected=float(weight*np.linalg.norm(Bq.T)*estimate); total+=projected
            points.append(dict(element=eid,point=flat,active=active,consistency_residual=residual,consistency_derivative=derivative,stress_error_estimate=estimate,reduced_force_error_estimate=projected))
        return total,points
    def observe(label,qp,tangent=False):
        history=copy.deepcopy(H); prior=copy.deepcopy(history); u=mapping.apply_kinematics(np.asarray(T@qp+u0).reshape(-1)); saved=u.copy()
        fi,K,trial=entry.ns._assemble_nonlinear_system(model,u,history,5,tangent=tangent,kinematics='corotational',corotational_tangent='work_conjugate')
        assert entry.identical(history,prior) and np.array_equal(saved,u)
        r=mapping.reduce_force(u,fi-Fc-lam*F); ev=material_events(model,history,trial); assert ev is not None
        local,points=local_error(u,trial)
        float_error=float(np.linalg.norm(64*eps*np.asarray(abs(mapping.jacobian(u)).T@(abs(fi)+abs(Fc+lam*F))).reshape(-1)))
        kr=mapping.reduce_tangent(u,K,fi-Fc-lam*F).toarray() if tangent else None
        value=dict(q=qp.copy(),u=u.copy(),r=r.copy(),events=ev,trial=copy.deepcopy(dict(trial)),K=kr,local_error=local,float_error=float_error,local_points=points)
        raw[label]=value; return value
    def save(status):
        assert pickle.dumps((c,pending))==original and entry.identical(H,Hbefore)
        report.update(status=status,elapsed=time.perf_counter()-started,inputs_unchanged=True)
        (out/'raw.pkl').write_bytes(pickle.dumps(raw)); (out/'result.json').write_text(json.dumps(report,indent=2,allow_nan=False)); print(json.dumps(report))
    center=observe('center',q,True); g=np.asarray(row@mapping.jacobian(center['u'])).reshape(-1); load_column=-mapping.reduce_force(center['u'],F)
    A=np.vstack((np.column_stack((center['K'],load_column)),np.r_[g,0.])); saved_A=pending['matrix'].toarray(); target=json.loads((Path(a.pending).parent/'result.json').read_text())['diagnostic_target']; rhs=np.r_[-center['r'],target-float(row@center['u'])]
    error=saved_A@pending['delta']-pending['rhs']; scale=abs(saved_A)@abs(pending['delta'])+abs(pending['rhs'])
    report.update(matrix_relative_reconstruction=float(np.linalg.norm(A-saved_A)/np.linalg.norm(saved_A)),rhs_absolute_reconstruction=float(np.linalg.norm(rhs-pending['rhs'])),load_column_absolute_reconstruction=float(np.linalg.norm(load_column-saved_A[:-1,-1])),control_row_absolute_reconstruction=float(np.linalg.norm(g-saved_A[-1,:-1])),linear_absolute_backward_error=float(np.linalg.norm(error)),linear_scaled_backward_error=float(np.max(abs(error)/np.maximum(1.,scale))))
    dq=pending['delta'][:-1]; norm=float(np.linalg.norm(dq,np.inf)); h0=eps**.2*max(1.,float(np.linalg.norm(q,np.inf)))/norm
    prediction=center['K']@dq; magnitude=float(np.linalg.norm(prediction)); threshold=1e-7*magnitude
    up=observe('center-ulp-upper',np.nextafter(q,np.inf)); down=observe('center-ulp-lower',np.nextafter(q,-np.inf))
    measured=float(max(np.linalg.norm(up['r']-center['r']),np.linalg.norm(down['r']-center['r'])))
    equation_unc=np.maximum(64*eps*np.maximum(1.,abs(center['events'].values)),np.maximum(abs(up['events'].values-center['events'].values),abs(down['events'].values-center['events'].values)))
    report.update(predicted_derivative_norm=magnitude,derivative_threshold=threshold,h0=float(h0),center_local_stopping_force_error=center['local_error'],center_float_force_error=center['float_error'],measured_q_ulp_force_error=measured,uncertified_estimates='Material residual-to-stress transport and empirical ULP/assembly envelope are local estimates, not interval certificates.',center_uncertain_indicator_indices=np.flatnonzero(abs(center['events'].values)<=equation_unc).tolist())
    if report['center_uncertain_indicator_indices']: save('unresolved_center_branch_at_source_or_ulp_margin'); return
    signature=center['events'].signature; exits=[]; counts=[]
    for sign in (1.,-1.):
        try: endpoint=observe('exit-endpoint-'+str(sign),q+sign*2*h0*dq)
        except entry.co.SO3MeanDomainError: save('unresolved_chart_refused_at_fixed_interval'); return
        lo=0.; hi=2*h0; count=0
        if np.array_equal(endpoint['events'].signature,signature): exits.append(2*h0); counts.append(0); continue
        for iteration in range(48):
            mid=(lo+hi)/2
            if mid==lo or mid==hi or np.array_equal(q+sign*mid*dq,q+sign*hi*dq): break
            try: value=observe(f'exit-{sign}-{iteration}',q+sign*mid*dq)
            except entry.co.SO3MeanDomainError: save('unresolved_chart_refused_in_fixed_interval'); return
            count+=1
            if np.array_equal(value['events'].signature,signature): lo=mid
            else: hi=mid
        # Interior side of observed branch exit; not a certified first exit.
        exits.append(lo); counts.append(count)
    h=min(h0,min(exits)/4); report.update(observed_branch_interval=exits,branch_bisections=counts,chosen_once_h=float(h))
    if h<=0 or np.array_equal(q+h*dq,q) or np.array_equal(q-h*dq,q): save('unresolved_no_representable_branch_interval'); return
    values={}
    for factor in (2.,1.,.5,-.5,-1.,-2.):
        try: value=observe('stencil-'+str(factor),q+factor*h*dq)
        except entry.co.SO3MeanDomainError: save('unresolved_chart_refused_at_stencil'); return
        if not np.array_equal(value['events'].signature,signature) or np.any(abs(value['events'].values)<=equation_unc): save('unresolved_stencil_not_common_resolved_branch'); return
        values[factor]=value
    def stencil(a,b,c,d,denominator):
        derivative=(-values[a]['r']+8*values[b]['r']-8*values[c]['r']+values[d]['r'])/denominator
        uncertainty=sum(weight*(values[key]['local_error']+values[key]['float_error']+measured) for key,weight in ((a,1),(b,8),(c,8),(d,1)))/denominator
        return derivative,uncertainty
    full,_=stencil(2.,1.,-1.,-2.,12*h); half,unc=stencil(1.,.5,-.5,-1.,6*h)
    trunc=float(np.linalg.norm(half-full)/15); uncertainty=float(unc+trunc+64*eps*np.linalg.norm(abs(center['K'])@abs(dq))); difference=float(np.linalg.norm(half-prediction))
    report.update(difference=difference,uncertainty=uncertainty,roundoff_and_local_stopping=unc,truncation_estimate=trunc,relative_difference=difference/magnitude,relative_uncertainty=uncertainty/magnitude)
    raw['derivative']=dict(full=full,half=half,predicted=prediction)
    status='passed_existing_1e_7_derivative_oracle' if difference<=threshold and uncertainty<=threshold else ('confirmed_actual_tangent_defect' if uncertainty<=threshold and difference>threshold+uncertainty else 'unresolved_derivative_difference_or_error_budget')
    save(status)


if __name__=='__main__': main()

