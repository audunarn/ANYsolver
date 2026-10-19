"""One resolved actual finite-entry diagnostic; no changed material/force law."""
import argparse,ast,copy,inspect,json,pickle,sys,time
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'tests'))
from test_nonlinear_beam_shell_slice3_continuation import _build_ep_model,_add_tip_load,_independent_equilibrium
from assessment_support import identical
from anysolver import DisplacementControl,solve_static_nonlinear
import anysolver.nonlinear_static as ns
import anysolver.corotational as co
from anysolver._nonlinear_events import material_events
from anysolver.constraint_audit import constraint_residual_summary
from anysolver.plasticity import plane_stress_elastic_matrix,lobatto_layers
from anysolver.elements import BeamElement,ShellElement,_beam_flow_scale


def material_observer(model,mapping,u,history,trial,q_uncertainty):
    """Source-consistent stress-drop force observer; never a Newton force."""
    n=len(q_uncertainty)
    correction=np.zeros(n); rows=[]; strain_rows=[]; witnesses=[]; stress_checks=[]; projection_error=0.
    J=mapping.jacobian(u); references=co._corotational_cache(model)
    for eid,state in sorted(trial.items()):
        if not isinstance(state,dict) or 'alpha' not in state: continue
        element=model.mesh.elements[eid]; material=model.get_material(element.material_name)
        E=float(material.elastic_modulus); old=history[eid]
        dofs=np.asarray(element.get_dof_mapping(model.mesh),dtype=int); ue=u[dofs]
        ref=references[eid]; ud,Rrig,deformed=co._corotational_deformation_state(ref,element,ue)
        Bco=co.corotational_deformation_jacobian(ref,element,deformed,ue.reshape(-1,6)[:,3:],Rrig)
        reduced=Bco@J[dofs,:].toarray()
        if isinstance(element,ShellElement):
            cache=element._nonlinear_geometry(model.mesh); T0=cache['T0']; uloc=T0@ud
            C=plane_stress_elastic_matrix(E,float(material.poisson_ratio)); z,weights=lobatto_layers(5,element.thickness)
            matrices=[]; quadrature=[]
            for gp in cache['gp']:
                theta=gp['Gw']@uloc
                Bnl=np.vstack([theta[0]*gp['Gw'][0],theta[1]*gp['Gw'][1],theta[0]*gp['Gw'][1]+theta[1]*gp['Gw'][0]])
                for zi,wi in zip(z,weights):
                    matrices.append((gp['B_m']+Bnl+zi*gp['B_b'])@T0@reduced)
                    quadrature.append(float(gp['detw']*wi))
            strain=np.asarray(state['layer_strain']); ep=np.asarray(state['plastic_strain']); epold=np.asarray(old['plastic_strain'])
            returned=np.asarray(state['layer_stress']); trial_stress=(strain-epold)@C.T
            drops=(ep-epold)@C.T; flow=np.asarray(material.hardening_curve.flow_stress(np.asarray(state['alpha'])))
            flowold=np.asarray(material.hardening_curve.flow_stress(np.asarray(old['alpha'])))
            for point,(Bq,weight) in enumerate(zip(matrices,quadrature)):
                sx,sy,tau=trial_stress[point]; a1,a2=sx+sy,sx-sy
                scale=max(float(flowold[point]**2),1.)
                loading=(a1*a1/12+a2*a2/4+tau*tau-flowold[point]**2/3-1e-10*scale)/scale
                nf=np.asarray([(2*sx-sy)/3,(2*sy-sx)/3,2*tau]); gradient=nf@C@Bq/scale
                ss=returned[point]; consistency=abs((ss[0]**2-ss[0]*ss[1]+ss[1]**2)/3+ss[2]**2-flow[point]**2/3)/max(float(flow[point]**2),1.)
                identity=np.linalg.norm(trial_stress[point]-returned[point]-drops[point])
                arithmetic=64*np.finfo(float).eps*(np.linalg.norm(trial_stress[point])+np.linalg.norm(returned[point])+np.linalg.norm(drops[point]))
                stress_checks.append(dict(element=int(eid),point=point,error=float(identity),bound=float(arithmetic),passed=bool(identity<=arithmetic)))
                projection_error+=weight*np.linalg.norm(Bq.T)*identity
                correction+=weight*(Bq.T@drops[point]); strain_rows.extend(Bq)
                rows.append(gradient)
                witnesses.append(dict(element=int(eid),point=point,kind='shell',strain=strain[point].copy(),strain_uncertainty=abs(Bq)@q_uncertainty,loading=float(loading),loading_uncertainty=float(abs(gradient)@q_uncertainty),alpha=float(state['alpha'][point]),alpha_old=float(old['alpha'][point]),plastic_change=float(np.max(abs(ep[point]-epold[point]))),plastic_ulp=float(64*np.max(abs(np.spacing(ep[point]))+abs(np.spacing(epold[point])))),consistency=float(consistency),consistency_tolerance=1e-10,stress_drop_identity_error=float(np.linalg.norm(trial_stress[point]-returned[point]-drops[point]))))
        elif isinstance(element,BeamElement):
            length,T0=element._beam_frame_and_transform(element.get_node_coordinates(model.mesh)); uloc=T0@ud
            config=element._fiber_plasticity_config(material); y,z,weights=element._fiber_section_grid(config)
            dv,dw=uloc[7]-uloc[1],uloc[8]-uloc[2]
            B=np.zeros((len(y),12)); B[:,0]=-1/length; B[:,6]=1/length
            B[:,1]=-dv/length**2; B[:,7]=dv/length**2; B[:,2]=-dw/length**2; B[:,8]=dw/length**2
            B[:,4]=-z/length; B[:,10]=z/length; B[:,5]=-y/length; B[:,11]=y/length
            Bqs=B@T0@reduced; strain=np.asarray(state['fiber_strain']); ep=np.asarray(state['plastic_strain']); epold=np.asarray(old['plastic_strain'])
            returned=np.asarray(state['fiber_stress']); trial_stress=E*(strain-epold); drops=E*(ep-epold)
            scale_flow=_beam_flow_scale(material,config.material_curve)
            flow=np.asarray(config.material_curve.flow_stress(np.asarray(state['alpha'])))*scale_flow
            flowold=np.asarray(config.material_curve.flow_stress(np.asarray(old['alpha'])))*scale_flow
            for point,(Bq,wi) in enumerate(zip(Bqs,weights)):
                scale=max(float(flowold[point]),1.); gradient=np.sign(trial_stress[point])*E*Bq/scale
                identity=abs(trial_stress[point]-returned[point]-drops[point])
                arithmetic=64*np.finfo(float).eps*(abs(trial_stress[point])+abs(returned[point])+abs(drops[point]))
                stress_checks.append(dict(element=int(eid),point=point,error=float(identity),bound=float(arithmetic),passed=bool(identity<=arithmetic)))
                projection_error+=length*wi*np.linalg.norm(Bq)*identity
                correction+=length*wi*Bq*drops[point]; strain_rows.append(Bq); rows.append(gradient)
                witnesses.append(dict(element=int(eid),point=point,kind='beam',strain=np.asarray([strain[point]]),strain_uncertainty=np.asarray([abs(Bq)@q_uncertainty]),loading=float((abs(trial_stress[point])-(flowold[point]+1e-9*scale))/scale),loading_uncertainty=float(abs(gradient)@q_uncertainty),alpha=float(state['alpha'][point]),alpha_old=float(old['alpha'][point]),plastic_change=float(abs(ep[point]-epold[point])),plastic_ulp=float(64*(abs(np.spacing(ep[point]))+abs(np.spacing(epold[point])))),consistency=float(abs(abs(returned[point])-flow[point])/max(float(flow[point]),1.)),consistency_tolerance=1e-8,stress_drop_identity_error=float(abs(trial_stress[point]-returned[point]-drops[point]))))
        else: raise ValueError('unsupported diagnostic material observer')
    return dict(correction=correction,strain_jacobian=np.asarray(strain_rows),loading_jacobian=np.asarray(rows),witnesses=witnesses,stress_identity_checks=stress_checks,stress_identity_pass=bool(all(v['passed'] for v in stress_checks)),projected_stress_identity_error=float(projection_error))


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('capture'); parser.add_argument('accepted'); parser.add_argument('output'); a=parser.parse_args()
    out=Path(a.output); out.mkdir(parents=True,exist_ok=False); started=time.perf_counter(); eps=np.finfo(float).eps
    capture=pickle.loads(Path(a.capture).read_bytes()); cur=pickle.loads(Path(a.accepted).read_bytes()); before=pickle.dumps((capture,cur))
    model,load,probe,grid=_build_ep_model('direct'); _add_tip_load(model,load,grid)
    T,u0=capture['T'],capture['u0']; mapping=co.build_nonlinear_rotating_mpc_map(model,T)
    qc=ns._reduced_coordinates(T,u0,mapping.to_linear_displacement(cur['displacements'])); lamc=float(cur['lam'])
    H=copy.deepcopy(cur['element_states']); Hbefore=copy.deepcopy(H); F=capture['F']; Fc=capture['F_const']; row=capture['row']; W0=4000.
    raw={}; events=[]; global_solves=0; calls=[]
    def observe(label,q,lam,tangent=False):
        history=copy.deepcopy(H); saved=copy.deepcopy(history)
        u=mapping.apply_kinematics(np.asarray(T@q+u0).reshape(-1)); ubefore=u.copy()
        fi,K,trial=ns._assemble_nonlinear_system(model,u,history,5,tangent=tangent,kinematics='corotational',corotational_tangent='work_conjugate')
        assert identical(history,saved) and np.array_equal(u,ubefore)
        r=mapping.reduce_force(u,fi-Fc-lam*F); ev=material_events(model,history,trial); assert ev is not None
        A=None
        if tangent:
            kr=mapping.reduce_tangent(u,K,fi-Fc-lam*F).toarray(); g=np.asarray(row@mapping.jacobian(u)).reshape(-1)
            A=np.vstack((np.column_stack((kr/W0,-mapping.reduce_force(u,F)/W0)),np.r_[g,0.]))
        ref=max(float(np.linalg.norm(mapping.reduce_force(u,Fc+max(abs(lam),1.)*F))),1.)
        value=dict(q=q.copy(),u=u.copy(),lam=float(lam),fi=fi.copy(),r=r.copy(),reference=ref,events=ev,trial=copy.deepcopy(dict(trial)),A=A,control=float(row@u))
        raw[label]=value; events.append(dict(label=label,r=float(np.linalg.norm(r)),control=value['control'],elapsed=time.perf_counter()-started))
        with (out/'events.jsonl').open('a') as stream: stream.write(json.dumps(events[-1])+'\n')
        return value
    def save(report):
        assert pickle.dumps((capture,cur))==before and identical(H,Hbefore)
        report.update(global_solves=global_solves,caller_inputs_unchanged=True,elapsed=time.perf_counter()-started)
        (out/'raw.pkl').write_bytes(pickle.dumps(raw)); (out/'result.json').write_text(json.dumps(report,indent=2,default=lambda v:v.tolist() if isinstance(v,np.ndarray) else float(v)))
        print(json.dumps({k:v for k,v in report.items() if not isinstance(v,(dict,list,np.ndarray))}))
    base=observe('base',qc,lamc,True)
    n=len(qc)
    def charged(A,rhs,label):
        nonlocal global_solves
        assert global_solves<40
        global_solves+=1; delta=np.linalg.solve(A,rhs)
        error=A@delta-rhs
        raw[label]=dict(matrix=A.copy(),rhs=rhs.copy(),delta=delta.copy(),linear_error=error.copy())
        return delta,error
    def floating_envelope(value,label):
        upper=observe(label+'-ulp-upper',np.nextafter(value['q'],np.inf),value['lam'])
        lower=observe(label+'-ulp-lower',np.nextafter(value['q'],-np.inf),value['lam'])
        J=abs(mapping.jacobian(value['u']))
        summation=64*eps*np.asarray(J.T@(abs(value['fi'])+abs(Fc+value['lam']*F))).reshape(-1)
        envelope=np.maximum.reduce((abs(upper['r']-value['r']),abs(lower['r']-value['r']),summation))
        return envelope
    def sensitivity_uncertainty(value,delta,error,envelope):
        A=value['A']; singular=np.linalg.svd(A,compute_uv=False)
        radius=(np.linalg.norm(error)+np.linalg.norm(envelope)/W0+64*eps*np.linalg.norm(abs(A)@abs(delta)))/singular[-1]
        return abs(delta[:-1])+radius,dict(kind='local_linear_estimate_not_certified_nonlinear_enclosure',sigma_min=float(singular[-1]),linear_residual=float(np.linalg.norm(error)),roundoff_radius=float(radius),equilibrium_defect_correction=delta.tolist())
    eqstep,eqerror=charged(base['A'],np.r_[-base['r']/W0,0.],'base-equilibrium-defect')
    unit,uniterror=charged(base['A'],np.r_[np.zeros(n),-1.],'unit-negative-control')
    base_envelope=floating_envelope(base,'base'); qbase_unc,base_uncertainty=sensitivity_uncertainty(base,eqstep,eqerror,base_envelope)
    radius=max(2e-9,1e-8,64*abs(np.spacing(base['control']))); span=4*radius; posttarget=base['control']-span
    prediction=eqstep+span*unit; qseed=qc+prediction[:-1]; lamseed=lamc+prediction[-1]
    pre=material_observer(model,mapping,base['u'],H,base['trial'],qbase_unc)
    if np.linalg.norm(prediction[:-1],np.inf)<=2*np.max(qbase_unc):
        save(dict(outcome='unresolved_base_equilibrium_uncertainty_exceeds_planned_advance',base_uncertainty=base_uncertainty,planned_span=span)); return
    predicted=observe('post-target-linear-prediction',qseed,lamseed)
    base_signature=base['events'].signature; upper_signature=predicted['events'].signature
    # Source-bound event ordering on THIS RAY only. No faces are held fixed.
    entry=dict(status='no_fingerprint_change_on_fixed_ray',observations=0)
    if not np.array_equal(base_signature,upper_signature):
        lo,hi=0.,1.; upper=predicted
        for iteration in range(48):
            mid=(lo+hi)/2
            if mid==lo or mid==hi or np.array_equal(qc+mid*prediction[:-1],qc+hi*prediction[:-1]): break
            value=observe(f'entry-ray-{iteration+1}',qc+mid*prediction[:-1],lamc+mid*prediction[-1]); entry['observations']+=1
            if np.array_equal(value['events'].signature,base_signature): lo=mid
            else: hi=mid; upper=value
        entry.update(status='fingerprint_boundary_on_fixed_ray_only',fraction=hi,control_distance=abs(upper['control']-base['control']),full_q_distance=float(np.linalg.norm(upper['q']-qc,np.inf)),base_q_uncertainty_inf=float(np.max(qbase_unc)),ordering_resolved_by_local_estimate=bool(np.linalg.norm(upper['q']-qc,np.inf)>2*np.max(qbase_unc)))
    # One clone preserves all normal public leases/guards and accepted rollback.
    tree=ast.parse(inspect.getsource(ns._solve_static_displacement_control)); changes=[]
    class Specialize(ast.NodeTransformer):
        def visit_FunctionDef(self,node):
            if node.name=='_solve_static_displacement_control': node.name='_finite_entry_kernel'
            return self.generic_visit(node)
        def visit_Assign(self,node):
            names=[t.id for t in node.targets if isinstance(t,ast.Name)]
            for key,value in [('target_scale',.2),('max_control_cutbacks',0)]:
                if key in names: node.value=ast.Constant(value); changes.append(dict(name=key,value=value))
            if names==['states_new'] and isinstance(node.value,ast.Name) and node.value.id=='committed_states':
                changes.append(dict(name='uncommitted_seed_after_accepted_origin',value=True))
                return [node,*ast.parse('assert T.shape == _diagnostic_T.shape and (T != _diagnostic_T).nnz == 0\nq = _diagnostic_q.copy()\nlam = _diagnostic_lam').body]
            return self.generic_visit(node)
    tree=ast.fix_missing_locations(Specialize().visit(tree)); (out/'guarded-kernel.py').write_text(ast.unparse(tree))
    def run_target(label,target,seedq,seedlam):
        nonlocal global_solves
        remaining=40-global_solves
        if remaining<=0: return None
        scope=dict(ns.__dict__); real_factorize=ns.factorize
        scope.update(_diagnostic_q=seedq.copy(),_diagnostic_lam=float(seedlam),_diagnostic_T=T)
        def factorize(matrix,*args,**kwargs):
            frame=inspect.currentframe().f_back
            try: local=dict(frame.f_locals)
            finally: del frame
            handle=real_factorize(matrix,*args,**kwargs)
            class Handle:
                def __getattr__(self,key): return getattr(handle,key)
                def solve(self,rhs):
                    nonlocal global_solves
                    assert global_solves<40
                    global_solves+=1; delta=handle.solve(rhs)
                    record=dict(label=label,global_solve=global_solves,iteration=local.get('iteration'),residual=local.get('residual_norm'),reference=local.get('reference'),lam=local.get('lam'))
                    calls.append(record)
                    with (out/'newton.jsonl').open('a') as stream: stream.write(json.dumps(record)+'\n')
                    (out/(label+'-pending.pkl')).write_bytes(pickle.dumps(dict(u=local['u'].copy(),q=local['q'].copy(),H=copy.deepcopy(dict(local['committed_states'])),lam=local['lam'],matrix=matrix.copy(),rhs=np.asarray(rhs).copy(),delta=np.asarray(delta).copy())))
                    return delta
            return Handle()
        scope['factorize']=factorize; exec(compile(tree,str(out/'guarded-kernel.py'),'exec'),scope)
        original=ns._solve_static_displacement_control; ns._solve_static_displacement_control=scope['_finite_entry_kernel']
        try:
            result=solve_static_nonlinear(model,load,control='displacement',displacement_control=DisplacementControl(node_id=probe,dof='uz',target_displacement=target),kinematics='corotational',corotational_tangent='work_conjugate',num_steps=1,max_iterations=remaining,tolerance=1e-8,initial_displacements=cur['displacements'].copy(),initial_element_states=H,equilibrate_initial_state=False,emit_restart_checkpoint=False,record_increment_snapshots=True)
        finally: ns._solve_static_displacement_control=original
        raw[label+'-result']=dict(u=result.displacements.copy(),H=copy.deepcopy(dict(result.element_states)),lam=result.load_factor,status=result.status,reason=result.stop_reason,info=dict(result.info))
        return result
    postresult=run_target('post-entry',posttarget,qseed,lamseed)
    report=dict(diagnostic_only=True,original_target_acceptance=False,base_uncertainty=base_uncertainty,control_radius=radius,span=span,diagnostic_target=posttarget,entry_ray=entry,kernel_specializations=changes)
    if postresult is None or postresult.status!='completed':
        report.update(outcome='actual_post_entry_corrector_not_completed',status=None if postresult is None else postresult.status,reason=None if postresult is None else postresult.stop_reason); save(report); return
    qpost=ns._reduced_coordinates(T,u0,mapping.to_linear_displacement(postresult.displacements))
    post=observe('post-entry-frozen-H-reconstruction',qpost,float(postresult.load_factor),True)
    post_envelope=floating_envelope(post,'post')
    if global_solves>=40: report.update(outcome='unresolved_no_budget_for_post_error_bound'); save(report); return
    poststep,posterror=charged(post['A'],np.r_[-post['r']/W0,0.],'post-equilibrium-defect')
    qpost_unc,post_uncertainty=sensitivity_uncertainty(post,poststep,posterror,post_envelope)
    obs=material_observer(model,mapping,post['u'],H,post['trial'],qpost_unc)
    raw['base-observer']=pre; raw['post-observer']=obs
    signal=float(np.linalg.norm(obs['correction'])); force_error=max(1e-8*post['reference'],float(np.linalg.norm(base_envelope)),float(np.linalg.norm(post_envelope)),float(np.linalg.norm(base['r'])))
    # Independently check the physical strain pullback at one common direction.
    # Fourth-order central stencil, fixed machine-derived h; no scale sweep.
    direction=qpost-qc; norm=float(np.linalg.norm(direction,np.inf))
    if norm==0.:
        report.update(outcome='unresolved_no_representable_post_state'); save(report); return
    h=eps**.2*max(1.,float(np.linalg.norm(qpost,np.inf)))/norm
    strain_points=[]
    for multiplier in (2.,1.,-1.,-2.):
        value=observe('post-strain-fd-'+str(multiplier),qpost+multiplier*h*direction,post['lam'])
        strain_points.append(value['events'].strains)
    finite=(-strain_points[0]+8*strain_points[1]-8*strain_points[2]+strain_points[3])/(12*h)
    predicted_strain=obs['strain_jacobian']@direction
    strain_jacobian_error=float(np.linalg.norm(finite-predicted_strain)/max(np.linalg.norm(predicted_strain),np.finfo(float).tiny))
    raw['strain-jacobian-check']=dict(finite=finite,predicted=predicted_strain,step=h,relative_error=strain_jacobian_error)
    positive=[]; unresolved=[]
    for old,witness in zip(pre['witnesses'],obs['witnesses']):
        alpha_ulp=64*(abs(np.spacing(witness['alpha']))+abs(np.spacing(witness['alpha_old'])))
        if witness['alpha']-witness['alpha_old']>alpha_ulp and witness['plastic_change']>witness['plastic_ulp']:
            strain_advance=float(np.max(abs(witness['strain']-old['strain'])))
            strain_error=float(np.max(witness['strain_uncertainty']+old['strain_uncertainty']))
            item=dict(element=witness['element'],point=witness['point'],kind=witness['kind'],loading=witness['loading'],loading_uncertainty=witness['loading_uncertainty'],strain_advance=strain_advance,strain_uncertainty=strain_error,consistency=witness['consistency'])
            positive.append(item)
            if witness['loading']<=witness['loading_uncertainty']+64*eps or strain_advance<=2*strain_error or witness['consistency']>witness['consistency_tolerance']: unresolved.append(item)
    case=dict(model=model,load=load,probe=probe,grid=grid,coupling='direct',result=postresult)
    returned_eq=_independent_equilibrium(case); frozen_eq=_independent_equilibrium(case,displacements=post['u'],load_factor=post['lam'],element_states=H)
    constraints=constraint_residual_summary(model,mapping.to_linear_displacement(postresult.displacements))
    actual_advance=base['control']-post['control']; qadvance=float(np.linalg.norm(qpost-qc,np.inf)); qerror=float(np.max(qbase_unc+qpost_unc))
    wrench=lambda eq: np.linalg.norm(eq['balance'])<=1e-6*max(np.linalg.norm(eq['applied_wrench']),1e-30)
    resolved=bool(actual_advance>2*radius and qadvance>2*qerror and signal>2*force_error and np.linalg.norm(post['r'])<=min(1e-8*post['reference'],signal/2) and positive and not unresolved and obs['stress_identity_pass'] and obs['projected_stress_identity_error']<force_error and strain_jacobian_error<=1e-7 and frozen_eq['relative_residual']<=1e-7 and returned_eq['relative_residual']<=1e-7 and wrench(frozen_eq) and wrench(returned_eq) and constraints['status']=='passed' and abs(post['control']-posttarget)<=2e-9)
    report.update(outcome='resolved_actual_post_entry_equilibrium' if resolved else 'unresolved_actual_post_entry_signal_or_error',actual_advance=actual_advance,q_advance=qadvance,q_uncertainty=qerror,post_uncertainty=post_uncertainty,plastic_force_signal=signal,force_error_radius=force_error,stress_identity_pass=obs['stress_identity_pass'],projected_stress_identity_error=obs['projected_stress_identity_error'],strain_jacobian_relative_error=strain_jacobian_error,frozen_relative_residual=frozen_eq['relative_residual'],returned_relative_residual=returned_eq['relative_residual'],frozen_wrench_pass=bool(wrench(frozen_eq)),returned_wrench_pass=bool(wrench(returned_eq)),constraints=constraints,positive_returned_points=positive,unresolved_returned_points=unresolved)
    if resolved:
        targetresult=run_target('original-first-target',float(capture['target']),qpost,float(postresult.load_factor))
        if targetresult is not None:
            case['result']=targetresult; targeteq=_independent_equilibrium(case)
            targetq=ns._reduced_coordinates(T,u0,mapping.to_linear_displacement(targetresult.displacements)); target=observe('original-target-frozen-H',targetq,float(targetresult.load_factor))
            targetconstraint=constraint_residual_summary(model,mapping.to_linear_displacement(targetresult.displacements))
            passed=bool(targetresult.status=='completed' and abs(target['control']-capture['target'])<=1e-8 and np.linalg.norm(target['r'])<=1e-8*target['reference'] and targeteq['relative_residual']<=1e-7 and wrench(targeteq) and targetconstraint['status']=='passed')
            report.update(original_first_target_strict_pass=passed,original_first_target_status=targetresult.status,original_first_target_reason=targetresult.stop_reason,original_first_target_control=target['control'],original_first_target_relative=targeteq['relative_residual'])
    assert global_solves<=40
    save(report)


if __name__=='__main__': main()


