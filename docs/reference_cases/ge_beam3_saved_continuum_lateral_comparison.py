"""Saved continuum equations versus hash-bound count data; no beam imports."""
import argparse
from dataclasses import fields
from hashlib import sha256
from math import isfinite
import os
from pathlib import Path
import sys
from docs.reference_cases.ge_beam3_retained_prestress_protocol import canonical,strict_bytes,read
from docs.reference_cases.ge_beam3_retained_prestress_wave import publish
from docs.reference_cases.ge_beam3_fibre_arch_probe import guard,ROOT
from docs.reference_cases.e4_pl_s3_v2_bounded_process import THREAD_ENVIRONMENT

ARCHIVE=Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-arch-repeats-307c48d-20260908')
ARCHIVE_SHA='14d83c2b09cce8acf04649ce5e4f4d09fbbb500986ad2bac949ad0a0cb9dd4aa'
COUNTS=Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-stability-interval-cb50f19-20260908/runs/cycle-a/aggregate.json')
COUNTS_SHA='0d37b5220c08233da5840249c2663775e7bc9ee3af39015ac74e6ed94658d8b1'
REF_KEYS={'height','displacement','axial','shear','bending','load','load_slope','force','parameter','fields','iterations',
    'callbacks','nodes','sensitivity_nodes','profile','boundary_error','differential_error','sensitivity_error',
    'strain_energy','work_error','production_qualified'}


def fixed_grid(reference):
    """Exact subset only; retain every original binary64 field component."""
    if type(reference) is not dict or set(reference)!=REF_KEYS:raise ValueError('exact continuum reference schema')
    p=reference['parameter'];f=reference['fields']
    if (type(p) is not list or not 129<=len(p)<=4097 or any(type(x) is not float or not isfinite(x) for x in p)
        or p[0]!=-1. or p[-1]!=0. or any(a>=b for a,b in zip(p,p[1:]))):raise ValueError('ordered bounded union grid')
    if type(f) is not list or len(f)!=4 or any(type(r) is not list or len(r)!=len(p)
        or any(type(x) is not float or not isfinite(x) for x in r) for r in f):raise ValueError('finite four-field grid')
    wanted=[-1.+i/128 for i in range(129)];indices=[]
    for x in wanted:
        if x not in p:raise ValueError('required exact sample missing; interpolation forbidden')
        indices.append(p.index(x))
    result=dict(reference,parameter=[p[i] for i in indices],fields=[[r[i] for i in indices] for r in f])
    return result,indices


def validate_point(point,observation,step):
    if type(point) is not dict or set(point)!={'reference','row','recovered'}:raise ValueError('exact saved point schema')
    r=point['reference'];row=point['row']
    if type(r) is not dict or set(r)!=REF_KEYS:raise ValueError('reference schema')
    if (r['height']!=.1 or r['axial']!=1000. or r['shear']!=400. or r['bending']!=.01
        or r['production_qualified'] is not False or r['profile']!='BVP9'):raise ValueError('frozen continuum model')
    if (type(step) is not int or step not in (6,7,9) or row['step']!=step or observation['step']!=step
        or r['displacement']!=row['drop'] or r['displacement']!=observation['drop']
        or row['load']!=observation['load'] or row['reference_load']!=r['load']):raise ValueError('matched saved equilibrium identity')
    for key,limit in (('boundary_error',1e-11),('differential_error',1e-8),('sensitivity_error',1e-8),('work_error',1e-8)):
        if type(r[key]) is not float or not 0.<=r[key]<=limit:raise ValueError('saved continuum quality')
    if any(type(r[key]) is not float or not isfinite(r[key]) for key in ('load','displacement')):raise ValueError('finite saved equilibrium')
    if r['displacement']<=0.:raise ValueError('positive registered displacement')
    return fixed_grid(r)


def inputs(n,step):
    if type(n) is not int or n not in (4,8,12) or type(step) is not int or step not in (6,7,9):raise ValueError('registered comparison extent')
    cr=read(COUNTS)
    if len(cr)!=25869 or sha256(cr).hexdigest()!=COUNTS_SHA:raise ValueError('count aggregate authority')
    counts=strict_bytes(cr)
    if counts['schema']!='GE_BEAM3_SAVED_ARC_STABILITY_INTERVALS_V1' or counts['production_qualified'] is not False:
        raise ValueError('count aggregate claims')
    selected=[r for r in counts['results'] if r['observation']['macros']==n and r['observation']['step']==step]
    if len(selected)!=1:raise ValueError('unique complete count result')
    science=selected[0];o=science['observation']
    if science['production_qualified'] is not False or science['exact_factor_decoupling'] is not True:raise ValueError('count science claims')
    mr=read(ARCHIVE/'archive-manifest.json')
    if sha256(mr).hexdigest()!=ARCHIVE_SHA:raise ValueError('arch manifest authority')
    manifest=strict_bytes(mr);prefix=f'cycle-a/n{n}/step-{step:02d}/science/'
    data={};bindings={}
    for kind in ('point','state'):
        name=prefix+f'{kind}-{step:02d}.json';raw=read(ARCHIVE/name)
        if manifest[name]!=[len(raw),sha256(raw).hexdigest().upper()]:raise ValueError('saved input changed')
        data[kind]=strict_bytes(raw);bindings[kind]=dict(relative_path=name,bytes=len(raw),sha256=sha256(raw).hexdigest())
    if data['state']['completed_steps']!=step or bindings['state']['sha256']!=o['checkpoint_sha256']:raise ValueError('same checkpoint required')
    reduced,indices=validate_point(data['point'],o,step)
    return dict(reference=reduced,indices=indices,observation=o,bindings=bindings,
        full_reference_sha256=sha256(canonical(data['point']['reference'])).hexdigest(),
        reduced_reference_sha256=sha256(canonical(reduced)).hexdigest())


def parity(det,count):
    if type(det) is not float or not isfinite(det) or det==0.:raise ValueError('nonzero finite determinant required')
    if type(count) is not int or count<0:raise ValueError('nonnegative exact count')
    return dict(determinant_negative=det<0.,discrete_count_odd=bool(count%2),
        parity_agreement=(det<0.)==bool(count%2),continuum_inertia_established=False,root_uniqueness_established=False)


def evaluate(n,step,registered):
    # Only independently reconstructed continuum equations, never the beam core.
    import numpy as np
    from docs.reference_cases.ge_beam3_curved_p5_arch_reference import ArchReference
    from docs.reference_cases.ge_beam3_curved_p5_arch_lateral_reference import arch_generator,boundary_measure
    from docs.reference_cases.ge_beam3_curved_p5_lateral_knot_diagnostic import propagate
    r=registered['reference']
    if set(r)!={f.name for f in fields(ArchReference)}:raise ValueError('frozen reference dataclass schema')
    params=dict(r)
    for k in ('parameter','fields','force'):params[k]=np.array(r[k],dtype=float)
    reference=ArchReference(**params);results={}
    j=np.block([[np.zeros((3,3)),np.eye(3)],[-np.eye(3),np.zeros((3,3))]])
    for stride in (1,2):
        generator=arch_generator(reference,stride=stride,torsion=.02,lateral_bending=.02)
        max_h=0.
        def checked(x,side):
            nonlocal max_h
            h=generator(x,side);error=float(np.linalg.norm(h.T@j+j@h))/max(1.,float(np.linalg.norm(h)))
            if error>1e-11:raise ValueError('continuum Hamiltonian identity')
            max_h=max(max_h,error);return h
        print(dict(stage='continuum-knot-transfer',macros=n,step=step,stride=stride),flush=True)
        transfers=[propagate(checked,np.eye(6),half_nodes=nodes) for nodes in (129,257)]
        a,b=[t['endpoint'] for t in transfers]
        error=float(np.linalg.norm(a-b))/max(1.,float(np.linalg.norm(b)))
        if error>1e-11:raise ValueError('full transfer grid refinement')
        measures=[boundary_measure(t) for t in (a,b)]
        comparisons=[parity(m['normalized_determinant'],registered['observation']['counts']['lateral']) for m in measures]
        if comparisons[0]['determinant_negative']!=comparisons[1]['determinant_negative']:raise ValueError('grid sign disagreement')
        symplectic=float(np.linalg.norm(b.T@j@b-j))/max(1.,float(np.linalg.norm(b))**2)
        if symplectic>1e-10:raise ValueError('registered normalized symplectic check')
        results[str(stride)]=dict(transfer=b.tolist(),coarse_transfer=a.tolist(),refinement_error=error,
            callbacks=[t['callbacks'] for t in transfers],hamiltonian_error=max_h,symplectic_error=symplectic,
            boundary={k:v.tolist() if isinstance(v,np.ndarray) else v for k,v in measures[1].items()},comparison=comparisons[1])
    if results['1']['comparison']['determinant_negative']!=results['2']['comparison']['determinant_negative']:
        raise ValueError('stride sign disagreement')
    stride_difference=float(np.linalg.norm(np.array(results['1']['transfer'])-np.array(results['2']['transfer'])))/max(1.,float(np.linalg.norm(results['1']['transfer'])))
    return dict(macros=n,step=step,inputs=registered,reference_results=results,stride_transfer_difference=stride_difference,
        continuum_load_is_not_native_load=True,production_qualified=False,critical_point_convergence_established=False,
        independent_review='PENDING')


def main():
    p=argparse.ArgumentParser();p.add_argument('--revision',required=True);p.add_argument('--macros',type=int,required=True)
    p.add_argument('--steps',type=int,nargs='+',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    guard(a.revision)
    if a.steps not in ([6],[7,9],[6,7,9]) or (a.steps!=[6,7,9] and a.macros!=4):raise ValueError('registered smoke/rehearsal/full subsets')
    registered={s:inputs(a.macros,s) for s in a.steps}
    if sys.flags.optimize or any(os.environ.get(k)!=v for k,v in THREAD_ENVIRONMENT.items()):raise ValueError('single thread and assertions')
    output=Path(a.output).resolve()
    if output.is_relative_to(ROOT) or output.exists():raise ValueError('fresh external directory')
    output.mkdir();results=[]
    for step in a.steps:
        r=evaluate(a.macros,step,registered[step])
        if inputs(a.macros,step)!=registered[step]:raise ValueError('inputs changed')
        results.append(r)
    guard(a.revision)
    for r in results:publish(output/f"step-{r['step']:02d}.json",dict(schema='GE_BEAM3_SAVED_CONTINUUM_LATERAL_V1',revision=a.revision,result=r))
    print(dict(stage='continuum-mesh-complete',macros=a.macros,steps=a.steps),flush=True)


if __name__=='__main__':main()
