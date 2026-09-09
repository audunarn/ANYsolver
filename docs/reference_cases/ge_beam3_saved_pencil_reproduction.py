"""Saved-pencil diagnostics only. No mechanics or production eigen imports."""
import hashlib
import json
from pathlib import Path
from time import monotonic
import numpy as np
from scipy import linalg

ARCHIVE=Path(r'C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\ge-beam3-native-continuum-frequencies-7a5c504-20260908')
INPUTS={
 'native-n8.json':(339195,'8BBA950126F865B53038827D764F4D8D8ABD84FF736ED9902D3F6B21D486B8E3'),
 'reference-high.json':(633457,'69F620FCCD5C65191327B3FE9E305B2F665116B48337E9B0E9E8C32AFEED8E34')}
RELATIVE=Path('runs/rehearsal-straight-diagonal/pytest/test_native_frequency_converge0')

def canonical(x):
    return (json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def pairs(rows):
    d={}
    for k,v in rows:
        if k in d:raise ValueError('duplicate key')
        d[k]=v
    return d
def load(name,root=ARCHIVE):
    raw=(root/RELATIVE/name).read_bytes();size,digest=INPUTS[name]
    if len(raw)!=size or hashlib.sha256(raw).hexdigest().upper()!=digest:raise ValueError('saved input hash/byte mismatch')
    value=json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
    if raw!=canonical(value):raise ValueError('noncanonical saved input')
    return value

def inspect(packet,previous,*,count):
    started=monotonic()
    k=np.array(packet['stiffness'],dtype=float);m=np.array(packet['mass'],dtype=float)
    if k.ndim!=2 or not 1<=len(k)<=256 or k.shape!=(len(k),len(k)) or m.shape!=k.shape:
        raise ValueError('bounded square saved pencil')
    if not np.isfinite(k).all() or not np.isfinite(m).all():raise ValueError('nonfinite pencil')
    for a in (k,m):
        if np.linalg.norm(a-a.T)>1e-11*max(1.,np.linalg.norm(a)):raise ValueError('asymmetric pencil')
    free=packet['free_dofs'];algebraic=packet['algebraic_dofs']
    for slots in (free,algebraic):
        if len(set(slots))!=len(slots) or any(type(i) is not int or not 0<=i<len(k) for i in slots):
            raise ValueError('invalid saved slots')
    if not set(algebraic)<=set(free) or np.any(m[:,algebraic]):raise ValueError('invalid massless partition')
    physical=[i for i in free if i not in algebraic]
    old=np.array(previous['eigenvalues']);saved=np.array(previous['full_modes'])
    if type(count) is not int or not len(old)<=count<=len(physical):raise ValueError('bounded requested spectrum')
    mapping=np.zeros((len(k),len(physical)));mapping[physical]=np.eye(len(physical))
    if algebraic:
        aa=k[np.ix_(algebraic,algebraic)];np.linalg.cholesky(aa)
        mapping[algebraic]=-np.linalg.solve(aa,k[np.ix_(algebraic,physical)])
    saved_map=np.array(previous['dynamic_map'])
    if saved_map.shape!=mapping.shape or saved.shape!=(len(k),len(old)):raise ValueError('saved modal shape')
    kr=mapping.T@k@mapping;mr=mapping.T@m@mapping
    np.linalg.cholesky(mr)
    # The lower triangular completion is exactly the symmetric input view
    # selected by the LAPACK calls below; no production matrix is changed.
    kl=np.tril(kr)+np.tril(kr,-1).T;ml=np.tril(mr)+np.tril(mr,-1).T
    lower=np.linalg.cholesky(ml)
    def metrics(values,vectors):
        full=mapping@vectors
        residual=(k@full-(m@full)*values)[free]
        norm=float(np.linalg.norm(residual)/max(1.,np.linalg.norm(k)*np.linalg.norm(full),np.linalg.norm(m)*np.linalg.norm(full*values)))
        mass_error=float(np.linalg.norm(full.T@m@full-np.eye(len(values))))
        dual=linalg.solve_triangular(lower,kl@vectors-(ml@vectors)*values,lower=True)
        standard_residual=np.linalg.norm(dual,axis=0)/np.linalg.norm(lower.T@vectors,axis=0)
        # Record the former failed criterion, do not replace its threshold.
        comparison=float(np.max(np.abs(values[:len(old)]-old)/np.maximum(1.,np.abs(old))))
        return dict(eigenvalues=values.tolist(),first_saved_count_difference=comparison,
            original_1e11_reproduction_criterion_passed=bool(comparison<1e-11),
            normalized_full_pencil_residual=norm,mass_orthogonality_error=mass_error,
            estimated_standard_residuals=standard_residual.tolist()),full
    variants={};full_modes={}
    for label,driver,subset in (('same-count','gvx',(0,len(old)-1)),('expanded-count','gvx',(0,count-1)),('full-spectrum','gvd',None)):
        kwargs={} if subset is None else dict(subset_by_index=subset)
        values,vectors=linalg.eigh(kr,mr,driver=driver,**kwargs)
        variants[label],full_modes[label]=metrics(values,vectors)
    old_residual=(k@saved-(m@saved)*old)[free]
    old_error=float(np.linalg.norm(old_residual)/max(1.,np.linalg.norm(k)*np.linalg.norm(saved),np.linalg.norm(m)*np.linalg.norm(saved*old)))
    report=dict(variants=variants,saved_eigenvalues=old.tolist(),saved_normalized_residual=old_error,
        reconstructed_map_exactly_equal=bool(np.array_equal(mapping,saved_map)),
        reconstructed_map_max_difference=float(np.max(np.abs(mapping-saved_map))),
        mass_condition_estimate=float(np.linalg.cond(mr)),
        reduced_stiffness_norm=float(np.linalg.norm(kr)),
        epsilon_times_largest_squared_frequency=float(np.finfo(float).eps*max(abs(np.array(variants['full-spectrum']['eigenvalues'])))),
        standard_residuals_are_floating_estimates_not_rigorous_bounds=True)
    if monotonic()-started>30:raise RuntimeError('saved-pencil inspection deadline')
    return report,full_modes

def physical_mac(modes,reference):
    if modes.shape[0]!=150 or reference['height']!=0.:raise ValueError('registered straight N8 fields only')
    fields=np.array(reference['fields']);lookup={float(t):i for i,t in enumerate(reference['sites'])}
    density=np.diag([2.,2.,2.,.07,.11,.09])
    g,w=np.polynomial.legendre.leggauss(32)
    count=modes.shape[1];overlap=np.zeros((count,len(fields)));nn=np.zeros(count);rr=np.zeros(len(fields))
    for half in range(16):
        for point,weight in zip(g,w):
            tau=float((point+1)/2);t=float(-1+(half+tau)/8)
            u=(1-tau)*modes[6*half:6*half+3]+tau*modes[6*(half+1):6*(half+1)+3]
            q=np.vstack((u,modes[102+3*half:105+3*half]))
            r=fields[:,lookup[t],:6].T;measure=float(weight/16)
            overlap+=measure*q.T@density@r
            nn+=measure*np.sum(q*(density@q),axis=0);rr+=measure*np.sum(r*(density@r),axis=0)
    if np.any(nn<=0) or np.any(rr<=0):raise ValueError('positive physical mode inertia')
    return overlap*overlap/(nn[:,None]*rr[None,:])

def registered_diagnostic():
    data=load('native-n8.json');reference=load('reference-high.json')
    report,modes=inspect(data['packet'],data['modes'],count=8)
    matching={}
    for name in ('expanded-count','full-spectrum'):
        values=np.array(report['variants'][name]['eigenvalues'])[:8]
        mac=physical_mac(modes[name][:,:8],reference)
        matching[name]=dict(mac=mac.tolist(),
            seventh_vs_reference_sixth_frequency_error=float(abs(np.sqrt(values[6]/reference['eigenvalues'][5])-1)),
            sixth_vs_second_torsion_frequency_error=float(abs(np.sqrt(values[5]/((3*np.pi/4)**2*(.8/.07)))-1)))
    report.update(schema='GE_BEAM3_SAVED_PENCIL_REPRODUCTION_DIAGNOSTIC_V1',inputs=INPUTS,
        matching=matching,old_gate_classification_changed=False,new_mechanical_assembly=False,
        production_qualified=False,independent_review='PENDING')
    return report
