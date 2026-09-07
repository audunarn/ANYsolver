"""Disposable supervisor mocks: no native solves or reference generation."""
from pathlib import Path
from hashlib import sha256
import pytest
from docs.reference_cases import ge_beam3_arch_field_probe as probe


@pytest.mark.parametrize('incident', ['success', 'exit', 'memory', 'timeout', 'inactivity',
    'invalid', 'cleanup_uncertain', 'descendant_alive', 'mutation_after_cleanup', 'inputs_changed'])
def test_job_cleanup_and_validation_precede_canonical_publication(tmp_path, monkeypatch, incident):
    calls = []; packet = b'{"diagnostic":true}\n'; ticks = iter([0., 601. if incident == 'timeout' else 121. if incident == 'inactivity' else 1., 601.])
    monkeypatch.setattr(probe.time, 'monotonic', lambda: next(ticks))
    monkeypatch.setattr(probe.time, 'sleep', lambda _: None)
    monkeypatch.setattr(probe, 'guard', lambda revision: calls.append('guard'))
    reads = 0
    def inputs():
        nonlocal reads
        reads += 1
        if incident == 'inputs_changed' and reads > 1: raise ValueError('input mutation')
        return {}, {}
    monkeypatch.setattr(probe, 'inputs', inputs)
    def validate(raw, detail, revision, packets):
        calls.append('validate')
        assert raw == detail == packet
        if incident == 'invalid': raise ValueError('invalid staged result')
    monkeypatch.setattr(probe, 'validate', validate)
    class Job:
        def __init__(self, memory): assert memory == 24*(1 << 30)
        def launch(self, command, *, cwd, env, stdout, stderr):
            assert command[3] == 'docs.reference_cases.ge_beam3_arch_field_probe'
            assert all(env[k] == v for k, v in probe.THREAD_ENVIRONMENT.items())
            assert 'PYTHONPATH' not in env
            self.root = Path(stdout.name).parent
            for name in ('comparison.pending.json','fields-diagnostic.json'): (self.root/name).write_bytes(packet)
            return self
        def accounting(self):
            return (0 if incident == 'inactivity' else 1, 1 if incident == 'descendant_alive' else 0,
                    24*(1 << 30) if incident == 'memory' else 1)
        def poll(self): return 1 if incident == 'exit' else 0
        def terminate(self):
            calls.append('terminate')
            if incident == 'mutation_after_cleanup': (self.root/'fields-diagnostic.json').write_bytes(packet+b' ')
            return incident != 'cleanup_uncertain'
        def close(self): calls.append('close')
    monkeypatch.setattr(probe, '_ProcessJob', Job)
    output = tmp_path/'fresh'
    if incident == 'success':
        probe.run('1'*40, output)
        assert (output/'comparison.json').read_bytes() == packet
        with pytest.raises(FileExistsError): probe.run('1'*40, output)
    else:
        with pytest.raises((ValueError, RuntimeError)): probe.run('1'*40, output)
        assert not (output/'comparison.json').exists()
    assert calls.count('terminate') == calls.count('close') == 1
    assert calls.index('terminate') < calls.index('close')


@pytest.mark.parametrize('raw', [b'',b'{"x":1,"x":2}\n',b'{"x":NaN}\n',b'{"x":Infinity}\n',b' {"x":1}\n'])
def test_diagnostic_encoding_rejects_duplicates_nonfinite_and_noncanonical(raw):
    with pytest.raises(ValueError): probe.parse_diagnostics(raw)


@pytest.fixture
def completed_fields():
    root = probe.EXTERNAL/'ge-beam3-arch-fields-20260907-v1'
    paths = [root/'comparison.json', root/'fields-diagnostic.json']
    paths += [probe.EXTERNAL/f'ge-beam3-fibre-arch{m}-20260907-v1/checkpoint-diagnostic.json' for m in (6, 12)]
    if any(not p.is_file() for p in paths):
        pytest.skip('External development fields not installed; not qualification evidence')
    raw, details = paths[0].read_bytes(), paths[1].read_bytes()
    assert sha256(raw).hexdigest() == '5902c40f7e9f0fa203a6e8a61d24ea65dba11ac7c4b3436b67242dbbd83f09b9'
    assert sha256(details).hexdigest() == '796d3b390daf986212067c78dde2e451d41fe7bcb1e3d0d5f7354c7b98cfe8d2'
    return raw, details, probe.inputs()[0]


def test_real_saved_field_metrics_recompute_without_reference_or_native_solve(completed_fields):
    raw, details, packets = completed_fields
    value = probe.validate(raw, details, '521327e7f0d1615eba238f950312995378f415fe', packets)
    assert len(value['rows']) == 8
    assert sum(r['station_recovery']['stations'] for r in value['rows']) == 576


@pytest.mark.parametrize('mutation', ['summary', 'recovery', 'reference', 'qualification', 'order'])
def test_real_field_or_summary_mutations_reject(completed_fields, mutation):
    raw, details, packets = completed_fields
    value = probe.audit.parse(raw); data = probe.parse_diagnostics(details)
    if mutation == 'summary': value['rows'][0]['station_recovery']['native_integrated_energy'] += 1.
    if mutation == 'recovery': data['recoveries'][0]['fields'][0]['stations'][0]['strain'][0] += .1
    if mutation == 'reference': data['recoveries'][0]['reference_fields']['force'][0][0] += 1.
    if mutation == 'qualification': value['production_qualified'] = True
    if mutation == 'order': value['rows'].reverse()
    changed = probe.audit.canonical(data)
    value['diagnostics_sha256'] = sha256(changed).hexdigest()
    with pytest.raises(ValueError):
        probe.validate(probe.audit.canonical(value), changed, '521327e7f0d1615eba238f950312995378f415fe', packets)
