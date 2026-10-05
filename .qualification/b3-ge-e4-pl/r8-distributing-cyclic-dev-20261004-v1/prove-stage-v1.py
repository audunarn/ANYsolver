from pathlib import Path
import hashlib, json, subprocess, sys

ROOT = Path(__file__).resolve().parent
label = sys.argv[1]
repo = (ROOT.parents[2] if label == 'solver' else
        Path('C:/Github/ANYfem/.worktrees/experimental-ge-panel-consumer'))
paths = json.loads((ROOT / (label + '-stage-v1.json')).read_text())
git = ['git', '-c', 'safe.directory=' + repo.as_posix()]
actual = subprocess.check_output(git + ['diff','--cached','--name-only','-z'], cwd=repo).decode().split('\0')
assert sorted(p for p in actual if p) == sorted(paths), 'unexpected staged scope'
normalized = {'.gitattributes', 'docs/agent_plans/B3_GE_E4_PL_ACTIVE_STATE.md',
              'docs/agent_plans/B3_GE_E4_PL_REVISION_8_GOAL.md',
              'docs/agent_plans/B3_GE_E4_PL_REVISION_8_PLAN.md',
              'docs/agent_plans/B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md'}
proof = {}
for name in paths:
    raw = (repo / name).read_bytes()
    expected = raw.replace(b'\r\n', b'\n') if name in normalized else raw
    staged = subprocess.check_output(git + ['show', ':' + name], cwd=repo)
    assert staged == expected, name
    proof[name] = hashlib.sha256(staged).hexdigest()
if label == 'solver':
    for name in ('docs/agent_plans/development/r8-distributing-reference-linear-20261004/results.md',
                 'docs/agent_plans/B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md'):
        old = subprocess.check_output(git + ['show', 'HEAD:' + name], cwd=repo)
        staged = subprocess.check_output(git + ['show', ':' + name], cwd=repo)
        assert staged.startswith(old), name
subprocess.run(git + ['-c','core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol',
    'diff','--cached','--check'], cwd=repo, check=True)
(ROOT / (label + '-staged-proof-v1.json')).open('x').write(json.dumps(proof, indent=2) + '\n')
print(f'Proved {len(proof)} {label} staged byte identities and exact file scope.')
