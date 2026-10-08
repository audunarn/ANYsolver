"""Targeted fine/half continuation; original coarse NONPASS stays immutable."""
from fractions import Fraction
from hashlib import sha256
import json
import os
from pathlib import Path
from time import perf_counter

import numpy as np

from anysolver.ge_beam3_native import create_analysis, SELECTOR, PROFILE_BYTES
from anysolver._ge_beam3_native_midpoint import MidpointContext
from anysolver._ge_beam3_retained_generalized_state import Mechanical
from anysolver._ge_beam3_p5.algebra import rotation, log_rotation
from anysolver._ge_beam3_p5.compensated_coordinates import split_sum
from anysolver._ge_beam3_p5_seeded.core import canonical
from anysolver._native_reference_modal import _owned
from anysolver._ge_beam3_centered_finite_inertia import PHYSICAL_DOFS, ALGEBRAIC_DOFS
from test_ge_beam3_native_midpoint import make_analysis


def test_fine_half_vibration_from_authentic_failed_coarse_prefix(record_property):
    started = perf_counter()
    inputs = json.loads(Path(os.environ['NATIVE_VIBRATION_INPUTS']).read_text(encoding='utf-8-sig'))
    historical = inputs['historical']
    old_path = Path(historical['raw_path'])
    assert sha256(old_path.read_bytes()).hexdigest() == historical['raw_sha256']
    old_input_path = Path(historical['input_path'])
    assert sha256(old_input_path.read_bytes()).hexdigest() == historical['input_sha256']
    old = json.loads(old_path.read_text())
    old_input = json.loads(old_input_path.read_text(encoding='utf-8-sig'))
    criteria = old_input['criteria']
    assert old['status'] == 'NONPASS' and old['accepted_steps_total'] == 2
    assert old['resolutions']['coarse']['endpoints'][1]['normalized_step_defects']['energy'] > criteria['normalized_defect_limit']
    output = Path(os.environ['NATIVE_VIBRATION_RAW_OUTPUT'])
    assert not output.exists()
    with output.open('x', encoding='utf-8') as stream:
        stream.write('{}\n')
    evidence = dict(status='RUNNING', original_coarse_disposition='NONPASS',
        historical=historical, accepted_steps_total=0, maximum_new_steps=16,
        criteria=criteria, scope='Two common-time prefix points; no fullcoarse order evidence',
        resolutions={}, source_sha256=inputs['source_sha256'])

    def save(stage):
        evidence.update(last_stage=stage, elapsed_seconds=perf_counter()-started)
        output.write_text(json.dumps(evidence, indent=2)+'\n', encoding='utf-8')
        print(json.dumps(dict(stage=stage, elapsed_seconds=evidence['elapsed_seconds'])), flush=True)
        assert evidence['elapsed_seconds'] < 120

    def pairs(high, low):
        return [Fraction(float(h))+Fraction(float(l)) for h, l in zip(high, low)]

    def delta(now, before, field):
        return np.array([float(a-b) for a, b in zip(
            pairs(getattr(now, field+'_momentum'), getattr(now, field+'_momentum_low')),
            pairs(getattr(before, field+'_momentum'), getattr(before, field+'_momentum_low')))])

    def descriptor(mechanical):
        return {name: value.tolist() for name, value in mechanical.descriptor().items()}

    def mechanical(data):
        return Mechanical(*(_owned(data[name]) for name in
            ('positions', 'position_low', 'nodal_frames', 'cell_rotations', 'resultants')))

    def accounting(a):
        return dict(time_seconds=a.time, epoch=a.epoch, state_sha256=a.state_sha256,
            linear_momentum=a.linear_momentum.tolist(), linear_momentum_low=a.linear_momentum_low.tolist(),
            angular_momentum=a.angular_momentum.tolist(), angular_momentum_low=a.angular_momentum_low.tolist(),
            kinetic_energy_j=a.kinetic_energy, elastic_energy_j=a.elastic_energy, total_energy_j=a.total_energy,
            elastic_witness_j=a.elastic_consistency_witness, compatibility18=a.resultant_compatibility18.tolist(),
            rank_mass=json.loads(a.rank_mass_checks))

    def compare(coarse, fine, floor, ratio):
        if coarse <= floor:
            return dict(historical_or_full=coarse, fine_or_half=fine, floor=floor, ratio=None,
                disposition='resolution_limited' if fine <= floor else 'unresolved_NONPASS', passes=bool(fine <= floor))
        return dict(historical_or_full=coarse, fine_or_half=fine, floor=floor, ratio=fine/coarse,
            disposition='bounded_comparison', passes=bool(fine <= ratio*coarse))

    try:
        p, z = list(PHYSICAL_DOFS), list(ALGEBRAIC_DOFS)
        ref = old['reference']
        assert ref['physical_indices'] == p and ref['algebraic_indices'] == z
        M = np.asarray(ref['M15'], dtype=float)
        mode = np.asarray(ref['selected_mode15'], dtype=float)
        full_mode = np.asarray(ref['full_linear_mode42'], dtype=float)
        assert np.array_equal(full_mode[p], mode)
        omega, duration = ref['omega_rad_per_s'], ref['duration_seconds']
        modal_mass, mass = ref['modal_mass'], ref['physical_total_mass_kg']
        h = old['resolutions']['coarse']['dt_seconds']/2
        theta = float(2*np.arctan(omega*h/2))
        coarse = old['resolutions']['coarse']['endpoints']
        reference = mechanical(ref['reference_mechanical'])
        evidence['frozen_reference'] = dict(mode15=mode.tolist(), full_mode42=full_mode.tolist(), M15=M.tolist(),
            omega_rad_per_s=omega, duration_seconds=duration, modal_mass=modal_mass, physical_mass_kg=mass,
            original_coarse_dt_seconds=2*h, new_dt_seconds=h,
            continuous_phase_per_step=omega*h, discrete_midpoint_phase_per_step=theta)
        save('authenticated_historical_reference')
        profile_before = PROFILE_BYTES
        _, definition = make_analysis()
        for label, amplitude in (('fine', criteria['amplitude']), ('half_fine', criteria['amplitude']/2)):
            analysis = create_analysis(SELECTOR, (definition,), ())
            context = MidpointContext(analysis, structural_owner='dynamic_elastic', inertia_order=24)
            assert not context.fixed and context.load_pattern is None and context._static is None
            assert context.physical_free == tuple(p) and context.algebraic_free == tuple(z)
            assert not analysis.model.boundary_conditions and not analysis.model.constraint_equations
            assert not analysis.model.mesh.point_masses and analysis.model.mesh.element_activity is None
            assert canonical(context._reference_mechanical) == canonical(reference)
            if label == 'fine':
                seed = mechanical(old['resolutions']['coarse']['initial_mechanical'])
            else:
                data = {key: value.copy() for key, value in reference.descriptor().items()}
                q0 = amplitude*full_mode
                for node in range(3):
                    for axis in range(3):
                        data['positions'][node, axis], data['position_low'][node, axis] = split_sum((
                            float(data['positions'][node, axis]), float(data['position_low'][node, axis]),
                            float(q0[6*node+axis])))
                    data['nodal_frames'][node] = rotation(q0[6*node+3:6*node+6])@reference.nodal_frames[node]
                for cell in (0, 1):
                    data['cell_rotations'][0, cell] = rotation(q0[18+3*cell:21+3*cell])@reference.cell_rotations[0, cell]
                data['resultants'][0] += q0[24:]
                seed = mechanical(data)
            state = context.initialize(seed, np.zeros(24))
            initial = context.endpoint_accounting(state)
            energy = initial.total_energy
            assert energy > 0
            speed = float(np.sqrt(2*energy/mass))
            scales = dict(energy_j=energy, momentum=mass*speed, angular_momentum=mass*2*speed,
                configuration=amplitude*np.sqrt(modal_mass), velocity=amplitude*omega*np.sqrt(modal_mass))
            run = evidence['resolutions'][label] = dict(amplitude=amplitude, dt_seconds=h, steps_requested=8,
                duration_seconds=duration, scales=scales, initial=accounting(initial), initial_mechanical=descriptor(state.mechanical),
                initial_checks=context.initial_checks, context_sha256=context._identity, endpoints=[],
                algebraic_initial_adjustment=dict(resultants=(state.mechanical.resultants-seed.resultants).tolist(),
                    nodal_frame_angles=[log_rotation(state.mechanical.nodal_frames[n]@seed.nodal_frames[n].T).tolist() for n in range(3)]))
            save(label+'_initialized_before_gates')
            assert np.array_equal(state.mechanical.positions, seed.positions)
            assert np.array_equal(state.mechanical.position_low, seed.position_low)
            assert np.array_equal(state.mechanical.cell_rotations, seed.cell_rotations)
            assert canonical(state.histories) == canonical(ref['virgin_histories'])
            if label == 'fine':
                assert energy == old['resolutions']['coarse']['initial']['total_energy_j']
                assert scales == old['resolutions']['coarse']['scales']
            assert initial.elastic_consistency_witness/energy <= criteria['elastic_witness_limit']
            previous = initial
            cell_path = np.zeros(2)
            for index in range(8):
                candidate = context.trial(state, dt=float(h))
                cell_path += [np.linalg.norm(candidate.unknown42[18+3*c:21+3*c]) for c in (0, 1)]
                run['pending_trial'] = dict(unknown42=candidate.unknown42.tolist(), endpoint=descriptor(candidate.endpoint.mechanical),
                    stage_residual_norm=candidate.stage_residual_norm, endpoint_algebraic_norm=candidate.endpoint_algebraic_norm,
                    represented_cell_path_rad=cell_path.tolist(), iterations=candidate.iterations, backtracks=candidate.backtracks)
                save(label+'_trial_'+str(index+1))
                assert np.max(cell_path) < 1e-3
                state = context.commit(candidate)
                now = context.endpoint_accounting(state)
                q42 = np.zeros(42)
                for node in range(3):
                    q42[6*node:6*node+3] = [float(a-b) for a, b in zip(
                        pairs(state.mechanical.positions[node], state.mechanical.position_low[node]),
                        pairs(reference.positions[node], reference.position_low[node]))]
                for cell in (0, 1):
                    q42[18+3*cell:21+3*cell] = log_rotation(state.mechanical.cell_rotations[0, cell]@reference.cell_rotations[0, cell].T)
                q, v = q42[p], state.physical_velocity24[p]
                qc, vc = amplitude*mode*np.cos(omega*state.time), -amplitude*omega*mode*np.sin(omega*state.time)
                qm, vm = amplitude*mode*np.cos((index+1)*theta), -amplitude*omega*mode*np.sin((index+1)*theta)
                def norm(value, scale):
                    square = float(value@M@value)
                    assert square >= 0
                    return float(np.sqrt(square)/scale)
                errors = dict(configuration_continuum=norm(q-qc, scales['configuration']),
                    velocity_continuum=norm(v-vc, scales['velocity']),
                    configuration_discrete_midpoint=norm(q-qm, scales['configuration']),
                    velocity_discrete_midpoint=norm(v-vm, scales['velocity']),
                    predicted_configuration_dispersion=norm(qm-qc, scales['configuration']),
                    predicted_velocity_dispersion=norm(vm-vc, scales['velocity']))
                dp, dh = delta(now, previous, 'linear'), delta(now, previous, 'angular')
                cp, ch = delta(now, initial, 'linear'), delta(now, initial, 'angular')
                step = dict(linear=float(np.linalg.norm(dp)/scales['momentum']), angular=float(np.linalg.norm(dh)/scales['angular_momentum']),
                            energy=abs(now.total_energy-previous.total_energy)/energy)
                cumulative = dict(linear=float(np.linalg.norm(cp)/scales['momentum']), angular=float(np.linalg.norm(ch)/scales['angular_momentum']),
                                  energy=abs(now.total_energy-initial.total_energy)/energy)
                row = dict(accounting=accounting(now), mechanical=descriptor(state.mechanical),
                    physical_velocity24=state.physical_velocity24.tolist(), physical_acceleration24=state.physical_acceleration24.tolist(),
                    q15=q.tolist(), continuous_q15=qc.tolist(), continuous_v15=vc.tolist(),
                    discrete_midpoint_q15=qm.tolist(), discrete_midpoint_v15=vm.tolist(), errors=errors,
                    normalized_step_defects=step, normalized_cumulative_defects=cumulative,
                    step_linear_impulse_n_s=dp.tolist(), step_angular_impulse_nm_s=dh.tolist(),
                    step_energy_defect_j=now.total_energy-previous.total_energy, stage_residual_norm=candidate.stage_residual_norm,
                    endpoint_algebraic_norm=candidate.endpoint_algebraic_norm, stage_iterations=candidate.iterations,
                    stage_backtracks=candidate.backtracks, history_sha256=sha256(canonical(state.histories)).hexdigest())
                run['endpoints'].append(row)
                run.pop('pending_trial')
                evidence['accepted_steps_total'] += 1
                save(label+'_endpoint_'+str(index+1))
                assert max(step.values()) <= criteria['normalized_defect_limit']
                assert max(cumulative.values()) <= criteria['normalized_defect_limit']
                assert now.elastic_consistency_witness/energy <= criteria['elastic_witness_limit']
                assert candidate.stage_residual_norm <= 1e-11 and candidate.endpoint_algebraic_norm <= 1e-11
                assert max(errors[key] for key in ('configuration_discrete_midpoint', 'velocity_discrete_midpoint')) <= criteria['nonlinear_to_discrete_limit']
                assert np.count_nonzero(candidate.stage.inertia.mixed_inertia[z]) == 0
                assert np.count_nonzero(candidate.stage.inertia.mixed_mass[z]) == 0
                assert canonical(state.histories) == canonical(ref['virgin_histories'])
                if label == 'fine' and index == 3:
                    common = run['endpoints'][1::2]
                    assert len(common) == 2
                    assert all(abs(a['accounting']['time_seconds']-b['accounting']['time_seconds']) <= 8*np.finfo(float).eps*duration
                               for a, b in zip(common, coarse))
                    comparisons = {}
                    for key in ('linear', 'angular', 'energy'):
                        comparisons[key] = compare(max(a['normalized_cumulative_defects'][key] for a in coarse),
                            max(a['normalized_cumulative_defects'][key] for a in common), criteria['invariant_floor'], criteria['time_refinement_ratio'])
                    keys = ('configuration_continuum', 'velocity_continuum')
                    comparisons['continuum_time'] = compare(max(a['errors'][key] for a in coarse for key in keys),
                        max(a['errors'][key] for a in common for key in keys), criteria['trajectory_floor'], criteria['time_refinement_ratio'])
                    intervals = []
                    for j in range(2):
                        interval_energy = sum(a['step_energy_defect_j'] for a in run['endpoints'][2*j:2*j+2])
                        intervals.append(dict(end_time_seconds=coarse[j]['accounting']['time_seconds'],
                            historical_coarse_energy_j=coarse[j]['step_energy_defect_j'],
                            sum_two_fine_energy_j=interval_energy))
                    evidence.update(common_time_prefix_comparisons=comparisons, same_interval_energy=intervals)
                    save('two_endpoint_prefix_before_gates')
                    assert all(a['passes'] for a in comparisons.values()), comparisons
                previous = now
            assert state.epoch == 8 and abs(state.time-duration) <= 8*np.finfo(float).eps*duration
            assert context._dynamic._active_session is None and context._work_session is None and len(context._dynamic._issued) == 1
        fine = evidence['resolutions']['fine']['endpoints']
        half = evidence['resolutions']['half_fine']['endpoints']
        assert all(abs(a['accounting']['time_seconds']-b['accounting']['time_seconds']) <= 8*np.finfo(float).eps*duration
                   for a, b in zip(fine, half))
        keys = ('configuration_discrete_midpoint', 'velocity_discrete_midpoint')
        amplitude = compare(max(a['errors'][key] for a in fine for key in keys),
            max(a['errors'][key] for a in half for key in keys), criteria['trajectory_floor'], criteria['amplitude_refinement_ratio'])
        evidence['amplitude_comparison'] = amplitude
        save('amplitude_comparison_before_gate')
        assert amplitude['passes'], amplitude
        assert evidence['accepted_steps_total'] == 16 and PROFILE_BYTES == profile_before
        evidence['status'] = 'PASS'
        save('complete')
        record_property('new_accepted_steps', 16)
        record_property('original_coarse_disposition', 'NONPASS')
        record_property('two_endpoint_prefix_comparisons', json.dumps(evidence['common_time_prefix_comparisons']))
        record_property('amplitude_comparison', json.dumps(amplitude))
    except BaseException as error:
        evidence.update(status='NONPASS', failure_type=type(error).__name__, failure=str(error))
        save('failure')
        raise
