"""One-use runner/evidence tests; no registered saved-state case is executed."""
from pathlib import Path
import sys
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import b3_e4_f03_variational_attribution as runner

def test_inventory_is_three_family_descriptions_without_new_meshes():
    assert runner.FAMILIES==('P1','hybrid','enriched')
    assert runner.MIDDLE==(8,16,16,8)
    assert set(runner.CASES.values())=={('Q4',16,32,32,16)}
    assert set(runner.PARENT_FILES)=={'registration.json','adjudication.json',
        'q4_middle/solved_state.npz','q4_fine/solved_state.npz'}

def test_parent_binding_rejects_changed_owned_state(monkeypatch):
    monkeypatch.setattr(runner,'parent_states',lambda name:(np.array([1.]),np.array([2.]),np.array([3.])))
    actions={'q_middle':np.array([1.]),'q_fine':np.array([2.]),'lambda_fine':np.array([3.])}
    runner.bind_parent(actions,'P1')
    actions['lambda_fine'][0]=4.
    with pytest.raises(ValueError,match='parent state'):runner.bind_parent(actions,'P1')

def test_original_scalar_and_layout_report_must_match_independent_actions():
    metrics={'family':'P1','middle_mesh':[8,16,16,8],'shell_distance_j':2.}
    verified={'attribution':dict(metrics)}
    runner.bind_attribution(metrics,verified)
    metrics['shell_distance_j']=-2.
    with pytest.raises(ValueError,match='matrix actions'):runner.bind_attribution(metrics,verified)
    with pytest.raises(ValueError,match='inventory'):runner.bind_attribution({},verified)

def test_premature_adjudication_does_not_consume_result(tmp_path,monkeypatch):
    monkeypatch.setattr(runner,'prerequisites',lambda:None)
    monkeypatch.setattr(runner.common,'_registered',lambda root:{})
    with pytest.raises(ValueError,match='complete supervisor'):runner.adjudicate(tmp_path)
    assert not (tmp_path/'adjudication.json').exists()

def test_cancellation_stops_subsequent_launches_and_preserves_prefix(tmp_path,monkeypatch):
    root=tmp_path/'evidence'
    monkeypatch.setattr(runner.common,'register',lambda path:path.mkdir())
    monkeypatch.setattr(runner.common,'_registration_hash',lambda path:'digest')
    called=[]
    def execute(path,name):
        called.append(name);(path/name).mkdir()
        (path/name/'supervision.json').write_text(
            '{"reason":"supervisor_failure","failure":"KeyboardInterrupt: cancelled"}')
        return False
    monkeypatch.setattr(runner.common,'execute',execute)
    with pytest.raises(KeyboardInterrupt):runner.run_once(root)
    assert called==['P1']
    assert not runner.read(root/'orchestration.json')['inventory_complete']
    with pytest.raises(FileExistsError):runner.run_once(root)
    assert called==['P1']

def test_launch_cutoff_keeps_unstarted_inventory_visible(tmp_path,monkeypatch):
    root=tmp_path/'evidence'
    monkeypatch.setattr(runner.common,'register',lambda path:path.mkdir())
    monkeypatch.setattr(runner.common,'_registration_hash',lambda path:'digest')
    times=iter((0.,1201.,1202.))
    monkeypatch.setattr(runner.time,'monotonic',lambda:next(times))
    with pytest.raises(TimeoutError):runner.run_once(root)
    assert runner.read(root/'orchestration.json')['cases']==[]

def test_failed_execution_is_preserved_without_missing_action_archive(tmp_path,monkeypatch):
    (tmp_path/'P1').mkdir()
    (tmp_path/'P1'/'supervision.json').write_text(
        '{"registration_sha256":"digest","reason":"time_limit","exit_code":1,"failure":null}')
    monkeypatch.setattr(runner.common,'_registration_hash',lambda path:'digest')
    assert runner.verify_case(tmp_path,'P1',{})['status']=='FAILED_EXECUTION'

def test_failed_numerical_check_is_not_a_pass(tmp_path,monkeypatch):
    for family in runner.FAMILIES:
        (tmp_path/family).mkdir()
        (tmp_path/family/'supervision.json').write_text('{}')
    monkeypatch.setattr(runner,'prerequisites',lambda:None)
    monkeypatch.setattr(runner.common,'_registered',lambda path:{'identity':{}})
    monkeypatch.setattr(runner.common,'_registration_hash',lambda path:'digest')
    monkeypatch.setattr(runner,'verify_case',lambda root,family,manifest:
        {'status':'FAILED_NUMERICAL_SCREEN' if family=='hybrid' else 'PASSED_ATTRIBUTION_DIAGNOSTIC'})
    assert not runner.adjudicate(tmp_path)
    record=runner.read(tmp_path/'adjudication.json')
    assert record['status']=='FAILED_NUMERICAL_SCREEN'
    assert record['registration_sha256']=='digest'

def test_child_consumes_authority_before_assembly_and_cannot_be_reentered(tmp_path,monkeypatch):
    import threadpoolctl
    import _b3_e4_f03_variational_attribution as implementation
    (tmp_path/'P1').mkdir()
    monkeypatch.setattr(runner.common,'_registered',lambda path:{'cases':{'P1':{}},'identity':{}})
    monkeypatch.setattr(runner.common,'_registration_hash',lambda path:'digest')
    monkeypatch.setattr(runner,'prerequisites',lambda:None)
    monkeypatch.setattr(runner,'parent_states',lambda name:(np.zeros(1),)*3)
    monkeypatch.setattr(threadpoolctl,'threadpool_info',lambda:[{'num_threads':1}])
    for key in runner.common.THREADS:monkeypatch.setenv(key,'1')
    calls=[]
    def interrupted(*args,**kwargs):
        calls.append(True)
        raise RuntimeError('mock interrupted assembly')
    monkeypatch.setattr(implementation,'attribute_saved_states',interrupted)
    with pytest.raises(RuntimeError,match='mock interrupted'):runner.child(tmp_path,'P1')
    with pytest.raises(FileExistsError):runner.child(tmp_path,'P1')
    assert calls==[True]
    assert runner.read(tmp_path/'P1'/'child_started.json')['registration_sha256']=='digest'
