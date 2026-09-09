"""Static development-checkpoint checks; never rerun package/mechanics work."""

import hashlib
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def record():
    path = ROOT/'docs/reference_cases/ge_beam3_curved_p5_package_development_evidence.json'
    # Git source records use canonical UTF8/LF even on CRLF checkouts. External
    # artifact bytes below remain exact and are never normalized.
    raw = path.read_text(encoding='utf-8').encode('utf-8')
    value = json.loads(raw)
    assert raw == (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
    return value


def test_development_evidence_does_not_authorize_activation_or_release():
    evidence = record()
    assert evidence['disposition'] == 'DEVELOPMENT_PACKAGE_INTEGRATION_ONLY'
    assert not any(evidence[key] for key in ('production_qualified','activation_authorized','release_authorized'))
    assert evidence['source_regression']['passed'] == 97
    assert evidence['source_regression']['failed'] == 0
    assert evidence['scientific_hashes_identical_across_eol']
    source_map = ROOT/'docs/reference_cases/ge_beam3_curved_p5_package_source_map.json'
    assert hashlib.sha256(source_map.read_text(encoding='utf-8').encode('utf-8')).hexdigest() == evidence['source_map_sha256']
    assert evidence['installed_checks'][-1]['source_map_sha256'] == evidence['source_map_sha256']


def test_development_archive_bindings_are_complete_and_unambiguous():
    evidence = record(); files = evidence['archive_files']
    assert len(files) == len({item['path'] for item in files}) == 12
    for item in files:
        assert item['bytes'] > 0 and len(item['sha256']) == 64
    for label, check in zip(('lf-initial','crlf-checked'),evidence['installed_checks']):
        matched = [r for r in files if '\\'+label+'\\' in r['path']]
        assert len(matched) == 6
        wheel = next(r for r in matched if r['path'].endswith('.whl'))
        assert wheel['sha256'] == check['wheel_sha256'] and wheel['bytes'] == check['wheel_bytes']
        cycles = [r for r in matched if r['path'].endswith(('cycle-1.json','cycle-2.json'))]
        assert len(cycles) == 2
        assert all(r['sha256'] == check['result_sha256'] and r['bytes'] == check['result_bytes'] for r in cycles)


def test_preserved_archive_bytes_and_scientific_eol_equivalence():
    files = record()['archive_files']
    if not all(Path(r['path']).is_file() for r in files):
        pytest.skip('external development archive is not mounted; this is not an executed package gate')
    for item in files:
        raw = Path(item['path']).read_bytes()
        assert len(raw) == item['bytes'] and hashlib.sha256(raw).hexdigest() == item['sha256']
    cycles = [json.loads(Path(r['path']).read_bytes()) for r in files if r['path'].endswith('cycle-1.json')]
    for key in ('response_sha256','recovery_sha256','checkpoint_sha256','reference_spectrum_sha256',
                'current_operator_sha256','current_spectrum_sha256'):
        assert cycles[0][key] == cycles[1][key]
