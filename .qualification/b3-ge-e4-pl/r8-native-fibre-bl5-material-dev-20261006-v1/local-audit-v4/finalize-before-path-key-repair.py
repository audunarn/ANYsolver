from pathlib import Path
from collections import Counter
import datetime, hashlib, json

ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT.parent
REPO = EVIDENCE.parents[2]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(Path(p).read_text(encoding='utf-8-sig'))
preservation = {}
for name in ('raw-artifact-sha256.json', 'raw-artifact-sha256-v2.json'):
    data = read(EVIDENCE/name)
    for path, row in data['artifacts'].items():
        assert sha(EVIDENCE/path) == row['sha256'], path
    preservation[name] = {'count': len(data['artifacts']), 'sha256': sha(EVIDENCE/name)}
read_handoff = read(EVIDENCE/'owner-diagnosis-v3-handoff.json')
for name, row in read_handoff['new_files'].items():
    assert sha(EVIDENCE/name) == row['sha256'], name
artifact = read(EVIDENCE/'artifact-binding-v1.json')
assert sha(artifact['artifact']) == artifact['sha256']
for name, digest in artifact['source'].items():
    target = EVIDENCE/'installed-wheel-v1'/name.replace('\\','/').removeprefix('src/')
    assert sha(target) == digest, name
product_names = ('src/anysolver/_stiffened_shell_ge_experimental.py',
                 'src/anysolver/_stiffened_shell_ge_finite_experimental.py',
                 'src/anysolver/_stiffened_shell_ge_point_buckling.py',
                 'src/anysolver/stiffened_shell.py')
product = {}
for name in product_names:
    digest = sha(REPO/name)
    assert digest == artifact['source'][name], name
    product[name] = digest
binding = read(ROOT/'binding-audit-v1.json')
for name, digest in binding['tools'].items():
    assert sha(ROOT/name) == digest and sha(ROOT/'executed-tools-audit-v1'/name) == digest, name
for name, digest in binding['fixture_sources'].items():
    assert sha(REPO/name) == digest and sha(ROOT/'executed-tools-audit-v1'/name) == digest, name
for name, digest in binding['saved_inputs'].items():
    assert sha(EVIDENCE/name) == digest, name
runtime = read(ROOT/'audit-v1/runtime.json')
installed = (EVIDENCE/'installed-wheel-v1').resolve()
assert all(Path(p).resolve().is_relative_to(installed) for p in runtime['imports'].values())
result = read(ROOT/'audit-v1/result.json')
assert result['local_audit_responses'] == 8
assert result['global_solves'] == result['global_failedstate_evaluations'] == 0
assert result['checkpoint_bytes_unchanged'] and result['history_origins_unchanged']
assert all(row['smooth_pass'] and row['explicit_branch_stable'] and row['origin_bytes_unchanged'] for row in result['results'])
execution = read(ROOT/'audit-v1/execution.json')
assert execution['status'] == 'completed' and execution['exit_code'] == 0
process = read(ROOT/'process-check.json')
assert process['matching_python_processes'] == 0
callback_counts = Counter((row['stage'], row['method']) for row in result['calls'])
handoff = {
    'status': 'verified against assigned local discriminator; global material milestone remains partial/unmet',
    'completed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'numerical_lease': 'RELEASE; owned entry/supervisor terminal, no matching owned Python process',
    'owned_process_check': process,
    'preserved_consumed': preservation,
    'preserved_read_handoff_sha256': sha(EVIDENCE/'owner-diagnosis-v3-handoff.json'),
    'preserved_read_files_verified': len(read_handoff['new_files']),
    'wheel': {'artifact': artifact['artifact'], 'sha256': artifact['sha256'],
              'verified_installed_payloads': len(artifact['source']), 'actual_solver_imports': len(runtime['imports'])},
    'unchanged_frozen_product': product,
    'checks_run': ['one bounded installed local audit', 'standard-library signed-margin/secant combination',
                   'terminal immutable input/artifact preservation verification', 'exact owned-process absence'],
    'callback_counts': [{'stage': stage, 'method': method, 'count': count}
                        for (stage, method), count in sorted(callback_counts.items())],
    'compile_owners': result['compile_owners'], 'fresh_restores': result['fresh_restores'],
    'accepted_factor': result['accepted_factor'], 'accepted_generation': result['accepted_generation'],
    'shapes': [{'member': row['member'], 'gradient': row['gradient_shape'], 'compliance': row['compliance_shape']} for row in result['results']],
    'smooth_criterion': result['criterion'],
    'smooth_errors': [{'member': row['member'], 'family': row['family'], 'relative_error': row['smooth_relative_error']} for row in result['results']],
    'terminal_execution': execution,
    'failures': ['output-procedure-failure.json: unexpected large permitted own-branch JSON formatting output; no protected content',
                 'no numerical or local criterion failure in this single audit'],
    'unresolved': ['global .3125 equilibrium', 'complete actual-chart assembly derivative/representation uncertainty',
                   'strict full lifecycle two cases and simultaneous shell/fibre gate remain failed/unmet'],
    'limitations': ['local compliance pass does not establish whole-system FD noise or global convergence',
                    'endpoint compliance jump does not bound geometric residual',
                    'audit exact numerical normalization weights not separately serialized; bound executed code retains their use',
                    'no product repair, public capability, qualification or global step treatment adopted'],
    'evidence': ['README.md', 'audit-v1/result.json', 'audit-v1/runtime.json', 'audit-v1/dependency-preflight.json',
                 'audit-v1/execution.json', 'audit-v1/thread-samples.json', 'summary.json', 'binding-audit-v1.json',
                 'executed-tools-audit-v1/', 'output-procedure-failure.json', 'process-check.json'],
}
(ROOT/'handoff.json').write_text(json.dumps(handoff, indent=2)+'\n')
manifest = {}
for path in sorted(ROOT.rglob('*')):
    if path.is_file() and '__pycache__' not in path.parts and path.name != 'artifact-sha256.json':
        manifest[str(path.relative_to(ROOT)).replace('\\','/')] = {'bytes': path.stat().st_size, 'sha256': sha(path)}
(ROOT/'artifact-sha256.json').write_text(json.dumps({'scope': 'only new local-audit-v4 artifacts; excludes self and caches',
                                                   'artifacts': manifest}, indent=2)+'\n')
print(json.dumps({'status': handoff['status'], 'preserved_counts': [v['count'] for v in preservation.values()],
                  'read_files_verified': len(read_handoff['new_files']), 'local_artifacts': len(manifest),
                  'solver_imports': len(runtime['imports']), 'owned_processes': process['matching_python_processes'],
                  'handoff_sha256': sha(ROOT/'handoff.json'), 'manifest_sha256': sha(ROOT/'artifact-sha256.json')}))
