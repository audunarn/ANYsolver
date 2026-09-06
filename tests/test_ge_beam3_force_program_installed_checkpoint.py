"""Static package evidence checks; no wheel rebuild or mechanics rerun."""

import hashlib
import json
from pathlib import Path

import pytest

from docs.reference_cases.ge_beam3_native_load_source_map import canonical


ROOT = Path(__file__).resolve().parents[1]
RECORD = 'docs/reference_cases/ge_beam3_force_program_installed_evidence.json'


def source(path): return (ROOT/path).read_text(encoding='utf-8').encode('utf-8')


def validate():
    raw = source(RECORD); record = json.loads(raw)
    assert canonical(record) == raw
    for path,expected in record['code_bindings'].items():
        data = source(path)
        assert dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest()) == expected
    return record


def test_installed_scope_and_bound_archive_extent():
    record = validate()
    assert record['candidate_commit'] == 'eec5f5f4032cfddb82f9d8b6ecdef1d291d5d2ce'
    assert record['installed_test']['passed'] == 1 and record['installed_test']['failed'] == 0
    assert record['canonical_source_bindings_verified'] == 52
    assert record['archive_file_count'] == len(record['archive_files']) == 18
    assert record['archive_total_bytes'] == sum(row['bytes'] for row in record['archive_files']) == 1497799
    assert len({row['path'] for row in record['archive_files']}) == 18


def test_two_process_records_and_checkpoints_match():
    record = validate(); files = {row['path']:row for row in record['archive_files']}
    assert record['fresh_process_count'] == 2
    for name in ('result.json','accepted-checkpoint.json'):
        left,right = files['cycle-1/'+name],files['cycle-2/'+name]
        assert left['bytes'] == right['bytes'] and left['sha256'] == right['sha256']
    assert record['scientific_records_byte_identical'] and record['accepted_checkpoints_byte_identical']


def test_installed_evidence_does_not_authorize_publication_or_qualification():
    record = validate()
    assert record['independent_review_status'] == 'PENDING' and record['remaining']
    assert record['formal_resource_requests'] == []
    assert not any(record[key] for key in ('production_qualified','public_driver_authorized',
        'mechanics_changed','defaults_changed','publication_authorized','version_changed',
        'source_runtime_comparison_claimed'))
    assert record['dependency_usage'] == 'ARTIFACT_IDENTITIES_ONLY_NO_REQUEST_OR_AUTHORITY_REUSE'


@pytest.mark.parametrize('path',[
    'docs/reference_cases/ge_beam3_force_program_installed_smoke.py',
    'tests/test_ge_beam3_force_program_installed.py',
])
def test_changed_installed_check_source_fails_binding(monkeypatch,path):
    original = source
    monkeypatch.setattr(__import__(__name__),'source',
        lambda item: original(item)+(b'\n# mutation\n' if item == path else b''))
    with pytest.raises(AssertionError): validate()
