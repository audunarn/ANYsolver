"""One acceleration-chart finite-spin step; no Euler/trajectory oracle."""
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
    length_scale_m=2., maximum_returned_stage_observations=128,
    stage_coordinates='acceleration', directional_intervals=[1e-5, 5e-6],
    directional_tangent_limit=1e-5, arithmetic_gamma_operations=64)
RAW_SHA = '705b627848aef2df9ce17cdce2dda937ea1ae29d1031a855f48ff567181248f7'
OLD_INPUT_SHA = '07b3f12777cd21ed5932fe14f51ec3254ba1796f6627d3ce8373be4c2996926d'
FIXTURE_SHA = '426f673d40e82a4d554c3964dc9b51b4ca5638f180f3f985e4ba85c974ebc05d'
FAILED_RAW_SHA = '63338a2594bd43c8bb996211ff12187e1e896bc88cf41d49ddecc4b102762d6f'
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


def stage_snapshot(context, prior, unknown, h, stage, *, evidence_kind='original_returned_unissued_stage', represented_increment=None):
    """Evidence-only arithmetic on the ORIGINAL returned stage; no owner calls.

    Rational differences compare the exact arithmetic of the represented input
    floats with the actual vm/am, not with an unknown exact physical trajectory.
    Matrix effects are diagnostics, not an automatic error/failure attribution.
    """
    u = np.asarray(unknown).copy()
    increment = u.copy()
    increment[list(P)] = h*prior.physical_velocity24[list(P)]+(.5*h*h)*u[list(P)]
    if represented_increment is not None:
        increment = np.array(represented_increment, copy=True)
    exact_v, exact_a, dv, da = (np.zeros(24) for _ in range(4))
    for index in P:
        vf = F(float(prior.physical_velocity24[index]))+F(float(h))*F(float(u[index]))/2
        af = F(float(u[index]))
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
            index = 6*node+axis
            midpoint_delta = (F(float(h))*F(float(prior.physical_velocity24[index]))/2
                              +F(float(h))**2*F(float(u[index]))/4)
            pose_error[node, axis] = float(dx-midpoint_delta)
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
    row = dict(stage_coordinates='acceleration', unknown42=u.tolist(), increment42=increment.tolist(),
        midpoint_acceleration_physical15=u[list(P)].tolist(),
        displacement_m=increment[:18].reshape(3, 6)[:, :3].tolist(),
        cell_phi_rad=increment[18:24].reshape(2, 3).tolist(), algebraic_frame_delta_rad=u[:18].reshape(3, 6)[:, 3:].tolist(),
        resultant_delta18=u[24:].tolist(), mechanical=json.loads(canonical(stage.mechanical)),
        actual_vm24=stage.physical_velocity24.tolist(), actual_am24=stage.physical_acceleration24.tolist(),
        exact_input_arithmetic_vm_rounded24=exact_v.tolist(), exact_input_arithmetic_am_rounded24=exact_a.tolist(),
        exact_input_minus_actual_vm24=dv.tolist(), exact_input_minus_actual_am24=da.tolist(),
        pose_delta_minus_exact_chart_expression_m=pose_error.tolist(), compensated_pose_vm_m_per_s=pose_velocity.tolist(),
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
        increment_correction = correction.copy()
        increment_correction[list(P)] *= .5*h*h
        row.update(newton_correction42=correction.tolist(), increment_newton_correction42=increment_correction.tolist(),
            normalized_newton_correction=context._correction(stage.mechanical, increment_correction),
            jacobian_free_condition=condition if np.isfinite(condition) else None,
            jacobian_condition_resolved=bool(np.isfinite(condition)),
            correction_below_half_ulp_physical=(abs(correction[list(P)]) < .5*ulp[list(P)]).tolist())
    except np.linalg.LinAlgError as error:
        row['diagnostic_factorization_failure'] = str(error)
    return row


def chart_equivalence(prior, unknown, h, stage):
    """Independent represented-input arithmetic bounds, not residual tolerances.

    Gamma64 bounds these short product/sum/divide chains with normal binary64
    inputs. It does not certify mechanics, integration or nonlinear truncation.
    No second owner or old-chart production stage is evaluated.
    """
    eps = np.finfo(float).eps
    gamma = 64*eps/(1-64*eps)
    p = list(P)
    a = unknown[p]
    v0 = prior.physical_velocity24[p]
    increment = h*v0+(.5*h*h)*a
    old_vm = increment/h
    old_am = 2*(old_vm-v0)/h
    vm_bound = gamma*(2*np.abs(v0)+h*np.abs(a))
    am_bound = gamma*(4*np.abs(v0)/h+3*np.abs(a))
    pose_error, pose_bound = np.zeros((3, 3)), np.zeros((3, 3))
    for node in range(3):
        for axis in range(3):
            index = 6*node+axis
            terms = (F(float(prior.mechanical.positions[node, axis])),
                F(float(prior.mechanical.position_low[node, axis])),
                F(float(h))*F(float(prior.physical_velocity24[index]))/2,
                F(float(h))**2*F(float(unknown[index]))/4)
            actual = F(float(stage.mechanical.positions[node, axis]))+F(float(stage.mechanical.position_low[node, axis]))
            pose_error[node, axis] = float(abs(actual-sum(terms)))
            pose_bound[node, axis] = gamma*float(sum(abs(term) for term in terms))
    cell_errors = []
    for cell in (0, 1):
        ids = slice(18+3*cell, 21+3*cell)
        phi = h*prior.physical_velocity24[ids]+(.5*h*h)*unknown[ids]
        half = phi/2
        angle = np.linalg.norm(half)
        cross = skew(half)
        # Independent Rodrigues formula for this resolved nonzero smooth branch.
        assert angle > 0 and np.isfinite(angle)
        rotation = np.eye(3)+(np.sin(angle)/angle)*cross+((1-np.cos(angle))/angle**2)*(cross@cross)
        expected = rotation@prior.mechanical.cell_rotations[0, cell]
        cell_errors.append(float(np.linalg.norm(stage.mechanical.cell_rotations[0, cell]-expected)))
    row = dict(gamma64=gamma, old_increment_vm24_physical=old_vm.tolist(),
        old_increment_am24_physical=old_am.tolist(),
        vm_difference=np.abs(old_vm-stage.physical_velocity24[p]).tolist(), vm_operation_bound=vm_bound.tolist(),
        am_difference=np.abs(old_am-stage.physical_acceleration24[p]).tolist(), am_operation_bound=am_bound.tolist(),
        midpoint_position_error_m=pose_error.tolist(), midpoint_position_operation_bound_m=pose_bound.tolist(),
        independent_rodrigues_error=cell_errors, independent_rodrigues_operation_bound=64*eps*3,
        actual_am_equals_authoritative_unknown=bool(np.array_equal(stage.physical_acceleration24[p], a)))
    return row


def directional_check(context, prior, unknown, h, stage, evidence, save):
    """Two frozen centered differences of the actual selected chart, all42 rows."""
    direction = np.sin(np.arange(42)+1.)
    direction[list(P)] *= 800.  # Unit chart direction maps to 1e-4 physical increment.
    direction[[3, 4, 5, 9, 10, 11, 15, 16, 17]] *= 1e-4
    direction[24:] *= 1e-4*max(1., np.linalg.norm(stage.mechanical.resultants))
    scale, _ = context._gate_inputs()
    expected = stage.jacobian@direction
    rows = []
    evidence['directional_tangent'] = rows
    def retained(actual, perturbed, side, interval):
        # Save each ORIGINAL returned FD stage before evaluating the pair/error.
        row = dict(evidence_kind='directional_'+side, interval=interval,
            stage_coordinates='acceleration', unknown42=perturbed.tolist(),
            R42=actual.structural_residual.tolist(), I42=actual.inertia.mixed_inertia.tolist(),
            e42=actual.residual.tolist(), J42=actual.jacobian.tolist(), M42=actual.inertia.mixed_mass.tolist(),
            actual_vm24=actual.physical_velocity24.tolist(), actual_am24=actual.physical_acceleration24.tolist(),
            mechanical=json.loads(canonical(actual.mechanical)), stage_sha256=sha(actual),
            context_sha256=context._identity, predecessor_sha256=sha(prior), predecessor_epoch=prior.epoch,
            original_returned_stage_preserved=True)
        evidence['unissued_stages'].append(row)
        save('original_returned_directional_'+side)
        assert len(evidence['unissued_stages']) <= CRITERIA['maximum_returned_stage_observations']
    for interval in CRITERIA['directional_intervals']:
        plus_unknown = np.array(unknown+interval*direction, dtype=np.float64)
        minus_unknown = np.array(unknown-interval*direction, dtype=np.float64)
        plus = context.evaluate_stage(prior, plus_unknown, dt=h)
        retained(plus, plus_unknown, 'plus', interval)
        minus = context.evaluate_stage(prior, minus_unknown, dt=h)
        retained(minus, minus_unknown, 'minus', interval)
        difference = (plus.residual-minus.residual)/(2*interval)
        denominator = float(np.linalg.norm(expected/scale))
        assert denominator > 0 and np.isfinite(denominator)
        rows.append(dict(interval=interval, direction42=direction.tolist(), analytic_derivative42=expected.tolist(),
            centered_derivative42=difference.tolist(), plus_R42=plus.structural_residual.tolist(),
            plus_I42=plus.inertia.mixed_inertia.tolist(), minus_R42=minus.structural_residual.tolist(),
            minus_I42=minus.inertia.mixed_inertia.tolist(), scaled_analytic_norm=denominator,
            relative_scaled_error=float(np.linalg.norm((difference-expected)/scale)/denominator)))
    return rows


def endpoint_chart_mapping(prior, endpoint, unknown, h, increment):
    """Use compensated issued translations and authenticated represented phi."""
    eps = np.finfo(float).eps
    gamma = 64*eps/(1-64*eps)
    errors, bounds = np.zeros((3, 3)), np.zeros((3, 3))
    for node in range(3):
        for axis in range(3):
            index = 6*node+axis
            terms = (F(float(prior.mechanical.positions[node, axis])),
                F(float(prior.mechanical.position_low[node, axis])),
                F(float(h))*F(float(prior.physical_velocity24[index])),
                F(float(h))**2*F(float(unknown[index]))/2)
            actual = F(float(endpoint.mechanical.positions[node, axis]))+F(float(endpoint.mechanical.position_low[node, axis]))
            errors[node, axis] = float(abs(actual-sum(terms)))
            bounds[node, axis] = gamma*float(sum(abs(term) for term in terms))
    p = list(P)
    velocity_errors = []
    velocity_bounds = []
    for index in P:
        exact = F(float(prior.physical_velocity24[index]))+F(float(h))*F(float(unknown[index]))
        velocity_errors.append(float(abs(exact-F(float(endpoint.physical_velocity24[index])))))
        velocity_bounds.append(gamma*(abs(prior.physical_velocity24[index])+h*abs(unknown[index])))
    frames = []
    for cell in (0, 1):
        phi = increment[18+3*cell:21+3*cell]
        angle = np.linalg.norm(phi)
        cross = skew(phi)
        assert angle > 0 and np.isfinite(angle)
        rotation = np.eye(3)+(np.sin(angle)/angle)*cross+((1-np.cos(angle))/angle**2)*(cross@cross)
        expected = rotation@prior.mechanical.cell_rotations[0, cell]
        frames.append(float(np.linalg.norm(endpoint.mechanical.cell_rotations[0, cell]-expected)))
    return dict(position_error_m=errors.tolist(), position_operation_bound_m=bounds.tolist(),
        velocity_error24_physical=velocity_errors, velocity_operation_bound24_physical=velocity_bounds,
        cell_phi_from_audit=increment[18:24].tolist(), independent_rodrigues_error=frames,
        independent_rodrigues_operation_bound=64*eps*3)


def test_one_acceleration_chart_finite_spin_step(record_property):
    started = perf_counter()
    inputs = json.loads(Path(os.environ['NATIVE_FINITE_SPIN_ACCELERATION_INPUTS']).read_text(encoding='utf-8-sig'))
    output = Path(os.environ['NATIVE_FINITE_SPIN_ACCELERATION_RAW_OUTPUT'])
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
        failed = json.loads(authentic('failed_increment_raw', FAILED_RAW_SHA))
        assert failed['status'] == 'NONPASS' and failed['accepted_steps'] == 0
        changed = inputs['historical_source_overrides']
        assert changed == {'_ge_beam3_native_midpoint.py':
            '2c8e243e74f0b6eafff485b536f08242a51154d31dd8500afe689e10b2f265df',
            'ge_beam3_native_dynamics.py': 'aeba9bb1dbc7aa2daa0eb9df0f6a1ac49e43f476bafefeb76dbbc4239654326b',
            '_ge_beam3_native_dynamic_restart.py': '5bbbb4f7c99ef04483183f112c2c96dce19bc55f9f58cb9f3eecefe2065cf320'}
        for path, expected in old_inputs['source_sha256'].items():
            expected = changed.get(Path(path).name, expected)
            assert sha256(Path(path).read_bytes()).hexdigest() == expected == inputs['source_sha256'][path]
        for path, expected in inputs['source_sha256'].items():
            assert sha256(Path(path).read_bytes()).hexdigest() == expected
        _, definition = make_analysis()  # Authentic builder only; no old test body.
        owner = create_analysis(SELECTOR, (definition,), (), inertia_order=24,
            stage_residual_tolerance=CRITERIA['explicit_stage_solve_tolerance'],
            stage_coordinates=CRITERIA['stage_coordinates'],
            momentum_origin_high=tuple(CRITERIA['origin_high_m']), momentum_origin_low=tuple(CRITERIA['origin_low_m']))
        c = owner._context
        assert c.fixed == () and tuple(c.physical_free) == P and tuple(c.algebraic_free) == Z
        assert c.load_pattern is None and c.stage_residual_tolerance == 1e-12 and c.stage_coordinates == 'acceleration'
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
        historical_initial = failed['initial']
        for key in ('mechanical', 'physical_velocity24', 'physical_acceleration24', 'histories'):
            assert canonical(evidence['initial']['state'][key]) == canonical(historical_initial['state'][key])
        for key in ('R42', 'I42', 'M42', 'balance42'):
            assert canonical(evidence['initial'][key]) == canonical(historical_initial[key])
        assert initial.total_energy == historical_initial['accounting']['total_energy']
        evidence['historical_increment_initial_physics_equal'] = True
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
            unknown42=audit.unknown42.tolist(), stage_coordinates=audit.stage_coordinates,
            increment42=audit.increment42.tolist(), stage_sha256=audit.stage_sha256,
            candidate_sha256=audit.candidate_sha256, predecessor_sha256=audit.predecessor_sha256,
            predecessor_epoch=audit.predecessor_epoch, endpoint_epoch=audit.endpoint_epoch,
            audit_authentication_session=json.loads(audit.session_provenance),
            stage_residual_norm=candidate.stage_residual_norm, endpoint_algebraic_norm=candidate.endpoint_algebraic_norm,
            iterations=candidate.iterations, backtracks=candidate.backtracks,
            authenticated_stage_arithmetic_snapshot=stage_snapshot(c, state, audit.unknown42, candidate.dt, audit.stage,
                evidence_kind='authenticated_issued_stage_evidence_copy', represented_increment=audit.increment42))
        save('authenticated_candidate_before_commit')
        assert audit.stage_coordinates == 'acceleration'
        assert np.array_equal(audit.stage.physical_acceleration24[list(P)], audit.unknown42[list(P)])
        evidence['chart_equivalence'] = chart_equivalence(state, audit.unknown42, candidate.dt, audit.stage)
        directional_check(c, state, audit.unknown42, candidate.dt, audit.stage, evidence, save)
        save('independent_chart_checks_before_gates')
        equivalence = evidence['chart_equivalence']
        assert equivalence['actual_am_equals_authoritative_unknown']
        assert np.all(np.asarray(equivalence['vm_difference']) <= equivalence['vm_operation_bound'])
        assert np.all(np.asarray(equivalence['am_difference']) <= equivalence['am_operation_bound'])
        assert np.all(np.asarray(equivalence['midpoint_position_error_m']) <= equivalence['midpoint_position_operation_bound_m'])
        assert max(equivalence['independent_rodrigues_error']) <= equivalence['independent_rodrigues_operation_bound']
        assert max(row['relative_scaled_error'] for row in evidence['directional_tangent']) <= CRITERIA['directional_tangent_limit']
        assert candidate.stage_residual_norm <= CRITERIA['scientific_stage_gate']
        assert candidate.endpoint_algebraic_norm <= CRITERIA['endpoint_balance_gate']
        predecessor = state
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
        evidence['endpoint']['chart_mapping'] = endpoint_chart_mapping(predecessor, state,
            audit.unknown42, candidate.dt, audit.increment42)
        save('actual_issued_endpoint_before_gates')
        mapped = evidence['endpoint']['chart_mapping']
        assert np.all(np.asarray(mapped['position_error_m']) <= mapped['position_operation_bound_m'])
        assert np.all(np.asarray(mapped['velocity_error24_physical']) <= mapped['velocity_operation_bound24_physical'])
        assert max(mapped['independent_rodrigues_error']) <= mapped['independent_rodrigues_operation_bound']
        assert max(defects.values()) <= CRITERIA['normalized_defect_limit']
        assert evidence['endpoint']['scaled_free_balance'] <= CRITERIA['endpoint_balance_gate']
        assert now.elastic_consistency_witness/energy <= CRITERIA['elastic_witness_limit']
        assert canonical(state.histories) == canonical(c._reference_origins)
        assert state.epoch == 1 and state.time == CRITERIA['dt_seconds']
        evidence['status'] = 'PASS'; save('complete')
        record_property('finite_spin_acceleration_chart_one_step_summary', json.dumps(defects))
    except BaseException as error:
        evidence.update(status='NONPASS', failure_type=type(error).__name__, failure=str(error))
        save('failure'); raise


def finite_spin_trajectory_criteria(steps, total_time):
    """Parameter construction; selected pairs are16/.008 or short4/.001."""
    if type(steps) is not int or steps < 1 or type(total_time) is not float or total_time <= 0:
        raise ValueError('positive typed step count and total time required')
    selected = {name: value for name, value in CRITERIA.items()
        if name not in ('directional_intervals', 'directional_tangent_limit')}
    selected.update(maximum_accepted_steps=steps, total_time_seconds=total_time,
        dt_seconds=total_time/steps, minimum_final_cell_attitude_rad=(0. if (steps, total_time) == (4, .001) else .2),
        maximum_returned_stage_observations=128, owner_count=1, checkpoint_segments=0)
    if (steps, total_time) == (4, .001):
        selected.update(common_time_energy_ratio_limit=.4, common_time_energy_resolution_floor=1e-10)
    return selected


def cell_geodesic_angles(mechanical, reference):
    """Principal SO(3) geodesics relative to the two actual initial cell frames.

    A future refinement must compare issued states at equal physical times;
    this16-only fixture makes no temporal-accuracy comparison.
    """
    angles = []
    for cell in (0, 1):
        relative = mechanical.cell_rotations[0, cell]@reference.cell_rotations[0, cell].T
        sine = .5*np.linalg.norm([relative[2, 1]-relative[1, 2],
            relative[0, 2]-relative[2, 0], relative[1, 0]-relative[0, 1]])
        cosine = .5*(np.trace(relative)-1.)
        angles.append(float(np.arctan2(sine, cosine)))
    return angles


def test_free_finite_spin_trajectory(record_property):
    """One owner, explicitly selected pair, signed prefix on first failure."""
    started = perf_counter()
    inputs = json.loads(Path(os.environ['NATIVE_FINITE_SPIN_TRAJECTORY_INPUTS']).read_text(encoding='utf-8-sig'))
    output = Path(os.environ['NATIVE_FINITE_SPIN_TRAJECTORY_RAW_OUTPUT'])
    criteria = inputs['criteria']
    assert criteria in (finite_spin_trajectory_criteria(16, .008), finite_spin_trajectory_criteria(4, .001)) and not output.exists()
    evidence = dict(status='RUNNING', criteria=criteria, solver_committed_steps=0,
        gate_passing_steps=0, accepted_steps=0, unissued_stages=[], endpoints=[], pending_attempt=None,
        scope=('Short common-time half-step full-elastic control; no finite-angle coverage/temporal accuracy/C7 admission'
            if criteria['maximum_accepted_steps'] == 4 else
            '16-only full-elastic finite-spin development control; no temporal/spatial accuracy or C7 admission'))
    def save(stage):
        evidence.update(last_stage=stage, elapsed_seconds=perf_counter()-started)
        output.write_text(json.dumps(evidence, indent=2, allow_nan=False)+'\n')
        print(json.dumps(dict(stage=stage, elapsed_seconds=evidence['elapsed_seconds'])), flush=True)
        assert evidence['elapsed_seconds'] < criteria['internal_time_limit_seconds']
    def authentic(label, expected):
        row = inputs['historical'][label]
        data = Path(row['path']).read_bytes()
        assert row['sha256'] == expected == sha256(data).hexdigest()
        return json.loads(data) if label != 'fixture' else data
    try:
        saved = authentic('raw', RAW_SHA)['reference']
        old_inputs = authentic('inputs', OLD_INPUT_SHA)
        authentic('fixture', FIXTURE_SHA)
        chart_record = inputs['historical']['passed_acceleration_raw']
        chart_bytes = Path(chart_record['path']).read_bytes()
        assert sha256(chart_bytes).hexdigest() == chart_record['sha256']
        chart_pass = json.loads(chart_bytes)
        assert chart_pass['status'] == 'PASS' and chart_pass['accepted_steps'] == 1
        assert chart_pass['criteria'] == CRITERIA
        changed = inputs['historical_source_overrides']
        expected_changed = {'_ge_beam3_native_midpoint.py':
            '2c8e243e74f0b6eafff485b536f08242a51154d31dd8500afe689e10b2f265df',
            'ge_beam3_native_dynamics.py': 'aeba9bb1dbc7aa2daa0eb9df0f6a1ac49e43f476bafefeb76dbbc4239654326b',
            '_ge_beam3_native_dynamic_restart.py': '5bbbb4f7c99ef04483183f112c2c96dce19bc55f9f58cb9f3eecefe2065cf320'}
        stage_reuse_mode = inputs.get('verification_mode')
        if stage_reuse_mode == 'stage_reuse_v1':
            assert type(stage_reuse_mode) is str and criteria == finite_spin_trajectory_criteria(4, .001)
            expected_changed['_ge_beam3_native_midpoint.py'] = '2c623affb3ef2e3fef7170afab51502c3edd96d645a73e61a68dc94955698921'
        assert changed == expected_changed
        for path, expected in old_inputs['source_sha256'].items():
            expected = changed.get(Path(path).name, expected)
            assert sha256(Path(path).read_bytes()).hexdigest() == expected == inputs['source_sha256'][path]
        for path, expected in inputs['source_sha256'].items():
            assert sha256(Path(path).read_bytes()).hexdigest() == expected
        _, definition = make_analysis()  # Authentic builder, never old test bodies.
        owner = create_analysis(SELECTOR, (definition,), (), inertia_order=24,
            stage_residual_tolerance=criteria['explicit_stage_solve_tolerance'],
            stage_coordinates=criteria['stage_coordinates'],
            momentum_origin_high=tuple(criteria['origin_high_m']), momentum_origin_low=tuple(criteria['origin_low_m']))
        c = owner._context
        assert c.fixed == () and tuple(c.physical_free) == P and tuple(c.algebraic_free) == Z
        assert c.load_pattern is None and c.stage_residual_tolerance == 1e-12 and c.stage_coordinates == 'acceleration'
        assert c.element.operator.order == 4 and len(c.analysis._elements) == 1
        assert canonical(c._reference_mechanical) == canonical(saved['reference_mechanical'])
        assert canonical(c._reference_origins) == canonical(saved['virgin_histories'])
        assert np.array_equal(c.analysis._inertias[c.element.element_id], saved['section_inertia'])
        reference = c._reference_mechanical
        omega = np.asarray(criteria['spatial_spin_rad_per_s'])
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
            angular_momentum=mass*criteria['length_scale_m']*speed)
        assert all(np.isfinite(value) and value > 0. for value in scales.values())
        evidence.update(scales=scales, independent_mass_input_M42=saved['M42'],
            definition=json.loads(definition.raw), section_inertia=saved['section_inertia'],
            initial_velocity24=velocity.tolist(), provenance=workflow_provenance(owner))
        save('authenticated_fixture_scales_before_initialization')
        state = owner.initialize(physical_velocity15=velocity[list(P)])
        initial_issued_state = state  # Exact original object for NEW stale-predecessor control.
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
        historical_initial = chart_pass['initial']
        for key in ('mechanical', 'physical_velocity24', 'physical_acceleration24', 'histories'):
            assert canonical(evidence['initial']['state'][key]) == canonical(historical_initial['state'][key])
        for key in ('R42', 'I42', 'M42', 'balance42'):
            assert canonical(evidence['initial'][key]) == canonical(historical_initial[key])
        assert scales == chart_pass['scales'] and initial.total_energy == historical_initial['accounting']['total_energy']
        assert canonical(state.mechanical) == canonical(reference)
        assert np.array_equal(state.physical_velocity24, velocity)
        assert np.linalg.norm(inertia.mixed_mass-m0)/np.linalg.norm(m0) <= 1e-12
        assert abs(initial.kinetic_energy-energy)/energy <= 1e-12
        assert evidence['initial']['scaled_free_balance'] <= criteria['endpoint_balance_gate']
        assert np.count_nonzero(state.physical_velocity24[[i for i in range(24) if i not in P]]) == 0
        assert np.count_nonzero(state.physical_acceleration24[[i for i in range(24) if i not in P]]) == 0
        assert np.count_nonzero(inertia.mixed_inertia[list(Z)]) == 0
        previous_accounting = initial
        owner_context = c._identity
        for index in range(criteria['maximum_accepted_steps']):
            assert evidence['solver_committed_steps'] == evidence['gate_passing_steps'] == index
            assert c._identity == owner_context  # One persistent owner; no restore/deadline renewal.
            prior = state
            evidence['pending_attempt'] = dict(step=index+1, predecessor_sha256=sha(prior), predecessor_epoch=prior.epoch)
            original_stage = c._stage
            first_observation = len(evidence['unissued_stages'])
            def observe(predecessor, unknown, h, token=None):
                actual = original_stage(predecessor, unknown, h, token)
                # Canonical ORIGINAL StageEvaluation includes complete signed R/I/J/M.
                row = dict(step=index+1, unknown42=np.asarray(unknown).tolist(), stage=json.loads(canonical(actual)),
                    context_sha256=c._identity, predecessor_sha256=sha(predecessor), predecessor_epoch=predecessor.epoch,
                    original_returned_stage_preserved=True)
                evidence['unissued_stages'].append(row)
                save('original_returned_stage_'+str(len(evidence['unissued_stages'])))
                assert len(evidence['unissued_stages'])-first_observation <= criteria['maximum_returned_stage_observations']
                return actual
            c._stage = observe
            try:
                candidate = owner.trial(prior, dt=criteria['dt_seconds'])
            finally:
                c._stage = original_stage
                save('trial_return_or_failure')
            audit = owner.candidate_stage_audit(candidate)
            evidence['pending_attempt'].update(endpoint=json.loads(canonical(candidate.endpoint)),
                stage_coordinates=audit.stage_coordinates, unknown42=audit.unknown42.tolist(), increment42=audit.increment42.tolist(),
                stage=json.loads(canonical(audit.stage)), stage_sha256=audit.stage_sha256, candidate_sha256=audit.candidate_sha256,
                predecessor_sha256=audit.predecessor_sha256, predecessor_epoch=audit.predecessor_epoch,
                endpoint_epoch=audit.endpoint_epoch, audit_authentication_session=json.loads(audit.session_provenance),
                stage_residual_norm=candidate.stage_residual_norm, endpoint_algebraic_norm=candidate.endpoint_algebraic_norm,
                iterations=candidate.iterations, backtracks=candidate.backtracks)
            save('authenticated_candidate_before_commit')
            assert audit.stage_coordinates == 'acceleration'
            assert audit.predecessor_epoch == index and audit.endpoint_epoch == index+1
            assert np.array_equal(audit.stage.physical_acceleration24[list(P)], audit.unknown42[list(P)])
            assert candidate.stage_residual_norm <= criteria['explicit_stage_solve_tolerance']
            assert candidate.stage_residual_norm <= criteria['scientific_stage_gate']
            assert candidate.endpoint_algebraic_norm <= criteria['endpoint_balance_gate']
            state = owner.commit(candidate)
            evidence['solver_committed_steps'] = index+1
            evidence['pending_attempt']['solver_committed_state'] = json.loads(canonical(state))
            save('solver_commit_before_endpoint_accounting')
            now = owner.endpoint_accounting(state)
            with c._atomic_operation():
                c._guard(); work = c._loaded_work(state.mechanical, state.histories)
                inertia = c._inertia(state.mechanical, state.physical_velocity24, state.physical_acceleration24)
            step_p, step_h = momentum_delta(now, previous_accounting, 'linear'), momentum_delta(now, previous_accounting, 'angular')
            total_p, total_h = momentum_delta(now, initial, 'linear'), momentum_delta(now, initial, 'angular')
            step_defects = dict(P=float(np.linalg.norm(step_p)/scales['momentum']), H=float(np.linalg.norm(step_h)/scales['angular_momentum']),
                E=abs(now.total_energy-previous_accounting.total_energy)/energy)
            cumulative_defects = dict(P=float(np.linalg.norm(total_p)/scales['momentum']), H=float(np.linalg.norm(total_h)/scales['angular_momentum']),
                E=abs(now.total_energy-initial.total_energy)/energy)
            row = dict(step=index+1, state=json.loads(canonical(state)), accounting=accounting(now),
                candidate=evidence['pending_attempt'], R42=work.residual.tolist(), I42=inertia.mixed_inertia.tolist(),
                balance42=(work.residual+inertia.mixed_inertia).tolist(), J42=work.spatial_jacobian.tolist(), M42=inertia.mixed_mass.tolist(),
                scaled_free_balance=c._norm(work.residual+inertia.mixed_inertia,c.free),
                step_delta_P_n_s=step_p.tolist(), step_delta_H_nm_s=step_h.tolist(),
                cumulative_delta_P_n_s=total_p.tolist(), cumulative_delta_H_nm_s=total_h.tolist(),
                normalized_step_defects=step_defects, normalized_cumulative_defects=cumulative_defects,
                elastic_witness_normalized=now.elastic_consistency_witness/energy,
                cell_attitude_from_initial_rad=cell_geodesic_angles(state.mechanical, reference), gate_status='NOT_YET_ASSESSED')
            evidence['endpoints'].append(row)
            save('actual_committed_endpoint_before_development_gates')
            assert max(step_defects.values()) <= criteria['normalized_defect_limit']
            assert max(cumulative_defects.values()) <= criteria['normalized_defect_limit']
            assert row['scaled_free_balance'] <= criteria['endpoint_balance_gate']
            assert row['elastic_witness_normalized'] <= criteria['elastic_witness_limit']
            assert np.count_nonzero(inertia.mixed_inertia[list(Z)]) == 0
            assert np.count_nonzero(state.physical_velocity24[[i for i in range(24) if i not in P]]) == 0
            assert np.count_nonzero(state.physical_acceleration24[[i for i in range(24) if i not in P]]) == 0
            assert canonical(state.histories) == canonical(c._reference_origins)
            assert state.epoch == index+1 and state.time == prior.time+criteria['dt_seconds']
            if index+1 == criteria['maximum_accepted_steps']:
                assert min(row['cell_attitude_from_initial_rad']) >= criteria['minimum_final_cell_attitude_rad']
            row['gate_status'] = 'DEVELOPMENT_GATES_PASS'
            evidence['gate_passing_steps'] = evidence['accepted_steps'] = index+1
            evidence['pending_attempt'] = None
            previous_accounting = now
            save('step_development_gates_pass')
        if criteria['maximum_accepted_steps'] == 4:
            coarse = authentic('failed_coarse_trajectory_raw',
                '21971d5cda63617f1b9fbb55f42fab0495b82683d1ab819bd88f9a41269ea7a7')
            assert coarse['status'] == 'NONPASS' and coarse['solver_committed_steps'] == 3 and coarse['gate_passing_steps'] == 2
            assert coarse['criteria'] == finite_spin_trajectory_criteria(16, .008)
            for key in ('mechanical', 'physical_velocity24', 'physical_acceleration24', 'histories'):
                assert canonical(evidence['initial']['state'][key]) == canonical(coarse['initial']['state'][key])
            for key in ('R42', 'I42', 'M42', 'balance42'):
                assert canonical(evidence['initial'][key]) == canonical(coarse['initial'][key])
            assert scales == coarse['scales'] and initial.total_energy == coarse['initial']['accounting']['total_energy']
            comparison = common_time_half_step_comparison(evidence, coarse, criteria)
            evidence['common_time_comparison'] = comparison
            save('common_time_comparison_before_prospective_gate')
            assert comparison['resolved'], 'common-time energy ratio unresolved at the unchanged1e-10 normalized floor'
            assert comparison['energy_ratio'] <= criteria['common_time_energy_ratio_limit']
            evidence['accuracy_disposition'] = 'Common-time energy prefix discriminator only; no temporal-order/accuracy, finite-angle or engineering qualification'
        else:
            evidence['accuracy_disposition'] = '16-only trajectory; temporal/spatial accuracy unmeasured; no engineering qualification'
        evidence['status'] = 'PASS'
        save('complete')
        record_property('finite_spin_trajectory_summary', json.dumps(dict(solver_committed_steps=evidence['solver_committed_steps'],
            gate_passing_steps=evidence['gate_passing_steps'], final_cell_attitude_rad=evidence['endpoints'][-1]['cell_attitude_from_initial_rad'])))
        if stage_reuse_mode == 'stage_reuse_v1':
            return owner, initial_issued_state, state
    except BaseException as error:
        evidence.update(status='NONPASS', failure_type=type(error).__name__, failure=str(error))
        if evidence['solver_committed_steps'] > evidence['gate_passing_steps']:
            if evidence['endpoints'] and evidence['endpoints'][-1]['step'] == evidence['solver_committed_steps']:
                evidence['endpoints'][-1]['gate_status'] = 'DEVELOPMENT_NONPASS; solver commit is not engineering admission'
            else:
                evidence['pending_attempt']['post_commit_failure'] = 'No gate-passing result; committed state retained before accounting failure'
        save('failure'); raise


def stage_reuse_physical_payload(row, kind):
    """Exclude ONLY owner/session-linked IDs; finite JSON floats roundtrip exactly.

    Canonical equality keeps float values, signed zero, shapes, histories and all
    stage work/tangent/inertia arrays. No tolerance is used for physical parity.
    """
    result = dict(row)
    if kind == 'state':
        for key in ('context_sha256', 'predecessor_sha256'):
            result.pop(key)
    elif kind == 'accounting':
        result.pop('state_sha256')
    elif kind == 'initial':
        result.pop('current_state_sha256')
        result['state'] = stage_reuse_physical_payload(result['state'], 'state')
        result['accounting'] = stage_reuse_physical_payload(result['accounting'], 'accounting')
    elif kind == 'endpoint':
        result['state'] = stage_reuse_physical_payload(result['state'], 'state')
        result['accounting'] = stage_reuse_physical_payload(result['accounting'], 'accounting')
        candidate = dict(result['candidate'])
        for key in ('predecessor_sha256', 'candidate_sha256', 'audit_authentication_session'):
            candidate.pop(key)
        candidate['endpoint'] = stage_reuse_physical_payload(candidate['endpoint'], 'state')
        candidate['solver_committed_state'] = stage_reuse_physical_payload(candidate['solver_committed_state'], 'state')
        result['candidate'] = candidate
    else:
        raise ValueError('declared physical parity payload kind required')
    return result


def test_stage_reuse_bitwise_half_step(record_property):
    """NEW source-bound cache control: one existing4-step loop + rejected attempts."""
    from anysolver.control import CancellationToken, SolveCancelled
    started = perf_counter()
    inputs = json.loads(Path(os.environ['NATIVE_FINITE_SPIN_TRAJECTORY_INPUTS']).read_text(encoding='utf-8-sig'))
    output = Path(os.environ['NATIVE_FINITE_SPIN_TRAJECTORY_RAW_OUTPUT'])
    assert inputs.get('verification_mode') == 'stage_reuse_v1' and type(inputs['verification_mode']) is str
    assert inputs['criteria'] == finite_spin_trajectory_criteria(4, .001)
    baseline_ref = inputs['historical']['passed_half_raw']
    baseline_bytes = Path(baseline_ref['path']).read_bytes()
    assert baseline_ref['sha256'] == sha256(baseline_bytes).hexdigest() == '2e232aa32e5f535bc6b50f28f2f3ef13d4aa18fc1e3667fc26c160b69f893846'
    baseline = json.loads(baseline_bytes)
    assert baseline['status'] == 'PASS' and baseline['solver_committed_steps'] == baseline['gate_passing_steps'] == 4
    evidence = None
    def save(label):
        evidence.update(last_stage=label, elapsed_seconds=perf_counter()-started)
        output.write_text(json.dumps(evidence, indent=2, allow_nan=False)+'\n')
        print(json.dumps(dict(stage=label, elapsed_seconds=evidence['elapsed_seconds'])), flush=True)
        assert evidence['elapsed_seconds'] < 120.
    try:
        owner, genesis, current = test_free_finite_spin_trajectory(record_property)
        c = owner._context
        evidence = json.loads(output.read_text())
        evidence.update(physical_fixture_status=evidence['status'], status='RUNNING_STAGE_REUSE_CONTROLS',
            verification_mode='stage_reuse_v1', bitwise_parity=[], rejected_attempts=[])
        for kind, actual, expected in [('initial', evidence['initial'], baseline['initial']),
            *[('endpoint', a, b) for a, b in zip(evidence['endpoints'], baseline['endpoints'])]]:
            ap, bp = stage_reuse_physical_payload(actual, kind), stage_reuse_physical_payload(expected, kind)
            equal = canonical(ap) == canonical(bp)
            evidence['bitwise_parity'].append(dict(kind=kind, epoch=actual['state']['epoch'],
                actual_physical_sha256=sha(ap), saved_physical_sha256=sha(bp), bitwise_equal=equal))
            save('physical_bit_parity_before_gate')
            assert equal, 'initial/issued endpoint/accounting/audit physical payload differs from saved halfPASS'
        assert len(evidence['endpoints']) == len(baseline['endpoints']) == 4
        counts = [sum(row['step'] == step for row in evidence['unissued_stages']) for step in range(1, 5)]
        old_counts = [sum(row['step'] == step for row in baseline['unissued_stages']) for step in range(1, 5)]
        evidence['stage_call_counts'] = dict(physical_steps=counts, total_physical_steps=sum(counts),
            saved_physical_steps=old_counts, saved_total_physical_steps=sum(old_counts), rejected_controls=0)
        save('actual_stage_counts_before_gate')
        assert counts == [3]*4 and old_counts == [5]*4
        assert all(row['candidate']['iterations'] == 2 and row['candidate']['backtracks'] == 0 for row in evidence['endpoints'])
        before = canonical(current)
        before_issued = tuple(c._issued)
        before_candidates = tuple(c._candidates)
        original_stage = c._stage
        stale_calls = []
        def stale_observer(prior, unknown, h, token=None):
            actual = original_stage(prior, unknown, h, token)
            stale_calls.append(dict(unknown42=np.asarray(unknown).tolist(), stage=json.loads(canonical(actual))))
            return actual
        c._stage = stale_observer
        try:
            try:
                owner.trial(genesis, dt=.00025)
            except ValueError as error:
                stale_error = str(error)
            else:
                raise AssertionError('stale issued predecessor was admitted')
        finally:
            c._stage = original_stage
            evidence['rejected_attempts'].append(dict(kind='stale_issued_predecessor', stage_calls=stale_calls,
                predecessor_epoch=genesis.epoch, current_epoch=current.epoch))
            save('stale_control_return_or_failure')
        evidence['rejected_attempts'][-1]['error'] = stale_error
        assert 'current issued immutable midpoint predecessor' in stale_error and not stale_calls
        assert owner.current is current and canonical(current) == before
        assert tuple(c._issued) == before_issued and tuple(c._candidates) == before_candidates
        token = CancellationToken()
        cancelled_rows = []
        solve_after_cancel = []
        original_solve = np.linalg.solve
        def solve_observer(matrix, rhs, *args, **kwargs):
            if token.is_cancelled:
                solve_after_cancel.append(dict(matrix_shape=list(np.shape(matrix)), rhs_shape=list(np.shape(rhs))))
            return original_solve(matrix, rhs, *args, **kwargs)
        def cancel_observer(prior, unknown, h, supplied_token=None):
            actual = original_stage(prior, unknown, h, supplied_token)
            cancelled_rows.append(dict(unknown42=np.asarray(unknown).tolist(), stage=json.loads(canonical(actual)),
                context_sha256=c._identity, predecessor_sha256=sha(prior), predecessor_epoch=prior.epoch,
                scaled_free_norm=c._norm(actual.residual, c.free)))
            evidence['cancellation_returned_stages'] = cancelled_rows
            save('original_cancel_control_stage_before_request')
            if len(cancelled_rows) == 2:
                assert cancelled_rows[1]['scaled_free_norm'] < cancelled_rows[0]['scaled_free_norm']
                token.cancel('stage-reuse control: accepted line-search result awaits next iteration guard')
            return actual  # Exact original object; no solver/work substitution.
        c._stage, np.linalg.solve = cancel_observer, solve_observer
        try:
            try:
                owner.trial(current, dt=.00025, cancellation_token=token)
            except SolveCancelled as error:
                cancel_error = dict(type=type(error).__name__, message=str(error), stage=error.stage)
            else:
                raise AssertionError('accepted-line cancellation did not reject')
        finally:
            c._stage, np.linalg.solve = original_stage, original_solve
            evidence['rejected_attempts'].append(dict(kind='accepted_line_search_cancellation',
                stage_calls=cancelled_rows, solve_calls_after_cancel=solve_after_cancel))
            evidence['stage_call_counts']['rejected_controls'] = len(stale_calls)+len(cancelled_rows)
            save('cancel_control_return_or_failure')
        evidence['rejected_attempts'][-1]['error'] = cancel_error
        assert cancel_error['stage'] == 'midpoint.stage' and len(cancelled_rows) == 2 and not solve_after_cancel
        assert owner.current is current and canonical(current) == before
        assert tuple(c._issued) == before_issued and tuple(c._candidates) == before_candidates
        evidence['guard_controls'] = dict(stale_rejected_before_stage=True,
            accepted_line_cancelled_at_reuse_guard=True, no_solve_after_cancellation=True,
            current_and_issuance_unchanged=True, physical_steps=4, extra_commits=0)
        evidence['status'] = 'PASS'
        save('stage_reuse_complete')
        record_property('stage_reuse_summary',json.dumps(evidence['stage_call_counts']))
    except BaseException as error:
        if evidence is None and output.exists():
            evidence = json.loads(output.read_text())
        if evidence is not None:
            evidence.update(status='NONPASS', failure_type=type(error).__name__, failure=str(error),
                last_stage='stage_reuse_failure',elapsed_seconds=perf_counter()-started)
            output.write_text(json.dumps(evidence,indent=2,allow_nan=False)+'\n')
        raise


def test_acceleration_checkpoint_continuation(record_property):
    """Official committed checkpoint; direct/restored fifth step, three owners."""
    started = perf_counter()
    inputs = json.loads(Path(os.environ['NATIVE_FINITE_SPIN_TRAJECTORY_INPUTS']).read_text(encoding='utf-8-sig'))
    output = Path(os.environ['NATIVE_FINITE_SPIN_TRAJECTORY_RAW_OUTPUT'])
    assert inputs.get('verification_mode') == 'stage_reuse_v1'
    assert inputs.get('restart_verification_mode') == 'acceleration_restart_v1'
    assert inputs['criteria'] == finite_spin_trajectory_criteria(4, .001)
    historical = inputs['historical']['passed_stage_reuse_raw']
    history_bytes = Path(historical['path']).read_bytes()
    assert historical['sha256'] == sha256(history_bytes).hexdigest() == 'f42520630d4dc5bfcb69ed42cbb2be09d71f78daa9f918050e17413e026cc154'
    saved = json.loads(history_bytes)
    assert saved['status'] == 'PASS' and saved['solver_committed_steps'] == saved['gate_passing_steps'] == 4
    evidence = None
    def save(label):
        evidence.update(last_stage=label,elapsed_seconds=perf_counter()-started)
        output.write_text(json.dumps(evidence,indent=2,allow_nan=False)+'\n')
        print(json.dumps(dict(stage=label,elapsed_seconds=evidence['elapsed_seconds'])),flush=True)
        assert evidence['elapsed_seconds'] < 120.
    try:
        owner, genesis, current4 = test_free_finite_spin_trajectory(record_property)
        evidence = json.loads(output.read_text())
        evidence.update(prefix_fixture_status=evidence['status'],status='RUNNING_ACCELERATION_RESTART',
            restart_verification_mode='acceleration_restart_v1',declared_dynamic_owner_count=3,actual_dynamic_owner_count=1,
            total_solver_committed_steps=4,total_gate_passing_steps=4,continuation_branches=[],
            scope='Acceleration-chart restart/branch control only; no segmentation, finite-angle/C7/accuracy claim')
        criteria, scales = evidence['criteria'],evidence['scales']
        for actual,expected in zip(evidence['endpoints'],saved['endpoints']):
            assert canonical(stage_reuse_physical_payload(actual,'endpoint')) == canonical(stage_reuse_physical_payload(expected,'endpoint'))
        assert canonical(stage_reuse_physical_payload(evidence['initial'],'initial')) == canonical(stage_reuse_physical_payload(saved['initial'],'initial'))
        initial_accounting = evidence['initial']['accounting']
        def saved_initial_momentum_delta(now, name):
            # Inert recorded numbers only; no stale-state owner call or credentials.
            return np.array([float(F(float(h))+F(float(l))-F(float(h0))-F(float(l0)))
                for h,l,h0,l0 in zip(getattr(now,name+'_momentum'),getattr(now,name+'_momentum_low'),
                    initial_accounting[name+'_momentum'],initial_accounting[name+'_momentum_low'])])
        before_accounting = owner.endpoint_accounting(current4)
        raw = owner.create_checkpoint()
        digest = sha256(raw).hexdigest()
        checkpoint_path = Path(inputs['checkpoint_output_path'])
        assert not checkpoint_path.exists()
        with checkpoint_path.open('xb') as stream:
            stream.write(raw)
        checkpoint = json.loads(raw)
        evidence['checkpoint'] = dict(path=str(checkpoint_path),external_sha256=digest,
            byte_count=len(raw),complete_payload=checkpoint)
        save('official_step4_checkpoint_before_gates')
        assert canonical(checkpoint['state']) == canonical(current4)
        assert checkpoint['header']['settings']['stage_coordinates'] == 'acceleration'
        assert current4.epoch == 4 and current4.time == .001
        # Reuse exact declared model input, never synthesize stored q/history.
        _, definition = make_analysis()
        assert canonical(json.loads(definition.raw)) == canonical(evidence['definition'])
        matching = create_analysis(SELECTOR,(definition,),(),inertia_order=24,
            stage_residual_tolerance=1e-12,stage_coordinates='acceleration',
            momentum_origin_high=(0.,0.,0.),momentum_origin_low=(0.,0.,0.))
        evidence['actual_dynamic_owner_count'] += 1
        restored4 = matching.restore_checkpoint(raw,expected_sha256=digest)
        restored_accounting = matching.endpoint_accounting(restored4)
        repeated_raw = matching.create_checkpoint()
        evidence['restore'] = dict(state=json.loads(canonical(restored4)),accounting=accounting(restored_accounting),
            checks=matching.restore_checks,reexport_sha256=sha256(repeated_raw).hexdigest(),
            canonical_complete_state_equal=canonical(restored4)==canonical(current4),
            checkpoint_byte_equal=repeated_raw==raw)
        save('official_restore_before_gates')
        assert restored4 is not current4 and matching.current is restored4
        assert canonical(restored4) == canonical(current4)
        assert canonical(accounting(restored_accounting)) == canonical(accounting(before_accounting))
        assert repeated_raw == raw
        checks = matching.restore_checks
        assert checks['algebraic_residual_norm'] <= 1e-11 and checks['algebraic_correction_norm'] <= 1e-11
        assert checks['physical_balance_norm'] <= 1e-11
        for label,branch_owner,prior in (('direct',owner,current4),('restored',matching,restored4)):
            c = branch_owner._context
            branch = dict(label=label,solver_committed_steps=0,gate_passing_steps=0,unissued_stages=[])
            evidence['continuation_branches'].append(branch)
            original_stage = c._stage
            def observe(predecessor,unknown,h,token=None):
                actual = original_stage(predecessor,unknown,h,token)
                branch['unissued_stages'].append(dict(unknown42=np.asarray(unknown).tolist(),
                    stage=json.loads(canonical(actual)),context_sha256=c._identity,
                    predecessor_sha256=sha(predecessor),predecessor_epoch=predecessor.epoch))
                save('original_'+label+'_fifth_stage')
                assert len(branch['unissued_stages']) <= 128
                return actual
            c._stage = observe
            try:
                candidate = branch_owner.trial(prior,dt=.00025)
            finally:
                c._stage = original_stage
                save(label+'_trial_return_or_failure')
            audit = branch_owner.candidate_stage_audit(candidate)
            branch['candidate'] = dict(endpoint=json.loads(canonical(candidate.endpoint)),
                stage_coordinates=audit.stage_coordinates,unknown42=audit.unknown42.tolist(),increment42=audit.increment42.tolist(),
                stage=json.loads(canonical(audit.stage)),stage_sha256=audit.stage_sha256,candidate_sha256=audit.candidate_sha256,
                predecessor_sha256=audit.predecessor_sha256,predecessor_epoch=audit.predecessor_epoch,endpoint_epoch=audit.endpoint_epoch,
                audit_authentication_session=json.loads(audit.session_provenance),
                stage_residual_norm=candidate.stage_residual_norm,endpoint_algebraic_norm=candidate.endpoint_algebraic_norm,
                iterations=candidate.iterations,backtracks=candidate.backtracks)
            save(label+'_authenticated_candidate_before_commit')
            assert audit.stage_coordinates == 'acceleration'
            assert candidate.stage_residual_norm <= 1e-12 and candidate.stage_residual_norm <= 1e-11
            assert candidate.endpoint_algebraic_norm <= 1e-11
            state5 = branch_owner.commit(candidate)
            branch['solver_committed_steps'] = 1
            evidence['total_solver_committed_steps'] += 1
            branch['committed_state'] = json.loads(canonical(state5))
            save(label+'_committed_state_before_accounting')
            now = branch_owner.endpoint_accounting(state5)
            with c._atomic_operation():
                c._guard(); work = c._loaded_work(state5.mechanical,state5.histories)
                inertia = c._inertia(state5.mechanical,state5.physical_velocity24,state5.physical_acceleration24)
            step_p,step_h = momentum_delta(now,before_accounting,'linear'),momentum_delta(now,before_accounting,'angular')
            total_p,total_h = saved_initial_momentum_delta(now,'linear'),saved_initial_momentum_delta(now,'angular')
            step_defects = dict(P=float(np.linalg.norm(step_p)/scales['momentum']),H=float(np.linalg.norm(step_h)/scales['angular_momentum']),
                E=abs(now.total_energy-before_accounting.total_energy)/scales['energy'])
            cumulative_defects = dict(P=float(np.linalg.norm(total_p)/scales['momentum']),H=float(np.linalg.norm(total_h)/scales['angular_momentum']),
                E=abs(now.total_energy-initial_accounting['total_energy'])/scales['energy'])
            branch.update(state=json.loads(canonical(state5)),accounting=accounting(now),
                R42=work.residual.tolist(),I42=inertia.mixed_inertia.tolist(),balance42=(work.residual+inertia.mixed_inertia).tolist(),
                J42=work.spatial_jacobian.tolist(),M42=inertia.mixed_mass.tolist(),
                scaled_free_balance=c._norm(work.residual+inertia.mixed_inertia,c.free),
                normalized_step_defects=step_defects,normalized_cumulative_defects=cumulative_defects,
                step_delta_P_n_s=step_p.tolist(),step_delta_H_nm_s=step_h.tolist(),
                cumulative_delta_P_n_s=total_p.tolist(),cumulative_delta_H_nm_s=total_h.tolist(),
                elastic_witness_normalized=now.elastic_consistency_witness/scales['energy'],gate_status='NOT_YET_ASSESSED')
            save(label+'_actual_endpoint_before_development_gates')
            assert max(step_defects.values()) <= 1e-6 and max(cumulative_defects.values()) <= 1e-6
            assert branch['scaled_free_balance'] <= 1e-11 and branch['elastic_witness_normalized'] <= 1e-10
            assert np.count_nonzero(inertia.mixed_inertia[list(Z)]) == 0
            assert np.count_nonzero(state5.physical_velocity24[[i for i in range(24) if i not in P]]) == 0
            assert np.count_nonzero(state5.physical_acceleration24[[i for i in range(24) if i not in P]]) == 0
            assert canonical(state5.histories) == canonical(c._reference_origins)
            assert state5.epoch == 5 and state5.time == prior.time+.00025
            branch['gate_status'] = 'DEVELOPMENT_GATES_PASS'
            branch['gate_passing_steps'] = 1
            evidence['total_gate_passing_steps'] += 1
            save(label+'_fifth_step_development_gates_pass')
        direct,continued = evidence['continuation_branches']
        da,ca = dict(direct),dict(continued)
        for row in (da,ca):
            row.pop('label');row.pop('unissued_stages')
            candidate = dict(row['candidate']);candidate.pop('audit_authentication_session')
            row['candidate'] = candidate
        evidence['continuation_parity'] = dict(complete_state_work_accounting_candidate_equal=canonical(da)==canonical(ca),
            direct_sha256=sha(da),restored_sha256=sha(ca))
        save('fifth_step_complete_bit_parity_before_gate')
        assert canonical(da) == canonical(ca)
        # Default chart is observed, not overridden to fake a negative control.
        incompatible = create_analysis(SELECTOR,(definition,),(),inertia_order=24,
            stage_residual_tolerance=1e-12,momentum_origin_high=(0.,0.,0.),momentum_origin_low=(0.,0.,0.))
        evidence['actual_dynamic_owner_count'] += 1
        wrong = incompatible._context
        assert wrong.stage_coordinates == 'increment' and incompatible.current is None
        work_calls = []
        original_work = wrong._loaded_work
        def observe_work(*args,**kwargs):
            work_calls.append(True)
            return original_work(*args,**kwargs)
        wrong._loaded_work = observe_work
        try:
            try:
                incompatible.restore_checkpoint(raw,expected_sha256=digest)
            except ValueError as error:
                rejection = str(error)
            else:
                raise AssertionError('default increment chart restored acceleration checkpoint')
        finally:
            wrong._loaded_work = original_work
            evidence['incompatible_restore'] = dict(observed_chart=wrong.stage_coordinates,semantic_work_calls=len(work_calls),
                current_is_none=incompatible.current is None,issued_count=len(wrong._issued),candidate_count=len(wrong._candidates),
                initial_checks=incompatible.initial_checks,restore_checks=incompatible.restore_checks)
            save('incompatible_restore_return_or_failure')
        evidence['incompatible_restore']['error'] = rejection
        assert 'checkpoint header/body authority mismatch' in rejection and not work_calls
        assert incompatible.current is None and wrong._visible_current is None and wrong._current_bytes is None
        assert not wrong._issued and not wrong._candidates and incompatible.initial_checks is None and incompatible.restore_checks is None
        assert evidence['total_solver_committed_steps'] == evidence['total_gate_passing_steps'] == 6
        assert evidence['actual_dynamic_owner_count'] == evidence['declared_dynamic_owner_count'] == 3
        evidence['status'] = 'PASS'
        save('acceleration_restart_complete')
        record_property('acceleration_restart_summary',json.dumps(evidence['continuation_parity']))
    except BaseException as error:
        if evidence is None and output.exists():
            evidence = json.loads(output.read_text())
        if evidence is not None:
            evidence.update(status='NONPASS',failure_type=type(error).__name__,failure=str(error),
                last_stage='acceleration_restart_failure',elapsed_seconds=perf_counter()-started)
            output.write_text(json.dumps(evidence,indent=2,allow_nan=False)+'\n')
        raise


def common_time_half_step_comparison(fine, coarse, criteria):
    """Saved-array common-time comparison, never an old trajectory replay."""
    coarse_row = next(row for row in coarse['endpoints'] if row['step'] == 2)
    fine_row = fine['endpoints'][-1]
    assert coarse_row['gate_status'] == fine_row['gate_status'] == 'DEVELOPMENT_GATES_PASS'
    assert coarse_row['state']['time'] == fine_row['state']['time'] == criteria['total_time_seconds'] == .001
    energy_scale = fine['scales']['energy']
    assert energy_scale == coarse['scales']['energy'] > 0
    coarse_error = abs(coarse_row['accounting']['total_energy']-coarse['initial']['accounting']['total_energy'])/energy_scale
    fine_error = abs(fine_row['accounting']['total_energy']-fine['initial']['accounting']['total_energy'])/energy_scale
    assert coarse_error == coarse_row['normalized_cumulative_defects']['E']
    assert fine_error == fine_row['normalized_cumulative_defects']['E']
    resolved = bool(coarse_error > criteria['common_time_energy_resolution_floor']
        and fine_error > criteria['common_time_energy_resolution_floor'])
    ratio = float(fine_error/coarse_error) if resolved else None
    fm, cm = fine_row['state']['mechanical'], coarse_row['state']['mechanical']
    displacement = np.array([[float(F(float(fm['positions'][node][axis]))+F(float(fm['position_low'][node][axis]))
        -F(float(cm['positions'][node][axis]))-F(float(cm['position_low'][node][axis])))
        for axis in range(3)] for node in range(3)])
    velocity = np.asarray(fine_row['state']['physical_velocity24'])-np.asarray(coarse_row['state']['physical_velocity24'])
    m0 = np.asarray(fine['independent_mass_input_M42'])[:24, :24]
    velocity_square = float(velocity@m0@velocity)
    assert np.isfinite(velocity_square) and velocity_square >= 0.
    velocity_norm = float(np.sqrt(velocity_square/(2*energy_scale)))
    attitudes = []
    for cell in (0, 1):
        relative = np.asarray(fm['cell_rotations'])[0, cell]@np.asarray(cm['cell_rotations'])[0, cell].T
        sine = .5*np.linalg.norm([relative[2, 1]-relative[1, 2],
            relative[0, 2]-relative[2, 0], relative[1, 0]-relative[0, 1]])
        attitudes.append(float(np.arctan2(sine,.5*(np.trace(relative)-1.))))
    return dict(common_time_seconds=.001, coarse_step=2, fine_step=4,
        coarse_fixture_status='NONPASS retained; step3 energy failure is not regraded',
        coarse_prefix_gate_status=coarse_row['gate_status'],
        coarse_normalized_cumulative_energy_error=coarse_error, fine_normalized_cumulative_energy_error=fine_error,
        normalized_energy_resolution_floor=criteria['common_time_energy_resolution_floor'],
        resolved=resolved, energy_ratio=ratio, prospective_energy_ratio_limit=criteria['common_time_energy_ratio_limit'],
        disposition=('UNRESOLVED' if not resolved else 'DECREASE_SUPPORTS_TEMPORAL_TRUNCATION' if ratio <= .4 else 'HYPOTHESIS_NONPASS'),
        fine_minus_coarse_physical_positions_m=displacement.tolist(),
        normalized_position_difference=float(np.linalg.norm(displacement)/criteria['length_scale_m']),
        fine_minus_coarse_spatial_velocity24=velocity.tolist(), frozen_initial_mass_velocity_difference_norm=velocity_norm,
        cell_geodesic_difference_rad=attitudes,
        claim_boundary='One common-time energy prefix discriminator; no general order, accuracy, causal proof or finite-angle coverage')
