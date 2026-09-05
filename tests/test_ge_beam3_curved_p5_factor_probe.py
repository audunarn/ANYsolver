"""Small reference-factor diagnostics; no slenderness qualification claims."""

import numpy as np
import pytest

from docs.reference_cases.ge_beam3_curved_p5_algebra_probe import (
    reference_hessians, rigid_matrix, rotation, T6,
)
from docs.reference_cases.ge_beam3_curved_p5_factor_probe import (
    constant_spatial_moment_mode, reference_factors,
)
from test_ge_beam3_curved_p5_algebra_probe import (
    assert_scaled_close, reference, section,
)


@pytest.mark.parametrize("geometry", [(0., 0., 0.), (.4, 0., 0.), (.6, .2, .15)])
def test_factors_reconstruct_reference_operator_and_eliminate_local_rotations(geometry):
    ref = reference(*geometry)
    factors = reference_factors(ref, section())
    _, reduced, condensed = reference_hessians(ref, section())
    assert factors.full.shape == (18, 24)
    assert factors.condensed.shape == (12, 18)
    assert factors.local_map.shape == (6, 18)
    assert_scaled_close(factors.full.T @ factors.full, reduced)
    assert_scaled_close(factors.condensed.T @ factors.condensed, condensed)
    assert_scaled_close(factors.local_map,
                        -np.linalg.solve(reduced[18:, 18:], reduced[18:, :18]))
    assert_scaled_close(factors.condensed @ rigid_matrix(ref.coordinates), np.zeros((12, 6)))
    assert np.linalg.matrix_rank(factors.condensed, tol=1e-10) == 12
    assert not factors.full.flags.writeable
    assert not factors.condensed.flags.writeable
    assert not factors.local_map.flags.writeable


@pytest.mark.parametrize("geometry", [(0., 0., 0.), (.4, 0., 0.), (.6, .2, .15)])
def test_manufactured_moment_satisfies_local_equilibrium_without_force_strain(geometry):
    ref = reference(*geometry)
    elastic = np.diag([100.]*3+[1., 2., 3.])
    q, local, expected = constant_spatial_moment_mode(ref, elastic, [.3, -.4, 1.])
    factors = reference_factors(ref, elastic)
    full_vector = np.concatenate((q, local))
    residual = factors.full @ full_vector
    assert_scaled_close(factors.full[:, 18:].T @ residual, np.zeros(6))
    assert_scaled_close(factors.local_map @ q, local)
    assert_scaled_close(residual @ residual / 2, expected)
    assert_scaled_close(factors.energy(q), expected)


@pytest.mark.parametrize("geometry", [(0., 0., 0.), (.4, 0., 0.), (.6, .2, .15)])
def test_high_contrast_factor_error_obeys_roundoff_bound_not_qualification_tolerance(geometry):
    ref = reference(*geometry)
    elastic = np.diag([1e12]*3+[1., 2., 3.])
    q, local, expected = constant_spatial_moment_mode(ref, elastic, [.3, -.4, 1.])
    factors = reference_factors(ref, elastic)
    error = abs(factors.energy(q)-expected)
    # A scale-aware algorithmic roundoff bound, NOT a relaxed mechanics gate.
    # The fixed 1e-11 qualification check is intentionally not claimed here.
    amplitude_error = 64*np.finfo(float).eps*np.linalg.norm(factors.full)*np.linalg.norm(
        np.concatenate((q, local)))
    energy_error_bound = np.sqrt(2*expected)*amplitude_error + amplitude_error**2/2
    assert error <= energy_error_bound
    direct = reference_hessians(ref, elastic)[2]
    direct_error = abs(q @ direct @ q / 2-expected)
    # At this fixed diagnostic geometry/contrast, expose the regression that
    # motivated retaining energy factors. Do not interpret as domain coverage.
    assert error < direct_error/100


def test_factor_energy_is_covariant_and_reversal_consistent():
    ref = reference(.6, .2, .15)
    elastic = section()
    q = np.linspace(-.4, .3, 18).reshape(3, 6)
    original = reference_factors(ref, elastic).energy(q.ravel())
    transform = rotation((.6, -.8, 1.1))
    moved = ref.rigidly_transformed(transform, np.array((3., -2., 1.)))
    rotated = q.copy()
    rotated[:, :3] = q[:, :3] @ transform.T
    rotated[:, 3:] = q[:, 3:] @ transform.T
    assert_scaled_close(reference_factors(moved, elastic).energy(rotated.ravel()), original)
    assert_scaled_close(reference_factors(ref.reversed(), T6 @ elastic @ T6.T).energy(
        q[::-1].ravel()), original)


def test_factor_repeated_evaluation_and_invalid_inputs():
    ref = reference()
    first = reference_factors(ref, section())
    second = reference_factors(ref, section())
    for name in ("full", "condensed", "local_map"):
        assert np.array_equal(getattr(first, name), getattr(second, name))
    for invalid in (np.zeros(17), np.full(18, np.nan), np.zeros((3, 6))):
        with pytest.raises(ValueError, match="18-component"):
            first.energy(invalid)
    with pytest.raises(ValueError, match="uncoupled"):
        constant_spatial_moment_mode(ref, section(), [1., 0., 0.])
    with pytest.raises(ValueError, match="spatial moment"):
        constant_spatial_moment_mode(ref, np.eye(6), [np.nan, 0., 0.])
    with pytest.raises(ValueError, match="positive definite"):
        reference_factors(ref, np.zeros((6, 6)))
