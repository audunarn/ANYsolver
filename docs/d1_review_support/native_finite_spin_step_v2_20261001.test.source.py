"""One prospective finite-spin step; returned-stage evidence, no Euler oracle."""
from dataclasses import asdict
from fractions import Fraction as F
from hashlib import sha256
import json
import os
from pathlib import Path
from time import perf_counter
import numpy as np

from anysolver.ge_beam3_native_dynamics import create_analysis, SELECTOR, workflow_provenance
from anysolver._ge_beam3_p5_seeded.core import canonical, sha
from test_ge_beam3_native_midpoint import make_analysis
from native_forced_response_reference import positions

CRITERIA = dict(spatial_spin_rad_per_s=[35., -25., 20.], dt_seconds=.0005,
    maximum_accepted_steps=1, internal_time_limit_seconds=120.,
    explicit_stage_solve_tolerance=1e-12, scientific_stage_gate=1e-11,
    endpoint_balance_gate=1e-11, normalized_defect_limit=1e-6,
    elastic_witness_limit=1e-10, origin_high_m=[0., 0., 0.], origin_low_m=[0., 0., 0.],
    length_scale_m=2., maximum_returned_stage_observations=128)
RAW_SHA = '705b627848aef2df9ce17cdce2dda937ea1ae29d1031a855f48ff567181248f7'
OLD_INPUT_SHA = '07b3f12777cd21ed5932fe14f51ec3254ba1796f6627d3ce8373be4c2996926d'
FIXTURE_SHA = '426f673d40e82a4d554c3964dc9b51b4ca5638f180f3f985e4ba85c974ebc05d'
P = (0, 1, 2, 6, 7, 8, 12, 13, 14, 18, 19, 20, 21, 22, 23)
Z = (3, 4, 5, 9, 10, 11, 15, 16, 17, *range(24, 42))


def accounting(value):
    row = asdict(value)
    row['rank_mass_checks'] = json.loads(row['rank_mass_checks'])
    return json.loads(canonical(row))


def momentum_delta(now, before, name):
    return np.array([float(F(float(h))+F(float(l))-F(float(h0))-F(float(l0)))
        for h, l, h0, l0 in zip(getattr(now, name+'_momentum'), getattr(now, name+'_momentum_low'),
            getattr(before, name+'_momentum'), getattr(before, name+'_momentum_low'))])


def skew(vector):
    x, y, z = vector
    return np.array(((0., -z, y), (z, 0., -x), (-y, x, 0.)))


def rigid_work_maps(mechanical):
    # World O=0, including all nodal algebraic frame and both cell moment rows.
    t, u = np.zeros((42, 3)), np.zeros((42, 3))
    for node, point in enumerate(positions(mechanical)):
        t[6*node:6*node+3] = np.eye(3)
        u[6*node:6*node+3] = -skew(point)
        u[6*node+3:6*node+6] = np.eye(3)
    u[18:21] = u[21:24] = np.eye(3)
    return t, u


def stage_snapshot(context, prior, unknown, h, stage, *, evidence_kind='original_returned_unissued_stage'):
    """Evidence-only arithmetic on the ORIGINAL returned stage; no owner calls.

    Rational differences compare the exact arithmetic of the represented input
    floats with the actual vm/am, not with an unknown exact physical trajectory.
    Matrix effects are diagnostics, not an automatic error/failure attribution.
    """
    u = np.asarray(unknown).copy()
    exact_v, exact_a, dv, da = (np.zeros(24) for _ in range(4))
    for index in P:
        vf = F(float(u[index]))/F(float(h))
        af = 2*(vf-F(float(prior.physical_velocity24[index])))/F(float(h))
        exact_v[index], exact_a[index] = float(vf), float(af)
        dv[index] = float(vf-F(float(stage.physical_velocity24[index])))
        da[index] = float(af-F(float(stage.physical_acceleration24[index])))
    pose_error, pose_velocity = np.zeros((3, 3)), np.zeros((3, 3))
    for node in range(3):
        for axis in range(3):
            dx = (F(float(stage.mechanical.positions[node, axis]))
                  +F(float(stage.mechanical.position_low[node, axis]))
                  -F(float(prior.mechanical.positions[node, axis]))
                  -F(float(prior.mechanical.position_low[node, axis])))
            pose_error[node, axis] = float(dx-F(float(u[6*node+axis]))/2)
            pose_velocity[node, axis] = float(2*dx/F(float(h)))
    inactive = [i for i in range(24) if i not in P]
    ulp = np.abs(np.spacing(u))
    mass_delta = stage.inertia.mixed_mass[:, :24]@da
    velocity_delta = stage.inertia.mixed_velocity_derivative[:, :24]@dv
    # Absolute-J times one unknown ULP is a local linear resolution indicator,
    # not a bound on nonlinear truncation, constitutive or derivative errors.
    j_ulp = np.abs(stage.jacobian)@ulp
    scale, length = context._gate_inputs()  # Actual guarded selected-owner values.
    free = list(context.free)
    t, rot = rigid_work_maps(stage.mechanical)
    row = dict(unknown42=u.tolist(), displacement_m=u[:18].reshape(3, 6)[:, :3].tolist(),
        cell_phi_rad=u[18:24].reshape(2, 3).tolist(), algebraic_frame_delta_rad=u[:18].reshape(3, 6)[:, 3:].tolist(),
        resultant_delta18=u[24:].tolist(), mechanical=json.loads(canonical(stage.mechanical)),
        actual_vm24=stage.physical_velocity24.tolist(), actual_am24=stage.physical_acceleration24.tolist(),
        exact_input_arithmetic_vm_rounded24=exact_v.tolist(), exact_input_arithmetic_am_rounded24=exact_a.tolist(),
        exact_input_minus_actual_vm24=dv.tolist(), exact_input_minus_actual_am24=da.tolist(),
        pose_delta_minus_half_unknown_m=pose_error.tolist(), compensated_pose_vm_m_per_s=pose_velocity.tolist(),
        unknown_ulp42=ulp.tolist(), acceleration_rounding_mass_effect42=mass_delta.tolist(),
        velocity_rounding_first_order_effect42=velocity_delta.tolist(), jacobian_unknown_ulp_indicator42=j_ulp.tolist(),
        jacobian_unknown_ulp_indicator_scaled_l2=float(np.linalg.norm((j_ulp/scale)[free])),
        acceleration_rounding_mass_effect_scaled_l2=float(np.linalg.norm((mass_delta/scale)[free])),
        velocity_rounding_first_order_effect_scaled_l2=float(np.linalg.norm((velocity_delta/scale)[free])),
        R42=stage.structural_residual.tolist(), I42=stage.inertia.mixed_inertia.tolist(), e42=stage.residual.tolist(),
        J42=stage.jacobian.tolist(), structural_J42=stage.structural_jacobian.tolist(),
        M42=stage.inertia.mixed_mass.tolist(), I_v42=stage.inertia.mixed_velocity_derivative.tolist(),
        I_q42=stage.inertia.mixed_configuration_derivative.tolist(), configuration_map42=stage.configuration_map.tolist(),
        actual_residual_scales42=np.asarray(scale).tolist(), actual_length_scale_m=float(length),
        scaled_free_norm=float(np.linalg.norm((stage.residual/scale)[free])),
        scaled_physical_norm=float(np.linalg.norm((stage.residual/scale)[list(P)])),
        scaled_algebraic_norm=float(np.linalg.norm((stage.residual/scale)[list(Z)])),
        rigid_residual_force_n=(t.T@stage.residual).tolist(), rigid_residual_moment_nm=(rot.T@stage.residual).tolist(),
        structural_rigid_force_n=(t.T@stage.structural_residual).tolist(),
        structural_rigid_moment_nm=(rot.T@stage.structural_residual).tolist(),
        inertia_rigid_force_n=(t.T@stage.inertia.mixed_inertia).tolist(),
        inertia_rigid_moment_nm=(rot.T@stage.inertia.mixed_inertia).tolist(),
        R_plus_I_minus_e42=(stage.structural_residual+stage.inertia.mixed_inertia-stage.residual).tolist(),
        exact_zero_algebraic_inertia=bool(np.count_nonzero(stage.inertia.mixed_inertia[list(Z)]) == 0),
        exact_zero_inactive_velocity_acceleration=bool(np.count_nonzero(stage.physical_velocity24[inactive]) == 0
            and np.count_nonzero(stage.physical_acceleration24[inactive]) == 0),
        context_sha256=context._identity, predecessor_sha256=sha(prior), predecessor_epoch=prior.epoch,
        stage_sha256=sha(stage), trial_session_active=context._work_session is not None,
        trial_session_provenance={'kind': evidence_kind,
            'session_object_id': None if context._work_session is None else id(context._work_session), 'context_object_id': id(context)})
    # Diagnostic factorization never changes the original stage or solver.
    try:
        correction = np.zeros(42)
        correction[free] = np.linalg.solve(stage.jacobian[np.ix_(free, free)], -stage.residual[free])
        condition = float(np.linalg.cond(stage.jacobian[np.ix_(free, free)]))
        if not np.isfinite(correction).all():
            raise np.linalg.LinAlgError('nonfinite diagnostic Newton solve')
        row.update(newton_correction42=correction.tolist(),
            normalized_newton_correction=context._correction(stage.mechanical, correction),
            jacobian_free_condition=condition if np.isfinite(condition) else None,
            jacobian_condition_resolved=bool(np.isfinite(condition)),
            correction_below_half_ulp_physical=(abs(correction[list(P)]) < .5*ulp[list(P)]).tolist())
    except np.linalg.LinAlgError as error:
        row['diagnostic_factorization_failure'] = str(error)
    return row


def test_one_finite_spin_step_resolution_and_actual_balance(record_property):
    started = perf_counter()
    inputs = json.loads(Path(os.environ['NATIVE_FINITE_SPIN_STEP_INPUTS']).read_text(encoding='utf-8-sig'))
    output = Path(os.environ['NATIVE_FINITE_SPIN_STEP_RAW_OUTPUT'])
    assert not output.exists() and inputs['criteria'] == CRITERIA
    evidence = dict(status='RUNNING', accepted_steps=0, criteria=CRITERIA, unissued_stages=[],
        scope='One finite-spin convergence/resolution screen; no finite-angle trajectory/reference claim')
    def save(stage):
        evidence.update(last_stage=stage, elapsed_seconds=perf_counter()-started)
        output.write_text(json.dumps(evidence, indent=2, allow_nan=False)+'\n')
        print(json.dumps(dict(stage=stage, elapsed_seconds=evidence['elapsed_seconds'])), flush=True)
        assert evidence['elapsed_seconds'] < CRITERIA['internal_time_limit_seconds']
    def authentic(label, expected):
        item = inputs['historical'][label]
        data = Path(item['path']).read_bytes()
        assert item['sha256'] == expected == sha256(data).hexdigest()
        return data
    try:
        saved = json.loads(authentic('raw', RAW_SHA))['reference']
        old_inputs = json.loads(authentic('inputs', OLD_INPUT_SHA))
        authentic('fixture', FIXTURE_SHA)
        changed = inputs['historical_source_overrides']
        assert changed == {'_ge_beam3_native_midpoint.py':
            'f2c494a93315b541500a8f6aa7330bfae2f731ac9f2251f1585704638f03f71a'}
        for path, expected in old_inputs['source_sha256'].items():
            expected = changed.get(Path(path).name, expected)
            assert sha256(Path(path).read_bytes()).hexdigest() == expected == inputs['source_sha256'][path]
        for path, expected in inputs['source_sha256'].items():
            assert sha256(Path(path).read_bytes()).hexdigest() == expected
        _, definition = make_analysis()  # Authentic builder only; no old test body.
        owner = create_analysis(SELECTOR, (definition,), (), inertia_order=24,
            stage_residual_tolerance=CRITERIA['explicit_stage_solve_tolerance'],
            momentum_origin_high=tuple(CRITERIA['origin_high_m']), momentum_origin_low=tuple(CRITERIA['origin_low_m']))
        c = owner._context
        assert c.fixed == () and tuple(c.physical_free) == P and tuple(c.algebraic_free) == Z
        assert c.load_pattern is None and c.stage_residual_tolerance == 1e-12
        assert c.element.operator.order == 4 and len(c.analysis._elements) == 1
        assert canonical(c._reference_mechanical) == canonical(saved['reference_mechanical'])
        assert canonical(c._reference_origins) == canonical(saved['virgin_histories'])
        assert np.array_equal(c.analysis._inertias[c.element.element_id], saved['section_inertia'])
        reference = c._reference_mechanical
        omega = np.asarray(CRITERIA['spatial_spin_rad_per_s'])
        velocity = np.zeros(24)
        for node, point in enumerate(positions(reference)):
            velocity[6*node:6*node+3] = np.cross(omega, point)
        velocity[18:21] = velocity[21:24] = omega
        m0 = np.asarray(saved['M42'])
        translation = np.zeros((42, 3))
        for node in range(3):
            translation[6*node:6*node+3] = np.eye(3)
        mass = float(np.trace(translation.T@m0@translation)/3.)
        energy = float(.5*velocity@m0[:24, :24]@velocity)
        speed = float(np.sqrt(2.*energy/mass))
        scales = dict(mass=mass, energy=energy, velocity=speed, momentum=mass*speed,
            angular_momentum=mass*CRITERIA['length_scale_m']*speed)
        assert all(np.isfinite(x) and x > 0. for x in scales.values())
        evidence.update(scales=scales, independent_mass_input_M42=saved['M42'],
            definition=json.loads(definition.raw), section_inertia=saved['section_inertia'],
            initial_velocity24=velocity.tolist(), provenance=workflow_provenance(owner))
        save('authenticated_fixture_scales_before_initialization')
        state = owner.initialize(physical_velocity15=velocity[list(P)])
        initial = owner.endpoint_accounting(state)
        with c._atomic_operation():
            c._guard(); work = c._loaded_work(state.mechanical, state.histories)
            inertia = c._inertia(state.mechanical, state.physical_velocity24, state.physical_acceleration24)
            scale, length = c._gate_inputs()
        balance = work.residual+inertia.mixed_inertia
        evidence['initial'] = dict(state=json.loads(canonical(state)), accounting=accounting(initial),
            R42=work.residual.tolist(), I42=inertia.mixed_inertia.tolist(), balance42=balance.tolist(),
            J42=work.spatial_jacobian.tolist(), M42=inertia.mixed_mass.tolist(),
            I_v42=inertia.mixed_velocity_derivative.tolist(), I_q42=inertia.mixed_configuration_derivative.tolist(),
            actual_residual_scales42=np.asarray(scale).tolist(), actual_length_scale_m=float(length),
            scaled_free_balance=float(np.linalg.norm((balance/scale)[list(c.free)])),
            initial_checks=owner.initial_checks, current_state_sha256=sha(state))
        save('actual_initial_signed_balance')
        assert canonical(state.mechanical) == canonical(reference)
        assert np.array_equal(state.physical_velocity24, velocity)
        assert np.linalg.norm(inertia.mixed_mass-m0)/np.linalg.norm(m0) <= 1e-12
        assert abs(initial.kinetic_energy-energy)/energy <= 1e-12
        assert evidence['initial']['scaled_free_balance'] <= CRITERIA['endpoint_balance_gate']
        assert np.count_nonzero(state.physical_velocity24[[i for i in range(24) if i not in P]]) == 0
        assert np.count_nonzero(state.physical_acceleration24[[i for i in range(24) if i not in P]]) == 0
        assert np.count_nonzero(inertia.mixed_inertia[list(Z)]) == 0
        original_stage = c._stage
        def observe(prior, unknown, h, token=None):
            actual = original_stage(prior, unknown, h, token)
            # Persist actual returned physics before any diagnostic arithmetic.
            row = dict(unknown42=np.asarray(unknown).tolist(),
                R42=actual.structural_residual.tolist(), I42=actual.inertia.mixed_inertia.tolist(),
                e42=actual.residual.tolist(), J42=actual.jacobian.tolist(), M42=actual.inertia.mixed_mass.tolist(),
                actual_vm24=actual.physical_velocity24.tolist(), actual_am24=actual.physical_acceleration24.tolist(),
                mechanical=json.loads(canonical(actual.mechanical)), context_sha256=c._identity,
                predecessor_sha256=sha(prior), predecessor_epoch=prior.epoch,
                original_returned_stage_preserved=True)
            evidence['unissued_stages'].append(row)
            save('original_returned_stage_'+str(len(evidence['unissued_stages'])))
            try:
                row.update(stage_snapshot(c, prior, unknown, h, actual))
            except Exception as error:
                row['diagnostic_failure'] = {'type': type(error).__name__, 'message': str(error)}
                save('returned_stage_diagnostic_failure')
                raise
            assert len(evidence['unissued_stages']) <= CRITERIA['maximum_returned_stage_observations']
            return actual  # Same object; no production equation or solver decision replacement.
        c._stage = observe
        try:
            candidate = owner.trial(state, dt=CRITERIA['dt_seconds'])
        finally:
            c._stage = original_stage
            save('trial_return_or_failure')
        audit = owner.candidate_stage_audit(candidate)
        evidence['candidate'] = dict(endpoint=json.loads(canonical(candidate.endpoint)),
            unknown42=audit.unknown42.tolist(), stage_sha256=audit.stage_sha256,
            candidate_sha256=audit.candidate_sha256, predecessor_sha256=audit.predecessor_sha256,
            predecessor_epoch=audit.predecessor_epoch, endpoint_epoch=audit.endpoint_epoch,
            audit_authentication_session=json.loads(audit.session_provenance),
            stage_residual_norm=candidate.stage_residual_norm, endpoint_algebraic_norm=candidate.endpoint_algebraic_norm,
            iterations=candidate.iterations, backtracks=candidate.backtracks,
            authenticated_stage_arithmetic_snapshot=stage_snapshot(c, state, audit.unknown42, candidate.dt, audit.stage,
                evidence_kind='authenticated_issued_stage_evidence_copy'))
        save('authenticated_candidate_before_commit')
        assert candidate.stage_residual_norm <= CRITERIA['scientific_stage_gate']
        assert candidate.endpoint_algebraic_norm <= CRITERIA['endpoint_balance_gate']
        state = owner.commit(candidate)
        evidence['accepted_steps'] = 1
        now = owner.endpoint_accounting(state)
        with c._atomic_operation():
            c._guard(); work = c._loaded_work(state.mechanical, state.histories)
            inertia = c._inertia(state.mechanical, state.physical_velocity24, state.physical_acceleration24)
        dp, dh = momentum_delta(now, initial, 'linear'), momentum_delta(now, initial, 'angular')
        defects = dict(P=float(np.linalg.norm(dp)/scales['momentum']),
            H=float(np.linalg.norm(dh)/scales['angular_momentum']), E=abs(now.total_energy-initial.total_energy)/energy)
        evidence['endpoint'] = dict(state=json.loads(canonical(state)), accounting=accounting(now),
            R42=work.residual.tolist(), I42=inertia.mixed_inertia.tolist(), balance42=(work.residual+inertia.mixed_inertia).tolist(),
            J42=work.spatial_jacobian.tolist(), M42=inertia.mixed_mass.tolist(),
            scaled_free_balance=c._norm(work.residual+inertia.mixed_inertia, c.free),
            delta_P_n_s=dp.tolist(), delta_H_nm_s=dh.tolist(), normalized_step_and_cumulative_defects=defects,
            elastic_witness_normalized=now.elastic_consistency_witness/energy)
        save('actual_issued_endpoint_before_gates')
        assert max(defects.values()) <= CRITERIA['normalized_defect_limit']
        assert evidence['endpoint']['scaled_free_balance'] <= CRITERIA['endpoint_balance_gate']
        assert now.elastic_consistency_witness/energy <= CRITERIA['elastic_witness_limit']
        assert canonical(state.histories) == canonical(c._reference_origins)
        assert state.epoch == 1 and state.time == CRITERIA['dt_seconds']
        evidence['status'] = 'PASS'; save('complete')
        record_property('finite_spin_one_step_summary', json.dumps(defects))
    except BaseException as error:
        evidence.update(status='NONPASS', failure_type=type(error).__name__, failure=str(error))
        save('failure'); raise
