"""Supervised conservative BL5 spectral development checks, not qualification."""
from dataclasses import replace
import pickle
import numpy as np
import pytest
from scipy.linalg import eig
from anysolver import stiffened_shell as public
from anysolver import _stiffened_shell_ge_point_buckling as buckling
from anysolver._ge_beam3_pose_joint import _exp_terms
from anysolver._ge_beam3_retained_generalized_state import Mechanical
from anysolver._stiffened_shell_ge_finite_experimental import _position_pair
from anysolver.control import CancellationToken
from test_stiffened_shell_bl5_finite import _model
from test_stiffened_shell_ge_point_buckling import dense_full_hessian, _MockInverse


def definition(basis):
    return replace(_model(3, basis), q4_pullback_policy=public.Q4_ALGORITHMIC_PULLBACK_V1)


@pytest.fixture(scope='module', params=('p0', 'continuous_p1_coarse'))
def accepted_owner(request):
    owner = public.create_analysis(definition=definition(request.param))
    result = owner.solve((public.NodalAction('beam', 105, (-1000., 0., 100., 0., 0., 0.)),),
                         (.5, 1.), max_iterations=24, max_backtracks=12)
    assert result.status == 'completed'
    yield owner
    owner.close()


def line_oracle(owner, packet):
    """Direct additive-shell Jet2 law, independent of spatial Hessian pullback."""
    h, km = dense_full_hessian(owner, packet)
    snap = packet.snapshot; driver = owner._finite_driver
    assert snap.shell_anchors is None or np.max(abs(snap.shell_anchors-np.eye(3))) < 1e-14
    u = snap.q[owner._shell_count:owner._shell_count+driver._beam_nodal].reshape(-1, 6)[:, :3]
    positions, low = _position_pair(driver._reference_positions, u)
    mechanical = Mechanical(positions, low, snap.frames, snap.cells, snap.resultants)
    for sample, (rows, basis) in zip(owner._line_samples, owner._line_terms, strict=True):
        op, slots, weight, _, _ = sample
        rows = rows+6*len(owner._connections)
        # evaluate(), unlike evaluate_spatial(), differentiates Exp(theta+dtheta)
        # directly with Jet2. Beam-cell rotation remains zero-left-Exp.
        local = op.evaluate(snap.q[slots[:12]].reshape(2, 6), mechanical, basis@snap.multipliers[rows])
        cross = local.gap_jacobian.T@basis
        material = np.block([[np.zeros((21, 21)), cross], [cross.T, np.zeros((len(rows), len(rows)))]])
        total = material.copy(); total[:21, :21] = local.hessian
        extended = np.r_[slots, packet.primal_count+rows]
        km[np.ix_(extended, extended)] += weight*material
        h[np.ix_(extended, extended)] += weight*total
    return h, km


def test_nonmatching_full_mixed_oracle_and_line_maps(accepted_owner):
    owner = accepted_owner; before = owner.checkpoint()
    packet, guard = buckling.capture(owner, owner._generation, lines=True)
    assert len(owner._shell_parts) == 3 and len(owner._beam_parts) == 2
    assert np.linalg.norm(packet.snapshot.multipliers) > 0
    assert np.linalg.norm(packet.snapshot.q[:owner._shell_count].reshape(-1, 6)[:, 3:]) > 0
    h, km = line_oracle(owner, packet)
    for actual, expected in ((packet.hessian, h), (packet.material, km), (packet.geometric, h-km)):
        np.testing.assert_allclose(actual.toarray(), expected, rtol=1e-11, atol=2e-6)
    free = list(packet.free)
    np.testing.assert_allclose((packet.material+packet.geometric)[free, :][:, free].toarray(),
                               h[np.ix_(free, free)], rtol=1e-11, atol=2e-6)
    assert packet.primal_count == owner._shell_count+6*len(owner._beam_ids)+24*len(owner._beam_parts)
    for station in packet.line_stations:
        with pytest.raises(ValueError): station.basis.setflags(write=True)
    guard(); assert owner.checkpoint() == before


def test_actual_update_covector_plateau(accepted_owner):
    owner = accepted_owner; driver = owner._finite_driver; before = owner.checkpoint()
    packet, _ = buckling.capture(owner, owner._generation, lines=True)
    state = driver._state; n = packet.primal_count
    direction = np.sin(np.arange(packet.material.shape[0])+1.)
    direction[:n] *= owner._coordinate_scale; direction[n:] *= owner._constraint_scale
    direction[owner._fixed] = 0.
    caches = {name: getattr(driver, name) for name in ('_line_trial_recovery', '_point_trial_recovery',
              '_distributing_trial_recovery', '_generalized_trial_recovery')}
    def covector(amount):
        trial = driver._advance(state, direction, amount)
        residual = driver._assemble(trial, driver._load_factor, pickle.loads(packet.snapshot.shell_origins),
            pickle.loads(packet.snapshot.beam_origins), applied_load=packet.snapshot.applied_dead_load)[0]
        value = residual.copy()
        for node, row in enumerate(trial.q[:owner._shell_count].reshape(-1, 6)):
            s = slice(6*node+3, 6*node+6); value[s] = _exp_terms(row[3:])[1].T@residual[s]
        retained = owner._shell_count+6*len(owner._beam_ids)
        starts = [owner._shell_count+6*i+3 for i in range(len(owner._beam_ids))]
        starts += [retained+24*i+3*j for i in range(len(owner._beam_parts)) for j in range(2)]
        for start in starts:
            s = slice(start, start+3); value[s] = _exp_terms(amount*direction[s])[1].T@residual[s]
        return value
    steps = (3e-6, 1e-6, 3e-7)
    try:
        differences = [(covector(h)-covector(-h))/(2*h) for h in steps]
    finally:
        for name, value in caches.items(): setattr(driver, name, value)
    exact = packet.hessian@direction; scale = np.r_[owner._coordinate_scale, owner._constraint_scale]
    errors = [np.max(abs((value-exact)*scale))/max(1., np.max(abs(exact*scale))) for value in differences]
    assert max(errors) <= 1e-6, errors
    assert owner.checkpoint() == before


def test_dense_descriptor_restart_and_recovery(accepted_owner):
    owner = accepted_owner; before = owner.checkpoint()
    packet, _ = buckling.capture(owner, owner._generation, lines=True)
    h, km = line_oracle(owner, packet); free = list(packet.free)
    _, _, scale = buckling._scaled_pencil(owner, packet); congruence = np.outer(scale, scale)
    values = eig(km[np.ix_(free, free)]*congruence, -(h-km)[np.ix_(free, free)]*congruence, right=False)
    finite = [v.real for v in values if np.isfinite(v) and v.real > 0 and abs(v.imag) <= 1e-8*abs(v.real)]
    result = owner.buckling(public.GELineBucklingRequest(owner._generation, count=2))
    assert type(result) is public.GELineBucklingResult and result.status == 'completed', result.failure_reason
    assert result.policy == buckling.LINE_POLICY and finite
    for i, factor in enumerate(result.prestress_multipliers):
        assert min(abs(factor-v)/max(1., abs(v)) for v in finite) < 1e-7
        for j, station in enumerate(packet.line_stations):
            np.testing.assert_array_equal(result.line_station_density_modes[i][j],
                station.basis@result.multiplier_modes[i][list(station.rows)])
            np.testing.assert_array_equal(result.line_station_gap_modes[i][j],
                station.gap_jacobian@result.full_coordinates[i][list(station.slots)])
    assert max(result.equation_residuals) <= 1e-8 and max(result.constraint_residuals) <= 1e-8
    other = public.create_analysis(definition=owner._definition)
    try:
        other.restore(before)
        replay, _ = buckling.capture(other, other._generation, lines=True)
        np.testing.assert_array_equal(replay.hessian.toarray(), packet.hessian.toarray())
        assert other.checkpoint() == before
    finally: other.close()
    assert owner.checkpoint() == before


def test_line_admission_mutation_cancellation_and_backend(accepted_owner, monkeypatch):
    owner = accepted_owner; before = owner.checkpoint()
    assert owner.line_buckling_capabilities['definition_admitted']
    assert not owner.point_buckling_capabilities['definition_admitted']
    with pytest.raises(ValueError): owner.buckling(public.GEPointBucklingRequest(owner._generation))
    with pytest.raises(ValueError, match='matching generation'):
        buckling.capture(owner, owner._generation+1, lines=True)
    _, guard = buckling.capture(owner, owner._generation, lines=True)
    saved = owner._line_terms
    rows, basis = saved[0]; changed = basis.copy(); changed[0, 0] += .01
    owner._line_terms = ((rows, changed),)+saved[1:]
    try:
        with pytest.raises(ValueError, match='model/support provenance'): guard()
    finally: owner._line_terms = saved
    guard()
    handle = _MockInverse(); token = CancellationToken()
    monkeypatch.setattr(buckling, 'factorize_cached', lambda *args: handle)
    def cancelled(operator, **kwargs):
        operator.matvec(np.ones(operator.shape[0])); token.cancel('line iteration')
        operator.matvec(np.ones(operator.shape[0]))
    monkeypatch.setattr(buckling, 'eigs', cancelled)
    result = owner.buckling(public.GELineBucklingRequest(owner._generation), cancellation_token=token)
    assert result.status == 'cancelled' and not result.full_coordinates
    def broken(rhs): raise RuntimeError('Sparse solve produced NaN/Inf values')
    handle.solve = broken
    monkeypatch.setattr(buckling, 'eigs', lambda operator, **kwargs: operator.matvec(np.ones(operator.shape[0])))
    result = owner.buckling(public.GELineBucklingRequest(owner._generation))
    assert result.status == 'failed' and not result.full_coordinates
    assert owner.checkpoint() == before


@pytest.mark.parametrize('change', ('policy', 'rotation', 'couple'))
def test_negative_line_admission(accepted_owner, change):
    owner = accepted_owner; before = owner.checkpoint()
    if change == 'policy':
        saved = owner._definition
        owner._definition = replace(saved, q4_pullback_policy='historical_corotational')
        restore = lambda: setattr(owner, '_definition', saved)
    elif change == 'rotation':
        saved = owner._fixed; owner._fixed = np.array([i for i in saved if i != 5])
        restore = lambda: setattr(owner, '_fixed', saved)
    else:
        driver = owner._finite_driver; saved = driver._applied_load
        applied = saved if saved is not None else driver._load_factor*driver._pattern
        driver._applied_load = applied.copy(); driver._applied_load[3] = 1.
        restore = lambda: setattr(driver, '_applied_load', saved)
    try:
        with pytest.raises(ValueError, match='nodal dead translations' if change == 'couple' else None):
            buckling.capture(owner, owner._generation, lines=True)
    finally: restore()
    assert owner.checkpoint() == before


@pytest.mark.parametrize('change', ('operator', 'inventory', 'basis'))
def test_compiled_line_map_admission_precedes_factorization(accepted_owner, monkeypatch, change):
    owner = accepted_owner; samples = owner._line_samples; terms = owner._line_terms
    monkeypatch.setattr(buckling, 'factorize_cached', lambda *args: pytest.fail('invalid capture reached factorization'))
    if change == 'operator':
        owner._line_samples = ((object(),)+samples[0][1:],)+samples[1:]
    elif change == 'inventory':
        owner._line_terms = terms[:-1]
    else:
        owner._line_terms = ((terms[0][0], terms[0][1][:-1]),)+terms[1:]
    try:
        with pytest.raises(ValueError, match='BL5'):
            owner.buckling(public.GELineBucklingRequest(owner._generation))
    finally:
        owner._line_samples = samples; owner._line_terms = terms


def test_line_material_admission_and_compiled_weight_guard(accepted_owner, monkeypatch):
    owner = accepted_owner; before = owner.checkpoint()
    _, guard = buckling.capture(owner, owner._generation, lines=True)
    samples = owner._line_samples
    sample = list(samples[0]); sample[2] *= 1.01
    owner._line_samples = (tuple(sample),)+samples[1:]
    try:
        with pytest.raises(ValueError, match='model/support provenance'): guard()
    finally: owner._line_samples = samples
    def reject(*args): raise ValueError('injected unresolved yield boundary')
    monkeypatch.setattr(buckling, '_elastic_beam', reject)
    monkeypatch.setattr(buckling, 'factorize_cached', lambda *args: pytest.fail('material rejection reached factorization'))
    with pytest.raises(ValueError, match='yield boundary'):
        owner.buckling(public.GELineBucklingRequest(owner._generation))
    assert owner.checkpoint() == before


def test_optional_point_rows_retain_their_curvature():
    model = replace(definition('p0'), points=(public.PointConnection(1, 101),))
    owner = public.create_analysis(definition=model)
    try:
        result = owner.solve((public.NodalAction('beam', 105, (-1000.,0.,100.,0.,0.,0.)),),
                             (.5,1.), max_iterations=24, max_backtracks=12)
        assert result.status == 'completed'
        packet, _ = buckling.capture(owner, owner._generation, lines=True)
        assert len(packet.snapshot.multipliers) == 6+owner._C.shape[0]-6
        h, km = line_oracle(owner, packet)
        np.testing.assert_allclose(packet.hessian.toarray(), h, rtol=1e-11, atol=2e-6)
        np.testing.assert_allclose(packet.material.toarray(), km, rtol=1e-11, atol=2e-6)
        assert all(min(s.rows) >= 6 for s in packet.line_stations)
    finally: owner.close()
