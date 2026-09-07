"""Disposable process-control mocks; no real subprocess or resource request."""
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pytest
from docs.reference_cases import ge_beam3_fibre_arch_probe as probe


REVISION = '1'*40


def ready():
    def row(target):
        return dict(displacement=target, native_load=1., reference_load=1., load_relative_error=0.,
            nodal_position_error=0., nodal_frame_error=0., stiffness_scale=1.e6, reference_energy=0.,
            reference_load_slope=1., reference_profile='BVP9',
            same_equilibrium_branch_proved=False, mechanics_replayed=True, production_qualified=False,
            geometry=dict(position_reflection_error=0., out_of_plane_position=0.,
                nodal_frame_reflection_error=0., cell_rotation_reflection_error=0., physical_second_director_error=0.),
            reference_errors_normalized=dict(boundary=0., differential=0., sensitivity=0., work=0.))
    return dict(schema='GE_BEAM3_FOUR_MACRO_ARCH_DEVELOPMENT_V1', revision=REVISION, macros=4,
        checkpoint_sha256=sha256(b'checkpoint').hexdigest(),
        rows=[row(v) for v in (.01, .025, .04, .055)],
        production_qualified=False, independent_review='PENDING', runtime_version_check_only=True)


def synthetic_comparison(monkeypatch, work):
    from docs.reference_cases import ge_beam3_fibre_arch_comparison as comparison
    # No native assembly or BVP. Use the actual comparator on a synthetic pose.
    monkeypatch.setattr(comparison.continuum, 'solve', lambda *a, **k: pytest.fail('No BVP permitted'))
    x = np.linspace(-1., 0., 129)
    reference = SimpleNamespace(displacement=.01, load=.0001, load_slope=.002, profile='BVP9',
        strain_energy=1e-6, boundary_error=0., differential_error=1e-10, sensitivity_error=2e-10,
        work_error=work, parameter=x, fields=np.array([x, .1*(1-x*x), np.arctan(-.2*x), 0.*x]))
    nodes = np.linspace(-1., 1., 9)
    positions, frames = comparison.sampled_geometry(reference, nodes)
    mechanical = dict(positions=positions.tolist(), position_low=np.zeros((9, 3)).tolist(),
        nodal_frames=frames.tolist(), cell_rotations=np.tile(np.eye(3), (4, 2, 1, 1)).tolist())
    row = dict(displacement_target=.01, parameter=100., mechanical=mechanical)
    return comparison.compare(row, nodes, 1e6, reference)


@pytest.mark.parametrize('work', [np.float64(0.), np.float64(8.80643214601351e-17),
                                  np.nextafter(np.float64(0.), np.float64(1.))])
def test_comparator_converts_numpy_work_scalar_without_changing_json(monkeypatch, work):
    made = synthetic_comparison(monkeypatch, work)
    assert type(made['reference_errors_normalized']['work']) is float
    assert np.float64(made['reference_errors_normalized']['work']).tobytes() == work.tobytes()
    old = {**made, 'reference_errors_normalized': {**made['reference_errors_normalized'], 'work': work}}
    assert probe.canonical(made) == probe.canonical(old)
    # Pre-correction in-memory scalar is rejected despite identical JSON bytes.
    packet = ready(); old['mechanics_replayed'] = True; packet['rows'][0] = old
    with pytest.raises(ValueError, match='finite diagnostic fields'): probe.validate_ready(packet, REVISION)
    made['mechanics_replayed'] = True; packet['rows'][0] = made
    probe.validate_ready(packet, REVISION)


@pytest.mark.parametrize('work', [np.float64(float('nan')), np.float64(float('inf')), np.float64(-.1)])
def test_work_scalar_conversion_does_not_relax_finite_nonnegative_guard(monkeypatch, work):
    made = synthetic_comparison(monkeypatch, work); made['mechanics_replayed'] = True
    packet = ready(); packet['rows'][0] = made
    with pytest.raises(ValueError): probe.validate_ready(packet, REVISION)


@pytest.mark.parametrize('incident', ['target', 'partial', 'extra', 'qualified', 'revision', 'row', 'nan', 'negative'])
def test_partial_or_wrong_ready_packet_is_rejected(incident):
    value = ready()
    if incident == 'target': value['rows'][0]['displacement'] = .02
    elif incident == 'partial': value['rows'].pop()
    elif incident == 'extra': value['extra'] = True
    elif incident == 'qualified': value['production_qualified'] = True
    elif incident == 'row': value['rows'][0].pop('native_load')
    elif incident == 'nan': value['rows'][0]['native_load'] = float('nan')
    elif incident == 'negative': value['rows'][0]['geometry']['position_reflection_error'] = -.1
    else: value['revision'] = '0'*40
    with pytest.raises(ValueError): probe.validate_ready(value, REVISION)


@pytest.mark.parametrize('incident', ['success', 'exit', 'memory', 'timeout', 'inactivity', 'malformed', 'hash'])
def test_process_exit_and_limits_control_exclusive_publication(tmp_path, monkeypatch, incident):
    monkeypatch.setattr(probe, 'guard', lambda revision: None)
    clock = iter([0., 601. if incident == 'timeout' else 121. if incident == 'inactivity' else 1.])
    monkeypatch.setattr(probe.time, 'monotonic', lambda: next(clock))
    events = []
    class Job:
        def __init__(self, limit): assert limit == 24*(1 << 30)
        def launch(self, command, *, cwd, env, stdout, stderr):
            assert '--worker' in command and all(env[k] == v for k, v in probe.THREAD_ENVIRONMENT.items())
            root = Path(stdout.name).parent
            value = ready()
            if incident == 'malformed': value['rows'].pop()
            (root/'comparison.pending.json').write_bytes(probe.canonical(value))
            (root/'checkpoint-diagnostic.json').write_bytes(b'changed' if incident == 'hash' else b'checkpoint')
            return self
        def accounting(self):
            return (0 if incident == 'inactivity' else 1, 0, 24*(1 << 30) if incident == 'memory' else 1)
        def poll(self): return 2 if incident == 'exit' else 0
        def terminate(self): events.append('terminated'); return True
        def close(self): events.append('closed')
    monkeypatch.setattr(probe, '_ProcessJob', Job)
    output = tmp_path/'exclusive'
    if incident == 'success':
        probe.run(REVISION, output)
        assert (output/'comparison.json').read_bytes() == (output/'comparison.pending.json').read_bytes()
        with pytest.raises(FileExistsError): probe.run(REVISION, output)
    else:
        with pytest.raises((RuntimeError, ValueError)): probe.run(REVISION, output)
        assert not (output/'comparison.json').exists()
    assert events == ['terminated', 'closed']
    assert (output/'checkpoint-diagnostic.json').is_file()
