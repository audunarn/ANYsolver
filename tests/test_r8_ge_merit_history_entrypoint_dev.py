"""Focused source controls for the current-candidate original material-history entrypoint."""
from hashlib import sha256
from pathlib import Path
import ast,json
import pytest

ROOT=Path(__file__).resolve().parents[1]

def test_source_history_entrypoint_guard_refusal(tmp_path,monkeypatch):
    from scripts import r8_ge_merit_interpolation_execution_dev as runner
    monkeypatch.delenv('GE_MERIT_HISTORY_STAGE',raising=False)
    monkeypatch.delenv('GE_MERIT_HISTORY_OUTPUT',raising=False)
    with pytest.raises(ValueError,match='sole installed-history child'):
        runner.installed_history(tmp_path)
    monkeypatch.setenv('GE_MERIT_HISTORY_STAGE','source-controls')
    monkeypatch.setenv('GE_MERIT_HISTORY_OUTPUT',str(tmp_path))
    with pytest.raises(ValueError,match='sole installed-history child'):
        runner.installed_history(tmp_path)
    monkeypatch.setenv('GE_MERIT_HISTORY_STAGE','installed-history')
    monkeypatch.setenv('GE_MERIT_HISTORY_OUTPUT',str(tmp_path/'other'))
    with pytest.raises(ValueError,match='sole installed-history child'):
        runner.installed_history(tmp_path)

def test_source_history_control_injection_seam(tmp_path,monkeypatch):
    from anysolver import stiffened_shell as ss
    from anysolver._stiffened_shell_displacement_corrector import PAIRED_FIXED_WORK_QUADRATIC_V1
    from scripts import r8_ge_merit_interpolation_execution_dev as runner
    from scripts import r8_ge_paired_adaptive_dev as adaptive
    from scripts.r8_ge_coupled_cycle_dev import IDENTITIES,SEED
    seen=[]
    monkeypatch.setattr(adaptive,'_connected_program',
        lambda out,*,control_factory=None,control_kwargs=None:seen.append((out,control_factory,control_kwargs)))
    monkeypatch.setattr(runner,'_history_slot',lambda:dict(status='AUTHORIZED'))
    monkeypatch.setenv('GE_MERIT_HISTORY_STAGE','installed-history')
    monkeypatch.setenv('GE_MERIT_HISTORY_OUTPUT',str(tmp_path))
    runner.installed_history(tmp_path)
    out,factory,kwargs=seen[0]
    assert out==tmp_path and factory is None
    assert kwargs==dict(merit_globalization=PAIRED_FIXED_WORK_QUADRATIC_V1)
    control=ss.DisplacementControl('shell',2,0,force_seed_sha256=IDENTITIES[SEED],**kwargs)
    assert control.merit_globalization==PAIRED_FIXED_WORK_QUADRATIC_V1=='PAIRED_FIXED_WORK_QUADRATIC_V1'

def test_source_history_reusable_program_routes(tmp_path,monkeypatch):
    from scripts import r8_ge_paired_adaptive_dev as adaptive
    from scripts.r8_ge_coupled_cycle_dev import TARGET
    with pytest.raises(ValueError,match='one explicit control injection route'):
        adaptive._connected_program(tmp_path,control_factory=lambda:None,control_kwargs={})
    monkeypatch.delenv('GE_PAIRED_ADAPTIVE_STAGE',raising=False)
    with pytest.raises(ValueError,match='sole installed child'):
        adaptive.connected(tmp_path)
    assert adaptive.PLAN['targets']==[TARGET/2.,0.,TARGET/2.,TARGET]
    assert (adaptive.PLAN['max_iterations'],adaptive.PLAN['max_backtracks'],
            adaptive.PLAN['max_cutbacks'],adaptive.PLAN['max_attempts'])==(20,8,4,96)
    source=Path(adaptive.__file__).read_text(encoding='utf-8');tree=ast.parse(source)
    body={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
    connected=ast.get_source_segment(source,body['connected'])
    assert "GE_PAIRED_ADAPTIVE_STAGE')!='installed-cycle'" in connected
    assert "out!=DOC/'attempt-installed-cycle1'" in connected
    assert 'require_adoption' in connected and 'artifact()' in connected
    assert 'return _connected_program(out)' in connected
    program=ast.get_source_segment(source,body['_connected_program'])
    assert 'GE_PAIRED_ADAPTIVE_STAGE' not in program
    assert "ss.DisplacementControl('shell',2,0,force_seed_sha256=prior.IDENTITIES[prior.SEED]" in program
    assert 'control_factory() if control_factory is not None' in program

def test_source_history_bindings_and_hold_records():
    from scripts import r8_ge_merit_interpolation_execution_dev as runner
    from scripts.r8_ge_coupled_cycle_dev import IDENTITIES
    bound=runner.bindings()
    for rel in ('tests/test_r8_ge_merit_history_entrypoint_dev.py',
                'tests/test_r8_f06_fibre_launch_seam_dev.py'):
        assert bound[rel]==sha256((ROOT/rel).read_bytes()).hexdigest()
    for path,digest in IDENTITIES.items():
        assert bound[path.relative_to(ROOT).as_posix()]==digest
    authority=json.loads((runner.DOC/'INSTALLED_HISTORY_AUTHORITY.json').read_text())
    assert (authority['budget_s'],authority['reserve_s'],authority['process_cap_s'])==(600,60,200)
    assert authority['status'] in ('HELD_PENDING_ROOT_ADOPTION','AUTHORIZED')
    check=json.loads((runner.DOC/'HISTORY_ENTRYPOINT_CONTROLS_AUTHORITY.json').read_text())
    assert (check['budget_s'],check['reserve_s'],check['process_cap_s'])==(600,60,20)
    assert check['status']=='AUTHORIZED'
    v1=json.loads((runner.DOC/'PHYSICAL_HISTORY_READINESS.json').read_text())
    assert v1['status']=='HELD_PENDING_ROOT_EXACT_ADOPTION'
    assert v1['proposed_execution']['runner_status']=='MISSING_RUNNER'
