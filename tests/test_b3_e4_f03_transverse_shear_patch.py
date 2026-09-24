"""Bounded admissible transverse-shear patch for the shell/B3 line ports."""

import numpy as np
import pytest

from scripts._b3_e4_f03_e4_trial_panel import FlatE4TrialPanel
from scripts._b3_e4_f03_native_fixture import build
from scripts._b3_e4_f03_native_spatial_port import NativeHalfCellSpatialPort
from scripts._b3_e4_f03_shell_finite_pose_candidate import (
    pose_from_e4_total, reference_nodes)
from scripts._b3_e4_f03_shell_spatial_linear_port import physical_shell_stiffness
from scripts._b3_e4_f03_shell_trace import make_shell


@pytest.mark.parametrize("topology", ("Q4", "S3-V2D"))
@pytest.mark.parametrize("n_y", (2, 4, 8))
def test_bonded_trace_admits_nonzero_transverse_shear(topology, n_y):
    panel = make_shell(4, topology, n_y=n_y)
    gamma = .02
    shell_total = np.zeros((panel.node_count, 6))
    shell_total[:, 2] = gamma*reference_nodes(panel)[:, 0]
    shell_total = shell_total.ravel()

    shell_energy = float(.5*shell_total@(
        physical_shell_stiffness(panel)@shell_total))
    shear_modulus = 210e9/(2*(1+.3))
    unrelaxed_energy = .5*(5/6)*shear_modulus*panel.thickness*2.*gamma**2
    if topology == "Q4":
        np.testing.assert_allclose(shell_energy, unrelaxed_energy,
                                   rtol=1e-12)
    else:
        trial = FlatE4TrialPanel(panel)
        factors = np.array([
            element.compute_stiffness_components(
                trial.model.mesh, trial.model.get_material("steel"))["phi_squared"]
            for _, _, element in trial.elements])
        np.testing.assert_allclose(factors, factors[0], rtol=1e-12)
        assert 0. < factors[0] < 1.
        np.testing.assert_allclose(shell_energy, unrelaxed_energy*factors[0],
                                   rtol=1e-12)

    beam = build(16)
    beam_step = np.zeros(beam.context.count)
    beam_nodes = (beam.context.initial.mechanical.positions+
                  beam.context.initial.mechanical.position_low)
    beam_step[2:beam.context.nodal_count:6] = gamma*beam_nodes[:, 0]
    beam_trial = beam.context.advance(beam.context.initial.mechanical, beam_step)
    for station in (0., .17, .37, .63, 1.):
        element, cell, fraction, _ = beam._locate(station)
        port = NativeHalfCellSpatialPort(beam.context, element, cell, fraction)
        beam_position, beam_frame = port.pose(beam_trial)
        shell_position, shell_frame = pose_from_e4_total(
            panel, station, shell_total)
        np.testing.assert_allclose(shell_position, beam_position, atol=1e-14)
        np.testing.assert_allclose(shell_frame, beam_frame, atol=1e-14)
        np.testing.assert_allclose(shell_frame[:, 2], (0., 0., 1.), atol=1e-14)
    geometric_normal = np.array((-gamma, 0., 1.))
    geometric_normal /= np.linalg.norm(geometric_normal)
    assert np.linalg.norm(shell_frame[:, 2]-geometric_normal) > .01
