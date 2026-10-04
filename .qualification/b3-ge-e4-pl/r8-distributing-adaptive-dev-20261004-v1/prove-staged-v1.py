from pathlib import Path
import hashlib, json, subprocess

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
paths = json.loads((ROOT / 'stage-list-v1.json').read_text())
normalized = {'.gitattributes', 'docs/agent_plans/B3_GE_E4_PL_ACTIVE_STATE.md',
    'docs/agent_plans/B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md'}
proof = {}
for name in paths:
    raw = (REPO / name).read_bytes()
    expected = raw.replace(b'\r\n', b'\n') if name in normalized else raw
    staged = subprocess.check_output(['git', 'show', ':' + name], cwd=REPO)
    assert staged == expected, name
    proof[name] = hashlib.sha256(staged).hexdigest()
for name in ('docs/agent_plans/development/r8-distributing-reference-linear-20261004/results.md',
             'docs/agent_plans/B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md'):
    old = subprocess.check_output(['git', 'show', 'HEAD:' + name], cwd=REPO)
    staged = subprocess.check_output(['git', 'show', ':' + name], cwd=REPO)
    assert staged.startswith(old), name
(ROOT / 'staged-proof-v1.json').open('x').write(json.dumps(proof, indent=2) + '\n')
print(f'Proved {len(proof)} staged file identities and historical report/matrix prefixes.')
