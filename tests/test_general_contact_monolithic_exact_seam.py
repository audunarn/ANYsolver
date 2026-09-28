"""Opt-in raw nodal-force work at the artificial Q4/S3 target seam."""

import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from anysolver.assembly import build_constraint_transformation
from anysolver.general_contact.q4_s3_overlap_derivatives import UnsupportedQ4S3Branch
from anysolver.general_contact import s3_patch_augmented
from anysolver.general_contact.s3_patch_static import GeneralS3PatchManager
from anysolver.matrix_assembly import assemble_stiffness_matrix
from scripts.general_contact_d1_coupled_refinement import build_case


def _case():
    model, definition, settings, _program = build_case(
        4, 2, True, gap_certificate="projected_matching",
        gap_tolerance=5.0e-5, normal_approach=0.01504,
    )
    settings = replace(
        settings, q4_s3_shared_edge_tie_step_m=3.0e-8,
        q4_s3_shared_edge_tie_direction=(1.0, 0.0, 0.0),
        q4_s3_shared_edge_tie_relative_tolerance=1.0e-6,
    )
    owner = GeneralS3PatchManager(model, definition, settings)
    saved = json.loads((Path(__file__).parent / "fixtures" /
                        "general_contact_q4_s3_neighbor_value_gate_pose.json").read_text())
    source = np.asarray(saved["source"])
    target = np.asarray(saved["target"])
    model.apply_boundary_conditions()
    stiffness, _ = assemble_stiffness_matrix(model)
    _, _, transform, _, _, _ = build_constraint_transformation(
        stiffness, np.zeros(model.mesh.dof_manager.total_dofs), model,
    )
    owner.restrict_tangent_to_reduced_variations(transform)
    base = owner.law.geometry.evaluate(source, target)
    z = np.asarray(saved["multipliers"])*base.reference_support
    return owner, source, target, base, z


def test_raw_nodal_force_exact_seam_has_supported_gap_rows_and_tangent():
    owner, source, target, base, z = _case()
    supported = np.flatnonzero(base.reference_support > 0.0)
    assert len(supported) > 1
    z[supported[0]] = 0.0
    work = owner.law.nodal_force_linearization(source, target, z, tangent=True)
    first_order = owner.law.nodal_force_linearization(
        source, target, z, tangent=False,
    )
    assert work.energy_evaluations <= owner.law.geometry.maximum_energy_evaluations
    np.testing.assert_allclose(work.state.normalized_gap, base.normalized_gap,
                               rtol=0.0, atol=0.0)
    np.testing.assert_allclose(work.residual, -z @ work.gap_gradient,
                               rtol=1e-6, atol=1e-10)
    np.testing.assert_allclose(first_order.residual, work.residual,
                               rtol=1e-6, atol=1e-10)
    np.testing.assert_allclose(first_order.gap_gradient, work.gap_gradient,
                               rtol=1e-6, atol=1e-10)
    assert np.linalg.norm(work.gap_gradient[supported[0]]) > 0.0
    np.testing.assert_allclose(work.tangent, work.tangent.T,
                               rtol=1e-6, atol=1e-10)

    coordinates = np.concatenate((source, target)).reshape(-1)
    for coordinate in (3*1, 3*2+2, 3*(len(source)+1)):
        h = 7.5e-9
        observations = []
        for sign in (-1.0, 1.0):
            displaced = coordinates.copy()
            displaced[coordinate] += sign*h
            observations.append(owner.law.geometry.evaluate(
                displaced[:3*len(source)].reshape(-1, 3),
                displaced[3*len(source):].reshape(-1, 3),
            ).normalized_gap)
        observed = (observations[1]-observations[0])/(2*h)
        np.testing.assert_allclose(work.gap_gradient[supported, coordinate],
                                   observed[supported], rtol=1e-5, atol=1e-8)

    h = 1.0e-7
    shifted_minus = source.copy()
    shifted_plus = source.copy()
    shifted_minus[1, 0] -= h
    shifted_plus[1, 0] += h
    minus = owner.law.nodal_force_linearization(
        shifted_minus, target, z, tangent=False,
    )
    plus = owner.law.nodal_force_linearization(
        shifted_plus, target, z, tangent=False,
    )
    active = owner.law.tangent_active_coordinates
    observed_force_change = (plus.residual-minus.residual)/(2*h)
    predicted_force_change = work.tangent[:, 3]
    assert (np.linalg.norm((observed_force_change-predicted_force_change)[active])
            / np.linalg.norm(predicted_force_change[active]) < 1.0e-5)


def test_raw_nodal_force_seam_rejects_missing_opt_in_and_accepts_signed_trial(
        monkeypatch):
    owner, source, target, base, z = _case()
    supported = np.flatnonzero(base.reference_support > 0.0)
    saved_tie = owner.law.shared_edge_tie
    owner.law.shared_edge_tie = None
    with pytest.raises(UnsupportedQ4S3Branch):
        owner.law.nodal_force_linearization(source, target, z, tangent=False)
    owner.law.shared_edge_tie = saved_tie
    z[supported[0]] = -1.0e-4
    z[supported[1]] = 0.0
    tiny_wedge_calls = []
    original_verifier = s3_patch_augmented.verify_tiny_wedge_derivatives

    def checked_tiny_wedge(*args, **kwargs):
        tiny_wedge_calls.append(kwargs["force_scale_n"])
        return original_verifier(*args, **kwargs)

    monkeypatch.setattr(s3_patch_augmented, "verify_tiny_wedge_derivatives",
                        checked_tiny_wedge)
    work = owner.law.nodal_force_linearization(source, target, z, tangent=False)
    assert tiny_wedge_calls and all(scale > 0.0 for scale in tiny_wedge_calls)
    assert work.tangent is None
    np.testing.assert_allclose(work.residual, -z @ work.gap_gradient,
                               rtol=1e-6, atol=1e-10)
    assert np.linalg.norm(work.gap_gradient[supported[1]]) > 0.0


def test_raw_nodal_force_seam_rejects_unresolved_topology_and_resource_limit():
    owner, source, target, _base, z = _case()
    saved_tie = owner.law.shared_edge_tie
    shared = owner.law._d1_reference_diagonal()
    edge = target[shared[1]]-target[shared[0]]
    owner.law.shared_edge_tie = (saved_tie[0], edge/np.linalg.norm(edge),
                                 saved_tie[2])
    with pytest.raises(UnsupportedQ4S3Branch):
        owner.law.nodal_force_linearization(source, target, z, tangent=False)
    owner.law.shared_edge_tie = saved_tie
    original_faces = owner.law.target_face_indices
    owner.law.target_face_indices = original_faces + (original_faces[0],)
    with pytest.raises(UnsupportedQ4S3Branch):
        owner.law.nodal_force_linearization(source, target, z, tangent=False)
    owner.law.target_face_indices = original_faces
    owner.law.geometry.maximum_energy_evaluations = 100
    with pytest.raises(MemoryError, match="budget exhausted"):
        owner.law.nodal_force_linearization(source, target, z, tangent=False)


def test_raw_nodal_force_seam_resolves_gap_rows_at_zero_force():
    owner, source, target, base, _z = _case()
    work = owner.law.nodal_force_linearization(
        source, target, np.zeros_like(base.reference_support), tangent=True,
    )
    np.testing.assert_array_equal(work.residual, np.zeros_like(work.residual))
    np.testing.assert_array_equal(work.tangent, np.zeros_like(work.tangent))
    supported = np.flatnonzero(base.reference_support > 0.0)
    assert np.all(np.linalg.norm(work.gap_gradient[supported], axis=1) > 0.0)
    h = 7.5e-9
    shifted_minus = source.copy()
    shifted_plus = source.copy()
    shifted_minus[1, 0] -= h
    shifted_plus[1, 0] += h
    observed = (owner.law.geometry.evaluate(shifted_plus, target).normalized_gap
                - owner.law.geometry.evaluate(shifted_minus, target).normalized_gap)/(2*h)
    np.testing.assert_allclose(work.gap_gradient[supported, 3],
                               observed[supported], rtol=1e-5, atol=1e-8)


def test_raw_seam_rejects_biased_supported_zero_force_gap_row(monkeypatch):
    owner, source, target, base, z = _case()
    tiny_source = owner.law.source_face_indices[1]  # pair 2, two target faces
    local = next(index for index, node in enumerate(tiny_source)
                 if base.reference_support[node] > 0.0)
    node = tiny_source[local]
    z[node] = 0.0
    original_verifier = s3_patch_augmented.verify_tiny_wedge_derivatives
    calls = []

    def biased_zero_force_row(*args, **kwargs):
        used, scenarios = original_verifier(*args, **kwargs)
        calls.append(True)
        altered = []
        for gradient_error, hessian_error in scenarios:
            biased = gradient_error.copy()
            biased[1, local, 0] += 1.0e-4*base.reference_support[node]
            altered.append((biased, hessian_error))
        return used, tuple(altered)

    monkeypatch.setattr(s3_patch_augmented, "verify_tiny_wedge_derivatives",
                        biased_zero_force_row)
    with pytest.raises(UnsupportedQ4S3Branch,
                       match="raw supported gap derivative is unresolved"):
        owner.law.nodal_force_linearization(source, target, z, tangent=False)
    assert calls
