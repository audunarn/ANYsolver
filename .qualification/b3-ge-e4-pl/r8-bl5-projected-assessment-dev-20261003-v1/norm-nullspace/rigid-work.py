from pathlib import Path
import hashlib,json
import numpy as np
from scipy import sparse
from threadpoolctl import threadpool_info
ROOT=Path(__file__).resolve().parent;ASSESS=ROOT.parent/'r8-bl5-projected-integration-v1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
with np.load(ROOT/'native/operators.npz',allow_pickle=False) as z:
 K=sparse.csr_matrix((z['K_data'],z['K_indices'],z['K_indptr']),shape=tuple(z['K_shape']))
 C=sparse.csr_matrix((z['C_data'],z['C_indices'],z['C_indptr']),shape=tuple(z['C_shape']))
 fixed=z['fixed'].copy();work=z['beam_rigid_work_map'].copy()
with np.load(ASSESS/'mixed.npz',allow_pickle=False) as z:
 S=sparse.csr_matrix((z['S_data'],z['S_indices'],z['S_indptr']),shape=tuple(z['S_shape']))
 x=z['physical_slots'].copy();lift=sparse.csr_matrix((z['lift_data'],z['lift_indices'],z['lift_indptr']),shape=tuple(z['lift_shape']))
data=json.loads((ROOT/'native/inputs.json').read_text());layout=data['layout'];ns=layout['counts']['shell_nodes'];nb=layout['counts']['beam_nodes'];base=layout['counts']['physical_dofs'];members=layout['counts']['members']
xyz=np.array(data['xyz_m']);origin=xyz[ns]
# Unit infinitesimal physical beam yaw, about its supported root. The root's
# normal spin is explicitly free. Rotational half-cell fields are physical,
# not guessed from nodal interpolation; full rigid work map validates all slots.
yaw=np.zeros(K.shape[0])
for node in range(nb):
 start=6*(ns+node);yaw[start:start+3]=np.cross((0.,0.,1.),xyz[ns+node]-origin);yaw[start+5]=1.
for member in range(members):
 for cell in (0,1):yaw[base+24*member+3*cell+2]=1.
work_error=float(np.max(np.abs(yaw-work.T[:,5])))
assert work_error<=1e-12 and np.max(np.abs(yaw[fixed]),initial=0.)==0.
r=yaw[x];sr=S@r;kr=K@yaw;gap=C@yaw
normalizer=max(float(sparse.linalg.norm(S))*float(np.linalg.norm(r)),1e-30)
backward=float(np.linalg.norm(sr)/normalizer)
full_backward=float(np.linalg.norm(kr)/max(sparse.linalg.norm(K)*np.linalg.norm(yaw),1e-30))
assert max(backward,full_backward)<=1e-12 and np.linalg.norm(gap)>1e-6
# Pick a physical density row whose action does nonzero work on this rigid
# mode. Such a load is incompatible with isolated supported structural S;
# the coupled KKT remains sound (the prior check already demonstrated that).
i=int(np.argmax(np.abs(gap)));density=np.zeros(len(gap));density[i]=1.
work_q=float(yaw@(C.T@density));assert abs(work_q-gap[i])<=1e-14
pools=threadpool_info();assert all(v['num_threads']==1 for v in pools)
np.savez_compressed(ROOT/'rigid-work.npz',yaw=yaw,supported_yaw=r,K_yaw=kr,S_yaw=sr,C_yaw=gap,density=density)
result=dict(status='COMPLETED_DEVELOPMENT_ONLY',source_sha256=sha(__file__),pools=pools,
 input_sha256={str(p):sha(p) for p in (ROOT/'native/operators.npz',ROOT/'native/inputs.json',ASSESS/'mixed.npz')},
 fixed_yaw_max=float(np.max(np.abs(yaw[fixed]),initial=0.)),rigid_work_map_error=work_error,
 stationary_S_backward=backward,full_native_K_backward=full_backward,
 S_yaw_norm=float(np.linalg.norm(sr)),K_yaw_norm=float(np.linalg.norm(kr)),
 constraint_action_norm=float(np.linalg.norm(gap)),witness_row=i,witness_density_rigid_work=work_q,
 conclusion='Bare supported structural energy has a physical rigid mode coupled by C. Unconstrained inverse-compliance interpretation requires explicit nullspace/work-compatibility treatment; no formulation-failure or F03 acceptance claim.')
(ROOT/'rigid-work.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
print(json.dumps({k:result[k] for k in ('rigid_work_map_error','stationary_S_backward','full_native_K_backward','constraint_action_norm','witness_density_rigid_work')}))
