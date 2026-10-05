from pathlib import Path
import hashlib, json
ROOT = Path(__file__).resolve().parent; REPO = ROOT.parents[2]
tested = ['scripts/r8_e02_double_output.py', 'tests/test_r8_e02_double_output.py']
binding = json.loads((ROOT/'fine-binding-v1.json').read_text())
for rel, value in binding['sources'].items():
    assert hashlib.sha256((REPO/rel).read_bytes()).hexdigest() == value
proof = {rel:hashlib.sha256((REPO/rel).read_bytes()).hexdigest() for rel in tested}
(ROOT/'tested-source-sha256.json').write_text(json.dumps(proof, indent=2)+'\n', encoding='ascii')
docs = ['.gitattributes', 'docs/agent_plans/B3_GE_E4_PL_ACTIVE_STATE.md',
    'docs/agent_plans/B3_GE_E4_PL_REVISION_8_GOAL.md', 'docs/agent_plans/B3_GE_E4_PL_REVISION_8_PLAN.md',
    'docs/agent_plans/B3_GE_E4_PL_REVISION_8_ACCEPTANCE_MATRIX.md',
    'docs/agent_plans/development/r8-distributing-reference-linear-20261004/results.md']
raw = [p.relative_to(REPO).as_posix() for p in ROOT.rglob('*') if p.is_file()]
stage = ROOT/'stage-list-v1.txt'
paths = sorted(set(docs+tested+raw+[stage.relative_to(REPO).as_posix()]))
assert all((REPO/p).resolve().is_relative_to(REPO.resolve()) for p in paths)
stage.write_text('\n'.join(paths)+'\n', encoding='ascii')
print(json.dumps(dict(stage_files=len(paths), raw_bytes=sum((REPO/p).stat().st_size for p in raw))))
