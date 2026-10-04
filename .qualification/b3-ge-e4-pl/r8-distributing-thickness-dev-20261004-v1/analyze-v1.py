"""Saved-output reciprocal/centroid work; no new solve or acceptance."""
from pathlib import Path
import hashlib,json,os
import numpy as np
from threadpoolctl import threadpool_info
from scripts.r8_e02_distributing_feasibility import build_case as old_build,_HEADER,_printed_number
from scripts.r8_e02_distributing_thickness import build_case as new_build
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]
OLD=REPO/'.qualification/b3-ge-e4-pl/r8-distributing-multihost-dev-20261004-v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
binding=json.loads((ROOT/'binding-v5.json').read_text(encoding='utf-8'))
assert sha(Path(binding['prior_comparison']))==binding['prior_comparison_sha256']
for rel,expected in binding['sources'].items():assert sha(REPO/rel)==expected
pools=threadpool_info();assert pools and all(p['num_threads']==1 for p in pools)
assert os.environ['NUMBA_DISABLE_JIT']=='1'
prior=json.loads(Path(binding['prior_comparison']).read_text(encoding='utf-8'))
inputs={str(Path(binding['prior_comparison']).relative_to(REPO)):binding['prior_comparison_sha256']}
a=np.array((0.,10.,0.,-.5,0.,0.));mx=np.array((0.,0.,0.,1.,0.,0.))

def solid(nx,ny,name,new=False):
    case=ROOT/f'ccx-{name}-v5' if new else OLD/f'ccx-{nx}x{ny}-{name}-v1'
    p=case/('parsed-v5.json' if new else 'parsed-v1.json')
    inputs[str(p.relative_to(REPO))]=sha(p)
    dat=case/'reference.dat';inputs[str(dat.relative_to(REPO))]=sha(dat)
    record=json.loads(p.read_text(encoding='utf-8'))
    _,_,area=new_build(name) if new else old_build(name,nx,ny)
    text=dat.read_text(encoding='ascii');headers=list(_HEADER.finditer(text))
    values={};bounds={}
    for i,h in enumerate(headers):
        if (h[1].lower(),h[2].upper())!=('displacements','ALL'):continue
        end=headers[i+1].start() if i+1<len(headers) else len(text)
        for line in text[h.end():end].splitlines():
            if not line.strip():continue
            n,*fields=line.split();v=[_printed_number(s) for s in fields]
            values[int(n)]=[x[0] for x in v];bounds[int(n)]=[x[1] for x in v]
    q=np.r_[record['observable']['mean_translation_m'],record['observable']['rotation_components_rad']]
    observed=area.recover(values)
    np.testing.assert_allclose(q,np.r_[observed.mean_translation_m,observed.rotation_components_rad],rtol=0,atol=0)
    b=np.sum([np.abs(w)@bounds[n] for n,w in zip(area.node_ids,area.weights)],axis=0)
    return q,b

def decompose(qx,qf,bx,bf):
    # Fy about the centroid has zero moment. Port Fy includes -0.5Nm Mx;
    # q_centroid=q_Fy+0.5*q_Mx, without assuming any compliance block decouples.
    cross=float(a@qx);reverse=float(mx@qf)
    center=qf+.5*qx;cb=bf+.5*bx
    wc=float(10*center[1])
    expanded=float(a@qf+.5*(cross+reverse)+.25*(mx@qx))
    np.testing.assert_allclose(wc,expanded,rtol=0,atol=1e-20)
    return dict(Mx_pose=qx.tolist(),Fy_pose=qf.tolist(),
        Mx_pose_decimal_bounds=bx.tolist(),Fy_pose_decimal_bounds=bf.tolist(),
        cross_pairing_J=cross,reverse_pairing_J=reverse,
        reciprocity_difference_J=cross-reverse,
        reciprocity_decimal_bound_J=float(np.abs(a)@bx+np.abs(mx)@bf),
        centroid_force_pose=center.tolist(),centroid_force_decimal_bounds=cb.tolist(),
        centroid_force_work_J=wc,centroid_force_work_decimal_bound_J=float(10*cb[1]))

results={}
for nx,ny in ((10,4),(20,8),(40,16)):
    key=f'{nx}x{ny}';base=prior['levels'][key]
    native=[]
    for name in ('Mx','Fy'):
        r=base[name];w=np.array(r['native_rotation_rad']);port=np.array(r['native_port_translation_m'])
        mean=port-np.cross(w,(0.,0.,.05));native.append(np.r_[mean,w])
    x,bx=solid(nx,ny,'Mx');f,bf=solid(nx,ny,'Fy')
    n=decompose(*native,np.zeros(6),np.zeros(6));s=decompose(x,f,bx,bf)
    n['precision_scope']='Binary64 saved native values; zero decimal bounds do not certify numerical error'
    results[key]=dict(native=n,solid_nz2=s,centroid_force_difference_relative=(n['centroid_force_work_J']-s['centroid_force_work_J'])/s['centroid_force_work_J'])
x,bx=solid(40,16,'Mx',True);f,bf=solid(40,16,'Fy',True)
s=decompose(x,f,bx,bf);old=results['40x16']['solid_nz2'];n=results['40x16']['native']
results['40x16']['solid_nz4']=s
results['40x16']['centroid_force_difference_nz4_relative']=(n['centroid_force_work_J']-s['centroid_force_work_J'])/s['centroid_force_work_J']
results['40x16']['centroid_force_thickness_change_relative']=(s['centroid_force_work_J']-old['centroid_force_work_J'])/old['centroid_force_work_J']
record=dict(scope='Saved-output decomposition and print-resolution bounds only; no convergence/physical acceptance',
    inputs=inputs,sources=binding['sources'],pools=pools,results=results,
    limits='Load-format rounding, binary64 solve error, discretization and model-form error are not covered by decimal bounds')
(ROOT/'analysis-v1.json').open('x',encoding='utf-8').write(json.dumps(record,indent=2)+'\n')
print(json.dumps({key:{k:value[k] for k in value if k.startswith('centroid_force_')} for key,value in results.items()}))
