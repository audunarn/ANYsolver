"""Shared bounded beam gate runner; only explicitly registered gates execute."""
import argparse
import ast
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import ge_beam3_g3b_environment as environment

SCOPE='GE_BEAM3_BOUNDED_REGISTERED_GATE_V2'
BASE='22289a62fda9bb09def91c21b297b2cf06533a19'
CONTRACT='docs/reference_cases/ge_beam3_g3c_b2_physical_contract_v1.json'
CONTRACT_SHA='6d202e2c25bc62c0987f090a7b5c092bc788318bbb37e27c1261e67af592996b'
DESIGN_REVIEW='docs/reference_cases/ge_beam3_g3c_b2_physical_contract_review_v1.json'
DESIGN_SHA='ba784eb40010a765fed25f891a0b0ccadf68c5beadabcf20b5161f2da5c204a4'
CAPSULE=Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-g3b-rehearsal-history-20260912-0fe7f8f/capsule/environment.json')
CAPSULE_SHA='2ce154b866565e1d03019651b1ae7fdd070e5554f38d72adf21d8080558b6756'
JOB='docs/reference_cases/e4_pl_s3_v2_bounded_process.py'
JOB_SHA='c5b192c9c3f6ee2c68a42ab4a0cfbcdbe81581381b800c13aacce0bb219a3383'
TEST='tests/test_ge_beam3_g3c_b2_physical_core.py'
TESTS={'b2-core':(TEST,'numeric_core'),
       'b2-adapter':('tests/test_ge_beam3_g3c_b2_physical_adapter.py','adapter')}
ALLOWED={
    'src/anysolver/_ge_beam3_g3c_b2_physical_adapter.py',TESTS['b2-adapter'][0],
    'scripts/run_ge_beam3_qualification.py','tests/test_ge_beam3_qualification_runner.py',
    'docs/GE_BEAM3_QUALIFICATION_COMPLETION_REGISTER.md',
    'docs/GE_BEAM3_B2_PHYSICAL_ADAPTER_PLAN.md','docs/GE_BEAM3_Q4_RECOVERY_COEFFICIENT_AUDIT_PLAN.md',
    'docs/reference_cases/ge_beam3_q4_exact_field.py',
    'docs/reference_cases/ge_beam3_q4_recovery_coefficient_producer.py',
    'docs/reference_cases/ge_beam3_q4_recovery_coefficient_checker.py',
    'docs/reference_cases/ge_beam3_8073635_integration_contract_review.json',
}
INTEGRATION_REVIEW='docs/reference_cases/ge_beam3_8073635_integration_contract_review.json'
INTEGRATION_SHA='3be7021fd63a259cca5c48d0e6b47e6a261805f10b4909374f5a9610c17a7b59'
MEMORY=24*1024**3
THREADS=('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','BLIS_NUM_THREADS','NUMBA_NUM_THREADS','TBB_NUM_THREADS')

def canonical(v):
    return (json.dumps(v,sort_keys=True,separators=(',', ':'),allow_nan=False)+'\n').encode('ascii')

def write(path,value):
    with path.open('xb') as stream:stream.write(canonical(value))

def read(path):return environment.regular(path).read_bytes()
def fingerprint(raw):return dict(bytes=len(raw),sha256=sha256(raw).hexdigest())

def git(*args):
    return subprocess.check_output(['git','-c','safe.directory='+ROOT.as_posix(),
        '-c','core.autocrlf=true','-c','core.eol=crlf',*args],cwd=ROOT,
        env=environment.git_env(),timeout=30).decode().strip()

def inputs():
    names=git('ls-files','-z').split('\0')
    return {name:fingerprint(read(ROOT/name).replace(b'\r\n',b'\n')) for name in sorted(names) if name}

def inventory(lane,gate='b2-core'):
    if gate not in TESTS:raise ValueError('unregistered gate')
    test_path,inventory_key=TESTS[gate]
    contract=environment.strict(read(ROOT/CONTRACT).replace(b'\r\n',b'\n'))
    names=contract['test_nodes'][inventory_key]
    tree=ast.parse(read(ROOT/test_path))
    actual=[n.name for n in tree.body if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')]
    if actual!=names:raise ValueError('registered test inventory changed')
    if lane=='smoke':names=[names[2],names[7]] if gate=='b2-core' else [names[0]]
    elif lane!='core':raise ValueError('unregistered lane')
    return [test_path+'::'+name for name in names]

def verify_review(raw,digest,candidate,rows,gate='b2-core'):
    if sha256(raw).hexdigest()!=digest:raise ValueError('review hash')
    r=environment.strict(raw)
    if (set(r)!={'decision','findings','reviewer','scope','subject_commit'}
        or r['decision']!='ACCEPTED_GE_BEAM3_REGISTERED_GATE_FOR_BOUNDED_EXECUTION' or r['findings']
        or r['reviewer'].get('independent') is not True
        or r['subject_commit']!=candidate['commit']
        or r['scope']!={'scope_id':SCOPE,'gate':gate,'subject_tree':candidate['tree'],
                        'inputs_sha256':sha256(canonical(rows)).hexdigest(),'contract_sha256':CONTRACT_SHA}):
        raise ValueError('implementation review authority')
    return r

def authority(review_path,review_sha,gate='b2-core'):
    if gate not in TESTS:raise ValueError('unregistered gate')
    if git('status','--porcelain','--untracked-files=all'):raise ValueError('dirty candidate')
    candidate=dict(commit=git('rev-parse','HEAD'),tree=git('rev-parse','HEAD^{tree}'))
    git('merge-base','--is-ancestor',BASE,'HEAD')
    changed=set(filter(None,git('diff','--name-only',BASE,'HEAD').splitlines()))
    if not changed<=ALLOWED:raise ValueError('production or unregistered extent changed')
    for path,digest in ((CONTRACT,CONTRACT_SHA),(DESIGN_REVIEW,DESIGN_SHA),(JOB,JOB_SHA),(INTEGRATION_REVIEW,INTEGRATION_SHA)):
        if sha256(read(ROOT/path).replace(b'\r\n',b'\n')).hexdigest()!=digest:raise ValueError('frozen authority input')
    contract=environment.strict(read(ROOT/CONTRACT).replace(b'\r\n',b'\n'))
    for key in ('source','proposal'):
        item=contract[key]
        if sha256(read(ROOT/item['path']).replace(b'\r\n',b'\n')).hexdigest()!=item['sha256']:raise ValueError('source equation changed')
    design=environment.strict(read(ROOT/INTEGRATION_REVIEW).replace(b'\r\n',b'\n'))
    for path,key in (('docs/GE_BEAM3_B2_PHYSICAL_ADAPTER_PLAN.md','b2_adapter_plan_sha256'),
                     ('docs/GE_BEAM3_Q4_RECOVERY_COEFFICIENT_AUDIT_PLAN.md','q4_audit_plan_sha256')):
        if sha256(read(ROOT/path).replace(b'\r\n',b'\n')).hexdigest()!=design['scope'][key]:raise ValueError('integration plan changed')
    inventory('core',gate)
    rows=inputs();raw=read(review_path);verify_review(raw,review_sha,candidate,rows,gate)
    environment.verify(CAPSULE,CAPSULE_SHA)
    return candidate,rows,raw

def monitor(job,process,progress,clock=time.monotonic,sleep=time.sleep,start=None):
    """One terminal state; reserve 15 seconds inside the child limit to drain."""
    start=clock() if start is None else start;last=start;seen=None;peak=0
    while True:
        cpu,active,mem=job.accounting();now=clock();peak=max(peak,mem)
        current=(cpu,*progress())
        if current!=seen:seen=current;last=now
        if now-start>=585 or now-last>=120 or peak>MEMORY:
            drained=job.terminate()
            return dict(status='RESOURCE_BLOCKED',active_processes=job.accounting()[1],
                        peak_tree_bytes=peak,drained=bool(drained),elapsed_seconds=clock()-start)
        code=process.poll()
        if code is not None and active==0:
            return dict(status='PASSED' if code==0 else 'FAILED',active_processes=0,
                        peak_tree_bytes=peak,drained=True,elapsed_seconds=clock()-start)
        sleep(.1)

def validate_lease(lease,expected,review_sha,lane,out):
    candidate,rows,_=expected
    if (set(lease)!={'schema','run_id','gate','lane','candidate','inputs','review_sha256','selected'}
        or lease['schema']!=SCOPE or lease['gate'] not in TESTS or lease['lane']!=lane
        or lease['candidate']!=candidate or lease['inputs']!=rows
        or lease['review_sha256']!=review_sha or lease['selected']!=inventory(lane,lease['gate'])
        or str(uuid.UUID(lease['run_id']))!=lease['run_id']):raise ValueError('lease authority')

def claim_attempt(out,run_id):
    write(out/'worker-attempt.json',dict(run_id=run_id))

def job_type():
    spec=importlib.util.spec_from_file_location('beam_bounded_job',ROOT/JOB)
    m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
    return m._ProcessJob

def worker(out,lease_sha):
    raw=read(out/'lease.json')
    if sha256(raw).hexdigest()!=lease_sha:raise ValueError('lease hash')
    lease=environment.strict(raw)
    print('BEAM CHECKPOINT initialization',flush=True)
    expected=authority(out/'review.json',lease['review_sha256'],lease['gate'])
    validate_lease(lease,expected,lease['review_sha256'],lease['lane'],out)
    claim_attempt(out,lease['run_id'])
    if any(os.environ.get(key)!='1' for key in THREADS):raise ValueError('numerical thread environment')
    print('BEAM CHECKPOINT authority complete',flush=True)
    sys.path[:0]=[str(ROOT/'src'),str(ROOT),str(CAPSULE.parent/'site')]
    import pytest
    class Recorder:
        def __init__(self):self.collected=[];self.passed=[];self.bad=[];self.module=None
        def pytest_collection_modifyitems(self,items):
            self.collected=[i.nodeid for i in items]
            if self.collected!=lease['selected']:raise ValueError('collected inventory differs')
            self.module=items[0].module
        def pytest_runtest_logstart(self,nodeid,location):print('BEAM CHECKPOINT test '+nodeid,flush=True)
        def pytest_runtest_logreport(self,report):
            if report.failed or report.skipped:self.bad.append(report.nodeid)
            if report.when=='call' and report.passed:self.passed.append(report.nodeid)
    recorder=Recorder()
    code=pytest.main(['-vv','-s','-p','no:cacheprovider','--basetemp',str(out/'pytest'),*lease['selected']],plugins=[recorder])
    if code!=0 or recorder.bad or recorder.passed!=lease['selected']:return 1
    records=recorder.module.SCIENTIFIC_RECORDS
    if not records:raise ValueError('missing numerical scientific records')
    if authority(out/'review.json',lease['review_sha256'],lease['gate'])!=expected:raise ValueError('final authority changed')
    scientific=dict(schema='GE_BEAM3_REGISTERED_GATE_SCIENCE_V2',gate=lease['gate'],lane=lease['lane'],
                    candidate=lease['candidate'],selected=lease['selected'],records=records,
                    full_g3c_qualified=False,production_qualified=False)
    write(out/'scientific.pending.json',scientific)
    write(out/'completion.json',dict(selected=recorder.passed,scientific=fingerprint(read(out/'scientific.pending.json'))))
    print('BEAM CHECKPOINT evidence complete',flush=True)
    return 0

class WaveWatchdog:
    """Active coordinator deadline, including authority IO and finalization.

    Start drain with twenty seconds left; an independent hard timer exits even
    if draining or coordinator IO stalls. Windows job handles are kill-on-close.
    """
    def __init__(self,timer=threading.Timer,exit_process=os._exit):
        self.expired=threading.Event();self.job=None;self.exit_process=exit_process
        self.soft=timer(1780,self.expire);self.hard=timer(1800,self.hard_exit)
        for t in (self.hard,self.soft):t.daemon=True;t.start()

    def check(self):
        if self.expired.is_set():raise TimeoutError('whole invocation deadline')

    def attach(self,job):
        self.job=job
        self.check()

    def expire(self):
        self.expired.set()
        try:
            if self.job is not None:self.job.terminate()
        finally:self.exit_process(124)

    def hard_exit(self):
        self.expired.set()
        self.exit_process(124)

    def close(self):
        self.soft.cancel();self.hard.cancel()


def execute(args):
    watchdog=WaveWatchdog()
    try:return execute_guarded(args,watchdog)
    finally:watchdog.close()


def execute_guarded(args,watchdog):
    wave_start=time.monotonic()
    expected=authority(args.review,args.review_sha256,args.gate)
    watchdog.check()
    out=Path(tempfile.mkdtemp(prefix='anysolver-beam-qualification-'))
    print('DIAGNOSTICS '+str(out),flush=True)
    lease=dict(schema=SCOPE,run_id=str(uuid.uuid4()),gate=args.gate,lane=args.lane,
               candidate=expected[0],inputs=expected[1],review_sha256=args.review_sha256,selected=inventory(args.lane,args.gate))
    write(out/'lease.json',lease)
    with (out/'review.json').open('xb') as stream:stream.write(expected[2])
    job=job_type()(MEMORY);record=dict(status='FAILED');process=None
    try:
        watchdog.attach(job)
        env=dict(os.environ,**{key:'1' for key in THREADS})
        env.update(PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTEST_ADDOPTS='',PYTHONDONTWRITEBYTECODE='1')
        with (out/'stdout.log').open('xb') as stdout,(out/'stderr.log').open('xb') as stderr:
            child_start=time.monotonic()
            watchdog.check()
            process=job.launch([sys.executable,'-I','-S','-B','-u',str(Path(__file__).resolve()),'--worker',str(out),
                sha256(read(out/'lease.json')).hexdigest()],cwd=ROOT,env=env,stdout=stdout,stderr=stderr)
            record=monitor(job,process,lambda:((out/'stdout.log').stat().st_size,(out/'stderr.log').stat().st_size),start=child_start)
        if record['status']=='PASSED':
            completion=environment.strict(read(out/'completion.json'))
            pending=read(out/'scientific.pending.json');science=environment.strict(pending)
            if (completion!={'selected':lease['selected'],'scientific':fingerprint(pending)}
                or set(science)!={'schema','gate','lane','candidate','selected','records','full_g3c_qualified','production_qualified'}
                or science['schema']!='GE_BEAM3_REGISTERED_GATE_SCIENCE_V2' or science['gate']!=lease['gate']
                or science['lane']!=lease['lane'] or type(science['records']) is not list or not science['records']
                or science['candidate']!=lease['candidate'] or science['selected']!=lease['selected']
                or science['full_g3c_qualified'] or science['production_qualified']):raise ValueError('completion mismatch')
            if authority(args.review,args.review_sha256,args.gate)!=expected:raise ValueError('coordinator final authority')
            if time.monotonic()-wave_start>=1800:raise ValueError('wave deadline')
    except BaseException as exc:
        record.update(status='FAILED',exception=type(exc).__name__)
        raise
    finally:
        try:
            if job.accounting()[1]:
                # monitor already consumed its drain reserve on resource failure.
                if record.get('status')!='RESOURCE_BLOCKED':job.terminate()
            record['active_processes']=job.accounting()[1]
            if record['active_processes']:record['status']='FAILED_TO_DRAIN'
        finally:job.close()
        record.update(scope=SCOPE,run_id=lease['run_id'],returncode=process.poll() if process else None,
                      wave_elapsed_seconds=time.monotonic()-wave_start,
                      files={p.name:fingerprint(p.read_bytes()) for p in out.iterdir() if p.is_file()})
        write(out/'process.json',record)
        print(canonical(record).decode(),flush=True)
    if record['status']=='PASSED':
        watchdog.check()
        if (out/'scientific.json').exists():raise ValueError('exclusive publication')
        os.rename(out/'scientific.pending.json',out/'scientific.json')
    return int(record['status']!='PASSED')

def main():
    if not (sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode):raise ValueError('use -I -S -B')
    if len(sys.argv)==4 and sys.argv[1]=='--worker':return worker(Path(sys.argv[2]),sys.argv[3])
    if os.name!='nt':raise ValueError('Windows process-tree execution required')
    parser=argparse.ArgumentParser()
    parser.add_argument('--gate',choices=list(TESTS),required=True)
    parser.add_argument('--lane',choices=['smoke','core'],required=True)
    parser.add_argument('--review',type=Path,required=True)
    parser.add_argument('--review-sha256',required=True)
    return execute(parser.parse_args())

if __name__=='__main__':raise SystemExit(main())
