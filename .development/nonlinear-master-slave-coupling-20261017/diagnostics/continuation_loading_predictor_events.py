"""Accepted-H control-directed branch predictor; six total direction solves, forty total corrections."""
import argparse,ast,copy,inspect,json,pickle,sys,time,hashlib
from pathlib import Path
from types import SimpleNamespace
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'tests'))
from test_nonlinear_beam_shell_slice3_continuation import _build_ep_model,_add_tip_load,_independent_equilibrium
from anysolver import DisplacementControl,solve_static_nonlinear
import anysolver.nonlinear_static as ns
from anysolver.corotational import build_nonlinear_rotating_mpc_map,SO3MeanDomainError
from anysolver.constraint_audit import constraint_residual_summary
from anysolver._nonlinear_events import material_events
from assessment_support import identical


def main():
    p=argparse.ArgumentParser(); p.add_argument('capture'); p.add_argument('accepted_folder'); p.add_argument('output'); a=p.parse_args()
    out=Path(a.output); out.mkdir(parents=True,exist_ok=False); started=time.perf_counter()
    c=pickle.loads(Path(a.capture).read_bytes()); folder=Path(a.accepted_folder)
    prev=pickle.loads((folder/'accepted-0010.pkl').read_bytes()); cur=pickle.loads((folder/'accepted-0011.pkl').read_bytes())
    before=pickle.dumps((c,prev,cur))
    model,load,probe,grid=_build_ep_model('direct'); _add_tip_load(model,load,grid)
    T,u0=c['T'],c['u0']; m=build_nonlinear_rotating_mpc_map(model,T)
    qs=[ns._reduced_coordinates(T,u0,m.to_linear_displacement(s['displacements'])) for s in (prev,cur)]
    control_prev,control_cur=float(prev['control']),float(cur['control']); ratio=(c['target']-control_cur)/(control_cur-control_prev)
    q=qs[1]+ratio*(qs[1]-qs[0]); lam=cur['lam']+ratio*(cur['lam']-prev['lam'])
    H=copy.deepcopy(cur['element_states']); Hinput=pickle.dumps(H)
    eps=np.finfo(float).eps
    qc=qs[1].copy(); lamc=float(cur['lam']); branch_log=[]; evaluations=[]; raw={}
    # Length1m, rotation1rad, unit load4000N: work scale4000Nm.
    W0=4000.
    def observe(label,qp,tangent=True):
        Hp=copy.deepcopy(H); old=copy.deepcopy(Hp)
        up=m.apply_kinematics(np.asarray(T@qp+u0).reshape(-1)); up0=up.copy()
        fi,kt,trial=ns._assemble_nonlinear_system(model,up,Hp,5,tangent=tangent,kinematics='corotational',corotational_tangent='work_conjugate')
        assert identical(Hp,old) and np.array_equal(up,up0)
        ev=material_events(model,Hp,trial); assert ev is not None
        rp=m.reduce_force(up,fi-lamc*c['F']-c['F_const'])
        g=np.asarray(c['row']@m.jacobian(up)).reshape(-1)
        A=None
        if tangent:
            kr=m.reduce_tangent(up,kt,fi-lamc*c['F']-c['F_const']).toarray()
            A=np.vstack((np.column_stack((kr/W0,-m.reduce_force(up,c['F'])/W0)),np.r_[g,0.]))
        value=dict(q=qp.copy(),u=up.copy(),r=rp,events=ev,trial=copy.deepcopy(dict(trial)),g=g,A=A)
        raw[label]=value
        evaluations.append(dict(label=label,physical_r=float(np.linalg.norm(rp)),branch=hashlib.sha256(ev.signature.tobytes()).hexdigest()))
        (out/'evaluations.json').write_text(json.dumps(evaluations,indent=2))
        return value
    base=observe('accepted_H11',qc)
    rhs=np.r_[-base['r']/W0,c['target']-float(c['row']@base['u'])]
    # Only existing entry/closure bands identify currently yield-adjacent faces.
    near=np.zeros(len(base['events'].values),dtype=bool); loading=near.copy(); cursor=0
    for eid,state in sorted(base['trial'].items()):
        if not isinstance(state,dict) or 'alpha' not in state: continue
        size=np.asarray(state['alpha']).size
        beam='fiber_strain' in state; entry=1e-9 if beam else 1e-10; closure=1e-8 if beam else 1e-10
        v=base['events'].values[cursor:cursor+size]
        near[cursor:cursor+size]=abs(v+entry)<=closure+64*eps
        loading[cursor:cursor+size]=True; cursor+=3*size
    assert cursor==len(near)
    def select(direction,index):
        d=direction[:-1]; norm=np.linalg.norm(d,np.inf)
        if norm==0. or not np.all(np.isfinite(direction)) or base['g']@d>=0.: return None,'invalid_or_nonnegative_control'
        hk=np.sqrt(eps)*max(1.,np.linalg.norm(qc,np.inf))/norm
        k=observe(f'direction-{index}-machine',qc+hk*d,False)
        values=base['events'].values; rates=(k['events'].values-values)/hk
        uncertainty=64*eps*np.maximum(1.,np.maximum(abs(values),abs(k['events'].values)))/hk
        unresolved=near & (abs(rates)<=uncertainty)
        # A near-surface equation with unresolved sign cannot pick a loading branch.
        if np.any(unresolved & (abs(values)<=64*eps)):
            return None,'near_face_direction_unresolved'
        selected=near & (abs(rates)>uncertainty)
        if not np.any(selected): return None,'no_resolved_yield_faces'
        buffer=64*eps*np.maximum(1.,abs(values)); required=np.zeros(len(values))
        required[selected]=np.maximum((np.sign(rates[selected])*buffer[selected]-values[selected])/rates[selected],0.)
        hstate=64*float(np.max(abs(np.spacing(qc))))/norm
        strain_slope=float(np.max(abs((k['events'].strains-base['events'].strains)/hk)))
        hstrain=64*float(np.max(abs(np.spacing(base['events'].strains))))/strain_slope if strain_slope>0 else 0.
        hp=float(np.nextafter(max(float(np.max(required)),hstate,hstrain),np.inf))
        other=(~selected)&(values*rates<0.)
        cap=float(np.min(-values[other]/rates[other])) if np.any(other) else float('inf')
        record=dict(index=index,machine_scale=hk,probe_scale=hp,event_cap=cap if np.isfinite(cap) else None,selected_faces=int(selected.sum()),unresolved_faces=int(unresolved.sum()))
        branch_log.append(record)
        if not np.isfinite(hp) or hp<=0. or hp>=cap or hk>=cap: return None,'no_common_event_free_interval'
        expected=base['events'].signature.copy(); expected[selected]=rates[selected]>0.
        signs=np.sign(rates[selected])
        def admitted(value):
            if not np.array_equal(value['events'].signature[~selected],base['events'].signature[~selected]):
                return None
            return bool(np.all(signs*value['events'].values[selected]>buffer[selected]))
        # Only actual indicators decide the resolved post-entry side. The known
        # machine probe is the fixed upper endpoint; no bracket expansion.
        upper_admission=admitted(k)
        if upper_admission is None: return None,'unrelated_branch_changed_at_machine_endpoint'
        if not upper_admission: return None,'actual_resolved_post_entry_not_bracketed'
        lo=0.; hi=hk; endpoint=k; bisections=0
        for bisect in range(48):
            mid=(lo+hi)/2.
            if mid==lo or mid==hi or np.array_equal(qc+mid*d,qc+hi*d): break
            try: candidate=observe(f'direction-{index}-event-{bisect+1}',qc+mid*d,False)
            except SO3MeanDomainError: return None,'typed_domain_refusal_in_event_bracket'
            bisections+=1; status=admitted(candidate)
            if status is None: return None,'unrelated_branch_changed_in_event_bracket'
            if status: hi=mid; endpoint=candidate
            else: lo=mid
        try: point=observe(f'direction-{index}-selected',endpoint['q'])
        except SO3MeanDomainError: return None,'typed_domain_refusal_at_resolved_event'
        record['linear_estimate_scale']=hp; record['probe_scale']=hi; record['bisections']=bisections
        record['minimum_signed_margin']=float(np.min(signs*point['events'].values[selected]))
        record['required_margin']=float(np.max(buffer[selected]))
        record['actual_branch']=hashlib.sha256(point['events'].signature.tobytes()).hexdigest()
        record['expected_branch']=hashlib.sha256(expected.tobytes()).hexdigest()
        if admitted(point) is not True or not np.array_equal(expected,point['events'].signature):
            return None,'actual_event_endpoint_unresolved'
        return point,'actual_selected'
    direction=np.linalg.solve(base['A'],rhs); direction_solves=1; seen=set(); consistent=False; why='six_direction_limit'
    point,why=select(direction,1)
    while point is not None and direction_solves<6:
        signature=point['events'].signature.tobytes()
        if signature in seen: why='repeated_branch_cycle'; break
        seen.add(signature)
        revised=np.linalg.solve(point['A'],rhs); direction_solves+=1
        newpoint,why=select(revised,direction_solves)
        if newpoint is None: break
        same=np.array_equal(newpoint['events'].signature,point['events'].signature)
        branch_log[-1]['changed_indicator_indices_from_used_branch']=np.flatnonzero(newpoint['events'].signature!=point['events'].signature).tolist()
        branch_log[-1]['reselects_used_branch']=bool(same)
        direction=revised; point=newpoint
        if same: consistent=True; why='self_consistent_modified_newton_branch'; break
    predictor_report=dict(consistent=consistent,reason=why,direction_solves=direction_solves,near_yield_faces=int(near.sum()),required_control_increment=float(rhs[-1]),predicted_control_increment=float(base['g']@direction[:-1]),branch_log=branch_log)
    (out/'predictor.json').write_text(json.dumps(predictor_report,indent=2)); (out/'predictor-raw.pkl').write_bytes(pickle.dumps(raw))
    if not consistent:
        assert pickle.dumps((c,prev,cur))==before and pickle.dumps(H)==Hinput
        print(json.dumps(predictor_report)); return
    q=qc+direction[:-1]; lam=lamc+direction[-1]
    source=inspect.getsource(ns._solve_static_displacement_control); tree=ast.parse(source)
    changes=[]
    class Specialize(ast.NodeTransformer):
        def visit_FunctionDef(self,node):
            if node.name=='_solve_static_displacement_control': node.name='_fixed_target_kernel'
            return self.generic_visit(node)
        def visit_Assign(self,node):
            names=[t.id for t in node.targets if isinstance(t,ast.Name)]
            for name,value in [('target_scale',.2),('max_control_cutbacks',0)]:
                if name in names:
                    node.value=ast.Constant(value); changes.append(dict(name=name,value=value))
            if names==['states_new'] and isinstance(node.value,ast.Name) and node.value.id=='committed_states':
                changes.append(dict(name='seed_after_committed_attempt_origin',value=True))
                seed=ast.parse("assert T.shape == _diagnostic_T.shape and (T != _diagnostic_T).nnz == 0\nq = _diagnostic_secant_q.copy()\nlam = _diagnostic_secant_lam").body
                return [node,*seed]
            return self.generic_visit(node)
    tree=ast.fix_missing_locations(Specialize().visit(tree)); kernel_source=ast.unparse(tree)
    (out/'fixed-target-kernel.py').write_text(kernel_source)
    scope=dict(ns.__dict__); calls=[]; real_factorize=ns.factorize
    scope.update(_diagnostic_secant_q=q.copy(),_diagnostic_secant_lam=float(lam),_diagnostic_T=T)
    def factorize(matrix,*args,**kwargs):
        frame=inspect.currentframe().f_back
        try: local=dict(frame.f_locals)
        finally: del frame
        handle=real_factorize(matrix,*args,**kwargs)
        class Handle:
            def __getattr__(self,name): return getattr(handle,name)
            def solve(self,rhs):
                delta=handle.solve(rhs); calls.append(dict(iteration=local['iteration'],residual=local['residual_norm'],reference=local['reference'],lam=local['lam']))
                with (out/'iterations.jsonl').open('a') as stream: stream.write(json.dumps(calls[-1])+'\n')
                (out/'latest-pending.pkl').write_bytes(pickle.dumps(dict(u=local['u'].copy(),q=local['q'].copy(),states=copy.deepcopy(dict(local['committed_states'])),lam=local['lam'],delta=np.asarray(delta).copy(),rhs=np.asarray(rhs).copy(),matrix=matrix.copy())))
                return delta
        return Handle()
    scope['factorize']=factorize; exec(compile(tree,str(out/'fixed-target-kernel.py'),'exec'),scope)
    real_kernel=ns._solve_static_displacement_control
    ns._solve_static_displacement_control=scope['_fixed_target_kernel']
    try:
        result=solve_static_nonlinear(
            model,load,control='displacement',displacement_control=DisplacementControl(node_id=probe,dof='uz',target_displacement=c['target']),
            kinematics='corotational',corotational_tangent='work_conjugate',num_steps=1,max_iterations=40-direction_solves,tolerance=1e-8,
            initial_displacements=cur['displacements'].copy(),initial_element_states=H,equilibrate_initial_state=False,
            emit_restart_checkpoint=False,record_increment_snapshots=True)
    finally: ns._solve_static_displacement_control=real_kernel
    assert len(calls)+direction_solves<=40 and pickle.dumps((c,prev,cur))==before and pickle.dumps(H)==Hinput
    case=dict(model=model,load=load,probe=probe,grid=grid,coupling='direct',result=result)
    eq=_independent_equilibrium(case); control=float(c['row']@result.displacements)
    constraints=constraint_residual_summary(model,m.to_linear_displacement(result.displacements))
    finalH=copy.deepcopy(cur['element_states']); fint,K,_=ns._assemble_nonlinear_system(model,result.displacements,finalH,5,tangent=False,kinematics='corotational',corotational_tangent='work_conjugate')
    r=m.reduce_force(result.displacements,c['F_const']+result.load_factor*c['F']-fint)
    reference=max(np.linalg.norm(m.reduce_force(result.displacements,c['F_const']+max(abs(result.load_factor),1.)*c['F'])),1.)
    passed=result.status=='completed' and np.linalg.norm(r)<=1e-8*reference and abs(control-c['target'])<=1e-8 and eq['relative_residual']<=1e-7 and constraints['status']=='passed' and np.linalg.norm(eq['balance'])<=1e-6*max(np.linalg.norm(eq['applied_wrench']),1e-30)
    report=dict(diagnostic_only=True,public_restart_claim=False,status=result.status,reason=result.stop_reason,strict_pass=bool(passed),control=control,target=c['target'],ratio=ratio,
                predicted_lambda=lam,actual_lambda=result.load_factor,predictor=predictor_report,total_direction_and_newton_corrections=len(calls)+direction_solves,total_newton_corrections=len(calls),last_unaccepted_trial=calls[-1] if calls else None,frozen_current_history_residual=float(np.linalg.norm(r)/reference),independent_relative=eq['relative_residual'],constraint_summary=constraints,
                original_accepted_control=control_cur,guarded_public_initial_inputs_valid=True,rollback_origin_preserved=True,
                initial_prediction_control=float(c['row']@m.apply_kinematics(np.asarray(T@q+u0).reshape(-1))),kernel_specializations=changes,input_unchanged=True,
                adaptation=result.info.get('displacement_control_adaptation'),elapsed=time.perf_counter()-started)
    (out/'result.json').write_text(json.dumps(report,indent=2)); (out/'final.pkl').write_bytes(pickle.dumps(dict(u=result.displacements,states=result.element_states,lam=result.load_factor,info=result.info)))
    print(json.dumps(report))


if __name__=='__main__': main()



