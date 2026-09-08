"""One native prefix, capture, or independent factor audit per bounded worker."""
import argparse
from dataclasses import fields
from hashlib import sha256
import os
from pathlib import Path
import sys
from docs.reference_cases import ge_beam3_fine_onset_protocol as p
from docs.reference_cases.ge_beam3_fibre_arch_probe import guard,ROOT
from docs.reference_cases.ge_beam3_retained_prestress_wave import write,publish
from docs.reference_cases.e4_pl_s3_v2_bounded_process import THREAD_ENVIRONMENT

def run(path,digest,output):
    raw=p.read(path)
    if sha256(raw).hexdigest()!=digest:raise ValueError('request hash')
    value=p.strict_bytes(raw);p.authority();previous=p.request(value);guard(value['revision'])
    if sys.flags.optimize or any(os.environ.get(k)!=v for k,v in THREAD_ENVIRONMENT.items()):raise ValueError('assertions/one numerical thread')
    output=Path(output).resolve()
    if output.exists() or output.is_relative_to(ROOT):raise ValueError('fresh external worker directory')
    output.mkdir();sys.path.insert(0,str(ROOT/'src'))
    from anysolver import _ge_beam3_retained_translation_control as control
    from anysolver import _ge_beam3_retained_translation_modal as modal
    from anysolver._ge_beam3_p5_seeded.core import canonical
    from docs.reference_cases import ge_beam3_refined_controlled_case as case
    n=value['macros'];stage=value['stage'];programme=case.program(n,value['drop'])
    checkpoint=packet=science=None
    print(dict(stage='fine-onset-initialized',macros=n,worker=stage),flush=True)
    if stage<=4:
        kw={} if previous is None else dict(checkpoint=p.read(previous['checkpoint']['path']),expected_sha256=previous['checkpoint']['sha256'])
        result=control.solve(case.model(n),programme,stop_after=stage,progress=lambda r:print(r,flush=True),**kw)
        write(output/'checkpoint-diagnostic.json',result.checkpoint)
        write(output/'disposition.json',dict(status=result.status,completed=result.completed_targets,failure=result.failure))
        if result.status!=('completed' if stage==4 else 'paused') or result.completed_targets!=stage:
            raise RuntimeError('native prefix did not complete: '+str(result.failure))
        loaded=p.strict_bytes(result.checkpoint);row=loaded['records'][-1]
        if max(*row['metrics'],row['correction'])>1e-11:raise ValueError('fully equilibrated native prefix required')
        write(output/'checkpoint.json',result.checkpoint);checkpoint=p.bind(output/'checkpoint.json')
    elif stage==5:
        checkpoint=previous['checkpoint'];m=case.model(n)
        made,check=modal.prepare(m,programme,p.read(checkpoint['path']),case.masses(m),expected_sha256=checkpoint['sha256'])
        check();encoded=canonical(made);check();write(output/'packet.json',encoded);packet=p.bind(output/'packet.json')
    else:
        from anysolver._native_reference_modal import _owned
        from docs.reference_cases.ge_beam3_refined_factor_partition import partition
        from docs.reference_cases.ge_beam3_decimal_inertia_audit import audit
        from docs.reference_cases.ge_beam3_fibre_arch_comparison import geometry_diagnostics
        checkpoint=previous['checkpoint'];packet=previous['packet'];data=p.bound(packet);capsule=p.bound(checkpoint)
        if set(data)!={f.name for f in fields(modal.TranslationPencil)}:raise ValueError('exact physical factor schema')
        if (data['policy']!=modal.POLICY or data['history_unchanged'] is not True or data['control_constraint_in_physical_stiffness'] is not False
                or data['buckling_factor_authorized'] is not False or data['finite_velocity_dynamics_authorized'] is not False
                or data['model_sha256']!=capsule['model_sha256']):raise ValueError('physical factor claims')
        values=dict(data)
        for k in ('left','right','geometric','kinetic','stiffness','mass','net_residual'):values[k]=_owned(data[k])
        for k in ('free_dofs','algebraic_dofs','compliance_errors'):values[k]=tuple(data[k])
        values['internal_layout']=tuple((i,tuple(slots)) for i,slots in data['internal_layout'])
        made=modal.TranslationPencil(**values);encoded=canonical(made)
        if encoded!=p.read(packet['path']):raise ValueError('canonical factor roundtrip')
        def check():
            if canonical(made)!=encoded:raise ValueError('immutable physical factor data')
        families=partition(made,6*(2*n+1),check);audits={};counts={}
        for name,f in families.items():
            print(dict(stage='independent-zero-inertia',macros=n,family=name),flush=True)
            rows=[audit(f['left'].tolist(),f['right'].tolist(),f['geometric'].tolist(),f['kinetic'].tolist(),f['free'],f['algebraic'],(0.,),digits=d) for d in (80,100)]
            if rows[0]['rows'][0]['negative']!=rows[1]['rows'][0]['negative']:raise ValueError('precision disagreement')
            audits[name]=rows;counts[name]=rows[0]['rows'][0]['negative'];check()
        geometry=[geometry_diagnostics(row['mechanical']) for row in capsule['records']]
        if any(max(g.values())>1e-11 for g in geometry):raise ValueError('registered planar reflection lost')
        row=capsule['records'][-1]
        if max(*row['metrics'],row['correction'],abs(row['control_value']-value['drop']))>1e-11 or row['parameter']!=made.parameter:
            raise ValueError('controlled equilibrium binding')
        publish(output/'science.json',dict(schema='GE_BEAM3_FINE_ONSET_POINT_V1',revision=value['revision'],macros=n,index=value['index'],
            drop=value['drop'],load=made.parameter,negative_counts=counts,families=audits,geometry=geometry,
            checkpoint_sha256=checkpoint['sha256'],packet_sha256=packet['sha256'],exact_factor_decoupling=True,
            critical_point_agreement_established=False,same_branch_uniqueness_proved=False,production_qualified=False,independent_review='PENDING'))
        science=p.bind(output/'science.json')
    guard(value['revision']);p.authority();p.request(value)
    if p.read(path)!=raw:raise ValueError('request changed')
    publish(output/'ready.json',dict(schema='GE_BEAM3_FINE_ONSET_READY_V1',revision=value['revision'],macros=n,index=value['index'],drop=value['drop'],stage=stage,
        request_sha256=digest,checkpoint=checkpoint,packet=packet,science=science,production_qualified=False))
    print(dict(stage='fine-onset-complete',macros=n,worker=stage),flush=True)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--request',required=True);parser.add_argument('--sha256',required=True);parser.add_argument('--output',required=True)
    a=parser.parse_args();run(a.request,a.sha256,a.output)
if __name__=='__main__':main()
