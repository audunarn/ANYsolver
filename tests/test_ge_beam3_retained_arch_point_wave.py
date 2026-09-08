"""Scheduling tests against hash-bound historical bytes, not new qualification."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import sys
from threading import Event
import time
import pytest
from docs.reference_cases import ge_beam3_retained_arch_point_protocol as p
from docs.reference_cases import ge_beam3_retained_arch_point_wave as w

ARCHIVE=Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-retained-arch-b97ac8c-20260908')
REV='457ad74cf56c6f1e40091d5fccc45879a420d5e1'

@pytest.fixture(scope='module')
def saved():
    raw=p.read(ARCHIVE/'archive-manifest.json')
    assert (len(raw),sha256(raw).hexdigest().upper())==(10459,'35B506E6509550C51E4E33378AE1FBA41ADEE6F7928482438D58DF1996C38458')
    manifest=p.strict_bytes(raw)
    folder=next((ARCHIVE/'2'/'pytest').rglob('checkpoint.json')).parent
    result={}
    for file in folder.glob('*.json'):
        raw=p.read(file)
        assert [len(raw),sha256(raw).hexdigest().upper()]==manifest[file.relative_to(ARCHIVE).as_posix()]
        result[file.name]=p.strict_bytes(raw)
    assert len(result)==15
    return result

def pairs_at(saved, root, count):
    pairs=[]
    for index in range(1,count+1):
        state=deepcopy(saved['checkpoint.json']); state['records']=state['records'][:index]; state['completed_steps']=index
        state['checkpoint_sha256']=sha256(p.canonical({k:v for k,v in state.items() if k!='checkpoint_sha256'})).hexdigest()
        a=root/('state-%02d.json'%index); b=root/('point-%02d.json'%index)
        w.write(a,state); w.write(b,saved[b.name]); pairs.append(dict(state=p.bind(a),point=p.bind(b)))
    return pairs

def first_assignment(root):
    prior=root/'prior.json'; w.write(prior,dict(schema=p.TRANSCRIPT,revision=REV,macros=2,outputs=[]))
    return dict(schema=p.SCHEMA,revision=REV,macros=2,index=1,prior=p.bind(prior))

def test_complete_historical_comparison_exact(saved,tmp_path):
    pairs=pairs_at(saved,tmp_path,12)
    assert p.canonical(p.finish(pairs,2))==p.canonical(saved['comparison.json'])
    with pytest.raises(ValueError,match='twelve'): p.finish(pairs[:-1],2)

@pytest.mark.parametrize('kind',('step','stations','metrics','nonfinite','bool','reference','negative','load','extra'))
def test_point_fact_mutation(saved,tmp_path,kind):
    pair=pairs_at(saved,tmp_path,1)[0]; proof=deepcopy(saved['point-01.json']); row=proof['row']
    if kind=='step': row['step']=2
    elif kind=='stations': row['stations']=True
    elif kind=='metrics': row['metrics'][0]=1e-10
    elif kind=='nonfinite': row['load_error']=float('inf')
    elif kind=='bool': row['load']=True
    elif kind=='reference': proof['reference']['displacement']+=.001
    elif kind=='negative': row['energy_error']=-1.
    elif kind=='load': row['load']+=.01
    else: row['qualified']=True
    # These are disposable mutations, not historical evidence writes.
    if kind=='nonfinite':
        with pytest.raises(ValueError): p.canonical(proof)
        return
    file=tmp_path/'mutant.json'; w.write(file,proof); pair['point']=p.bind(file)
    with pytest.raises(ValueError): p.outputs([pair],2)

@pytest.mark.parametrize('kind',('record','outer','order','prefix','origins','step-size'))
def test_checkpoint_mutation(saved,kind):
    value=deepcopy(saved['checkpoint.json'])
    if kind=='record': value['records'][0]['parameter']+=.1
    elif kind=='outer': value['completed_steps']=11
    elif kind=='order': value['records'][1]['step']=1
    elif kind=='prefix': value['records'][1]['previous_sha256']='0'*64
    elif kind=='origins': value['records'][1]['origins']=[]
    else: value['records'][1]['step_size']=.02
    # Repair nested seals to test semantic history validation, not only hashes.
    if kind not in ('record','outer'):
        for row in value['records']:
            row['record_sha256']=sha256(p.canonical({k:v for k,v in row.items() if k!='record_sha256'})).hexdigest()
        value['checkpoint_sha256']=sha256(p.canonical({k:v for k,v in value.items() if k!='checkpoint_sha256'})).hexdigest()
    with pytest.raises(ValueError): p.checkpoint(value,12)

@pytest.mark.parametrize('kind',('valid','index','mesh','revision','bytes','hash','changed','extra'))
def test_assignment_mutation(tmp_path,kind):
    a=first_assignment(tmp_path)
    if kind=='valid': assert p.assignment(a)['outputs']==[]; return
    if kind=='index': a['index']=2
    elif kind=='mesh': a['macros']=4
    elif kind=='revision': a['revision']='1'*40
    elif kind=='bytes': a['prior']['bytes']=True
    elif kind=='hash': a['prior']['sha256']='0'*64
    elif kind=='extra': a['retry']=True
    else:
        with Path(a['prior']['path']).open('ab') as f: f.write(b' ')
    with pytest.raises(ValueError): p.assignment(a)

@pytest.mark.parametrize('raw',(b'{"x":1,"x":1}\n',b'{"x":NaN}\n',b'{"x":1e999}\n',b'{ "x":1}\n',b'{"x":1}'))
def test_strict_bytes(raw):
    with pytest.raises(ValueError): p.strict_bytes(raw)

def test_guard_before_evaluation(tmp_path,monkeypatch):
    a=first_assignment(tmp_path); request=tmp_path/'assignment.json'; w.write(request,a)
    def denied(_): raise RuntimeError('source denied')
    def forbidden(*args): raise AssertionError('mechanics must not run')
    monkeypatch.setattr(w,'guard',denied); monkeypatch.setattr(w,'evaluate',forbidden)
    with pytest.raises(RuntimeError,match='source denied'):
        w.point(request,sha256(p.read(request)).hexdigest(),tmp_path/'unused')
    assert not (tmp_path/'unused').exists()

def test_exclusive_publication(tmp_path):
    file=tmp_path/'aggregate.json'; w.publish(file,dict(done=True)); raw=file.read_bytes()
    with pytest.raises(FileExistsError): w.publish(file,dict(done=False))
    assert file.read_bytes()==raw

@pytest.mark.parametrize('kind',('timeout','memory','child-failure','wave-deadline'))
def test_process_failure_no_aggregate(kind,tmp_path):
    if kind=='timeout':
        code="import subprocess,sys,time; subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)']); time.sleep(60)"
        wall=1.; memory=128*1024**2; deadline=time.monotonic()+10
    elif kind=='memory':
        code='x=bytearray(512*1024**2)'; wall=10.; memory=96*1024**2; deadline=time.monotonic()+15
    elif kind=='wave-deadline':
        code='import time;time.sleep(60)'; wall=10.; memory=128*1024**2; deadline=time.monotonic()+.5
    else:
        code='raise RuntimeError("disposable failure")'; wall=10.; memory=128*1024**2; deadline=time.monotonic()+15
    result=w.supervise([sys.executable,'-B','-c',code],tmp_path,deadline,Event(),wall=wall,memory=memory)
    assert not result['success'] and result['after'][1]==0 and result['cleanup_error'] is None
    assert not (tmp_path/'aggregate.json').exists()
    if kind=='timeout': assert result['reason']=='CHILD_DEADLINE'
    elif kind=='wave-deadline': assert result['reason']=='WAVE_DEADLINE'
    elif kind=='memory': assert b'MemoryError' in (tmp_path/'stderr.txt').read_bytes()
    else: assert result['reason']=='CHILD_FAILURE'

@pytest.mark.parametrize('mesh',(True,1,3,16))
def test_registered_meshes_only(mesh):
    with pytest.raises(ValueError): p.extent(mesh)
