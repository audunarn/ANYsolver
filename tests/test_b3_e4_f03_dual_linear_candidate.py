"""Biorthogonal dual-P1 line candidate, before F03 space selection."""

import numpy as np
import pytest

from scripts._b3_e4_f03_dual_linear_norm import (
    dual_linear_cosine_moments, dual_linear_gram,
    dual_linear_l2_gram)


@pytest.mark.parametrize("cells", (1, 2, 4, 8))
def test_dual_is_biorthogonal_to_continuous_primal_hats(cells):
    from scripts._b3_e4_f03_weak_line_candidate import LineMultiplierSpace
    knots = tuple(np.linspace(0., 1., cells+1))
    dual = LineMultiplierSpace("dual_linear", knots)
    primal = LineMultiplierSpace("continuous_linear", knots)
    roots, weights = np.polynomial.legendre.leggauss(4)
    cross = np.zeros((cells+1, cells+1))
    for left, right in zip(knots[:-1], knots[1:]):
        for root, weight in zip(roots, weights):
            station = (left+right)/2+(right-left)*root/2
            values = dual.values(station)
            assert np.sum(values) == pytest.approx(1.)
            cross += (right-left)*weight/2*np.outer(
                values, primal.values(station))
    expected = np.diag(np.r_[1/(2*cells),
                              np.full(cells-1, 1/cells), 1/(2*cells)])
    np.testing.assert_allclose(cross, expected, rtol=1e-14, atol=1e-15)


def test_dual_cosine_moments_match_independent_gauss_integration():
    from scripts._b3_e4_f03_weak_line_candidate import LineMultiplierSpace
    cells = 4
    space = LineMultiplierSpace("dual_linear",
                                tuple(np.linspace(0., 1., cells+1)))
    roots, weights = np.polynomial.legendre.leggauss(32)
    observed = np.zeros((cells+1, 13))
    for cell in range(cells):
        for root, weight in zip(roots, weights):
            station = (cell+(root+1)/2)/cells
            cosine = np.r_[1., np.sqrt(2.)*
                np.cos(np.pi*np.arange(1, 13)*station)]
            observed += weight/(2*cells)*np.outer(
                space.values(station), cosine)
    np.testing.assert_allclose(
        dual_linear_cosine_moments(cells, 0, 13), observed,
        rtol=1e-11, atol=1e-12)
    lower, upper = dual_linear_gram(cells, 1., 4095)
    assert np.linalg.eigvalsh(lower)[0] > 0.
    assert np.linalg.eigvalsh(upper-lower)[0] > -1e-12


def test_dual_hminus_one_and_exact_l2_norms_match_basis_work():
    from scripts._b3_e4_f03_weak_line_candidate import LineMultiplierSpace

    cells = 4
    length = 1.
    space = LineMultiplierSpace("dual_linear",
                                tuple(np.linspace(0., 1., cells+1)))
    roots, weights = np.polynomial.legendre.leggauss(4)
    integrated = np.zeros((space.count, space.count))
    for cell in range(cells):
        for root, weight in zip(roots, weights):
            station = (cell+(root+1)/2)/cells
            value = space.values(station)
            integrated += weight/(2*cells)*np.outer(value, value)
    l2 = dual_linear_l2_gram(cells, length)
    np.testing.assert_allclose(l2, integrated, rtol=1e-14, atol=1e-15)
    lower, upper = dual_linear_gram(
        cells, length, 4095, sobolev_order=1.)
    half, _ = dual_linear_gram(cells, length, 4095)
    ones = np.ones(space.count)
    alternating = np.array([1., -1., 1., -1., 1.])
    assert ones @ lower @ ones == pytest.approx(length**2, abs=1e-12)
    assert ones @ l2 @ ones == pytest.approx(length**2, abs=1e-12)
    assert (0. < alternating @ lower @ alternating
            < alternating @ half @ alternating
            < alternating @ l2 @ alternating)
    assert np.linalg.eigvalsh(upper-lower)[0] > -1e-14
    with pytest.raises(ValueError, match="dual order"):
        dual_linear_gram(cells, length, 4, sobolev_order=0.)


@pytest.mark.parametrize("topology", ("Q4", "S3-V2D"))
@pytest.mark.parametrize("shell_port", ("rail", "local_translation"))
def test_dual_reference_kkt_matches_weak_derivative(topology, shell_port):
    from scripts._b3_e4_f03_e4_trial_panel import FlatE4TrialPanel
    from scripts._b3_e4_f03_native_fixture import build
    from scripts._b3_e4_f03_shell_trace import make_shell
    from scripts._b3_e4_f03_weak_line_candidate import (
        LineMultiplierSpace, assemble_reference_kkt, integrate_weak_line)
    shell = FlatE4TrialPanel(make_shell(1, topology))
    beam = build(4)
    space = LineMultiplierSpace("dual_linear", (0., .5, 1.))
    kkt = assemble_reference_kkt(shell, beam, space, shell_port=shell_port)
    rng = np.random.default_rng(4711)
    shell_direction = rng.normal(size=(shell.panel.node_count, 6))*.001
    beam_direction = rng.normal(size=beam.context.count)*.001
    beam_direction[list(beam.context.fixed)] = 0.
    for node in (0, 2*shell.panel.n_s+1,
                 2*(2*shell.panel.n_s+1)):
        shell_direction[node] = 0.
    weak = integrate_weak_line(
        shell, beam, space, np.zeros((space.count, 6)),
        np.zeros_like(shell_direction).ravel(),
        np.zeros_like(shell_direction).ravel(),
        shell_direction, np.zeros_like(shell_direction),
        beam.context.initial.mechanical,
        beam_direction, np.zeros_like(beam_direction), shell_port=shell_port)
    direction = np.r_[shell_direction.ravel(), beam_direction]
    np.testing.assert_allclose(kkt.constraint_jacobian@direction,
                               weak.weak_first.ravel(),
                               rtol=2e-11, atol=2e-12)
