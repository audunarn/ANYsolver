"""One-use bounded compensated 32-element onset successor; research only."""

import argparse
import os
from pathlib import Path
import re
import sys
import threading

from docs.reference_cases import ge_beam3_curved_p5_arch_onset_wave as shared
from docs.reference_cases import ge_beam3_curved_p5_arch_onset32_wave as historical
from docs.reference_cases import ge_beam3_curved_p5_compensated32_diagnostic as diagnostic
from docs.reference_cases import ge_beam3_curved_p5_compensated_onset_probe as probe
from docs.reference_cases.ge_beam3_curved_p5_compensated_onset_inspection import inspect_worker


BASE = '709eb294d78b894289cb1e9b4b10e59877f217c3'
MODULE = 'docs.reference_cases.ge_beam3_curved_p5_compensated_onset_wave'
SCHEMA = 'GE_BEAM3_P5_COMPENSATED_ONSET32_WAVE_V1'
MANAGER = shared.MANAGER
PREFIX = 'ge-beam3-compensated-onset32-'
ALLOWED = {'docs/reference_cases/ge_beam3_curved_p5_compensated_onset_probe.py',
    'docs/reference_cases/ge_beam3_curved_p5_compensated_onset_inspection.py',
    'docs/reference_cases/ge_beam3_curved_p5_compensated_onset_wave.py',
    'tests/test_ge_beam3_curved_p5_compensated_onset.py',
    'docs/agent_plans/GE_BEAM3_CURVED_P5_COMPENSATED_ONSET_PLAN.md'}
ROOT = Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-p5-compensated32-20260906-530101a9fd6a4c1cbf864484571fc219')
FILES = {
    'diagnostic.json': (5854,'fc5e4f12b361c023b7b72c4f81aae0335770339f0c0374de931931a91c62d12f'),
    'inputs.json': (6024,'ef221acad6721d36bb02f8431f7619ac38772b8263742d6497d3de7ef15d5f41'),
    'compensated32/complete.json': (5967,'3fc422671ea4fd86f5f38f7f517f778213e9f35e5993e3be32f55ec7a2e06a66'),
    'compensated32/initial.json': (1159786,'10a13fd5ce0c5867fd86c87ebe4e7c10fe8d431122fefbe8cbc99acb3f62ca0f'),
    'compensated32/target.json': (1194913,'afc4d21eeacd3212f34a6cb2809f398510b079241aaadb0c624e048b9463db75'),
    'compensated32/process-start.json': (381,'a28b453438c43bed928622abc012718057a441101cf5452a52d48c1c5105cdad'),
    'compensated32/process.json': (100,'e8a016d13b99bf874af43846f814d67257f2c5f3e3e09affcdb6fdc81baafde6'),
    'compensated32/progress.jsonl': (5639,'d9a918428546f24ec4818646802a1f042382df46821149bd5751b942a29a8529'),
    'compensated32/stdout.log': (0,'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'),
    'compensated32/stderr.log': (0,'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'),
}
CONSUMED = ('5fbe008bfc7744079ed0e35d12dc72f1','5b59e2613245422a922616891f8b003b',
    '69778aebc5d44cbd8f91e0426edc2232','1b6bdcd793404eae8d19435b708701d7',
    '4d4cbecbbba445a4a9656976f1e2dee8','1b014e442280411a95c66e27502d0465')
CASE = dict(historical.CASE, wave_seconds=890, coordinate_schema=diagnostic.COORDINATES,
    assembly_schema=diagnostic.CASE['assembly_schema'], total_local_force_budget=1e-12,
    local_rotation_length=2., local_force_scale=1., production_qualified=False,
    raw_schema=probe.RAW_SCHEMA, result_schema=probe.SCHEMA)


def preserved():
    for name,(size,digest) in FILES.items():
        data = shared.ordinary(ROOT/name)
        if len(data) != size or shared.sha(data) != digest:
            raise ValueError('preserved compensated comparison hash mismatch')
    if {p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file()} != set(FILES):
        raise ValueError('preserved compensated comparison inventory mismatch')
    historical.previous();shared.references()
    return {'compensated_comparison': {k:{'bytes':v[0],'sha256':v[1]} for k,v in FILES.items()},
        'failed_inputs': diagnostic.failed_inputs(), 'observation_inputs': diagnostic.observation_inputs(),
        'force_inputs': diagnostic.force_inputs(), 'centered_inputs': diagnostic.centered_inputs(),
        'onset_4_8_16': {'bytes':historical.PREVIOUS_BINDING[0],'sha256':historical.PREVIOUS_BINDING[1]},
        'continuum': {str(k):{'bytes':v[0],'sha256':v[1]} for k,v in shared.ROOTS.items()}}


def authority(repo,commit):
    if not re.fullmatch('[0-9a-f]{40}',commit) or shared.git(repo,'rev-parse','HEAD') != commit:
        raise ValueError('frozen onset commit mismatch')
    if shared.git(repo,'status','--porcelain','--untracked-files=all'):
        raise ValueError('dirty onset input')
    if (shared.git(repo,'rev-parse','HEAD^') != BASE or
            set(shared.git(repo,'diff','--name-only',BASE,commit).splitlines()) != ALLOWED):
        raise ValueError('exact onset parent/path set required')
    if (shared.git(shared.SIBLING,'status','--porcelain','--untracked-files=all') or
            shared.git(shared.SIBLING,'rev-parse','HEAD') != shared.SIBLING_COMMIT or
            shared.git(shared.SIBLING,'rev-parse','HEAD^{tree}') != shared.SIBLING_TREE):
        raise ValueError('frozen sibling mismatch')
    env = shared.environment()
    if shared.sha(shared.canonical(env)) != shared.ENVIRONMENT_SHA:
        raise ValueError('frozen environment mismatch')
    return {'commit':commit,'tree':shared.git(repo,'rev-parse','HEAD^{tree}'),
        'case_sha256':shared.sha(shared.canonical(CASE)),'environment':env,
        'sibling_commit':shared.SIBLING_COMMIT,'sibling_tree':shared.SIBLING_TREE,'preserved':preserved()}


def command(repo,commit,output):
    return f"& '{sys.executable}' -B -m {MODULE} --coordinate --commit {commit} --output '{Path(output)}'"


def lease(repo,commit,output,*,manager=None):
    manager = MANAGER if manager is None else Path(manager)
    owner = shared.load(manager/'active-lock/owner.json',strict=False)
    request_id = owner.get('request_id')
    if not isinstance(request_id,str) or not re.fullmatch('[0-9a-f]{32}',request_id):
        raise ValueError('active onset lease required')
    path = manager/'requests'/(request_id+'.json');request = shared.load(path,strict=False)
    for value in (owner,request):
        if (value.get('request_id') != request_id or value.get('command') != command(repo,commit,output) or
                Path(value.get('repository','')).resolve() != Path(repo).resolve()):
            raise ValueError('exact onset command/lease required')
    rows = [[v.strip() for v in line.split('|')[1:-1]] for line in
        (manager/'ledger.md').read_text(encoding='utf-8-sig').splitlines() if line.startswith('|')]
    if [r[2] for r in rows if len(r)>2 and r[1]==request_id] != ['APPROVED'] or request_id in CONSUMED:
        raise ValueError('one unconsumed administrator approval required')
    if any(p.name.endswith(request_id) and p.name != PREFIX+request_id for p in (manager/'claims').glob('*')):
        raise ValueError('request already claimed by another runner')
    return request_id,shared.sha(path.read_bytes())


def worker(repo,commit,output):
    frozen = authority(repo,commit);request_id,request_sha = lease(repo,commit,output)
    folder = output/'elements-32'
    with (folder/'progress.jsonl').open('xb') as stream:
        def progress(phase,label,event=None):
            stream.write(shared.canonical({'phase':phase,'id':label,'event':event}));stream.flush()
        result = probe.records(count=32,progress=progress,
            publish_raw=lambda label,raw:shared.publish(folder/(label+'.json'),raw))
        if authority(repo,commit) != frozen or lease(repo,commit,output) != (request_id,request_sha):
            raise ValueError('onset worker authority changed')
        shared.publish(folder/'complete.json',{'schema':SCHEMA,'authority':frozen,
            'request_id':request_id,'request_sha256':request_sha,'result':result})
        progress('COMPLETION',None)


def compare(packet,roots,previous):
    # Pure endpoint arithmetic only; does not call any old worker or inspector.
    result = historical.compare(packet,roots,previous)
    result.update(schema=SCHEMA,disposition='RESEARCH_COMPENSATED_ONSET32_DIAGNOSTICS_COMPLETE',
                  coordinate_schema=diagnostic.COORDINATES)
    return result


def _coordinate(repo,commit,output):
    frozen = authority(repo,commit);request_id,request_sha = lease(repo,commit,output)
    excluded = (repo,ROOT,diagnostic.FAILED_ROOT,diagnostic.OBSERVATION_ROOT,diagnostic.FORCE_ROOT,
                diagnostic.CENTERED_ROOT,shared.REFERENCE,historical.PREVIOUS.parent)
    if output.exists() or output.is_symlink() or any(output.resolve().is_relative_to(p.resolve()) for p in excluded):
        raise ValueError('fresh external onset output required')
    (MANAGER/'claims'/(PREFIX+request_id)).mkdir();output.mkdir(parents=True,exist_ok=False)
    shared.publish(output/'inputs.json',{'authority':frozen,'case':CASE,'request_id':request_id,'request_sha256':request_sha})
    folder = output/'elements-32';folder.mkdir();process = None
    try:
        env = dict(os.environ,**shared.THREAD_ENVIRONMENT,PYTHONHASHSEED='0',PYTHONDONTWRITEBYTECODE='1')
        env['PYTHONPATH'] = str(repo/'src')+os.pathsep+str(shared.SIBLING/'src')
        line = [sys.executable,'-B','-m',MODULE,'--worker','--commit',commit,'--output',str(output)]
        process = shared.run_child(line,folder,repo,env,timeout=600.,inactivity=300.,memory=24*(1<<30))
        shared.publish(folder/'process.json',process)
        if process['exit_code'] != 0: raise ValueError('onset worker failed; no retry')
        packet = inspect_worker(folder,32,frozen,request_id,request_sha,schema=SCHEMA)
        if authority(repo,commit) != frozen or lease(repo,commit,output) != (request_id,request_sha):
            raise ValueError('onset final authority mismatch')
        result = compare(packet,shared.references(),historical.previous())
        result.update(authority=frozen,request_id=request_id,request_sha256=request_sha,
            worker_sha256=shared.sha(shared.ordinary(folder/'complete.json')),
            progress_sha256=shared.sha(shared.ordinary(folder/'progress.jsonl')))
        shared.publish(output/'aggregate.json',result)
        return result
    except BaseException as error:
        shared.publish(output/'blocked-diagnostic.json',{'schema':SCHEMA,'production_qualified':False,
            'request_id':request_id,'error_type':type(error).__name__,'error':str(error),'process':process})
        raise


def coordinate(repo,commit,output):
    finished = threading.Event()
    def stop():
        if not finished.wait(890.): os._exit(124)
    threading.Thread(target=stop,daemon=True).start()
    try: return _coordinate(repo,commit,output)
    finally: finished.set()


def main():
    parser = argparse.ArgumentParser();mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--coordinate',action='store_true');mode.add_argument('--worker',action='store_true')
    parser.add_argument('--commit',required=True);parser.add_argument('--output',required=True,type=Path)
    args = parser.parse_args();repo = Path(__file__).resolve().parents[2]
    for key,value in shared.THREAD_ENVIRONMENT.items(): os.environ[key] = value
    if args.coordinate: print(shared.canonical(coordinate(repo,args.commit,args.output.resolve())).decode(),end='')
    else: worker(repo,args.commit,args.output.resolve())


if __name__ == '__main__': main()
