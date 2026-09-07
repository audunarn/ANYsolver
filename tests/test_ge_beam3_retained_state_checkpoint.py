"""Static source/evidence integrity, separate from the numerical test suites."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import pytest

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT/'docs/reference_cases/ge_beam3_retained_state_development_evidence.json'


def strict(raw):
    def pairs(rows):
        value = {}
        for key, item in rows:
            if key in value: raise ValueError('duplicate key')
            value[key] = item
        return value
    def reject(value): raise ValueError('nonfinite number')
    data = json.loads(raw, object_pairs_hook=pairs, parse_constant=reject)
    if (json.dumps(data, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode() != raw:
        raise ValueError('noncanonical JSON')
    return data


def test_source_hashes_and_private_port_scope():
    data = strict(PATH.read_bytes().replace(b'\r\n', b'\n'))
    assert len(data['sources']) == 5
    modules = []
    for row in data['sources']:
        raw = (ROOT/row['path']).read_bytes().replace(b'\r\n', b'\n')
        assert len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256']
        if row['path'].startswith('src/'):
            modules.append(row['path'])
            tree = ast.parse(raw)
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    assert not (node.module or '').startswith(('docs', 'tests'))
                elif isinstance(node, ast.Import):
                    assert all(not item.name.startswith(('docs', 'tests')) for item in node.names)
    assert len(modules) == 3


def test_development_is_not_qualification_or_public_activation():
    data = strict(PATH.read_bytes().replace(b'\r\n', b'\n'))
    assert data['production_qualified'] is False
    assert data['public_integration_authorized'] is False
    assert data['central_analysis_dispatcher_integrated'] is False
    assert data['independent_review'] == 'PENDING'
    runs = {row['run']: row for row in data['inventories']}
    for name in ('final-a', 'final-b'):
        assert runs[name]['tests'] == 36
        assert all(runs[name][key] == 0 for key in ('errors', 'failures', 'skipped'))
    assert len(data['matching_json_pairs']) == 9
    assert len({row['path'] for row in data['matching_json_pairs']}) == 9
    assert len(data['limitations']) >= 8
    assert data['boundary']['resource_requests_consumed'] is False


@pytest.mark.parametrize('raw', [b'{"a":1,"a":1}\n', b'{"a":NaN}\n', b'{"a":Infinity}\n', b'{ "a":1}\n'])
def test_noncanonical_evidence_rejected(raw):
    with pytest.raises(ValueError): strict(raw)


def test_original_tracked_files_are_unchanged():
    data = strict(PATH.read_bytes().replace(b'\r\n', b'\n'))
    base = data['base']['commit']
    assert subprocess.check_output(['git', 'rev-parse', base+'^{tree}'], cwd=ROOT, text=True).strip() == data['base']['tree']
    # Missing local history is an error. No historical file is modified.
    changes = subprocess.check_output(['git', 'diff', '--name-only', '--diff-filter=MDRCT', base], cwd=ROOT, text=True)
    assert not changes.strip()
