import argparse,json,math
from pathlib import Path
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import splu
from threadpoolctl import threadpool_info
from scripts.b3_e4_bl5_riesz_controls_dev import beam_norm

p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
assert not a.output.exists()
pools=threadpool_info();assert pools and all(t['num_threads']==1 for t in pools)
cells,supports,subdivision=512,16,8
d=np.diag(np.repeat((1.,1.,1.,.4,.4),supports)).reshape(5,supports,5*supports)
force=np.repeat(np.moveaxis(d[:3],0,1),cells//supports,axis=0)
moment_support=np.moveaxis(np.stack((.05*d[1]-d[4],-.05*d[0]+d[3],np.zeros_like(d[0]))),0,1)
moments=np.repeat(moment_support,cells//supports,axis=0)/cells
knots,h,active,_=beam_norm(1.,.4,cells,subdivision,np.array((0.,0.,-.05)),.1)
u=np.zeros((len(knots),3,5*supports));dx=1/(cells*subdivision)
for e in range(len(knots)-1):u[e:e+2]+=dx*force[e//subdivision]/2
b=np.concatenate((u.reshape(-1,5*supports),moments.reshape(-1,5*supports)))[active]
def residual(z):return np.linalg.norm(h@z-b,axis=0)/np.linalg.norm(b,axis=0)
records=[]
for name in ('direct','diagonal_equilibration'):
    scale=np.ones(h.shape[0]) if name=='direct' else 1/np.sqrt(h.diagonal())
    diagonal=sparse.diags(scale,format='csc')
    factor=splu(diagonal@h@diagonal)
    z=scale[:,None]*factor.solve(scale[:,None]*b)
    history=[]
    for iteration in range(5):
        r=residual(z);history.append(dict(iteration=iteration,max_relative_residual=float(np.max(r)),worst_column=int(np.argmax(r))))
        if iteration<4:z+=scale[:,None]*factor.solve(scale[:,None]*(b-h@z))
    records.append(dict(method=name,history=history,all_columns_residual=r.tolist(),energy_trace=float(np.trace(b.T@z))))
csr=h.tocsr()
def compensated_residual(z):
    out=np.empty_like(b)
    for row in range(csr.shape[0]):
        indices=csr.indices[csr.indptr[row]:csr.indptr[row+1]]
        data=csr.data[csr.indptr[row]:csr.indptr[row+1]]
        for column in range(b.shape[1]):
            terms=[float(b[row,column])]
            for index,value in zip(indices,data):
                x=float(value);y=float(z[index,column]);product=x*y
                terms.extend((-product,-math.fma(x,y,-product)))
            out[row,column]=math.fsum(terms)
    return out
factor=splu(h);z=factor.solve(b);history=[]
for iteration in range(4):
    r=compensated_residual(z)
    history.append(dict(iteration=iteration,max_compensated_relative_residual=float(np.max(np.linalg.norm(r,axis=0)/np.linalg.norm(b,axis=0))),max_raw_relative_residual=float(np.max(residual(z)))))
    if iteration<3:z+=factor.solve(r)
records.append(dict(method='fma_fsum_residual_refinement',history=history))
result=dict(status='COMPLETED_DIAGNOSTIC_ONLY',threads=pools,cells=cells,supports=supports,
    subdivision=subdivision,rows=h.shape[0],records=records,
    equation='H z=B unchanged; positive diagonal coordinate congruence and residual corrections only')
with a.output.open('x') as out:json.dump(result,out,indent=2)
print(json.dumps(dict(status=result['status'],histories=records)))
