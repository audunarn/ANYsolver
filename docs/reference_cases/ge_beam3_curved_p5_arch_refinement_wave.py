"""One-use contained research arch refinement; never production qualification.

Frozen Git/lease checks precede numerical imports. Reuses unchanged exclusive
publication, strict parsing and Windows process containment from the prior P5
wave, but has its own authority, case, request claim and evidence identity.
"""

import argparse
import math
import os
from pathlib import Path
import re
import sys
import threading

from docs.reference_cases.ge_beam3_curved_p5_refinement_wave import (
    canonical,sha,load,publish,git,run_child,THREAD_ENVIRONMENT,RefinementError,
)


BASE = 'f6b42eabf6fae9be7b212224e1402ec546940b8f'
MODULE = 'docs.reference_cases.ge_beam3_curved_p5_arch_refinement_wave'
SCHEMA = 'GE_BEAM3_P5_ARCH_REFINE16_RESEARCH_V1'
MANAGER = Path('C:/Github/.resource-manager')
ALLOWED = {
    'docs/reference_cases/ge_beam3_curved_p5_arch_refinement_case.py',
    'docs/reference_cases/ge_beam3_curved_p5_arch_refinement_wave.py',
    'tests/test_ge_beam3_curved_p5_arch_refinement_wave.py',
    'docs/agent_plans/GE_BEAM3_CURVED_P5_ARCH_REFINE16_PLAN.md',
}
CASE = {'height':.1,'span':2.,'section_diagonal':[1000.,400.,400.,.02,.01,.02],
        'elements':16,'nodes':33,'fixed_nodes':[0,32],'crown_node':16,
        'order':8,'steps':8,'arc_step':.01,'reference_profile':'BVP9',
        'physical_residual_limit':1e-11,'accuracy_limit':.02,
        'reference_interpolation_limit':1e-6,'iterations_per_step':16,
        'mixed_evaluations_per_step':4096,'stations_per_step':256}
ERRORS = ('relative_load_error','recovery_energy_norm_error','physical_energy_relative_error')


def command(repo,commit,output):
    return f"& '{sys.executable}' -B -m {MODULE} --coordinate --commit {commit} --output '{Path(output)}'"


def authority(repo,commit):
    if not re.fullmatch('[0-9a-f]{40}',commit) or git(repo,'rev-parse','HEAD')!=commit:
        raise RefinementError('frozen arch commit mismatch')
    if git(repo,'status','--porcelain','--untracked-files=all'):
        raise RefinementError('dirty research inputs')
    if git(repo,'rev-parse','HEAD^')!=BASE:
        raise RefinementError('exact arch implementation parent required')
    if set(git(repo,'diff','--name-only',BASE,commit).splitlines())!=ALLOWED:
        raise RefinementError('unexpected arch research extent')
    return {'commit':commit,'tree':git(repo,'rev-parse','HEAD^{tree}'),
            'case_sha256':sha(canonical(CASE)),'python':str(Path(sys.executable).resolve()),
            'python_sha256':sha(Path(sys.executable).read_bytes())}


def lease(repo,commit,output,*,manager=MANAGER):
    owner = load(manager/'active-lock'/'owner.json',strict=False)
    request_id = owner.get('request_id')
    if not isinstance(request_id,str) or not re.fullmatch('[0-9a-f]{32}',request_id):
        raise RefinementError('valid active arch resource lease required')
    request_path = manager/'requests'/(request_id+'.json')
    request = load(request_path,strict=False)
    expected = command(repo,commit,output)
    if (request.get('request_id')!=request_id or request.get('command')!=expected or
            owner.get('command')!=expected or
            Path(request.get('repository','')).resolve()!=Path(repo).resolve() or
            Path(owner.get('repository','')).resolve()!=Path(repo).resolve()):
        raise RefinementError('exact arch command/repository lease mismatch')
    rows = [[v.strip() for v in line.split('|')[1:-1]]
            for line in (manager/'ledger.md').read_text(encoding='utf-8-sig').splitlines() if line.startswith('|')]
    states = [r[2] for r in rows if len(r)>2 and r[1]==request_id]
    if states!=['APPROVED']:
        raise RefinementError('one unconsumed administrator approval required')
    return request_id,sha(request_path.read_bytes())


def worker(repo,commit,output):
    frozen = authority(repo,commit)
    request_id,request_hash = lease(repo,commit,output)
    # Numerical imports must remain below both guards.
    from docs.reference_cases.ge_beam3_curved_p5_arch_refinement_case import records
    folder = output/'arch16'
    with (folder/'progress.jsonl').open('xb') as stream:
        def progress(phase,step=None):
            stream.write(canonical({'phase':phase,'step':step}));stream.flush()
        progress('INITIALIZATION')
        rows = records(count=16,steps=8,progress=progress,
            publish_raw=lambda i,raw:publish(folder/f'step-{i:02}.json',raw))
        if authority(repo,commit)!=frozen or lease(repo,commit,output)!=(request_id,request_hash):
            raise RefinementError('arch authority changed during computation')
        publish(folder/'complete.json',{'schema':SCHEMA,'authority':frozen,'request_id':request_id,
            'request_sha256':request_hash,'production_qualified':False,'records':rows})
        progress('COMPLETION')


def check_samples(full,row,*,count=256):
    """Recompute raw field metrics without importing numerical mechanics.

    This is integrity validation, not independent reconstruction of mechanics.
    A small rounding allowance covers different scalar/NumPy summation orders.
    """
    samples,reference = full['samples'],full['reference']
    assembly = full['trial']['assembly_trial']
    if set(samples)!={'parameters','measures','reference_resultants','coarser_reference_resultants',
                     'actual_resultants','actual_strains','physical_energy'}:
        raise RefinementError('raw sample schema mismatch')
    def finite(value):
        return type(value) in (int,float) and math.isfinite(value)
    for key in ('parameters','measures'):
        if len(samples[key])!=count or not all(finite(v) for v in samples[key]):
            raise RefinementError('raw sample vector mismatch')
    if any(abs(v)>1 for v in samples['parameters']) or any(v<=0 for v in samples['measures']):
        raise RefinementError('invalid station domain/measure')
    for key in ('reference_resultants','coarser_reference_resultants','actual_resultants','actual_strains'):
        if (len(samples[key])!=count or any(len(v)!=6 or not all(finite(x) for x in v) for v in samples[key])):
            raise RefinementError('raw six-component field mismatch')
    stations = [s['response'] for e in assembly['response']['elements'] for s in e['stations']]
    if (samples['actual_resultants']!=[s['resultants'] for s in stations] or
            samples['actual_strains']!=[s['strain'] for s in stations]):
        raise RefinementError('sample fields differ from station recovery')
    weights,actual,expected,coarse,strains = (samples[k] for k in
        ('measures','actual_resultants','reference_resultants','coarser_reference_resultants','actual_strains'))
    section = CASE['section_diagonal']
    def norm(a,b):
        return math.fsum(w*(x-y)**2/c for w,u,v in zip(weights,a,b) for x,y,c in zip(u,v,section))
    denominator = norm(expected,[[0.]*6 for _ in range(count)])
    if denominator<=0:
        raise RefinementError('positive reference norm required')
    energy = .5*math.fsum(w*x*y for w,u,v in zip(weights,actual,strains) for x,y in zip(u,v))
    potential = assembly['response']['potential']
    if not finite(reference['strain_energy']) or reference['strain_energy']<=0:
        raise RefinementError('positive reference energy required')
    def equal(a,b):
        return finite(a) and finite(b) and abs(a-b)<=1e-12*max(1.,abs(a),abs(b))
    checks = {'recovery_energy_norm_error':math.sqrt(norm(actual,expected)/denominator),
              'reference_interpolation_error':math.sqrt(norm(coarse,expected)/denominator),
              'physical_energy_relative_error':abs(energy/reference['strain_energy']-1),
              'stationary_work_error':abs(energy-potential)/max(1.,abs(energy),abs(potential))}
    if not equal(energy,samples['physical_energy']) or any(not equal(row[k],v) for k,v in checks.items()):
        raise RefinementError('raw recovery/energy metric mismatch')


def inspect_worker(folder,frozen,request_id,request_hash):
    packet = load(folder/'complete.json')
    if (set(packet)!={'schema','authority','request_id','request_sha256','production_qualified','records'} or
            packet['schema']!=SCHEMA or packet['authority']!=frozen or packet['request_id']!=request_id or
            packet['request_sha256']!=request_hash or packet['production_qualified'] is not False or
            len(packet['records'])!=8):
        raise RefinementError('arch complete identity/coverage mismatch')
    keys = {'step','crown_drop','load','reference_load','relative_load_error','current_load_slope',
            'minimum_free_eigenvalue','equilibrium_error','arc_error','iterations','mixed_evaluations',
            'recovery_energy_norm_error','physical_energy_relative_error','stationary_work_error',
            'reference_interpolation_error','global_balance_error','stations','raw'}
    for i,row in enumerate(packet['records']):
        if set(row)!=keys or type(row['step']) is not int or row['step']!=i:
            raise RefinementError('arch row schema/order mismatch')
        for key in keys-{'raw'}:
            if type(row[key]) not in (int,float) or not math.isfinite(row[key]):
                raise RefinementError('nonfinite or nonnumeric arch row')
        if (type(row['stations']) is not int or row['stations']!=256 or
                type(row['iterations']) is not int or not 0<=row['iterations']<=16 or
                type(row['mixed_evaluations']) is not int or not 0<=row['mixed_evaluations']<=4096):
            raise RefinementError('arch station/iteration coverage mismatch')
        for key in ('equilibrium_error','arc_error','stationary_work_error','global_balance_error'):
            if not 0<=row[key]<=1e-11:
                raise RefinementError('unresolved arch equilibrium/work check')
        if not 0<=row['reference_interpolation_error']<=1e-6 or any(row[k]<0 for k in ERRORS):
            raise RefinementError('invalid arch comparison metric')
        raw = row['raw']
        if set(raw)!={'name','bytes','sha256'} or raw['name']!=f'step-{i:02}.json':
            raise RefinementError('arch raw binding schema mismatch')
        payload = (folder/raw['name']).read_bytes()
        if len(payload)!=raw['bytes'] or sha(payload)!=raw['sha256']:
            raise RefinementError('arch raw hash mismatch')
        full = load(folder/raw['name'])
        if set(full)!={'trial','reference','samples','comparison'} or full['comparison']!={k:v for k,v in row.items() if k!='raw'}:
            raise RefinementError('arch summary differs from raw comparison')
        trial,reference,samples = full['trial']['assembly_trial'],full['reference'],full['samples']
        if (len(trial['positions'])!=33 or len(trial['response']['elements'])!=16 or
                len(samples['parameters'])!=256 or len(samples['measures'])!=256 or
                any(len(e['stations'])!=16 for e in trial['response']['elements'])):
            raise RefinementError('arch raw geometry/station inventory mismatch')
        forces = [[0.,0.,0.] for _ in range(33)];forces[16][1] = -row['load']
        if (trial['forces']!=forces or trial['residual_norm']!=row['equilibrium_error'] or
                full['trial']['parameter']!=row['load'] or full['trial']['arc_residual']!=row['arc_error'] or
                .1-trial['positions'][16][1]!=row['crown_drop'] or reference['load']!=row['reference_load'] or
                reference['displacement']!=row['crown_drop'] or reference['profile']!='BVP9'):
            raise RefinementError('arch raw physical summary mismatch')
        if reference['load']<=0 or row['relative_load_error']!=abs(row['load']/reference['load']-1):
            raise RefinementError('arch load comparison mismatch')
        check_samples(full,row)
    return packet


def adjudicate(packet):
    rows = packet['records']
    if len(rows)!=8 or [r['step'] for r in rows]!=list(range(8)):
        raise RefinementError('eight ordered arch records required')
    crossing = rows[0]['current_load_slope']>0>rows[-1]['current_load_slope']
    maxima = {key:max(r[key] for r in rows) for key in ERRORS}
    if any(not math.isfinite(v) or v<0 for v in maxima.values()):
        raise RefinementError('finite nonnegative accuracy metrics required')
    passing = crossing and all(v<.02 for v in maxima.values())
    return {'schema':SCHEMA,'disposition':'RESEARCH_ARCH_COMPARISONS_BELOW_2_PERCENT' if passing
            else 'RESEARCH_ARCH_COMPARISONS_UNRESOLVED','production_qualified':False,
            'restriction':'NO_GO_PRODUCTION_RESTRICTION_UNCHANGED','descending_branch_reached':crossing,
            'maxima':maxima}


def _coordinate(repo,commit,output):
    frozen = authority(repo,commit)
    request_id,request_hash = lease(repo,commit,output)
    if output.exists() or output.is_symlink():
        raise RefinementError('fresh exclusive external output required')
    try:
        output.resolve().relative_to(Path(repo).resolve())
    except ValueError:
        pass
    else:
        raise RefinementError('arch diagnostics must be outside worktree')
    (MANAGER/'claims'/('ge-beam3-arch-refine16-'+request_id)).mkdir()
    output.mkdir(parents=True,exist_ok=False)
    publish(output/'inputs.json',{'authority':frozen,'case':CASE,'request_id':request_id,'request_sha256':request_hash})
    folder = output/'arch16';folder.mkdir()
    process = None
    try:
        env = dict(os.environ,**THREAD_ENVIRONMENT,PYTHONHASHSEED='0',PYTHONDONTWRITEBYTECODE='1')
        env['PYTHONPATH'] = str(Path(repo)/'src')+os.pathsep+'C:/Github/ANYfileIO/src'
        line = [sys.executable,'-B','-m',MODULE,'--worker','--commit',commit,'--output',str(output)]
        process = run_child(line,folder,repo,env,timeout=600.,inactivity=300.,memory=24*(1<<30))
        publish(folder/'process.json',process)
        if process['exit_code']!=0:
            raise RefinementError('arch child failed; no retry')
        packet = inspect_worker(folder,frozen,request_id,request_hash)
        if authority(repo,commit)!=frozen or lease(repo,commit,output)!=(request_id,request_hash):
            raise RefinementError('final arch authority mismatch')
        aggregate = adjudicate(packet)
        aggregate.update(authority=frozen,request_id=request_id,request_sha256=request_hash,
                         worker_sha256=sha((folder/'complete.json').read_bytes()))
        publish(output/'aggregate.json',aggregate)
        return aggregate
    except BaseException as exc:
        publish(output/'blocked-diagnostic.json',{'schema':SCHEMA,'production_qualified':False,
            'error_type':type(exc).__name__,'error':str(exc),'process':process,'request_id':request_id})
        raise


def coordinate(repo,commit,output):
    finished = threading.Event()
    def stop():
        if not finished.wait(890.):
            os._exit(124)
    threading.Thread(target=stop,daemon=True).start()
    try:
        return _coordinate(repo,commit,output)
    finally:
        finished.set()


def main():
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--coordinate',action='store_true')
    modes.add_argument('--worker',action='store_true')
    parser.add_argument('--commit',required=True)
    parser.add_argument('--output',required=True,type=Path)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    output = args.output.resolve()
    if args.coordinate:
        print(canonical(coordinate(repo,args.commit,output)).decode('ascii'),end='')
    else:
        worker(repo,args.commit,output)


if __name__=='__main__':
    main()
