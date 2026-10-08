"""Exact envelope inventory and scalar action controls, no qualification run."""
from dataclasses import FrozenInstanceError
from fractions import Fraction as F
import json
from types import SimpleNamespace

import numpy as np
import pytest

from scripts import r8_bl5_projected_envelope_norm_dev as norm
from scripts.r8_bl5_projected_auxiliary_norm_dev import integrated_p1


def test_exact_21_case_registry_and_actual_counts():
    cases = norm.all_cases()
    assert len(cases) == 21 and len({case.fixture_case for case in cases}) == 21
    assert norm.validate_campaign(cases) == cases
    ratios = (F(1, 8), F(1, 4), F(1, 2), F(1), F(2), F(4), F(8))
    assert tuple((case.nx, case.member_ratio) for case in cases) == tuple(
        (nx, ratio) for nx in (16, 32, 64) for ratio in ratios)
    expected = {
        16: ((4, 1, 517, 563), (8, 2, 553, 645), (16, 4, 625, 809),
             (32, 4, 769, 1097), (64, 4, 1057, 1673), (128, 4, 1633, 2825), (256, 4, 2785, 5129)),
        32: ((8, 2, 1801, 1893), (16, 4, 1873, 2057), (32, 8, 2017, 2385),
             (64, 8, 2305, 2961), (128, 8, 2881, 4113), (256, 8, 4033, 6417), (512, 8, 6337, 11025)),
        64: ((16, 4, 6673, 6857), (32, 8, 6817, 7185), (64, 16, 7105, 7841),
             (128, 16, 7681, 8993), (256, 16, 8833, 11297), (512, 16, 11137, 15905), (1024, 16, 15745, 25121)),
    }
    for case in cases:
        halfcells, supports, physical_free, kkt = expected[case.nx][ratios.index(case.member_ratio)]
        assert case.ny == case.nx//4
        assert (case.halfcells, case.supports) == (halfcells, supports)
        assert case.span == 4*max(1, halfcells//case.nx)
        assert case.fixture == dict(nx=case.nx, ny=case.ny, halfcells=halfcells, supports=supports)
        counts = case.counts
        assert counts['shell_nodes'] == {16: 85, 32: 297, 64: 1105}[case.nx]
        assert counts['beam_nodes'] == halfcells+1
        assert counts['physical_dofs'] == 6*(counts['shell_nodes']+counts['beam_nodes'])
        assert counts['members'] == halfcells//2
        assert counts['retained_cell_rotations'] == 3*halfcells
        assert counts['retained_resultants'] == 9*halfcells
        assert counts['retained_dofs'] == 12*halfcells
        assert counts['full_q'] == counts['physical_dofs']+12*halfcells
        assert counts['multipliers'] == 10*supports
        assert counts['physical_free'] == physical_free
        assert counts['kernel'] == physical_free-10*supports
        assert case.fixed_count == {16: 35, 32: 59, 64: 107}[case.nx]
        assert case.supported_kkt_count == kkt
        assert norm.case_from_id(case.fixture_case) == case


@pytest.mark.parametrize('case', norm.all_cases(), ids=lambda case: case.fixture_case)
def test_exact_quarters_projection_mass_and_independent_signed_action(case):
    p = norm.projection(case)
    expected = norm.density_mass_diagonal(case)
    assert p.shape == (case.halfcells, 2*case.supports)
    assert np.linalg.matrix_rank(p) == 2*case.supports
    np.testing.assert_allclose(p.T@p/case.halfcells, np.diag(expected), rtol=0., atol=1e-15)
    witness = norm.quarter_witness(case)
    interval_span = F(case.nx, case.supports)
    assert witness == tuple((int(j*interval_span+interval_span/4),
                             int(j*interval_span+3*interval_span/4)) for j in range(case.supports))
    exact = norm.exact_boundary(case)
    xs = np.linspace(0., 1., case.nx+1)
    knots = np.linspace(0., 1., case.halfcells+1)
    boundary = integrated_p1(xs, p, knots)
    np.testing.assert_allclose(boundary, exact, rtol=0., atol=1e-13)
    cells = norm.cell_action(case)
    np.testing.assert_allclose(cells@p, exact, rtol=0., atol=1e-13)
    assert cells.shape == (case.nx+1, case.halfcells)
    assert np.linalg.matrix_rank(np.c_[exact[1:], exact[1:, 0]]) == 2*case.supports
    for support, (left, right) in enumerate(witness):
        assert exact[left, 2*support+1] < 0.
        assert exact[right, 2*support+1] > 0.
        left_mean = F(2*(support*case.span)+1, 2*case.halfcells)
        assert p[support*case.span, 2*support+1] == float(
            2*(left_mean-F(support, case.supports))*case.supports-1)


def test_cases_and_returned_arrays_have_no_mutable_shared_case_state():
    a, b = norm.case_from_id('ns16_b1_8'), norm.case_from_id('ns64_b8')
    with pytest.raises(FrozenInstanceError):
        a.nx = 64
    with pytest.raises(TypeError):
        norm.CRITERIA['reference_error'] = 1.
    fixture, counts = a.fixture, a.counts
    fixture['nx'] = 99
    counts['full_q'] = 0
    assert a.fixture['nx'] == 16 and a.counts['full_q'] > 0
    first = norm.projection(a)
    saved = first.copy()
    other = norm.projection(b)
    first[:] = 123.
    np.testing.assert_array_equal(norm.projection(a), saved)
    assert other.shape == (1024, 32)
    assert not np.shares_memory(first, other)
    assert norm.projection(a).shape == (4, 2)


@pytest.mark.parametrize('nx,ratio', ((8, F(1)), (16., F(1)), (True, F(1)),
                                    (16, .125), (16, 1), (16, F(3)), (16, True)))
def test_invalid_or_inexact_case_inputs(nx, ratio):
    with pytest.raises(ValueError):
        norm.EnvelopeCase(nx, ratio)


def test_invalid_duplicate_reordered_or_mutable_campaign_inputs():
    cases = norm.all_cases()
    for invalid in (cases[::-1], cases[:-1], (cases[0],)*21, list(cases)):
        with pytest.raises(ValueError):
            norm.validate_campaign(invalid)
    for invalid in ('ns16_b3', 'whole_half', 16, None):
        with pytest.raises(ValueError):
            norm.case_from_id(invalid)
    for invalid in (None, {'nx': 16}, cases):
        with pytest.raises(ValueError):
            norm.projection(invalid)


def test_fixed_criteria_and_source_binding_are_explicit():
    case = norm.case_from_id('ns16_b1_2')
    assert dict(norm.CRITERIA) == dict(reference_error=1e-3, inverse_eigen_symmetry=1e-10,
        condition_budget=1e4, arithmetic_beta_margin=1e-6, variational_ceiling=(1+1e-6)**2)
    assert norm.MODES == (4096, 8192, 16384)
    assert norm.helpers(case) == dict(norm.EXPECTED_HELPERS)
    assert norm.IDENTITY == 'BL5_PROJECTED_WHOLE_MEMBER_ENVELOPE_DEV_V1'


def test_existing_output_pair_is_rejected_without_replacement(tmp_path):
    output = tmp_path/'registration.json'
    output.write_text('preserved', encoding='utf-8')
    with pytest.raises(ValueError):
        norm.register(norm.case_from_id('ns16_b1_2'), output)
    assert output.read_text(encoding='utf-8') == 'preserved'
    output.unlink()
    output.with_suffix('.npz').write_bytes(b'preserved-array')
    with pytest.raises(ValueError):
        norm.register(norm.case_from_id('ns16_b1_2'), output)
    assert output.with_suffix('.npz').read_bytes() == b'preserved-array'


@pytest.mark.parametrize('failure_type', (RuntimeError, KeyboardInterrupt))
def test_preparation_failure_keeps_raw_and_propagates_primary(tmp_path, monkeypatch, failure_type):
    # Deliberately inject a pre-inverse failure; this is no scalar solve/configuration claim.
    failure = failure_type('injected before scalar assembly')
    monkeypatch.setattr(norm, 'sys', SimpleNamespace(modules={}))
    monkeypatch.setattr(norm, 'threadpool_info', lambda: [dict(num_threads=1)])
    def fail(*args, **kwargs):
        raise failure
    monkeypatch.setattr(norm, 'shell_scalar', fail)
    # The real helper binding is checked separately; the replaced callable here
    # serves only to exercise failure recording without an inverse operation.
    monkeypatch.setattr(norm, 'helpers', lambda case: dict(norm.EXPECTED_HELPERS))
    output = tmp_path/'failure.json'
    with pytest.raises(failure_type) as caught:
        norm.register(norm.case_from_id('ns16_b1_8'), output)
    assert caught.value is failure
    record = json.loads(output.read_text(encoding='utf-8'))
    assert record['status'] == 'FAILED_ENVELOPE_DEVELOPMENT_PREPARATION'
    assert record['failure']['type'] == failure_type.__name__
    with np.load(output.with_suffix('.npz'), allow_pickle=False) as arrays:
        np.testing.assert_array_equal(arrays['projection'], norm.projection(norm.case_from_id('ns16_b1_8')))
        assert arrays['knots'].shape == (5,)
    assert record['arrays_sha256'] == norm.sha(output.with_suffix('.npz'))


def test_changed_helper_identity_is_rejected(monkeypatch):
    expected = dict(norm.EXPECTED_HELPERS)
    expected['r8_bl5_projected_modal_envelope_dev.py'] = '0'*64
    monkeypatch.setattr(norm, 'EXPECTED_HELPERS', expected)
    with pytest.raises(ValueError, match='helper identity changed'):
        norm.helpers(norm.case_from_id('ns16_b1_2'))
