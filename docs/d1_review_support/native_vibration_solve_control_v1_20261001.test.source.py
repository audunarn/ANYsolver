"""One free native vibration control, with shared spatial matrices as inputs.

No old temporal tests are executed. This scalar modal reference eliminates only
the algebraic coordinates and compares continuum and discrete midpoint time
separately. It does not independently qualify the spatial beam operator.
"""
from contextlib import contextmanager
from dataclasses import replace
from fractions import Fraction
from hashlib import sha256
import inspect
import json
import os
from pathlib import Path
from time import perf_counter

import numpy as np
import pytest

from anysolver.ge_beam3_native import create_analysis, SELECTOR, PROFILE_BYTES
from anysolver._ge_beam3_native_midpoint import MidpointContext, IMPLEMENTATION_ID
from anysolver._ge_beam3_centered_finite_inertia import PHYSICAL_DOFS, ALGEBRAIC_DOFS
from anysolver._ge_beam3_retained_generalized_state import Mechanical
from anysolver._ge_beam3_p5.algebra import rotation, log_rotation
from anysolver._ge_beam3_p5.compensated_coordinates import split_sum
from anysolver._ge_beam3_p5_seeded.core import canonical, sha
from anysolver._native_reference_modal import _owned
from test_ge_beam3_native_midpoint import make_analysis


def test_explicit_tighter_solve_with_authenticated_stage_impulse_audit(record_property):
    started = perf_counter()
    output = Path(os.environ['NATIVE_VIBRATION_RAW_OUTPUT'])
    assert not output.exists()
    p, z = list(PHYSICAL_DOFS), list(ALGEBRAIC_DOFS)
    inputs = json.loads(Path(os.environ['NATIVE_VIBRATION_INPUTS']).read_text(encoding='utf-8-sig'))
    historical = inputs['historical']
    for label in ('v2', 'v3', 'initial_forcing'):
        for kind in ('raw', 'input'):
            path = Path(historical[label+'_'+kind+'_path'])
            assert sha256(path.read_bytes()).hexdigest() == historical[label+'_'+kind+'_sha256']
    old = json.loads(Path(historical['v2_raw_path']).read_text())
    forcing = json.loads(Path(historical['initial_forcing_raw_path']).read_text())
    original = json.loads(Path(historical['v2_input_path']).read_text(encoding='utf-8-sig'))
    criteria = inputs['criteria']
    assert old['status'] == 'NONPASS' and old['accepted_steps_total'] == 2
    assert forcing['status'] == 'PASS' and forcing['time_steps'] == 0
    expected_criteria = dict(original['criteria'], amplitude=2.5e-5)
    assert criteria == expected_criteria
    assert inputs['maximum_new_steps'] == 20
    changed = inputs['source_impact']
    assert len(changed) == 1
    for path, expected in original['source_sha256'].items():
        if path in changed:
            assert changed[path]['historical_sha256'] == expected
            assert changed[path]['current_sha256'] == inputs['source_sha256'][path]
        else:
            assert inputs['source_sha256'][path] == expected
    assert inputs['stage_residual_tolerance'] == 1e-15
    evidence = dict(status='RUNNING', accepted_steps_total=0, criteria=criteria,
                    scope='One-mode small-motion temporal development; shared spatial input',
                    source_sha256=inputs['source_sha256'], historical=historical, resolutions={})

    def save(stage):
        evidence.update(last_stage=stage, elapsed_seconds=perf_counter()-started)
        output.write_text(json.dumps(evidence, indent=2)+'\n', encoding='utf-8')
        print(json.dumps(dict(stage=stage, elapsed_seconds=evidence['elapsed_seconds'])), flush=True)
        assert evidence['elapsed_seconds'] < criteria['internal_time_limit_seconds']

    def pairs(high, low):
        return [Fraction(float(h))+Fraction(float(l)) for h, l in zip(high, low)]

    def difference(now, before, name):
        return np.array([float(a-b) for a, b in zip(
            pairs(getattr(now, name+'_momentum'), getattr(now, name+'_momentum_low')),
            pairs(getattr(before, name+'_momentum'), getattr(before, name+'_momentum_low')))])

    def coordinates(mechanical, reference):
        q = np.zeros(42)
        for node in range(3):
            q[6*node:6*node+3] = [float(a-b) for a, b in zip(
                pairs(mechanical.positions[node], mechanical.position_low[node]),
                pairs(reference.positions[node], reference.position_low[node]))]
        for cell in (0, 1):
            q[18+3*cell:21+3*cell] = log_rotation(
                mechanical.cell_rotations[0, cell]@reference.cell_rotations[0, cell].T)
        return q[p]

    def mechanical_data(mechanical):
        return {name: value.tolist() for name, value in mechanical.descriptor().items()}

    def accounting(data):
        return dict(time_seconds=data.time, epoch=data.epoch, state_sha256=data.state_sha256,
            linear_momentum=data.linear_momentum.tolist(), linear_momentum_low=data.linear_momentum_low.tolist(),
            angular_momentum=data.angular_momentum.tolist(), angular_momentum_low=data.angular_momentum_low.tolist(),
            kinetic_energy_j=data.kinetic_energy, elastic_energy_j=data.elastic_energy,
            total_energy_j=data.total_energy, elastic_witness_j=data.elastic_consistency_witness,
            compatibility18=data.resultant_compatibility18.tolist(), rank_mass=json.loads(data.rank_mass_checks))

    def compare(coarse, fine, floor, ratio):
        if coarse <= floor:
            return dict(coarse=coarse, fine=fine, floor=floor, ratio=None,
                        disposition='resolution_limited' if fine <= floor else 'unresolved_NONPASS',
                        passes=bool(fine <= floor))
        return dict(coarse=coarse, fine=fine, floor=floor, ratio=fine/coarse,
                    disposition='bounded_comparison', passes=bool(fine <= ratio*coarse))

    with output.open('x', encoding='utf-8') as stream:
        stream.write('{}\n')
    save('entry')
    try:
        profile_before = bytes(PROFILE_BYTES)
        _, definition = make_analysis()  # Frozen accepted curved/cross-inertia fixture only.
        contexts = []
        for _ in range(3):
            analysis = create_analysis(SELECTOR, (definition,), ())
            context = MidpointContext(analysis, structural_owner='dynamic_elastic', inertia_order=24,
                stage_residual_tolerance=inputs['stage_residual_tolerance'])
            assert not context.fixed and context.load_pattern is None and context._static is None
            assert not analysis.model.boundary_conditions and not analysis.model.constraint_equations
            assert not analysis.model.mesh.point_masses and analysis.model.mesh.element_activity is None
            assert context.physical_free == tuple(p) and context.algebraic_free == tuple(z)
            contexts.append(context)
        saved = old['reference']
        assert saved['physical_indices'] == p and saved['algebraic_indices'] == z
        reference = Mechanical(*(_owned(saved['reference_mechanical'][name]) for name in
            ('positions', 'position_low', 'nodal_frames', 'cell_rotations', 'resultants')))
        M, Ke = np.asarray(saved['M15']), np.asarray(saved['Ke15'])
        mode, full = np.asarray(saved['selected_mode15']), np.asarray(saved['full_linear_mode42'])
        omega, duration = saved['omega_rad_per_s'], saved['duration_seconds']
        modal_mass, mass = saved['modal_mass'], saved['physical_total_mass_kg']
        length = 2.
        B = np.asarray(saved['transformed_eigenvectors']).T@np.linalg.cholesky(M).T
        evidence['reference'] = dict(saved,
            provenance='Authenticated original V2 spatial/modal matrices; no new eigensolve or structural reference assembly')
        save('authenticated_reference')
        assert saved['Kzz_rank'] == 27 and min(saved['physical_mass_eigenvalues']) > 0
        assert saved['eigenpair_relative_residual'] <= criteria['eigenpair_residual_limit']
        runs = (('coarse', criteria['amplitude'], 4), ('fine', criteria['amplitude'], 8),
                ('half_fine', criteria['amplitude']/2, 8))
        for context, (label, amplitude, count) in zip(contexts, runs):
            assert canonical(context._reference_mechanical) == canonical(reference)
            seeded = {name: value.copy() for name, value in reference.descriptor().items()}
            initial_seed = amplitude*full
            for node in range(3):
                for axis in range(3):
                    seeded['positions'][node, axis], seeded['position_low'][node, axis] = split_sum((
                        float(seeded['positions'][node, axis]), float(seeded['position_low'][node, axis]),
                        float(initial_seed[6*node+axis])))
                seeded['nodal_frames'][node] = rotation(initial_seed[6*node+3:6*node+6])@reference.nodal_frames[node]
            for cell in (0, 1):
                seeded['cell_rotations'][0, cell] = rotation(initial_seed[18+3*cell:21+3*cell])@reference.cell_rotations[0, cell]
            seeded['resultants'][0] += initial_seed[24:]
            mechanical = Mechanical(*(_owned(seeded[name]) for name in
                ('positions', 'position_low', 'nodal_frames', 'cell_rotations', 'resultants')))
            state = context.initialize(mechanical, np.zeros(24))
            initial = context.endpoint_accounting(state)
            h = float(duration/count)
            theta = float(2*np.arctan(omega*h/2))
            energy = initial.total_energy
            assert energy > 0 and np.isfinite(energy)
            speed = float(np.sqrt(2*energy/mass))
            scales = dict(energy_j=energy, momentum=mass*speed, angular_momentum=mass*length*speed,
                          configuration=amplitude*np.sqrt(modal_mass), velocity=amplitude*omega*np.sqrt(modal_mass))
            correction = dict(resultants=(state.mechanical.resultants-mechanical.resultants).tolist(),
                nodal_frame_angles=[log_rotation(state.mechanical.nodal_frames[n]@mechanical.nodal_frames[n].T).tolist() for n in range(3)])
            run = evidence['resolutions'][label] = dict(amplitude=amplitude, steps_requested=count,
                dt_seconds=h, duration_seconds=duration, discrete_phase_per_step=theta,
                initial=accounting(initial), initial_mechanical=mechanical_data(state.mechanical),
                algebraic_initial_adjustment=correction, scales=scales, initial_checks=context.initial_checks,
                context_sha256=context._identity, endpoints=[])
            # Capture actual initialized work/acceleration through the shared
            # authenticated session; no nested public operation or stage issuance.
            with context._atomic_operation():
                context._require_current(state)
                R0, J0, material0 = context._structural(state.mechanical, state.histories)
                zero0 = context._inertia(state.mechanical, np.zeros(24), np.zeros(24))
                I0 = context._inertia(state.mechanical, state.physical_velocity24, state.physical_acceleration24)
                residual_scales = context._gate_inputs()[0].copy()
            initial_balance = R0+I0.mixed_inertia
            actual_q = coordinates(state.mechanical, reference)
            linear_a = -np.linalg.solve(M, Ke@actual_q)
            run['initial_work'] = dict(physical_velocity24=state.physical_velocity24.tolist(),
                physical_acceleration24=state.physical_acceleration24.tolist(), q15=actual_q.tolist(),
                structural_residual42=R0.tolist(), structural_spatial_jacobian42=J0.tolist(),
                configuration_mass42=zero0.mixed_mass.tolist(), inertial_work42=I0.mixed_inertia.tolist(),
                zero_velocity_acceleration_inertia42=zero0.mixed_inertia.tolist(),
                balance42=initial_balance.tolist(), residual_scales42=residual_scales.tolist(),
                physical_balance_norm=float(np.linalg.norm((initial_balance/residual_scales)[p])),
                algebraic_balance_norm=float(np.linalg.norm((initial_balance/residual_scales)[z])),
                linear_acceleration15=linear_a.tolist(),
                acceleration_remainder15=(state.physical_acceleration24[p]-linear_a).tolist(),
                modal_remainder15=(B@(state.physical_acceleration24[p]-linear_a)).tolist(),
                histories=json.loads(canonical(state.histories)), material_sha256=material0)
            save(label+'_initialized')
            assert np.array_equal(state.physical_velocity24, np.zeros(24))
            assert np.array_equal(zero0.mixed_inertia, np.zeros(42))
            assert np.count_nonzero(zero0.mixed_mass[z]) == 0 and np.count_nonzero(zero0.mixed_mass[:, z]) == 0
            assert np.count_nonzero(I0.mixed_inertia[z]) == 0
            assert run['initial_work']['physical_balance_norm'] <= 1e-11
            assert run['initial_work']['algebraic_balance_norm'] <= 1e-11
            assert canonical(state.histories) == canonical(saved['virgin_histories'])
            assert np.array_equal(state.mechanical.positions, mechanical.positions)
            assert np.array_equal(state.mechanical.position_low, mechanical.position_low)
            assert np.array_equal(state.mechanical.cell_rotations, mechanical.cell_rotations)
            assert canonical(state.histories) == canonical(context._reference_origins)
            assert initial.elastic_consistency_witness/energy <= criteria['elastic_witness_limit']
            previous_account = initial
            represented_cell_path = np.zeros(2)
            for index in range(count):
                candidate = context.trial(state, dt=h)
                represented_cell_path += [np.linalg.norm(candidate.unknown42[18+3*c:21+3*c]) for c in (0, 1)]
                run['pending_trial'] = dict(unknown42=candidate.unknown42.tolist(),
                    endpoint=mechanical_data(candidate.endpoint.mechanical),
                    stage_residual_norm=candidate.stage_residual_norm,
                    endpoint_algebraic_norm=candidate.endpoint_algebraic_norm,
                    iterations=candidate.iterations, backtracks=candidate.backtracks,
                    represented_cell_path_rad=represented_cell_path.tolist())
                audit = context.candidate_stage_audit(candidate)
                assert audit.context_sha256 == state.context_sha256
                assert audit.predecessor_sha256 == sha(state) and audit.predecessor_epoch == state.epoch
                assert audit.endpoint_epoch == state.epoch+1 and audit.dt == h
                assert audit.candidate_sha256 == sha(candidate) and audit.stage_sha256 == sha(candidate.stage)
                assert audit.stage_residual_tolerance == 1e-15
                assert np.array_equal(audit.stage.residual,
                    audit.stage.structural_residual+audit.stage.inertia.mixed_inertia)
                assert not audit.unknown42.flags.writeable and not audit.residual_scales42.flags.writeable
                assert context.current is state and context._work_session is None
                assert context._dynamic._active_session is None
                T, U = np.zeros((42, 3)), np.zeros((42, 3))
                for node in range(3):
                    first = 6*node
                    r = np.array([float(Fraction(float(audit.stage.mechanical.positions[node, axis]))
                        +Fraction(float(audit.stage.mechanical.position_low[node, axis]))
                        -Fraction(float(context.momentum_origin_high[axis]))
                        -Fraction(float(context.momentum_origin_low[axis]))) for axis in range(3)])
                    a, b, c = r
                    T[first:first+3] = np.eye(3)
                    U[first:first+3] = np.array(((0., c, -b), (-c, 0., a), (b, -a, 0.)))
                    U[first+3:first+6] = np.eye(3)
                for first in (18, 21):
                    U[first:first+3] = np.eye(3)
                vectors = dict(structural=audit.stage.structural_residual,
                    inertial=audit.stage.inertia.mixed_inertia, residual=audit.stage.residual)
                projections = {key: dict(force_n=(T.T@value).tolist(),
                    moment_nm=(U.T@value).tolist()) for key, value in vectors.items()}
                stage_record = dict(context_sha256=audit.context_sha256,
                    candidate_sha256=audit.candidate_sha256, stage_sha256=audit.stage_sha256,
                    predecessor_sha256=audit.predecessor_sha256,
                    predecessor_epoch=audit.predecessor_epoch, endpoint_epoch=audit.endpoint_epoch,
                    dt_seconds=audit.dt, session_provenance=json.loads(audit.session_provenance),
                    unknown42=audit.unknown42.tolist(), mechanical=mechanical_data(audit.stage.mechanical),
                    structural_residual42=audit.stage.structural_residual.tolist(),
                    inertial_work42=audit.stage.inertia.mixed_inertia.tolist(),
                    residual42=audit.stage.residual.tolist(), residual_scales42=audit.residual_scales42.tolist(),
                    physical_velocity24=audit.stage.physical_velocity24.tolist(),
                    physical_acceleration24=audit.stage.physical_acceleration24.tolist(),
                    rigid_translation_map42x3=T.tolist(), rigid_rotation_map42x3=U.tolist(),
                    signed_projections=projections, stage_residual_tolerance=audit.stage_residual_tolerance,
                    stage_residual_norm=audit.stage_residual_norm, material_sha256=audit.stage.material_sha256)
                run['pending_trial']['authenticated_stage_audit'] = stage_record
                if label == 'coarse' and index == 0:
                    with pytest.raises(ValueError, match='issued current-predecessor'):
                        context.candidate_stage_audit(replace(candidate))
                    assert context.current is state
                save(label+'_trial_'+str(index+1))
                assert np.max(represented_cell_path) < 1e-3
                state = context.commit(candidate)
                if label == 'coarse' and index == 0:
                    with pytest.raises(ValueError, match='issued current-predecessor'):
                        context.candidate_stage_audit(candidate)
                    assert context.current is state
                now = context.endpoint_accounting(state)
                q = coordinates(state.mechanical, reference)
                v = state.physical_velocity24[p]
                continuous_phase = omega*state.time
                discrete_phase = (index+1)*theta
                qcont, vcont = amplitude*mode*np.cos(continuous_phase), -amplitude*omega*mode*np.sin(continuous_phase)
                qmid, vmid = amplitude*mode*np.cos(discrete_phase), -amplitude*omega*mode*np.sin(discrete_phase)
                def norm(value, scale):
                    square = float(value@M@value)
                    assert square >= 0
                    return float(np.sqrt(square)/scale)
                errors = dict(configuration_continuum=norm(q-qcont, scales['configuration']),
                    velocity_continuum=norm(v-vcont, scales['velocity']),
                    configuration_discrete_midpoint=norm(q-qmid, scales['configuration']),
                    velocity_discrete_midpoint=norm(v-vmid, scales['velocity']),
                    predicted_configuration_dispersion=norm(qmid-qcont, scales['configuration']),
                    predicted_velocity_dispersion=norm(vmid-vcont, scales['velocity']))
                dp, dh = difference(now, previous_account, 'linear'), difference(now, previous_account, 'angular')
                cp, ch = difference(now, initial, 'linear'), difference(now, initial, 'angular')
                step = dict(linear=float(np.linalg.norm(dp)/scales['momentum']),
                    angular=float(np.linalg.norm(dh)/scales['angular_momentum']),
                    energy=abs(now.total_energy-previous_account.total_energy)/energy)
                cumulative = dict(linear=float(np.linalg.norm(cp)/scales['momentum']),
                    angular=float(np.linalg.norm(ch)/scales['angular_momentum']),
                    energy=abs(now.total_energy-initial.total_energy)/energy)
                impulse_parts = {}
                for name, delta, map_key in (('linear', dp, 'force_n'), ('angular', dh, 'moment_nm')):
                    integrated = {key: h*np.asarray(value[map_key]) for key, value in projections.items()}
                    impulse_parts[name] = dict(projected_structural_work=integrated['structural'].tolist(),
                        projected_inertial_work=integrated['inertial'].tolist(),
                        projected_solve_residual=integrated['residual'].tolist(),
                        kinetic_midpoint_to_endpoint_remainder=(delta-integrated['inertial']).tolist(),
                        total_minus_projected_solve=(delta-integrated['residual']).tolist())
                endpoint = dict(authenticated_stage_audit=stage_record, impulse_parts=impulse_parts, accounting=accounting(now), mechanical=mechanical_data(state.mechanical),
                    physical_velocity24=state.physical_velocity24.tolist(),
                    physical_acceleration24=state.physical_acceleration24.tolist(), q15=q.tolist(),
                    continuous_q15=qcont.tolist(), continuous_v15=vcont.tolist(),
                    discrete_midpoint_q15=qmid.tolist(), discrete_midpoint_v15=vmid.tolist(), errors=errors,
                    step_linear_impulse_n_s=dp.tolist(), step_angular_impulse_nm_s=dh.tolist(),
                    step_energy_defect_j=now.total_energy-previous_account.total_energy,
                    normalized_step_defects=step, normalized_cumulative_defects=cumulative,
                    stage_residual_norm=candidate.stage_residual_norm, endpoint_algebraic_norm=candidate.endpoint_algebraic_norm,
                    stage_iterations=candidate.iterations, stage_backtracks=candidate.backtracks,
                    history_sha256=sha256(canonical(state.histories)).hexdigest())
                run['endpoints'].append(endpoint)
                run.pop('pending_trial')
                evidence['accepted_steps_total'] += 1
                save(label+'_endpoint_'+str(index+1))
                assert max(step.values()) <= criteria['normalized_defect_limit']
                assert max(cumulative.values()) <= criteria['normalized_defect_limit']
                assert now.elastic_consistency_witness/energy <= criteria['elastic_witness_limit']
                assert candidate.stage_residual_norm <= 1e-15 and candidate.endpoint_algebraic_norm <= 1e-11
                assert max(errors[k] for k in ('configuration_discrete_midpoint', 'velocity_discrete_midpoint')) <= criteria['nonlinear_to_discrete_limit']
                assert np.count_nonzero(candidate.stage.inertia.mixed_inertia[z]) == 0
                assert np.count_nonzero(candidate.stage.inertia.mixed_mass[z]) == 0
                assert canonical(state.histories) == canonical(context._reference_origins)
                previous_account = now
            assert state.epoch == count and abs(state.time-duration) <= 8*np.finfo(float).eps*duration
            assert context._dynamic._active_session is None and context._work_session is None
            assert len(context._dynamic._issued) == 1
        coarse = evidence['resolutions']['coarse']['endpoints']
        fine_common = evidence['resolutions']['fine']['endpoints'][1::2]
        fine = evidence['resolutions']['fine']['endpoints']
        half = evidence['resolutions']['half_fine']['endpoints']
        def maximum(rows, keys):
            return max(row['errors'][key] for row in rows for key in keys)
        continuum_keys = ('configuration_continuum', 'velocity_continuum')
        discrete_keys = ('configuration_discrete_midpoint', 'velocity_discrete_midpoint')
        comparisons = dict(continuum_time=compare(maximum(coarse, continuum_keys), maximum(fine_common, continuum_keys),
                criteria['trajectory_floor'], criteria['time_refinement_ratio']),
            amplitude=compare(maximum(fine, discrete_keys), maximum(half, discrete_keys),
                criteria['trajectory_floor'], criteria['amplitude_refinement_ratio']))
        for key in ('linear', 'angular', 'energy'):
            comparisons[key] = compare(max(row['normalized_cumulative_defects'][key] for row in coarse),
                max(row['normalized_cumulative_defects'][key] for row in fine_common),
                criteria['invariant_floor'], criteria['time_refinement_ratio'])
        evidence['comparisons'] = comparisons
        save('comparisons_before_gates')
        assert all(row['passes'] for row in comparisons.values()), comparisons
        assert evidence['accepted_steps_total'] == 20 and PROFILE_BYTES == profile_before
        evidence['status'] = 'PASS'
        save('complete')
        record_property('accepted_steps', 20)
        record_property('selected_omega_rad_per_s', omega)
        record_property('comparisons', json.dumps(comparisons))
    except BaseException as error:
        evidence.update(status='NONPASS', failure_type=type(error).__name__, failure=str(error))
        save('failure')
        raise



def test_explicit_stage_tolerance_default_identity_and_guard(record_property):
    """Focused zero-timestep changed-setting/default-payload check only."""
    started = perf_counter()
    output = Path(os.environ['NATIVE_VIBRATION_RAW_OUTPUT'])
    with output.open('x', encoding='utf-8') as stream:
        stream.write('{}\n')
    evidence = dict(status='RUNNING', time_steps=0, checks={})
    try:
        clamp, definition = make_analysis()
        legacy = MidpointContext(clamp)
        old_payload = dict(implementation=IMPLEMENTATION_ID, analysis=legacy.analysis.identity,
            inertia_order=legacy.inertia_order, iterations=legacy.max_iterations,
            backtracks=legacy.max_backtracks, physical=legacy.physical_free,
            algebraic=legacy.algebraic_free, free=legacy.free, static_context=legacy._static.identity)
        assert canonical(legacy._identity_data()) == canonical(old_payload)
        assert legacy._identity == sha(old_payload) and legacy.stage_residual_tolerance == 1e-11
        free = create_analysis(SELECTOR, (definition,), ())
        default = MidpointContext(free, structural_owner='dynamic_elastic')
        explicit_default = MidpointContext(free, structural_owner='dynamic_elastic', stage_residual_tolerance=1e-11)
        tighter = MidpointContext(free, structural_owner='dynamic_elastic', stage_residual_tolerance=1e-15)
        assert default._identity == explicit_default._identity
        assert 'stage_residual_tolerance' not in default._identity_data()
        payload = dict(default._identity_data(), stage_residual_tolerance=1e-15)
        assert canonical(tighter._identity_data()) == canonical(payload)
        assert tighter._identity == sha(payload) and tighter._identity != default._identity
        evidence['checks']['default_payload_and_nondefault_identity'] = True
        for invalid in (0., -1., float('nan'), float('inf'), True, '1e-15', 10**1000):
            with pytest.raises(ValueError, match='positive finite'):
                MidpointContext(free, structural_owner='dynamic_elastic', stage_residual_tolerance=invalid)
        evidence['checks']['seven_invalid_settings_rejected'] = True
        for context, mutation in ((default, 1e-15), (tighter, 1e-13), (tighter, float('nan'))):
            original = context.stage_residual_tolerance
            context.stage_residual_tolerance = mutation
            with pytest.raises(ValueError, match='midpoint.*changed'):
                with context._atomic_operation():
                    context._guard()
            context.stage_residual_tolerance = original
            with context._atomic_operation():
                context._guard()
            assert context.current is None and not context._candidates
        evidence['checks']['actual_setting_mutations_rejected'] = True
        operation = tighter._work_operation
        @contextmanager
        def mutate_on_scope_exit():
            with operation():
                yield
            tighter.stage_residual_tolerance = 1e-13
        tighter._work_operation = mutate_on_scope_exit
        with pytest.raises(ValueError, match='stage residual tolerance changed'):
            with tighter._atomic_operation():
                tighter._guard()
        tighter.stage_residual_tolerance = 1e-15
        tighter._work_operation = operation
        assert tighter.current is None and not tighter._candidates
        with tighter._atomic_operation():
            tighter._guard()
        evidence['checks']['scope_exit_setting_mutation_rejected'] = True
        with pytest.raises(ValueError, match='issued current-predecessor'):
            tighter.candidate_stage_audit(object())
        assert tighter.current is None and not tighter._candidates
        assert tighter._work_session is None and tighter._dynamic._active_session is None
        evidence['checks']['unissued_audit_and_session_closure'] = True
        evidence['status'] = 'PASS'
        record_property('time_steps', 0)
    except BaseException as error:
        evidence.update(status='NONPASS', failure_type=type(error).__name__, failure=str(error))
        raise
    finally:
        evidence['elapsed_seconds'] = perf_counter()-started
        output.write_text(json.dumps(evidence, indent=2)+'\n', encoding='utf-8')
