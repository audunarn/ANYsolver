"""Static checkpoint integrity, separate from mechanics test inventories."""
import hashlib
import json
from pathlib import Path
import subprocess
import pytest

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT/'docs/reference_cases/ge_beam3_retained_resultant_development_evidence.json'


def load(raw):
    def pairs(rows):
        result = {}
        for key, value in rows:
            if key in result: raise ValueError('duplicate key')
            result[key] = value
        return result
    def nonfinite(value): raise ValueError('nonfinite value')
    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)
    expected = (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode()
    if expected != raw: raise ValueError('canonical JSON required')
    return value


def test_checkpoint_source_identity_and_scope():
    value = load(PATH.read_bytes().replace(b'\r\n', b'\n'))
    assert len(value['sources']) == 9
    for row in value['sources']:
        data = (ROOT/row['path']).read_bytes().replace(b'\r\n', b'\n')
        assert len(data) == row['bytes']
        assert hashlib.sha256(data).hexdigest() == row['sha256']
        assert row['path'].startswith(('tests/', 'docs/reference_cases/'))
    assert value['independent_review'] == 'PENDING'
    assert value['production_qualified'] is False
    assert value['public_integration_authorized'] is False
    assert value['native_state_restart_qualified'] is False


def test_failures_are_preserved_and_passes_are_not_qualification():
    value = load(PATH.read_bytes().replace(b'\r\n', b'\n'))
    runs = {r['run']: r for r in value['runs']}
    assert runs['original-force-failure']['tests'] == 3
    assert runs['original-force-failure']['failures'] == 2
    assert len(value['original_failures']) == 2
    assert all(r['completed_targets'] == 0 for r in value['original_failures'])
    for name in ('final-a', 'final-b'):
        assert runs[name]['tests'] == 19
        assert all(runs[name][k] == 0 for k in ('failures', 'errors', 'skipped'))
    assert len(value['matching_json_pairs']) == 14
    assert len({r['path'] for r in value['matching_json_pairs']}) == 14
    assert value['interpretation']['scientific_success_of_original_v5_force_gate'] is False
    assert len(value['open_requirements']) >= 8


@pytest.mark.parametrize('raw', [b'{"a":1,"a":1}\n', b'{"a":NaN}\n', b'{"a":Infinity}\n', b'{ "a": 1 }\n'])
def test_bad_checkpoint_json_rejected(raw):
    with pytest.raises(ValueError): load(raw)


def test_no_existing_tracked_path_change_from_bound_base():
    value = load(PATH.read_bytes().replace(b'\r\n', b'\n'))
    base = value['base']['commit']
    tree = subprocess.check_output(['git', 'rev-parse', base+'^{tree}'], cwd=ROOT, text=True).strip()
    assert tree == value['base']['tree']
    # This checkpoint is additive. Missing local base is never silently valid.
    changes = subprocess.check_output(['git', 'diff', '--name-only', '--diff-filter=MDRCT', base],
                                     cwd=ROOT, text=True)
    assert not changes.strip()
