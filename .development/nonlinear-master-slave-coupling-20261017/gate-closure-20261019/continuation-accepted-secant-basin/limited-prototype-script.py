"""One fixed-target accepted-secant seed, actual private Newton/globalization."""
import argparse,ast,copy,inspect,json,pickle,sys,time
from pathlib import Path
from types import SimpleNamespace
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'tests'))
from test_nonlinear_beam_shell_slice3_continuation import _build_ep_model,_add_tip_load,_independent_equilibrium
from anysolver import DisplacementControl
import anysolver.nonlinear_static as ns
from anysolver.corotational import build_nonlinear_rotating_mpc_map
from anysolver.constraint_audit import constraint_residual_summary


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
    H=copy.deepcopy(cur['element_states']); Hinput=pickle.dumps(cur['element_states'])
    source=inspect.getsource(ns._solve_static_displacement_control); tree=ast.parse(source)
    changes=[]
    class Specialize(ast.NodeTransformer):
        def visit_FunctionDef(self,node):
            if node.name=='_solve_static_displacement_control': node.name='_fixed_target_kernel'
            return self.generic_visit(node)
        def visit_Assign(self,node):
            names=[t.id for t in node.targets if isinstance(t,ast.Name)]
            for name,value in [('target_scale',float(c['target_scale'])),('max_control_cutbacks',0)]:
                if name in names:
                    node.value=ast.Constant(value); changes.append(dict(name=name,value=value))
            return self.generic_visit(node)
    tree=ast.fix_missing_locations(Specialize().visit(tree)); kernel_source=ast.unparse(tree)
    (out/'fixed-target-kernel.py').write_text(kernel_source)
    scope=dict(ns.__dict__); calls=[]; real_factorize=ns.factorize
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
    result=scope['_fixed_target_kernel'](
        model=model,T=T,u0=u0,F_const=c['F_const'],F_prop=c['F'],stage_vectors=[],load_case=load,constant_load_case=None,load_program=None,
        displacement_control=DisplacementControl(node_id=probe,dof='uz',target_displacement=c['target']),committed_states=H,num_layers=5,num_steps=1,max_iterations=40,tolerance=1e-8,
        info={'kinematics':'corotational','corotational_tangent':'work_conjugate','control':'displacement'},start_time=time.perf_counter(),
        kinematics='corotational',corotational_tangent='work_conjugate',initial_reduced_displacements=q,initial_load_factor=lam,rotating_mpc_map=m,
        record_increment_snapshots=True)
    assert len(calls)<=40 and pickle.dumps((c,prev,cur))==before and pickle.dumps(cur['element_states'])==Hinput
    case=dict(model=model,load=load,probe=probe,grid=grid,coupling='direct',result=result)
    eq=_independent_equilibrium(case); control=float(c['row']@result.displacements)
    constraints=constraint_residual_summary(model,m.to_linear_displacement(result.displacements))
    finalH=copy.deepcopy(cur['element_states']); fint,K,_=ns._assemble_nonlinear_system(model,result.displacements,finalH,5,tangent=False,kinematics='corotational',corotational_tangent='work_conjugate')
    r=m.reduce_force(result.displacements,c['F_const']+result.load_factor*c['F']-fint)
    reference=max(np.linalg.norm(m.reduce_force(result.displacements,c['F_const']+max(abs(result.load_factor),1.)*c['F'])),1.)
    passed=result.status=='completed' and np.linalg.norm(r)<=1e-8*reference and abs(control-c['target'])<=1e-8 and eq['relative_residual']<=1e-7 and constraints['status']=='passed'
    report=dict(diagnostic_only=True,public_restart_claim=False,status=result.status,reason=result.stop_reason,strict_pass=bool(passed),control=control,target=c['target'],ratio=ratio,
                predicted_lambda=lam,actual_lambda=result.load_factor,total_newton_corrections=len(calls),frozen_current_history_residual=float(np.linalg.norm(r)/reference),independent_relative=eq['relative_residual'],constraint_summary=constraints,
                initial_prediction_control=float(c['row']@m.apply_kinematics(np.asarray(T@q+u0).reshape(-1))),kernel_specializations=changes,input_unchanged=True,
                adaptation=result.info.get('displacement_control_adaptation'),elapsed=time.perf_counter()-started)
    (out/'result.json').write_text(json.dumps(report,indent=2)); (out/'final.pkl').write_bytes(pickle.dumps(dict(u=result.displacements,states=result.element_states,lam=result.load_factor,info=result.info)))
    print(json.dumps(report))


if __name__=='__main__': main()
