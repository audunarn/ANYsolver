"""Disposable six-macro process mocks, never a native refinement execution."""
from hashlib import sha256
from pathlib import Path
import pytest

from docs.reference_cases import ge_beam3_fibre_arch_six_probe as probe


REVISION = '1'*40


def data(monkeypatch, macros=6):
    def seal(value, key): return {**value, key: sha256(probe.audit.canonical(value)).hexdigest()}
    initial = seal(dict(target=0), 'record_sha256'); previous = initial['record_sha256']; rows = []
    for index, target in enumerate(probe.audit.TARGETS, 1):
        row = seal(dict(target=index, displacement_target=target, parameter=105.,
            previous_sha256=previous, histories=[dict(stations=[dict(rows=[[0., 0.]])])]), 'record_sha256')
        previous = row['record_sha256']; rows.append(row)
    checkpoint = seal(dict(schema='GE_BEAM3_PHYSICAL_FIBRE_TRANSLATION_CONTROL_CHAIN_V1',
        program=dict(schema='GE_BEAM3_KINEMATIC_SEEDED_SPATIAL_NEWTON_FIBRE_CONTROL_V1'),
        node_ids=list(range(1, 2*macros+2)), element_ids=list(range(1, macros+1)), completed_targets=4,
        initial=initial, records=rows), 'checkpoint_sha256')
    reference = dict(schema='GE_BEAM3_PRESERVED_FIBRE_ARCH_GEOMETRIC_COMPARISON_V1',
        production_qualified=False, mechanics_replayed=False,
        section_comparison='NOMINAL_ELASTIC_EA_1E6_GA_4E5_EI_100_NOT_EXACT_DYADIC_SECTION_CERTIFICATE',
        rows=[dict(displacement=t, reference_load=100., native_load=120., reference_profile='BVP9',
            stiffness_scale=1e6, same_equilibrium_branch_proved=False, production_qualified=False)
            for t in (*probe.audit.TARGETS, .075, .1, .15, .2)])
    cp, ref = probe.audit.canonical(checkpoint), probe.audit.canonical(reference)
    monkeypatch.setattr(probe.audit, 'REFERENCE_LF_SHA', sha256(ref).hexdigest())
    return cp, ref


def test_six_macro_packet_uses_preserved_reference_not_missing_prior_output(monkeypatch):
    checkpoint, reference = data(monkeypatch); result = probe.ready(checkpoint, reference, REVISION)
    assert result['macros'] == 6 and result['native_replay_performed']
    assert not result['reference_recomputed'] and not result['production_qualified']
    assert not result['prior_four_macro_request_successful'] and not result['same_equilibrium_branch_proved']
    assert [row['six_macro_relative_load_error'] for row in result['rows']] == [.05]*4
    assert [row['native_six_macro_load'] for row in result['rows']] == [105.]*4
    with pytest.raises(ValueError): probe.ready(checkpoint, reference+b' ', REVISION)
    with pytest.raises(ValueError): probe.ready(checkpoint, reference, 'wrong')
    with pytest.raises(ValueError): probe.audit.inspect_records(probe.audit.parse(checkpoint), probe.audit.parse(reference))


@pytest.mark.parametrize('macros', [True, 2, 8, 6.0])
def test_unregistered_audit_count_rejected(monkeypatch, macros):
    checkpoint, reference = data(monkeypatch)
    with pytest.raises(ValueError): probe.audit.inspect_records(probe.audit.parse(checkpoint), probe.audit.parse(reference), macros=macros)


@pytest.mark.parametrize('incident', ['success', 'exit', 'memory', 'timeout', 'inactivity',
    'partial', 'hash', 'reference_changed', 'cleanup_uncertain', 'descendant_alive'])
@pytest.mark.parametrize('macros', [6, 12])
def test_complete_process_state_and_hashes_control_publication(tmp_path, monkeypatch, incident, macros):
    checkpoint, reference = data(monkeypatch, macros); calls = []
    monkeypatch.setattr(probe, 'guard', lambda revision: calls.append('guard'))
    ref_calls = 0
    def read_reference():
        nonlocal ref_calls
        ref_calls += 1
        return reference+b' ' if incident == 'reference_changed' and ref_calls > 1 else reference
    monkeypatch.setattr(probe, 'reference_bytes', read_reference)
    clock = iter([0., 601. if incident == 'timeout' else 121. if incident == 'inactivity' else 1., 601.])
    monkeypatch.setattr(probe.time, 'monotonic', lambda: next(clock))
    monkeypatch.setattr(probe.time, 'sleep', lambda _: None)
    class Job:
        def __init__(self, memory): assert memory == 24*(1 << 30)
        def launch(self, command, *, cwd, env, stdout, stderr):
            assert command[3] == 'docs.reference_cases.ge_beam3_fibre_arch_six_probe'
            assert '--worker' in command and all(env[k] == v for k, v in probe.THREAD_ENVIRONMENT.items())
            assert command[command.index('--macros')+1] == str(macros)
            root = Path(stdout.name).parent; made = probe.ready(checkpoint, reference, REVISION, macros=macros)
            if incident == 'partial': made['rows'].pop()
            (root/'checkpoint-diagnostic.json').write_bytes(checkpoint+b' ' if incident == 'hash' else checkpoint)
            (root/'comparison.pending.json').write_bytes(probe.audit.canonical(made))
            return self
        def accounting(self):
            return (0 if incident == 'inactivity' else 1, 1 if incident == 'descendant_alive' else 0,
                    24*(1 << 30) if incident == 'memory' else 1)
        def poll(self): return 1 if incident == 'exit' else 0
        def terminate(self): calls.append('terminate'); return incident != 'cleanup_uncertain'
        def close(self): calls.append('close')
    monkeypatch.setattr(probe, '_ProcessJob', Job)
    output = tmp_path/'fresh'
    if incident == 'success':
        probe.run(REVISION, output, macros=macros)
        assert (output/'comparison.json').read_bytes() == (output/'comparison.pending.json').read_bytes()
        with pytest.raises(FileExistsError): probe.run(REVISION, output, macros=macros)
    else:
        with pytest.raises((ValueError, RuntimeError)): probe.run(REVISION, output, macros=macros)
        assert not (output/'comparison.json').exists()
    assert calls.count('terminate') == calls.count('close') == 1
    assert calls.index('terminate') < calls.index('close')
    if incident == 'success': assert calls.index('close') < len(calls)-1


def test_twelve_scope_has_distinct_schema_and_rejects_six_records(monkeypatch):
    checkpoint, reference = data(monkeypatch, 12)
    value = probe.ready(checkpoint, reference, REVISION, macros=12)
    assert value['schema'] == 'GE_BEAM3_TWELVE_MACRO_PRESERVED_REFERENCE_LOAD_DIAGNOSTIC_V1'
    assert value['macros'] == 12 and not value['production_qualified']
    assert [r['twelve_macro_relative_load_error'] for r in value['rows']] == [.05]*4
    with pytest.raises(ValueError): probe.ready(checkpoint, reference, REVISION)
    for bad in (True, 12., 8, 24):
        with pytest.raises(ValueError): probe.checked_macros(bad)
