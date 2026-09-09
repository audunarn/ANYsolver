"""Read-only coordinate-successor evidence checks; no mechanics rerun."""

import hashlib
import json
from pathlib import Path

import pytest

from docs.reference_cases import ge_beam3_curved_p5_coordinate_source_map as source_map


ROOT = Path(__file__).resolve().parents[1]


def record():
    raw = (ROOT/'docs/reference_cases/ge_beam3_curved_p5_coordinate_development_evidence.json').read_text().encode('ascii')
    value = json.loads(raw)
    assert raw == source_map.canonical(value)
    return value


def test_coordinate_checkpoint_binds_source_and_not_qualification():
    evidence = record()
    assert evidence['source_regression']['passed'] == 94 and evidence['source_regression']['failed'] == 0
    assert evidence['installed_test']['passed'] == 1 and evidence['installed_test']['failed'] == 0
    assert evidence['independent_review_status'] == 'PENDING'
    assert not any(evidence[k] for k in ('production_qualified','public_selector_authorized',
        'release_authorized','defaults_changed','historical_evidence_reclassified'))
    assert evidence['formal_resource_requests'] == []
    raw = source_map.source(source_map.MANIFEST)
    assert hashlib.sha256(raw).hexdigest() == evidence['source_map_sha256']
    assert source_map.canonical(source_map.build()) == raw
    assert len(evidence['remaining']) > 0


def test_coordinate_archive_inventory_binds_both_identical_results():
    evidence = record(); files = evidence['archive_files']; installed = evidence['installed_test']
    assert len(files) == len({f['name'] for f in files}) == 6
    assert sum(f['bytes'] for f in files) == 1327084
    cycles = [f for f in files if f['name'].startswith('cycle-')]
    assert len(cycles) == 2
    assert all(f['bytes'] == installed['result_bytes'] and f['sha256'] == installed['result_sha256'] for f in cycles)
    assert installed['cycles_identical'] and installed['sub_ulp_axial_commit_verified']
    wheel = next(f for f in files if f['name'].endswith('.whl'))
    assert (wheel['bytes'],wheel['sha256']) == (installed['wheel_bytes'],installed['wheel_sha256'])


def test_preserved_coordinate_archive_bytes_and_runtime_provenance():
    evidence = record(); root = Path(evidence['archive_root'])
    if not all((root/f['name']).is_file() for f in evidence['archive_files']):
        pytest.skip('development archive is not mounted; not an executed artifact verification')
    for item in evidence['archive_files']:
        raw = (root/item['name']).read_bytes()
        assert len(raw) == item['bytes'] and hashlib.sha256(raw).hexdigest() == item['sha256']
    first = (root/'cycle-1.json').read_bytes(); second = (root/'cycle-2.json').read_bytes()
    assert first == second
    output = json.loads(first)
    assert output['formulation'] == evidence['formulation_id']
    assert output['coordinate_policy'] == evidence['coordinate_policy']
    assert output['source_map_sha256'] == evidence['source_map_sha256']
    assert output['imports_isolated'] and output['research_imports_forbidden'] and output['restart_exact']
    assert output['sub_ulp_axial_commit_verified'] and not output['production_qualified']
    receipt = json.loads((root/'receipt.json').read_bytes())
    assert receipt['result_sha256'] == evidence['installed_test']['result_sha256']
    assert len(receipt['dependencies']) == 10 and not receipt['release_authorized']
