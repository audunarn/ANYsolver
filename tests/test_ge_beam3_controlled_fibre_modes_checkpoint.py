"""Static bounded-control modal checkpoint; no qualification authority."""
import hashlib
from pathlib import Path
import pytest
from test_ge_beam3_kinematic_fibre_checkpoint import parse

ROOT = Path(__file__).resolve().parents[1]


def record():
    raw = (ROOT/'docs/reference_cases/ge_beam3_controlled_fibre_modes_development_evidence.json').read_bytes()
    return parse(raw.replace(b'\r\n', b'\n'))


def test_private_spectral_development_is_not_activation_or_critical_load():
    value = record()
    assert value['status'] == 'DEVELOPMENT_NATIVE_CONTROL_HISTORY_SIGNED_SPECTRA_PASS'
    assert value['independent_review'] == 'PENDING'
    for key in ('qualification_pass', 'production_qualified', 'public_routing_changed',
                'state_advanced', 'checkpoint_converted', 'continuation_constraint_retained',
                'buckling_factor_authorized', 'certified_intervals'):
        assert value[key] is False
    assert value['deterministic_cycle_pair_completed'] is True
    assert value['resource_requests_consumed'] == []
    assert value['verified_scope']['root_width'] == '1e-10'
    assert value['verified_scope']['residual_gate'] == '1e-11'


@pytest.mark.parametrize('index', range(5))
def test_final_tested_source_is_frozen(index):
    row = record()['sources'][index]
    raw = (ROOT/row['path']).read_bytes().replace(b'\r\n', b'\n')
    assert len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256']


def test_failed_sign_resolution_and_final_cycles_have_separate_inventories():
    value = record()
    assert [(r['label'], r['tests'], r['failures'], r['errors'], r['skipped'])
            for r in value['inventories']] == [
        ('initial', 17, 1, 0, 0), ('exact-unit', 7, 0, 0, 0),
        ('cycle-a', 24, 0, 0, 0), ('cycle-b', 24, 0, 0, 0)]
    assert value['incident']['status'] == 'PRESERVED_FAILED_ARCH_SHIFTED_SIGN'
    assert value['incident']['source'] == 'source-variants/initial/control-modes.py'
    assert value['archive']['content_files'] == 35
    assert value['archive']['content_bytes'] == 1832335
    assert value['archive']['manifest_sha256'] == '3824ba8ea1edc27b8b8a54025407f7d9d4dc340d96cd86faad45761b1250453b'


def test_nine_pairs_and_signed_arch_roots_are_preserved():
    value = record()
    pairs = value['deterministic_pairs']
    assert len(pairs) == 9 == value['verified_scope']['deterministic_json_pairs']
    assert len({row['path'] for row in pairs}) == 9
    for row in pairs:
        assert row['bytes'] > 0 and len(row['sha256']) == 64
        assert set(row['sha256']) <= set('0123456789abcdef')
    early, descending = value['arch_spectra']
    assert early['negative_count'] == 0 and descending['negative_count'] == 2
    assert all(float(x) > 0 for x in early['eigenvalues'])
    assert sum(float(x) < 0 for x in descending['eigenvalues']) == 2
    assert max(float(row['ritz_error']) for row in (early, descending)) <= 1e-11
