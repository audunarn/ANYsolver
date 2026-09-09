"""Static scope and preservation checks, not an independent scientific review."""
import hashlib
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT/'docs/reference_cases/ge_beam3_kinematic_fibre_development_evidence.json'


def parse(raw):
    def unique(pairs):
        value = {}
        for key, member in pairs:
            if key in value:
                raise ValueError('duplicate checkpoint key')
            value[key] = member
        return value
    def finite(value):
        raise ValueError('nonfinite checkpoint value')
    value = json.loads(raw, object_pairs_hook=unique, parse_constant=finite)
    if raw != (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode('ascii'):
        raise ValueError('noncanonical checkpoint')
    return value


def record():
    return parse(EVIDENCE.read_bytes().replace(b'\r\n', b'\n'))


def test_development_pass_does_not_activate_or_claim_independent_qualification():
    value = record()
    assert value['schema'] == 'GE_BEAM3_KINEMATIC_FIBRE_CONTROL_DEVELOPMENT_V1'
    assert value['status'] == 'DEVELOPMENT_KINEMATIC_INITIALIZATION_AND_SPATIAL_NEWTON_PASS'
    assert value['independent_review'] == 'PENDING'
    assert value['deterministic_cycle_pair_completed'] is True
    for key in ('qualification_pass', 'production_qualified', 'public_routing_changed'):
        assert value[key] is False
    assert value['resource_requests_consumed'] == []
    scope = value['verified_scope']
    assert scope['control_contrasts'] == ['1', '1e12']
    assert scope['targets_per_loading_sequence'] == 4 and scope['split_restart_after'] == 2
    assert scope['arch_targets'] == 8
    assert (scope['newton_limit'], scope['backtrack_limit'], scope['chart_limit']) == (24, 8, '0.9*pi')
    assert scope['equilibrium_gate'] == '1e-11' and scope['spatial_derivative_gate'] == '1e-7'


def test_failed_variants_and_final_cycles_are_separate_inventories():
    value = record()
    assert [(r['label'], r['tests'], r['failures'], r['errors'], r['skipped'])
            for r in value['inventories']] == [
        ('local-initial', 15, 0, 0, 0),
        ('chart-bound', 4, 1, 0, 0),
        ('retraction', 4, 1, 0, 0),
        ('spatial-retraction', 5, 1, 0, 0),
        ('spatial-pass', 5, 0, 0, 0),
        ('cycle-a', 30, 0, 0, 0),
        ('cycle-b', 30, 0, 0, 0),
    ]
    assert [r['inventory'] for r in value['incidents']] == [
        'chart-bound', 'retraction', 'spatial-retraction']
    assert len(value['source_variant_binding']) == 7
    assert value['source_variant_binding'][-2:] == [
        {'inventory': 'cycle-a', 'snapshot': 'source'},
        {'inventory': 'cycle-b', 'snapshot': 'source'}]


@pytest.mark.parametrize('index', range(4))
def test_final_tested_source_hash_is_preserved(index):
    row = record()['sources'][index]
    raw = (ROOT/row['path']).read_bytes().replace(b'\r\n', b'\n')
    assert len(raw) == row['bytes']
    assert hashlib.sha256(raw).hexdigest() == row['sha256']


def test_predecessor_failure_has_not_been_reclassified():
    value = record()
    row = value['predecessor']
    raw = (ROOT/row['path']).read_bytes().replace(b'\r\n', b'\n')
    assert len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256']
    old = parse(raw)
    assert old['status'] == 'DEVELOPMENT_HIGH_CONTRAST_CONTROL_UNRESOLVED'
    assert old['qualification_pass'] is False
    assert old['inventories'][-1]['failures'] == 1
    assert value['parent_commit'] == '6162e811fea24a99e15c3e1f47d1c4811ba3ccaa'
    assert value['parent_tree'] == 'ce2c1e42b0ff3f16108f6bc38b646072f1e4ba95'


def test_archive_and_pair_inventory_are_complete_and_narrow():
    value = record()
    archive = value['archive']
    assert (archive['content_files'], archive['content_bytes'], archive['manifest_bytes']) == (87, 2098545, 13585)
    assert archive['manifest_sha256'] == 'e20116d5b9e6313969cf1b696d97133a4bb7760dc3e6ce9dbe2632b5d9d7711d'
    rows = value['deterministic_pairs']
    assert len(rows) == value['verified_scope']['deterministic_json_pairs'] == 17
    paths = [row['path'] for row in rows]
    assert len(set(paths)) == len(paths)
    assert sum(path.endswith('/primal.json') for path in paths) == 6
    assert sum(path.endswith('/whole.json') for path in paths) == 2
    assert sum(path.endswith('/paused.json') for path in paths) == 3
    assert sum(path.endswith('/progress.json') for path in paths) == 2
    for row in rows:
        assert not Path(row['path']).is_absolute() and '..' not in Path(row['path']).parts
        assert row['bytes'] > 0 and len(row['sha256']) == 64
        assert set(row['sha256']) <= set('0123456789abcdef')


@pytest.mark.parametrize('raw', [
    b'{"x":1,"x":2}\n',
    b'{"x":NaN}\n',
    b'{"x":Infinity}\n',
    b'{ "x":1}\n',
])
def test_checkpoint_parser_rejects_ambiguous_bytes(raw):
    with pytest.raises(ValueError):
        parse(raw)
