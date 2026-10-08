"""Exact straight, centered, longitudinal principal-spin development control.

Analytic attitude uses literal sine/cosine, not the production SO(3) update.
No Euler rotor is substituted for a deforming native beam. This exact invariant
fixture is a distinct, bounded verification row; general native C7 stays open.
"""
from dataclasses import asdict
from fractions import Fraction
from hashlib import sha256
import json
import os
from pathlib import Path
from time import perf_counter
import traceback

import numpy as np
from anysolver.ge_beam3_native import define_beam, SELECTOR as STATIC_SELECTOR
from anysolver.ge_beam3_native_dynamics import create_analysis, SELECTOR
from anysolver._ge_beam3_generalized_ellipsoid_section import EllipsoidalGeneralizedSection
from anysolver._ge_beam3_centered_finite_inertia import _CenteredFiniteKernel
from anysolver._ge_beam3_p5_seeded.core import canonical, sha

spec_path = Path(os.environ['NATIVE_PRINCIPAL_SPIN_INPUTS'])
spec = json.loads(spec_path.read_text())
for path, expected in spec['source_sha256'].items():
    assert sha256(Path(path).read_bytes()).hexdigest() == expected, path
for name, expected in spec['environment'].items():
    assert os.environ.get(name) == expected, name
criteria = spec['criteria']
assert criteria == dict(steps=8, dt_seconds=.001, spin_rad_per_s=50.,
    stage_solve_tolerance=1e-12, endpoint_gate=1e-11,
    trajectory_error_limit=1e-10, invariant_error_limit=1e-6,
    elastic_witness_limit=1e-10, elastic_witness_absolute_limit_j=1e-10, minimum_final_angle_rad=.2,
    length_m=2., mass_per_length_kg_m=2.7,
    section_rotary_inertia=[.12, .17, .19],
    reference_kinetic_energy_j=300., reference_angular_momentum_nms=12.)
raw_path = Path(spec['raw_output'])
assert not raw_path.exists()
started = perf_counter()
raw = dict(status='RUNNING', criteria=criteria, endpoints=[], original_stages=[],
    input_sha256=sha256(spec_path.read_bytes()).hexdigest(),
    scope='Exact principal-axis rigid-invariant native trajectory only; C7 open')

def save(stage):
    raw.update(last_stage=stage, elapsed_seconds=perf_counter()-started)
    raw_path.write_bytes(canonical(raw))
    print(json.dumps(dict(stage=stage, elapsed_seconds=raw['elapsed_seconds'])), flush=True)

def plain(value):
    if hasattr(value, 'rank_mass_checks'):
        value = asdict(value)
        value['rank_mass_checks'] = json.loads(value['rank_mass_checks'])
    elif hasattr(value, 'session_provenance'):
        value = asdict(value)
        value['session_provenance'] = json.loads(value['session_provenance'])
    return json.loads(canonical(value))

def exact_rotation(time):
    angle = criteria['spin_rad_per_s']*time
    c, s = np.cos(angle), np.sin(angle)
    return np.array(((1., 0., 0.), (0., c, -s), (0., s, c)))

def momentum(value, name):
    return np.array([float(Fraction(float(h))+Fraction(float(l)))
        for h, l in zip(getattr(value, name+'_momentum'), getattr(value, name+'_momentum_low'))])

try:
    points = np.array(((-1., 0., 0.), (0., 0., 0.), (1., 0., 0.)))
    frames = np.repeat(np.eye(3)[None], 3, axis=0)
    section = EllipsoidalGeneralizedSection(
        np.diag((30000., 10000., 8000., 2., 1., 1.5)), np.eye(6), 1e6, 1.)
    section_mass = np.diag((2.7, 2.7, 2.7, .12, .17, .19))
    definition = define_beam(STATIC_SELECTOR, 1, (1, 2, 3), points,
        frames, section, section_mass, quadrature=4)
    owner = create_analysis(SELECTOR, (definition,), (), inertia_order=24,
        stage_coordinates='acceleration', stage_residual_tolerance=1e-12)
    context = owner._context
    assert context.runtime_limit_seconds == 120. and context.load_pattern is None
    assert context.fixed == () and len(context.physical_free) == 15 and len(context.algebraic_free) == 27
    assert np.array_equal(context._reference_mechanical.positions, points)
    assert np.array_equal(context._reference_mechanical.nodal_frames, frames)
    assert np.array_equal(context._reference_mechanical.cell_rotations, np.repeat(np.eye(3)[None], 2, axis=0)[None])
    # Principal x axis in every physical section; no centroid or lift spin.
    kernel = _CenteredFiniteKernel(context.element.operator.reference, section_mass, 24)
    for cell, left, right, t, frame, offset, measure in kernel._stations:
        assert np.array_equal(frame, np.eye(3)) and offset[1] == offset[2] == 0.
    velocity15 = np.zeros(15)
    velocity15[9] = velocity15[12] = criteria['spin_rad_per_s']
    state = owner.initialize(physical_velocity15=velocity15)
    initial = owner.endpoint_accounting(state)
    assert owner.initial_checks['algebraic_rank'] == 27
    assert owner.initial_checks['physical_mass_min_eigenvalue'] > 0.
    raw.update(definition=json.loads(definition.raw), initial_state=plain(state),
        initial_accounting=plain(initial), initial_checks=owner.initial_checks,
        fixed_scales_before_trials=dict(length_m=2., angular_velocity_per_s=50.,
            acceleration_m_per_s2=5000., angular_acceleration_per_s2=2500.,
            energy_j=300., momentum_ns=540., angular_momentum_nms=12.))
    assert abs(initial.kinetic_energy-300.)/300. <= 1e-12
    assert np.linalg.norm(momentum(initial, 'linear'))/540. <= 1e-12
    assert np.linalg.norm(momentum(initial, 'angular')-np.array((12., 0., 0.)))/12. <= 1e-12
    reference = context._reference_mechanical
    def check_endpoint(state, accounting):
        expected = exact_rotation(state.time)
        mechanical = state.mechanical
        position = mechanical.positions + mechanical.position_low
        errors = dict(position=float(np.linalg.norm(position-points)/2.),
            nodal_frame=float(np.linalg.norm(mechanical.nodal_frames-expected[None])),
            cell_frame=float(np.linalg.norm(mechanical.cell_rotations[0]-expected[None])),
            velocity=float(np.linalg.norm(state.physical_velocity24[list(context.physical_free)]-velocity15)/50.),
            acceleration=float(np.linalg.norm(state.physical_acceleration24[list(context.physical_free)]
                /np.array([5000.]*9+[2500.]*6))))
        assert max(errors.values()) <= criteria['trajectory_error_limit'], errors
        resultant_scales = np.array([27000.]*6+[54000.]*12)
        assert np.linalg.norm(mechanical.resultants[0]/resultant_scales) <= criteria['trajectory_error_limit']
        assert canonical(state.histories) == canonical(context._reference_origins)
        assert np.all(state.physical_velocity24[[3,4,5,9,10,11,15,16,17]] == 0.)
        assert np.all(state.physical_acceleration24[[3,4,5,9,10,11,15,16,17]] == 0.)
        defects = dict(E=abs(accounting.total_energy-300.)/300.,
            P=float(np.linalg.norm(momentum(accounting, 'linear'))/540.),
            H=float(np.linalg.norm(momentum(accounting, 'angular')-np.array((12., 0., 0.)))/12.))
        assert max(defects.values()) <= criteria['invariant_error_limit'], defects
        assert accounting.elastic_consistency_witness/300. <= criteria['elastic_witness_limit']
        assert accounting.elastic_consistency_witness <= criteria['elastic_witness_absolute_limit_j']
        assert abs(accounting.elastic_energy)/300. <= criteria['trajectory_error_limit']
        return errors, defects
    def signed_endpoint(state):
        with context._atomic_operation():
            context._guard()
            work = context._loaded_work(state.mechanical, state.histories)
            inertia = context._inertia(state.mechanical, state.physical_velocity24,
                state.physical_acceleration24)
            endpoint_norm = context._norm(work.residual+inertia.mixed_inertia, context.free)
        return endpoint_norm, plain(work), plain(inertia)
    initial_norm, initial_work, initial_inertia = signed_endpoint(state)
    raw.update(initial_endpoint_norm=initial_norm, initial_signed_work=initial_work,
        initial_signed_inertia=initial_inertia)
    assert initial_norm <= criteria['endpoint_gate']
    initial_errors, initial_defects = check_endpoint(state, initial)
    raw.update(initial_errors=initial_errors, initial_defects=initial_defects)
    save('analytic_initial_state_consistent')
    previous = initial
    for step in range(1, criteria['steps']+1):
        prior = state
        original_stage = context._stage
        stage_start = len(raw['original_stages'])
        def observed_stage(accepted, unknown, dt, token=None):
            actual = original_stage(accepted, unknown, dt, token)
            raw['original_stages'].append(dict(step=step, predecessor_sha256=sha(accepted),
                unknown42=unknown.tolist(), stage=plain(actual)))
            return actual
        context._stage = observed_stage
        try:
            candidate = owner.trial(prior, dt=criteria['dt_seconds'])
        finally:
            context._stage = original_stage
        audit = owner.candidate_stage_audit(candidate)
        assert candidate.stage_residual_norm <= criteria['stage_solve_tolerance']
        assert candidate.endpoint_algebraic_norm <= criteria['endpoint_gate']
        state = owner.commit(candidate)
        now = owner.endpoint_accounting(state)
        endpoint_norm, work, inertia = signed_endpoint(state)
        row = dict(step=step, candidate=plain(candidate), audit=plain(audit),
            state=plain(state), accounting=plain(now), endpoint_norm=endpoint_norm,
            signed_endpoint_work=work, signed_endpoint_inertia=inertia,
            stages=len(raw['original_stages'])-stage_start)
        raw['endpoints'].append(row)
        save('committed_endpoint_before_gates')
        assert endpoint_norm <= criteria['endpoint_gate']
        row['trajectory_errors'], row['invariant_defects'] = check_endpoint(state, now)
        row['step_invariant_defects'] = dict(E=abs(now.total_energy-previous.total_energy)/300.,
            P=float(np.linalg.norm(momentum(now, 'linear')-momentum(previous, 'linear'))/540.),
            H=float(np.linalg.norm(momentum(now, 'angular')-momentum(previous, 'angular'))/12.))
        assert max(row['step_invariant_defects'].values()) <= criteria['invariant_error_limit']
        assert state.epoch == step and state.predecessor_sha256 == sha(prior)
        row['gates_passed'] = True
        previous = now
        save('endpoint_gates_passed')
    assert abs(state.time-criteria['steps']*criteria['dt_seconds']) <= 64*np.finfo(float).eps*.008
    assert criteria['spin_rad_per_s']*state.time >= criteria['minimum_final_angle_rad']
    for path, expected in spec['source_sha256'].items():
        assert sha256(Path(path).read_bytes()).hexdigest() == expected, path
    raw.update(status='PASS', verified_source_count=len(spec['source_sha256']),
        source_postmatch=True, solver_committed_steps=len(raw['endpoints']),
        gate_passing_steps=sum(row.get('gates_passed', False) for row in raw['endpoints']))
    save('complete')
except BaseException:
    raw.update(status='NONPASS', traceback=traceback.format_exc())
    save('failure')
    raise
