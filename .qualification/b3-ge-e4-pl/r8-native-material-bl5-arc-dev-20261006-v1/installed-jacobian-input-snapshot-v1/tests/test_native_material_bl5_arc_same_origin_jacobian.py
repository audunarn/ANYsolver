"""SOURCE_ONLY_UNRUN: common-origin full native BL5 arc directional oracle.

One mixed/P1 loaded fixture and one uncommitted arc candidate. This is neither
a limit-point test nor authority to run a new numerical campaign.
"""
import json
import hashlib
import os
from pathlib import Path
import numpy as np
import pytest
from scipy import sparse

from anysolver import stiffened_shell as ss
from anysolver._stiffened_shell_arc_trial import correct, path_row
from anysolver._stiffened_shell_ge_finite_experimental import _fibre_recovery
from anysolver._stiffened_shell_beam_history import arrays as beam_arrays
from anysolver._stiffened_shell_q4_material_event import _origin_values
from anysolver.plasticity import _jit_consistency_residual_scalar
from examples.stiffened_shell_native_fibre_bl5_mixed_j2_displacement import definition
from examples.stiffened_shell_native_fibre_bl5_displacement import ACTIONS, CONTROL, OPTIONS, TARGETS
from examples.stiffened_shell_native_material_bl5_arc import arc_control


def _loaded_seed(owner, tmp_path):
    """Optional authentic gen3 input; strict restore remains the admission gate."""
    source = os.environ.get('ANY_NATIVE_BL5_ARC_JACOBIAN_FIXTURE')
    expected = os.environ.get('ANY_NATIVE_BL5_ARC_JACOBIAN_FIXTURE_SHA256')
    assert (source is None) == (expected is None), 'fixture path and expected SHA256 must be supplied together'
    if source is None:
        owner.solve(ACTIONS, (.001,), **OPTIONS)
        owner.solve(ACTIONS, TARGETS[:2], displacement_control=CONTROL, **OPTIONS)
        provenance = dict(source='fresh loaded fixture')
    else:
        # Root adopted this exact existing matched mixed/P1 checkpoint. Neither
        # an arbitrary caller digest nor a fabricated replacement is admitted.
        assert expected == '70b162593ee8939aea0755fa20a5d84956da58a435879518aa5e26ad0573f8dc'
        raw = Path(source).read_bytes()
        assert len(raw) == 46984 and hashlib.sha256(raw).hexdigest() == expected
        copied = tmp_path/'loaded-seed-fixture.bin'
        copied.write_bytes(raw)
        owned = copied.read_bytes()
        assert owned == raw and hashlib.sha256(owned).hexdigest() == expected
        loaded = owner.restore(owned)
        assert loaded.status == 'accepted_prefix' and loaded.generation == 3
        assert loaded.target == TARGETS[1]
        assert owner.checkpoint() == owned, 'strict model/pose/material restore changed bytes'
        provenance = dict(source=str(Path(source)), sha256=expected, bytes=len(raw))
    loaded = owner.recover()
    assert loaded.status == 'accepted_prefix' and loaded.generation == 3
    assert loaded.target == TARGETS[1]
    return loaded, provenance


def _inventory(owner, driver, state, shell, beam, evaluation):
    """Read actual material recovery and fixed-origin shell switch diagnostics.

    The existing scalar consistency kernel at zero multiplier supplies the
    elastic-trial drive; this does not reconstruct an equilibrium or tangent.
    Its returned-stress arithmetic differs slightly from the initial batch
    switch arithmetic, so require agreement with actual candidate alpha growth.
    Exact switch equality or a hardening knot fails; it is never skipped.
    """
    labels = []
    margins = []
    knots = []
    captures = driver._q4_boundary_trial
    assert captures[0] is state and captures[1] is shell
    assert len(captures[3]) == len(owner._shell_parts)
    for part, origin, candidate, (slots, capture) in zip(
            owner._shell_parts, shell, evaluation[4], captures[3], strict=True):
        eid, element, actual_slots, _ = part
        assert tuple(actual_slots) == slots
        assert capture.origin is origin
        assert capture.origin_values == _origin_values(origin)
        material = owner._shell_model.get_material(element.material_name)
        curve = material.hardening_curve
        parameters = tuple(float(getattr(curve, name)) for name in (
            'sigma_prop', 'sigma_yield', 'sigma_yield_2', 'eps_p_y1',
            'eps_p_y2', 'K', 'n', '_power_offset'))
        alpha = np.asarray(candidate['alpha']).reshape(-1)
        previous = np.asarray(origin['alpha']).reshape(-1)
        stress = (np.asarray(capture.strain)-np.asarray(origin['plastic_strain']).reshape(-1, 3)) @ np.asarray(capture.elastic_matrix).T
        family = 'S3' if len(slots) == 18 else 'Q4'
        for station, (sigma, old, new) in enumerate(zip(stress, previous, alpha, strict=True)):
            value, flow = _jit_consistency_residual_scalar(
                0., sigma[0]+sigma[1], sigma[0]-sigma[1], sigma[2],
                float(old), material.elastic_modulus/(3*(1-material.poisson_ratio)),
                material.elastic_modulus/(2*(1+material.poisson_ratio)), *parameters)
            margin = float(value-capture.tolerance*max(flow*flow, 1.))
            assert np.isfinite(margin) and margin != 0., 'shell switch: no smooth-branch claim'
            plastic = bool(new > old)
            assert plastic == (margin > 0.), 'shell scalar/candidate branch disagreement'
            if not plastic:
                assert new == old
            band = int(np.searchsorted((curve.eps_p_y1, curve.eps_p_y2), new))
            distances = (float(new-curve.eps_p_y1), float(new-curve.eps_p_y2))
            assert all(value != 0. for value in distances), 'shell hardening knot'
            labels.append((family, int(eid), station, 'PLASTIC' if plastic else 'ELASTIC', band))
            margins.append(margin)
            knots.extend(distances)
    fibres, _ = _fibre_recovery(owner, state, beam, evaluation[5])
    for station in fibres:
        for fibre in station.fibres:
            assert fibre.branch not in ('YIELD_BOUNDARY', 'HARDENING_KNOT')
            assert all(np.isfinite(fibre.algorithmic_modulus))
            labels.append(('FIBRE', station.element_id, station.cell, station.station,
                           fibre.fibre_id, fibre.branch))
    generalized = driver._generalized_records(state, beam, evaluation[5], include_native=True)
    for member in generalized:
        for station in member.stations:
            assert station.branch in ('ELASTIC', 'PLASTIC'), 'generalized yield boundary'
            labels.append(('GENERALIZED', member.element_id, station.cell, station.station, station.branch))
    return tuple(labels), np.asarray(margins), np.asarray(knots)


def test_common_accepted_origins_full_arc_residual_direction(request, tmp_path):
    owner = ss.create_analysis(definition=definition('mixed', 'biaxial', 'mixed', 'continuous_p1_coarse'))
    request.addfinalizer(owner.close)
    loaded, fixture_provenance = _loaded_seed(owner, tmp_path)
    assert any(np.any(row.alpha > 0.) for row in loaded.shell_s3_material)
    driver = owner._finite_driver
    saved = owner.checkpoint()
    parent = driver._state
    shell, beam = driver._shell_origins, driver._beam_origins
    histories = dict(beam_arrays(owner._beam_parts, beam, 'beam_origin'))
    assert np.any(histories['beam_origin_fibres'][:, 2:] > 0.)
    control = arc_control(owner)
    trial = correct(driver, load_direction=driver._load(ACTIONS), metric=control.metric,
        radius=control.radius, predictor_dof=CONTROL.dof(owner), orientation=control.orientation,
        max_iterations=control.max_iterations, max_backtracks=control.max_backtracks)
    assert trial.predecessor_state is parent
    assert trial.shell_predecessor is shell and trial.beam_predecessor is beam
    state = trial.state
    normal = (trial.normal_translations, trial.normal_spins)
    n = len(state.q)
    size = n+len(state.multipliers)
    nodal = owner._shell_count+6*len(owner._beam_ids)
    direction = np.zeros(size)
    # Explicit component units: translation m, rotation rad, retained force N
    # and moment N*m; multiplier units follow the existing BL5 row work law.
    for index in owner._free:
        if index < nodal:
            direction[index] = np.sin(index+1.)*(1e-6 if index % 6 < 3 else 1e-3)
    for member in range(len(owner._beam_parts)):
        start = nodal+24*member
        direction[start:start+6] = 1e-3*np.sin(np.arange(6)+member+1.)
        direction[start+6:start+24] = np.sin(np.arange(18)+member+1.)
    direction[n:] = np.cos(np.arange(size-n)+1.)
    amplitude_direction = .003
    load_column = np.r_[trial.load_direction, np.zeros(size-n)]

    def evaluate(point, amplitude):
        evaluation = driver._assemble(point, 0., shell, beam,
            applied_load=trial.base_load+amplitude*trial.load_direction)
        inventory = _inventory(owner, driver, point, shell, beam, evaluation)
        value, row = path_row(driver, point, parent, control.metric, normal)
        return np.r_[evaluation[0], value-trial.radius], evaluation[1], row, inventory

    residual, matrix, row, center = evaluate(state, trial.amplitude)
    assert matrix.shape == (size, size)
    assert any(label[-1] == 'PLASTIC' or (label[0] in ('Q4', 'S3') and label[-2] == 'PLASTIC')
               for label in center[0]), 'chosen arc trial has no active plastic material branch'
    np.testing.assert_array_equal(row[nodal:], np.zeros(size-nodal))
    border = sparse.bmat([[matrix, sparse.csc_matrix(-load_column[:, None])],
                          [sparse.csc_matrix(row[None, :]), sparse.csc_matrix((1, 1))]], format='csc')
    expected = border @ np.r_[direction, amplitude_direction]
    material_expected = matrix @ direction
    errors = []
    inventories = []
    for h in (1e-5, 1e-6):
        plus_state = driver._advance(state, direction, h)
        minus_state = driver._advance(state, direction, -h)
        assert np.any(plus_state.cells != state.cells) and np.any(plus_state.resultants != state.resultants)
        assert np.any(plus_state.frames != state.frames) and np.any(plus_state.multipliers != state.multipliers)
        plus, _, _, upper = evaluate(plus_state, trial.amplitude+h*amplitude_direction)
        minus, _, _, lower = evaluate(minus_state, trial.amplitude-h*amplitude_direction)
        assert upper[0] == center[0] == lower[0], 'central stencil changes actual material branch'
        for slot in (1, 2):
            movement = np.maximum(abs(upper[slot]-center[slot]), abs(lower[slot]-center[slot]))
            assert np.all(abs(center[slot]) > movement), 'stencil reaches shell switch/knot margin'
        difference = (plus-minus)/(2*h)
        equilibrium_error = float(np.linalg.norm(difference[:-1]-expected[:-1])/max(np.linalg.norm(expected[:-1]), 1.))
        # Removing the exact dead-load column prevents it masking J-direction error.
        material_error = float(np.linalg.norm(difference[:-1]+load_column*amplitude_direction-material_expected)/max(np.linalg.norm(material_expected), 1.))
        assert equilibrium_error <= 1e-5 and material_error <= 1e-5
        assert difference[-1] == pytest.approx(float(row @ direction), rel=1e-8, abs=1e-10)
        errors.append(dict(h=h, equilibrium=equilibrium_error, material=material_error,
                          path=float(abs(difference[-1]-expected[-1]))))
        inventories.append(dict(h=h, plus=upper[0], minus=lower[0],
                                shell_switch_margins=[upper[1].tolist(), lower[1].tolist()]))
    assert owner._finite_driver is driver and driver._state is parent
    assert driver._shell_origins is shell and driver._beam_origins is beam
    assert owner.checkpoint() == saved
    (tmp_path/'same-origin-arc-jacobian.json').write_text(json.dumps(dict(
        status='EXECUTED_DEVELOPMENT_DIRECTIONAL_CHECK', errors=errors,
        fixture=fixture_provenance,
        center_branches=center[0], stencil=inventories, direction=direction.tolist(),
        amplitude_direction=amplitude_direction, shape=list(border.shape),
        material_criterion=1e-5, norm='all-row unweighted L2; denominator max(norm(expected),1)',
        path_criteria=dict(relative=1e-8, absolute=1e-10),
        production_qualified=False), indent=2))
