"""Single static closeout node. Never rerun G3b mechanics."""
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/'docs/reference_cases'
CANDIDATE = '0fe7f8f0d740f4aebd926227e49fa40bedc2e32c'
TREE = 'e06b1374260769f2af23f362cccd8386479d33af'
LANES = ('mb2', 'mb3', 'mq4', 'ms3', 'weighted', 'transport', 'owner', 'owner_corrections')
COUNTS = (25, 40, 42, 45, 54, 39, 60, 180)
TERMINAL = 'PROVISIONAL_GO_GE_BEAM3_G3B_REFERENCE_MIXED_ELASTIC_STATIC_ONLY'
SCOPE = 'G3B_S16_MIXED_S18_REFERENCE_LINEAR_ONLY'
BOUNDARY = ('Reference-linear G3b S16/mixed S18 only; no finite mixed response, '
            'G3c, G4, G5, full parity, defaults or release.')


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'),
                       ensure_ascii=True, allow_nan=False)+'\n').encode('ascii')


def read(path):
    raw = path.read_bytes().replace(b'\r\n', b'\n')
    def pairs(items):
        made = {}
        for key, value in items:
            assert key not in made
            made[key] = value
        return made
    def nonfinite(value):
        raise AssertionError(value)
    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)
    assert canonical(value) == raw
    return raw, value


def binding(value):
    assert type(value) is dict and set(value) == {'bytes', 'sha256'}
    assert type(value['bytes']) is int and value['bytes'] >= 0
    assert type(value['sha256']) is str and re.fullmatch('[0-9a-f]{64}', value['sha256'])


def git(*args):
    import os
    env = {k:v for k,v in os.environ.items() if not k.startswith('GIT_')}
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_SYSTEM=os.devnull,
               GIT_CONFIG_GLOBAL=os.devnull, GIT_NO_REPLACE_OBJECTS='1', GIT_ATTR_NOSYSTEM='1')
    return subprocess.check_output(['git', '-c', 'safe.directory='+ROOT.as_posix(),
        '-c', 'core.attributesFile='+os.devnull, '-c', 'core.autocrlf=true',
        '-c', 'core.eol=crlf', *args], cwd=ROOT, env=env, timeout=30).decode().strip()


def test_g3b_formal_closeout():
    _, closeout = read(DATA/'ge_beam3_g3b_closeout_v1.json')
    assert set(closeout) == {'schema', 'candidate', 'tree', 'terminal', 'artifacts',
        'external_archive', 'defaults_changed', 'general_static_parity'}
    assert closeout['schema'] == 'GE_BEAM3_G3B_STATIC_CLOSEOUT_V1'
    assert closeout['candidate'] == CANDIDATE and closeout['tree'] == TREE
    assert closeout['terminal'] == TERMINAL
    assert closeout['defaults_changed'] is False and closeout['general_static_parity'] is False
    names = {'ge_beam3_g3b_confirmation_v1.json', 'ge_beam3_g3b_implementation_review_v1.json',
             'ge_beam3_g3b_confirmation_review_v1.json', 'ge_beam3_g3b_formal_raw_manifest_v1.json'}
    assert set(closeout['artifacts']) == names
    values = {}
    for name in sorted(names):
        raw, values[name] = read(DATA/name)
        binding(closeout['artifacts'][name])
        assert closeout['artifacts'][name] == dict(bytes=len(raw), sha256=sha256(raw).hexdigest())
    result = values['ge_beam3_g3b_confirmation_v1.json']
    assert set(result) == {'schema', 'candidate', 'tree', 'inputs_sha256', 'environment_sha256',
        'review_sha256', 'inventory_sha256', 'scope', 'cycles', 'lanes', 'terminal',
        'defaults_changed', 'general_static_parity'}
    assert result['schema'] == 'GE_BEAM3_G3B_CONFIRMATION_V1'
    assert result['candidate'] == CANDIDATE and result['tree'] == TREE and result['terminal'] == TERMINAL
    assert type(result['cycles']) is int and result['cycles'] == 2
    assert result['defaults_changed'] is False and result['general_static_parity'] is False
    assert result['scope'] == SCOPE
    inv_raw, inv = read(DATA/'ge_beam3_g3b_confirmation_inventory_v2.json')
    assert result['inventory_sha256'] == sha256(inv_raw).hexdigest()
    assert [r['lane'] for r in result['lanes']] == list(LANES)
    for registered, row, lane, count in zip(inv['lanes'], result['lanes'], LANES, COUNTS):
        assert registered['lane'] == row['lane'] == lane and len(registered['nodes']) == count
        scientific = row['scientific']
        assert set(scientific) == {'lane', 'tests', 'checkpoints', 'packet'}
        assert scientific['lane'] == lane
        tests = scientific['tests']
        assert set(tests) == {'lane', 'collected', 'reports', 'exitcode'}
        assert tests['lane'] == lane and tests['collected'] == registered['nodes']
        assert type(tests['exitcode']) is int and tests['exitcode'] == 0
        assert tests['reports'] == [dict(node=n, phase=p, outcome='passed')
            for n in registered['nodes'] for p in ('setup', 'call', 'teardown')]
    implementation = values['ge_beam3_g3b_implementation_review_v1.json']
    evidence = values['ge_beam3_g3b_confirmation_review_v1.json']
    for review in (implementation, evidence):
        assert set(review) == {'decision', 'findings', 'reviewer', 'scope', 'subject_commit'}
        assert review['findings'] == [] and review['subject_commit'] == CANDIDATE
        who = review['reviewer']
        assert set(who) == {'id', 'independent', 'provenance'}
        assert who['independent'] is True and type(who['id']) is str
        assert who['id'].strip() and who['id'] != '/root'
        assert who['provenance'] in ('separate_reviewer', 'external_reviewer')
        assert review['scope']['subject_tree'] == TREE
        assert review['scope']['scope_id'] == SCOPE
    assert set(implementation['scope']) == {'subject_tree', 'scope_id', 'inputs_sha256',
        'environment_sha256', 'inventory_sha256'}
    assert set(evidence['scope']) == {'subject_tree', 'scope_id', 'aggregate_sha256',
        'raw_manifest_sha256', 'implementation_review_sha256', 'acceptance_boundary'}
    assert evidence['scope']['acceptance_boundary'] == BOUNDARY
    assert implementation['decision'] == 'ACCEPTED_G3B_IMPLEMENTATION_AND_RUNNER_REVIEW'
    assert evidence['decision'] == 'ACCEPTED_G3B_SCOPED_CONFIRMATION'
    assert result['review_sha256'] == closeout['artifacts']['ge_beam3_g3b_implementation_review_v1.json']['sha256']
    for key in ('inputs_sha256', 'environment_sha256', 'inventory_sha256'):
        assert implementation['scope'][key] == result[key]
    assert evidence['scope']['aggregate_sha256'] == closeout['artifacts']['ge_beam3_g3b_confirmation_v1.json']['sha256']
    assert evidence['scope']['raw_manifest_sha256'] == closeout['artifacts']['ge_beam3_g3b_formal_raw_manifest_v1.json']['sha256']
    assert evidence['scope']['implementation_review_sha256'] == result['review_sha256']
    manifest = values['ge_beam3_g3b_formal_raw_manifest_v1.json']
    assert set(manifest) == {'schema', 'candidate', 'tree', 'terminal', 'source_directory', 'files'}
    assert manifest['schema'] == 'G3B_FORMAL_RAW_ARCHIVE_V1'
    assert manifest['candidate'] == CANDIDATE and manifest['tree'] == TREE
    assert manifest['terminal'] == TERMINAL and manifest['source_directory']
    assert type(manifest['files']) is list and manifest['files']
    for row in manifest['files']:
        assert type(row) is dict and set(row) == {'path', 'bytes', 'sha256'}
        path = row['path']
        assert type(path) is str and path and not path.startswith('/')
        assert '\\' not in path and ':' not in path and all(p not in ('', '.', '..') for p in path.split('/'))
        binding({k:v for k,v in row.items() if k != 'path'})
    paths = [r['path'] for r in manifest['files']]
    assert len(paths) == len(set(paths)) and 'formal/aggregate.json' in paths
    aggregate_row = next(r for r in manifest['files'] if r['path'] == 'formal/aggregate.json')
    assert {k:v for k,v in aggregate_row.items() if k != 'path'} == closeout['artifacts']['ge_beam3_g3b_confirmation_v1.json']
    assert git('rev-parse', CANDIDATE+'^{tree}') == TREE
    git('merge-base', '--is-ancestor', CANDIDATE, 'HEAD')
    assert not git('diff', '--name-only', CANDIDATE, '--', 'src', 'scripts', 'pyproject.toml', '.github')
    allowed = {'tests/test_ge_beam3_g3b_closeout.py', 'docs/GE_BEAM3_G3B_CONFIRMATION_STATUS.md',
        'docs/GE_BEAM3_G3B_IMPLEMENTATION_REVIEW.md', 'docs/GE_BEAM3_G3B_EVIDENCE_REVIEW.md',
        'docs/reference_cases/ge_beam3_g3b_closeout_v1.json'}
    allowed.update('docs/reference_cases/'+name for name in names)
    changed = set(git('diff', '--name-only', CANDIDATE).splitlines())
    untracked = set(git('ls-files', '--others', '--exclude-standard').splitlines())
    assert changed|untracked == allowed
    git('diff', '--check', CANDIDATE)
