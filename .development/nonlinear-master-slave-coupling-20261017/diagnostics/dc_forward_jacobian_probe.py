"""Frozen modified-Newton forward-branch discriminant, never commits history."""
import argparse, copy, json, pickle, sys
from pathlib import Path
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve
sys.path.insert(0, str(Path(__file__).resolve().parents[3]/'tests'))
from test_nonlinear_beam_shell_slice3_continuation import _build_ep_model
from anysolver.corotational import build_nonlinear_rotating_mpc_map
from anysolver.nonlinear_static import _assemble_nonlinear_system
from assessment_support import identical, source_identity

def main():
    p=argparse.ArgumentParser(); p.add_argument('capture'); p.add_argument('output'); a=p.parse_args()
    out=Path(a.output); out.mkdir(parents=True, exist_ok=False)
    c=pickle.loads(Path(a.capture).read_bytes()); before=copy.deepcopy(c['states'])
    model,*_=_build_ep_model('interp'); m=build_nonlinear_rotating_mpc_map(model,c['T'])
    def evaluate(q,lam,tangent):
        u=m.apply_kinematics(np.asarray(c['T']@q+c['u0']).reshape(-1))
        history=copy.deepcopy(c['states']); frozen=copy.deepcopy(history)
        f,k,_=_assemble_nonlinear_system(model,u,history,5,tangent=tangent,kinematics='corotational',corotational_tangent='work_conjugate')
        assert identical(history,frozen)
        external=c['F_const']+lam*c['F']
        rhs=np.r_[m.reduce_force(u,external-f),c['target']-float(c['row']@u)]
        if not tangent: return rhs,None
        kr=m.reduce_tangent(u,k,f-external)
        row=np.asarray(c['row']@m.jacobian(u)).reshape(-1)
        A=sparse.bmat([[kr,sparse.csr_matrix((-m.reduce_force(u,c['F'])).reshape(-1,1))],[sparse.csr_matrix(row.reshape(1,-1)),sparse.csr_matrix((1,1))]],format='csr')
        return rhs,A
    lookahead=1e-4
    _,A=evaluate(c['q']+lookahead*c['delta'][:-1],c['lam']+lookahead*c['delta'][-1],True)
    delta=spsolve(A,c['rhs']); rows=[]; alpha=1.; phi0=c['merit']
    for _ in range(8):
        rhs,_=evaluate(c['q']+alpha*delta[:-1],c['lam']+alpha*delta[-1],False)
        merit=np.linalg.norm(rhs[:-1])/(c['tolerance']*c['reference'])+abs(rhs[-1])/(c['tolerance']*c['target_scale'])
        rows.append(dict(alpha=alpha,residual=float(np.linalg.norm(rhs[:-1])),merit=float(merit),improves=bool(merit<=(1-1e-4*alpha)*phi0)))
        if rows[-1]['improves']: break
        denominator=merit-phi0+alpha*phi0
        alpha=float(np.clip(.5*alpha*alpha*phi0/denominator,.1*alpha,.5*alpha)) if np.isfinite(denominator) and denominator>0 else alpha*.5
    assert identical(c['states'],before)
    (out/'raw.pkl').write_bytes(pickle.dumps(dict(matrix=A,delta=delta)))
    report=dict(identity=source_identity(),lookahead=lookahead,trials=rows,input_history_unchanged=True,linear_error=float(np.linalg.norm(A@delta-c['rhs'])/np.linalg.norm(c['rhs'])))
    (out/'result.json').write_text(json.dumps(report,indent=2)); print(json.dumps(report))
if __name__=='__main__': main()
