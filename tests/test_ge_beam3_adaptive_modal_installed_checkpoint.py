"""Static package binding; no wheel rebuild or mechanics execution."""

import hashlib
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def source(path): return (ROOT/path).read_text(encoding='utf-8').encode('utf-8')


def validate():
    raw = source('docs/reference_cases/ge_beam3_adaptive_modal_installed_evidence.json')
    record = json.loads(raw)
    assert (json.dumps(record, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode('ascii') == raw
    for path, expected in record['code_bindings'].items():
        data = source(path)
        assert dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest()) == expected
    for path, expected in record['preserved_records'].items():
        assert hashlib.sha256(source(path)).hexdigest() == expected
    return record


def test_installed_scope_and_retained_checkpoint_contracts():
    record = validate()
    assert record['candidate_commit'] == 'd73b86bb3a1cc688c1776dd3ebae7bf74ff1d260'
    assert record['installed_test']['passed'] == 1 and record['installed_test']['failed'] == 0
    assert record['canonical_source_bindings_verified'] == 60
    adaptive, modal = record['controls']['adaptive'], record['controls']['modal']
    assert (adaptive['accepted_steps'], adaptive['attempts'], adaptive['cutbacks']) == (8, 15, 7)
    assert adaptive['restart_exact'] and adaptive['resealed_attempt_mutation_rejected']
    assert modal['restart_exact'] and modal['accepted_history_preserved'] and modal['load_parameter_mismatch_rejected']
    assert (modal['retained_coordinates'], modal['physical_mode_columns']) == (24, 12)


def test_all_fresh_outputs_and_archive_hashes_match():
    record = validate(); rows = {row['path']: row for row in record['archive_files']}
    assert len(rows) == record['archive_file_count'] == 22
    assert sum(row['bytes'] for row in rows.values()) == record['archive_total_bytes']
    for name in ('result.json', 'adaptive-checkpoint.json', 'modal-checkpoint.json', 'modal-diagnostic.json'):
        a, b = rows['cycle-1/'+name], rows['cycle-2/'+name]
        assert a['bytes'] == b['bytes'] and a['sha256'] == b['sha256']


def test_package_check_is_not_qualification_or_publication():
    record = validate()
    assert record['independent_review_status'] == 'PENDING' and record['remaining']
    assert record['installed_imports_isolated'] and record['research_imports_forbidden']
    assert record['formal_resource_requests'] == []
    assert record['dependency_usage'] == 'ARTIFACT_IDENTITIES_ONLY_NO_REQUEST_OR_AUTHORITY_REUSE'
    assert not any(record[k] for k in ('production_qualified', 'public_driver_authorized', 'mechanics_changed',
        'defaults_changed', 'publication_authorized', 'version_changed', 'source_runtime_comparison_claimed', 'buckling_factor_qualified'))


@pytest.mark.parametrize('path', ['docs/reference_cases/ge_beam3_adaptive_modal_installed_smoke.py',
    'tests/test_ge_beam3_adaptive_modal_installed.py'])
def test_package_harness_mutation_is_rejected(monkeypatch, path):
    original = source
    monkeypatch.setattr(__import__(__name__), 'source',
        lambda item: original(item)+(b'\n# mutation\n' if item == path else b''))
    with pytest.raises(AssertionError): validate()
