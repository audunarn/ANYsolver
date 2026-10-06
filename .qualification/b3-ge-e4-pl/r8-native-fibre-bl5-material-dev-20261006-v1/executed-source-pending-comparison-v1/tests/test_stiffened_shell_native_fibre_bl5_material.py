"""Focused DEV coverage of the explicit force-controlled Q4 native material BL5 policy."""
from dataclasses import replace
import json
import numpy as np
import pytest
from anysolver import stiffened_shell as ss
from anysolver.control import CancellationToken, SolveCancelled
from anysolver._stiffened_shell_ge_finite_experimental import FinitePointDriver
from examples.stiffened_shell_native_fibre_bl5_material import definition, ACTIONS, CONTROLS


def make(request, model):
    owner = ss.create_analysis(definition=model)
    request.addfinalizer(owner.close)
    return owner


def test_policy_admission_and_force_only_refusals(request):
    model = definition()
    a = make(request, model)
    assert a.capabilities['analysis'][-1] == 'experimental_native_fibre_material_bl5'
    assert 'shell J2 plastic' not in a.capabilities['excluded']
    assert a.capabilities['retained_coordinate_scale_policy'] == 'native_force_moment_roles_v1'
    start = a._shell_count+6*len(a._beam_ids)
    from anysolver._stiffened_shell_ge_experimental import _reference_section_tangent
    for i, (element, _, _) in enumerate(a._beam_parts):
        scale = np.abs(_reference_section_tangent(element.section))@np.r_[np.ones(3), np.ones(3)/a._reference_length]
        expected = np.r_[np.tile(scale[:3], 2), np.tile(scale[3:], 4)]
        np.testing.assert_array_equal(a._coordinate_scale[start+24*i+6:start+24*i+24], expected)
    assert not a.native_line_buckling_capabilities['definition_admitted']
    for bad in (replace(model, lines=()), replace(model, bl5_material_policy='elastic'),
                replace(model, bl5_material_policy=ss.BL5_ELASTIC_NATIVE_FIBRE_V1),
                replace(model, shell=replace(model.shell, s3_elements=((1, 2, 6),)))):
        with pytest.raises(ValueError):
            ss.create_analysis(definition=bad)
    before = a._generation
    programme = ss.StagedDeadLoadProgramme(a.preflight()['identity'], (ACTIONS, ACTIONS))
    with pytest.raises(ValueError, match='force-controlled'):
        a.solve(programme)
    with pytest.raises(ValueError, match='force-controlled'):
        a.solve(ACTIONS, displacement_control=object())
    with pytest.raises(ValueError, match='force-controlled'):
        a.continue_arc_length(ACTIONS, object())
    with pytest.raises(ValueError, match='spectra'):
        a.buckling(ss.GENativeLineBucklingRequest(1))
    assert a._generation == before and a._finite_driver is None


def test_policy_restore_load_and_envelope_refusals_are_atomic(request):
    from anysolver._stiffened_shell_ge_experimental import CHECKPOINT, CHART_CHECKPOINT_MAGIC
    from anysolver._stiffened_shell_staged_load_experimental import MAGIC as STAGED_MAGIC
    from anysolver._stiffened_shell_ge_distributed_load import MAGIC as DISTRIBUTED_MAGIC
    from anysolver._stiffened_shell_ge_distributed_programme import MAGIC as PROGRAMME_MAGIC
    model = definition(shell_material=False)
    a = make(request, model)
    zero = dict(schema=CHECKPOINT, model=a.preflight()['identity'], generation=1,
                q=np.zeros(a._K.shape[0]).tolist(), multipliers=np.zeros(a._C.shape[0]).tolist(),
                load=np.zeros(a._K.shape[0]).tolist())
    accepted = a.restore(json.dumps(zero).encode())
    saved = a.checkpoint()
    fixed_rotation = next(int(i) for i in a._fixed if int(i) % 6 >= 3 and int(i) < a._shell_count)
    moment = dict(zero, load=list(zero['load']))
    moment['load'][fixed_rotation] = 1.
    fresh = make(request, model)
    with pytest.raises(ValueError, match='nodal dead translations'):
        fresh.restore(json.dumps(moment).encode())
    assert fresh._generation == 0 and fresh._accepted is None and fresh._finite_driver is None
    # The excluded moment is mechanically consistent: it is a support reaction.
    legacy = make(request, replace(model, bl5_material_policy=ss.BL5_ELASTIC_NATIVE_FIBRE_V1))
    legacy.restore(json.dumps(dict(moment, model=legacy.preflight()['identity'])).encode())
    assert legacy._generation == 1
    retained = dict(zero, load=list(zero['load']))
    retained['load'][a._shell_count+6*len(a._beam_ids)] = 1.
    with pytest.raises(ValueError, match='nodal dead translations'):
        fresh.restore(json.dumps(retained).encode())
    # Admission is intentionally before envelope decoding/compilation. The
    # inner payload cannot widen this policy, even if a historical codec accepts it.
    for magic in (CHART_CHECKPOINT_MAGIC, STAGED_MAGIC, DISTRIBUTED_MAGIC, PROGRAMME_MAGIC):
        with pytest.raises(ValueError, match='force-controlled scope excludes'):
            fresh.restore(magic+b'payload must not be decoded')
        assert fresh._generation == 0 and fresh._accepted is None and fresh._finite_driver is None
        with pytest.raises(RuntimeError, match='fresh'):
            a.restore(magic+b'payload must not be decoded')
        assert a._generation == accepted.generation and a.checkpoint() == saved


@pytest.mark.parametrize('shell_material', (False, True))
def test_native_material_lifecycle_and_fixed_predecessor_tangent(request, monkeypatch, tmp_path, shell_material):
    model = definition(shell_material=shell_material)
    a = make(request, model)
    inventories = []
    def observe(result):
        assert result.free_equilibrium_ratio <= 1e-8 and result.constraint_max <= 1e-9
        inventories.append(dict(factor=result.load_factor,
                                shell=np.asarray(result.shell_layer_alpha).tolist(),
                                beams=np.asarray(result.beam_station_accumulated).tolist()))
    prefix = a.solve(ACTIONS, (.5, 1.), on_accepted=observe, **CONTROLS)
    assert prefix.load_factor == 1.
    assert np.max(prefix.beam_station_accumulated) > 0.
    assert np.max(prefix.beam_station_accumulated[0]) > 0.
    assert prefix.beam_fibre_material and prefix.beam_fibre_energy and prefix.beam_shell_line_work
    assert all(len(slots) == 42 for _, slots, _ in a._beam_parts)
    assert prefix.beam_generalized_material
    assert not prefix.beam_fibre_material[0].strain.flags.writeable
    with pytest.raises(ValueError):
        prefix.beam_fibre_material[0].strain[0] += 1.
    if shell_material:
        assert np.max(prefix.shell_layer_alpha) > 0.
        assert prefix.shell_q4_material
        prior_shell = np.zeros_like(inventories[0]['shell'])
        prior_fibre = np.zeros_like(inventories[0]['beams'][-1])
        simultaneous = []
        for item in inventories:
            shell = np.asarray(item['shell']); fibre = np.asarray(item['beams'][-1])
            simultaneous.append(dict(factor=item['factor'], shell_advancing=int(np.count_nonzero(shell > prior_shell)),
                                     fibre_advancing=int(np.count_nonzero(fibre > prior_fibre))))
            prior_shell, prior_fibre = shell, fibre
        assert any(item['shell_advancing'] and item['fibre_advancing'] for item in simultaneous), simultaneous
    saved = a.checkpoint()
    (tmp_path/'accepted-prefix.bin').write_bytes(saved)
    driver = a._finite_driver
    state = driver._state
    def evaluate(trial):
        return driver._assemble(trial, 1., driver._shell_predecessors,
                                driver._beam_predecessors, pattern=driver._pattern)
    base_evaluation = evaluate(state)
    residual, tangent, *_ = base_evaluation
    def activity(evaluation):
        shell = tuple(tuple(np.asarray(candidate['alpha']) > np.asarray(origin['alpha']))
                      for candidate, origin in zip(evaluation[4], driver._shell_predecessors)) if shell_material else ()
        beam = []
        for candidate, origin in zip(evaluation[5], driver._beam_predecessors):
            for after, before in zip(candidate.stations, origin.stations):
                if hasattr(after, 'rows'):
                    beam.extend(float(row[2]+row[3]) > float(old[2]+old[3]) for row, old in zip(after.rows, before.rows))
                else:
                    beam.append(sum(after.accumulated) > sum(before.accumulated))
        return shell, tuple(beam)
    branch = activity(base_evaluation)
    assert any(branch[1])
    if shell_material:
        assert any(any(row) for row in branch[0])
    direction = np.zeros(len(residual))
    direction[:a._shell_count:6] = np.linspace(0., 1e-4, len(a._shell_ids))
    direction[3:a._shell_count:6] = np.linspace(0., 2e-4, len(a._shell_ids))
    direction[4:a._shell_count:6] = np.linspace(0., -3e-4, len(a._shell_ids))
    for i in range(len(a._beam_ids)):
        direction[a._shell_count+6*i+2] = .001*(i+1)
        direction[a._shell_count+6*i+3:a._shell_count+6*i+6] = (2e-4, -1e-4, 3e-4)
    retained = a._shell_count+driver._beam_nodal
    for i in range(len(a._beam_parts)):
        direction[retained+24*i:retained+24*i+6] = (2e-4, -3e-4, 1e-4, -2e-4, 1e-4, 3e-4)
        direction[retained+24*i+6:retained+24*i+24] = a._coordinate_scale[retained+24*i+6:retained+24*i+24]*1e-4
    direction[len(state.q):] = np.linspace(1., 2., len(state.multipliers))
    direction[a._fixed] = 0.
    expected = tangent@direction
    weights = np.r_[a._coordinate_scale, np.ones(a._C.shape[0])]
    errors = []
    for h in (1e-4, 1e-5, 1e-6):
        positive = evaluate(driver._advance(state, direction, h))
        negative = evaluate(driver._advance(state, direction, -h))
        assert activity(positive) == activity(negative) == branch
        plus, minus = positive[0], negative[0]
        errors.append(np.linalg.norm(((plus-minus)/(2*h)-expected)*weights)/max(np.linalg.norm(expected*weights), 1.))
    assert max(errors[1:]) <= 1e-5, errors
    (tmp_path/'lifecycle.json').write_text(json.dumps(dict(inventories=inventories, tangent_errors=errors,
                                                       simultaneous=simultaneous if shell_material else []), indent=2))
    assert a.checkpoint() == saved
    original = FinitePointDriver._assemble
    midtrial = CancellationToken()
    def cancel_trial(self, *args, **kwargs):
        value = original(self, *args, **kwargs)
        midtrial.cancel('after trial assembly before atomic publication')
        return value
    with monkeypatch.context() as patch:
        patch.setattr(FinitePointDriver, '_assemble', cancel_trial)
        with pytest.raises(SolveCancelled):
            a.solve(ACTIONS, (1.1,), cancellation_token=midtrial, **CONTROLS)
    assert a.checkpoint() == saved
    from anysolver._stiffened_shell_increment_control import FiniteIncrementFailure
    with pytest.raises(FiniteIncrementFailure) as rejected:
        a.solve(ACTIONS, (1.1,), max_iterations=1, max_backtracks=0)
    assert rejected.value.attempt.status == 'rejected'
    assert a.checkpoint() == saved
    def failed_trial(self, *args, **kwargs):
        original(self, *args, **kwargs)
        raise RuntimeError('injected local material trial failure')
    with monkeypatch.context() as patch:
        patch.setattr(FinitePointDriver, '_assemble', failed_trial)
        with pytest.raises(RuntimeError, match='injected local'):
            a.solve(ACTIONS, (1.1,), **CONTROLS)
    assert a.checkpoint() == saved
    from anysolver._ge_beam3_retained_fibre import RetainedFibreOperator
    calls = []
    def refuse_mutated_inventory(self):
        calls.append(1)
        raise ValueError('captured retained fibre reference changed')
    with monkeypatch.context() as patch:
        patch.setattr(RetainedFibreOperator, 'guard', refuse_mutated_inventory)
        with pytest.raises(ValueError, match='captured retained fibre'):
            a.solve(ACTIONS, (1.1,), **CONTROLS)
    assert len(calls) == 1 and a.checkpoint() == saved
    cancelled = CancellationToken()
    cancelled.cancel('before candidate publication')
    with pytest.raises(SolveCancelled):
        a.solve(ACTIONS, (1.1,), cancellation_token=cancelled, **CONTROLS)
    assert a.checkpoint() == saved
    with pytest.raises(ValueError):
        a.rebase_rotations(prefix.generation-1)
    assert a.checkpoint() == saved
    fresh = make(request, model)
    restored = fresh.restore(saved)
    assert fresh.checkpoint() == saved
    for left, right in zip(prefix.beam_fibre_material, restored.beam_fibre_material):
        np.testing.assert_array_equal(left.strain, right.strain)
        np.testing.assert_array_equal(left.resultants, right.resultants)
    if shell_material:
        for left, right in zip(prefix.shell_q4_material, restored.shell_q4_material):
            np.testing.assert_array_equal(left.alpha, right.alpha)
            np.testing.assert_array_equal(left.layer_stress, right.layer_stress)
    legacy = make(request, replace(model, shell=replace(model.shell, j2_curve=None),
                                  bl5_material_policy=ss.BL5_ELASTIC_NATIVE_FIBRE_V1))
    with pytest.raises(ValueError):
        legacy.restore(saved)
    assert legacy._finite_driver is None
    corrupt = make(request, model)
    with pytest.raises(ValueError):
        corrupt.restore(saved[:-1]+bytes((saved[-1]^1,)))
    assert corrupt._finite_driver is None
    final = a.solve(ACTIONS, (1.1,), **CONTROLS)
    resumed = fresh.solve(ACTIONS, (1.1,), **CONTROLS)
    assert final.status == resumed.status == 'completed'
    assert final.free_equilibrium_ratio <= 1e-8 and final.constraint_max <= 1e-9
    assert a.checkpoint() == fresh.checkpoint()
