"""Pure authority tests; no fabricated native state is executed."""
import pytest
from docs.reference_cases import ge_beam3_fine_upper_protocol as p

def request():return dict(schema=p.SCHEMA,revision='a'*40,macros=24,stage=1,previous=None)
def receipt():return dict(reason='COMPLETED',success=True,exit_code=0,error=None,cleanup_error=None,elapsed=2.,before=[1,0,100],after=[1,0,100])

def test_frozen_capacity_and_start():
    p.authority();assert p.request(request()) is None;p.receipt(receipt());assert p.TARGETS==(.01,.02,.03,.0456)

@pytest.mark.parametrize('key,value',(('schema','wrong'),('revision','a'),('macros',True),('macros',12),('macros',25),('stage',True),('stage',0),('stage',7),('previous',{})))
def test_request_mutation(key,value):
    v=request();v[key]=value
    with pytest.raises(ValueError):p.request(v)

@pytest.mark.parametrize('key,value',(('success',False),('exit_code',True),('exit_code',1),('reason','CHILD_FAILURE'),('error','x'),('cleanup_error','x'),('elapsed',601.),('elapsed',float('nan')),('before',[1,1,100]),('after',[1,1,100]),('after',[1,0,25*1024**3]),('before',[True,0,100])))
def test_receipt_mutation(key,value):
    v=receipt();v[key]=value
    with pytest.raises(ValueError):p.receipt(v)

@pytest.mark.parametrize('raw',(b'{"x":1,"x":2}\n',b'{"x":NaN}\n',b'{"x":Infinity}\n',b'{ "x":1}\n'))
def test_noncanonical(raw):
    with pytest.raises(ValueError):p.strict_bytes(raw)

def test_missing_previous_and_hash(tmp_path):
    f=tmp_path/'prior.json';f.write_bytes(p.canonical(dict(request=None)))
    v=request();v['stage']=2;v['previous']=p.bind(f)
    with pytest.raises(ValueError):p.request(v)
    v['previous']['sha256']='0'*64
    with pytest.raises(ValueError):p.request(v)

def test_wrong_preceding_stage_rejected_before_recursion(tmp_path):
    r=request();r['stage']=4;f=tmp_path/'request.json';f.write_bytes(p.canonical(r))
    c=tmp_path/'completion.json';c.write_bytes(p.canonical(dict(request=p.bind(f),ready=None,receipt=None)))
    v=request();v['stage']=2;v['previous']=p.bind(c)
    with pytest.raises(ValueError,match='previous worker identity'):p.request(v)

def test_extra_request_key():
    v=request();v['drop']=.046
    with pytest.raises(ValueError):p.request(v)

def test_source_authority_mutation(tmp_path,monkeypatch):
    f=tmp_path/'docs/reference_cases/ge_beam3_capture_guard_status.json';f.parent.mkdir(parents=True);f.write_bytes(b'{}\n')
    monkeypatch.setattr(p,'ROOT',tmp_path)
    with pytest.raises(ValueError,match='source authority'):p.authority()

def test_exclusive_output(tmp_path):
    from docs.reference_cases.ge_beam3_retained_prestress_wave import publish
    f=tmp_path/'ready.json';publish(f,dict(value=1));raw=f.read_bytes()
    with pytest.raises(FileExistsError):publish(f,dict(value=2))
    assert f.read_bytes()==raw

def test_historical_lower_is_evidence_only():
    a=p.authority()
    assert set(a['lower'])=={'20','24'} and set(a['reference'])=={'1','2'}
    assert all(r['drop']==.045 and r['negative_counts']['lateral']==0 for r in a['lower'].values())

def test_old_sixteen_mesh_outside_new_extent():
    v=request();v['macros']=16
    with pytest.raises(ValueError):p.request(v)

def test_lower_archive_mutation(tmp_path,monkeypatch):
    (tmp_path/'archive-manifest.json').write_bytes(b'{}\n');monkeypatch.setattr(p,'LOWER',tmp_path)
    with pytest.raises(ValueError,match='lower archive authority'):p.authority()
