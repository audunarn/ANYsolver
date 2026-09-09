"""Research-only zero-inertia samples of already accepted arc equilibria."""
import argparse
from dataclasses import fields
from fractions import Fraction
from hashlib import sha256
from math import isfinite
from pathlib import Path
from docs.reference_cases.ge_beam3_retained_prestress_protocol import canonical,strict_bytes,read,bind,bound,digest
from docs.reference_cases.ge_beam3_retained_prestress_wave import write,publish
from docs.reference_cases.ge_beam3_retained_arch_loaded import ARCHIVE,MANIFEST_SHA
from docs.reference_cases.ge_beam3_arc_spatial_refinement import start
from docs.reference_cases.ge_beam3_fibre_arch_probe import guard

MESHES=(4,8,12)
STEPS=(6,7,9)
BASE=Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-spatial-refinement-c714d9e-20260908')
BASE_SHA='edf2e82feabd7b7ef98a35e94bacca713db16e2ce311684617c3019451d76b2c'
BASE_REV='c714d9e61de740b38da095deba3122366dbb8089'


def historical(n,step,*,endpoint=False):
    if type(n) is not int or n not in MESHES or type(step) is not int or step not in ((1,12) if endpoint else STEPS):
        raise ValueError('registered saved intermediate extent')
    raw=read(ARCHIVE/'archive-manifest.json')
    if sha256(raw).hexdigest()!=MANIFEST_SHA:raise ValueError('archive manifest authority')
    manifest=strict_bytes(raw);name=f'cycle-a/n{n}/step-{step:02d}/science/state-{step:02d}.json'
    data=read(ARCHIVE/name)
    if manifest[name]!=[len(data),sha256(data).hexdigest().upper()]:raise ValueError('registered checkpoint changed')
    value=strict_bytes(data)
    if value['completed_steps']!=step:raise ValueError('checkpoint step mismatch')
    return data,dict(sha256=sha256(data).hexdigest(),bytes=len(data),relative_path=name)


def observation(n,step,raw,counts):
    state=strict_bytes(raw)['records'][-1];m=state['mechanical']
    drop=float(Fraction(.1)-Fraction(m['positions'][n][1])-Fraction(m['position_low'][n][1]))
    return dict(macros=n,step=step,drop=drop,load=state['parameter'],checkpoint_sha256=sha256(raw).hexdigest(),counts=counts)


def endpoint(n,step):
    raw,identity=historical(n,step,endpoint=True)
    manifest_raw=read(BASE/'archive-manifest.json')
    if sha256(manifest_raw).hexdigest()!=BASE_SHA:raise ValueError('endpoint archive identity')
    manifest=strict_bytes(manifest_raw);name=f'refinement/cycle-a/n{n}-step{step:02d}/inspect/output/science.json'
    data=read(BASE/name)
    if manifest[name]!=[len(data),sha256(data).hexdigest().upper()]:raise ValueError('endpoint science hash')
    v=strict_bytes(data)
    if (v['revision']!=BASE_REV or v['macros']!=n or v['step']!=step or v['checkpoint_sha256']!=identity['sha256']
        or v['production_qualified'] is not False or v['full_spatial_qualified'] is not False
        or v['exact_factor_decoupling'] is not True):raise ValueError('endpoint claims')
    counts={}
    for name in ('planar','lateral'):
        family=v['families'][name];audits=family['audits']
        if [a['digits'] for a in audits]!=[80,100]:raise ValueError('endpoint precisions')
        c=family['negative_physical_modes']
        if any(a['rows'][0]['shift']!=0. or a['rows'][0]['negative']!=c for a in audits):raise ValueError('endpoint counts')
        counts[name]=c
    return observation(n,step,raw,counts)


def capture(revision,n,step,output):
    raw,identity=historical(n,step);output=start(revision,output)
    import numpy as np
    from anysolver import _ge_beam3_retained_arc_modal as modal
    from anysolver._ge_beam3_p5_seeded.core import canonical as native_canonical
    from docs.reference_cases import ge_beam3_retained_arch_case as case
    print(dict(stage='intermediate-native-capture',macros=n,step=step),flush=True)
    model=case.model(n);masses={eid:np.diag([1.,1.,1.,3e-5,1e-5,2e-5]) for eid in model.mesh.elements}
    packet,check=modal.prepare(model,case.program(n),raw,masses,expected_sha256=identity['sha256'])
    check();data=native_canonical(packet);check()
    if packet.completed_steps!=step or packet.checkpoint_sha256!=identity['sha256']:raise ValueError('capture identity')
    guard(revision);historical(n,step);write(output/'packet.json',data)
    publish(output/'ready.json',dict(schema='GE_BEAM3_INTERMEDIATE_ARC_CAPTURE_V1',revision=revision,macros=n,step=step,
        checkpoint=identity,packet=bind(output/'packet.json'),native_arc_replay=True,production_qualified=False))
    print(dict(stage='intermediate-capture-complete',macros=n,step=step),flush=True)


def assignment(value):
    if type(value) is not dict or set(value)!={'schema','revision','ready','receipt'} or value['schema']!='GE_BEAM3_INTERMEDIATE_INERTIA_ASSIGNMENT_V1':
        raise ValueError('exact intermediate assignment')
    ready=bound(value['ready']);receipt=bound(value['receipt'])
    if (type(ready) is not dict or set(ready)!={'schema','revision','macros','step','checkpoint','packet','native_arc_replay','production_qualified'}
        or ready['schema']!='GE_BEAM3_INTERMEDIATE_ARC_CAPTURE_V1' or ready['revision']!=value['revision']
        or ready['native_arc_replay'] is not True or ready['production_qualified'] is not False):raise ValueError('capture authority')
    if (receipt['success'] is not True or receipt['reason']!='COMPLETED' or receipt['exit_code']!=0 or receipt['after'][1]!=0
        or receipt['cleanup_error'] is not None or receipt['error'] is not None or not 0.<=receipt['elapsed']<=600
        or not 0<=receipt['before'][2]<=24*1024**3):raise ValueError('capture process bounds')
    _,identity=historical(ready['macros'],ready['step'])
    if ready['checkpoint']!=identity:raise ValueError('checkpoint authority')
    data=bound(ready['packet'])
    if data['checkpoint_sha256']!=identity['sha256']:raise ValueError('packet authority')
    return ready,data


def inspect(request,digest,output):
    raw=read(request)
    if sha256(raw).hexdigest()!=digest:raise ValueError('assignment external hash')
    value=strict_bytes(raw);ready,data=assignment(value);output=start(value['revision'],output)
    from anysolver._ge_beam3_retained_arc_modal import ArcPencil,POLICY
    from anysolver._native_reference_modal import _owned
    from anysolver._ge_beam3_p5_seeded.core import canonical as native_canonical
    from docs.reference_cases.ge_beam3_retained_arc_spectrum import planar_partition
    from docs.reference_cases.ge_beam3_decimal_inertia_audit import audit
    if set(data)!={f.name for f in fields(ArcPencil)}:raise ValueError('exact packet schema')
    if (data['policy']!=POLICY or data['production_qualified'] is not False or data['history_unchanged'] is not True
        or data['arc_constraint_in_physical_stiffness'] is not False or data['buckling_factor_authorized'] is not False
        or data['finite_velocity_dynamics_authorized'] is not False or data['completed_steps']!=ready['step']):raise ValueError('packet claims')
    parameters=dict(data)
    for name in ('left','right','geometric','kinetic','stiffness','mass','net_residual'):parameters[name]=_owned(data[name])
    for name in ('free_dofs','algebraic_dofs','compliance_errors'):parameters[name]=tuple(data[name])
    parameters['internal_layout']=tuple((i,tuple(slots)) for i,slots in data['internal_layout'])
    packet=ArcPencil(**parameters);packet_bytes=native_canonical(packet)
    if packet_bytes!=canonical(data):raise ValueError('packet serialization')
    def check():
        if native_canonical(packet)!=packet_bytes:raise ValueError('packet changed')
    families=planar_partition(packet,6*(2*ready['macros']+1),check);results={};counts={}
    for name,f in families.items():
        print(dict(stage='zero-shift-audit',family=name,macros=ready['macros'],step=ready['step']),flush=True)
        audits=[audit(f['left'].tolist(),f['right'].tolist(),f['geometric'].tolist(),f['kinetic'].tolist(),
            f['free'],f['algebraic'],(0.,),digits=d) for d in (80,100)]
        c=[a['rows'][0]['negative'] for a in audits]
        if c[0]!=c[1]:raise ValueError('independent precision disagreement')
        counts[name]=c[0];results[name]=audits;check()
    state,_=historical(ready['macros'],ready['step']);guard(value['revision']);assignment(value)
    if read(request)!=raw:raise ValueError('assignment changed')
    publish(output/'science.json',dict(schema='GE_BEAM3_SAVED_ARC_ZERO_INERTIA_V1',revision=value['revision'],
        observation=observation(ready['macros'],ready['step'],state,counts),families=results,
        packet_sha256=ready['packet']['sha256'],exact_factor_decoupling=True,production_qualified=False,
        full_spatial_qualified=False,independent_review='PENDING'))
    print(dict(stage='intermediate-inspection-complete',macros=ready['macros'],step=ready['step']),flush=True)


def intervals(rows):
    if type(rows) is not list or len(rows)!=5 or [r['step'] for r in rows]!=[1,6,7,9,12]:raise ValueError('ordered complete samples')
    n=rows[0]['macros']
    if type(n) is not int or n not in MESHES or any(r['macros']!=n for r in rows):raise ValueError('single registered mesh')
    for r in rows:
        if set(r)!={'macros','step','drop','load','checkpoint_sha256','counts'} or type(r['step']) is not int or type(r['macros']) is not int:
            raise ValueError('exact observation schema')
        if any(type(r[k]) is not float or not isfinite(r[k]) for k in ('drop','load')):raise ValueError('finite equilibrium observations')
        digest(r['checkpoint_sha256'])
        if set(r['counts'])!={'planar','lateral'} or any(type(c) is not int or c<0 for c in r['counts'].values()):raise ValueError('exact inertia counts')
    changes=[]
    for left,right in zip(rows,rows[1:]):
        for name in ('planar','lateral'):
            if left['counts'][name]!=right['counts'][name]:changes.append(dict(family=name,left=left,right=right))
    return dict(macros=n,samples=rows,changed_count_intervals=changes,root_uniqueness_established=False,
        matched_displacement_convergence=False,production_qualified=False)


def main():
    p=argparse.ArgumentParser();m=p.add_mutually_exclusive_group(required=True);m.add_argument('--capture',action='store_true');m.add_argument('--inspect')
    p.add_argument('--revision');p.add_argument('--macros',type=int);p.add_argument('--step',type=int);p.add_argument('--expected-sha256');p.add_argument('--output',required=True)
    a=p.parse_args()
    if a.capture:capture(a.revision,a.macros,a.step,a.output)
    else:inspect(a.inspect,a.expected_sha256,a.output)


if __name__=='__main__':main()
