"""Scheduling/serialization/process checks, not replacement mechanics evidence."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import sys
from threading import Event
import time
import pytest
from docs.reference_cases import ge_beam3_retained_prestress_protocol as protocol
from docs.reference_cases import ge_beam3_retained_prestress_wave as wave

ARCHIVE=Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-retained-guard-16bef8b-20260908')
REV='60e42facb4013866dafec8239755dcf87180adea'

@pytest.fixture(scope='module')
def saved():
    raw=protocol.read(ARCHIVE/'archive-manifest.json')
    assert len(raw)==32910 and sha256(raw).hexdigest().upper()=='ECCAEF6F8E79A3FFC41E866362C16832ACF8677557A768767779AFFA2129CAE1'
    manifest=protocol.strict_bytes(raw);out={}
    for n in (1,2,4):
        path=next((ARCHIVE/('n%d'%n)/'pytest').rglob('buckling.json'))
        raw=protocol.read(path)
        assert [len(raw),sha256(raw).hexdigest().upper()]==manifest[path.relative_to(ARCHIVE).as_posix()]
        out[n]=protocol.strict_bytes(raw)
    return out

@pytest.mark.parametrize('n',(1,2,4))
def test_prior_search_protocol_identical(saved,n):
    old=saved[n];rows=old['rows']
    for index,row in enumerate(rows):assert protocol.search(rows[:index],n)[0]==row['compression']
    assert protocol.canonical(protocol.finish(rows,n))==protocol.canonical(old)

@pytest.mark.parametrize('kind',('index','compression','nonfinite','bool','error','hash','extra','root-check'))
def test_search_mutations(saved,kind):
    rows=deepcopy(saved[1]['rows'])
    if kind=='index':rows[1]['index']=2
    elif kind=='compression':rows[5]['compression']+=.001
    elif kind=='nonfinite':rows[1]['lambda_min']=float('inf')
    elif kind=='bool':rows[0]['compression']=True
    elif kind=='error':rows[0]['reaction_error']=-1.
    elif kind=='hash':rows[0]['checkpoint_sha256']='wrong'
    elif kind=='extra':rows[0]['qualified']=True
    else:rows[0]['full_partition_root_error']=None
    with pytest.raises(ValueError):protocol.finish(rows,1)

@pytest.mark.parametrize('raw',(b'{"x":1,"x":1}\n',b'{"x":NaN}\n',b'{"x":1e999}\n',b'{ "x":1}\n',b'{"x":1}'))
def test_strict_json(raw):
    with pytest.raises(ValueError):protocol.strict_bytes(raw)

def first_assignment(tmp_path):
    p=tmp_path/'prior.json';wave.write(p,dict(revision=REV,macros=1,rows=[],outputs=[]))
    return dict(schema='GE_BEAM3_EULER_POINT_ASSIGNMENT_V1',revision=REV,macros=1,index=0,
                compression=-.5*protocol.EULER,prior=protocol.bind(p))

@pytest.mark.parametrize('kind',('valid','load','index','mesh','bytes','hash','prior-change'))
def test_assignment_bindings(tmp_path,kind):
    a=first_assignment(tmp_path)
    if kind=='valid':assert protocol.assignment(a)['rows']==[];return
    if kind=='load':a['compression']=0.
    elif kind=='index':a['index']=True
    elif kind=='mesh':a['macros']=2
    elif kind=='bytes':a['prior']['bytes']=True
    elif kind=='hash':a['prior']['sha256']='0'*64
    else:
        # A deliberately changed disposable file must not retain authority.
        with Path(a['prior']['path']).open('ab') as stream:stream.write(b' ')
    with pytest.raises(ValueError):protocol.assignment(a)

def test_guard_before_mechanics(tmp_path,monkeypatch):
    a=first_assignment(tmp_path);request=tmp_path/'request.json';wave.write(request,a)
    def denied(revision):raise RuntimeError('frozen source denied')
    monkeypatch.setattr(wave,'guard',denied)
    with pytest.raises(RuntimeError,match='frozen source denied'):
        wave.point(request,sha256(protocol.read(request)).hexdigest(),tmp_path/'unused')
    assert not (tmp_path/'unused').exists()

def test_complete_only_and_exclusive_publication(saved,tmp_path):
    with pytest.raises(ValueError):protocol.finish(saved[1]['rows'][:-1],1)
    path=tmp_path/'canonical.json';wave.publish(path,dict(valid=True));before=path.read_bytes()
    with pytest.raises(FileExistsError):wave.publish(path,dict(valid=False))
    assert path.read_bytes()==before

@pytest.mark.parametrize('kind',('timeout','memory','child-failure','wave-deadline'))
def test_bounded_failure_leaves_no_aggregate(kind,tmp_path):
    if kind=='timeout':
        code="import subprocess,sys,time; subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)']); time.sleep(60)"
        wall=1.;memory=128*1024**2;deadline=time.monotonic()+10
    elif kind=='memory':
        code='x=bytearray(512*1024**2)';wall=10.;memory=96*1024**2;deadline=time.monotonic()+15
    elif kind=='wave-deadline':
        code='import time;time.sleep(60)';wall=10.;memory=128*1024**2;deadline=time.monotonic()+.5
    else:
        code='raise RuntimeError("disposable failure")';wall=10.;memory=128*1024**2;deadline=time.monotonic()+15
    result=wave.supervise([sys.executable,'-B','-c',code],tmp_path,deadline,Event(),wall=wall,memory=memory)
    assert not result['success'] and result['after'][1]==0 and result['cleanup_error'] is None
    assert not (tmp_path/'aggregate.json').exists()
    if kind=='timeout':assert result['reason']=='CHILD_DEADLINE'
    elif kind=='wave-deadline':assert result['reason']=='WAVE_DEADLINE'
    elif kind=='memory':assert b'MemoryError' in (tmp_path/'stderr.txt').read_bytes()
    else:assert result['reason']=='CHILD_FAILURE'
