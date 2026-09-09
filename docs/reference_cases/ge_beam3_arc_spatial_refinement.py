"""Research-only isolated arc capture and hash-bound spectral inspection."""
import argparse
from dataclasses import fields
from hashlib import sha256
import os
from pathlib import Path
import sys
from docs.reference_cases.ge_beam3_retained_prestress_protocol import canonical,strict_bytes,read,bind,bound
from docs.reference_cases.ge_beam3_retained_prestress_wave import write,publish
from docs.reference_cases.ge_beam3_retained_arch_loaded import ARCHIVE,MANIFEST_SHA
from docs.reference_cases.ge_beam3_fibre_arch_probe import guard,ROOT
from docs.reference_cases.e4_pl_s3_v2_bounded_process import THREAD_ENVIRONMENT


def historical(macros,step):
    if type(macros) is not int or macros not in (2,4,8,12) or type(step) is not int or step not in (1,12):
        raise ValueError('registered saved-state refinement extent')
    raw=read(ARCHIVE/'archive-manifest.json')
    if sha256(raw).hexdigest()!=MANIFEST_SHA:raise ValueError('archive manifest authority')
    manifest=strict_bytes(raw)
    name=f'cycle-a/n{macros}/step-{step:02d}/science/state-{step:02d}.json'
    data=read(ARCHIVE/name)
    if manifest[name]!=[len(data),sha256(data).hexdigest().upper()]:raise ValueError('registered checkpoint changed')
    value=strict_bytes(data)
    if value['completed_steps']!=step:raise ValueError('checkpoint step mismatch')
    return data,dict(sha256=sha256(data).hexdigest(),bytes=len(data),relative_path=name)


def start(revision,output):
    guard(revision)
    if sys.flags.optimize or any(os.environ.get(k)!=v for k,v in THREAD_ENVIRONMENT.items()):
        raise ValueError('assertions and single numerical thread required')
    output=Path(output).resolve()
    if output.is_relative_to(ROOT) or output.exists():raise ValueError('fresh external directory required')
    output.mkdir()
    sys.path.insert(0,str(ROOT/'src'))
    return output


def capture(revision,macros,step,output):
    raw,binding=historical(macros,step);output=start(revision,output)
    import numpy as np
    from anysolver import _ge_beam3_retained_arc_modal as modal
    from anysolver._ge_beam3_p5_seeded.core import canonical as native_canonical
    from docs.reference_cases import ge_beam3_retained_arch_case as case
    print(dict(stage='native-arc-capture',macros=macros,step=step),flush=True)
    m=case.model(macros);p=case.program(macros)
    masses={eid:np.diag([1.,1.,1.,3e-5,1e-5,2e-5]) for eid in m.mesh.elements}
    packet,check=modal.prepare(m,p,raw,masses,expected_sha256=binding['sha256'])
    check();packet_bytes=native_canonical(packet);check()
    if packet.completed_steps!=step or packet.checkpoint_sha256!=binding['sha256']:
        raise ValueError('captured arc identity mismatch')
    guard(revision);historical(macros,step)
    write(output/'packet.json',packet_bytes)
    publish(output/'ready.json',dict(schema='GE_BEAM3_ARC_FACTOR_CAPTURE_V1',revision=revision,macros=macros,step=step,
        checkpoint=binding,packet=bind(output/'packet.json'),native_arc_replay=True,production_qualified=False))
    print(dict(stage='native-arc-capture-complete',macros=macros,step=step),flush=True)


def assignment(value):
    if type(value) is not dict or set(value)!={'schema','revision','ready','receipt'} or value['schema']!='GE_BEAM3_SPATIAL_INSPECTION_ASSIGNMENT_V1':
        raise ValueError('exact spectral assignment schema')
    ready=bound(value['ready']);receipt=bound(value['receipt'])
    if (type(ready) is not dict or set(ready)!={'schema','revision','macros','step','checkpoint','packet','native_arc_replay','production_qualified'}
        or ready['schema']!='GE_BEAM3_ARC_FACTOR_CAPTURE_V1' or ready['revision']!=value['revision']
        or ready['native_arc_replay'] is not True or ready['production_qualified'] is not False):
        raise ValueError('exact native capture authority')
    if (receipt['success'] is not True or receipt['reason']!='COMPLETED' or receipt['exit_code']!=0
        or receipt['after'][1]!=0 or receipt['cleanup_error'] is not None or receipt['error'] is not None
        or receipt['elapsed']>600 or receipt['before'][2]>24*1024**3):
        raise ValueError('capture process did not finish within bounds')
    _,registered=historical(ready['macros'],ready['step'])
    if ready['checkpoint']!=registered:raise ValueError('wrong historical checkpoint')
    packet=bound(ready['packet'])
    if packet['checkpoint_sha256']!=registered['sha256']:raise ValueError('packet checkpoint identity')
    return ready,packet


def inspect(request,expected_sha256,output):
    raw=read(request)
    if sha256(raw).hexdigest()!=expected_sha256:raise ValueError('assignment external hash')
    value=strict_bytes(raw);ready,data=assignment(value);output=start(value['revision'],output)
    import numpy as np
    from anysolver._ge_beam3_retained_arc_modal import ArcPencil,POLICY
    from anysolver._native_reference_modal import _owned
    from anysolver._ge_beam3_p5_seeded.core import canonical as native_canonical
    from anysolver._native_paired_factor_chain_modes import solve_paired_factor_chain_modes as paired
    from docs.reference_cases.ge_beam3_retained_arc_spectrum import planar_partition
    from docs.reference_cases.ge_beam3_decimal_inertia_audit import audit
    if set(data)!={f.name for f in fields(ArcPencil)}:raise ValueError('exact captured factor schema')
    if (data['policy']!=POLICY or data['production_qualified'] is not False or data['history_unchanged'] is not True
        or data['arc_constraint_in_physical_stiffness'] is not False or data['buckling_factor_authorized'] is not False
        or data['finite_velocity_dynamics_authorized'] is not False):raise ValueError('unsupported captured factor claim')
    parameters=dict(data)
    for name in ('left','right','geometric','kinetic','stiffness','mass','net_residual'):parameters[name]=_owned(data[name])
    for name in ('free_dofs','algebraic_dofs','compliance_errors'):parameters[name]=tuple(data[name])
    parameters['internal_layout']=tuple((i,tuple(slots)) for i,slots in data['internal_layout'])
    packet=ArcPencil(**parameters)
    if native_canonical(packet)!=canonical(data):raise ValueError('factor deserialization changed bytes')
    packet_bytes=native_canonical(packet)
    def check():
        if native_canonical(packet)!=packet_bytes:raise ValueError('captured factors changed')
    groups=planar_partition(packet,6*(2*ready['macros']+1),check);results={}
    for name,f in groups.items():
        print(dict(stage='signed-family',family=name,macros=ready['macros'],step=ready['step']),flush=True)
        modes=paired(f['left'],f['right'],f['geometric'],f['kinetic'],f['free'],f['algebraic'],
                     bounds=(-100.,1e6),num_modes=6)
        shifts=(0.,*map(float,modes.numerical_brackets.ravel()))
        audits=[audit(f['left'].tolist(),f['right'].tolist(),f['geometric'].tolist(),f['kinetic'].tolist(),
                      f['free'],f['algebraic'],shifts,digits=digits) for digits in (80,100)]
        counts=[[r['negative'] for r in a['rows']] for a in audits]
        if counts[0]!=counts[1] or counts[0][1:]!=[i for j in range(6) for i in (j,j+1)]:
            raise ValueError('independent full-family root count disagreement')
        results[name]=dict(modes=modes,audits=audits,negative_physical_modes=counts[0][0])
        check()
    # Exact original-factor decoupling makes the union complete. No rounded
    # global matrix or truncated Ritz subspace is substituted for that proof.
    union=sorted(float(v) for r in results.values() for v in r['modes'].eigenvalues)[:6]
    guard(value['revision']);assignment(value)
    if read(request)!=raw:raise ValueError('assignment changed during inspection')
    result=dict(schema='GE_BEAM3_SPATIAL_REFINEMENT_SPECTRA_V1',revision=value['revision'],macros=ready['macros'],step=ready['step'],
        checkpoint_sha256=ready['checkpoint']['sha256'],packet_sha256=ready['packet']['sha256'],families=results,
        lowest_full_frequency_squared=union,negative_physical_modes=sum(r['negative_physical_modes'] for r in results.values()),
        exact_factor_decoupling=True,full_spatial_qualified=False,production_qualified=False,independent_review='PENDING')
    publish(output/'science.json',native_canonical(result))
    print(dict(stage='spatial-inspection-complete',macros=ready['macros'],step=ready['step']),flush=True)


def main():
    p=argparse.ArgumentParser();mode=p.add_mutually_exclusive_group(required=True);mode.add_argument('--capture',action='store_true');mode.add_argument('--inspect')
    p.add_argument('--revision');p.add_argument('--macros',type=int);p.add_argument('--step',type=int);p.add_argument('--expected-sha256');p.add_argument('--output',required=True)
    a=p.parse_args()
    if a.capture:capture(a.revision,a.macros,a.step,a.output)
    else:inspect(a.inspect,a.expected_sha256,a.output)


if __name__=='__main__':main()
