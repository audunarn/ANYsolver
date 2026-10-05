"""Partial-overlap path checks; no generic finite-rotation CCD claim."""
from dataclasses import replace

import numpy as np

from anysolver.general_contact import s3_patch_static as owner
from test_general_contact_projected_penalty import _candidate


def _manager():
    model, definition, settings = _candidate()
    return model, owner.GeneralS3PatchManager(model, definition, settings)


def test_partial_children_retain_original_path_endpoint_enclosures(monkeypatch):
    _, manager = _manager()
    calls = []

    def force_subdivision(*args, endpoint_errors=None):
        calls.append(endpoint_errors)
        # First interval must subdivide, even though its endpoint gaps pass.
        if len(calls) == 1:
            return -np.inf, 1
        return 0.0, 1

    monkeypatch.setattr(owner, "overlap_local_swept_lower", force_subdivision)
    first = np.zeros(manager.n_dof)
    assert manager._swept_admissible(first, first)
    assert calls[0] is not None
    assert all(np.array_equal(error, np.zeros_like(error)) for error in calls[0])
    assert any(np.any(error > 0.0) for call in calls[1:] for error in call)


def test_enclosed_child_orientation_cannot_use_only_rounded_representative(monkeypatch):
    _, manager = _manager()
    real_midpoint = owner._affine_midpoint_with_error
    gap_calls = 0

    def force_subdivision(*args, **kwargs):
        nonlocal gap_calls
        gap_calls += 1
        return (-np.inf if gap_calls == 1 else 0.0), 1

    def uncertain_midpoint(*args):
        middle, errors = real_midpoint(*args)
        # A deliberately uncertain child can contain inverted geometry even
        # though its rounded representative is valid. It must not certify.
        return middle, tuple(error + 2.0 for error in errors)

    manager.settings = replace(manager.settings, maximum_swept_subdivisions=1)
    monkeypatch.setattr(owner, "overlap_local_swept_lower", force_subdivision)
    monkeypatch.setattr(owner, "_affine_midpoint_with_error", uncertain_midpoint)
    first = np.zeros(manager.n_dof)
    assert not manager._swept_admissible(first, first)


def test_separated_endpoints_cannot_hide_partial_overlap_crossing():
    model, manager = _manager()
    first = np.zeros(manager.n_dof)
    last = first.copy()
    for node in range(1, 7):
        dof = model.mesh.dof_manager.get_node_dofs(node)[2]
        first[dof] = last[dof] = -0.045  # physical gap -.030 < -.020 budget
    for node in range(7, 11):
        dof = model.mesh.dof_manager.get_node_dofs(node)[0]
        first[dof], last[dof] = -2.0, 2.0
    assert np.isinf(manager._gap_lower(manager._positions(first)))
    assert np.isinf(manager._gap_lower(manager._positions(last)))
    assert manager._gap_lower(manager._positions(.5*(first+last))) < -manager.gap_tolerance
    assert not manager.swept_increment_admissible(first, last, 0.0, 1.0)
    assert not manager.swept_increment_admissible(last, first, 1.0, 0.0)
    fraction = manager.admissible_step_fraction(first, last)
    assert 0.0 < fraction < .5
    assert manager._swept_admissible(first, first + fraction*(last-first))


def test_partial_revision_is_explicit_and_interior_revision_unchanged():
    _, manager = _manager()
    settings = manager.restart_contract()["settings"]
    assert settings["partial_overlap_swept_certificate_revision"] == "affine_outward_endpoint_enclosures_v1"
    # Interior admission owns its separate existing contract. This checks
    # serialization only, without admitting this partial fixture as interior.
    manager.settings = replace(
        manager.settings, d1_interior_profile=True,
        d1_interior_coverage_tolerance_m2=1e-10,
        d1_interior_boundary_force_tolerance_n=1e-8)
    settings = manager.restart_contract()["settings"]
    assert "partial_overlap_swept_certificate_revision" not in settings
    assert settings["d1_swept_certificate_revision"] == "affine_union_outward_swept_search_v2"
