"""Saved FB algebra audit only: no FE/material evaluation or linear solves."""
import argparse,json,pickle
from pathlib import Path
import numpy as np

p=argparse.ArgumentParser(); p.add_argument('folder'); p.add_argument('output'); a=p.parse_args()
folder=Path(a.folder); out=Path(a.output); out.mkdir(parents=True,exist_ok=False)
raw=pickle.loads((folder/'predictor-raw.pkl').read_bytes()); terms=pickle.loads((folder/'cone-terms.pkl').read_bytes())
states=pickle.loads((folder/'fb-raw.pkl').read_bytes()); info=json.loads((folder/'cone.json').read_text())
base=raw['accepted_H11']; A=raw['direction-1-selected']['A'].copy(); n=A.shape[0]-1; k=len(terms); eps=np.finfo(float).eps
for term in terms: A[:n,:n]+=term['delta']/4000.
A[-1,:]=base['A'][-1,:]; A[:-1,-1]=base['A'][:-1,-1]
rhs=np.r_[-base['r']/4000.,json.loads((folder/'predictor.json').read_text())['required_control_increment']]
Y=np.asarray([t['yield_stress'] for t in terms]); E=np.asarray([t['elastic_modulus'] for t in terms]); h=np.asarray([t['h'] for t in terms])
wy=-np.asarray([t['row'] for t in terms])/(E*Y)[:,None]; wg=h/(E*Y*Y)
P=np.column_stack([t['coupling']/t['yield_stress'] for t in terms])/4000.
def residual(x,complex_extension=False):
    z=x[:n+1]; gamma=x[n+1:]; w=wy@z[:-1]+wg*gamma
    top=A@z-rhs; top[:-1]-=P@gamma
    norm=np.sqrt(gamma*gamma+w*w) if complex_extension else np.hypot(gamma,w)
    return np.r_[top,norm-gamma-w]
def jacobian(x):
    gamma=x[n+1:]; w=wy@x[:n]+wg*gamma; norm=np.hypot(gamma,w)
    ag=np.full(k,1/np.sqrt(2)-1); aw=ag.copy(); nz=norm>0
    ag[nz]=gamma[nz]/norm[nz]-1; aw[nz]=w[nz]/norm[nz]-1
    J=np.zeros((len(x),len(x))); J[:n+1,:n+1]=A; J[:n,n+1:]=-P
    J[n+1:,:n]=aw[:,None]*wy; J[n+1:,n+1:]=np.diag(ag+aw*wg)
    return J
reports=[]
for i,state in enumerate(states):
    x=state['x']; R=residual(x); J=jacobian(x); sv=np.linalg.svd(J,compute_uv=False)
    item=dict(index=i,saved_residual_reconstruction_inf=float(np.max(abs(R-state['residual']))),jacobian_sigma_max=float(sv[0]),jacobian_sigma_min=float(sv[-1]),dimensionless_condition=float(sv[0]/sv[-1]),componentwise=[])
    if i+1<len(states):
        alpha=info['semismooth'][i]['armijo_trials'][-1]['alpha']; nxt=states[i+1]['x']
        step=(nxt-x)/alpha; error=J@step+R; scale=abs(J)@abs(step)+abs(R)
        uncertainty=abs(J)@(64*eps*(abs(nxt)+abs(x))/alpha)
        ratio=abs(error)/np.maximum(scale,np.finfo(float).tiny)
        item.update(reconstructed_accepted_step_only=True,alpha=alpha,absolute_linear_residual_inf=float(np.max(abs(error))),normwise_backward_error=float(np.linalg.norm(error)/(np.linalg.norm(J)*np.linalg.norm(step)+np.linalg.norm(R))),global_scale_backward_error=float(np.max(abs(error)/np.maximum(1.,scale))))
        for j in np.flatnonzero(ratio>1e-7):
            item['componentwise'].append(dict(row=int(j),kind='control' if j==n else ('force' if j<n else 'FB'),rhs=float(-R[j]),absolute_error=float(error[j]),denominator=float(scale[j]),relative_componentwise=float(ratio[j]),step_reconstruction_roundoff_bound=float(uncertainty[j])))
    else:
        item['step_gap']='Failed final linear step was not saved; no new linear solve is performed to recreate it.'
    reports.append(item)
x=states[-1]['x']; J=jacobian(x); step=eps**2; Jcs=np.zeros_like(J)
assert np.all(np.hypot(x[n+1:],wy@x[:n]+wg*x[n+1:])>0)
for j in range(len(x)):
    z=x.astype(complex); z[j]+=1j*step; Jcs[:,j]=np.imag(residual(z,True))/step
audit=dict(method='Complex-step analytic extension away from nonzero pair norm; step=eps^2 fixed',relative_error=float(np.linalg.norm(J-Jcs)/np.linalg.norm(Jcs)),absolute_error_inf=float(np.max(abs(J-Jcs))),existing_1e_7_oracle_pass=bool(np.linalg.norm(J-Jcs)<=1e-7*np.linalg.norm(Jcs)))
result=dict(existing_algebra_only=True,no_force_material_evaluation_or_global_linear_solve=True,reports=reports,final_jacobian_audit=audit)
(out/'result.json').write_text(json.dumps(result,indent=2)); (out/'operators.pkl').write_bytes(pickle.dumps(dict(A=A,P=P,wy=wy,wg=wg,rhs=rhs,J=J,J_complex=Jcs)))
print(json.dumps(dict(states=len(states),audit=audit,final_condition=reports[-1]['dimensionless_condition'],maximum_reconstructed_absolute_error=max(r.get('absolute_linear_residual_inf',0.) for r in reports))))
