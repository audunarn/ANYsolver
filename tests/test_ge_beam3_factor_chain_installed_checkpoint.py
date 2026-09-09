"""Installed private package evidence is not whole-beam qualification."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import pytest

ROOT=Path(__file__).parents[1]
RECORD='docs/reference_cases/ge_beam3_factor_chain_installed_evidence.json'
EXTRA={RECORD,'docs/agent_plans/GE_BEAM3_FACTOR_CHAIN_INSTALLED_CHECKPOINT.md',
       'tests/test_ge_beam3_factor_chain_installed_checkpoint.py'}


def parse(raw):
    def unique(rows):
        value={}
        for k,v in rows:
            if k in value:raise ValueError('duplicate')
            value[k]=v
        return value
    def reject(value):raise ValueError('nonfinite')
    value=json.loads(raw,object_pairs_hook=unique,parse_constant=reject)
    if raw!=(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode('ascii'):
        raise ValueError('noncanonical')
    return value


def read():return parse((ROOT/RECORD).read_bytes().replace(b'\r\n',b'\n'))


@pytest.mark.parametrize('raw',[b'{"a":1,"a":2}\n',b'{"a":NaN}\n',b'{"a":Infinity}\n'])
def test_invalid_canonical_evidence_is_rejected(raw):
    with pytest.raises(ValueError):parse(raw)


def test_private_success_does_not_authorize_publication_or_full_qualification():
    p=read()
    assert p['status']=='INSTALLED_DEVELOPMENT_CHECKS_PASS_QUALIFICATION_INCOMPLETE'
    assert p['production_qualified'] is p['public_routing_changed'] is p['release_authorized'] is False
    assert p['independent_review']=='PENDING' and p['formal_resource_requests_consumed']==[]
    assert p['preserved_failure']['overwritten'] is p['preserved_failure']['rerun'] is p['preserved_failure']['reclassified'] is False
    assert 'NEVER_PUBLISH_OR_REPLACE_RELEASED_0_4_2' in p['private_version_collision_warning']
    assert p['bounds']['beam_shell_connections_qualified'] is False
    assert p['bounds']['covariance_rtol']==p['bounds']['covariance_atol']==1e-11


def test_exact_fifteen_case_inventory_keeps_both_coordinate_orders():
    p=read();cases=p['cases'];names={r['case'] for r in cases}
    base={'straight_compression','straight_tension','curved_pair','plastic_unloading','free_curved'}
    expected=base|{order+'_'+group+'_contrast_'+rotation
        for order in ('per_node','batched') for group,rotations in (
            ('reference',('E','R90','GENERAL')),('finite',('E','GENERAL'))) for rotation in rotations}
    assert len(cases)==15 and names==expected
    assert all(r['checks_passed'] and r['state_preserved'] and r['replay_exact'] for r in cases)
    assert max(r['retained_coordinates'] for r in cases)==42
    test=p['test'];assert (test['passed'],test['failed'],test['errors'],test['skipped'])==(1,0,0,0)
    assert test['fresh_processes']==2 and test['installed_source_modules']==87
    assert test['worker_wall_limit_seconds']==180 and test['automatic_retry'] is False


def test_two_bound_sources_are_unchanged_since_the_package_run():
    rows=read()['sources'];assert len(rows)==2
    for row in rows:
        raw=(ROOT/row['path']).read_bytes().replace(b'\r\n',b'\n')
        assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']


def test_archive_receipt_and_all_thirty_one_pairs_agree():
    p=read();a=p['archive'];rows=a['files'];index={r['path']:r for r in rows}
    assert len(index)==len(rows)==a['file_count']==80
    assert sum(r['bytes'] for r in rows)==a['bytes']==6344510
    assert a['ordinary_context_hash_verified'] is True and p['test']['junit'] in index
    assert len(p['deterministic_json_pairs'])==31
    receipt=p['receipt'];assert receipt['candidate_commit']==p['base_commit']
    assert receipt['cycles_identical'] is True and receipt['production_qualified'] is receipt['release_authorized'] is False
    assert len(receipt['dependencies'])==10 and len(receipt['diagnostics'])==30
    for pair in p['deterministic_json_pairs']:
        for cycle in (1,2):
            row=index['cycle-'+str(cycle)+'/'+pair['path']]
            assert (row['bytes'],row['sha256'])==(pair['bytes'],pair['sha256'])
        if pair['path']!='result.json':
            assert receipt['diagnostics'][pair['path']]==dict(bytes=pair['bytes'],sha256=pair['sha256'])
    wheel=index['wheels/'+receipt['wheel_file']]
    assert (wheel['bytes'],wheel['sha256'])==(receipt['wheel_bytes'],receipt['wheel_sha256'])
    result=index['cycle-1/result.json']
    assert (result['bytes'],result['sha256'])==(receipt['result_bytes'],receipt['result_sha256'])
    assert index['candidate-source.zip']['sha256']==receipt['source_archive_sha256']
    assert index['source-map.json']['sha256']==receipt['source_map_sha256']
    for row in rows:
        assert row['bytes']>=0 and len(row['sha256'])==64
        assert not Path(row['path']).is_absolute() and '..' not in Path(row['path']).parts


def test_five_path_extent_contains_no_production_changes():
    p=read()
    def git(*args):return subprocess.run(['git',*args],cwd=ROOT,check=True,capture_output=True,text=True,timeout=30).stdout
    assert git('show','-s','--format=%T',p['base_commit']).strip()==p['base_tree']
    rows=[r.split('\t') for r in git('diff','--name-status',p['base_commit'],'--').splitlines()]
    assert all(kind=='A' for kind,_ in rows)
    paths={path for _,path in rows}|set(git('ls-files','--others','--exclude-standard').splitlines())
    assert paths=={r['path'] for r in p['sources']}|EXTRA
    assert all(path.startswith(('docs/','tests/')) for path in paths)


def test_independent_arithmetic_reference_is_preserved_not_retuned():
    def functions(path):
        tree=ast.parse((ROOT/path).read_text())
        return {n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,ast.FunctionDef)}
    old=functions('docs/reference_cases/ge_beam3_reassembled_modes_installed_smoke.py')
    new=functions('docs/reference_cases/ge_beam3_factor_chain_modes_installed_smoke.py')
    for name in ('characteristic','bending_roots'):assert old[name]==new[name]
    text=(ROOT/'docs/reference_cases/ge_beam3_factor_chain_modes_installed_smoke.py').read_text()
    assert 'for batched in (False,True):' in text
    assert 'points=points@q.T if batched else np.array([q@point for point in points])' in text
    assert 'np.testing.assert_allclose(np.abs(cross),np.eye(6),rtol=1e-11,atol=1e-11)' in text
