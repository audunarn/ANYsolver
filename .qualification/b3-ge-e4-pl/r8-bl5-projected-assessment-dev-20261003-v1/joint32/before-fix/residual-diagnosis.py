import json,hashlib
from pathlib import Path
import numpy as np
from scipy import sparse
from anysolver._b2_physical_linear_batch_dev import _accurate_sparse_residual
from scripts.r8_bl5_projected_joint_kernel_dev import saved_csr
from threadpoolctl import threadpool_info
r=Path(__file__).resolve().parent
assert all(p['num_threads']==1 for p in threadpool_info())
z=np.load(r/'kernel.npz',allow_pickle=False)
k,c=saved_csr(z,'K',(2940,2940)),saved_csr(z,'C',(80,2940))
f=z['free']; x=z['physical_slots']; sc=z['physical_scale']; rn=z['constraint_row_scale']
s=saved_csr(z,'S',(2305,2305)); cs=c[:,x].toarray()*sc/rn[:,None]
a=sparse.bmat([[k[f][:,f],c[:,f].T],[c[:,f],None]],format='csr')
ss=sparse.bmat([[sparse.diags(sc)@s@sparse.diags(sc),sparse.csr_matrix(cs.T)],[sparse.csr_matrix(cs),None]],format='csr')
sslow=sparse.tril(ss)+sparse.tril(ss,-1).T
rhs=np.vstack((np.column_stack([z[n+'_owner_load'][f] for n in ('fy','mx','mz')]),np.zeros((80,3))))
br=np.vstack((np.column_stack([z[n+'_owner_load'][x]*sc for n in ('fy','mx','mz')]),np.zeros((80,3))))
report={'kernel_npz_sha256':hashlib.sha256((r/'kernel.npz').read_bytes()).hexdigest(),'pools':threadpool_info(),'cases':{}}
for i,case in enumerate(('fy','mx','mz')):
 full=z['corrected_full_solution'][:,i]; red=np.r_[z[case+'_reduced_q'][f],z[case+'_reduced_multipliers']]
 report['cases'][case]={'compensated_full_defect_max':float(np.max(np.abs(_accurate_sparse_residual(a,full[:,None],rhs[:,i:i+1])))), 'compensated_lifted_reduced_defect_max':float(np.max(np.abs(_accurate_sparse_residual(a,red[:,None],rhs[:,i:i+1])))), 'actual_reduced_defect_max':float(np.max(np.abs(_accurate_sparse_residual(ss,z['reduced_solution'][:,i:i+1],br[:,i:i+1])))), 'lower_triangle_reduced_defect_max':float(np.max(np.abs(_accurate_sparse_residual(sslow,z['reduced_solution'][:,i:i+1],br[:,i:i+1]))))}
(r/'residual-diagnosis.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report['cases']))
