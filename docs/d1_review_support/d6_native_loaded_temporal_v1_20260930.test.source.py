"""One bounded new midpoint/descriptor/rollback development discriminator."""
from dataclasses import replace
from contextlib import contextmanager
from hashlib import sha256
import inspect
import json
import os
from pathlib import Path
from time import perf_counter
from threading import Lock
from types import SimpleNamespace
import numpy as np
import pytest

from anysolver.ge_beam3_native import define_beam, create_analysis, SELECTOR, PROFILE_BYTES
from anysolver.boundary import BoundaryCondition
from anysolver._ge_beam3_generalized_ellipsoid_section import EllipsoidalGeneralizedSection
from anysolver._ge_beam3_native_midpoint import MidpointContext, MidpointState, MidpointCandidate
from anysolver._ge_beam3_retained_generalized_state import Mechanical
from anysolver._native_reference_modal import _owned
from anysolver._ge_beam3_centered_finite_inertia import ALGEBRAIC_DOFS
from anysolver._ge_beam3_p5.algebra import log_rotation
from anysolver._ge_beam3_p5_seeded.core import canonical
from anysolver.control import CancellationToken, SolveCancelled


def make_analysis():
    x = np.array((-1., 0., 1.))
    points = np.column_stack((x, .2*(1-x*x), np.zeros(3)))
    frames = []
    for value in x:
        tangent = np.array((1., -.4*value, 0.))
        tangent /= np.linalg.norm(tangent)
        second = np.array((0., 0., 1.))
        frames.append(np.column_stack((tangent, second, np.cross(tangent, second))))
    rho = 100.
    ea = 3*rho*rho
    d = np.diag(np.sqrt((ea, ea/3, ea/3.5, 2., 1., 1.5)))
    b = np.eye(6)
    b[0, 3], b[1, 5] = .02, .03
    f = b@d
    section = EllipsoidalGeneralizedSection(f.T@f, np.eye(6), 1e6, 1.)
    mass = 2.7
    center = np.array((.035, -.025, .012))
    a, bb, c = center
    skew = np.array(((0., -c, bb), (c, 0., -a), (-bb, a, 0.)))
    shift = -mass*(skew@skew)
    shift = np.triu(shift)+np.triu(shift, 1).T
    inertia = np.block([[mass*np.eye(3), -mass*skew],
        [mass*skew, np.diag((.12, .17, .19))+shift]])
    definition = define_beam(SELECTOR, 1, (1, 2, 3), points, np.array(frames),
        section, inertia, quadrature=4)
    boundary = BoundaryCondition('homogeneous-root', [1],
        {key: 0. for key in ('ux', 'uy', 'uz', 'rx', 'ry', 'rz')})
    return create_analysis(SELECTOR, (definition,), (boundary,)), definition


def physical_coordinates(context, state):
    initial = context._static.initial.mechanical
    q = np.zeros(42)
    for node in range(3):
        q[6*node:6*node+3] = (state.mechanical.positions[node]-initial.positions[node]
            +state.mechanical.position_low[node]-initial.position_low[node])
        q[6*node+3:6*node+6] = log_rotation(
            state.mechanical.nodal_frames[node]@initial.nodal_frames[node].T)
    for cell in (0, 1):
        q[18+3*cell:21+3*cell] = log_rotation(
            state.mechanical.cell_rotations[0, cell]@initial.cell_rotations[0, cell].T)
    q[24:] = state.mechanical.resultants[0]
    return q


def relative(a, b):
    return float(np.linalg.norm(a-b)/max(1e-30, np.linalg.norm(b)))


def test_single_centered_midpoint_descriptor_and_rollback(record_property):
    started = perf_counter()
    evidence_path = Path(os.environ['D6_MIDPOINT_OUTPUT'])
    assert not evidence_path.exists()
    evidence = dict(status='running', checks={}, steps=[], elapsed_seconds=0.)

    def save(stage, **fields):
        evidence.update(fields)
        evidence['last_stage'] = stage
        evidence['elapsed_seconds'] = perf_counter()-started
        evidence_path.write_text(json.dumps(evidence, indent=2)+'\n')
        print(json.dumps(dict(stage=stage, elapsed_seconds=evidence['elapsed_seconds'])), flush=True)

    try:
        module = Path(inspect.getsourcefile(MidpointContext)).resolve()
        assert module == Path(__file__).resolve().parents[1]/'src/anysolver/_ge_beam3_native_midpoint.py'
        evidence['source_identity'] = dict(module=str(module), sha256=sha256(module.read_bytes()).hexdigest(),
            test=str(Path(__file__).resolve()), test_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
            cache=os.environ['NUMBA_CACHE_DIR'])
        profile_before = PROFILE_BYTES
        analysis, definition = make_analysis()
        evidence['definition'] = json.loads(definition.raw)
        evidence['initial_velocity24'] = [0.]*18+[.01, -.007, .004, -.006, .009, .005]
        evidence['dt_seconds'] = 1e-4
        evidence['accepted_step_count'] = 8
        for kwargs in (dict(inertia_order=True), dict(max_iterations=13)):
            with pytest.raises(ValueError):
                MidpointContext(analysis, **kwargs)
        context = MidpointContext(analysis)
        velocity = np.array(evidence['initial_velocity24'])
        state = context.initialize(physical_velocity24=velocity)
        initial = state
        evidence['initial_checks'] = context.initial_checks
        assert context.initial_checks['algebraic_rank'] == 24
        assert context.initial_checks['physical_mass_min_eigenvalue'] > 0.
        save('initial_rank_and_mass_pass')

        r0, k0, _ = context._structural(state.mechanical, state.histories)
        m0 = context._inertia(state.mechanical, np.zeros(24), np.zeros(24)).mixed_mass
        p, z = list(context.physical_free), list(context.algebraic_free)
        evidence['reference_matrices'] = dict(K42=k0.tolist(), M42=m0.tolist(),
            free_physical=p, free_algebraic=z)
        assert np.array_equal(m0[list(ALGEBRAIC_DOFS), :], np.zeros((27, 42)))
        assert np.array_equal(m0[:, list(ALGEBRAIC_DOFS)], np.zeros((42, 27)))
        assert np.linalg.norm(r0) < 1e-11
        with pytest.raises(AttributeError):
            context.current = replace(state)
        with pytest.raises(ValueError):
            context.evaluate_stage(replace(state), np.zeros(42), dt=1e-4)
        for bad in (True, 0., -1., float('nan'), 1e-200):
            with pytest.raises(ValueError):
                context.evaluate_stage(state, np.zeros(42), dt=bad)
        with analysis._operation():
            with pytest.raises(ValueError, match='already in use'):
                context.evaluate_stage(state, np.zeros(42), dt=1e-4)
        bad_velocity = velocity.copy()
        bad_velocity[9] = .01
        with pytest.raises(ValueError, match='one finite typed'):
            context.initialize(physical_velocity24=bad_velocity)
        assert canonical(context.current) == canonical(state)

        # Exercise nonzero physical and algebraic charts without pretending that
        # inertial zero slots mean zero algebraic-frame coordinate derivative.
        u = np.zeros(42)
        u[p] = 1e-4*velocity[p]
        u[6:9] += np.array((.0002, -.0001, .00015))
        u[9:12] = (.002, -.0015, .0008)
        u[15:18] = (-.001, .0012, -.0009)
        u[18:24] += np.array((.002, -.001, .0013, -.0012, .0018, .0007))
        u[24:] = np.linspace(-.002, .003, 18)
        direction = np.zeros(42)
        direction[6:] = np.sin(np.arange(36)+.3)*.03
        direction[24:] *= 3.
        stage = context.evaluate_stage(state, u, dt=1e-4)
        analytical = stage.jacobian@direction
        derivative_errors = []
        for delta in (1e-5, 2e-6):
            plus = context.evaluate_stage(state, u+delta*direction, dt=1e-4)
            minus = context.evaluate_stage(state, u-delta*direction, dt=1e-4)
            finite = (plus.residual-minus.residual)/(2*delta)
            derivative_errors.append(dict(delta=delta,
                physical=relative(finite[p], analytical[p]),
                algebraic=relative(finite[z], analytical[z]),
                full=relative(finite, analytical)))
        evidence['checks']['full_stage_directional'] = derivative_errors
        assert max(item[key] for item in derivative_errors for key in ('physical', 'algebraic', 'full')) < 1e-5
        assert np.any(stage.mechanical.nodal_frames[1] != state.mechanical.nodal_frames[1])
        assert not np.any(stage.physical_velocity24[[3, 4, 5, 9, 10, 11, 15, 16, 17]])
        save('stage_directional_and_admission_pass')

        # Independent linear descriptor block, keeping all physical cell spins.
        kpp, kpz = k0[np.ix_(p, p)], k0[np.ix_(p, z)]
        kzp, kzz = k0[np.ix_(z, p)], k0[np.ix_(z, z)]
        mass = m0[np.ix_(p, p)]
        dt = 1e-4
        descriptor = np.block([[.5*kpp+2*mass/dt**2, kpz], [.5*kzp, kzz]])
        evidence['reference_matrices']['descriptor36'] = descriptor.tolist()
        linear_q, linear_v = np.zeros(12), velocity[p].copy()
        first_candidate = None
        for index in range(8):
            previous_bytes = canonical(state)
            candidate = context.trial(state, dt=dt)
            assert canonical(context.current) == previous_bytes
            if index == 0:
                # Valid discard invalidates the issued token; recompute this one
                # disposable trial solely to check publication rollback.
                first_candidate = candidate
                context.discard(candidate)
                with pytest.raises(ValueError):
                    context.commit(candidate)
                assert canonical(context.current) == previous_bytes
                candidate = context.trial(state, dt=dt)
                token = CancellationToken()
                token.cancel('focused before-commit rollback')
                with pytest.raises(SolveCancelled):
                    context.commit(candidate, cancellation_token=token)
                with pytest.raises(ValueError):
                    context.commit(replace(candidate, iterations=candidate.iterations+1))
                assert canonical(context.current) == previous_bytes
            rhs = np.r_[2*mass@(linear_q/dt**2+linear_v/dt)-.5*kpp@linear_q,
                        -.5*kzp@linear_q]
            linear_result = np.linalg.solve(descriptor, rhs)
            next_q = linear_result[:12]
            next_v = 2*(next_q-linear_q)/dt-linear_v
            linear_q, linear_v = next_q, next_v
            endpoint_z = np.linalg.solve(kzz, -kzp@linear_q)
            state = context.commit(candidate)
            with pytest.raises(ValueError):
                context.commit(candidate)
            actual_q = physical_coordinates(context, state)
            q_error = relative(actual_q[p], linear_q)
            v_error = relative(state.physical_velocity24[p], linear_v)
            z_error = relative(actual_q[z], endpoint_z)
            evidence['steps'].append(dict(epoch=state.epoch, time=state.time,
                iterations=candidate.iterations, backtracks=candidate.backtracks,
                stage_residual=candidate.stage_residual_norm,
                endpoint_algebraic_residual=candidate.endpoint_algebraic_norm,
                descriptor_q_relative=q_error, descriptor_v_relative=v_error,
                descriptor_z_relative=z_error, q42=actual_q.tolist(),
                velocity24=state.physical_velocity24.tolist(),
                acceleration24=state.physical_acceleration24.tolist(),
                reaction42=candidate.endpoint_reaction42.tolist(),
                kinetic_energy=candidate.stage.inertia.kinetic_energy,
                stage_algebraic_to_endpoint_change=float(np.linalg.norm(
                    state.mechanical.resultants-candidate.stage.mechanical.resultants))))
            assert max(q_error, v_error, z_error) < 1e-3
            assert state.epoch == index+1 and abs(state.time-(index+1)*dt) < 1e-18
            assert np.any(state.mechanical.cell_rotations != initial.mechanical.cell_rotations)
            assert canonical(state.histories) == canonical(initial.histories)
            assert not np.any(state.physical_velocity24[:6])
            for array in (state.physical_velocity24, state.physical_acceleration24,
                          state.mechanical.positions, state.mechanical.nodal_frames,
                          state.mechanical.cell_rotations, state.mechanical.resultants):
                with pytest.raises(ValueError):
                    array.setflags(write=True)
            save('accepted_step_'+str(index+1))

        # Endpoint algebraic spatial derivative: physical coordinates unchanged.
        r, j, _ = context._structural(state.mechanical, state.histories)
        dz = np.zeros(42)
        dz[z] = np.cos(np.arange(len(z))+.2)*.04
        alg_errors = []
        for delta in (1e-5, 2e-6):
            plus = context._static.advance(state.mechanical, delta*dz)
            minus = context._static.advance(state.mechanical, -delta*dz)
            rp, _, _ = context._structural(plus, state.histories)
            rm, _, _ = context._structural(minus, state.histories)
            alg_errors.append(dict(delta=delta, relative=relative((rp-rm)[z]/(2*delta), (j@dz)[z])))
            assert np.array_equal(plus.positions, state.mechanical.positions)
            assert np.array_equal(plus.cell_rotations, state.mechanical.cell_rotations)
        evidence['checks']['endpoint_algebraic_directional'] = alg_errors
        assert max(item['relative'] for item in alg_errors) < 1e-5

        # Independent differentiation of the physical momentum recovery, about
        # world origin. Include prescribed algebraic-frame reaction couples.
        speed, acceleration = state.physical_velocity24, state.physical_acceleration24
        full_step = np.zeros(42)
        full_step[p] = speed[p]
        instantaneous = context._inertia(state.mechanical, speed, acceleration)
        reaction = r+instantaneous.mixed_inertia
        force = sum((reaction[6*n:6*n+3] for n in range(3)), np.zeros(3))
        moment = sum((np.cross(state.mechanical.positions[n]+state.mechanical.position_low[n],
                              reaction[6*n:6*n+3])+reaction[6*n+3:6*n+6]
                      for n in range(3)), np.zeros(3))+reaction[18:21]+reaction[21:24]
        momentum_errors = []
        for delta in (1e-5, 2e-6):
            plus = context._static.advance(state.mechanical, delta*full_step)
            minus = context._static.advance(state.mechanical, -delta*full_step)
            ip = context._inertia(plus, speed+delta*acceleration, np.zeros(24))
            im = context._inertia(minus, speed-delta*acceleration, np.zeros(24))
            pdot = (ip.linear_momentum-im.linear_momentum)/(2*delta)
            hdot = (ip.angular_momentum-im.angular_momentum)/(2*delta)
            momentum_errors.append(dict(delta_seconds=delta,
                linear_relative=relative(pdot, force), angular_relative=relative(hdot, moment),
                linear_rate_n=pdot.tolist(), angular_rate_nm=hdot.tolist()))
        evidence['checks']['momentum_rates'] = momentum_errors
        evidence['reaction_wrench'] = dict(force_n=force.tolist(), moment_nm=moment.tolist())
        assert max(item[key] for item in momentum_errors for key in ('linear_relative', 'angular_relative')) < 1e-5
        assert PROFILE_BYTES == profile_before
        assert first_candidate is not None
        with pytest.raises(ValueError):
            context.commit(first_candidate)
        evidence['checks']['rollback_and_identity'] = dict(valid_discard=True, cancelled_commit=True,
            foreign_candidate=True, foreign_state=True, stale_candidate=True,
            operation_lock=True, immutable_arrays=True, public_profile_unchanged=True)
        record_property('initial_checks', json.dumps(context.initial_checks))
        record_property('final_descriptor_errors', json.dumps(evidence['steps'][-1]))
        save('completed', status='PASS')
    except BaseException as error:
        save('failed', status='NONPASS', failure=repr(error))
        raise


def test_transaction_exit_guard_rollback_only(record_property):
    """No mechanics replay: disposable complete issuance tokens and exit fault.

    The injected guard observes tentative private data but must never observe a
    changed public current, and every failure restores the exact prior registry.
    """
    mechanical = Mechanical(_owned(np.zeros((3, 3))), _owned(np.zeros((3, 3))),
        _owned(np.tile(np.eye(3), (3, 1, 1))), _owned(np.tile(np.eye(3), (1, 2, 1, 1))),
        _owned(np.zeros((1, 18))))
    prior = MidpointState(mechanical, (), (), _owned(np.zeros(24)), _owned(np.zeros(24)),
        0., 0, 'unit', 'unit')
    from anysolver._ge_beam3_p5_seeded.core import sha
    endpoint = replace(prior, epoch=1, time=1., predecessor_sha256=sha(prior))
    candidate = MidpointCandidate(endpoint, None, _owned(np.zeros(42)), 1., sha(prior),
        0, 0, 0., 0., _owned(np.zeros(42)))
    context = object.__new__(MidpointContext)
    context._identity = 'unit'
    context._current = context._visible_current = prior
    context._current_bytes = canonical(prior)
    context._issued = {id(prior): (prior, canonical(prior))}
    context._candidates = {id(candidate): (candidate, canonical(candidate))}
    context._initial_checks = b'{}'
    context._transaction_lock = Lock()
    context._guard = lambda *args: None
    original_issued = context._issued.copy()
    original_candidates = context._candidates.copy()
    fault = [True]
    observations = []

    @contextmanager
    def operation():
        yield
        observations.append(context.current is prior)
        if fault[0]:
            raise RuntimeError('injected operation exit guard')

    context.analysis = SimpleNamespace(_operation=operation)
    context.structural_owner = 'legacy_clamp'
    with pytest.raises(RuntimeError, match='exit guard'):
        context.commit(candidate)
    assert context.current is prior and context._current is prior
    assert context._current_bytes == canonical(prior)
    assert context._issued == original_issued and context._candidates == original_candidates
    with pytest.raises(RuntimeError, match='exit guard'):
        context.discard(candidate)
    assert context._candidates == original_candidates and context.current is prior
    assert observations == [True, True]
    fault[0] = False
    assert context.commit(candidate) is endpoint
    assert context.current is endpoint and context._current is endpoint

    # Initialization exit failure also leaves no visible state or issued token.
    context._current = context._visible_current = None
    context._current_bytes = None
    context._issued = {}
    context._candidates = {}
    context._initial_checks = None
    context._static = SimpleNamespace(initial=SimpleNamespace(mechanical=mechanical, histories=()),
        make=lambda data: mechanical)
    context._reference_mechanical = mechanical
    context._reference_origins = ()
    context.physical_free = (6, 7, 8, 12, 13, 14, 18, 19, 20, 21, 22, 23)
    context._solve_algebraic = lambda m, o, token: (m, None, None, 0., 'unit')
    context._endpoint_acceleration = lambda m, o, v: (_owned(np.zeros(24)), None, {'unit': True})
    fault[0] = True
    with pytest.raises(RuntimeError, match='exit guard'):
        context.initialize()
    assert context.current is None and context._current is None
    assert context._issued == {} and context._candidates == {} and context._initial_checks is None
    record_property('exit_guard_rollback', json.dumps(dict(commit=True, discard=True, initialization=True,
        visible_current_stayed_previous=True, no_mechanics_replay=True)))


def test_free_temporal_discrete_invariants_two_resolutions(record_property):
    """One predeclared 24-step contact-free temporal discriminator, no sweep.

    Accounting uses actual endpoint momenta and total consistent endpoint energy.
    The initial rigid velocity does not constrain the subsequent elastic motion.
    """
    from concurrent.futures import ThreadPoolExecutor
    from fractions import Fraction
    from anysolver._ge_beam3_dynamic_elastic_state import DynamicElasticContext
    from anysolver._ge_beam3_p5.compensated_coordinates import split_sum
    from anysolver._ge_beam3_p5_seeded.core import sha

    started = perf_counter()
    output = Path(os.environ['D6_FREE_TEMPORAL_OUTPUT'])
    assert not output.exists()
    evidence = dict(status='running', checks={}, cases={}, prospective=dict(
        time_seconds=.004, resolutions=[dict(dt_seconds=.001, steps=4),
            dict(dt_seconds=.0005, steps=8)], total_accepted_steps=24,
        translation_velocity_m_per_s=[.12, -.08, .05],
        initial_spin_rad_per_s=[.35, -.25, .20], length_scale_m=2.,
        momentum_origins_frozen=True, external_force_n=[0., 0., 0.],
        external_torque_nm=[0., 0., 0.], external_work_j=0.,
        residual_tolerance=1e-11, translation_invariant_tolerance=1e-10,
        translation_pose_tolerance=1e-12, spin_invariant_tolerance=1e-6,
        resolution_floor=1e-10, fine_coarse_ratio_limit=.6,
        elastic_witness_over_initial_energy_tolerance=1e-10))

    def save(stage, **fields):
        evidence.update(fields)
        evidence.update(last_stage=stage, elapsed_seconds=perf_counter()-started)
        output.write_text(json.dumps(evidence, indent=2)+'\n')
        print(json.dumps(dict(stage=stage, elapsed_seconds=evidence['elapsed_seconds'])), flush=True)

    def pairs(high, low):
        return [Fraction(float(h))+Fraction(float(l)) for h, l in zip(high, low)]

    def delta_momentum(now, before, kind):
        h = getattr(now, kind+'_momentum')
        l = getattr(now, kind+'_momentum_low')
        hb = getattr(before, kind+'_momentum')
        lb = getattr(before, kind+'_momentum_low')
        return np.array([float(a-b) for a, b in zip(pairs(h, l), pairs(hb, lb))])

    def accounting(data):
        return dict(time_seconds=data.time, epoch=data.epoch, state_sha256=data.state_sha256,
            linear_momentum_kg_m_per_s=data.linear_momentum.tolist(),
            linear_momentum_low_kg_m_per_s=data.linear_momentum_low.tolist(),
            angular_momentum_kg_m2_per_s=data.angular_momentum.tolist(),
            angular_momentum_low_kg_m2_per_s=data.angular_momentum_low.tolist(),
            kinetic_energy_j=data.kinetic_energy, consistent_elastic_energy_j=data.elastic_energy,
            total_energy_j=data.total_energy,
            elastic_consistency_witness_j=data.elastic_consistency_witness,
            resultant_compatibility18=data.resultant_compatibility18.tolist(),
            rank_mass_checks=json.loads(data.rank_mass_checks))

    def defect(now, before, scales):
        dp = delta_momentum(now, before, 'linear')
        dh = delta_momentum(now, before, 'angular')
        de = now.total_energy-before.total_energy
        return dict(linear_impulse_defect_n_s=dp.tolist(), angular_impulse_defect_nm_s=dh.tolist(),
            energy_defect_j=de, normalized_linear=float(np.linalg.norm(dp)/scales['momentum']),
            normalized_angular=float(np.linalg.norm(dh)/scales['angular_momentum']),
            normalized_energy=abs(de)/scales['energy'])

    def compare(coarse, fine):
        if coarse <= 1e-10:
            return dict(coarse=coarse, fine=fine, fine_coarse_ratio=None,
                disposition='resolution_limited' if fine <= 1e-10 else 'unresolved_NONPASS',
                passes=fine <= 1e-10)
        ratio = fine/coarse
        return dict(coarse=coarse, fine=fine, fine_coarse_ratio=ratio,
            disposition='decreasing' if ratio <= .6 else 'unresolved_NONPASS', passes=ratio <= .6)

    try:
        managed = Path(__file__).resolve().parents[1]
        modules = (MidpointContext, DynamicElasticContext)
        evidence['source_identity'] = dict(modules={str(Path(inspect.getsourcefile(m)).resolve()):
            sha256(Path(inspect.getsourcefile(m)).read_bytes()).hexdigest() for m in modules},
            test=str(Path(__file__).resolve()), test_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
            cache=os.environ['NUMBA_CACHE_DIR'], managed_worktree=str(managed))
        for module in modules:
            assert Path(inspect.getsourcefile(module)).resolve().parent == managed/'src/anysolver'
        profile_before = PROFILE_BYTES
        _, definition = make_analysis()
        evidence['definition'] = json.loads(definition.raw)

        # Scope controls are new interface checks. No time step or static genesis.
        analysis = create_analysis(SELECTOR, (definition,), ())
        structural = DynamicElasticContext(analysis)
        permanent = structural.reference_state()
        preserved = structural._issued.copy()
        standalone_work = structural.evaluate(permanent)
        with structural.session() as session:
            ephemeral = session.work(permanent.mechanical).state
            with ThreadPoolExecutor(max_workers=1) as pool:
                with pytest.raises(ValueError, match='same-thread'):
                    pool.submit(session.evaluate, ephemeral).result()
            with pytest.raises(ValueError, match='already in use'):
                with structural.session():
                    pass
            for _ in range(127):
                structural._issue(permanent.mechanical, permanent.origins)
            with pytest.raises(ValueError, match='capacity'):
                structural._issue(permanent.mechanical, permanent.origins)
            assert len(session._issued) == 128 and structural._issued == preserved
        assert not session._active and not session._issued and structural._active_session is None
        with pytest.raises(ValueError, match='same-thread'):
            session.evaluate(ephemeral)
        with pytest.raises(ValueError, match='issued immutable'):
            structural.evaluate(ephemeral)
        assert structural.reference_state() is permanent and structural._issued == preserved
        assert np.array_equal(structural.evaluate(permanent).residual, standalone_work.residual)
        evidence['checks']['scoped_work_issuance'] = dict(thread_bound=True, nested_rejected=True,
            scoped_capacity=128, over_capacity_rejected=True, ephemeral_invalid_after_exit=True,
            standalone_states_preserved=True, no_eviction=True)
        save('session_controls_complete')

        total_steps = 0
        for case in ('translation', 'anisotropic_spin'):
            case_record = evidence['cases'][case] = dict(resolutions={})
            for label, h, count in (('coarse', .001, 4), ('fine', .0005, 8)):
                analysis = create_analysis(SELECTOR, (definition,), ())
                origin = np.array((2.**40, -2.**40, 2.**41)) if case == 'translation' else np.zeros(3)
                context = MidpointContext(analysis, structural_owner='dynamic_elastic',
                    momentum_origin_high=origin)
                assert context._static is None and not context.fixed
                assert len(context.physical_free) == 15 and len(context.algebraic_free) == 27
                data = context._reference_mechanical.descriptor()
                velocity = np.zeros(24)
                if case == 'translation':
                    high, low = np.array(data['positions'], copy=True), np.array(data['position_low'], copy=True)
                    for node in range(3):
                        for axis in range(3):
                            high[node, axis], low[node, axis] = split_sum((float(origin[axis]),
                                float(high[node, axis]), float(low[node, axis])))
                    data.update(positions=high, position_low=low)
                    for node in range(3):
                        velocity[6*node:6*node+3] = (.12, -.08, .05)
                else:
                    omega = np.array((.35, -.25, .20))
                    for node in range(3):
                        velocity[6*node:6*node+3] = np.cross(omega, data['positions'][node])
                    velocity[18:21] = velocity[21:24] = omega
                initial_mechanical = Mechanical(*(_owned(data[k]) for k in Mechanical.__dataclass_fields__))
                state = context.initialize(initial_mechanical, velocity)
                initial = state
                initial_account = context.endpoint_accounting(state)
                mass_response = context._inertia(context._reference_mechanical, np.zeros(24), np.zeros(24))
                translation_map = np.zeros((42, 3))
                for node in range(3):
                    translation_map[6*node:6*node+3] = np.eye(3)
                mass = float(np.trace(translation_map.T@mass_response.mixed_mass@translation_map)/3)
                energy = initial_account.kinetic_energy
                assert mass > 0. and energy > 0.
                speed = float(np.sqrt(2*energy/mass))
                scales = dict(mass=mass, length=2., energy=energy, velocity=speed,
                    momentum=mass*speed, angular_momentum=mass*2.*speed,
                    angular_velocity=float(np.linalg.norm(velocity[18:21])) if case != 'translation' else speed/2.)
                run = case_record['resolutions'][label] = dict(dt_seconds=h, steps_requested=count,
                    momentum_origin_high_m=origin.tolist(), momentum_origin_low_m=[0., 0., 0.],
                    context_sha256=context._identity, initial_rank_mass=context.initial_checks,
                    scales=scales, initial=dict(accounting=accounting(initial_account),
                        positions_m=state.mechanical.positions.tolist(), position_low_m=state.mechanical.position_low.tolist(),
                        nodal_frames=state.mechanical.nodal_frames.tolist(),
                        cell_rotations=state.mechanical.cell_rotations.tolist(),
                        resultants=state.mechanical.resultants.tolist(), physical_velocity24=velocity.tolist()),
                    endpoints=[], accepted_steps=0)
                previous_account = initial_account
                save(case+'_'+label+'_initialized')
                for index in range(count):
                    prior = state
                    candidate = context.trial(prior, dt=h)
                    assert candidate.stage_residual_norm <= 1e-11 and candidate.endpoint_algebraic_norm <= 1e-11
                    assert np.count_nonzero(candidate.stage.inertia.mixed_inertia[list(ALGEBRAIC_DOFS)]) == 0
                    assert np.count_nonzero(candidate.stage.inertia.mixed_mass[list(ALGEBRAIC_DOFS)]) == 0
                    assert canonical(candidate.endpoint.histories) == canonical(initial.histories)
                    if case == 'translation' and label == 'coarse' and index == 0:
                        before_bytes = canonical(prior)
                        issuance = context._issued.copy()
                        candidates = context._candidates.copy()
                        original_operation = analysis._operation
                        observations = []

                        @contextmanager
                        def exit_failure():
                            with original_operation():
                                yield
                            # Real native guard has completed; scoped tokens
                            # have expired and visible midpoint remains prior.
                            observations.append(dict(visible_prior=context.current is prior,
                                scoped_closed=context._dynamic._active_session is None,
                                work_session_closed=context._work_session is None))
                            raise RuntimeError('injected post-native publication exit failure')

                        analysis._operation = exit_failure
                        try:
                            with pytest.raises(RuntimeError, match='publication exit'):
                                context.commit(candidate)
                        finally:
                            analysis._operation = original_operation
                        assert context.current is prior and context._current is prior
                        assert context._current_bytes == before_bytes
                        assert context._issued == issuance and context._candidates == candidates
                        assert all(all(row.values()) for row in observations)
                        cancellation = CancellationToken()
                        cancellation.cancel('new temporal publication rollback control')
                        with pytest.raises(SolveCancelled):
                            context.commit(candidate, cancellation_token=cancellation)
                        assert context.current is prior and context._candidates == candidates
                        old_owner = context.structural_owner
                        context.structural_owner = 'legacy_clamp'
                        try:
                            with pytest.raises(ValueError, match='route changed'):
                                context.commit(candidate)
                        finally:
                            context.structural_owner = old_owner
                        evidence['checks']['free_publication_rollback'] = dict(
                            real_native_exit_guard_completed=True, scoped_tokens_expired=True,
                            visible_prior_until_exit=True, issuance_and_candidate_restored=True,
                            cancelled_commit_restored=True, route_identity_bound=True,
                            same_ready_candidate_reused=True, observations=observations)
                    state = context.commit(candidate)
                    total_steps += 1
                    now = context.endpoint_accounting(state)
                    step_defect = defect(now, previous_account, scales)
                    cumulative = defect(now, initial_account, scales)
                    endpoint = dict(accounting=accounting(now), step_defect=step_defect,
                        cumulative_defect=cumulative, accepted_epoch=state.epoch,
                        positions_m=state.mechanical.positions.tolist(), position_low_m=state.mechanical.position_low.tolist(),
                        nodal_frames=state.mechanical.nodal_frames.tolist(), cell_rotations=state.mechanical.cell_rotations.tolist(),
                        resultants=state.mechanical.resultants.tolist(), physical_velocity24=state.physical_velocity24.tolist(),
                        physical_acceleration24=state.physical_acceleration24.tolist(),
                        stage_iterations=candidate.iterations, backtracks=candidate.backtracks,
                        stage_residual_norm=candidate.stage_residual_norm,
                        endpoint_algebraic_norm=candidate.endpoint_algebraic_norm,
                        endpoint_residual42_n_or_nm=candidate.endpoint_reaction42.tolist(),
                        stage_residual42_n_or_nm=candidate.stage.residual.tolist(),
                        history_sha256=sha(state.histories), elastic_witness_normalized=now.elastic_consistency_witness/energy)
                    if case == 'translation':
                        errors = []
                        for node in range(3):
                            for axis in range(3):
                                actual = Fraction(float(state.mechanical.positions[node, axis]))+Fraction(float(state.mechanical.position_low[node, axis]))
                                start = Fraction(float(initial.mechanical.positions[node, axis]))+Fraction(float(initial.mechanical.position_low[node, axis]))
                                expected = start+Fraction(float(velocity[6*node+axis]))*Fraction(float(h))*(index+1)
                                errors.append(float(actual-expected))
                        translation_error = float(np.linalg.norm(errors)/scales['length'])
                        velocity_error = float(np.linalg.norm(state.physical_velocity24-velocity)/speed)
                        cell_error = float(np.linalg.norm(state.mechanical.cell_rotations-initial.mechanical.cell_rotations))
                        frame_error = float(np.linalg.norm(state.mechanical.nodal_frames-initial.mechanical.nodal_frames))
                        endpoint['exact_translation_error'] = dict(position_over_length=translation_error,
                            velocity_over_speed=velocity_error, cell_frame=cell_error, nodal_frame=frame_error)
                    run['endpoints'].append(endpoint)
                    run['accepted_steps'] = index+1
                    evidence['accepted_steps_total'] = total_steps
                    save(case+'_'+label+'_step_'+str(index+1))
                    for field in ('normalized_linear', 'normalized_angular', 'normalized_energy'):
                        limit = 1e-10 if case == 'translation' else 1e-6
                        assert step_defect[field] <= limit, (case, label, index, field, step_defect[field])
                        assert cumulative[field] <= limit, (case, label, index, field, cumulative[field])
                    assert now.elastic_consistency_witness/energy <= 1e-10
                    if case == 'translation':
                        assert max(endpoint['exact_translation_error'].values()) <= 1e-12
                    previous_account = now
                assert state.epoch == count and abs(state.time-.004) <= 1e-17
                run['elapsed_seconds_at_end'] = perf_counter()-started
                assert context._dynamic._active_session is None and context._work_session is None
                assert len(context._dynamic._issued) == 1  # Its standalone reference, no evicted work.
            comparisons = case_record['resolution_comparison'] = {}
            coarse_end = case_record['resolutions']['coarse']['endpoints']
            fine_common = case_record['resolutions']['fine']['endpoints'][1::2]
            for field in ('normalized_linear', 'normalized_angular', 'normalized_energy'):
                coarse = max(row['cumulative_defect'][field] for row in coarse_end)
                fine = max(row['cumulative_defect'][field] for row in fine_common)
                comparisons[field] = compare(coarse, fine)
            save(case+'_resolution_comparison')
            assert all(row['passes'] for row in comparisons.values()), comparisons
        assert total_steps == 24 and PROFILE_BYTES == profile_before
        evidence['checks']['public_profile_unchanged'] = True
        # Read the frozen legacy payload and compare its field keys/default
        # statically; no repeated legacy timestep or reference-genesis campaign.
        import ast
        tree = ast.parse(Path(inspect.getsourcefile(MidpointContext)).read_text())
        owner_class = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'MidpointContext')
        constructor = next(n for n in owner_class.body if isinstance(n, ast.FunctionDef) and n.name == '__init__')
        kw_defaults = {arg.arg: default for arg, default in zip(constructor.args.kwonlyargs, constructor.args.kw_defaults)}
        assert ast.literal_eval(kw_defaults['structural_owner']) == 'legacy_clamp'
        identity = next(n for n in owner_class.body if isinstance(n, ast.FunctionDef) and n.name == '_identity_data')
        initial_payload = identity.body[0].value
        assert {item.arg for item in initial_payload.keywords} == {
            'implementation', 'analysis', 'inertia_order', 'iterations', 'backtracks', 'physical', 'algebraic', 'free'}
        assert identity.body[1].test.comparators[0].value == 'legacy_clamp'
        assert identity.body[1].body[0].targets[0].slice.value == 'static_context'
        evidence['checks']['legacy_default_identity_payload'] = dict(
            explicit_new_owner_only=True, default='legacy_clamp', default_payload_unchanged=True)
        record_property('discrete_invariant_summary', json.dumps({name: row['resolution_comparison']
            for name, row in evidence['cases'].items()}))
        save('completed', status='PASS', accepted=False, released=False)
    except BaseException as error:
        save('failed', status='NONPASS', failure=repr(error), accepted=False, released=False)
        raise


@pytest.mark.parametrize('owner', ('legacy_clamp', 'dynamic_elastic'))
def test_acceptance_scale_length_alias_mutation_rejected(owner, record_property):
    """Changed gate binding only: no time step or previous trajectory replay."""
    clamp, definition = make_analysis()
    analysis = clamp if owner == 'legacy_clamp' else create_analysis(SELECTOR, (definition,), ())
    context = MidpointContext(analysis, structural_owner=owner)
    context._guard()
    initial_identity = context._identity
    initial_payload = canonical(context._identity_data())
    original_scale, original_length = context.scale, context.length
    mechanical = context._reference_mechanical
    residual = np.arange(1., 43.)
    step = np.linspace(-.1, .1, 42)
    base_norm = context._norm(residual, list(context.free))
    base_correction = context._correction(mechanical, step)
    mutations = []
    for field, bad_value in (('scale', _owned(np.asarray(original_scale)*1e12)),
                             ('length', original_length*1e12)):
        setattr(context, field, bad_value)
        try:
            # Actual numerical gates read the selected-owner inputs even before
            # the public operation rejects the changed informational alias.
            assert context._norm(residual, list(context.free)) == base_norm
            assert context._correction(mechanical, step) == base_correction
            with pytest.raises(ValueError, match='acceptance scale/length changed'):
                context.initialize()
            assert context.current is None and context._current is None
            assert not context._issued and not context._candidates and context._initial_checks is None
            assert context._identity == initial_identity
            assert canonical(context._identity_data()) == initial_payload
            mutations.append(dict(field=field, rejected_before_initial_mechanics=True,
                actual_gate_unchanged=True, issuance_unchanged=True, identity_payload_unchanged=True))
        finally:
            setattr(context, field, original_scale if field == 'scale' else original_length)
        context._guard()
    if owner == 'legacy_clamp':
        from anysolver._ge_beam3_p5_seeded.core import sha
        old_payload = dict(implementation='DEVELOPMENT_C7_SINGLE_CENTERED_NATIVE_MIDPOINT_V1',
            analysis=analysis.identity, inertia_order=context.inertia_order,
            iterations=context.max_iterations, backtracks=context.max_backtracks,
            physical=context.physical_free, algebraic=context.algebraic_free, free=context.free,
            static_context=context._static.identity)
        assert sha(old_payload) == context._identity
    result = dict(owner=owner, mutation_controls=mutations, time_steps=0,
        numerical_norm=base_norm, numerical_correction=base_correction,
        default_identity_preserved=owner == 'legacy_clamp')
    record_property('acceptance_gate_binding', json.dumps(result))
    print(json.dumps(dict(stage='acceptance_gate_binding_complete', result=result)), flush=True)


def test_loaded_finite_common_stage_work_and_impulse(record_property):
    """New 12-step loaded finite-pose row, with a scalar station-load oracle."""
    from fractions import Fraction
    from anysolver._ge_beam3_native_generalized_loading import DistributedPattern
    from anysolver._ge_beam3_native_line_loading import LinePattern
    from anysolver._ge_beam3_p5.algebra import rotation
    from anysolver._ge_beam3_p5_seeded.core import sha

    started = perf_counter()
    output = Path(os.environ['D6_LOADED_TEMPORAL_OUTPUT'])
    assert not output.exists()
    force = np.array((.2, -.15, .1))
    density = np.array((.03, -.04, .02))
    spin = np.array((.35, -.25, .20))
    common_velocity = np.array((.12, -.08, .05))
    initial_rotation_vector = np.array((.2, -.1, .15))
    evidence = dict(status='running', checks={}, resolutions={}, prospective=dict(
        final_time_seconds=.004, dt_seconds=[.001, .0005], steps=[4, 8], total_steps=12,
        force_density_n_per_m=force.tolist(), couple_density_nm_per_m=density.tolist(),
        initial_rotation_vector_rad=initial_rotation_vector.tolist(), initial_spin_rad_per_s=spin.tolist(),
        common_velocity_m_per_s=common_velocity.tolist(), fixed_origin_m=[0., 0., 0.],
        force_rule_order=4, inertia_rule_order=24, normalized_defect_limit=1e-6,
        fine_coarse_limit=.6, floor=1e-10, load_map_work_limit=1e-12,
        smooth_stage_directional_limit=1e-5, perturbations=[1e-5, 2e-6]))

    def save(stage, **fields):
        evidence.update(fields, last_stage=stage, elapsed_seconds=perf_counter()-started)
        output.write_text(json.dumps(evidence, indent=2)+'\n')
        print(json.dumps(dict(stage=stage, elapsed_seconds=evidence['elapsed_seconds'])), flush=True)

    def fractions(high, low):
        return [Fraction(float(h))+Fraction(float(l)) for h, l in zip(high, low)]

    def momentum_delta(now, before, key):
        return np.array([float(a-b) for a, b in zip(
            fractions(getattr(now, key+'_momentum'), getattr(now, key+'_momentum_low')),
            fractions(getattr(before, key+'_momentum'), getattr(before, key+'_momentum_low')))])

    def positions(mechanical):
        return np.array([[float(Fraction(float(h))+Fraction(float(l))) for h, l in zip(row, tail)]
            for row, tail in zip(mechanical.positions, mechanical.position_low)])

    def position_difference(now, before):
        return np.array([[float(a-b) for a, b in zip(fractions(h, l), fractions(h0, l0))]
            for h, l, h0, l0 in zip(now.positions, now.position_low, before.positions, before.position_low)])

    def averaging_rotation(phi):
        # Independent analytic integral of Exp(t*phi), not production AD/chart.
        a, b, c = phi
        skew = np.array(((0., -c, b), (c, 0., -a), (-b, a, 0.)))
        theta2 = float(phi@phi)
        if theta2 < 1e-4:
            first = .5-theta2/24+theta2**2/720-theta2**3/40320
            second = 1/6-theta2/120+theta2**2/5040-theta2**3/362880
        else:
            theta = np.sqrt(theta2)
            first = (1-np.cos(theta))/theta2
            second = (theta-np.sin(theta))/(theta2*theta)
        return np.eye(3)+first*skew+second*(skew@skew)

    def scalar_load_oracle(points, cells, rows, reference_points):
        # Only declared shared reference geometry/station inputs are consumed.
        # No production contact/load kernel, line-work AD, or mass is called.
        load = np.zeros(42)
        jacobian = np.zeros((42, 42))
        couple = np.zeros(42)
        wrench_force = np.zeros(3)
        wrench_moment = np.zeros(3)
        potential = 0.
        for row in rows:
            cell, left, right = row['cell'], row['left'], row['right']
            t, measure, lift0 = row['t'], row['measure_m'], np.array(row['lift0_m'])
            lift = cells[cell]@lift0
            field = (1-t)*points[left]+t*points[right]+lift
            displacement = (1-t)*(points[left]-reference_points[left])+t*(points[right]-reference_points[right])
            displacement += lift-lift0
            load[6*left:6*left+3] += measure*(1-t)*force
            load[6*right:6*right+3] += measure*t*force
            first = 18+3*cell
            load[first:first+3] += measure*(np.cross(lift, force)+density)
            couple[first:first+3] += measure*density
            jacobian[first:first+3, first:first+3] += measure*(np.outer(lift, force)-(lift@force)*np.eye(3))
            wrench_force += measure*force
            wrench_moment += measure*(np.cross(field, force)+density)
            potential += measure*float(force@displacement)
        return dict(load=load, jacobian=jacobian, couple=couple, force=wrench_force,
            moment=wrench_moment, line_potential=float(potential))

    def path_oracle(prior, endpoint, candidate, rows, reference_points):
        # Issued candidate phi fixes the represented left-Exp branch.
        phi = candidate.unknown42[18:24].reshape(2, 3)
        before, after = prior.mechanical, endpoint.mechanical
        delta_positions = position_difference(after, before)
        average_points = positions(before)+.5*delta_positions
        average_cells = np.array([averaging_rotation(phi[c])@before.cell_rotations[0, c] for c in (0, 1)])
        averaged = scalar_load_oracle(average_points, average_cells, rows, reference_points)
        line_work = 0.
        couple_work = 0.
        for row in rows:
            cell, left, right = row['cell'], row['left'], row['right']
            t, weight = row['t'], row['measure_m']
            delta_lift = (after.cell_rotations[0, cell]-before.cell_rotations[0, cell])@np.array(row['lift0_m'])
            field_displacement = (1-t)*delta_positions[left]+t*delta_positions[right]+delta_lift
            line_work += weight*float(force@field_displacement)
            couple_work += weight*float(density@phi[cell])
        return dict(line_work=float(line_work), couple_work=float(couple_work),
            exact_work=float(line_work+couple_work),
            linear_impulse=candidate.dt*averaged['force'],
            angular_impulse=candidate.dt*averaged['moment'], phi=phi,
            average_cells=average_cells)

    def accounting(data):
        return dict(time_seconds=data.time, epoch=data.epoch, state_sha256=data.state_sha256,
            linear_momentum=data.linear_momentum.tolist(), linear_momentum_low=data.linear_momentum_low.tolist(),
            angular_momentum=data.angular_momentum.tolist(), angular_momentum_low=data.angular_momentum_low.tolist(),
            kinetic_energy_j=data.kinetic_energy, elastic_energy_j=data.elastic_energy,
            total_energy_j=data.total_energy, elastic_witness_j=data.elastic_consistency_witness,
            compatibility18=data.resultant_compatibility18.tolist(), rank_mass=json.loads(data.rank_mass_checks))

    def compare(coarse, fine):
        if coarse <= 1e-10:
            return dict(coarse=coarse, fine=fine, ratio=None,
                disposition='resolution_limited' if fine <= 1e-10 else 'unresolved_NONPASS', passes=fine <= 1e-10)
        ratio = fine/coarse
        return dict(coarse=coarse, fine=fine, ratio=ratio,
            disposition='decreasing' if ratio <= .6 else 'unresolved_NONPASS', passes=ratio <= .6)

    try:
        _, definition = make_analysis()
        pattern = DistributedPattern(LinePattern(((1, *map(float, force)),)), ((1, *map(float, density)),))
        evidence['definition'] = json.loads(definition.raw)
        evidence['constant_load_pattern'] = json.loads(canonical(pattern))
        profile_before = PROFILE_BYTES
        # New admission/binding controls only; no old mechanical test replay.
        clamped, _ = make_analysis()
        with pytest.raises(ValueError, match='requires dynamic elastic'):
            MidpointContext(clamped, load_pattern=pattern)
        bad = DistributedPattern(LinePattern(((99, *map(float, force)),)), ())
        with pytest.raises(ValueError, match='unknown element'):
            MidpointContext(create_analysis(SELECTOR, (definition,), ()), structural_owner='dynamic_elastic', load_pattern=bad)
        total_steps = 0
        for label, h, count in (('coarse', .001, 4), ('fine', .0005, 8)):
            analysis = create_analysis(SELECTOR, (definition,), ())
            context = MidpointContext(analysis, structural_owner='dynamic_elastic', load_pattern=pattern)
            assert context.load_pattern is not pattern
            assert context._static is None and not context.fixed
            data = context._reference_mechanical.descriptor()
            common_rotation = rotation(initial_rotation_vector)
            data['positions'] = data['positions']@common_rotation.T
            data['nodal_frames'] = np.array([common_rotation@frame for frame in data['nodal_frames']])
            data['cell_rotations'] = np.tile(common_rotation, (1, 2, 1, 1))
            initial_mechanical = Mechanical(*(_owned(data[k]) for k in Mechanical.__dataclass_fields__))
            velocity = np.zeros(24)
            for node in range(3):
                velocity[6*node:6*node+3] = common_velocity+np.cross(spin, data['positions'][node])
            velocity[18:21] = velocity[21:24] = spin
            state = context.initialize(initial_mechanical, velocity)
            initial = state
            initial_account = context.endpoint_accounting(state)
            reference = context.element.operator.reference
            reference_points = np.array(reference.coordinates)
            points, weights = np.polynomial.legendre.leggauss(4)
            rows = []
            for cell in (0, 1):
                for point, weight in zip(points, weights):
                    t = float((point+1)/2)
                    rows.append(dict(cell=cell, left=cell, right=cell+1, t=t,
                        measure_m=float(weight*reference.jacobian(cell-1+t)/2),
                        lift0_m=np.array(reference.half_cell_lift(cell, t)).tolist()))
            mass_response = context._inertia(context._reference_mechanical, np.zeros(24), np.zeros(24))
            translation_map = np.zeros((42, 3))
            for node in range(3):
                translation_map[6*node:6*node+3] = np.eye(3)
            mass = float(np.trace(translation_map.T@mass_response.mixed_mass@translation_map)/3)
            initial_energy = initial_account.kinetic_energy
            speed = float(np.sqrt(2*initial_energy/mass))
            scales = dict(mass=mass, length=2., energy=initial_energy, velocity=speed,
                momentum=mass*speed, angular_momentum=mass*2.*speed,
                angular_velocity=float(np.linalg.norm(spin)),
                force=sum(row['measure_m'] for row in rows)*float(np.linalg.norm(force)),
                couple=sum(row['measure_m'] for row in rows)*float(np.linalg.norm(density)))
            run = evidence['resolutions'][label] = dict(dt_seconds=h, requested_steps=count,
                context_sha256=context._identity, pattern_sha256=sha(context.load_pattern),
                scales=scales, independent_reference_stations=rows, initial=accounting(initial_account),
                initial_rank_mass=context.initial_checks, initial_velocity24=velocity.tolist(),
                initial_acceleration24=state.physical_acceleration24.tolist(),
                initial_mechanical=json.loads(canonical(state.mechanical)), endpoints=[])
            initial_load = context.physical_load_accounting(state.mechanical)
            initial_oracle = scalar_load_oracle(positions(state.mechanical), state.mechanical.cell_rotations[0], rows, reference_points)
            run['initial_load'] = dict(full42=initial_load.external_load42.tolist(),
                jacobian42=initial_load.external_spatial_jacobian42.tolist(), force_n=initial_load.force.tolist(),
                moment_nm=initial_load.moment_about_origin.tolist(), line_work_j=initial_load.line_force_work,
                mapped_cell_force_moment_nonsymmetry=float(np.linalg.norm(initial_load.external_spatial_jacobian42-initial_load.external_spatial_jacobian42.T)))
            initial_map_error = float(np.linalg.norm(initial_load.external_load42-initial_oracle['load'])/max(scales['force'], scales['couple']))
            run['initial_load']['independent_map_error'] = initial_map_error
            assert initial_map_error <= 1e-12
            previous_account = initial_account
            previous_load = initial_load
            cumulative_linear = np.zeros(3)
            cumulative_path_angular = np.zeros(3)
            cumulative_mid_angular = np.zeros(3)
            cumulative_exact_work = 0.
            cumulative_mid_work = 0.
            save(label+'_initialized')
            for index in range(count):
                prior = state
                candidate = context.trial(prior, dt=h)
                run['pending_candidate'] = dict(unknown42=candidate.unknown42.tolist(),
                    stage_mechanical=json.loads(canonical(candidate.stage.mechanical)),
                    endpoint_mechanical=json.loads(canonical(candidate.endpoint.mechanical)),
                    endpoint_velocity24=candidate.endpoint.physical_velocity24.tolist(),
                    endpoint_acceleration24=candidate.endpoint.physical_acceleration24.tolist(),
                    stage_residual42=candidate.stage.residual.tolist(),
                    stage_jacobian42=candidate.stage.jacobian.tolist(),
                    endpoint_residual42=candidate.endpoint_reaction42.tolist())
                save(label+'_candidate_'+str(index+1)+'_ready')
                stage_load = context.physical_load_accounting(candidate.stage.mechanical)
                oracle = scalar_load_oracle(positions(candidate.stage.mechanical), candidate.stage.mechanical.cell_rotations[0], rows, reference_points)
                errors = dict(force_map=float(np.linalg.norm(stage_load.external_load42-oracle['load'])/max(scales['force'], scales['couple'])),
                    load_spatial_jacobian=float(np.linalg.norm(stage_load.external_spatial_jacobian42-oracle['jacobian'])/scales['force']),
                    force_wrench=float(np.linalg.norm(stage_load.force-oracle['force'])/scales['force']),
                    moment_wrench=float(np.linalg.norm(stage_load.moment_about_origin-oracle['moment'])/(scales['force']*2+scales['couple'])),
                    scalar_line_potential=abs(stage_load.line_force_work-oracle['line_potential'])/initial_energy)
                assert max(errors.values()) <= 1e-12, errors
                assert stage_load.has_nonpotential_couple
                assert np.count_nonzero(stage_load.external_load42[list(ALGEBRAIC_DOFS)]) == 0
                assert np.count_nonzero(stage_load.external_spatial_jacobian42[list(ALGEBRAIC_DOFS)]) == 0
                assert np.count_nonzero(candidate.stage.inertia.mixed_inertia[list(ALGEBRAIC_DOFS)]) == 0
                assert canonical(candidate.endpoint.histories) == canonical(initial.histories)
                if label == 'coarse' and index == 0:
                    # Check the full loaded stage, including all free algebraics.
                    rng = np.random.default_rng(20260930)
                    direction = rng.normal(size=42)
                    direction[:24] *= .001
                    run['first_stage_derivative_inputs'] = dict(direction42=direction.tolist(),
                        unknown42=candidate.unknown42.tolist(), configuration_map=candidate.stage.configuration_map.tolist(),
                        structural_jacobian42=candidate.stage.structural_jacobian.tolist(),
                        inertia_mass42=candidate.stage.inertia.mixed_mass.tolist(),
                        inertia_velocity_jacobian42=candidate.stage.inertia.mixed_velocity_derivative.tolist(),
                        inertia_configuration_jacobian42=candidate.stage.inertia.mixed_configuration_derivative.tolist(),
                        complete_stage_jacobian42=candidate.stage.jacobian.tolist())
                    fd_checks = []
                    for epsilon in (1e-5, 2e-6):
                        plus = context.evaluate_stage(prior, candidate.unknown42+epsilon*direction, dt=h)
                        minus = context.evaluate_stage(prior, candidate.unknown42-epsilon*direction, dt=h)
                        difference = (plus.residual-minus.residual)/(2*epsilon)
                        expected = candidate.stage.jacobian@direction
                        error = dict(epsilon=epsilon,
                            observed_residual_derivative42=difference.tolist(), expected_residual_derivative42=expected.tolist(),
                            physical_relative=relative(difference[list(context.physical_free)], expected[list(context.physical_free)]),
                            algebraic_relative=relative(difference[list(context.algebraic_free)], expected[list(context.algebraic_free)]))
                        fd_checks.append(error)
                    evidence['checks']['full_loaded_stage_directional'] = fd_checks
                    save('loaded_stage_directional_complete')
                    assert all(max(row['physical_relative'], row['algebraic_relative']) <= 1e-5 for row in fd_checks), fd_checks
                    # Existing ready candidate supplies its one accepted step.
                    before = canonical(prior)
                    issuance, candidates = context._issued.copy(), context._candidates.copy()
                    valid_load = context.load_pattern
                    changed = DistributedPattern(LinePattern(((1, float(force[0])*2, float(force[1]), float(force[2])),)), valid_load.couples)
                    context.load_pattern = changed
                    try:
                        with pytest.raises(ValueError, match='constant physical load changed'):
                            context.commit(candidate)
                    finally:
                        context.load_pattern = valid_load
                    assert context.current is prior and context._current_bytes == before
                    assert context._issued == issuance and context._candidates == candidates
                    cancelled = CancellationToken()
                    cancelled.cancel('loaded publication control')
                    with pytest.raises(SolveCancelled):
                        context.commit(candidate, cancellation_token=cancelled)
                    assert context.current is prior and context._candidates == candidates
                    evidence['checks']['constant_pattern_and_cancelled_publication'] = dict(
                        exact_owned_pattern=True, foreign_element_rejected=True, legacy_loading_rejected=True,
                        changed_pattern_rejected=True, canonical_predecessor_and_issuance_preserved=True,
                        cancelled_commit=True, same_ready_candidate_reused=True)
                state = context.commit(candidate)
                total_steps += 1
                now = context.endpoint_accounting(state)
                endpoint_load = context.physical_load_accounting(state.mechanical)
                physical = path_oracle(prior, state, candidate, rows, reference_points)
                mid_angular = h*oracle['moment']
                mid_work = float(stage_load.external_load42@candidate.unknown42)
                cumulative_linear += physical['linear_impulse']
                cumulative_path_angular += physical['angular_impulse']
                cumulative_mid_angular += mid_angular
                cumulative_exact_work += physical['exact_work']
                cumulative_mid_work += mid_work
                dp, dh = momentum_delta(now, previous_account, 'linear'), momentum_delta(now, previous_account, 'angular')
                energy_change = now.total_energy-previous_account.total_energy
                cum_dp, cum_dh = momentum_delta(now, initial_account, 'linear'), momentum_delta(now, initial_account, 'angular')
                step_defect = dict(linear=float(np.linalg.norm(dp-physical['linear_impulse'])/scales['momentum']),
                    path_angular=float(np.linalg.norm(dh-physical['angular_impulse'])/scales['angular_momentum']),
                    midpoint_angular=float(np.linalg.norm(dh-mid_angular)/scales['angular_momentum']),
                    exact_work_energy=abs(energy_change-physical['exact_work'])/initial_energy,
                    midpoint_work_energy=abs(energy_change-mid_work)/initial_energy)
                cumulative_defect = dict(linear=float(np.linalg.norm(cum_dp-cumulative_linear)/scales['momentum']),
                    path_angular=float(np.linalg.norm(cum_dh-cumulative_path_angular)/scales['angular_momentum']),
                    midpoint_angular=float(np.linalg.norm(cum_dh-cumulative_mid_angular)/scales['angular_momentum']),
                    exact_work_energy=abs(now.total_energy-initial_account.total_energy-cumulative_exact_work)/initial_energy,
                    midpoint_work_energy=abs(now.total_energy-initial_account.total_energy-cumulative_mid_work)/initial_energy)
                exact_line_value_difference = endpoint_load.line_force_work-previous_load.line_force_work
                work_scale = h*(scales['force']*speed+scales['couple']*scales['angular_velocity'])
                scalar_work_error = abs(exact_line_value_difference-physical['line_work'])/work_scale
                endpoint = dict(accounting=accounting(now), actual_linear_impulse=dp.tolist(), actual_angular_impulse=dh.tolist(),
                    actual_energy_change_j=energy_change, path_linear_impulse=physical['linear_impulse'].tolist(),
                    path_angular_impulse=physical['angular_impulse'].tolist(), midpoint_angular_impulse=mid_angular.tolist(),
                    path_vs_midpoint_angular_impulse=(physical['angular_impulse']-mid_angular).tolist(),
                    exact_line_work_j=physical['line_work'], exact_couple_work_j=physical['couple_work'],
                    exact_physical_work_j=physical['exact_work'], midpoint_generalized_work_j=mid_work,
                    midpoint_vs_exact_work_j=mid_work-physical['exact_work'], scalar_work_error=scalar_work_error,
                    issued_cell_increment_phi_rad=physical['phi'].tolist(), path_average_cell_matrix=physical['average_cells'].tolist(),
                    normalized_step_defect=step_defect, normalized_cumulative_defect=cumulative_defect,
                    stage_load_map_errors=errors, stage_load42=stage_load.external_load42.tolist(),
                    endpoint_load42=endpoint_load.external_load42.tolist(), stage_force_n=stage_load.force.tolist(),
                    stage_torque_nm=stage_load.moment_about_origin.tolist(), endpoint_force_n=endpoint_load.force.tolist(),
                    endpoint_torque_nm=endpoint_load.moment_about_origin.tolist(),
                    positions_m=state.mechanical.positions.tolist(), position_low_m=state.mechanical.position_low.tolist(),
                    nodal_frames=state.mechanical.nodal_frames.tolist(), cell_rotations=state.mechanical.cell_rotations.tolist(),
                    resultants=state.mechanical.resultants.tolist(), physical_velocity24=state.physical_velocity24.tolist(),
                    physical_acceleration24=state.physical_acceleration24.tolist(), stage_residual42=candidate.stage.residual.tolist(),
                    endpoint_residual42=candidate.endpoint_reaction42.tolist(), stage_iterations=candidate.iterations,
                    stage_residual_norm=candidate.stage_residual_norm, endpoint_algebraic_norm=candidate.endpoint_algebraic_norm,
                    history_sha256=sha(state.histories), elastic_witness_normalized=now.elastic_consistency_witness/initial_energy)
                run['endpoints'].append(endpoint)
                run.pop('pending_candidate')
                evidence['accepted_steps_total'] = total_steps
                save(label+'_step_'+str(index+1))
                assert max(step_defect.values()) <= 1e-6 and max(cumulative_defect.values()) <= 1e-6
                assert scalar_work_error <= 1e-12, scalar_work_error
                assert now.elastic_consistency_witness/initial_energy <= 1e-10
                assert candidate.stage_residual_norm <= 1e-11 and candidate.endpoint_algebraic_norm <= 1e-11
                previous_account, previous_load = now, endpoint_load
            assert state.epoch == count and abs(state.time-.004) <= 1e-17
            assert len(context._dynamic._issued) == 1 and context._dynamic._active_session is None
        comparisons = evidence['resolution_comparison'] = {}
        coarse = evidence['resolutions']['coarse']['endpoints']
        fine = evidence['resolutions']['fine']['endpoints'][1::2]
        for field in coarse[0]['normalized_cumulative_defect']:
            comparisons[field] = compare(max(row['normalized_cumulative_defect'][field] for row in coarse),
                max(row['normalized_cumulative_defect'][field] for row in fine))
        save('loaded_resolution_comparison')
        assert all(row['passes'] for row in comparisons.values()), comparisons
        assert total_steps == 12 and PROFILE_BYTES == profile_before
        evidence['checks']['public_profile_unchanged'] = True
        record_property('loaded_common_stage_discrete_summary', json.dumps(comparisons))
        save('completed', status='PASS', accepted=False, released=False)
    except BaseException as error:
        save('failed', status='NONPASS', failure=repr(error), accepted=False, released=False)
        raise
