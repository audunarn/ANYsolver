"""Prospective clamped descriptor/reaction check; no old temporal test body is executed."""
from dataclasses import asdict
from fractions import Fraction
from hashlib import sha256
import json
import os
from pathlib import Path
from time import perf_counter
import numpy as np

from anysolver.ge_beam3_native import LinePattern, DistributedPattern
from anysolver.boundary import BoundaryCondition
from anysolver.ge_beam3_native_dynamics import create_analysis, SELECTOR, workflow_provenance
from anysolver._ge_beam3_p5.algebra import log_rotation
from anysolver._ge_beam3_p5_seeded.core import canonical, sha
from test_ge_beam3_native_midpoint import make_analysis
from native_clamped_response_reference import (
    ConstrainedDescriptor, FIXED, PHYSICAL, ALGEBRAIC, reaction_wrench,
    line_stations, load_map, path_accounting, positions, position_delta, compare)


CRITERIA = dict(duration_seconds=.004, coarse_steps=4, fine_steps=8, half_load_fine_steps=8,
    maximum_accepted_steps=20, internal_time_limit_seconds=120.,
    force_density_n_per_m=[.2, -.15, .1], couple_density_nm_per_m=[0., 0., 0.],
    explicit_stage_solve_tolerance=1e-12, scientific_stage_gate=1e-11,
    endpoint_balance_gate=1e-11, normalized_defect_limit=1e-6,
    elastic_witness_limit=1e-10, nonlinear_to_discrete_limit=.002,
    trajectory_floor=1e-6, invariant_floor=1e-10, time_refinement_ratio=.4,
    amplitude_refinement_ratio=.75, resolved_coarse_phase_limit=.4,
    origin_high_m=[0., 0., 0.], origin_low_m=[0., 0., 0.])

RAW_SHA = '705b627848aef2df9ce17cdce2dda937ea1ae29d1031a855f48ff567181248f7'
OLD_INPUT_SHA = '07b3f12777cd21ed5932fe14f51ec3254ba1796f6627d3ce8373be4c2996926d'
FIXTURE_SHA = '426f673d40e82a4d554c3964dc9b51b4ca5638f180f3f985e4ba85c974ebc05d'
PROJECTION_SHA = '171105027214b8dafe5e144b5cab43e6c13914011c6a60c684938bd05dcee1c0'


def accounting(value):
    row = asdict(value)
    row['rank_mass_checks'] = json.loads(row['rank_mass_checks'])
    return json.loads(canonical(row))


def momentum_delta(now, before, name):
    return np.array([float(Fraction(float(h))+Fraction(float(l))-
                           Fraction(float(h0))-Fraction(float(l0)))
        for h, l, h0, l0 in zip(getattr(now, name+'_momentum'), getattr(now, name+'_momentum_low'),
            getattr(before, name+'_momentum'), getattr(before, name+'_momentum_low'))])


def test_clamped_virgin_rest_line_force_descriptor_and_support_impulses(record_property):
    started = perf_counter()
    inputs = json.loads(Path(os.environ['NATIVE_CLAMPED_RESPONSE_INPUTS']).read_text(encoding='utf-8-sig'))
    output = Path(os.environ['NATIVE_CLAMPED_RESPONSE_RAW_OUTPUT'])
    assert not output.exists() and inputs['criteria'] == CRITERIA
    evidence = dict(status='RUNNING', accepted_steps=0, criteria=CRITERIA, resolutions={},
        scope='One clamped line-load temporal/reaction development; accepted spatial input')

    def save(stage):
        evidence.update(last_stage=stage, elapsed_seconds=perf_counter()-started)
        output.write_text(json.dumps(evidence, indent=2)+'\n')
        print(json.dumps(dict(stage=stage, elapsed_seconds=evidence['elapsed_seconds'])), flush=True)
        assert evidence['elapsed_seconds'] < CRITERIA['internal_time_limit_seconds']

    def authentic(label, expected):
        item = inputs['historical'][label]
        raw = Path(item['path']).read_bytes()
        assert item['sha256'] == expected == sha256(raw).hexdigest()
        return raw

    def relative(actual, expected):
        return float(np.linalg.norm(actual-expected)/np.linalg.norm(expected))

    def coordinates(mechanical, reference):
        q = np.zeros(42)
        q[[6*n+i for n in range(3) for i in range(3)]] = position_delta(mechanical, reference).ravel()
        for c in (0, 1):
            q[18+3*c:21+3*c] = log_rotation(mechanical.cell_rotations[0, c]@reference.cell_rotations[0, c].T)
        return q[p]

    try:
        old = json.loads(authentic('raw', RAW_SHA))
        old_inputs = json.loads(authentic('inputs', OLD_INPUT_SHA))
        authentic('fixture', FIXTURE_SHA)
        projection = json.loads(authentic('projection', PROJECTION_SHA))
        saved = old['reference']
        # The only historical source changed here is the reviewed midpoint owner;
        # graph/profile identities are not substitutes for exact source inputs.
        changed = inputs['historical_source_overrides']
        assert changed == {'_ge_beam3_native_midpoint.py':
            'f2c494a93315b541500a8f6aa7330bfae2f731ac9f2251f1585704638f03f71a'}
        for path, expected in old_inputs['source_sha256'].items():
            if Path(path).name in changed:
                expected = changed[Path(path).name]
            assert sha256(Path(path).read_bytes()).hexdigest() == expected
            assert inputs['source_sha256'][path] == expected
        for path, expected in inputs['source_sha256'].items():
            assert sha256(Path(path).read_bytes()).hexdigest() == expected
        p, z = list(PHYSICAL), list(ALGEBRAIC)
        assert len(p) == 12 and len(z) == 24
        descriptor = ConstrainedDescriptor.from_full(saved['K42'], saved['M42'])
        evidence['constrained_reference'] = dict(physical_indices=p, algebraic_indices=z,
            fixed_indices=list(FIXED), M12=descriptor.mass.tolist(), Ke12=descriptor.stiffness.tolist(),
            algebraic_Z=descriptor.algebraic_map.tolist(), embedding42=descriptor.embedding.tolist(),
            eigenvalues=descriptor.eigenvalues.tolist(), modes=descriptor.modes.tolist(),
            checks=descriptor.checks)
        save('constrained_reference_rank_mass_before_steps')
        duration = CRITERIA['duration_seconds']
        assert max(descriptor.omega)*duration/4 < CRITERIA['resolved_coarse_phase_limit']
        assert max(descriptor.omega)*duration < np.pi/2.
        _, definition = make_analysis()  # Authentic builder only; no old test body.
        owners = []
        for factor in (1., 1., .5):
            force = factor*np.asarray(CRITERIA['force_density_n_per_m'])
            pattern = DistributedPattern(LinePattern(((1, *map(float, force)),)), ())
            boundary = BoundaryCondition('homogeneous-root', [1],
                {key: 0. for key in ('ux', 'uy', 'uz', 'rx', 'ry', 'rz')})
            owner = create_analysis(SELECTOR, (definition,), (boundary,), inertia_order=24,
                stage_residual_tolerance=CRITERIA['explicit_stage_solve_tolerance'],
                momentum_origin_high=tuple(CRITERIA['origin_high_m']),
                momentum_origin_low=tuple(CRITERIA['origin_low_m']), load_pattern=pattern)
            c = owner._context
            assert c.stage_residual_tolerance == CRITERIA['explicit_stage_solve_tolerance']
            assert c._captured_stage_residual_tolerance == c.stage_residual_tolerance
            assert c.analysis._admit_boundaries() == FIXED and c.fixed == FIXED
            assert tuple(c.physical_free) == tuple(p) and tuple(c.algebraic_free) == tuple(z)
            assert not c.analysis.model.mesh.point_masses and c.analysis.model.mesh.element_activity is None
            assert len(c.analysis._elements) == 1 and c.element.operator.order == 4
            assert np.array_equal(c.analysis._inertias[c.element.element_id], saved['section_inertia'])
            assert canonical(c._reference_mechanical) == canonical(saved['reference_mechanical'])
            assert canonical(c._reference_origins) == canonical(saved['virgin_histories'])
            owners.append(owner)
        context = owners[0]._context
        reference = context._reference_mechanical
        reference_points = positions(reference)
        rows = line_stations(reference_points)
        force = np.asarray(CRITERIA['force_density_n_per_m'])
        base_load = load_map(reference_points, reference.cell_rotations[0], rows, force, reference_points)
        assert relative(base_load['load42'][saved['physical_indices']],
                        np.asarray(projection['physical_load15_n'])) <= 1e-12
        modal_force = descriptor.modes.T@base_load['load42'][p]
        assert np.linalg.norm(modal_force) > 0.
        evidence['constrained_modal_force'] = modal_force.tolist()
        section = np.asarray(saved['section_inertia'])
        skew = -section[:3, 3:]/2.7
        centroid = np.array((skew[2, 1], skew[0, 2], skew[1, 0]))
        assert np.allclose(centroid, (.035, -.025, .012), rtol=0., atol=1e-17)
        evidence['fixture'] = dict(definition=json.loads(definition.raw),
            physical_section_centroid_m=centroid.tolist(), section_inertia=saved['section_inertia'],
            reference_mechanical=saved['reference_mechanical'], virgin_history=saved['virgin_histories'],
            line_force42=base_load['load42'].tolist(), all12_modal_force=modal_force.tolist(),
            boundaries={'node_id': 1, 'homogeneous_fixed_indices': list(FIXED)},
            note='Force is on the lifted reference line, not section mass centroid/body force')
        # One actual virgin structural/mass check prevents silent transplantation.
        with context._atomic_operation():
            context._guard()
            work = context._work_session.work(reference, origins=context._reference_origins)
            inertia = context._inertia(reference, np.zeros(24), np.zeros(24))
            actual_z = -np.linalg.solve(work.spatial_jacobian[np.ix_(z, z)], work.spatial_jacobian[np.ix_(z, p)])
            actual_ke = work.spatial_jacobian[np.ix_(p, p)]+work.spatial_jacobian[np.ix_(p, z)]@actual_z
        errors = dict(K42=relative(work.spatial_jacobian, np.asarray(saved['K42'])),
            M42=relative(inertia.mixed_mass, np.asarray(saved['M42'])),
            Z24x12=relative(actual_z, descriptor.algebraic_map),
            Ke12=relative(actual_ke, descriptor.stiffness),
            M12=relative(inertia.mixed_mass[np.ix_(p, p)], descriptor.mass))
        evidence['shared_spatial_match'] = dict(errors=errors, actual_K42=work.spatial_jacobian.tolist(),
            actual_M42=inertia.mixed_mass.tolist(), actual_algebraic_Z=actual_z.tolist())
        save('authenticated_spatial_and_force_reference')
        assert max(errors.values()) <= 1e-12
        assert np.count_nonzero(inertia.mixed_mass[z]) == np.count_nonzero(inertia.mixed_mass[:, z]) == 0
        length = 2.
        fields = ('configuration', 'velocity', 'elastic_configuration', 'elastic_velocity')
        def trajectory_errors(q, v, qc, vc, scales):
            return dict(configuration=descriptor.mass_norm(q-qc)/scales['configuration'],
                velocity=descriptor.mass_norm(v-vc)/scales['velocity'],
                elastic_configuration=descriptor.positive_norm(q-qc)/scales['elastic_configuration'],
                elastic_velocity=descriptor.positive_norm(v-vc)/scales['elastic_velocity'])
        base_scales = descriptor.scales(base_load['load42'][p], base_load['force'], length, duration)
        predicted = {}
        for count in (4, 8):
            values = []
            for index in range(1, count+1):
                time, h = duration*index/count, duration/count
                qc, vc = descriptor.trajectory(base_load['load42'][p], time)
                qm, vm = descriptor.trajectory(base_load['load42'][p], time, dt=h, index=index)
                values.append(trajectory_errors(qm, vm, qc, vc, base_scales))
            predicted[count] = values
        prediction_checks = {field: compare(max(row[field] for row in predicted[4]),
            max(row[field] for row in predicted[8][1::2]), CRITERIA['trajectory_floor'],
            CRITERIA['time_refinement_ratio']) for field in fields}
        evidence['reference_preflight'] = dict(scales=base_scales,
            max_omega_rad_s=float(max(descriptor.omega)), predictions=predicted,
            common_time_dispersion_checks=prediction_checks)
        save('reference_preflight_before_initialization')
        assert all(row['passes'] for row in prediction_checks.values()), prediction_checks
        for owner, (label, factor, count) in zip(owners,
                (('coarse', 1., 4), ('fine', 1., 8), ('half_fine', .5, 8))):
            c = owner._context
            f = factor*force
            load0 = load_map(reference_points, reference.cell_rotations[0], rows, f, reference_points)
            scales = descriptor.scales(load0['load42'][p], load0['force'], length, duration)
            # Worst accepted solve contribution is below half of each fixed
            # refinement floor, even half load. This is not a total-error bound.
            p_bound = duration*np.sqrt(3.)*c.stage_residual_tolerance
            h_bound = duration*np.sqrt(3.*1.1**2+5.*length**2)*c.stage_residual_tolerance
            assert p_bound < .5*CRITERIA['invariant_floor']*scales['momentum']
            assert h_bound < .5*CRITERIA['invariant_floor']*scales['angular_momentum']
            state = owner.initialize()  # Actual fixed-physical algebraic consistency and a0.
            initial = previous = owner.endpoint_accounting(state)
            assert canonical(state.mechanical) == canonical(reference)
            assert np.count_nonzero(state.physical_velocity24) == 0
            a_reference = np.linalg.solve(descriptor.mass, load0['load42'][p])
            assert descriptor.mass_norm(state.physical_acceleration24[p]-a_reference)/descriptor.mass_norm(a_reference) <= 1e-10
            with c._atomic_operation():
                c._guard(); w0 = c._loaded_work(state.mechanical, state.histories)
                i0 = c._inertia(state.mechanical, state.physical_velocity24, state.physical_acceleration24)
            run = evidence['resolutions'][label] = dict(factor=factor, steps=count, dt=duration/count,
                scales=scales, effective_stage_solve_tolerance=c.stage_residual_tolerance,
                residual_impulse_envelope=dict(P=p_bound, H=h_bound),
                initial=dict(state=json.loads(canonical(state)), accounting=accounting(initial),
                    R42=w0.residual.tolist(), J42=w0.spatial_jacobian.tolist(),
                    I42=i0.mixed_inertia.tolist(), M42=i0.mixed_mass.tolist(),
                    balance42=(w0.residual+i0.mixed_inertia).tolist(), reference_acceleration12=a_reference.tolist(),
                    actual_support_reaction6=(w0.residual+i0.mixed_inertia)[:6].tolist(),
                    linear_support_reaction6=descriptor.continuous_reaction(load0['load42'], 0.).tolist()),
                endpoints=[], provenance=workflow_provenance(owner))
            assert c._norm(w0.residual+i0.mixed_inertia, c.free) <= CRITERIA['endpoint_balance_gate']
            assert np.count_nonzero(state.physical_velocity24[:6]) == 0
            assert np.count_nonzero(state.physical_acceleration24[:6]) == 0
            fixed_point = positions(reference)[0]
            origin = np.asarray(CRITERIA['origin_high_m'])+np.asarray(CRITERIA['origin_low_m'])
            cumulative_support6 = np.zeros(6)
            previous_load = owner.physical_load_accounting(state.mechanical)
            cumulative_p, cumulative_h, cumulative_hmid = np.zeros(3), np.zeros(3), np.zeros(3)
            cumulative_work = cumulative_workmid = 0.
            h = duration/count
            for index in range(count):
                prior = state
                original_stage = c._stage
                observations = []
                def observe(accepted, unknown, step, token=None):
                    actual = original_stage(accepted, unknown, step, token)
                    observations.append(dict(unknown42=np.asarray(unknown).tolist(),
                        R42=actual.structural_residual.tolist(), I42=actual.inertia.mixed_inertia.tolist(),
                        e42=actual.residual.tolist(), scaled_norm=c._norm(actual.residual, c.free),
                        predecessor_sha256=sha(accepted), predecessor_epoch=accepted.epoch,
                        context_sha256=c._identity, trial_session_active=c._work_session is not None))
                    assert len(observations) <= 128
                    return actual  # Same original object; no numerical decision changed.
                c._stage = observe
                try:
                    candidate = owner.trial(prior, dt=h)
                finally:
                    c._stage = original_stage
                    run['unissued_trial_observations'] = observations
                    save(label+'_trial_return_'+str(index+1))
                audit = owner.candidate_stage_audit(candidate)
                stage_load = owner.physical_load_accounting(candidate.stage.mechanical)
                independent = load_map(positions(candidate.stage.mechanical), candidate.stage.mechanical.cell_rotations[0],
                    rows, f, reference_points)
                load_errors = dict(force=relative(stage_load.external_load42, independent['load42']),
                    tangent=relative(stage_load.external_spatial_jacobian42, independent['tangent42']))
                physical = path_accounting(prior.mechanical, candidate, rows, f, reference_points)
                reaction6 = audit.stage.residual[:6]
                support_force, support_moment = reaction_wrench(reaction6, fixed_point, origin)
                support_p, support_h = h*support_force, h*support_moment
                linear_mid_reaction6 = descriptor.midpoint_reaction(load0['load42'], h, index+1)
                linear_cont_reaction6 = descriptor.continuous_reaction(load0['load42'], h*(index+.5))
                reaction_errors = dict(force=float(np.linalg.norm(reaction6[:3]-linear_mid_reaction6[:3])/scales['force']),
                    couple=float(np.linalg.norm(reaction6[3:]-linear_mid_reaction6[3:])/scales['moment']))
                reaction_dispersion = dict(force=float(np.linalg.norm(linear_mid_reaction6[:3]-linear_cont_reaction6[:3])/scales['force']),
                    couple=float(np.linalg.norm(linear_mid_reaction6[3:]-linear_cont_reaction6[3:])/scales['moment']))
                mid_h = h*stage_load.moment_about_origin+support_h
                mid_work = float(h*(stage_load.external_load42[:24]@candidate.stage.physical_velocity24))

                support_work = float(reaction6[:3]@position_delta(candidate.endpoint.mechanical, prior.mechanical)[0])
                # Exact unchanged nodal frame also gives zero algebraic couple work.
                run['pending_candidate'] = dict(endpoint=json.loads(canonical(candidate.endpoint)),
                    stage_mechanical=json.loads(canonical(audit.stage.mechanical)),
                    stage_velocity24=candidate.stage.physical_velocity24.tolist(),
                    stage_acceleration24=candidate.stage.physical_acceleration24.tolist(),
                    reaction_errors_discrete=reaction_errors, reaction_predicted_dispersion=reaction_dispersion,
                    support_reaction6=reaction6.tolist(), support_force_n=support_force.tolist(),
                    support_moment_about_origin_nm=support_moment.tolist(), support_work_j=support_work,
                    linear_midpoint_support_reaction6=linear_mid_reaction6.tolist(),
                    linear_continuous_support_reaction6=linear_cont_reaction6.tolist(),
                    unknown42=audit.unknown42.tolist(), stage_R42=audit.stage.structural_residual.tolist(),
                    stage_I42=audit.stage.inertia.mixed_inertia.tolist(), stage_e42=audit.stage.residual.tolist(),
                    stage_J42=audit.stage.jacobian.tolist(), stage_M42=audit.stage.inertia.mixed_mass.tolist(),
                    audit_authentication_session=json.loads(audit.session_provenance),
                    stage_sha256=audit.stage_sha256, predecessor_sha256=audit.predecessor_sha256,
                    predecessor_epoch=audit.predecessor_epoch, endpoint_epoch=audit.endpoint_epoch)
                save(label+'_candidate_'+str(index+1))
                for mechanical in (candidate.stage.mechanical, candidate.endpoint.mechanical):
                    assert np.array_equal(mechanical.positions[0], reference.positions[0])
                    assert np.array_equal(mechanical.position_low[0], reference.position_low[0])
                    assert np.array_equal(mechanical.nodal_frames[0], reference.nodal_frames[0])
                assert np.count_nonzero(audit.unknown42[:6]) == 0
                assert np.count_nonzero(candidate.stage.physical_velocity24[:6]) == 0
                assert np.count_nonzero(candidate.stage.physical_acceleration24[:6]) == 0
                assert np.count_nonzero(candidate.endpoint.physical_velocity24[:6]) == 0
                assert np.count_nonzero(candidate.endpoint.physical_acceleration24[:6]) == 0
                assert support_work == 0.
                assert max(load_errors.values()) <= 1e-12
                assert max(reaction_errors.values()) <= CRITERIA['nonlinear_to_discrete_limit']
                assert max(np.linalg.norm(row) for row in positions(candidate.stage.mechanical)) <= 1.1
                assert candidate.stage_residual_norm <= CRITERIA['scientific_stage_gate']
                assert candidate.endpoint_algebraic_norm <= CRITERIA['endpoint_balance_gate']
                assert max(np.linalg.norm(candidate.unknown42[18+3*x:21+3*x]) for x in (0, 1)) < 1e-3
                state = owner.commit(candidate)
                now = owner.endpoint_accounting(state)
                endpoint_load = owner.physical_load_accounting(state.mechanical)
                q, v = coordinates(state.mechanical, reference), state.physical_velocity24[p]
                assert max(np.linalg.norm(row) for row in positions(state.mechanical)) <= 1.1
                qc, vc = descriptor.trajectory(load0['load42'][p], state.time)
                qmid, vmid = descriptor.trajectory(load0['load42'][p], state.time, dt=h, index=index+1)
                cont = trajectory_errors(q, v, qc, vc, scales)
                discrete = trajectory_errors(q, v, qmid, vmid, scales)
                prediction = trajectory_errors(qmid, vmid, qc, vc, scales)
                dp, dh = momentum_delta(now, previous, 'linear'), momentum_delta(now, previous, 'angular')
                cp, ch = momentum_delta(now, initial, 'linear'), momentum_delta(now, initial, 'angular')
                applied_p = physical['linear_impulse']+support_p
                applied_h = physical['angular_impulse']+support_h
                cumulative_p += applied_p; cumulative_h += applied_h
                cumulative_support6 += h*reaction6
                reference_support6 = descriptor.midpoint_reaction_integral(load0['load42'], h, index+1)
                reference_cont_support6 = descriptor.continuous_reaction_integral(load0['load42'], 0., state.time)
                support_impulse_errors = dict(force=float(np.linalg.norm(cumulative_support6[:3]-reference_support6[:3])/scales['momentum']),
                    couple=float(np.linalg.norm(cumulative_support6[3:]-reference_support6[3:])/scales['angular_momentum']))
                support_continuous_errors = dict(force=float(np.linalg.norm(cumulative_support6[:3]-reference_cont_support6[:3])/scales['momentum']),
                    couple=float(np.linalg.norm(cumulative_support6[3:]-reference_cont_support6[3:])/scales['angular_momentum']))
                cumulative_hmid += mid_h; cumulative_work += physical['exact_work']; cumulative_workmid += mid_work
                def defects(delta_p, delta_h, energy_change, impulse_p, impulse_h, impulse_hmid, work, workmid):
                    return dict(P=float(np.linalg.norm(delta_p-impulse_p)/scales['momentum']),
                        H_path=float(np.linalg.norm(delta_h-impulse_h)/scales['angular_momentum']),
                        H_midpoint=float(np.linalg.norm(delta_h-impulse_hmid)/scales['angular_momentum']),
                        E_exact_work=abs(energy_change-work)/scales['energy'],
                        E_midpoint_work=abs(energy_change-workmid)/scales['energy'])
                step = defects(dp, dh, now.total_energy-previous.total_energy, applied_p,
                    applied_h, mid_h, physical['exact_work'], mid_work)
                cumulative = defects(cp, ch, now.total_energy-initial.total_energy, cumulative_p,
                    cumulative_h, cumulative_hmid, cumulative_work, cumulative_workmid)
                endpoint = dict(state=json.loads(canonical(state)), accounting=accounting(now), q12=q.tolist(),
                    actual_spatial_velocity12=v.tolist(), continuous_q12=qc.tolist(), continuous_v12=vc.tolist(),
                    discrete_q12=qmid.tolist(), discrete_v12=vmid.tolist(), errors_continuous=cont,
                    errors_discrete=discrete, predicted_dispersion=prediction, step_defects=step,
                    cumulative_defects=cumulative, delta_P_n_s=dp.tolist(), delta_H_nm_s=dh.tolist(),
                    exact_path_P_n_s=physical['linear_impulse'].tolist(), exact_path_H_nm_s=physical['angular_impulse'].tolist(),
                    midpoint_H_nm_s=mid_h.tolist(), exact_path_work_j=physical['exact_work'], midpoint_work_j=mid_work,
                    support_reaction6=reaction6.tolist(), support_midpoint_P_n_s=support_p.tolist(),
                    support_midpoint_H_nm_s=support_h.tolist(), support_work_j=support_work,
                    applied_total_P_n_s=applied_p.tolist(), applied_total_H_nm_s=applied_h.tolist(),
                    linear_midpoint_support_reaction6=linear_mid_reaction6.tolist(),
                    linear_continuous_support_reaction6=linear_cont_reaction6.tolist(),
                    reaction_errors_discrete=reaction_errors, reaction_predicted_dispersion=reaction_dispersion,
                    cumulative_support_impulse6=cumulative_support6.tolist(),
                    linear_midpoint_support_impulse6=reference_support6.tolist(),
                    linear_continuous_support_impulse6=reference_cont_support6.tolist(),
                    support_impulse_errors_discrete=support_impulse_errors,
                    support_impulse_errors_continuous=support_continuous_errors,
                    stage_norm=candidate.stage_residual_norm, endpoint_algebraic_norm=candidate.endpoint_algebraic_norm,
                    stage_iterations=candidate.iterations, stage_backtracks=candidate.backtracks,
                    load_map_errors=load_errors, retained_candidate_audit=run.pop('pending_candidate'),
                    unissued_trial_observations=run.pop('unissued_trial_observations'))
                run['endpoints'].append(endpoint); evidence['accepted_steps'] += 1
                save(label+'_endpoint_'+str(index+1))
                assert max(support_impulse_errors.values()) <= CRITERIA['nonlinear_to_discrete_limit']
                assert max(step.values()) <= CRITERIA['normalized_defect_limit']
                assert max(cumulative.values()) <= CRITERIA['normalized_defect_limit']
                assert max(discrete.values()) <= CRITERIA['nonlinear_to_discrete_limit']
                assert now.elastic_consistency_witness/scales['energy'] <= CRITERIA['elastic_witness_limit']
                assert abs(endpoint_load.line_force_work-previous_load.line_force_work-physical['exact_work'])/scales['energy'] <= 1e-12
                assert np.count_nonzero(candidate.stage.inertia.mixed_inertia[z]) == 0
                assert np.count_nonzero(candidate.stage.inertia.mixed_mass[z]) == 0
                assert canonical(state.histories) == canonical(c._reference_origins)
                previous, previous_load = now, endpoint_load
            assert state.epoch == count and abs(state.time-duration) <= 8*np.finfo(float).eps*duration
            assert c._dynamic._active_session is None and c._work_session is None and len(c._dynamic._issued) == 1
        coarse = evidence['resolutions']['coarse']['endpoints']
        fine = evidence['resolutions']['fine']['endpoints']; common = fine[1::2]
        half = evidence['resolutions']['half_fine']['endpoints']
        comparisons = {}
        for field in fields:
            for kind in ('errors_continuous', 'predicted_dispersion'):
                comparisons[kind+'_'+field] = compare(max(row[kind][field] for row in coarse),
                    max(row[kind][field] for row in common), CRITERIA['trajectory_floor'], CRITERIA['time_refinement_ratio'])
            comparisons['amplitude_'+field] = compare(max(row['errors_discrete'][field] for row in fine),
                max(row['errors_discrete'][field] for row in half), CRITERIA['trajectory_floor'], CRITERIA['amplitude_refinement_ratio'])
        for component in ('force', 'couple'):
            comparisons['support_impulse_time_'+component] = compare(
                max(row['support_impulse_errors_continuous'][component] for row in coarse),
                max(row['support_impulse_errors_continuous'][component] for row in common),
                CRITERIA['trajectory_floor'], CRITERIA['time_refinement_ratio'])
            comparisons['support_impulse_amplitude_'+component] = compare(
                max(row['support_impulse_errors_discrete'][component] for row in fine),
                max(row['support_impulse_errors_discrete'][component] for row in half),
                CRITERIA['trajectory_floor'], CRITERIA['amplitude_refinement_ratio'])
        for key in coarse[0]['cumulative_defects']:
            comparisons['invariant_'+key] = compare(max(row['cumulative_defects'][key] for row in coarse),
                max(row['cumulative_defects'][key] for row in common), CRITERIA['invariant_floor'], CRITERIA['time_refinement_ratio'])
        evidence['comparisons'] = comparisons
        save('completed_comparisons')
        assert all(row['passes'] for row in comparisons.values()), comparisons
        assert evidence['accepted_steps'] == 20
        evidence['status'] = 'PASS'; save('complete')
        record_property('clamped_descriptor_support_summary', json.dumps(comparisons))
    except BaseException as error:
        evidence.update(status='NONPASS', failure_type=type(error).__name__, failure=str(error))
        save('failure'); raise
