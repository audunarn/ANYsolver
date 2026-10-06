"""Metadata-only root inspection; no numerical imports or solver evaluations."""
from pathlib import Path
import hashlib
import json
import subprocess

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE.parent
REPO = EVIDENCE.parents[2]
OUTPUT = HERE / 'root-binding-v1.json'
assert not OUTPUT.exists(), 'one-use root record already exists'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def check_manifest(base, name):
    data = json.loads((base / name).read_text())
    rows = data['artifacts']
    for relative, row in rows.items():
        assert sha(base / relative) == row['sha256'], relative
    return {'count': len(rows), 'manifest_sha256': sha(base / name)}

handoff = json.loads((HERE / 'handoff-v6.json').read_text())
assert handoff['state'] == 'FAILED_FULL_TARGET'
assert handoff['numerical_lease'] == 'RELEASED'
assert handoff['owned_processes_present'] == 0
verified = {'v6': check_manifest(HERE, 'artifact-sha256-v6.json')}
for name in ('raw-artifact-sha256.json', 'raw-artifact-sha256-v2.json'):
    verified[name] = check_manifest(EVIDENCE, name)
verified['local-v4'] = check_manifest(EVIDENCE / 'local-audit-v4', 'artifact-sha256.json')
verified['boundary-v5'] = check_manifest(EVIDENCE / 'boundary-candidate-v5', 'artifact-sha256.json')
read_handoff = json.loads((EVIDENCE / 'owner-diagnosis-v3-handoff.json').read_text())
for relative, row in read_handoff['new_files'].items():
    assert sha(EVIDENCE / relative) == row['sha256'], relative
verified['read-v3'] = {'count': len(read_handoff['new_files']),
                       'handoff_sha256': sha(EVIDENCE / 'owner-diagnosis-v3-handoff.json')}
for relative, expected in handoff['source_sha256'].items():
    assert sha(REPO / relative) == expected, relative
strict = handoff['unchanged_strict_test']
assert sha(REPO / strict['path']) == strict['sha256']
old_artifact = json.loads((EVIDENCE / 'artifact-binding-v1.json').read_text())
assert sha(old_artifact['artifact']) == old_artifact['sha256']
for relative, expected in old_artifact['source'].items():
    installed = relative.replace('\\', '/').removeprefix('src/')
    assert sha(EVIDENCE / 'installed-wheel-v1' / installed) == expected, relative
archive = REPO / 'docs/agent_plans/history/PRE_J2_UNBLOCK_SHORTENING_20261006.md'
assert archive.stat().st_size == 13665
assert sha(archive) == '0d1864bc2e136f645f082b99b481e52d54a23fdcea05bff623cf317ccca2a888'
matrix_name = 'docs/agent_plans/B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md'
old_matrix = subprocess.run(['git', 'show', '1bc4dd4f:' + matrix_name], cwd=REPO,
                            capture_output=True, check=True).stdout
new_matrix = (REPO / matrix_name).read_bytes()
assert new_matrix.startswith(old_matrix), 'historical matrix prefix changed'
new_matrix[len(old_matrix):].decode('ascii')
review_names = ('independent-derivative-contract-v1.md', 'independent-paired-review-v1.md',
                'independent-q4-event-review-v1.md', 'independent-transition-decision-v1.md')
reviews = {name: sha(HERE / name) for name in review_names}
report = {
    'kind': 'metadata-only preservation/source binding; not mechanics qualification',
    'state': 'FAILED_FULL_TARGET', 'verified_manifests': verified,
    'source_sha256': handoff['source_sha256'], 'strict_test': strict,
    'handoff_sha256': sha(HERE / 'handoff-v6.json'), 'independent_reviews': reviews,
    'old_wheel_sha256': old_artifact['sha256'], 'old_installed_source_count': len(old_artifact['source']),
    'matrix_preserved_prefix_bytes': len(old_matrix), 'matrix_append_bytes': len(new_matrix) - len(old_matrix),
    'active_state_sha256': sha(REPO / 'docs/agent_plans/B3_GE_E4_PL_ACTIVE_STATE.md'),
    'archive_sha256': sha(archive), 'root_tool_sha256': sha(__file__),
    'numerical_evaluations': 0, 'new_installed_artifact': False,
}
OUTPUT.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'status': 'PRESERVED', 'v6_artifacts': verified['v6']['count'],
                  'source_files': len(handoff['source_sha256']), 'old_installed_files': len(old_artifact['source']),
                  'report': str(OUTPUT)}))
