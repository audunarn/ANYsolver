"""Static evidence integrity: the remaining cell failure is not waived."""
import hashlib
import json
from pathlib import Path
import subprocess
import pytest

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT/'docs/reference_cases/ge_beam3_complementary_plastic_development_evidence.json'


def strict(raw):
    def pairs(rows):
        data = {}
        for key, value in rows:
            if key in data: raise ValueError('duplicate key')
            data[key] = value
        return data
    def reject(value): raise ValueError('nonfinite number')
    result = json.loads(raw, object_pairs_hook=pairs, parse_constant=reject)
    if (json.dumps(result, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode() != raw:
        raise ValueError('noncanonical JSON')
    return result


def test_frozen_source_and_failed_draft_bindings():
    data = strict(PATH.read_bytes().replace(b'\r\n', b'\n'))
    assert len(data['sources']) == 4 and len(data['failed_drafts']) == 6
    for row in data['sources']:
        raw = (ROOT/row['path']).read_bytes().replace(b'\r\n', b'\n')
        assert len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256']
    assert len(data['matching_section_json_pairs']) == 4
    assert len({row['path'] for row in data['matching_section_json_pairs']}) == 4


def test_cell_failure_blocks_nonlinear_integration():
    data = strict(PATH.read_bytes().replace(b'\r\n', b'\n'))
    runs = {row['run']: row for row in data['inventories']}
    for name in ('section-final-a', 'section-final-b'):
        assert runs[name]['tests'] == 27
        assert all(runs[name][key] == 0 for key in ('errors', 'failures', 'skipped'))
    assert runs['cell-final-failure']['tests'] == 7
    assert runs['cell-final-failure']['failures'] == 1
    assert runs['cell-final-failure']['skipped'] == 0
    assert data['cell']['final_failure']['force_error'] > data['cell']['force_tolerance']
    assert data['nonlinear_beam_integration_authorized'] is False
    assert data['production_qualified'] is False and data['independent_review'] == 'PENDING'


@pytest.mark.parametrize('raw', [b'{"a":1,"a":1}\n', b'{"a":NaN}\n', b'{"a":Infinity}\n', b'{ "a":1}\n'])
def test_invalid_checkpoint_json_rejected(raw):
    with pytest.raises(ValueError): strict(raw)


def test_no_existing_tracked_paths_changed():
    data = strict(PATH.read_bytes().replace(b'\r\n', b'\n'))
    base = data['base']['commit']
    assert subprocess.check_output(['git', 'rev-parse', base+'^{tree}'], cwd=ROOT, text=True).strip() == data['base']['tree']
    changed = subprocess.check_output(['git', 'diff', '--name-only', '--diff-filter=MDRCT', base], cwd=ROOT, text=True)
    assert not changed.strip()
