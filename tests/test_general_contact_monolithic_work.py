"""Mapped two-body virtual work for the opt-in nodal-force equations."""

import numpy as np

from anysolver.general_contact.s3_patch_static import GeneralS3PatchManager
from anysolver.general_contact.semismooth import (
    linearize, raw_certificate, reference_nodal_support,
)
from scripts.general_contact_d1_mixed_mesh_jet2_schur_press import build_case


def test_mapped_source_target_force_and_smooth_tangent():
    model, definition, settings, _program = build_case(
        4, load_profile="distributed", total_force_n=0.3,
        target_right_x_m=1.3,
    )
    manager = GeneralS3PatchManager(model, definition, settings)
    z = 0.3*reference_nodal_support(manager.law)
    u = np.zeros(model.mesh.dof_manager.total_dofs)
    rng = np.random.default_rng(41)
    direction = rng.normal(size=len(u))
    direction /= np.linalg.norm(direction)

    base = linearize(manager, u, z, tangent=True)
    step = 2e-7
    plus = linearize(manager, u+step*direction, z, tangent=False)
    minus = linearize(manager, u-step*direction, z, tangent=False)
    force_fd = (plus.force-minus.force)/(2*step)
    predicted = base.tangent @ direction
    assert np.linalg.norm(force_fd-predicted)/np.linalg.norm(predicted) < 1e-5
    gap_fd = (plus.state.normalized_gap-minus.state.normalized_gap)/(2*step)
    gap_predicted = base.gap_gradient @ direction
    assert np.linalg.norm(gap_fd-gap_predicted)/np.linalg.norm(gap_predicted) < 1e-5

    local_physical = -base.local_force.reshape(-1, 3)
    source_count = len(manager.law.source_node_ids)
    np.testing.assert_allclose(
        local_physical[:source_count].sum(axis=0)
        + local_physical[source_count:].sum(axis=0),
        0.0, atol=1e-9,
    )
    _force, _tangent, projected = manager.evaluate(u, tangent=False)
    reported = raw_certificate(manager, u, base, projected)
    assert reported.energy_evaluations == base.evaluations
    assert reported.pair_geometry_evaluations == base.evaluations
    np.testing.assert_allclose(reported.numerical_pressure_pa,
                               base.state.pressure, rtol=0.0, atol=0.0)
