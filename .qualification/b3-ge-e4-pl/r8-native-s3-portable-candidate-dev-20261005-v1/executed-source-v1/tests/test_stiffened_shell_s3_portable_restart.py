"""Opt-in S3 mechanical certificates; strict archive defaults remain intact."""
from pathlib import Path
from dataclasses import replace
import numpy as np
import pytest
from anysolver import stiffened_shell as ss
from anysolver.control import CancellationToken, SolveCancelled
from anysolver._stiffened_shell_s3_restart_certificate import POLICY, UncertifiedS3Restart, material, _flow, _Bound
from anysolver._stiffened_shell_displacement_adaptive import decode, encode
from anysolver._stiffened_shell_displacement_checkpoint import decode_snapshot, encode_snapshot
from examples.stiffened_shell_coupled_s3_adaptive_history import definition, DIRECTION, CONTROL
from test_stiffened_shell_native_point_displacement import owner

RAW = Path(__file__).parent/'data/native_s3_fibre_history/unloaded-v1.bin'


def test_portable_old_seed_preserves_bytes_and_reports_margin(request):
    analysis = owner(request, definition())
    raw = RAW.read_bytes()
    result = analysis.restore(raw, consistency_policy=POLICY)
    assert analysis.checkpoint() == raw
    assert result.restart_consistency_policy == POLICY
    assert result.free_equilibrium_ratio <= result.restart_equilibrium_upper <= 1e-8
    assert result.constraint_max <= 1e-9
    accepted = analysis._finite_driver._shell_origins
    parent = analysis._finite_driver._shell_predecessors
    assert any(np.any(state['alpha']) for state in accepted)
    for a, p in zip(accepted, parent):
        np.testing.assert_array_equal(a['alpha'], p['alpha'])
        np.testing.assert_array_equal(a['plastic_strain'], p['plastic_strain'])
    fresh = owner(request, definition())
    token = CancellationToken();token.cancel('before portable publication')
    with pytest.raises(SolveCancelled):fresh.restore(raw, consistency_policy=POLICY, cancellation_token=token)
    assert fresh._finite_driver is None and fresh._generation == 0
    assert not hasattr(fresh, '_s3_restart_policy')


@pytest.mark.parametrize('family', ('accepted', 'predecessor'))
def test_portable_checksum_valid_changed_physical_association_is_atomic(request, family):
    analysis = owner(request, definition())
    context, inner = decode(analysis, RAW.read_bytes())
    metadata, arrays = decode_snapshot(analysis, inner)
    arrays = {name:np.array(value, copy=True) if isinstance(value, np.ndarray) else value
              for name, value in arrays.items()}
    name = 'q' if family == 'accepted' else 'shell_origin_q'
    free = next(int(slot) for slot in analysis._free if slot < analysis._shell_count and slot%6 < 3)
    arrays[name][free] += 1e-4
    corrupted_inner = encode_snapshot(analysis, generation=metadata['generation'],
        seed_generation=metadata['seed_generation'], seed_sha256=metadata['seed_sha256'],
        control_dof=metadata['control_dof'], arrays=arrays, chart_events=metadata.get('chart_events', 0))
    corrupted = encode(analysis._identity, context, corrupted_inner, native=True)
    with pytest.raises(ValueError):analysis.restore(corrupted, consistency_policy=POLICY)
    assert analysis._finite_driver is None and analysis._generation == 0
    assert not hasattr(analysis, '_s3_restart_policy')


def test_portable_scalar_yielded_update_and_corner_rejection(request):
    analysis = owner(request, definition())
    analysis.restore(RAW.read_bytes(), consistency_policy=POLICY)
    element = analysis._shell_parts[0][1]
    parent = analysis._finite_driver._shell_predecessors[0]
    model = analysis._shell_model
    law = model.get_material(element.material_name)
    local = np.asarray(parent['committed_constitutive_u'])*1.1
    _, _, candidate = element.compute_nonlinear_response(model.mesh, law, local, parent, 3, True)
    assert np.any(candidate['alpha'] > parent['alpha'])
    assert len(material(model, element, parent, candidate, np.zeros(18))) == 18
    with pytest.raises(UncertifiedS3Restart, match='hardening corner'):
        _flow(_Bound(float(law.hardening_curve.eps_p_y1)*.99,
                     float(law.hardening_curve.eps_p_y1)*1.01), law.hardening_curve)
