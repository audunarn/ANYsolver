"""Pure lifecycle authority tests; actual plastic solves run in bounded workers."""
from copy import deepcopy
from hashlib import sha256
import pytest
from docs.reference_cases import ge_beam3_plastic_arc_lifecycle_protocol as p
from docs.reference_cases.ge_beam3_plastic_arc_lifecycle_worker import mutated

def save(path,value):path.write_bytes(p.canonical(value));return p.bind(path)

def request(tmp_path,mode='full'):
    return dict(schema='GE_BEAM3_PLASTIC_ARC_LIFECYCLE_REQUEST_V1',revision='a'*40,macros=1,mode=mode,
        inputs={key:save(tmp_path/(key+'.json'),{}) for key in sorted(p.INPUTS[mode])})

def test_historical_smoke_and_two_cases():
    a=p.authority()
    assert a['one_macro_checkpoint_sha256']=='29c1d272c7c24328265434efc5f5d36c8c42c1c9895ab7a4f8c99b8333b6e062'
    assert set(a['fixtures'])=={'1','2'} and len(p.MODES)==9 and len(p.MUTATIONS)==13

@pytest.mark.parametrize('mode',p.MODES)
def test_exact_stage_input_inventory(tmp_path,mode):
    value=request(tmp_path,mode);assert set(p.request(value))==p.INPUTS[mode]
    value['inputs']['unexpected']=save(tmp_path/'unexpected.json',{})
    with pytest.raises(ValueError):p.request(value)

@pytest.mark.parametrize('key,value',(('schema','bad'),('revision','a'),('macros',True),('macros',0),('macros',3),('mode',[]),('mode','bad'),('inputs',[])))
def test_request_identity_mutation(tmp_path,key,value):
    v=request(tmp_path);v[key]=value
    with pytest.raises(ValueError):p.request(v)

def test_predecessor_hash_mutation(tmp_path):
    v=request(tmp_path,'resume');v['inputs']['prefix']['sha256']='0'*64
    with pytest.raises(ValueError):p.request(v)

@pytest.mark.parametrize('mode',p.MODES)
def test_unperformed_report_cannot_pass(mode):
    required={'full':{'full_completed'},'prefix':{'paused_after_plastic_step'},'resume':{'resumed_equals_full'},
        'capture':{'original_histories_replayed'},'check':{'all_stations_independently_checked'},
        'mutations':set(p.MUTATIONS)}
    keys=required.get(mode,{'injection_reached','preceding_checkpoint_preserved','resumed_equals_full'})
    v=dict(schema='GE_BEAM3_PLASTIC_ARC_LIFECYCLE_REPORT_V1',revision='a'*40,macros=1,mode=mode,
        checkpoint_sha256='b'*64 if mode=='prefix' or mode.startswith('cancel-') else 'c'*64,
        reference_full_sha256='c'*64,checks={k:True for k in keys},production_qualified=False)
    assert p.validate_report(v,'a'*40,1,mode,'c'*64,'b'*64)==v
    for key in keys:
        changed=deepcopy(v);changed['checks'][key]=False
        with pytest.raises(ValueError):p.validate_report(changed,'a'*40,1,mode,'c'*64,'b'*64)
    v['production_qualified']=True
    with pytest.raises(ValueError):p.validate_report(v,'a'*40,1,mode,'c'*64,'b'*64)

@pytest.mark.parametrize('phase',('formal-a','formal-b','unknown'))
def test_missing_phase_authority(phase):
    with pytest.raises(ValueError):p.prior(phase,None,'a'*40)

def test_rehearsal_has_no_prior(tmp_path):
    assert p.prior('rehearsal',None,'a'*40) is None
    with pytest.raises(ValueError):p.prior('rehearsal',tmp_path/'absent','a'*40)

@pytest.mark.parametrize('kind',('origins','histories','accumulated','predictor','program','work','recovery','cursor'))
def test_mutation_refreshes_all_self_hashes(kind):
    history=[dict(stations=[dict(plastic=[[0.,0.] for _ in range(6)],accumulated=[0.,0.])])]
    row=dict(origins=history,histories=deepcopy(history),predictor=[0.,1.],work=[0.],recovery_sha256='a'*64,
        previous_sha256='a'*64,record_sha256='a'*64)
    value=dict(initial=dict(record_sha256='a'*64),program=dict(steps=[.05,.05,.05]),records=[deepcopy(row) for _ in range(3)],completed_steps=3,checkpoint_sha256='a'*64)
    raw=p.canonical(value);changed=p.strict_bytes(mutated(raw,kind));previous='a'*64
    assert p.canonical(changed)!=raw
    for record in changed['records']:
        assert record['previous_sha256']==previous
        assert record['record_sha256']==sha256(p.canonical({k:v for k,v in record.items() if k!='record_sha256'})).hexdigest()
        previous=record['record_sha256']
    assert changed['checkpoint_sha256']==sha256(p.canonical({k:v for k,v in changed.items() if k!='checkpoint_sha256'})).hexdigest()

def test_mutated_archive_authority(tmp_path,monkeypatch):
    name=tmp_path/'docs/reference_cases/ge_beam3_plastic_arc_smoke_status.json';name.parent.mkdir(parents=True);name.write_bytes(b'{}\n')
    monkeypatch.setattr(p,'ROOT',tmp_path)
    with pytest.raises(ValueError,match='smoke status authority'):p.authority()

@pytest.mark.parametrize('raw',(b'{"x":1,"x":2}\n',b'{"x":Infinity}\n',b'{ "x":1}\n'))
def test_strict_json(raw):
    with pytest.raises(ValueError):p.strict_bytes(raw)
