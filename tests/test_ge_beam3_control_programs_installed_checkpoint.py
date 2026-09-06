"""Static installed-control receipt checks; never rebuild or rerun mechanics."""

import ast
import hashlib
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
RECORD = 'docs/reference_cases/ge_beam3_control_programs_installed_evidence.json'


def source(path):
    return (ROOT/path).read_text(encoding='utf-8').encode('utf-8')


def validate():
    raw = source(RECORD)
    record = json.loads(raw)
    assert (json.dumps(record, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode('ascii') == raw
    for path, expected in record['code_bindings'].items():
        data = source(path)
        assert dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest()) == expected
    for path, expected in record['preserved_records'].items():
        assert hashlib.sha256(source(path)).hexdigest() == expected
    return record


def test_installed_control_scope_and_bound_inputs():
    record = validate()
    assert record['candidate_commit'] == 'f7c65a157bafc37ee9bd6cefbceff151710a1c62'
    assert record['candidate_tree'] == 'f159596e6789b803eb6da26b87d0ca833c05f108'
    assert record['installed_test']['passed'] == 1 and record['installed_test']['failed'] == 0
    assert record['canonical_source_bindings_verified'] == 56
    assert record['installed_imports_isolated'] and record['research_imports_forbidden']


def test_two_control_records_and_capsules_are_identical():
    record = validate(); files = {row['path']: row for row in record['archive_files']}
    assert record['fresh_process_count'] == 2
    for name in ('result.json', 'displacement-checkpoint.json', 'arc-checkpoint.json'):
        left, right = files['corrected/cycle-1/'+name], files['corrected/cycle-2/'+name]
        assert left['bytes'] == right['bytes'] and left['sha256'] == right['sha256']
    assert record['scientific_records_byte_identical'] and record['accepted_checkpoints_byte_identical']
    assert record['cancellation_both_sides_of_commit_checked'] and record['resealed_reaction_mutation_rejected']


def test_failure_is_preserved_and_not_counted_as_accepted():
    record = validate()
    assert record['development_incidents'][0]['classification'] == 'UNFROZEN_INSTALLED_FIXTURE_SECTION_OWNERSHIP'
    assert record['development_incidents'][0]['failed'] == 1
    files = {row['path']: row for row in record['archive_files']}
    assert files['failed/cycle-1.stderr']['bytes'] > 0
    assert 'failed/cycle-1/result.json' not in files
    assert 'failed/receipt.json' not in files
    assert record['archive_file_count'] == len(files)
    assert record['archive_total_bytes'] == sum(row['bytes'] for row in files.values())
    assert all(row['bytes'] >= 0 and len(row['sha256']) == 64 for row in files.values())


def test_no_qualification_release_or_cross_runtime_claim():
    record = validate()
    assert record['independent_review_status'] == 'PENDING' and record['remaining']
    assert record['formal_resource_requests'] == []
    assert not any(record[key] for key in ('production_qualified', 'public_driver_authorized',
        'mechanics_changed', 'defaults_changed', 'publication_authorized', 'version_changed',
        'source_runtime_comparison_claimed'))
    assert record['dependency_usage'] == 'ARTIFACT_IDENTITIES_ONLY_NO_REQUEST_OR_AUTHORITY_REUSE'


@pytest.mark.parametrize('path', [
    'docs/reference_cases/ge_beam3_control_programs_installed_smoke.py',
    'tests/test_ge_beam3_control_programs_installed.py',
])
def test_changed_package_harness_is_rejected(monkeypatch, path):
    original = source
    monkeypatch.setattr(__import__(__name__), 'source',
        lambda item: original(item)+(b'\n# mutation\n' if item == path else b''))
    with pytest.raises(AssertionError): validate()


def test_smoke_has_no_repository_fixture_imports():
    tree = ast.parse(source('docs/reference_cases/ge_beam3_control_programs_installed_smoke.py'))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import): names = [item.name for item in node.names]
        elif isinstance(node, ast.ImportFrom): names = [node.module or '']
        else: continue
        assert not any(name.startswith(('docs', 'tests', 'test_')) for name in names)
