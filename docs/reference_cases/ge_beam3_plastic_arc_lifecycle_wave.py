"""Two isolated lifecycle chains, rehearsal then two authorized exact repeats."""
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
from hashlib import sha256
from pathlib import Path
from threading import Event
import sys,time,traceback
from docs.reference_cases import ge_beam3_plastic_arc_lifecycle_protocol as p
from docs.reference_cases.ge_beam3_fibre_arch_probe import guard,ROOT
from docs.reference_cases.ge_beam3_retained_prestress_wave import supervise,write,publish

MODULE='docs.reference_cases.ge_beam3_plastic_arc_lifecycle_worker'

def saved_value(path,live):
    raw=p.read(path)
    if p.canonical(live)!=raw:raise ValueError('live/stored receipt disagreement')
    return p.strict_bytes(raw)

def saved_receipt(path,live):
    value=saved_value(path,live);p.receipt(value)
    return value

def chain(n,root,revision,deadline,stop,receipts):
    root.mkdir();files={};reports={};requests={}
    try:
        for mode in p.MODES:
            guard(revision);job=root/mode;job.mkdir()
            data=dict(schema='GE_BEAM3_PLASTIC_ARC_LIFECYCLE_REQUEST_V1',revision=revision,macros=n,mode=mode,
                inputs={key:files[key] for key in sorted(p.INPUTS[mode])})
            p.request(data);write(job/'request.json',data);request=p.bind(job/'request.json')
            result=supervise([sys.executable,'-B','-m',MODULE,'--request',request['path'],'--sha256',request['sha256'],
                '--output',str(job/'output')],job,deadline,stop)
            receipts[f'n{n}/{mode}']=result
            print(dict(macros=n,mode=mode,**result),flush=True)
            if not result['success']:raise RuntimeError('lifecycle worker failed: '+mode+'; no retry')
            saved_receipt(job/'process.json',result);p.bound(request)
            reports[mode]=p.bind(job/'output/report.json');requests[mode]=request
            if mode in ('full','prefix'):files[mode]=p.bind(job/'output/checkpoint.json')
            elif mode=='capture':files['capture']=p.bind(job/'output/capture.json')
            elif mode=='check':files['material']=p.bind(job/'output/material.json')
            p.validate_report(p.bound(reports[mode]),revision,n,mode,files['full']['sha256'],files.get('prefix',{}).get('sha256'))
        return dict(**files,reports=reports,requests=requests)
    except BaseException:stop.set();raise

def run(revision,phase,output,prior):
    guard(revision);authority=p.authority();before=p.prior(phase,prior,revision)
    predecessor=None if prior is None else p.bind(prior)
    root=Path(output).resolve()
    if root.exists() or root.is_relative_to(ROOT):raise ValueError('fresh external wave root')
    root.mkdir(parents=True,exist_ok=False);start=time.monotonic();deadline=start+1800.;stop=Event()
    receipts={};cases={};errors=[]
    unit=root/'unit';unit.mkdir()
    code="import sys;sys.path[:0]=['src','.'];import pytest;raise SystemExit(pytest.main(sys.argv[1:]))"
    receipts['unit']=supervise([sys.executable,'-B','-c',code,'-q','-p','no:cacheprovider',
        'tests/test_ge_beam3_plastic_arc_lifecycle_protocol.py','--basetemp',str(unit/'pytest')],unit,deadline,stop)
    if receipts['unit']['success']:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures={pool.submit(chain,n,root/f'n{n}',revision,deadline,stop,receipts):n for n in (1,2)}
            for future in as_completed(futures):
                try:cases[str(futures[future])]=future.result()
                except BaseException:errors.append(traceback.format_exc());stop.set()
    else:errors.append('lifecycle authority unit failed; no mechanics launched')
    try:guard(revision);p.authority()
    except Exception:errors.append(traceback.format_exc())
    elapsed=time.monotonic()-start
    if elapsed>=1800.:errors.append('wave deadline')
    wave=dict(revision=revision,phase=phase,receipts=receipts,cases=cases,elapsed=elapsed,
        success=not errors and set(cases)=={'1','2'},errors=errors,all_children_terminal=True)
    write(root/'wave.json',wave)
    wave=saved_value(root/'wave.json',wave)
    if not wave['success']:raise RuntimeError('lifecycle wave blocked; preserve partials; no retry')
    rows=[]
    for n in (1,2):
        case=cases[str(n)]
        rows.append(dict(macros=n,full_sha256=case['full']['sha256'],prefix_sha256=case['prefix']['sha256'],
            capture_sha256=case['capture']['sha256'],material=p.bound(case['material']),reports=[p.bound(case['reports'][mode]) for mode in p.MODES]))
    aggregate=dict(schema='GE_BEAM3_PLASTIC_ARC_LIFECYCLE_AGGREGATE_V1',revision=revision,authority=authority,cases=rows,
        terminal='PRIVATE_ACTIVE_PLASTIC_ARC_LIFECYCLE_PASS',independent_review='PENDING',production_qualified=False)
    p.validate_wave(wave,aggregate,revision)
    if phase=='formal-b' and p.canonical(aggregate)!=p.read(before['aggregate']['path']):
        write(root/'disagreement-diagnostic.json',aggregate)
        raise RuntimeError('formal replicas disagree; no aggregate or acceptance')
    publish(root/'aggregate.json',aggregate)
    publish(root/'acceptance.json',dict(schema='GE_BEAM3_PLASTIC_ARC_LIFECYCLE_ACCEPTANCE_V1',revision=revision,phase=phase,
        wave=p.bind(root/'wave.json'),aggregate=p.bind(root/'aggregate.json'),predecessor=predecessor))
    print(dict(stage='lifecycle-wave-complete',phase=phase,workers=len(receipts),seconds=elapsed,terminal=aggregate['terminal']),flush=True)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--revision',required=True);parser.add_argument('--phase',required=True,choices=('rehearsal','formal-a','formal-b'))
    parser.add_argument('--output',required=True);parser.add_argument('--prior')
    a=parser.parse_args();run(a.revision,a.phase,a.output,a.prior)

if __name__=='__main__':main()
