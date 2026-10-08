"""Flat-reference six-channel shell trace with actual Q4/S3 physical blocks."""

import numpy as np
import pytest

from scripts._b3_e4_f03_shell_trace import make_shell
from scripts._b3_e4_f03_shell_spatial_linear_port import (
    physical_shell_stiffness, reference_spatial_trace,
    reference_wrench_pullback)


def _reference_nodes(panel):
    nx = 2*panel.n_s
    return np.array([(-.5+i/panel.n_s, y, 0.)
                     for y in (-.5, 0., .5) for i in range(nx+1)])


@pytest.mark.parametrize("topology", ("Q4", "S3-V2D"))
@pytest.mark.parametrize("n_s", (1, 2))
def test_reference_port_recovers_all_six_infinitesimal_rigid_channels(
        topology, n_s):
    panel = make_shell(n_s, topology)
    nodes = _reference_nodes(panel)
    for station in (0., .37, .5, 1.):
        trace = reference_spatial_trace(panel, station)
        assert trace.shape == (6, 6*panel.node_count)
        np.testing.assert_array_equal(trace[:, 5::6], 0.)
        for translation, rotation in (
                ((.07, -.03, .09), (.0, .0, .0)),
                ((0., 0., 0.), (.04, -.06, .11)),
                ((-.03, .05, 0.), (-.08, .02, -.05))):
            translation, rotation = np.array(translation), np.array(rotation)
            values = np.zeros((panel.node_count, 6))
            values[:, :3] = translation+np.cross(rotation, nodes)
            values[:, 3:] = rotation
            expected = np.r_[translation+np.cross(rotation, (station, 0., 0.)),
                             rotation]
            np.testing.assert_allclose(trace@values.ravel(), expected,
                                       rtol=0, atol=2e-15)


@pytest.mark.parametrize("topology", ("Q4", "S3-V2D"))
def test_director_tilt_is_independent_of_midsurface_slope_and_drilling(topology):
    panel = make_shell(2, topology)
    trace = reference_spatial_trace(panel, .37)
    nodes = _reference_nodes(panel)
    slope_only = np.zeros((panel.node_count, 6))
    slope_only[:, 2] = .04*nodes[:, 1]
    assert np.linalg.norm((trace@slope_only.ravel())[3:]) < 1e-15
    director_only = np.zeros_like(slope_only)
    director_only[:, 3] = .04
    np.testing.assert_allclose((trace@director_only.ravel())[3:],
                               (.04, 0., 0.), rtol=0, atol=1e-15)
    wrench = np.array((2., -3., 5., 7., -11., 13.))
    pulled = reference_wrench_pullback(panel, .37, wrench)
    np.testing.assert_array_equal(pulled[5::6], 0.)
    np.testing.assert_allclose(pulled@director_only.ravel(), .04*wrench[3],
                               rtol=0, atol=1e-14)
    yaw_wrench = np.zeros(6)
    yaw_wrench[5] = 1.
    yaw_load = reference_wrench_pullback(panel, .37, yaw_wrench)
    assert np.linalg.norm(yaw_load[0::6]) > 0.
    assert np.linalg.norm(yaw_load[1::6]) > 0.
    np.testing.assert_array_equal(yaw_load.reshape(-1, 6)[:, 2:], 0.)
    np.testing.assert_allclose(yaw_load.reshape(-1, 6)[:, :3].sum(axis=0),
                               0., rtol=0, atol=2e-14)
    moment_about_station = np.sum(np.cross(
        nodes-np.array((.37, 0., 0.)),
        yaw_load.reshape(-1, 6)[:, :3]), axis=0)
    np.testing.assert_allclose(moment_about_station, (0., 0., 1.),
                               rtol=0, atol=2e-14)
    with pytest.raises(ValueError, match="finite six-component"):
        reference_wrench_pullback(panel, .37, np.ones(5))


@pytest.mark.parametrize("topology", ("Q4", "S3-V2D"))
def test_full_physical_shell_matrix_matches_old_inplane_projection(topology):
    panel = make_shell(1, topology)
    physical = physical_shell_stiffness(panel)
    assert physical.shape == (6*panel.node_count,)*2
    assert np.isfinite(physical.data).all()
    inplane = np.array([6*node+axis for node in range(panel.node_count)
                        for axis in (0, 1)])
    np.testing.assert_allclose(physical[np.ix_(inplane, inplane)].toarray(),
                               panel.stiffness.toarray(), rtol=3e-14, atol=1e-5)
    scale = np.linalg.norm(physical.data)
    assert np.linalg.norm(physical[:, 5::6].data) < 1e-14*scale
    assert np.linalg.norm((physical-physical.T).data) < 1e-14*scale
    nodes = _reference_nodes(panel)
    for axis in range(6):
        values = np.zeros((panel.node_count, 6))
        if axis < 3:
            values[:, axis] = 1.
        else:
            rotation = np.eye(3)[axis-3]
            values[:, :3] = np.cross(rotation, nodes)
            values[:, 3:] = rotation
        q = values.ravel()
        assert np.linalg.norm(physical@q) < 1e-10*scale*np.linalg.norm(q)


@pytest.mark.parametrize("topology", ("Q4", "S3-V2D"))
def test_physical_shell_matrix_keeps_transverse_shear_field(topology):
    panel = make_shell(1, topology)
    physical = physical_shell_stiffness(panel)
    nodes = _reference_nodes(panel)
    slope_without_director = np.zeros((panel.node_count, 6))
    slope_without_director[:, 2] = .01*nodes[:, 1]
    q = slope_without_director.ravel()
    energy = float(q@(physical@q))
    assert energy > 0.
    trace = reference_spatial_trace(panel, .37)
    np.testing.assert_allclose((trace@q)[3:], 0., rtol=0, atol=1e-15)
