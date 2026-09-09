"""One-use serialized P5 refinement diagnostics; not formal qualification.

Authority and lease validation precede numerical imports. Windows Job Objects
bound whole child trees. Historical S3 process containment is reused unchanged.
"""

import argparse
from dataclasses import asdict
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time

from docs.reference_cases.e4_pl_s3_v2_bounded_process import _ProcessJob, THREAD_ENVIRONMENT, _publish_exclusive


BASE = '607e45b9255de35500c6744df06ece9bc6b30e7e'
MODULE = 'docs.reference_cases.ge_beam3_curved_p5_refinement_wave'
MANAGER = Path('C:/Github/.resource-manager')
SCHEMA = 'GE_BEAM3_P5_REFINE16_DEVELOPMENT_V1'
KINDS = ('continuum256','elements16_order8','elements16_order24')
ALLOWED = {
    'docs/reference_cases/ge_beam3_curved_p5_assembly_history_probe.py',
    'docs/reference_cases/ge_beam3_curved_p5_refinement_wave.py',
    'docs/agent_plans/GE_BEAM3_CURVED_P5_REFINE16_PLAN.md',
    'tests/test_ge_beam3_curved_p5_refinement_wave.py',
}
CASE = {'height': .4, 'factor': [[2.,.1,0.,.2,-.1,0.],[0.,3.,.2,0.,.3,.1],
        [0.,0.,4.,.1,0.,.2],[0.,0.,0.,1.,.1,.2],[0.,0.,0.,0.,1.5,.1],[0.,0.,0.,0.,0.,2.]],
        'direction':[1.,.2,-.1,.3,-.4,.5], 'yield_force':.02, 'hardening':.4,
        'force_pattern':[.1,-.3,.2], 'schedule':[.1,.2,.1,0.,-.2,0.], 'elements':16,
        'reference_steps':256, 'orders':[8,24], 'relative_tip_limit':.02}


class RefinementError(ValueError):
    pass


def canonical(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False,
                       ensure_ascii=True,default=lambda a:a.tolist())+'\n').encode('ascii')


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def _pairs(pairs):
    made = {}
    for key,value in pairs:
        if key in made:
            raise RefinementError('duplicate JSON key')
        made[key] = value
    return made


def _constant(value):
    raise RefinementError('nonfinite JSON value')


def load(path, *, strict=True):
    payload = Path(path).read_bytes()
    if len(payload) > 32*(1<<20):
        raise RefinementError('oversized record')
    value = json.loads(payload.decode('ascii' if strict else 'utf-8-sig'),
                      object_pairs_hook=_pairs,parse_constant=_constant)
    encoded = canonical(value)
    if strict and encoded != payload:
        raise RefinementError('canonical JSON required')
    return value


def publish(path, value):
    payload = canonical(value)
    _publish_exclusive(Path(path),payload)
    return {'name':Path(path).name,'bytes':len(payload),'sha256':sha(payload)}


def git(repo, *arguments):
    env = dict(os.environ, GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull,GIT_NO_REPLACE_OBJECTS='1')
    result = subprocess.run(['git','--no-replace-objects','-C',str(repo),*arguments],
                            capture_output=True,text=True,check=True,timeout=20,env=env)
    return result.stdout.strip()


def command(repo, commit, output):
    return f"& '{sys.executable}' -B -m {MODULE} --coordinate --commit {commit} --output '{Path(output)}'"


def authority(repo, commit):
    repo = Path(repo).resolve()
    if not re.fullmatch('[0-9a-f]{40}',commit) or git(repo,'rev-parse','HEAD') != commit:
        raise RefinementError('frozen commit mismatch')
    if git(repo,'status','--porcelain','--untracked-files=all'):
        raise RefinementError('dirty research inputs')
    git(repo,'merge-base','--is-ancestor',BASE,commit)
    if set(git(repo,'diff','--name-only',BASE,commit).splitlines()) != ALLOWED:
        raise RefinementError('unexpected research implementation extent')
    return {'commit':commit,'tree':git(repo,'rev-parse','HEAD^{tree}'),
            'case_sha256':sha(canonical(CASE)),'python':str(Path(sys.executable).resolve()),
            'python_sha256':sha(Path(sys.executable).read_bytes())}


def lease(repo, commit, output, *, manager=MANAGER):
    owner = load(manager/'active-lock'/'owner.json',strict=False)
    request_id = owner.get('request_id')
    if not isinstance(request_id,str) or not re.fullmatch('[0-9a-f]{32}',request_id):
        raise RefinementError('valid active resource lease required')
    path = manager/'requests'/(request_id+'.json')
    request = load(path,strict=False)
    expected = command(repo,commit,output)
    if (request.get('request_id') != request_id or Path(request.get('repository','')).resolve() != Path(repo).resolve()
            or request.get('command') != expected or owner.get('command') != expected
            or Path(owner.get('repository','')).resolve() != Path(repo).resolve()):
        raise RefinementError('exact registered command/repository lease mismatch')
    rows = [[field.strip() for field in line.split('|')[1:-1]]
            for line in (manager/'ledger.md').read_text(encoding='utf-8-sig').splitlines() if line.startswith('|')]
    states = [row[2] for row in rows if len(row)>2 and row[1] == request_id]
    if states != ['APPROVED']:
        raise RefinementError('one unconsumed administrator approval required')
    return request_id,sha(path.read_bytes())


def refined_references(np, count=16):
    from anysolver.ge_beam3_curved_reference import CurvedBeam3ReferenceGeometry
    if type(count) is not int or count not in (1,2,4,8,16):
        raise RefinementError('registered refinement count required')
    t = np.linspace(-1.,1.,2*count+1)
    nodes = np.column_stack((t,CASE['height']*(1-t*t),np.zeros_like(t)))
    frames = []
    for point in t:
        tangent = np.array([1.,-2*CASE['height']*point,0.]);tangent /= np.linalg.norm(tangent)
        normal = np.array([0.,0.,1.])
        frames.append(np.column_stack((tangent,normal,np.cross(tangent,normal))))
    return tuple(CurvedBeam3ReferenceGeometry(nodes[i:i+3],np.array(frames[i:i+3])) for i in range(0,2*count,2))


def numerical_records(kind, folder, progress):
    """Called only after the worker has validated frozen authority and lease."""
    if kind not in KINDS:
        raise RefinementError('registered worker kind required')
    import numpy as np
    factor = np.array(CASE['factor']);elastic = factor.T @ factor
    records = []
    origins = None
    if kind != 'continuum256':
        from docs.reference_cases.ge_beam3_curved_p5_assembly_history_probe import NonlinearAssemblyHistoryProbe
        from docs.reference_cases.ge_beam3_curved_p5_section_probe import DirectedHardeningSectionProbe
        order = 8 if kind == 'elements16_order8' else 24
        sections = [DirectedHardeningSectionProbe(elastic,CASE['direction'],CASE['yield_force'],CASE['hardening']) for _ in range(16)]
        model = NonlinearAssemblyHistoryProbe(refined_references(np),[(2*i,2*i+1,2*i+2) for i in range(16)],
                                             sections,order=order,extent='REFINEMENT16')
    for index,amplitude in enumerate(CASE['schedule']):
        progress('STEP_START',index)
        force = amplitude*np.array(CASE['force_pattern'])
        if kind == 'continuum256':
            from docs.reference_cases.ge_beam3_curved_p5_continuum_history_reference import HistoryParabolicCantileverReference
            result = HistoryParabolicCantileverReference(CASE['height'],elastic,CASE['direction'],CASE['yield_force'],
                CASE['hardening'],steps=256,origins=origins).solve(force)
            origins = result.histories
            position,potential = result.response.coordinates[-1],result.response.potential
            residual,local = result.response.tip_moment_residual,result.dense_orthogonality_error
            active,count = int(np.count_nonzero(result.dissipation_increments)),len(origins)
        else:
            loads = np.zeros((33,3));loads[-1] = force
            result = model.trial(loads)
            model.commit(result)
            if sha(canonical(asdict(model.replay()))) != sha(canonical(asdict(result.response))):
                raise RefinementError('assembled accepted-origin replay mismatch')
            position,potential = result.positions[-1],result.response.potential
            residual = result.residual_norm
            local = max(e.local_residual_norm for e in result.response.elements)
            active = sum(s.response.plastic_active for e in result.response.elements for s in e.stations)
            count = sum(len(e.stations) for e in result.response.elements)
        raw = publish(folder/f'step-{index:02}.json',asdict(result))
        records.append({'step':index,'amplitude':amplitude,'force':force.tolist(),
            'tip_displacement':(position-np.array([1.,0.,0.])).tolist(),'potential':float(potential),
            'residual':float(residual),'local_check':float(local),'active':int(active),'stations':count,'raw':raw})
        progress('STEP_COMPLETE',index)
    return records


def worker(repo, commit, output, kind):
    if kind not in KINDS:
        raise RefinementError('registered worker kind required')
    frozen = authority(repo,commit)
    request_id,request_hash = lease(repo,commit,output)
    folder = output/kind
    with (folder/'progress.jsonl').open('xb') as stream:
        def progress(phase,step=None):
            stream.write(canonical({'phase':phase,'step':step}));stream.flush()
        progress('INITIALIZATION')
        records = numerical_records(kind,folder,progress)
        if authority(repo,commit) != frozen or lease(repo,commit,output) != (request_id,request_hash):
            raise RefinementError('authority changed during computation')
        publish(folder/'complete.json',{'schema':SCHEMA,'kind':kind,'authority':frozen,'request_id':request_id,
            'request_sha256':request_hash,'production_qualified':False,'records':records})
        progress('COMPLETION')


def run_child(command_line, folder, repo, env, *, timeout=600., inactivity=300., memory=24*(1<<30)):
    if os.name != 'nt' or not 0<timeout<=600 or not 0<inactivity<=300 or not 0<memory<=24*(1<<30):
        raise RefinementError('bounded Windows process-tree controls required')
    job = _ProcessJob(memory)
    started = changed = time.monotonic()
    previous = None
    expired = threading.Event()
    def hard_child_stop():
        expired.set()
        job.terminate()
    timer = threading.Timer(max(.001,timeout-min(15.,timeout/4)),hard_child_stop)
    timer.daemon = True
    timer.start()
    try:
        with (folder/'stdout.log').open('xb') as stdout,(folder/'stderr.log').open('xb') as stderr:
            process = job.launch(command_line,cwd=repo,env=env,stdout=stdout,stderr=stderr)
            publish(folder/'process-start.json',{'pid':process.pid,'command':list(command_line),'started_unix_ns':time.time_ns()})
            while True:
                cpu,active,peak = job.accounting()
                code = process.poll()
                now = time.monotonic()
                progress = folder/'progress.jsonl'
                observation = (cpu,progress.stat().st_size if progress.exists() else 0)
                if observation != previous:
                    changed,previous = now,observation
                if expired.is_set():
                    raise RefinementError('child wall bound reached')
                if code is not None and active == 0:
                    return {'exit_code':int(code),'wall_seconds':now-started,'cpu_100ns':cpu,'peak_tree_bytes':peak}
                if code is not None and active:
                    raise RefinementError('root exited with live descendants')
                if peak > memory or now-started >= timeout or now-changed >= inactivity:
                    raise RefinementError('child memory, wall or inactivity bound reached')
                time.sleep(.1)
    finally:
        timer.cancel()
        timer.join(timeout=16.)
        try:
            if not job.terminate():
                raise RefinementError('process tree did not drain')
        finally:
            job.close()


def inspect_worker(folder, kind, frozen, request_id, request_hash):
    record = load(folder/'complete.json')
    if (set(record) != {'schema','kind','authority','request_id','request_sha256','production_qualified','records'}
            or record['schema'] != SCHEMA or record['kind'] != kind or record['authority'] != frozen
            or record['request_id'] != request_id or record['request_sha256'] != request_hash
            or record['production_qualified'] is not False or len(record['records']) != 6):
        raise RefinementError('complete worker identity/coverage mismatch')
    expected_count = {'continuum256':513,'elements16_order8':256,'elements16_order24':768}[kind]
    for index,row in enumerate(record['records']):
        if set(row) != {'step','amplitude','force','tip_displacement','potential','residual','local_check','active','stations','raw'}:
            raise RefinementError('worker row schema mismatch')
        if (type(row['step']) is not int or row['step'] != index or type(row['stations']) is not int
                or row['amplitude'] != CASE['schedule'][index] or row['stations'] != expected_count):
            raise RefinementError('step/station coverage mismatch')
        if row['force'] != [row['amplitude']*v for v in CASE['force_pattern']] or len(row['tip_displacement']) != 3:
            raise RefinementError('registered force or displacement shape mismatch')
        residual_limit = 1e-12 if kind == 'continuum256' else 1e-11
        if type(row['active']) is not int or not 0<=row['active']<=expected_count or not 0<=row['residual']<=residual_limit:
            raise RefinementError('unresolved scientific row')
        limit = 1e-7 if kind == 'continuum256' else 1e-11
        if not 0<=row['local_check']<=limit:
            raise RefinementError('unresolved local/reference health check')
        raw = row['raw']
        if set(raw) != {'name','bytes','sha256'} or raw['name'] != f'step-{index:02}.json':
            raise RefinementError('raw record binding schema mismatch')
        payload = (folder/raw['name']).read_bytes()
        if len(payload) != raw['bytes'] or sha(payload) != raw['sha256']:
            raise RefinementError('raw record hash mismatch')
        full = load(folder/raw['name'])
        if kind == 'continuum256':
            response = full['response']
            position = response['coordinates'][-1]
            count = len(full['histories'])
            active = sum(v>0 for v in full['dissipation_increments'])
            norm,local = response['tip_moment_residual'],full['dense_orthogonality_error']
            if full['force'] != row['force'] or len(response['coordinates']) != 257:
                raise RefinementError('raw reference force/grid mismatch')
        else:
            response = full['response']
            position = full['positions'][-1]
            elements = response['elements']
            count = sum(len(e['stations']) for e in elements)
            active = sum(s['response']['plastic_active'] for e in elements for s in e['stations'])
            norm,local = full['residual_norm'],max(e['local_residual_norm'] for e in elements)
            if (len(elements) != 16 or any(len(e['stations']) != expected_count//16 for e in elements)
                    or len(full['positions']) != 33 or full['forces'] != [[0.,0.,0.]]*32+[row['force']]):
                raise RefinementError('raw element/force inventory mismatch')
        if (row['tip_displacement'] != [position[0]-1.,position[1],position[2]]
                or row['potential'] != response['potential'] or row['stations'] != count
                or row['active'] != active or row['residual'] != norm or row['local_check'] != local):
            raise RefinementError('summary differs from bound raw record')
    return record


def adjudicate(records):
    if [r['kind'] for r in records] != list(KINDS):
        raise RefinementError('exact serialized worker inventory required')
    comparisons = []
    for index,reference in enumerate(records[0]['records']):
        norm = math.sqrt(sum(v*v for v in reference['tip_displacement']))
        if not math.isfinite(norm) or norm <= 0:
            raise RefinementError('nonzero finite reference displacement required')
        errors = [math.sqrt(sum((a-b)**2 for a,b in zip(r['records'][index]['tip_displacement'],reference['tip_displacement'])))/norm
                  for r in records[1:]]
        quadrature = math.sqrt(sum((a-b)**2 for a,b in zip(records[1]['records'][index]['tip_displacement'],records[2]['records'][index]['tip_displacement'])))/norm
        comparisons.append({'step':index,'relative_tip_errors':errors,'quadrature_relative_tip_difference':quadrature})
    passing = all(error < CASE['relative_tip_limit'] for row in comparisons for error in row['relative_tip_errors'])
    return {'schema':SCHEMA,'disposition':'RESEARCH_REFINEMENT_BELOW_2_PERCENT' if passing else 'RESEARCH_REFINEMENT_ABOVE_2_PERCENT',
            'production_qualified':False,'restriction':'NO_GO_PRODUCTION_RESTRICTION_UNCHANGED','comparisons':comparisons}


def _coordinate(repo, commit, output, started):
    frozen = authority(repo,commit)
    request_id,request_hash = lease(repo,commit,output)
    if output.exists() or output.is_symlink():
        raise RefinementError('fresh exclusive external output root required')
    try:
        output.resolve().relative_to(repo.resolve())
    except ValueError:
        pass
    else:
        raise RefinementError('diagnostic output must be external to worktree')
    (MANAGER/'claims'/('ge-beam3-refine16-'+request_id)).mkdir()
    output.mkdir(parents=True,exist_ok=False)
    publish(output/'inputs.json',{'authority':frozen,'case':CASE,'request_id':request_id,'request_sha256':request_hash})
    processes,records = [],[]
    env = dict(os.environ,**THREAD_ENVIRONMENT,PYTHONHASHSEED='0',PYTHONDONTWRITEBYTECODE='1')
    env['PYTHONPATH'] = str(repo/'src')+os.pathsep+'C:/Github/ANYfileIO/src'
    try:
        for kind in KINDS:
            remaining = 1800-(time.monotonic()-started)-30
            if remaining <= 0:
                raise RefinementError('wave wall budget exhausted')
            folder = output/kind;folder.mkdir()
            line = [sys.executable,'-B','-m',MODULE,'--worker',kind,'--commit',commit,'--output',str(output)]
            process = run_child(line,folder,repo,env,timeout=min(600.,remaining))
            processes.append({'kind':kind,**process})
            publish(folder/'process.json',process)
            if process['exit_code'] != 0:
                raise RefinementError('worker process failed; no retry')
            records.append(inspect_worker(folder,kind,frozen,request_id,request_hash))
        if authority(repo,commit) != frozen or lease(repo,commit,output) != (request_id,request_hash):
            raise RefinementError('final authority mismatch')
        aggregate = adjudicate(records)
        aggregate.update({'authority':frozen,'request_id':request_id,'request_sha256':request_hash,
                          'worker_hashes':[sha((output/k/'complete.json').read_bytes()) for k in KINDS]})
        publish(output/'aggregate.json',aggregate)
        return aggregate
    except BaseException as exc:
        publish(output/'blocked-diagnostic.json',{'schema':SCHEMA,'production_qualified':False,
            'error_type':type(exc).__name__,'error':str(exc),'processes':processes,'request_id':request_id})
        raise


def coordinate(repo, commit, output):
    started = time.monotonic()
    finished = threading.Event()
    def hard_wave_stop():
        if not finished.wait(1780.):
            # Includes authority preflight and final publication, not just math.
            # Closing our Job handles kills assigned descendants. The external
            # PowerShell lease owner still executes its finally after exit.
            os._exit(124)
    threading.Thread(target=hard_wave_stop,daemon=True).start()
    try:
        return _coordinate(repo,commit,output,started)
    finally:
        finished.set()


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--coordinate',action='store_true')
    mode.add_argument('--worker',choices=KINDS)
    parser.add_argument('--commit',required=True)
    parser.add_argument('--output',required=True,type=Path)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    output = args.output.resolve()
    if args.coordinate:
        print(canonical(coordinate(repo,args.commit,output)).decode('ascii'),end='')
    else:
        worker(repo,args.commit,output,args.worker)


if __name__ == '__main__':
    main()
