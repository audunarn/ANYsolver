"""Freeze one reviewed development case; no solver imports or execution."""
from pathlib import Path
import hashlib
import json

root = Path('C:/Users/AudunArnesenNyhus/.codex/worktrees/general-contact-native-dynamics/ANYsolver')
support = Path('C:/ANYworkspaceWork/ANYsolver-general-contact/docs/d1_review_support')
prefix = 'native_forced_response_v1_20261001'
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
proposal_path = support/(prefix+'.proposal.json')
proposal = json.loads(proposal_path.read_text(encoding='utf-8'))
old_path = support/'native_vibration_v2_20260930.inputs.json'
assert digest(old_path) == proposal['history']['input_sha256']
old = json.loads(old_path.read_text(encoding='utf-8'))
overrides = {'_ge_beam3_native_midpoint.py': 'f2c494a93315b541500a8f6aa7330bfae2f731ac9f2251f1585704638f03f71a'}
source_sha = {}
for path, expected in old['source_sha256'].items():
    expected = overrides.get(Path(path).name, expected)
    assert digest(Path(path)) == expected, path
    source_sha[path] = expected
for label, relative in [('reference','tests/native_forced_response_reference.py'),
                        ('test','tests/test_ge_beam3_native_forced_response.py')]:
    assert digest(root/relative) == proposal['source_sha256'][label]
    source_sha[str(root/relative)] = digest(root/relative)
historical = {}
for label, filename, hash_key in [
    ('raw', 'native_vibration_v2_20260930.raw.json', 'raw_sha256'),
    ('inputs', 'native_vibration_v2_20260930.inputs.json', 'input_sha256'),
    ('fixture', None, 'fixture_sha256'),
    ('projection', prefix+'.saved_projection.json', 'projection_sha256')]:
    path = support/filename if filename else root/'tests/test_ge_beam3_native_midpoint.py'
    assert digest(path) == proposal['history'][hash_key], str(path)
    historical[label] = {'path': str(path), 'sha256': digest(path)}
basetemp = Path('C:/ANYworkspaceWork/general-contact-native-forced-v1-tmp-20261001')
for path in [basetemp]+[support/(prefix+suffix) for suffix in
                       ('.inputs.json','.raw.json','.xml','.log','.resources.json')]:
    assert not path.exists(), path
paths = set((root/'src/anysolver').rglob('*.py'))
paths.update(root/p for p in ['pyproject.toml','tests/conftest.py',
    'tests/test_ge_beam3_native_midpoint.py','tests/native_forced_response_reference.py',
    'tests/test_ge_beam3_native_forced_response.py','docs/d1_review_support/contact_development_check.py'])
record = dict(workspace=str(root), source_commit='reviewed forced-response source; production unchanged',
    environment={'PYTHONPATH':'src;tests;.;examples','OMP_NUM_THREADS':'1',
        'OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1',
        'NATIVE_FORCED_RESPONSE_INPUTS':str(support/(prefix+'.inputs.json')),
        'NATIVE_FORCED_RESPONSE_RAW_OUTPUT':str(support/(prefix+'.raw.json'))},
    sources=[{'path':str(p.relative_to(root)), 'sha256':digest(p)} for p in sorted(paths)],
    source_sha256=source_sha, historical_source_overrides=overrides, historical=historical,
    criteria=proposal['criteria'], proposal_sha256=digest(proposal_path),
    pytest_args=['-q','-s','tests/test_ge_beam3_native_forced_response.py',
        '--junitxml='+str(support/(prefix+'.xml')),'--basetemp='+str(basetemp)],
    limits=proposal['supervisor'], basetemp_admission={'path':str(basetemp),'must_be_absent_before_execution':True},
    purpose='Forced response temporal development against authenticated shared spatial inputs; no C7 acceptance')
out = support/(prefix+'.inputs.json')
out.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'input':str(out),'sha256':digest(out),'sources':len(paths),'history':historical}))
