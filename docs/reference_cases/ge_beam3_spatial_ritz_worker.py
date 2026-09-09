"""Bounded full-spatial continuum trial work on immutable saved endpoints."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
from time import monotonic

ARCHIVE=Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-next-reference-5469c43-20260909')
MANIFEST='6e4ee30363656257d27db2fc5ace7ff24b76472b17050e6481af6d72ffe82ff6'
INPUTS={'plus':(1580596,'deaded9e95bcafe8654b9b51143d38c12fd194422458ed420c1ab139aa070a5f'),
        'minus':(1585040,'6a2d9cdc2e0a66d8894965783bf2f2311122ac8bc57b11092f1c09ec66ac774f')}


def canonical(value):return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode('ascii')
def unique(pairs):
    result={}
    for k,v in pairs:
        if k in result:raise ValueError('duplicate key')
        result[k]=v
    return result
def reject(value):raise ValueError('nonfinite JSON')
def strict(raw):
    value=json.loads(raw,object_pairs_hook=unique,parse_constant=reject)
    if canonical(value)!=raw:raise ValueError('noncanonical bytes')
    return value
def source(sign,root=ARCHIVE):
    if sign not in INPUTS:raise ValueError('registered signed endpoint')
    raw=(root/'manifest.json').read_bytes()
    if sha256(raw).hexdigest()!=MANIFEST:raise ValueError('saved endpoint manifest')
    manifest=strict(raw);relative='wave/'+sign+'-a/output/comparison.json'
    rows=[r for r in manifest['entries'] if r['path']==relative]
    count,digest=INPUTS[sign]
    if rows!=[dict(path=relative,bytes=count,sha256=digest)]:raise ValueError('bound input extent')
    raw=(root/relative).read_bytes()
    if len(raw)!=count or sha256(raw).hexdigest()!=digest:raise ValueError('saved endpoint bytes')
    return strict(raw)


def evaluate(value,progress):
    import numpy as np
    from scipy.linalg import eigh,expm_frechet
    from docs.reference_cases.ge_beam3_spatial_next_reference import unpack
    from docs.reference_cases import ge_beam3_spatial_second_variation as form
    from docs.reference_cases.ge_beam3_spatial_continuum import matrix
    start=monotonic();poly=unpack(value['polynomial']);c=np.diag([1000.,400.,400.,.02,.01,.02])
    inverse=1/np.diag(c);order=24
    def check():
        if monotonic()-start>60:raise RuntimeError('continuum trial-work 60-second bound')
    def sites(quadrature):
        points,weights=np.polynomial.legendre.leggauss(quadrature)
        for segment in range(4):
            lo=-1.+.5*segment
            for t,w in zip(points,weights):
                check();u=(t+1)/2;x=lo+.5*u;jac=float(np.sqrt(1+.04*x*x))
                y=poly(u)[13*segment:13*(segment+1)];r=matrix(y[3:7])
                stress=np.r_[r.T@y[7:10],r.T@y[10:13]];strain=inverse*stress
                velocity=r@(np.r_[1.,0.,0.]+strain[:3])
                q,dq=form.variation_basis(x,jac,order)
                yield float(w*.25*jac),r,velocity,y[7:10],y[10:13],strain,q,dq
    matrices={};symmetry={}
    for quadrature in (64,128):
        h=np.zeros((144,144));mass=np.zeros_like(h)
        for weight,r,v,n,m,e,q,dq in sites(quadrature):
            d,b,f=form.blocks(r,c,v,n,m)
            h+=weight*(dq.T@d@dq+dq.T@b@q+q.T@b.T@dq+q.T@f@q)
            mass+=weight*(q.T@q)
        error=float(np.max(abs(h-h.T))/(1+np.max(abs(h))))
        if error>1e-11:raise ValueError('full spatial Hessian symmetry')
        symmetry[str(quadrature)]=error
        # Roundoff symmetrization is disclosed. Raw h and its error are saved.
        matrices[quadrature]=(h,mass)
        progress(dict(stage='spatial-trial-integration',quadrature=quadrature))
    rows=[];chosen=None
    for nmode in (8,16,24):
        indices=np.concatenate([np.arange(i*order,i*order+nmode) for i in range(6)])
        h,mass=matrices[128];a=h[np.ix_(indices,indices)];g=mass[np.ix_(indices,indices)]
        vals,vecs=eigh(.5*(a+a.T),g,subset_by_index=(0,0),driver='gvx')
        vector=np.zeros(144);vector[indices]=vecs[:,0]
        pivot=int(np.argmax(abs(vector)))
        if vector[pivot]<0:vector*=-1
        rows.append(dict(modes_per_component=nmode,dimension=6*nmode,lowest_ritz_value=float(vals[0])))
        chosen=vector
    h,mass=matrices[128];trial=chosen
    values=[];directs=[]
    for quadrature in (64,128):
        values.append(float(trial@matrices[quadrature][0]@trial))
        direct=0.
        for w,r,v,n,m,e,q,dq in sites(quadrature):direct+=w*form.direct_density(r,c,v,n,m,q@trial,dq@trial)
        directs.append(float(direct))
    if max(abs(a-b)/(1+abs(a)) for a,b in zip(values,directs))>1e-11:
        raise ValueError('block/direct continuum work disagreement')
    if abs(values[0]-values[1])/max(abs(values[1]),1e-30)>1e-8:
        raise ValueError('fixed-trial quadrature disagreement')
    # Direct finite-rotation potential; baseline strain comes from the saved
    # reference constitutive fields, not from a native beam or Ritz Hessian.
    energy={t:0. for t in (0.,.001,-.001,.0005,-.0005)}
    for weight,r,v,n,m,e,basis,derivative in sites(128):
        q=basis@trial;dq=derivative@trial
        for t in energy:
            f,fs=expm_frechet(t*form.skew(q[3:]),t*form.skew(dq[3:]))
            spin=f.T@fs;axl=np.array([spin[2,1],spin[0,2],spin[1,0]])
            changed=np.r_[r.T@f.T@(v+t*dq[:3])-np.r_[1.,0.,0.],e[3:]+r.T@axl]
            energy[t]+=float(weight*.5*changed@c@changed)
    differences=[(energy[t]-2*energy[0.]+energy[-t])/t**2 for t in (.001,.0005)]
    extrapolated=(4*differences[1]-differences[0])/3
    error=abs(extrapolated-values[1])/(1+abs(values[1]))
    if error>1e-7:raise ValueError('finite rotation energy variation disagreement')
    # Finite Ritz negatives imply admissible negative directions numerically;
    # positive Ritz values cannot rule out other unstable continuum directions.
    negative=values[1]<0 and extrapolated<0 and abs(values[1])>100*abs(values[1]-extrapolated)
    check();progress(dict(stage='spatial-trial-work-complete',negative=bool(negative)))
    return dict(rows=rows,trial=trial.tolist(),trial_component_norms=np.linalg.norm(trial.reshape(6,24),axis=1).tolist(),
        work_orders=values,direct_work_orders=directs,variation_energy={str(k):v for k,v in energy.items()},
        finite_differences=differences,extrapolated_second_variation=float(extrapolated),directional_error=float(error),
        symmetry=symmetry,raw_hessian=h.tolist(),gram=mass.tolist(),trial_norm=float(trial@mass@trial),
        numerical_negative_direction=bool(negative),full_inertia_proved=False,interval_certificate=False,
        stable_equilibrium_proved=False,spatial_dead_load_tangent_zero=True,interior_control_imposed=False,
        production_qualified=False,independent_author_review=False)


def worker(revision,sign,output):
    from docs.reference_cases.ge_beam3_fibre_arch_probe import guard
    from docs.reference_cases.e4_pl_s3_v2_bounded_process import THREAD_ENVIRONMENT
    guard(revision)
    if any(os.environ.get(k)!=v for k,v in THREAD_ENVIRONMENT.items()):raise ValueError('one numerical thread')
    value=source(sign);root=Path(output);root.mkdir(exist_ok=False)
    def progress(row):print(json.dumps(row,sort_keys=True),flush=True)
    progress(dict(stage='authority-complete',sign=sign))
    result=evaluate(value,progress)
    result.update(schema='GE_BEAM3_FULL_SPATIAL_CONTINUUM_TRIAL_WORK_V1',revision=revision,sign=sign,
        source_sha256=INPUTS[sign][1],amplitude=value['reference']['amplitude'])
    raw=canonical(result)
    with (root/'diagnostic.json').open('xb') as stream:stream.write(raw)
    source(sign);guard(revision)
    with (root/'trial-work.json').open('xb') as stream:stream.write(raw)
    progress(dict(stage='evidence-complete',bytes=len(raw),sha256=sha256(raw).hexdigest()))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--revision',required=True)
    parser.add_argument('--sign',choices=tuple(INPUTS),required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args();worker(args.revision,args.sign,args.output)
