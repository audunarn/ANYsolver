"""Capture actual consistent initial forcing; no timesteps or eigen campaign."""
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
from anysolver._ge_beam3_centered_finite_inertia import PHYSICAL_DOFS, ALGEBRAIC_DOFS
from anysolver._ge_beam3_p5.algebra import rotation, log_rotation
from anysolver._ge_beam3_p5.compensated_coordinates import split_sum
from anysolver._ge_beam3_p5_seeded.core import canonical
from anysolver._native_reference_modal import _owned
from test_ge_beam3_native_midpoint import make_analysis


def test_actual_initial_modal_forcing_quadratic_amplitude_control(record_property):
    started = perf_counter()
    inputs = json.loads(Path(os.environ['NATIVE_VIBRATION_INPUTS']).read_text(encoding='utf-8-sig'))
    historical = inputs['historical']
    for label in ('v2', 'v3'):
        for kind in ('raw', 'input'):
            path = Path(historical[label+'_'+kind+'_path'])
            assert sha256(path.read_bytes()).hexdigest() == historical[label+'_'+kind+'_sha256']
    old = json.loads(Path(historical['v2_raw_path']).read_text())
    prior_inputs = json.loads(Path(historical['v2_input_path']).read_text(encoding='utf-8-sig'))
    criteria = inputs['criteria']
    temporal = prior_inputs['criteria']
    assert old['status'] == 'NONPASS' and old['accepted_steps_total'] == 2
    output = Path(os.environ['NATIVE_VIBRATION_RAW_OUTPUT'])
    assert not output.exists()
    with output.open('x', encoding='utf-8') as stream:
        stream.write('{}\n')
    evidence = dict(status='RUNNING', time_steps=0, historical=historical, criteria=criteria,
        source_sha256=inputs['source_sha256'], initial_states={},
        scope='Initial finite-amplitude acceleration remainder; previous temporal NONPASS retained')

    def save(stage):
        evidence.update(last_stage=stage, elapsed_seconds=perf_counter()-started)
        output.write_text(json.dumps(evidence, indent=2)+'\n', encoding='utf-8')
        print(json.dumps(dict(stage=stage, elapsed_seconds=evidence['elapsed_seconds'])), flush=True)
        assert evidence['elapsed_seconds'] < 120

    def mechanical(data):
        return Mechanical(*(_owned(data[key]) for key in
            ('positions', 'position_low', 'nodal_frames', 'cell_rotations', 'resultants')))

    def descriptor(state):
        return {key: value.tolist() for key, value in state.descriptor().items()}

    try:
        ref = old['reference']
        p, z = list(PHYSICAL_DOFS), list(ALGEBRAIC_DOFS)
        assert ref['physical_indices'] == p and ref['algebraic_indices'] == z
        M0, Ke = np.asarray(ref['M15']), np.asarray(ref['Ke15'])
        W = np.asarray(ref['transformed_eigenvectors'])
        B = W.T@np.linalg.cholesky(M0).T
        mode = np.asarray(ref['selected_mode15'])
        full_mode = np.asarray(ref['full_linear_mode42'])
        reference = mechanical(ref['reference_mechanical'])
        inverse_M0_bound = 1/min(ref['physical_mass_eigenvalues'])
        gamma = 256*np.finfo(float).eps/(1-256*np.finfo(float).eps)
        evidence['reference'] = dict(mode15=mode.tolist(), full_mode42=full_mode.tolist(), M0=M0.tolist(),
            Ke=Ke.tolist(), modal_projection_B=B.tolist(), eigenvalues=ref['eigenvalues'],
            selected_mode_index=6, fast_mode_index=9, gamma256=gamma,
            source_of_matrices='Authenticated V2 shared spatial reference, no new eigensolve')
        save('authenticated_reference')
        _, definition = make_analysis()
        profile_before = PROFILE_BYTES
        for label, amplitude in (('full', temporal['amplitude']), ('half', temporal['amplitude']/2)):
            analysis = create_analysis(SELECTOR, (definition,), ())
            context = MidpointContext(analysis, structural_owner='dynamic_elastic', inertia_order=24)
            assert not context.fixed and context._static is None and context.load_pattern is None
            assert not analysis.model.boundary_conditions and not analysis.model.constraint_equations
            assert not analysis.model.mesh.point_masses and analysis.model.mesh.element_activity is None
            assert context.physical_free == tuple(p) and context.algebraic_free == tuple(z)
            assert canonical(context._reference_mechanical) == canonical(reference)
            if label == 'full':
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
            account = context.endpoint_accounting(state)
            # One authenticated operation and disposable structural session,
            # with no nested public operation or stage/candidate issuance.
            with context._atomic_operation():
                context._require_current(state)
                R, J, material = context._structural(state.mechanical, state.histories)
                zero = context._inertia(state.mechanical, np.zeros(24), np.zeros(24))
                inertia = context._inertia(state.mechanical, state.physical_velocity24, state.physical_acceleration24)
                scales = context._gate_inputs()[0].copy()
            balance = R+inertia.mixed_inertia
            q42 = np.zeros(42)
            for node in range(3):
                for axis in range(3):
                    q42[6*node+axis] = float(Fraction(float(state.mechanical.positions[node, axis]))
                        +Fraction(float(state.mechanical.position_low[node, axis]))
                        -Fraction(float(reference.positions[node, axis]))-Fraction(float(reference.position_low[node, axis])))
                q42[6*node+3:6*node+6] = log_rotation(state.mechanical.nodal_frames[node]@reference.nodal_frames[node].T)
            for cell in (0, 1):
                q42[18+3*cell:21+3*cell] = log_rotation(state.mechanical.cell_rotations[0, cell]@reference.cell_rotations[0, cell].T)
            q42[24:] = state.mechanical.resultants[0]-reference.resultants[0]
            a = state.physical_acceleration24[p]
            q = q42[p]
            linear_acceleration = -np.linalg.solve(M0, Ke@q)
            remainder = a-linear_acceleration
            modal = B@remainder
            Mq = zero.mixed_mass[np.ix_(p, p)]
            propagated = B@np.linalg.solve(Mq, np.diag(scales[p]))
            # The owner's gate is the l2 norm of scaled physical balance,
            # so Cauchy-Schwarz row norms are valid (no signed summation).
            # Inflate for the actual-M solve's conditioning as well.
            actual_condition = context.initial_checks['physical_mass_condition']
            balance_floor = np.nextafter(np.linalg.norm(propagated, axis=1)*1e-11
                *(1+gamma*(1+actual_condition)), np.inf)
            operand = np.linalg.norm(a)+inverse_M0_bound*np.linalg.norm(np.abs(Ke)@np.abs(q))
            # Absolute Ke*q operands plus ||M0^-1|| and cond(M0) cover the
            # linear solve/product cancellation, not just a0-minus-alinear.
            arithmetic_floor = gamma*(1+ref['mass_condition'])*np.linalg.norm(B, axis=1)*operand
            floor = np.nextafter(balance_floor+arithmetic_floor, np.inf)
            record = evidence['initial_states'][label] = dict(amplitude=amplitude, epoch=state.epoch, time_seconds=state.time,
                context_sha256=context._identity, state_mechanical=descriptor(state.mechanical), physical_q15=q.tolist(),
                mixed_q42=q42.tolist(), algebraic_indices=z, physical_indices=p,
                physical_velocity24=state.physical_velocity24.tolist(), physical_acceleration24=state.physical_acceleration24.tolist(),
                structural_residual42=R.tolist(), structural_spatial_jacobian42=J.tolist(), inertial_work42=inertia.mixed_inertia.tolist(),
                zero_velocity_acceleration_inertia42=zero.mixed_inertia.tolist(), configuration_mass42=zero.mixed_mass.tolist(),
                balance42=balance.tolist(), residual_scales42=scales.tolist(),
                physical_balance_norm=float(np.linalg.norm((balance/scales)[p])),
                algebraic_balance_norm=float(np.linalg.norm((balance/scales)[z])),
                linear_acceleration15=linear_acceleration.tolist(), acceleration_remainder15=remainder.tolist(),
                modal_initial_acceleration15=(B@a).tolist(), modal_remainder15=modal.tolist(),
                balance_floor15=balance_floor.tolist(), arithmetic_floor15=arithmetic_floor.tolist(), total_floor15=floor.tolist(),
                total_energy_j=account.total_energy, kinetic_energy_j=account.kinetic_energy,
                elastic_energy_j=account.elastic_energy, elastic_witness_j=account.elastic_consistency_witness,
                histories=json.loads(canonical(state.histories)), material_sha256=material,
                rank_mass_checks=context.initial_checks)
            save(label+'_captured_before_gates')
            assert np.array_equal(state.mechanical.positions, seed.positions)
            assert np.array_equal(state.mechanical.position_low, seed.position_low)
            assert np.array_equal(state.mechanical.cell_rotations, seed.cell_rotations)
            assert state.epoch == 0 and state.time == 0 and context.current is state and not context._candidates
            assert canonical(state.histories) == canonical(ref['virgin_histories'])
            assert np.array_equal(state.physical_velocity24, np.zeros(24))
            assert np.array_equal(zero.mixed_inertia, np.zeros(42))
            assert np.count_nonzero(zero.mixed_mass[z]) == 0 and np.count_nonzero(zero.mixed_mass[:, z]) == 0
            assert np.count_nonzero(inertia.mixed_inertia[z]) == 0
            assert record['physical_balance_norm'] <= 1e-11 and record['algebraic_balance_norm'] <= 1e-11
            assert account.total_energy > 0 and account.elastic_consistency_witness/account.total_energy <= temporal['elastic_witness_limit']
            if label == 'full':
                assert account.total_energy == old['resolutions']['coarse']['initial']['total_energy_j']
            assert context._work_session is None and context._dynamic._active_session is None and len(context._dynamic._issued) == 1
        full = evidence['initial_states']['full']
        half = evidence['initial_states']['half']
        f, g = np.asarray(full['modal_remainder15']), np.asarray(half['modal_remainder15'])
        floors = np.asarray(full['total_floor15'])
        half_floors = np.asarray(half['total_floor15'])
        difference = g-.25*f
        mode9_error = abs(difference[9])/(.25*abs(f[9]))
        vector_error = np.linalg.norm(difference)/(.25*np.linalg.norm(f))
        checks = evidence['quadratic_comparison'] = dict(full_modal_remainder15=f.tolist(), half_modal_remainder15=g.tolist(),
            difference_from_quarter15=difference.tolist(), mode9_relative_error=float(mode9_error),
            full_vector_relative_error=float(vector_error), resolved_full_mode9=bool(abs(f[9])>20*floors[9]),
            resolved_half_mode9=bool(abs(g[9])>20*half_floors[9]),
            resolved_full_vector=bool(np.linalg.norm(f)>20*np.linalg.norm(floors)),
            initial_force_sign_matches_saved_constant_fit=bool(f[9]<0 and g[9]<0),
            temporal_steps=0, stage_directional_check='Not needed if measured initial forcing resolves the principal hypothesis')
        save('quadratic_comparison_before_gates')
        assert checks['resolved_full_mode9'] and checks['resolved_half_mode9'] and checks['resolved_full_vector']
        assert checks['initial_force_sign_matches_saved_constant_fit']
        assert mode9_error <= criteria['quadratic_relative_limit'] and vector_error <= criteria['quadratic_relative_limit']
        assert PROFILE_BYTES == profile_before
        evidence['status'] = 'PASS'
        save('complete')
        record_property('time_steps', 0)
        record_property('mode9_initial_remainder', float(f[9]))
        record_property('mode9_half_relative_quadratic_error', float(mode9_error))
        record_property('all_mode_relative_quadratic_error', float(vector_error))
    except BaseException as error:
        evidence.update(status='NONPASS', failure_type=type(error).__name__, failure=str(error))
        save('failure')
        raise
