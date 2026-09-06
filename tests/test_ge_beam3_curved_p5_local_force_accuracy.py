"""Small opt-in solver-accuracy tests; no full arch or qualification wave."""

from dataclasses import asdict, replace
import json

import numpy as np
import pytest

from docs.reference_cases.ge_beam3_curved_p5_nonlinear_mixed_probe import (
    LocalForceAccuracy, NonlinearLocalError, NonlinearMixedBeamProbe, _accuracy_metrics,
)
from docs.reference_cases.ge_beam3_curved_p5_section_probe import SectionHistory
from docs.reference_cases.ge_beam3_curved_p5_algebra_probe import rotation
from test_ge_beam3_curved_p5_nonlinear_mixed_probe import law
from test_ge_beam3_curved_p5_algebra_probe import reference, perturbed
from test_ge_beam3_curved_p5_local_residual_diagnostic import witness


def test_refines_accepted_but_force_inaccurate_internal_witness(witness):
    model, root, _, old, _, _, _, (x, q, u, m) = witness
    accuracy = LocalForceAccuracy(1e-12, 2.)
    made = model.solve(x, q, initial_rotations=u, initial_moments=m, force_accuracy=accuracy)
    evaluated = model.evaluate(x, q, made.local_rotations, made.moments)
    assert old.iterations == 0 and np.linalg.norm(old.residual-root.residual) > 1e-10
    assert made.iterations > 0 and made.local_residual_norm <= 1e-11
    assert _accuracy_metrics(evaluated, accuracy)[1] <= accuracy.limit
    assert np.linalg.norm(made.residual-root.residual) < 1e-12
    # The actual residual is returned, not a Schur-corrected/fabricated force.
    np.testing.assert_array_equal(made.residual, evaluated.residual[:18])
    assert made.potential == evaluated.potential
    serialize = lambda v: json.dumps([asdict(s) for s in v], default=lambda v: v.tolist(), sort_keys=True)
    assert serialize(made.stations) == serialize(evaluated.stations)


@pytest.mark.parametrize('limit,length,scale', [
    (True, 1., 1.), (0., 1., 1.), (-1., 1., 1.), (1e-10, 1., 1.),
    (1e-12, 0., 1.), (1e-12, float('nan'), 1.), (1e-12, 1., .5),
    (float('inf'), 1., 1.), ('1e-12', 1., 1.), (1e-12, 1., True),
])
def test_accuracy_contract_rejects_invalid_or_relaxed_values(limit, length, scale):
    with pytest.raises(ValueError):
        LocalForceAccuracy(limit, length, scale)


def test_error_scaling_and_spatial_rotation_covariance(witness):
    _, _, _, _, ev, _, _, _ = witness
    a = LocalForceAccuracy(1e-12, 2.)
    original = _accuracy_metrics(ev, a)[1]
    assert _accuracy_metrics(ev, replace(a, force_scale=2.))[1] == original/2
    g = rotation([.8, -.4, .3])
    transform = np.eye(36)
    transform[:24, :24] = np.kron(np.eye(8), g)
    moved = replace(ev, residual=transform @ ev.residual,
                    hessian=transform @ ev.hessian @ transform.T)
    assert abs(_accuracy_metrics(moved, a)[1]/original-1) < 1e-10


@pytest.mark.parametrize('height,yield_force', [(0., 1000.), (.4, 1000.), (.4, .02)])
def test_coupled_elastic_and_plastic_origins_are_fixed(height, yield_force):
    ref = reference(height)
    x, q, _ = perturbed(ref)
    origins = tuple(SectionHistory(.0001*i, .0002*i) for i in range(16))
    model = NonlinearMixedBeamProbe(ref, law(yield_force), order=8, origins=origins)
    accuracy = LocalForceAccuracy(1e-12, 2.)
    made = model.solve(x, q, force_accuracy=accuracy)
    ev = model.evaluate(x, q, made.local_rotations, made.moments)
    assert _accuracy_metrics(ev, accuracy)[1] <= accuracy.limit
    assert made.local_residual_norm <= 1e-11 and made.evaluations <= 64
    assert tuple(s.response.origin for s in made.stations) == model.origins == origins
    assert any(s.response.plastic_active for s in made.stations) == (yield_force == .02)
    np.testing.assert_array_equal(made.residual, ev.residual[:18])


def test_failure_is_bounded_and_cannot_commit(witness):
    model, _, _, _, _, _, _, (x, q, u, m) = witness
    origins = model.origins
    accuracy = LocalForceAccuracy(1e-12, 2.)
    for kwargs in ({'max_iterations': 0}, {'max_evaluations': 1}):
        with pytest.raises(NonlinearLocalError, match='budget'):
            model.solve(x, q, initial_rotations=u, initial_moments=m,
                        force_accuracy=accuracy, **kwargs)
        assert model.origins == origins
    with pytest.raises(ValueError, match='LocalForceAccuracy'):
        model.solve(x, q, force_accuracy={})


def test_default_path_is_identical_to_explicit_none(witness):
    model, _, _, _, _, _, _, (x, q, u, m) = witness
    kwargs = dict(initial_rotations=u, initial_moments=m)
    a = model.solve(x, q, **kwargs)
    b = model.solve(x, q, force_accuracy=None, **kwargs)
    serialize = lambda v: json.dumps(asdict(v), default=lambda v: v.tolist(), sort_keys=True)
    assert serialize(a) == serialize(b)


def test_nonfinite_and_singular_estimates_fail_closed(witness):
    _, _, _, _, ev, _, _, _ = witness
    a = LocalForceAccuracy(1e-12, 2.)
    h = ev.hessian.copy(); h[18:, 18:] = 0
    with pytest.raises(NonlinearLocalError, match='singular'):
        _accuracy_metrics(replace(ev, hessian=h), a)
    r = ev.residual.copy(); r[18] = float('nan')
    with pytest.raises(NonlinearLocalError, match='nonfinite'):
        _accuracy_metrics(replace(ev, residual=r), a)


@pytest.mark.parametrize('yield_force', [1000., .02])
def test_opt_in_directional_energy_residual_and_tangent(yield_force):
    ref = reference(.4)
    x, q, _ = perturbed(ref)
    model = NonlinearMixedBeamProbe(ref, law(yield_force), order=8)
    accuracy = LocalForceAccuracy(1e-12, 2.)
    root = model.solve(x, q, force_accuracy=accuracy)
    direction = np.sin(np.arange(18)+.2)/8
    step = 1e-6
    evaluations = []
    for sign in (1., -1.):
        delta = sign*step*direction.reshape(3, 6)
        made_q = np.array([rotation(delta[n, 3:]) @ q[n] for n in range(3)])
        solved = model.solve(x+delta[:, :3], made_q, force_accuracy=accuracy)
        # Common external increment chart, as required for the Hessian check.
        evaluations.append(model.evaluate(x, q, solved.local_rotations, solved.moments,
                                          increment=np.r_[delta.ravel(), np.zeros(18)]))
    plus, minus = evaluations
    active = lambda v: tuple(s.response.plastic_active for s in v.stations)
    assert active(plus) == active(root) == active(minus)
    assert abs((plus.potential-minus.potential)/(2*step)-root.residual @ direction) < 1e-7
    assert np.linalg.norm((plus.residual[:18]-minus.residual[:18])/(2*step)-root.tangent @ direction) < 1e-7


def test_opt_in_is_deterministic_and_singular_failures_do_not_fall_back(witness, monkeypatch):
    model, _, _, _, ev, _, _, (x, q, u, m) = witness
    accuracy = LocalForceAccuracy(1e-12, 2.)
    kwargs = dict(initial_rotations=u, initial_moments=m, force_accuracy=accuracy)
    a, b = model.solve(x, q, **kwargs), model.solve(x, q, **kwargs)
    serialize = lambda v: json.dumps(asdict(v), default=lambda v: v.tolist(), sort_keys=True)
    assert serialize(a) == serialize(b)
    h = ev.hessian.copy(); h[18:, 18:] = 0
    monkeypatch.setattr(model, 'evaluate', lambda *a, **kw: replace(ev, hessian=h))
    with pytest.raises(NonlinearLocalError, match='singular'):
        model.solve(x, q, **kwargs)
