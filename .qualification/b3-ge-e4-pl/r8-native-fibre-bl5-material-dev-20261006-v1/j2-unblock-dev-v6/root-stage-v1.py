"""Stage only this owned, source-bound slice; inspect staged bytes."""
from pathlib import Path
import hashlib
import json
import subprocess

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parents[2]
PREFIX = HERE.relative_to(REPO).as_posix()
manifest = json.loads((HERE / 'artifact-sha256-v6.json').read_text())
handoff = json.loads((HERE / 'handoff-v6.json').read_text())
paths = {PREFIX + '/' + name for name in manifest['artifacts']}
paths.update(handoff['source_sha256'])
paths.update(PREFIX + '/' + name for name in (
    'artifact-sha256-v6.json', 'independent-transition-decision-v1.md',
    'root-preservation-v1.py', 'root-binding-v1.json', 'root-stage-v1.py'))
paths.update(('.gitattributes', 'docs/agent_plans/B3_GE_E4_PL_ACTIVE_STATE.md',
              'docs/agent_plans/B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md',
              'docs/agent_plans/history/PRE_J2_UNBLOCK_SHORTENING_20261006.md'))
paths = sorted(paths)
before = subprocess.run(['git', 'diff', '--cached', '--name-only', '-z'], cwd=REPO,
                         capture_output=True, check=True).stdout
assert not before, 'preserve unrelated existing staging'
for start in range(0, len(paths), 32):
    subprocess.run(['git', '-c', 'core.longpaths=true', 'add', '-f', '--', *paths[start:start+32]],
                   cwd=REPO, capture_output=True, check=True)
staged = subprocess.run(['git', 'diff', '--cached', '--name-only', '-z'], cwd=REPO,
                        capture_output=True, check=True).stdout.decode().rstrip('\0').split('\0')
assert set(staged) == set(paths), 'unexpected staged ownership'
normalized = []
for name in paths:
    working = (REPO / name).read_bytes()
    indexed = subprocess.run(['git', 'show', ':' + name], cwd=REPO,
                             capture_output=True, check=True).stdout
    if indexed != working:
        assert name == '.gitattributes' and indexed == working.replace(b'\r\n', b'\n'), name
        normalized.append(name)
report = {'staged_count': len(paths), 'byte_exact_count': len(paths)-len(normalized),
          'benign_crlf_normalization': normalized,
          'source_sha256': handoff['source_sha256'],
          'paths_digest': hashlib.sha256(('\n'.join(paths)+'\n').encode()).hexdigest(),
          'root_tool_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
print(json.dumps(report))
