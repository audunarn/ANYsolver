"""Frozen direct-state constitutive branch/Jacobian discriminant; harness only."""
import argparse, copy, json, pickle, sys
from pathlib import Path
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve
sys.path.insert(0, str(Path(__file__).resolve().parents[3]/"tests"))
from test_nonlinear_beam_shell_slice3_continuation import _build_ep_model, _add_tip_load
from anysolver.corotational import build_nonlinear_rotating_mpc_map
from anysolver.nonlinear_static import _assemble_nonlinear_system
from assessment_support import identical, source_identity


def main():
    p=argparse.ArgumentParser(); p.add_argument("capture"); p.add_argument("output"); a=p.parse_args()
    out=Path(a.output); out.mkdir(parents=True, exist_ok=False)
    c=pickle.loads(Path(a.capture).read_bytes()); original=copy.deepcopy(c)
    model,load,probe,grid=_build_ep_model("direct"); _add_tip_load(model,load,grid)
    m=build_nonlinear_rotating_mpc_map(model,c["T"])
    def evaluate(q,lam,tangent=False):
        u=m.apply_kinematics(np.asarray(c["T"]@q+c["u0"]).reshape(-1))
        H=copy.deepcopy(c["states"]); H0=copy.deepcopy(H); u0=u.copy()
        f,K,state=_assemble_nonlinear_system(model,u,H,5,tangent=tangent,kinematics="corotational",corotational_tangent="work_conjugate")
        assert identical(H,H0) and np.array_equal(u,u0)
        r=m.reduce_force(u,c["F_const"]+lam*c["F"]-f)
        g=c["target"]-float(c["row"]@u)
        aug=None
        if tangent:
            kr=m.reduce_tangent(u,K,f-c["F_const"]-lam*c["F"])
            row=np.asarray(c["row"]@m.jacobian(u)).reshape(-1)
            aug=sparse.bmat([[kr,sparse.csr_matrix((-m.reduce_force(u,c["F"])).reshape(-1,1))],
                            [sparse.csr_matrix(row.reshape(1,-1)),sparse.csr_matrix((1,1))]],format="csr")
        return dict(u=u,r=r,g=g,state=copy.deepcopy(dict(state)),matrix=aug)
    base=evaluate(c["q"],c["lam"],True); rows=[]; raw={"base":base}
    for h in (1e-8,1e-7,1e-6):
        trial=evaluate(c["q"]+h*c["delta"][:-1],c["lam"]+h*c["delta"][-1],True)
        delta=np.asarray(spsolve(trial["matrix"],np.r_[base["r"],base["g"]]))
        records=[]
        for alpha in (1.,.1,.01,.001,1e-4,1e-5,1e-6,1e-7,1e-8):
            value=evaluate(c["q"]+alpha*delta[:-1],c["lam"]+alpha*delta[-1])
            records.append(dict(alpha=alpha,residual=float(np.linalg.norm(value["r"])),control_error=abs(value["g"])))
        changes=[]
        for eid,state in trial["state"].items():
            if not isinstance(state,dict) or "alpha" not in state: continue
            alpha0=np.asarray(base["state"][eid]["alpha"]); alpha1=np.asarray(state["alpha"])
            changes.append(dict(eid=eid,type=type(model.mesh.elements[eid]).__name__,
                alpha_delta_max=float(np.max(abs(alpha1-alpha0))),
                alpha_changed=int(np.count_nonzero(alpha1!=alpha0)),
                tangent_relative_change=float(np.linalg.norm((trial["matrix"]-base["matrix"]).data)/max(np.linalg.norm(base["matrix"].data),1.))))
        rows.append(dict(h=h,state_changes=changes,correction_trials=records))
        raw[h]=dict(trial=trial,delta=delta)
    assert identical(original["states"],c["states"]) and np.array_equal(original["u"],c["u"])
    report=dict(identity=source_identity(),diagnostic_only=True,input_unchanged=True,
                base_residual=float(np.linalg.norm(base["r"])),checks=rows)
    (out/"raw.pkl").write_bytes(pickle.dumps(raw)); (out/"result.json").write_text(json.dumps(report,indent=2))
    print(json.dumps(report))

if __name__=="__main__": main()
