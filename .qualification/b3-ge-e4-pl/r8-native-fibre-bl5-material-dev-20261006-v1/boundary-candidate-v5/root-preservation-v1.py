"""Read-only artifact/source checks and one root delivery record; no mechanics."""
from pathlib import Path
import hashlib
import json
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[4]
RAW = ROOT / '.qualification/b3-ge-e4-pl/r8-native-fibre-bl5-material-dev-20261006-v1'
CANDIDATE = RAW / 'boundary-candidate-v5'
REPORT = CANDIDATE / 'root-binding-v1.json'
assert not REPORT.exists(), 'consumed delivery records are never overwritten'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def inside(base, name):
    path = (base / name).resolve()
    path.relative_to(base.resolve())
    return path

def load(path):
    return json.loads(path.read_text(encoding='utf-8'))

def verify_manifest(base, path, expected_sha, expected_count):
    assert sha(path) == expected_sha, str(path)
    rows = load(path)['artifacts']
    assert len(rows) == expected_count, str(path)
    for name, row in rows.items():
        selected = inside(base, name)
        assert selected.stat().st_size == row['bytes'], name
        assert sha(selected) == row['sha256'], name
    return rows

handoff_path = CANDIDATE / 'handoff.json'
assert sha(handoff_path) == 'eda02f771c5a8e0bde8af28e5cd1662d64baa0ed3c349226bebddce97c6b2c24'
handoff = load(handoff_path)
assert handoff['process_check']['remaining_owned_job_handles'] == 0
assert handoff['process_check']['matching_python_processes'] == 0
assert handoff['numerical_lease'].startswith('RELEASE')
for key in ('changed_paths_and_sha256', 'unchanged_strict_fixture_and_legacy'):
    for name, expected in handoff[key].items():
        assert sha(inside(ROOT, name)) == expected, name

preserved = {}
for name, row in handoff['preserved_original_manifests'].items():
    verify_manifest(RAW, RAW / name, row['sha256'], row['count'])
    preserved[name] = row
local = handoff['preserved_local_audit']
verify_manifest(RAW / 'local-audit-v4', RAW / 'local-audit-v4/artifact-sha256.json',
                local['manifest_sha256'], local['files'])
manifest = CANDIDATE / 'artifact-sha256.json'
candidate_rows = verify_manifest(CANDIDATE, manifest,
    'f0f530eda26592b0b010e2248e38a091fb77db8fb4b6eab6fb03b2c97b15c14a', 184)
review = CANDIDATE / 'independent-boundary-review-v1.md'
assert sha(review) == '3f1b6f7668df4f89656880f479b56202918f635a283326ff27e0feda09db84ea'

wheel = inside(ROOT, '.qualification/b3-ge-e4-pl/r8-native-fibre-bl5-material-dev-20261006-v1/wheel-v1/anysolver-0.4.7-py3-none-any.whl')
assert sha(wheel) == handoff['preserved_old_wheel']['sha256']
payloads = 0
with zipfile.ZipFile(wheel) as archive:
    for name in archive.namelist():
        if name.startswith('anysolver/') and not name.endswith('/'):
            installed = inside(RAW / 'installed-wheel-v1', name)
            assert installed.read_bytes() == archive.read(name), name
            payloads += 1
assert payloads == 424

for name in ('screen-v2', 'cohort-v1', 'helpers-v3'):
    runtime = load(CANDIDATE / name / 'runtime.json')
    assert runtime['jit_disabled'] is True and runtime['affinity'] == [0]
    assert all(row['num_threads'] == 1 for row in runtime['pools'])
    for dependency in runtime['dependencies'].values():
        assert 'ci-site-network-v2' in dependency['path'], dependency['path']
    for imported in runtime['imports'].values():
        assert str(ROOT).lower() in imported.lower(), imported
screen = load(CANDIDATE / 'screen-v2/result.json')
assert screen['screen_pass'] is True and len(screen['accepted']) == 1
accepted = screen['accepted'][0]
assert abs(accepted['factor'] - .3125) <= 1e-15
assert accepted['generation'] == 6 and accepted['iterations'] == 5
assert accepted['equilibrium'] <= 1e-8 and accepted['gap'] <= 1e-9
assert len(screen['amounts']) == 8
cohort = load(CANDIDATE / 'cohort-v1/result.json')
assert cohort['pytest_exit_code'] == 1
assert sum(row['outcome'] == 'failed' for row in cohort['call_reports']) == 2
assert sum(row['outcome'] == 'passed' for row in cohort['call_reports']) == 6
assert load(CANDIDATE / 'helpers-v3/result.json')['pytest_exit_code'] == 0
assert '15 passed' in (CANDIDATE / 'helpers-v3/stdout.log').read_text(encoding='utf-8')

matrix = 'docs/agent_plans/B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md'
previous = subprocess.check_output(['git', 'show', 'HEAD:' + matrix], cwd=ROOT)
assert len(previous) == 228268
assert inside(ROOT, matrix).read_bytes().startswith(previous)
source = handoff['changed_paths_and_sha256']
named = [inside(CANDIDATE, name).relative_to(ROOT).as_posix() for name in candidate_rows]
named.extend((manifest.relative_to(ROOT).as_posix(),
              Path(__file__).resolve().relative_to(ROOT).as_posix(),
              REPORT.relative_to(ROOT).as_posix()))
named.extend(source)
named.extend(('.gitattributes', matrix, 'docs/agent_plans/B3_GE_E4_PL_ACTIVE_STATE.md'))
assert len(named) == len(set(named))
report = dict(
    state='PARTIAL_IMPLEMENTATION; narrow screen only; full material gate FAILED/unqualified',
    head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
    handoff_sha256=sha(handoff_path), manifest_sha256=sha(manifest),
    candidate_artifacts=184, current_source_sha256=source,
    unchanged_source_sha256=handoff['unchanged_strict_fixture_and_legacy'],
    independent_review_sha256=sha(review), preserved_manifests=preserved,
    local_audit_files=33, older_wheel_payloads=payloads,
    old_wheel_limitation='Older source only; no candidate wheel or installed scientific claim',
    acceptance_prefix_bytes=len(previous), acceptance_prefix_sha256=hashlib.sha256(previous).hexdigest(),
    checks=dict(screen='PASS five Newton/eight candidates at pending .3125',
                cohort='FAILED 2 native cases / 6 historical cases PASS',
                focused_final_source='15 PASS; post-cohort compatibility repairs'),
    numerical_evaluations_by_root=0,
    known_gaps=['J2 fails at .90625 after simultaneous accepted .75/.875 prefix',
                'elastic-shell FD field crosses branches before derivative errors',
                'failed J2 trial residual/tangent/norms not saved',
                'screen/cohort use pre-schema-repair source; final focused checks bind amended source',
                'full programme and installed/artifact acceptance remain OPEN'],
    stage_paths=named)
REPORT.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(dict(candidate_artifacts=184, source_paths=len(source),
    preserved_historical_artifacts='760/779 plus33 local audit', older_wheel_payloads=payloads,
    acceptance_prefix_preserved=True, stage_paths=len(named), report=str(REPORT))))
