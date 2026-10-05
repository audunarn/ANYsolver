"""Registered joint refinement: four new equilibria sets, two saved-state sets.

Each set contains P1/hybrid/enriched. The independently validated analytic
norm changes diagnostics only. Earlier FE32/64 HOLD decisions are immutable.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import time
import zipfile

import b3_e4_f03_area_feasibility as common
import b3_e4_f03_endpoint_comparison as previous
import _b3_e4_f03_joint_refinement_checks as checks

ROOT=Path(__file__).resolve().parents[1]
FAMILIES=checks.FAMILIES
LEVELS={'coarse':(4,8,8,4),'middle':(8,16,16,8),'fine':(16,32,32,16)}
CASES={f'{prefix}_{level}':(topology,*counts)
       for prefix,topology in (('q4','Q4'),('cst_cb','CST-CB'))
       for level,counts in LEVELS.items()}
PARENT=ROOT/'.qualification/b3-ge-e4-pl/f03-endpoint-comparison-v1'
NORM=ROOT/'.qualification/b3-ge-e4-pl/f03-analytical-norm-v1'
PARENT_REGISTRATION='56548b5a4d44c2ae09235d2557f2aa36ed3232d31446865caf172e03ce0380bb'
PARENT_STATES={
    'q4_middle':'0034bd8809b27859b962e478378fdcc397274847dad0c78134307357a631161c',
    'cst_cb_middle':'e436d920c8a960ab8fd123df8939dd550aa640d6980e3637d20892a0d141cc38'}
NORM_REGISTRATION='4c4682a1648966d10d7b02317f918be849dd6a3d3375c8d767c3710ca0e68e30'
NORM_ADJUDICATION='b524f55f3cff2ba40973851ed125569198ded0b2e5daa3486099e435fab4df18'
PARENT_ADJUDICATION='956539fbdc34eedb1c6e7de609f2f386f706a853d67f5a5b157f60de426b3fd6'
SOURCE_NAMES=tuple(dict.fromkeys((
    'b3_e4_f03_joint_refinement.py','_b3_e4_f03_joint_refinement_checks.py',
    '_b3_e4_f03_trace_dual_exact.py','_b3_e4_f03_joint_refinement_observables.py',
    *previous.SOURCE_NAMES)))
sha=previous.sha
read=previous.read
observable_event=previous.observable_event


def prerequisites():
    if (sha(PARENT/'registration.json')!=PARENT_REGISTRATION or
            sha(PARENT/'adjudication.json')!=PARENT_ADJUDICATION or
            sha(NORM/'registration.json')!=NORM_REGISTRATION or
            sha(NORM/'adjudication.json')!=NORM_ADJUDICATION):
        raise ValueError('parent or validated norm evidence changed')
    norm_sources=read(NORM/'registration.json')['identity']['sources']
    key='scripts/_b3_e4_f03_trace_dual_exact.py'
    if norm_sources[key]!=sha(ROOT/key):
        raise ValueError('analytic norm implementation differs from validated source')
    for name,digest in PARENT_STATES.items():
        if sha(parent_path(name))!=digest:
            raise ValueError('parent snapshot changed')
        directory=parent_path(name).parent
        if sha(directory/'observables.json')!=read(directory/'supervision.json')['observables_sha256']:
            raise ValueError('parent observable receipt mismatch')
    structural=('_b3_e4_f03_area_hybrid.py','_b3_e4_f03_area_loaded.py',
        '_b3_e4_f03_area_line.py','_b3_e4_f03_area_port.py',
        '_b3_e4_f03_independent_beam.py','_b3_e4_f03_independent_line.py',
        '_b3_e4_f03_independent_shell.py','_b3_e4_f03_kkt_scaling.py')
    prior=read(PARENT/'registration.json')['identity']
    if prior['dependencies']!=common._versions():
        raise ValueError('saved-state dependency identities changed')
    for filename in structural:
        if sha(ROOT/'scripts'/filename)!=prior['sources']['scripts/'+filename]:
            raise ValueError('saved-state physical operator source changed')


def parent_path(name):
    return PARENT/name.replace('_middle','_baseline')/'solved_state.npz'


def parent_states(name):
    import numpy as np
    if name not in PARENT_STATES:
        return None
    with np.load(parent_path(name),allow_pickle=False) as data:
        return {key:data[key].copy() for key in data.files}


def parent_parity(name,states):
    import numpy as np
    parent=parent_states(name)
    if parent is None:
        return 0.
    if set(parent)!=set(states) or any(not np.array_equal(parent[k],states[k]) for k in parent):
        raise ValueError('saved equilibrium was altered')
    return 0.


def parent_observable_parity(name,data):
    """Unchanged physical metrics must reproduce saved-state reconstruction."""
    import numpy as np
    if name not in PARENT_STATES:
        return 0.
    prior=read(parent_path(name).parent/'observables.json')
    worst=0.
    for family in FAMILIES:
        for key,value in prior['families'][family].items():
            if key in ('stability','combined_dual_norm_N'):
                continue
            old=np.asarray(value,dtype=float); new=np.asarray(data['families'][family][key],dtype=float)
            if old.shape!=new.shape or not np.all(np.isfinite(new)):
                raise ValueError('parent physical observable layout mismatch')
            floor=(1e-15 if key.endswith('_m') or key.endswith('_scaled') or key=='balance_scaled'
                   else 1e-12 if key.endswith('_j') else 1e-5)
            worst=max(worst,float(np.max(np.abs(new-old)/(floor+1e-10*np.abs(old)))))
    return worst


def child(root,name):
    manifest=common._registered(root)
    prerequisites()
    if any(os.environ.get(key)!='1' for key in common.THREADS):
        raise ValueError('child thread environment mismatch')
    import numpy as np
    from threadpoolctl import threadpool_info
    import _b3_e4_f03_area_hybrid_loaded as loaded
    pools=threadpool_info()
    if not pools or any(p['num_threads']!=1 for p in pools):
        raise ValueError('child numerical pools must be single-threaded')
    print(json.dumps({'phase':'identity','case':name,'identity':common._identity(),
                      'registration_sha256':common._registration_hash(root),
                      'threadpools':pools}),flush=True)
    spec=manifest['cases'][name]
    from _b3_e4_f03_independent_shell import panel
    from _b3_e4_f03_joint_refinement_observables import fixed_bands,gap_metrics
    model=panel(spec['n_s'],spec['n_y'],spec['topology'])
    partial_files={}
    enriched_metrics={}
    def preserve(family,metrics,q,lam):
        metrics.update(gap_metrics(model,spec['n_beam'],spec['n_mortar'],q))
        metrics['fixed_bands']=fixed_bands(metrics['physical_line_coefficients'],metrics['endpoint_atoms'])
        enriched_metrics[family]=metrics
        common._json_new(root/name/(family+'_observables.json'),metrics)
        with (root/name/(family+'_state.npz')).open('xb') as stream:
            np.savez_compressed(stream,physical_q=q,physical_lambda=lam)
        for suffix in ('_observables.json','_state.npz'):
            partial_files[family+suffix]=sha(root/name/(family+suffix))
    def preserve_stability(family,schur,gram):
        filename=family+'_stability.npz'
        with (root/name/filename).open('xb') as stream:
            np.savez_compressed(stream,schur=schur,gram=gram)
        partial_files[filename]=sha(root/name/filename)
    data,states=loaded.solve_case(spec['n_s'],spec['n_y'],spec['n_beam'],
        spec['n_mortar'],spec['topology'],.05,family_sink=preserve,
        norm_source='analytic_h1',saved_states=parent_states(name),stability_sink=preserve_stability)
    data['families']=enriched_metrics
    data['family_artifact_hashes']=partial_files
    data['parent_state_parity_ratio']=parent_parity(name,states)
    data['parent_observable_parity_ratio']=parent_observable_parity(name,data)
    data['equilibrium_source']='saved_states' if name in PARENT_STATES else 'new_solve'
    common._json_new(root/name/'observables.json',data)
    with (root/name/'solved_state.npz').open('xb') as stream:
        np.savez_compressed(stream,**states)
    print(json.dumps(observable_event(root/name,name,spec,True)),flush=True)


def verify_case(root,name,spec,manifest):
    import numpy as np
    import _b3_e4_f03_area_hybrid_loaded as loaded
    directory=root/name
    digest=common._registration_hash(root)
    receipt=read(directory/'supervision.json')
    if receipt['registration_sha256']!=digest:
        raise ValueError('supervisor registration identity mismatch')
    if receipt['reason']!='completed' or receipt['exit_code']!=0 or receipt['failure'] is not None:
        return {'status':'FAILED_EXECUTION','supervision':receipt},None
    events=[json.loads(line) for line in (directory/'stdout.jsonl').read_text().splitlines()]
    expected=observable_event(directory,name,spec,True)
    if (receipt['phases']!=['identity','observables'] or
            receipt['observables_sha256']!=expected['sha256'] or
            not 0<=receipt['elapsed_seconds']<=common.MAX_SECONDS or
            not 0<=receipt['sampled_peak_rss_bytes']<=common.MAX_RSS_BYTES or
            len(events)!=2 or not all(isinstance(e,dict) for e in events) or
            events[0].get('phase')!='identity' or events[0].get('case')!=name or
            events[0].get('identity')!=manifest['identity'] or
            events[0].get('registration_sha256')!=digest or
            not events[0].get('threadpools') or
            any(p.get('num_threads')!=1 for p in events[0]['threadpools']) or
            events[1]!=expected):
        raise ValueError('raw source/state/resource receipt mismatch')
    data=read(directory/'observables.json')
    expected_source='saved_states' if name in PARENT_STATES else 'new_solve'
    if data['equilibrium_source']!=expected_source:
        raise ValueError('equilibrium reuse contract mismatch')
    with np.load(directory/'solved_state.npz',allow_pickle=False) as stored:
        parity=parent_parity(name,stored)
        expected_files={f+s for f in FAMILIES for s in ('_observables.json','_state.npz','_stability.npz')}
        if set(data['family_artifact_hashes'])!=expected_files:
            raise ValueError('incomplete partial artifact inventory')
        for filename,digest in data['family_artifact_hashes'].items():
            if sha(directory/filename)!=digest:
                raise ValueError('partial artifact hash mismatch')
        for family in FAMILIES:
            if read(directory/(family+'_observables.json'))!=data['families'][family]:
                raise ValueError('partial/final observables differ')
            with np.load(directory/(family+'_state.npz'),allow_pickle=False) as part:
                if (set(part.files)!={'physical_q','physical_lambda'} or
                        not np.array_equal(part['physical_q'],stored[family+'_q']) or
                        not np.array_equal(part['physical_lambda'],stored[family+'_lambda'])):
                    raise ValueError('partial/final states differ')
            from scipy import linalg
            from _b3_e4_f03_trace_dual_exact import dual_gram
            with np.load(directory/(family+'_stability.npz'),allow_pickle=False) as matrices:
                count=3*(spec['n_mortar']+(3 if family=='enriched' else 1))
                if set(matrices.files)!={'schur','gram'}:
                    raise ValueError('saved matrix inventory mismatch')
                s=checks.finite(matrices['schur'],(count,count),'saved Schur')
                g=checks.finite(matrices['gram'],(count,count),'saved Gram')
                if (np.linalg.norm(s-s.T)>1e-9*np.linalg.norm(s) or
                        np.linalg.norm(g-g.T)>1e-9*np.linalg.norm(g) or
                        not np.array_equal(g,np.kron(dual_gram(spec['n_mortar'],family),np.eye(3)))):
                    raise ValueError('saved matrices disagree with symmetry or norm contract')
                linalg.cholesky(g,lower=True)
                checks.bind_physical_multipliers(data['families'][family],family,
                    spec['n_mortar'],stored[family+'_lambda'],g)
                eig=linalg.eigvalsh(s,g)
                if not np.array_equal(eig,data['families'][family]['stability']['generalized_eigenvalues']):
                    raise ValueError('saved spectrum mismatch')
    if data['parent_state_parity_ratio']!=parity:
        raise ValueError('parent parity metric mismatch')
    if data['parent_observable_parity_ratio']!=parent_observable_parity(name,data):
        raise ValueError('parent observable parity metric mismatch')
    identities={family:loaded.analytic_norm_identity(spec['n_mortar'],family) for family in FAMILIES}
    metrics=checks.measurements(data,spec,identities)
    status=('PASSED_DIAGNOSTIC_CHECKS' if all(metrics[k]<=v for k,v in checks.LIMITS.items())
            else 'FAILED_NUMERICAL_SCREEN')
    return {'status':status,'measurements':metrics,'equilibrium_source':expected_source},data


def adjudicate(root):
    manifest=common._registered(root)
    prerequisites()
    if any(not (root/name/'supervision.json').is_file() for name in manifest['cases']):
        raise ValueError('complete supervisor inventory required before adjudication')
    decisions={}; observations={}
    for name,spec in manifest['cases'].items():
        try:
            decisions[name],data=verify_case(root,name,spec,manifest)
            if data is not None:
                observations[name]=data
        except (OSError,ValueError,KeyError,TypeError,IndexError,AttributeError,EOFError,
                zipfile.BadZipFile) as exc:
            decisions[name]={'status':'FAILED_EVIDENCE','reason':f'{type(exc).__name__}: {exc}'}
    passed=all(d['status']=='PASSED_DIAGNOSTIC_CHECKS' for d in decisions.values())
    report=checks.refinement_summary(observations) if passed else None
    status=(report['status'] if passed else next(status for status in
            ('FAILED_EVIDENCE','FAILED_EXECUTION','FAILED_NUMERICAL_SCREEN')
            if any(d['status']==status for d in decisions.values())))
    common._json_new(root/'adjudication.json',{'identity':manifest['identity'],
        'registration_sha256':common._registration_hash(root),
        'cases':decisions,'refinement':report,'status':status,'scope':common.SCOPE})
    print(json.dumps({'cases':decisions,'status':status},sort_keys=True))
    return status=='PASSED_BOUNDED_TREND_SCREEN'


def configure():
    common.CASES=CASES
    common.RUNNER=Path(__file__).resolve()
    common.SOURCES=tuple(ROOT/'scripts'/name for name in SOURCE_NAMES)+(
        ROOT/'docs/agent_plans/B3_GE_E4_PL_G0_F03_JOINT_REFINEMENT_PROTOCOL.md',)
    common.KIND='experimental-classical-joint-refinement-v1'
    common.SCOPE='three-level classical diagnostic; no production selection, native qualification, G0B or G1'
    common.PHYSICAL_MODEL={
        'halfwidth_m':.05,'load':'smooth','families':list(FAMILIES),
        'parent_registration_sha256':PARENT_REGISTRATION,'parent_state_hashes':PARENT_STATES,
        'parent_adjudication_sha256':PARENT_ADJUDICATION,
        'norm_registration_sha256':NORM_REGISTRATION,'norm_adjudication_sha256':NORM_ADJUDICATION,
        'norm_source':'analytic_h1','fresh_equilibrium_sets':4,'reused_equilibrium_sets':2,
        'launch_budget_seconds':2400,'physical_relative_floor_fraction':1e-3,
        'physical_comparisons':'signed componentwise, last-step 1% descriptive screen; all channels retained'}
    common.PARITY_REFERENCE={}
    common.CAPTURE_STATE=True
    common.LIMITS=checks.LIMITS
    common.child=child
    common._observable_event=observable_event
    common.adjudicate=adjudicate


def run_once(root):
    """Consume a fresh registration once; supervise serial children, never retry."""
    common.register(root)
    started=time.monotonic()
    completed=[]
    try:
        for name in CASES:
            if time.monotonic()-started>2400:
                raise TimeoutError('registered launch budget exhausted; remaining inventory incomplete')
            ok=common.execute(root,name)
            completed.append({'case':name,'execution_completed':ok})
            print(json.dumps(completed[-1]),flush=True)
            if not ok:
                receipt=read(root/name/'supervision.json')
                failure=receipt.get('failure') or ''
                if receipt.get('reason')=='supervisor_failure' and failure.startswith(
                        ('KeyboardInterrupt:','SystemExit:','GeneratorExit:')):
                    raise KeyboardInterrupt(f'preserved supervised cancellation: {failure}')
        return adjudicate(root)
    finally:
        common._json_new(root/'orchestration.json',{
            'registration_sha256':common._registration_hash(root),
            'elapsed_seconds':time.monotonic()-started,'cases':completed,
            'supervisor_thread_caps':{key:os.environ.get(key) for key in common.THREADS},
            'inventory_complete':len(completed)==len(CASES)})


if __name__=='__main__':
    configure()
    if any(os.environ.get(key)!='1' for key in common.THREADS):
        raise ValueError('all registered supervisor and child thread caps must equal one')
    prerequisites()
    if '--run-all' in sys.argv:
        import argparse
        parser=argparse.ArgumentParser(description=__doc__)
        parser.add_argument('--run-all',action='store_true')
        parser.add_argument('--root',required=True,type=Path)
        args=parser.parse_args()
        raise SystemExit(0 if run_once(args.root.resolve()) else 1)
    raise SystemExit(common.main())
