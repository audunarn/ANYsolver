"""One bounded rehearsal or authorized deterministic cycle; never retry."""
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
from hashlib import sha256
from pathlib import Path
from threading import Event
import sys,time,traceback
from docs.reference_cases import ge_beam3_fine_onset_protocol as p
from docs.reference_cases.ge_beam3_fibre_arch_probe import guard,ROOT
from docs.reference_cases.ge_beam3_retained_prestress_wave import supervise,write,publish
MODULE='docs.reference_cases.ge_beam3_fine_onset_worker'

def prior_authority(phase,prior,revision):
    if phase not in ('rehearsal','formal-a','formal-b'):raise ValueError('registered phase')
    if phase=='rehearsal':
        if prior is not None:raise ValueError('rehearsal has no predecessor')
        return None
    if prior is None:raise ValueError('accepted predecessor required')
    value=p.bound(p.bind(prior))
    if (set(value)!={'schema','phase','revision','wave','aggregate','transcript','eligible','predecessor'}
            or value['schema']!='GE_BEAM3_FINE_ONSET_ACCEPTANCE_V1' or value['phase']!=('rehearsal' if phase=='formal-a' else 'formal-a')
            or value['revision']!=revision or value['eligible'] is not True):raise ValueError('accepted phase identity')
    wave=p.bound(value['wave']);aggregate=p.bound(value['aggregate']);transcript=p.bound(value['transcript'])
    if (wave['revision']!=revision or wave['phase']!=value['phase'] or wave['success'] is not True or wave['all_futures_terminal'] is not True
            or not 0<wave['elapsed']<=1800 or aggregate['engineering_pass'] is not True or aggregate['revision']!=revision
            or aggregate['production_qualified'] is not False or set(transcript)!={'20','24'}):raise ValueError('predecessor evidence/limits')
    for receipt in wave['receipts'].values():p.receipt(receipt)
    if len(wave['receipts'])!=37:raise ValueError('all predecessor workers required')
    # Bind every original checkpoint chain, not just the terminal enum.
    for n in (20,24):
        points=transcript[str(n)]['points']
        if len(points)!=3:raise ValueError('three predecessor points required')
        rows=[]
        for i,point in enumerate(points):
            r=p.bound(p.bound(point['completion'])['request'])
            ready=p.completion(point['completion'],revision,n,i,r['drop'],r['prior'],6)
            rows.append(p.science(p.bound(ready['science']),revision,n,i))
        if p.finish(rows,n,p.authority())!=aggregate['results'][0 if n==20 else 1]:raise ValueError('predecessor complete science')
    if value['phase']=='formal-a':
        p.bound(value['predecessor']);prior_authority('formal-a',value['predecessor']['path'],revision)
    return value

def mesh(n,root,revision,deadline,stop,receipts):
    root.mkdir(exist_ok=False);rows=[];outputs=[];points=[];auth=p.authority()
    try:
        for index in range(3):
            drop,_,_=p.search(rows,auth['points'][str(n)]);dest=root/f'point-{index}';dest.mkdir()
            write(dest/'prior.json',dict(revision=revision,macros=n,rows=rows,outputs=outputs));prior=p.bind(dest/'prior.json');previous=None
            for stage in range(1,7):
                guard(revision);job=dest/f'stage-{stage}';job.mkdir()
                request=dict(schema=p.SCHEMA,revision=revision,macros=n,index=index,drop=drop,prior=prior,stage=stage,previous=previous)
                p.request(request);write(job/'request.json',request);binding=p.bind(job/'request.json')
                r=supervise([sys.executable,'-B','-m',MODULE,'--request',str(job/'request.json'),'--sha256',binding['sha256'],
                    '--output',str(job/'output')],job,deadline,stop)
                receipts[f'n{n}/point-{index}/stage-{stage}']=r
                print(dict(macros=n,index=index,drop=drop,stage=stage,**r),flush=True)
                if not r['success']:raise RuntimeError('native/audit worker failed; no retry')
                write(job/'completion.json',dict(request=binding,ready=p.bind(job/'output/ready.json'),receipt=p.bind(job/'process.json')))
                previous=p.bind(job/'completion.json');ready=p.completion(previous,revision,n,index,drop,prior,stage)
            science=p.bound(ready['science']);publish(dest/'result.json',science)
            rows.append(p.science(science,revision,n,index));outputs.append(p.bind(dest/'result.json'))
            points.append(dict(completion=previous,result=outputs[-1]))
            print(dict(stage='actual-point-complete',macros=n,index=index,drop=drop,load=science['load'],counts=science['negative_counts']),flush=True)
        result=p.finish(rows,n,auth);publish(root/'result.json',result)
        return dict(points=points,result=p.bind(root/'result.json'))
    except BaseException:stop.set();raise

def run(revision,output,phase,prior):
    guard(revision);p.authority();before=prior_authority(phase,prior,revision)
    predecessor=None if prior is None else p.bind(prior)
    output=Path(output).resolve()
    if output.exists() or output.is_relative_to(ROOT):raise ValueError('fresh external wave root')
    output.mkdir();start=time.monotonic();deadline=start+1800;stop=Event();receipts={};results={};errors=[]
    unit=output/'unit';unit.mkdir();code="import sys;sys.path[:0]=['src','.'];import pytest;raise SystemExit(pytest.main(sys.argv[1:]))"
    receipts['unit']=supervise([sys.executable,'-B','-c',code,'-q','-p','no:cacheprovider','tests/test_ge_beam3_fine_onset_protocol.py',
        '--basetemp',str(unit/'pytest')],unit,deadline,stop)
    print(dict(stage='protocol-unit',**receipts['unit']),flush=True)
    if receipts['unit']['success']:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures={pool.submit(mesh,n,output/f'n{n}',revision,deadline,stop,receipts):n for n in (20,24)}
            for future in as_completed(futures):
                try:results[futures[future]]=future.result()
                except BaseException:errors.append(traceback.format_exc());stop.set()
    else:errors.append('authority unit failed; no mechanics launched')
    guard(revision);p.authority()
    if time.monotonic()>=deadline:errors.append('wave deadline')
    success=not errors and set(results)=={20,24}
    write(output/'wave.json',dict(revision=revision,phase=phase,coordinator_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
        elapsed=time.monotonic()-start,success=success,all_futures_terminal=True,errors=errors,receipts=receipts))
    if not success:raise RuntimeError('bounded search blocked; preserve partials; no retry')
    write(output/'completion-transcript.json',results)
    science=[p.bound(results[n]['result']) for n in (20,24)];passed=all(r['engineering_pass'] for r in science)
    aggregate=dict(schema='GE_BEAM3_FINE_ONSET_AGGREGATE_V1',revision=revision,authority=p.authority(),results=science,engineering_pass=passed,
        disposition='PRIVATE_FINE_ONSET_ENGINEERING_PASS' if passed else 'NO_GO_FINE_CONTROLLED_ONSET_COMPARISON',
        production_qualified=False,independent_review='PENDING')
    encoded=p.canonical(aggregate)
    if phase=='formal-b' and encoded!=p.read(before['aggregate']['path']):
        write(output/'disagreement-diagnostic.json',encoded)
        raise RuntimeError('formal replicas disagree; no canonical aggregate or acceptance')
    publish(output/'aggregate.json',aggregate)
    publish(output/'acceptance.json',dict(schema='GE_BEAM3_FINE_ONSET_ACCEPTANCE_V1',phase=phase,revision=revision,
        wave=p.bind(output/'wave.json'),aggregate=p.bind(output/'aggregate.json'),transcript=p.bind(output/'completion-transcript.json'),
        eligible=passed,predecessor=predecessor))
    print(dict(stage='wave-complete',phase=phase,engineering_pass=passed,results=[dict(macros=r['macros'],errors=r['endpoint_errors']) for r in science]),flush=True)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--revision',required=True);parser.add_argument('--output',required=True)
    parser.add_argument('--phase',required=True,choices=('rehearsal','formal-a','formal-b'));parser.add_argument('--prior')
    a=parser.parse_args();run(a.revision,a.output,a.phase,a.prior)
if __name__=='__main__':main()
