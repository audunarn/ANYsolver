"""Strict research restart/continuation; no production qualification claim."""

from copy import deepcopy
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from docs.reference_cases import ge_beam3_curved_p5_dynamic_restart_probe as codec
from test_ge_beam3_curved_p5_dynamic_assembly_probe import model,load,assembly,digest


@pytest.fixture(scope='module')
def loaded():
    made=model();made.commit(made.trial(.02,load(made)))
    return made


@pytest.fixture(scope='module')
def checkpoint(loaded): return codec.dumps(loaded)


def modified(payload,path,value):
    record=json.loads(payload);cursor=record
    for part in path[:-1]: cursor=cursor[part]
    cursor[path[-1]]=value
    body={k:v for k,v in record.items() if k!='payload_sha256'}
    record['payload_sha256']=hashlib.sha256(codec.canonical(body)).hexdigest()
    return codec.canonical(record)


def test_initial_and_accepted_roundtrips_are_canonical(checkpoint,loaded):
    first=model();initial=codec.dumps(first)
    assert codec.dumps(codec.loads(initial,first))==initial
    restored=codec.loads(checkpoint,first)
    assert codec.dumps(restored)==checkpoint
    assert digest(restored.committed)==digest(loaded.committed)
    assert digest(restored.replay())==digest(loaded.replay())
    assert len(checkpoint)<codec.MAX_BYTES


def test_continuation_is_byte_identical_through_reversal_and_unloading(checkpoint,loaded):
    uninterrupted=deepcopy(loaded);resumed=codec.loads(checkpoint,model())
    for scale in (-.5,0.,.3):
        a=uninterrupted.trial(.02,scale*load(uninterrupted));b=resumed.trial(.02,scale*load(resumed))
        assert digest(a)==digest(b)
        uninterrupted.commit(a);resumed.commit(b)
        assert digest(uninterrupted.committed)==digest(resumed.committed)
        payload=codec.dumps(resumed)
        assert codec.dumps(uninterrupted)==payload
        resumed=codec.loads(payload,model())
    assert resumed.committed.epoch==4 and resumed.committed.time==.08
    assert np.linalg.norm(resumed.committed.cell_angular_velocity)>1e-6


@pytest.mark.parametrize('mutation',[
    lambda p:p.rstrip(),lambda p:b' '+p,lambda p:b'\xff'+p,
    lambda p:p.replace(b'{',b'{"schema":null,',1),
    lambda p:p.replace(b'"origin":{',b'"origin":{"time":0.0,',1),
    lambda p:b'{"x":NaN}\n',lambda p:b'{"x":Infinity}\n',lambda p:b'{"x":1e400}\n',
    lambda p:b'['*33+b'0'+b']'*33,lambda p:b' '*(codec.MAX_BYTES+1),lambda p:b'',
])
def test_strict_parser_limits(checkpoint,mutation):
    with pytest.raises(codec.RestartError): codec.loads(mutation(checkpoint),model())


@pytest.mark.parametrize('path,value',[
    (['state','epoch'],True),(['state','epoch'],1.0),(['state','epoch'],2147483648),
    (['state','time'],.03),(['state','positions',0,0],'-1.0'),(['state','positions',0,0],-1),
    (['state','nodal_velocity',4,0],.2),(['state','cell_angular_velocity',1,1,0],.2),
    (['state','rotations',4,0,0],.5),(['state','cell_rotations'],[]),(['state','unknown'],0),
    (['accepted','origin','epoch'],2),(['accepted','origin','time'],.01),
    (['accepted','origin','nodal_velocity',4,0],.1),(['accepted','increment',12],.001),
    (['accepted','step'],.04),(['accepted','forces',4,0],.02),(['accepted','evaluations'],129),
    (['accepted','response','stage','tangent',0,0],99.),
    (['accepted','response','stage','element_inertia',1,0],.1),
    (['accepted','response','endpoint_element_forces',1,0],.1),
    (['accepted','response','trace_evaluations'],65),(['accepted','response','kinetic_energy'],1.),
    (['accepted','response','stage','endpoint_guess','schema'],'LEGACY_B3'),
])
def test_rehashed_schema_and_semantic_mutations_are_rejected(checkpoint,path,value):
    with pytest.raises(codec.RestartError): codec.loads(modified(checkpoint,path,value),model())


def test_identity_and_checksum_mismatch_precede_replay(checkpoint,monkeypatch):
    def forbidden(*args,**kwargs): raise AssertionError('identity failure reached mechanics replay')
    monkeypatch.setattr(assembly.DynamicAssemblyProbe,'_endpoint',forbidden)
    monkeypatch.setattr(assembly.DynamicAssemblyProbe,'_reconstruct',forbidden)
    for path,value in [(['schema'],'GE_BEAM3_P5_RESEARCH_ASSEMBLY_RESTART_V1'),
                       (['identity','production_qualified'],True),(['identity','model_sha256'],'0'*64),
                       (['identity','implementation_sources'],{}),(['identity','runtime','numpy'],'other'),
                       (['identity','elements',1,'inertia',0,0],4.),(['identity','fixed_nodes'],[]),
                       (['identity','state_schema'],'BACKWARD_EULER'),(['identity','cell_inertia'],'GUYAN')]:
        with pytest.raises(codec.RestartError): codec.loads(modified(checkpoint,path,value),model())
    record=json.loads(checkpoint);record['payload_sha256']='0'*64
    with pytest.raises(codec.RestartError): codec.loads(codec.canonical(record),model())


@pytest.mark.parametrize('path,value',[(['state','time'],0.),(['accepted','origin','epoch'],1)])
def test_positive_epoch_cannot_have_zero_time(checkpoint,path,value,monkeypatch):
    def forbidden(*args,**kwargs): raise AssertionError('impossible chronology reached mechanics')
    monkeypatch.setattr(assembly.DynamicAssemblyProbe,'_endpoint',forbidden)
    with pytest.raises(codec.RestartError,match='epoch/time'):
        codec.loads(modified(checkpoint,path,value),model())


def test_changed_expected_model_and_pending_export_are_rejected(checkpoint):
    for expected in (model(height=.5),model(order=9),model(fixed_nodes=()),model(rolled=True)):
        before=digest(expected.committed)
        with pytest.raises(codec.RestartError): codec.loads(checkpoint,expected)
        assert digest(expected.committed)==before
    pending=model();trial=pending.trial(.02,load(pending));before=digest(pending.committed)
    with pytest.raises(codec.RestartError): codec.dumps(pending)
    with pytest.raises(codec.RestartError): codec.loads(checkpoint,pending)
    assert digest(pending.committed)==before
    pending.discard(trial)


@pytest.mark.parametrize('kwargs',[{'rolled':True},{'count':4},{'fixed_nodes':()}])
def test_nondefault_graph_authority_roundtrips_without_losing_velocity_or_triad_data(kwargs):
    made=model(**kwargs);made.commit(made.trial(.02,load(made)))
    payload=codec.dumps(made);restored=codec.loads(payload,model(**kwargs))
    assert codec.dumps(restored)==payload
    assert digest(made.committed)==digest(restored.committed)


def test_later_origin_must_already_satisfy_algebraic_equilibrium(loaded,monkeypatch):
    made=deepcopy(loaded);made.commit(made.trial(.02,-.5*load(made)))
    payload=codec.dumps(made);record=json.loads(payload)
    from docs.reference_cases.ge_beam3_curved_p5_algebra_probe import rotation
    changed=(rotation([.05,0.,0.])@np.array(record['accepted']['origin']['rotations'][3])).tolist()
    payload=modified(payload,['accepted','origin','rotations',3],changed)
    def forbidden(*args): raise AssertionError('corrupt origin reached accepted-step replay')
    monkeypatch.setattr(assembly.DynamicAssemblyProbe,'_reconstruct',forbidden)
    with pytest.raises(codec.RestartError,match='origin algebraic'):
        codec.loads(payload,model())


def test_no_initial_velocity_authority_is_fabricated():
    made=model();state=made.committed;v=state.nodal_velocity.copy();v[-1,0]=.2
    made._checkpoint=(replace(state,nodal_velocity=v),None)
    before=digest(made.committed)
    with pytest.raises(codec.RestartError,match='initial restart'): codec.dumps(made)
    assert digest(made.committed)==before


def test_late_replay_failure_returns_no_model_and_preserves_expected(checkpoint,loaded,monkeypatch):
    expected=deepcopy(loaded);before=digest(expected.committed)
    original=assembly.DynamicAssemblyProbe._endpoint
    calls=[]
    def fail_after_origin(self,*args,**kwargs):
        calls.append(1)
        if len(calls)>1: raise ValueError('injected endpoint replay failure')
        return original(self,*args,**kwargs)
    monkeypatch.setattr(assembly.DynamicAssemblyProbe,'_endpoint',fail_after_origin)
    with pytest.raises(codec.RestartError): codec.loads(checkpoint,expected)
    assert len(calls)==2 and digest(expected.committed)==before and expected._pending is None


def test_exclusive_file_publication_preserves_existing_and_removes_only_own_stage(tmp_path,loaded,monkeypatch):
    target=tmp_path/'dynamic.json';result=codec.write_exclusive(target,loaded)
    preserved=target.read_bytes();assert hashlib.sha256(preserved).hexdigest()==result
    with pytest.raises(FileExistsError): codec.write_exclusive(target,loaded)
    assert target.read_bytes()==preserved
    assert list(tmp_path.iterdir())==[target]
    def fail_link(*args): raise OSError('injected publication failure')
    monkeypatch.setattr(codec.os,'link',fail_link)
    with pytest.raises(OSError): codec.write_exclusive(tmp_path/'absent.json',loaded)
    assert list(tmp_path.iterdir())==[target] and target.read_bytes()==preserved


def test_fresh_process_reexports_identical_bytes(tmp_path,loaded):
    source=tmp_path/'source.json';target=tmp_path/'restored.json'
    codec.write_exclusive(source,loaded)
    root=Path(__file__).resolve().parents[1]
    code=("import sys; from pathlib import Path; sys.path.insert(0,str(Path.cwd()/'tests')); "
          "from test_ge_beam3_curved_p5_dynamic_assembly_probe import model; "
          "from docs.reference_cases import ge_beam3_curved_p5_dynamic_restart_probe as codec; "
          "restored=codec.loads(Path(sys.argv[1]).read_bytes(),model()); "
          "codec.write_exclusive(Path(sys.argv[2]),restored)")
    env=os.environ.copy()
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'): env[key]='1'
    process=subprocess.run([sys.executable,'-B','-c',code,str(source),str(target)],cwd=root,env=env,
                           capture_output=True,text=True,timeout=60)
    assert process.returncode==0,process.stdout+process.stderr
    assert source.read_bytes()==target.read_bytes()
