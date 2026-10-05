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
