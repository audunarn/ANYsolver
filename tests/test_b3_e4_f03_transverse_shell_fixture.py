"""Bounded transverse refinement and explicit shell-support diagnostics."""

import numpy as np
import pytest

from scripts._b3_e4_f03_shell_trace import make_shell, _SAMPLE_OFFSETS
from scripts._b3_e4_f03_shell_finite_pose_candidate import (
    pose_from_e4_total, reference_nodes)
from scripts._b3_e4_f03_shell_spatial_linear_port import (
    physical_shell_stiffness)


@pytest.mark.parametrize("topology", ("Q4", "S3-V2D"))
@pytest.mark.parametrize("n_y", (2, 4, 8))
def test_transverse_grid_preserves_reference_samples_and_physical_assembly(
        topology, n_y):
    panel = make_shell(2, topology, n_y=n_y)
    nodes = reference_nodes(panel)
    assert nodes.shape == (panel.node_count, 3)
    assert panel.node_count == (n_y+1)*5
    for station in (0., .375, 1.):
        samples = panel.sample_weights(station)@nodes
        expected = np.array([(station+ox, y, 0.)
                             for ox, y in _SAMPLE_OFFSETS])
        np.testing.assert_allclose(samples, expected,
                                   rtol=0, atol=2e-15)
    edges = panel.breakpoints()
    for left, right in zip(edges[:-1], edges[1:]):
        first = left+(right-left)/4
        second = left+3*(right-left)/4
        for ox, y in _SAMPLE_OFFSETS:
            assert np.array_equal(panel._shape(first+ox, y)[0],
                                  panel._shape(second+ox, y)[0])
    origin, frame = pose_from_e4_total(
        panel, .375, np.zeros(6*panel.node_count))
    np.testing.assert_allclose(origin, (.375, 0., 0.), atol=2e-15)
    np.testing.assert_allclose(frame, np.eye(3), atol=2e-15)
    physical = physical_shell_stiffness(panel).toarray()
    in_plane = [6*i+axis for i in range(panel.node_count)
                for axis in (0, 1)]
    np.testing.assert_allclose(
        physical[np.ix_(in_plane, in_plane)], panel.stiffness.toarray(),
        rtol=2e-15, atol=2e-5)


@pytest.mark.parametrize("topology", ("Q4", "S3-V2D"))
def test_default_two_row_fixture_is_exactly_the_explicit_two_row_fixture(
        topology):
    default = make_shell(2, topology)
    explicit = make_shell(2, topology, n_y=2)
    np.testing.assert_array_equal(default.stiffness.data,
                                  explicit.stiffness.data)
    np.testing.assert_array_equal(default.stiffness.indices,
                                  explicit.stiffness.indices)
    np.testing.assert_array_equal(default.stiffness.indptr,
                                  explicit.stiffness.indptr)
    np.testing.assert_array_equal(default.free, explicit.free)
    np.testing.assert_array_equal(default.breakpoints(),
                                  explicit.breakpoints())


def test_explicit_both_edges_supports_all_in_plane_edge_coordinates():
    from scripts._b3_e4_f03_e4_trial_panel import FlatE4TrialPanel
    from scripts._b3_e4_f03_native_fixture import build
    from scripts._b3_e4_f03_weak_line_candidate import (
        LineMultiplierSpace, assemble_reference_kkt)
    shell = FlatE4TrialPanel(make_shell(1, "Q4", n_y=4))
    beam = build(4)
    space = LineMultiplierSpace("piecewise_constant", (0., 1.))
    old = assemble_reference_kkt(shell, beam, space)
    new = assemble_reference_kkt(
        shell, beam, space, shell_support_policy="both_xy_edges")
    assert old.shell_support_policy == "legacy_three_left_nodes"
    assert new.shell_support_policy == "both_xy_edges"
    old_free, new_free = set(old.free_primal), set(new.free_primal)
    nx = 2*shell.panel.n_s
    assert 6*nx in old_free
    for j in range(shell.panel.n_y+1):
        for i in (0, nx):
            for axis in (0, 1):
                assert 6*(j*(nx+1)+i)+axis not in new_free
    assert 6*(4*(nx+1))+0 in old_free
    with pytest.raises(ValueError, match="support policy"):
        assemble_reference_kkt(
            shell, beam, space, shell_support_policy="unknown")


def test_full_left_edge_matches_legacy_at_two_y_intervals_and_scales_with_rows():
    from scripts._b3_e4_f03_e4_trial_panel import FlatE4TrialPanel
    from scripts._b3_e4_f03_native_fixture import build
    from scripts._b3_e4_f03_weak_line_candidate import (
        LineMultiplierSpace, assemble_reference_kkt)
    beam = build(4)
    space = LineMultiplierSpace("piecewise_constant", (0., 1.))
    for n_y in (2, 4):
        shell = FlatE4TrialPanel(make_shell(1, "Q4", n_y=n_y))
        legacy = assemble_reference_kkt(shell, beam, space)
        full = assemble_reference_kkt(
            shell, beam, space, shell_support_policy="full_left_edge")
        if n_y == 2:
            np.testing.assert_array_equal(full.free_primal, legacy.free_primal)
            np.testing.assert_allclose(full.scaled_system,
                                       legacy.scaled_system, rtol=0, atol=0)
        nx = 2*shell.panel.n_s
        free = set(full.free_primal)
        for j in range(n_y+1):
            for axis in range(6):
                assert 6*j*(nx+1)+axis not in free
        if n_y == 4:
            assert len(legacy.free_primal)-len(full.free_primal) == 12


def test_transverse_grid_mutation_invalidates_owned_trial():
    from scripts._b3_e4_f03_e4_trial_panel import FlatE4TrialPanel
    shell = FlatE4TrialPanel(make_shell(1, "Q4", n_y=4))
    shell.panel.n_y = 8
    with pytest.raises(ValueError, match="definition or predecessor"):
        shell.guard()
