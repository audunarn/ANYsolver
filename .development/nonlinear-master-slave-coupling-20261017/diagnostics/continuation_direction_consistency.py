"""Frozen shared-direction branch fixed point, no state commits or FE solve."""
import argparse,copy,hashlib,json,pickle,sys,time
from pathlib import Path
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'tests'))
from test_nonlinear_beam_shell_slice3_continuation import _build_ep_model,_add_tip_load
from anysolver.corotational import build_nonlinear_rotating_mpc_map
from anysolver.nonlinear_static import _assemble_nonlinear_system
from assessment_support import identical


def main():
    p=argparse.ArgumentParser(); p.add_argument('capture'); p.add_argument('output'); a=p.parse_args()
    out=Path(a.output); out.mkdir(parents=True,exist_ok=False); started=time.perf_counter()
    c=pickle.loads(Path(a.capture).read_bytes()); original=copy.deepcopy(c); original_bytes=pickle.dumps(c)
    model,load,probe,grid=_build_ep_model('direct'); _add_tip_load(model,load,grid)
    mapping=build_nonlinear_rotating_mpc_map(model,c['T']); evaluations=0
    def evaluate(q,lam,tangent):
        nonlocal evaluations
        evaluations+=1
        u=mapping.apply_kinematics(np.asarray(c['T']@q+c['u0']).reshape(-1))
        H=copy.deepcopy(c['states']); frozen=copy.deepcopy(H); before=u.copy()
        f,K,trial=_assemble_nonlinear_system(model,u,H,5,tangent=tangent,kinematics='corotational',corotational_tangent='work_conjugate')
        assert identical(H,frozen) and np.array_equal(u,before)
        r=mapping.reduce_force(u,c['F_const']+lam*c['F']-f)
        rhs=np.r_[r,c['target']-float(c['row']@u)]
        A=None
        if tangent:
            kr=mapping.reduce_tangent(u,K,f-c['F_const']-lam*c['F'])
            row=np.asarray(c['row']@mapping.jacobian(u)).reshape(-1)
            A=sparse.bmat([[kr,sparse.csr_matrix((-mapping.reduce_force(u,c['F'])).reshape(-1,1))],[sparse.csr_matrix(row.reshape(1,-1)),sparse.csr_matrix((1,1))]],format='csr')
        signature=[]; material=model.get_material('steel'); curve=material.hardening_curve
        boundaries=[float(curve.eps_p_y1),float(curve.eps_p_y2)]
        for eid,state in sorted(trial.items()):
            if not isinstance(state,dict) or 'alpha' not in state: continue
            alpha=np.asarray(state['alpha']); old=np.asarray(c['states'][eid]['alpha'])
            active=alpha>old
            region=np.searchsorted(boundaries,alpha,side='left')
            signature.append((eid,alpha.shape,active.tobytes(),region.tobytes()))
        return dict(u=u,rhs=rhs,A=A,signature=signature,states=copy.deepcopy(dict(trial)))
    base=evaluate(c['q'],c['lam'],True); rhs=base['rhs']; direction=spsolve(base['A'],rhs)
    lam_scale=max(abs(c['lam']),1.); scale=np.r_[np.ones(len(c['q'])),lam_scale]
    x=np.r_[c['q'],c['lam']]/scale
    def probe_direction(d,tangent=True):
        # Standard first-order difference balance: O(h) truncation against
        # O(eps/h) roundoff in a common nondimensional direction, no fit.
        eta=np.sqrt(np.finfo(float).eps)*max(1.,np.linalg.norm(x,np.inf))/max(np.linalg.norm(d/scale,np.inf),np.finfo(float).tiny)
        return evaluate(c['q']+eta*d[:-1],c['lam']+eta*d[-1],tangent),float(eta)
    rows=[]; raw={'base':base}; consistent=False
    for iteration in range(6):
        selected,eta=probe_direction(direction)
        candidate=np.asarray(spsolve(selected['A'],rhs)); selected_next,eta_next=probe_direction(candidate,False)
        same=selected['signature']==selected_next['signature']
        row=dict(iteration=iteration+1,probe_scale=eta,next_probe_scale=eta_next,
                 selected_branch_consistent=same,direction_relative_change=float(np.linalg.norm(candidate-direction)/max(np.linalg.norm(candidate),1e-30)),
                 linear_backward_error=float(np.linalg.norm(selected['A']@candidate-rhs)/np.linalg.norm(rhs)),
                 base_signature_equal=selected['signature']==base['signature'],
                 selected_fingerprint=hashlib.sha256(pickle.dumps(selected['signature'])).hexdigest(),
                 reselected_fingerprint=hashlib.sha256(pickle.dumps(selected_next['signature'])).hexdigest())
        rows.append(row); raw[iteration]=dict(selected=selected,next=selected_next,candidate=candidate)
        direction=candidate
        if same:
            consistent=True; break
    trials=[]; alpha=1.; phi0=np.linalg.norm(rhs[:-1])/(c['tolerance']*c['reference'])+abs(rhs[-1])/(c['tolerance']*c['target_scale'])
    for i in range(8):
        value=evaluate(c['q']+alpha*direction[:-1],c['lam']+alpha*direction[-1],False)
        phi=np.linalg.norm(value['rhs'][:-1])/(c['tolerance']*c['reference'])+abs(value['rhs'][-1])/(c['tolerance']*c['target_scale'])
        accepted=phi<=(1-1e-4*alpha)*phi0
        trials.append(dict(alpha=alpha,residual=float(np.linalg.norm(value['rhs'][:-1])),control_error=abs(float(value['rhs'][-1])),merit=float(phi),armijo=bool(accepted)))
        if accepted: break
        denominator=phi-phi0+alpha*phi0
        alpha=alpha*.1 if phi>=phi0 else float(np.clip(.5*alpha*alpha*phi0/denominator,.1*alpha,.5*alpha))
    probe,eta=probe_direction(direction,False)
    directional=(rhs-probe['rhs'])/eta; predicted=selected['A']@direction
    assert identical(c['states'],original['states']) and np.array_equal(c['u'],original['u']) and pickle.dumps(c)==original_bytes
    report=dict(diagnostic_only=True,evaluations=evaluations,base_residual=float(np.linalg.norm(rhs[:-1])),directional_branch_consistent=consistent,
                fixed_point=rows,trials=trials,forward_direction_relative_error=float(np.linalg.norm(directional-predicted)/max(np.linalg.norm(predicted),1e-30)),
                captured_rhs_reconstruction_error=float(np.linalg.norm(rhs-c['rhs'])),
                actual_control=float(c['row']@base['u']),target=float(c['target']),
                captured_augmented_matrix_relative_error=float(np.linalg.norm((base['A']-c['matrix']).data)/max(np.linalg.norm(c['matrix'].data),1.)),
                input_unchanged=True,elapsed=time.perf_counter()-started,capture_sha256=hashlib.sha256(Path(a.capture).read_bytes()).hexdigest())
    (out/'raw.pkl').write_bytes(pickle.dumps(raw)); (out/'result.json').write_text(json.dumps(report,indent=2)); print(json.dumps(report))


if __name__=='__main__': main()
