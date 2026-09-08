"""Bounded native cold-start point and separately authenticated factor audit."""
import argparse
from dataclasses import fields
from hashlib import sha256
import os
from pathlib import Path
import sys
from docs.reference_cases import ge_beam3_controlled_onset_protocol as protocol
from docs.reference_cases.ge_beam3_retained_prestress_wave import write,publish
from docs.reference_cases.ge_beam3_fibre_arch_probe import guard,ROOT
from docs.reference_cases.e4_pl_s3_v2_bounded_process import THREAD_ENVIRONMENT


def request(path,digest):
    raw=protocol.read(path)
    if sha256(raw).hexdigest()!=digest:raise ValueError('external point assignment hash')
    value=protocol.strict_bytes(raw);protocol.assignment(value);return raw,value


def start(revision,path):
    guard(revision)
    if sys.flags.optimize or any(os.environ.get(k)!=v for k,v in THREAD_ENVIRONMENT.items()):raise ValueError('one thread and assertions')
    root=Path(path).resolve()
    if root.exists() or root.is_relative_to(ROOT):raise ValueError('fresh external point directory')
    root.mkdir();sys.path.insert(0,str(ROOT/'src'));return root


def point(path,digest,output):
    assignment_bytes,v=request(path,digest);output=start(v['revision'],output)
    import numpy as np
    from anysolver import _ge_beam3_retained_translation_control as control
    from anysolver import _ge_beam3_retained_translation_modal as modal
    from anysolver._ge_beam3_p5_seeded.core import canonical
    from docs.reference_cases import ge_beam3_retained_arch_case as case
    n=v['macros'];programme=control.Program(protocol.targets(v['drop']),n+1,(0.,-1.,0.),case.program(n).nodal_forces)
    print(dict(stage='native-controlled-cold-start',macros=n,index=v['index'],targets=programme.targets),flush=True)
    result=control.solve(case.model(n),programme,progress=lambda r:print(r,flush=True))
    write(output/'checkpoint-diagnostic.json',result.checkpoint)
    write(output/'disposition.json',dict(status=result.status,completed=result.completed_targets,failure=result.failure))
    if result.status!='completed' or result.completed_targets!=len(programme.targets):raise RuntimeError('native controlled point failed: '+str(result.failure))
    raw=result.checkpoint;loaded=protocol.strict_bytes(raw);row=loaded['records'][-1];mechanical=row['mechanical']
    if max(*row['metrics'],row['correction'])>1e-11 or abs(row['control_value']-v['drop'])>1e-11:raise ValueError('fully equilibrated target required')
    error=None
    if v['index']==0:
        old,drop,_=protocol.anchor(n)
        if drop!=v['drop']:raise ValueError('anchor target identity')
        errors=[abs(row['parameter']-old['parameter'])/max(1.,abs(old['parameter']))]
        for key in ('positions','position_low','nodal_frames','cell_rotations','resultants'):
            a=np.array(mechanical[key]);b=np.array(old['mechanical'][key])
            if a.shape!=b.shape:raise ValueError('anchor mechanical layout')
            errors.append(float(np.linalg.norm(a-b))/max(1.,float(np.linalg.norm(b))))
        error=max(errors)
        if error>1e-11:raise ValueError('cold controlled point differs from accepted arc branch')
    print(dict(stage='controlled-factor-capture',macros=n,index=v['index']),flush=True)
    model=case.model(n);masses={eid:np.diag([1.,1.,1.,3e-5,1e-5,2e-5]) for eid in model.mesh.elements}
    packet,check=modal.prepare(model,programme,raw,masses,expected_sha256=sha256(raw).hexdigest())
    check();packet_bytes=canonical(packet);check()
    if packet.displacement_target!=v['drop'] or packet.parameter!=row['parameter']:raise ValueError('captured controlled point identity')
    guard(v['revision']);protocol.assignment(v)
    if protocol.read(path)!=assignment_bytes:raise ValueError('assignment changed')
    write(output/'checkpoint.json',raw);write(output/'packet.json',packet_bytes)
    publish(output/'ready.json',dict(schema='GE_BEAM3_CONTROLLED_ONSET_POINT_READY_V1',revision=v['revision'],macros=n,index=v['index'],
        drop=v['drop'],load=packet.parameter,anchor_error=error,assignment_sha256=digest,
        checkpoint=protocol.bind(output/'checkpoint.json'),packet=protocol.bind(output/'packet.json'),production_qualified=False))
    print(dict(stage='controlled-point-complete',macros=n,index=v['index'],anchor_error=error),flush=True)


def inspection_assignment(v):
    if type(v) is not dict or set(v)!={'schema','assignment','ready','receipt'} or v['schema']!='GE_BEAM3_CONTROLLED_ONSET_INSPECTION_V1':raise ValueError('exact inspection assignment')
    source=protocol.bound(v['assignment']);protocol.assignment(source)
    ready=protocol.bound(v['ready']);receipt=protocol.bound(v['receipt'])
    if set(ready)!={'schema','revision','macros','index','drop','load','anchor_error','assignment_sha256','checkpoint','packet','production_qualified'}:
        raise ValueError('exact native ready schema')
    if ready['schema']!='GE_BEAM3_CONTROLLED_ONSET_POINT_READY_V1' or ready['production_qualified'] is not False or ready['assignment_sha256']!=v['assignment']['sha256']:
        raise ValueError('ready identity')
    if any(ready[k]!=source[k] for k in ('revision','macros','index','drop')):raise ValueError('point identity mismatch')
    if (receipt['success'] is not True or receipt['exit_code']!=0 or receipt['reason']!='COMPLETED' or receipt['after'][1]!=0
        or receipt['error'] is not None or receipt['cleanup_error'] is not None or not 0<=receipt['elapsed']<=600
        or not 0<=receipt['before'][2]<=24*1024**3):raise ValueError('producer process did not finish within bounds')
    checkpoint=protocol.bound(ready['checkpoint']);data=protocol.bound(ready['packet'])
    if data['checkpoint_sha256']!=ready['checkpoint']['sha256'] or checkpoint['completed_targets']!=len(protocol.targets(source['drop'])):
        raise ValueError('complete own checkpoint required')
    return source,ready,data


def inspect(path,digest,output):
    raw=protocol.read(path)
    if sha256(raw).hexdigest()!=digest:raise ValueError('external inspection hash')
    v=protocol.strict_bytes(raw);source,ready,data=inspection_assignment(v);output=start(source['revision'],output)
    from anysolver._ge_beam3_retained_translation_modal import TranslationPencil,POLICY
    from anysolver._native_reference_modal import _owned
    from anysolver._ge_beam3_p5_seeded.core import canonical
    from docs.reference_cases.ge_beam3_retained_arc_spectrum import planar_partition
    from docs.reference_cases.ge_beam3_decimal_inertia_audit import audit
    if set(data)!={f.name for f in fields(TranslationPencil)}:raise ValueError('exact translation factor schema')
    if (data['policy']!=POLICY or data['production_qualified'] is not False or data['history_unchanged'] is not True
        or data['control_constraint_in_physical_stiffness'] is not False or data['buckling_factor_authorized'] is not False
        or data['finite_velocity_dynamics_authorized'] is not False or data['displacement_target']!=source['drop']
        or data['parameter']!=ready['load'] or data['completed_targets']!=len(protocol.targets(source['drop']))):raise ValueError('factor claims')
    values=dict(data)
    for k in ('left','right','geometric','kinetic','stiffness','mass','net_residual'):values[k]=_owned(data[k])
    for k in ('free_dofs','algebraic_dofs','compliance_errors'):values[k]=tuple(data[k])
    values['internal_layout']=tuple((i,tuple(slots)) for i,slots in data['internal_layout'])
    packet=TranslationPencil(**values);packet_bytes=canonical(packet)
    if packet_bytes!=protocol.canonical(data):raise ValueError('factor roundtrip')
    def check():
        if canonical(packet)!=packet_bytes:raise ValueError('factor data changed')
    families=planar_partition(packet,6*(2*source['macros']+1),check);results={};counts={}
    for name,f in families.items():
        print(dict(stage='controlled-zero-inertia',family=name,index=source['index']),flush=True)
        a=[audit(f['left'].tolist(),f['right'].tolist(),f['geometric'].tolist(),f['kinetic'].tolist(),
            f['free'],f['algebraic'],(0.,),digits=d) for d in (80,100)]
        c=[x['rows'][0]['negative'] for x in a]
        if c[0]!=c[1]:raise ValueError('precision count disagreement')
        results[name]=a;counts[name]=c[0];check()
    row=dict(index=source['index'],drop=source['drop'],load=ready['load'],planar_negative=counts['planar'],
        lateral_negative=counts['lateral'],anchor_error=ready['anchor_error'],checkpoint_sha256=ready['checkpoint']['sha256'],packet_sha256=ready['packet']['sha256'])
    prior=protocol.assignment(source);_,drop,_=protocol.anchor(source['macros']);protocol.search([*prior['rows'],row],drop)
    guard(source['revision']);inspection_assignment(v)
    if protocol.read(path)!=raw:raise ValueError('inspection assignment changed')
    publish(output/'science.json',dict(schema='GE_BEAM3_CONTROLLED_ONSET_POINT_V1',revision=source['revision'],macros=source['macros'],
        row=row,families=results,exact_factor_decoupling=True,production_qualified=False,independent_review='PENDING'))
    print(dict(stage='controlled-point-inspected',row=row),flush=True)


def main():
    p=argparse.ArgumentParser();m=p.add_mutually_exclusive_group(required=True);m.add_argument('--point');m.add_argument('--inspect')
    p.add_argument('--expected-sha256',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    if a.point:point(a.point,a.expected_sha256,a.output)
    else:inspect(a.inspect,a.expected_sha256,a.output)


if __name__=='__main__':main()
