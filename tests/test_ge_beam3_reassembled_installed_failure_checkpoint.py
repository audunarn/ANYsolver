"""Preserve an actual failed gate without converting audit success to qualification."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import pytest

ROOT=Path(__file__).parents[1]
RECORD='docs/reference_cases/ge_beam3_reassembled_installed_failure_evidence.json'
EXTRA={RECORD,'docs/agent_plans/GE_BEAM3_REASSEMBLED_INSTALLED_FAILURE.md',
       'tests/test_ge_beam3_reassembled_installed_failure_checkpoint.py'}


def read():
    def unique(rows):
        made={}
        for k,v in rows:
            if k in made: raise ValueError('duplicate')
            made[k]=v
        return made
    def reject(value): raise ValueError('nonfinite')
    raw=(ROOT/RECORD).read_bytes().replace(b'\r\n',b'\n')
    value=json.loads(raw,object_pairs_hook=unique,parse_constant=reject)
    assert raw==(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode('ascii')
    return value


def test_package_failure_is_not_qualification_or_a_retry_authority():
    p=read()
    assert p['status']=='DEVELOPMENT_INCOMPLETE_SUPPLIED_FACTOR_COVARIANCE'
    assert p['production_qualified'] is p['public_routing_changed'] is p['release_authorized'] is False
    assert p['independent_review']=='PENDING' and p['formal_resource_requests_consumed']==[]
    gate=p['package']
    assert (gate['passed'],gate['failed'],gate['errors'],gate['skipped'])==(0,1,0,0)
    assert gate['second_worker_launched'] is gate['canonical_result_created'] is gate['receipt_created'] is False
    assert len(gate['completed_cases'])==7 and len(gate['unexecuted_cases'])==2
    assert gate['failed_case']=='reference_contrast_GENERAL'
    assert 'NEVER_PUBLISH' in gate['private_version_collision_warning']


def test_diagnosis_retains_both_variants_and_distinguishes_arithmetic_review():
    d=read()['diagnosis']
    assert d['covariance_rtol']==d['covariance_atol']==1e-11
    assert d['source_failed_correlation_error']>1e-11
    assert d['installed_failed_correlation_error']>1e-11
    assert d['audit_per_node_correlation_error']>1e-11
    assert d['audit_batched_correlation_error']<1e-11
    assert d['native_audit_maximum_error']<1e-15
    assert d['exact_upstream_cause']=='NOT_YET_ISOLATED'
    assert d['independent_mechanics_review'] is d['certified_intervals'] is False
    assert d['audit_tests']==dict(passed=6,failed=0,errors=0,skipped=0)


def test_six_sources_have_exact_normalized_hashes():
    rows=read()['sources']; assert len(rows)==len({r['path'] for r in rows})==6
    for row in rows:
        raw=(ROOT/row['path']).read_bytes().replace(b'\r\n',b'\n')
        assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']


def test_archive_binds_only_actual_files_and_failed_wheel():
    p=read(); a=p['archive']; rows=a['files']; paths={r['path'] for r in rows}
    assert len(rows)==len(paths)==a['file_count']==62
    assert sum(r['bytes'] for r in rows)==a['bytes']==5274537
    assert p['package']['wheel'] in rows
    assert 'package-junit.xml' in paths and 'audit-junit.xml' in paths
    assert not any('cycle-2/' in x or x.endswith('/receipt.json') or x.endswith('/result.json') for x in paths)
    assert len([x for x in paths if x.startswith('package/cycle-1/')])==14
    assert len([x for x in paths if x.endswith('.npz')])==8
    for row in rows:
        assert row['bytes']>=0 and len(row['sha256'])==64
        assert not Path(row['path']).is_absolute() and '..' not in Path(row['path']).parts


def test_frozen_mechanics_are_unchanged_and_extent_is_additive():
    p=read()
    def git(*args):
        return subprocess.run(['git',*args],cwd=ROOT,capture_output=True,text=True,check=True,timeout=30).stdout
    assert git('show','-s','--format=%T',p['base_commit']).strip()==p['base_tree']
    rows=[x.split('\t') for x in git('diff','--name-status',p['base_commit'],'--').splitlines()]
    assert all(kind=='A' for kind,_ in rows)
    paths={path for _,path in rows}|set(git('ls-files','--others','--exclude-standard').splitlines())
    assert paths=={r['path'] for r in p['sources']}|EXTRA
    assert not any(path.startswith('src/') for path in paths)


def test_worker_and_harness_keep_frozen_candidate_and_unwaived_assertions():
    for path in ('docs/reference_cases/ge_beam3_reassembled_modes_installed_smoke.py',
                 'tests/test_ge_beam3_reassembled_modes_installed.py'):
        text=(ROOT/path).read_text(); tree=ast.parse(text)
        assert read()['base_commit'] in text
        assert not any(isinstance(n,ast.Attribute) and n.attr=='xfail' for n in ast.walk(tree))
    worker=(ROOT/'docs/reference_cases/ge_beam3_reassembled_modes_installed_smoke.py').read_text()
    assert "q@np.array([x,.25*(1-x*x),.125*(1-x*x)])" in worker
    assert "np.testing.assert_allclose(np.abs(cross),np.eye(6),rtol=1e-11,atol=1e-11)" in worker


def test_audit_modes_are_standard_library_only():
    tree=ast.parse((ROOT/'docs/reference_cases/ge_beam3_decimal_mode_audit.py').read_text())
    assert {n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)}=={'decimal','time'}
    assert not any(isinstance(n,ast.Import) for n in ast.walk(tree))
