"""Source-bound public loaded/clamped acceleration-chart split restart control."""
from dataclasses import asdict
from fractions import Fraction
from hashlib import sha256
import json
import os
from pathlib import Path
from time import perf_counter
from types import SimpleNamespace

import numpy as np
import pytest

from anysolver.boundary import BoundaryCondition
from anysolver.ge_beam3_native import LinePattern, DistributedPattern
from anysolver.ge_beam3_native_dynamics import create_analysis, SELECTOR, workflow_provenance
from anysolver._ge_beam3_p5_seeded.core import canonical, sha
from test_ge_beam3_native_midpoint import make_analysis
from native_forced_response_reference import line_stations, load_map, path_accounting, positions, position_delta
from native_clamped_response_reference import reaction_wrench


CRITERIA = dict(dt=.001, prefix_steps=2, continuation_steps=2, total_physical_steps=6,
    owners=2, internal_time_limit_seconds=120., stage_solve_tolerance=1e-12,
    stage_and_endpoint_limit=1e-11, correction_limit=1e-11, energy_momentum_limit=1e-6,
    witness_limit=1e-10, load_map_limit=1e-12, rotation_increment_limit=1e-3,
    observation_limit_per_trial=128, position_radius_limit=1.1, support_work_j=0.)


def payload(value):
    row = asdict(value)
    for key in ('rank_mass_checks', 'session_provenance'):
        if key in row:
            row[key] = json.loads(row[key])
    return json.loads(canonical(row))


def momentum_delta(now, before, name):
    return np.array([float(Fraction(float(h))+Fraction(float(l))-
                           Fraction(float(h0))-Fraction(float(l0)))
        for h, l, h0, l0 in zip(now[name+'_momentum'], now[name+'_momentum_low'],
            before[name+'_momentum'], before[name+'_momentum_low'])])


def test_public_loaded_clamped_acceleration_split_restart():
    started = perf_counter()
    spec = json.loads(Path(os.environ['NATIVE_LOADED_CLAMPED_RESTART_INPUTS']).read_bytes())
    assert spec['criteria'] == CRITERIA
    output = Path(spec['outputs']['raw'])
    journal = Path(spec['outputs']['stages'])
    assert not output.exists() and not journal.exists()
    journal.touch(exist_ok=False)
    evidence = dict(status='RUNNING', solver_committed_steps=0, gate_passing_steps=0,
        criteria=CRITERIA, scope='Public loaded/clamped acceleration restart routing, not temporal accuracy',
        stage_records=[], branches={}, negative_controls=[], owner_count=0)

    def save(stage):
        evidence.update(last_stage=stage, elapsed_seconds=perf_counter()-started)
        output.write_bytes(canonical(evidence))
        print(json.dumps(dict(stage=stage, elapsed_seconds=evidence['elapsed_seconds'],
            committed=evidence['solver_committed_steps'], gate_passing=evidence['gate_passing_steps'])), flush=True)
        assert evidence['elapsed_seconds'] < CRITERIA['internal_time_limit_seconds']

    def new_owner():
        _, definition = make_analysis()
        boundary = BoundaryCondition('homogeneous-root', [1],
            {key: 0. for key in ('ux', 'uy', 'uz', 'rx', 'ry', 'rz')})
        pattern = DistributedPattern(LinePattern(((1, .2, -.15, .1),)), ())
        owner = create_analysis(SELECTOR, (definition,), (boundary,), inertia_order=24,
            stage_residual_tolerance=CRITERIA['stage_solve_tolerance'], stage_coordinates='acceleration',
            load_pattern=pattern, momentum_origin_high=(0., 0., 0.), momentum_origin_low=(0., 0., 0.))
        evidence['owner_count'] += 1
        assert evidence['owner_count'] <= CRITERIA['owners']
        assert owner._context.runtime_limit_seconds == 120.
        assert owner._context.stage_coordinates == 'acceleration'
        assert owner._context.fixed == tuple(range(6))
        assert owner._context.physical_free == (6, 7, 8, 12, 13, 14, 18, 19, 20, 21, 22, 23)
        assert owner._context.algebraic_free == (9, 10, 11, 15, 16, 17, *range(24, 42))
        return owner, definition

    def fresh(owner):
        c = owner._context
        assert c.current is None and c._current is None and c._visible_current is None
        assert c._current_bytes is None and not c._issued and not c._candidates
        assert c._initial_checks is None and c._restore_checks is None
        assert c._dynamic._active_session is None and c._work_session is None
        assert len(c._dynamic._issued) == 1

    try:
        old = json.loads(Path(spec['historical']['clamped_raw']['path']).read_bytes())
        scales = old['resolutions']['coarse']['scales']
        assert scales == spec['scales'] and all(np.isfinite(v) and v > 0. for v in scales.values())
        evidence['scales'] = scales
        owner, definition = new_owner()
        c = owner._context
        reference = c._reference_mechanical
        assert canonical(json.loads(definition.raw)) == canonical(old['fixture']['definition'])
        assert canonical(reference) == canonical(old['fixture']['reference_mechanical'])
        assert canonical(c._reference_origins) == canonical(old['fixture']['virgin_history'])
        reference_points = positions(reference)
        rows = line_stations(reference_points)
        force = np.array((.2, -.15, .1))
        fixed_point, origin = reference_points[0], np.zeros(3)
        state = owner.initialize()
        initial = payload(owner.endpoint_accounting(state))
        evidence['initial'] = dict(state=json.loads(canonical(state)), accounting=initial,
            checks=owner.initial_checks, definition=json.loads(definition.raw), provenance=workflow_provenance(owner))
        assert np.count_nonzero(state.physical_velocity24) == 0
        assert canonical(state.mechanical) == canonical(reference)
        assert initial['total_energy'] == 0.
        save('virgin_consistent_initialization')

        def advance(active, prior, branch, index, cumulative):
            context = active._context
            before = payload(active.endpoint_accounting(prior))
            original = context._stage
            first = len(evidence['stage_records'])

            def observe(accepted, unknown, h, token=None):
                actual = original(accepted, unknown, h, token)
                row = dict(branch=branch, index=index, predecessor_sha256=sha(accepted),
                    predecessor_epoch=accepted.epoch, context_sha256=context._identity,
                    active_trial_session=context._work_session is not None,
                    unknown42=np.asarray(unknown).tolist(), stage=json.loads(canonical(actual)))
                encoded = canonical(row)
                with journal.open('ab') as stream:
                    offset = stream.tell(); stream.write(encoded); stream.flush()
                evidence['stage_records'].append(dict(offset=offset, length=len(encoded),
                    sha256=sha256(encoded).hexdigest(), branch=branch, index=index))
                assert len(evidence['stage_records'])-first <= CRITERIA['observation_limit_per_trial']
                return actual

            context._stage = observe
            try:
                candidate = active.trial(prior, dt=CRITERIA['dt'])
            finally:
                context._stage = original
                save(branch+'_trial_return_'+str(index))
            audit = active.candidate_stage_audit(candidate)
            load = active.physical_load_accounting(candidate.stage.mechanical)
            independent = load_map(positions(candidate.stage.mechanical), candidate.stage.mechanical.cell_rotations[0],
                rows, force, reference_points)
            load_errors = {key: float(np.linalg.norm(actual-expected)/np.linalg.norm(expected))
                for key, actual, expected in (
                    ('load', load.external_load42, independent['load42']),
                    ('tangent', load.external_spatial_jacobian42, independent['tangent42']))}
            # Data-only chart adapter for the independently reviewed pure path helper.
            # This is not an issued candidate and is never passed to any owner operation.
            path_data = SimpleNamespace(endpoint=candidate.endpoint, dt=candidate.dt, unknown42=audit.increment42)
            physical = path_accounting(prior.mechanical, path_data, rows, force, reference_points)
            reaction = audit.stage.residual[:6]
            support_force, support_moment = reaction_wrench(reaction, fixed_point, origin)
            support_p, support_h = candidate.dt*support_force, candidate.dt*support_moment
            mid_h = candidate.dt*load.moment_about_origin+support_h
            mid_work = float(candidate.dt*(load.external_load42[:24]@candidate.stage.physical_velocity24))
            support_work = float(reaction[:3]@position_delta(candidate.endpoint.mechanical, prior.mechanical)[0])
            record = dict(candidate=json.loads(canonical(candidate)), audit=payload(audit),
                load=payload(load), independent_load=json.loads(canonical(independent)),
                physical_path=json.loads(canonical(physical)), reaction6=reaction.tolist(),
                support_force_n=support_force.tolist(), support_moment_nm=support_moment.tolist(),
                support_work_j=support_work, load_errors=load_errors)
            evidence['branches'].setdefault(branch, []).append(record)
            save(branch+'_candidate_before_gates_'+str(index))
            for mechanical in (candidate.stage.mechanical, candidate.endpoint.mechanical):
                assert np.array_equal(mechanical.positions[0], reference.positions[0])
                assert np.array_equal(mechanical.position_low[0], reference.position_low[0])
                assert np.array_equal(mechanical.nodal_frames[0], reference.nodal_frames[0])
            assert np.count_nonzero(audit.increment42[:6]) == 0
            for vector in (candidate.stage.physical_velocity24, candidate.stage.physical_acceleration24,
                           candidate.endpoint.physical_velocity24, candidate.endpoint.physical_acceleration24):
                assert np.count_nonzero(vector[:6]) == 0
                assert np.count_nonzero(vector[[3, 4, 5, 9, 10, 11, 15, 16, 17]]) == 0
            assert support_work == 0.
            algebraic = [3, 4, 5, 9, 10, 11, 15, 16, 17, *range(24, 42)]
            assert np.count_nonzero(audit.stage.inertia.mixed_inertia[algebraic]) == 0
            assert np.count_nonzero(audit.stage.inertia.mixed_mass[algebraic]) == 0
            assert np.count_nonzero(audit.stage.inertia.mixed_mass[:, algebraic]) == 0
            assert max(load_errors.values()) <= CRITERIA['load_map_limit']
            assert candidate.stage_residual_norm <= CRITERIA['stage_and_endpoint_limit']
            assert candidate.endpoint_algebraic_norm <= CRITERIA['stage_and_endpoint_limit']
            assert max(np.linalg.norm(p) for p in positions(candidate.endpoint.mechanical)) <= CRITERIA['position_radius_limit']
            assert max(np.linalg.norm(p) for p in audit.increment42[18:24].reshape(2, 3)) < CRITERIA['rotation_increment_limit']
            current = active.commit(candidate)
            evidence['solver_committed_steps'] += 1
            now = payload(active.endpoint_accounting(current))
            cumulative['P'] += physical['linear_impulse']+support_p
            cumulative['H_path'] += physical['angular_impulse']+support_h
            cumulative['H_midpoint'] += mid_h
            cumulative['E_exact'] += physical['exact_work']
            cumulative['E_midpoint'] += mid_work
            defects = dict(P=float(np.linalg.norm(momentum_delta(now, before, 'linear')-physical['linear_impulse']-support_p)/scales['momentum']),
                H_path=float(np.linalg.norm(momentum_delta(now, before, 'angular')-physical['angular_impulse']-support_h)/scales['angular_momentum']),
                H_midpoint=float(np.linalg.norm(momentum_delta(now, before, 'angular')-mid_h)/scales['angular_momentum']),
                E_exact=abs(now['total_energy']-before['total_energy']-physical['exact_work'])/scales['energy'],
                E_midpoint=abs(now['total_energy']-before['total_energy']-mid_work)/scales['energy'])
            total = dict(P=float(np.linalg.norm(momentum_delta(now, initial, 'linear')-cumulative['P'])/scales['momentum']),
                H_path=float(np.linalg.norm(momentum_delta(now, initial, 'angular')-cumulative['H_path'])/scales['angular_momentum']),
                H_midpoint=float(np.linalg.norm(momentum_delta(now, initial, 'angular')-cumulative['H_midpoint'])/scales['angular_momentum']),
                E_exact=abs(now['total_energy']-initial['total_energy']-cumulative['E_exact'])/scales['energy'],
                E_midpoint=abs(now['total_energy']-initial['total_energy']-cumulative['E_midpoint'])/scales['energy'])
            record.update(state=json.loads(canonical(current)), accounting=now, step_defects=defects,
                cumulative_defects=total, cumulative=json.loads(canonical(cumulative)))
            save(branch+'_committed_before_energy_gates_'+str(index))
            assert max(defects.values()) <= CRITERIA['energy_momentum_limit']
            assert max(total.values()) <= CRITERIA['energy_momentum_limit']
            assert now['elastic_consistency_witness']/scales['energy'] <= CRITERIA['witness_limit']
            assert canonical(current.histories) == canonical(c._reference_origins)
            evidence['gate_passing_steps'] += 1
            save(branch+'_gate_pass_'+str(index))
            return current

        cumulative = dict(P=np.zeros(3), H_path=np.zeros(3), H_midpoint=np.zeros(3), E_exact=0., E_midpoint=0.)
        for index in (1, 2):
            state = advance(owner, state, 'prefix', index, cumulative)
        prefix_cumulative = {key: value.copy() if isinstance(value, np.ndarray) else value for key, value in cumulative.items()}
        raw = owner.create_checkpoint()
        evidence['checkpoint_ascii'] = raw.decode('ascii')
        evidence['checkpoint_sha256'] = sha256(raw).hexdigest()
        evidence['prefix_accounting'] = payload(owner.endpoint_accounting(state))
        save('official_prefix_checkpoint')
        restored, restored_definition = new_owner()
        fresh(restored)
        assert canonical(json.loads(restored_definition.raw)) == canonical(json.loads(definition.raw))
        for label, change in (
            ('incompatible_chart', lambda row: row['header']['settings'].__setitem__('stage_coordinates', 'increment')),
            ('incompatible_load', lambda row: row['header'].__setitem__('constant_load_pattern', None)),
            ('incompatible_support', lambda row: row['header'].__setitem__('fixed', []))):
            row = json.loads(raw); change(row)
            row['checkpoint_sha256'] = sha({key: value for key, value in row.items() if key != 'checkpoint_sha256'})
            invalid = canonical(row)
            control = dict(label=label, checkpoint_ascii=invalid.decode('ascii'), sha256=sha256(invalid).hexdigest())
            with pytest.raises(ValueError, match='header/body authority mismatch') as rejected:
                restored.restore_checkpoint(invalid, expected_sha256=control['sha256'])
            fresh(restored)
            control['exception'] = str(rejected.value)
            evidence['negative_controls'].append(control)
            save(label+'_rejected_before_publication')
        restored_state = restored.restore_checkpoint(raw, expected_sha256=evidence['checkpoint_sha256'])
        assert restored.current is restored_state and restored_state is not state
        assert canonical(restored_state) == canonical(state)
        assert restored.create_checkpoint() == raw
        assert canonical(restored.initial_checks) == canonical(owner.initial_checks)
        assert canonical(payload(restored.endpoint_accounting(restored_state))) == canonical(evidence['prefix_accounting'])
        evidence['restore_checks'] = restored.restore_checks
        assert evidence['restore_checks']['algebraic_residual_norm'] <= CRITERIA['stage_and_endpoint_limit']
        assert evidence['restore_checks']['algebraic_correction_norm'] <= CRITERIA['correction_limit']
        assert evidence['restore_checks']['physical_balance_norm'] <= CRITERIA['stage_and_endpoint_limit']
        save('matching_fresh_official_restore')
        for index in (3, 4):
            state = advance(owner, state, 'direct', index, cumulative)
        restored_cumulative = prefix_cumulative
        for index in (3, 4):
            restored_state = advance(restored, restored_state, 'restored', index, restored_cumulative)
        evidence['parity'] = []
        for direct, split in zip(evidence['branches']['direct'], evidence['branches']['restored']):
            a, b = dict(direct), dict(split)
            a['audit'], b['audit'] = dict(a['audit']), dict(b['audit'])
            # Explicit evidence-only provenance is distinct; every other field is compared.
            a['audit'].pop('session_provenance'); b['audit'].pop('session_provenance')
            equal = canonical(a) == canonical(b)
            evidence['parity'].append(equal)
            assert equal
        assert owner.create_checkpoint() == restored.create_checkpoint()
        evidence['final_checkpoint_ascii'] = owner.create_checkpoint().decode('ascii')
        evidence['journal_sha256'] = sha256(journal.read_bytes()).hexdigest()
        evidence['journal_bytes'] = journal.stat().st_size
        assert evidence['solver_committed_steps'] == evidence['gate_passing_steps'] == 6
        evidence['status'] = 'PASS'
        save('complete')
    except BaseException as failure:
        evidence.update(status='NONPASS', exception_type=type(failure).__name__, exception=str(failure))
        evidence['journal_sha256'] = sha256(journal.read_bytes()).hexdigest()
        evidence['journal_bytes'] = journal.stat().st_size
        save('failure')
        raise
