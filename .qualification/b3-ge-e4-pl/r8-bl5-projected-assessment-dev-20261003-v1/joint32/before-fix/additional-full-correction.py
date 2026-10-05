import json
from pathlib import Path
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import splu
from anysolver._b2_physical_linear_batch_dev import _accurate_sparse_residual
from scripts.r8_bl5_projected_joint_kernel_dev import saved_csr,parity
from threadpoolctl import threadpool_info
r=Path(__file__).resolve().parent;z=np.load(r/'kernel-v2.npz',allow_pickle=False)
assert all(p['num_threads']==1 for p in threadpool_info())
k,c=saved_csr(z,'K',(2940,2940)),saved_csr(z,'C',(80,2940));free=z['free'];fixed=z['fixed'];x=z['physical_slots'];pp=z['resultant_slots']
a=sparse.bmat([[k[free][:,free],c[:,free].T],[c[:,free],None]],format='csc');factor=splu(a)
rhs=np.vstack((np.column_stack([z[n+'_owner_load'][free] for n in ('fy','mx','mz')]),np.zeros((80,3))))
original=z['corrected_full_solution'];defect=_accurate_sparse_residual(a,original,rhs); delta=factor.solve(-defect);result=original+delta
roles=dict(physical=x,shell=x[x<1782],beam_nodes=x[(x>=1782)&(x<2172)],cell_rotations=x[x>=2172])
report={'status':'DEVELOPMENT_DIAGNOSIS_ONLY','full_factorizations':1,'additional_corrections':1,'cases':{}}
for i,n in enumerate(('fy','mx','mz')):
 q=np.zeros(2940);q[free]=result[:2881,i];lm=result[2881:,i];load=z[n+'_owner_load'];reaction=np.zeros(2940);reaction[fixed]=(k@q+c.T@lm-load)[fixed]
 other=(z[n+'_reduced_q'],z[n+'_reduced_multipliers'],z[n+'_reduced_reactions'])
 values=parity((q,lm,reaction),other,roles,pp,z['coordinate_scale'],z['constraint_scale'],(z['shell_rigid_work_map'],z['beam_rigid_work_map']),c,k,load)
 report['cases'][n]={'parity':values,'additional_relative_correction':float(np.linalg.norm(delta[:,i])/np.linalg.norm(original[:,i]))}
np.savez_compressed(r/'additional-full-correction.npz',solution=result,defect=defect,correction=delta)
(r/'additional-full-correction.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({c:max(d['parity'].values()) for c,d in report['cases'].items()}))
