"""Static planning-inventory tests; no solver, numerical or research imports."""
import ast
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

import pytest
from scripts import audit_beam_parity_matrix as audit

ROOT = Path(__file__).resolve().parents[1]


def matrix():
    return audit.strict((ROOT / audit.MATRIX).read_bytes())


def test_frozen_matrix_inventory_and_report_agree():
    data = matrix()
    inventory = audit.strict((ROOT / audit.INVENTORY).read_bytes())
    audit.validate_rows(data)
    assert inventory['matrix_sha256'] == sha256(audit.canonical(data)).hexdigest()
    assert inventory['baseline_commit'] == audit.BASE
    assert inventory['baseline_tree'] == audit.TREE
    assert inventory['mechanics_executed'] is False
    assert len(inventory['test_module_corpus']) == 792
    assert len(inventory['source_bindings']) == 73
    assert set().union(*map(set, inventory['legacy_public_members'].values())) == set(audit.METHOD_ROWS)
    assert (ROOT / audit.REPORT).read_bytes().replace(b'\r\n', b'\n') == audit.render(data, inventory)
    for row in data['rows']:
        for ref in row['sources'] + row['legacy_tests'] + row['ge_tests']:
            assert ref.split('::')[0] in inventory['source_bindings']


@pytest.mark.parametrize('mutation', ('row_missing', 'row_duplicate', 'row_order', 'test_removed', 'hash'))
def test_matrix_mutation_cannot_match_frozen_inventory(mutation):
    data = matrix()
    if mutation == 'row_missing': data['rows'].pop()
    elif mutation == 'row_duplicate': data['rows'].append(deepcopy(data['rows'][0]))
    elif mutation == 'row_order': data['rows'].reverse()
    elif mutation == 'test_removed': data['rows'][0]['legacy_tests'].pop()
    else: data['baseline_commit'] = '0'*40
    inventory = audit.strict((ROOT / audit.INVENTORY).read_bytes())
    assert sha256(audit.canonical(data)).hexdigest() != inventory['matrix_sha256']
    if mutation != 'test_removed':
        with pytest.raises(ValueError): audit.validate_rows(data)


@pytest.mark.parametrize('mutation', ('mechanics', 'defaults', 'unsupported_as_required', 'unknown', 'path'))
def test_planning_boundary_rejects_mutation(mutation):
    data = matrix()
    if mutation == 'mechanics': data['scientific_tests_run'] = True
    elif mutation == 'defaults': data['default_changes'] = True
    elif mutation == 'unsupported_as_required': data['rows'][32]['action'] = 'IMPLEMENT'
    elif mutation == 'unknown': data['rows'][0]['ge'] = 'FULLY_QUALIFIED'
    else: data['rows'][0]['sources'] = ['../escape.py']
    with pytest.raises(ValueError): audit.validate_rows(data)


@pytest.mark.parametrize('raw', (b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":Infinity}', b'{"a": 1}'))
def test_duplicate_nonfinite_and_noncanonical_json_rejected(raw):
    with pytest.raises(ValueError): audit.strict(raw)


def test_unmapped_tests_are_not_misrepresented_as_irrelevant_or_passed():
    inventory = audit.strict((ROOT / audit.INVENTORY).read_bytes())
    assert {v['role'] for v in inventory['test_module_corpus'].values()} == {
        'ROW_REFERENCE', 'NOT_USED_AS_DIRECT_PARITY_EVIDENCE'}
    assert not any('passed' in v for v in inventory['test_module_corpus'].values())


def test_auditor_imports_only_the_standard_library():
    tree = ast.parse((ROOT / 'scripts/audit_beam_parity_matrix.py').read_text())
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import): names.update(n.name.split('.')[0] for n in node.names)
        if isinstance(node, ast.ImportFrom): names.add(node.module.split('.')[0])
    assert names <= {'__future__', 'argparse', 'ast', 'hashlib', 'json', 'pathlib', 're', 'subprocess'}
    assert not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                   and n.func.id in {'eval', 'exec', '__import__'} for n in ast.walk(tree))


def test_genuine_limitations_are_not_fabricated_legacy_parity():
    rows = {r['id']: r for r in matrix()['rows']}
    assert rows['U01']['legacy'] == rows['U02']['legacy'] == 'LEGACY_REJECTED'
    assert rows['U07']['legacy'] == 'LEGACY_PLACEHOLDER'
    assert rows['P25']['legacy'] == 'LEGACY_COVERAGE_UNESTABLISHED'
    assert rows['P26']['legacy'] == 'B2_TESTED_B3_COVERAGE_GAP'
    assert rows['P18']['legacy'] == 'SHARED_ROUTE_TESTED'
