"""Static development evidence checks; no mechanics rerun or qualification."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT/'docs/reference_cases/ge_beam3_station_resultant_development_evidence.json'


def canonical(value): return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode()
def sha(raw): return hashlib.sha256(raw).hexdigest()
def strict(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result: raise ValueError('duplicate key')
            result[key] = value
        return result
    def invalid(_): raise ValueError('nonfinite JSON')
    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)
    if canonical(value) != raw: raise ValueError('noncanonical JSON')
    return value


def test_record_is_canonical_and_does_not_claim_qualification():
    record = strict(RECORD.read_bytes())
    assert record['production_qualified'] is False
    assert record['independent_review'] == 'PENDING'
    assert record['force_tolerance'] == '1e-11'
    assert record['disposition'] == 'DEVELOPMENT_CELL_IDENTITIES_PASS_NOT_BEAM_QUALIFICATION'
    assert len(record['remaining']) == 5


@pytest.mark.parametrize('bad', [b'{"a":1,"a":2}\n', b'{"a":NaN}\n', b'{"a":Infinity}\n', b'{ "a":1}\n'])
def test_strict_parser_rejects_invalid_evidence(bad):
    with pytest.raises(ValueError): strict(bad)


def test_source_bindings_and_research_only_import_closure():
    record = strict(RECORD.read_bytes())
    for source in record['sources']:
        raw = (ROOT/source['path']).read_bytes().replace(b'\r\n', b'\n')
        assert len(raw) == source['bytes'] and sha(raw) == source['sha256']
    files = ['ge_beam3_station_resultant_cell.py', 'ge_beam3_decimal_cell_force_audit.py', 'ge_beam3_decimal_chain_audit.py']
    allowed = {'docs.reference_cases.ge_beam3_decimal_chain_audit'}
    for file in files:
        tree = ast.parse((ROOT/'docs/reference_cases'/file).read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import): imports = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom): imports = [node.module]
            else: continue
            assert all(name in allowed or name.split('.')[0] in sys.stdlib_module_names for name in imports)


def test_archive_hashes_inventories_and_exact_pairs():
    record = strict(RECORD.read_bytes()); archive = Path(record['archive']['path'])
    if not archive.exists(): pytest.skip('explicit external development archive required')
    raw = (archive/'archive-manifest.json').read_bytes()
    assert len(raw) == record['archive']['manifest_bytes']
    assert sha(raw) == record['archive']['manifest_sha256']
    manifest = json.loads(raw)
    assert len(manifest['files']) == record['archive']['files']
    assert sum(row['bytes'] for row in manifest['files']) == record['archive']['bytes']
    for row in manifest['files']:
        content = (archive/row['path']).read_bytes()
        assert len(content) == row['bytes'] and sha(content) == row['sha256']
    assert len(record['deterministic_pairs']) == 26
    for row in record['deterministic_pairs']:
        a = (archive/'cycle-a'/row['path']).read_bytes()
        b = (archive/'cycle-b'/row['path']).read_bytes()
        assert a == b and len(a) == row['bytes'] and sha(a) == row['sha256']
    assert [(row['tests'], row['errors'], row['failures'], row['skipped']) for row in record['inventories']] == [
        (1, 1, 0, 0), (16, 0, 0, 0), (26, 0, 0, 0), (37, 0, 0, 0), (37, 0, 0, 0)]


def test_exact_seven_research_path_extent_and_no_production_delta():
    record = strict(RECORD.read_bytes())
    def git(*args): return subprocess.check_output(['git', *args], cwd=ROOT, text=True).splitlines()
    # Missing local base is an error, not silently accepted.
    assert git('rev-parse', record['base_commit']+'^{tree}') == [record['base_tree']]
    changed = set(git('diff', '--name-only', record['base_commit']))
    changed.update(git('ls-files', '--others', '--exclude-standard', '--', 'docs/', 'tests/', 'src/'))
    expected = {row['path'] for row in record['sources']} | {
        'docs/agent_plans/GE_BEAM3_STATION_RESULTANT_DEVELOPMENT_CHECKPOINT.md',
        'docs/reference_cases/ge_beam3_station_resultant_development_evidence.json',
        'tests/test_ge_beam3_station_resultant_checkpoint.py'}
    assert changed == expected
