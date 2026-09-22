"""Registered Q4 saved-state attribution: assembly/actions, no equilibrium solve."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time
import zipfile
import b3_e4_f03_area_feasibility as common

ROOT=Path(__file__).resolve().parents[1]
PARENT=ROOT/'.qualification/b3-ge-e4-pl/f03-joint-refinement-v1'
MIDDLE=(8,16,16,8)
FAMILIES=('P1','hybrid','enriched')
CASES={f:('Q4',16,32,32,16) for f in FAMILIES}
PARENT_FILES={
 'registration.json':'42a9fcddee56232921edcaf7f7108e6093196003cd3c18f6de78a944c8263558',
 'adjudication.json':'aa7848374fbe2664037794c129e918251bc9e67f6519537fea123790bdbef471',
 'q4_middle/solved_state.npz':'0034bd8809b27859b962e478378fdcc397274847dad0c78134307357a631161c',
 'q4_fine/solved_state.npz':'06b9be5dc7048394b2375bf0e5de93b11790acd5c681ca63ea87f9cf3215aa1f'}
PHYSICAL_SOURCES=('_b3_e4_f03_area_hybrid.py','_b3_e4_f03_area_line.py',
 '_b3_e4_f03_area_port.py','_b3_e4_f03_independent_beam.py',
 '_b3_e4_f03_independent_line.py','_b3_e4_f03_independent_shell.py',
 '_b3_e4_f03_kkt_scaling.py')
SOURCES=('b3_e4_f03_variational_attribution.py','_b3_e4_f03_variational_attribution.py',
 '_b3_e4_f03_attribution_evidence.py','b3_e4_f03_area_feasibility.py',*PHYSICAL_SOURCES)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def prerequisites():
    for name,digest in PARENT_FILES.items():
        if sha(PARENT/name)!=digest:
            raise ValueError('saved-state parent evidence changed')
    prior=read(PARENT/'registration.json')['identity']
    if prior['dependencies']!=common._versions():
        raise ValueError('physical dependency identities changed')
    for name in PHYSICAL_SOURCES:
        if sha(ROOT/'scripts'/name)!=prior['sources']['scripts/'+name]:
            raise ValueError('physical operator changed since saved-state execution')

def parent_states(family):
    import numpy as np
    with np.load(PARENT/'q4_middle/solved_state.npz',allow_pickle=False) as mid, \
         np.load(PARENT/'q4_fine/solved_state.npz',allow_pickle=False) as fine:
        return mid[family+'_q'].copy(),fine[family+'_q'].copy(),fine[family+'_lambda'].copy()

def bind_parent(actions,family):
    import numpy as np
    for key,value in zip(('q_middle','q_fine','lambda_fine'),parent_states(family)):
        if not np.array_equal(actions[key],value):
            raise ValueError('action archive altered an owned parent state')

def bind_attribution(metrics,verified):
    if not verified['attribution'] or not set(verified['attribution']).issubset(metrics):
        raise ValueError('incomplete independent attribution inventory')
    for key,value in verified['attribution'].items():
        equal=(isinstance(metrics[key],(int,float)) and math.isclose(
               metrics[key],value,rel_tol=1e-11,abs_tol=1e-12)
               if isinstance(value,(int,float)) else metrics[key]==value)
        if not equal:
            raise ValueError(f'attribution differs from saved matrix actions: {key}')

def observable_event(directory,name,spec,capture_state):
    if capture_state is not False:
        raise ValueError('this route captures actions, not a new equilibrium')
    return {'phase':'observables','case':name,'sha256':sha(directory/'observables.json'),
            'actions_sha256':sha(directory/'actions.npz'),
            'child_started_sha256':sha(directory/'child_started.json')}

def child(root,name):
    manifest=common._registered(root)
    prerequisites()
    if any(os.environ.get(k)!='1' for k in common.THREADS):
        raise ValueError('child thread environment mismatch')
    if name not in CASES or name not in manifest['cases']:
        raise ValueError('unregistered attribution child case')
    common._json_new(root/name/'child_started.json',{'case':name,
        'registration_sha256':common._registration_hash(root),'pid':os.getpid(),
        'started_unix_seconds':time.time()})
    import numpy as np
    from threadpoolctl import threadpool_info
    import _b3_e4_f03_variational_attribution as implementation
    import _b3_e4_f03_attribution_evidence as evidence
    pools=threadpool_info()
    if not pools or any(p['num_threads']!=1 for p in pools):
        raise ValueError('child numerical pools must be single-threaded')
    print(json.dumps({'phase':'identity','case':name,'identity':manifest['identity'],
        'registration_sha256':common._registration_hash(root),'threadpools':pools}),flush=True)
    metrics,actions=implementation.attribute_saved_states(*MIDDLE,name,*parent_states(name))
    bind_parent(actions,name)
    with (root/name/'actions.npz').open('xb') as stream:
        np.savez_compressed(stream,**evidence.pack_actions(actions,middle_mesh=MIDDLE,family=name))
    reopened=evidence.unpack_actions(root/name/'actions.npz',middle_mesh=MIDDLE,family=name)
    verified=evidence.verify_actions(reopened,middle_mesh=MIDDLE,family=name)
    bind_attribution(metrics,verified)
    common._json_new(root/name/'observables.json',{'attribution':metrics,'verified':verified,
        'equilibrium_solves':0,'schur_solves':0,'scope':common.SCOPE})
    print(json.dumps(observable_event(root/name,name,manifest['cases'][name],False)),flush=True)

def verify_case(root,name,manifest):
    import _b3_e4_f03_attribution_evidence as evidence
    directory=root/name
    receipt=read(directory/'supervision.json')
    digest=common._registration_hash(root)
    if receipt['registration_sha256']!=digest:
        raise ValueError('supervision registration mismatch')
    if receipt['reason']!='completed' or receipt['exit_code']!=0 or receipt['failure'] is not None:
        return {'status':'FAILED_EXECUTION','supervision':receipt}
    event=observable_event(directory,name,manifest['cases'][name],False)
    started=read(directory/'child_started.json')
    if (set(started)!={'case','registration_sha256','pid','started_unix_seconds'} or
            started['case']!=name or started['registration_sha256']!=digest or
            type(started['pid']) is not int or started['pid']<=0 or
            not isinstance(started['started_unix_seconds'],(int,float)) or
            not math.isfinite(started['started_unix_seconds'])):
        raise ValueError('child start authority mismatch')
    events=[json.loads(line) for line in (directory/'stdout.jsonl').read_text().splitlines()]
    if (receipt['phases']!=['identity','observables'] or
            receipt['observables_sha256']!=event['sha256'] or
            not 0<=receipt['elapsed_seconds']<=common.MAX_SECONDS or
            not 0<=receipt['sampled_peak_rss_bytes']<=common.MAX_RSS_BYTES or
            len(events)!=2 or not all(isinstance(e,dict) for e in events) or
            events[0].get('identity')!=manifest['identity'] or
            events[0].get('phase')!='identity' or events[0].get('case')!=name or
            events[0].get('registration_sha256')!=digest or
            not events[0].get('threadpools') or
            any(p.get('num_threads')!=1 for p in events[0]['threadpools']) or events[1]!=event):
        raise ValueError('raw identity, artifact or resource receipt mismatch')
    actions=evidence.unpack_actions(directory/'actions.npz',middle_mesh=MIDDLE,family=name)
    bind_parent(actions,name)
    verified=evidence.verify_actions(actions,middle_mesh=MIDDLE,family=name)
    data=read(directory/'observables.json')
    if (data['verified']!=verified or data['equilibrium_solves']!=0 or
            data['schur_solves']!=0 or data['scope']!=common.SCOPE):
        raise ValueError('saved independent verification or work contract mismatch')
    bind_attribution(data['attribution'],verified)
    values=verified['checks']
    if set(values)!=set(evidence.LIMITS) or any(not math.isfinite(v) or v<0 for v in values.values()):
        raise ValueError('invalid numerical check inventory')
    passed=all(values[k]<=limit for k,limit in evidence.LIMITS.items())
    return {'status':'PASSED_ATTRIBUTION_DIAGNOSTIC' if passed else 'FAILED_NUMERICAL_SCREEN',
            'checks':values,'attribution':verified['attribution']}

def adjudicate(root):
    manifest=common._registered(root)
    prerequisites()
    if any(not (root/name/'supervision.json').is_file() for name in CASES):
        raise ValueError('complete supervisor inventory required before adjudication')
    decisions={}
    for name in CASES:
        try:
            decisions[name]=verify_case(root,name,manifest)
        except (OSError,ValueError,KeyError,TypeError,IndexError,AttributeError,
                EOFError,zipfile.BadZipFile) as exc:
            decisions[name]={'status':'FAILED_EVIDENCE','reason':f'{type(exc).__name__}: {exc}'}
    status=next((candidate for candidate in ('FAILED_EVIDENCE','FAILED_EXECUTION','FAILED_NUMERICAL_SCREEN')
        if any(row['status']==candidate for row in decisions.values())),'PASSED_ATTRIBUTION_DIAGNOSTIC')
    common._json_new(root/'adjudication.json',{'registration_sha256':common._registration_hash(root),
        'identity':manifest['identity'],'status':status,'cases':decisions,'scope':common.SCOPE})
    print(json.dumps({'status':status,'cases':decisions},sort_keys=True))
    return status=='PASSED_ATTRIBUTION_DIAGNOSTIC'

def configure():
    import _b3_e4_f03_attribution_evidence as evidence
    common.CASES=CASES
    common.RUNNER=Path(__file__).resolve()
    common.SOURCES=tuple(ROOT/'scripts'/name for name in SOURCES)+(
        ROOT/'docs/agent_plans/B3_GE_E4_PL_G0_F03_VARIATIONAL_ATTRIBUTION_PROTOCOL.md',)
    common.KIND='experimental-classical-saved-state-variational-attribution-v1'
    common.SCOPE='Q4 saved-state energy/work attribution only; no continuum error estimate, native qualification or G0B closure'
    common.PHYSICAL_MODEL={'parent_hashes':PARENT_FILES,'middle_mesh':list(MIDDLE),
        'fine_mesh':[2*n for n in MIDDLE],'families':list(FAMILIES),'halfwidth_m':.05,
        'load':'smooth','equilibrium_solves':0,'schur_solves':0,
        'launch_cutoff_seconds':1200,'preserved_result':'UNRESOLVED_JOINT_REFINEMENT'}
    common.CAPTURE_STATE=False
    common.PARITY_REFERENCE={}
    common.LIMITS=dict(evidence.LIMITS)
    common.child=child
    common._observable_event=observable_event
    common.adjudicate=adjudicate

def run_once(root):
    common.register(root)
    start=time.monotonic(); completed=[]
    try:
        for name in CASES:
            if time.monotonic()-start>1200:
                raise TimeoutError('launch cutoff reached; remaining evidence incomplete')
            ok=common.execute(root,name)
            completed.append({'case':name,'execution_completed':ok})
            if not ok:
                receipt=read(root/name/'supervision.json')
                if receipt.get('reason')=='supervisor_failure' and (receipt.get('failure') or '').startswith(
                        ('KeyboardInterrupt:','SystemExit:','GeneratorExit:')):
                    raise KeyboardInterrupt('preserved supervised cancellation')
        return adjudicate(root)
    finally:
        common._json_new(root/'orchestration.json',{'registration_sha256':common._registration_hash(root),
            'cases':completed,'inventory_complete':len(completed)==len(CASES),
            'elapsed_seconds':time.monotonic()-start,
            'supervisor_thread_caps':{k:os.environ.get(k) for k in common.THREADS}})

if __name__=='__main__':
    if any(os.environ.get(k)!='1' for k in common.THREADS):
        raise ValueError('all supervisor and child thread caps must equal one')
    configure(); prerequisites()
    if '--run-all' in sys.argv:
        parser=argparse.ArgumentParser(description=__doc__)
        parser.add_argument('--run-all',action='store_true')
        parser.add_argument('--root',required=True,type=Path)
        args=parser.parse_args()
        raise SystemExit(0 if run_once(args.root.resolve()) else 1)
    raise SystemExit(common.main())
